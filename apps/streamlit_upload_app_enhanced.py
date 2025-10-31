"""
Enhanced Streamlit application with Advanced Chunking and Document Cleaning.

New Features:
- Document cleaning (remove TOC, acknowledgements)
- Multiple chunking strategies (Semantic, Context, Late, Markup)
- Hybrid chunking options
- Statistics and visualizations
- Real-time configuration
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import time
import tempfile
from typing import Dict, Optional, List, Union
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import hashlib
import json
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.models import SearchParams, PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer

# Import processors
from src.processing.pdf_processor import PDFProcessor, PDFContent
from src.processing.document_cleaner import clean_document, SmartDocumentCleaner
from src.processing.advanced_chunking import UnifiedChunker, ChunkingStrategy
from src.processing.hybrid_chunking import (
    SemanticLateChunker, 
    MarkupContextChunker, 
    MarkupSemanticContextChunker
)


# Page configuration
st.set_page_config(
    page_title="Advanced Document Search 🚀",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def init_qdrant_client(host: str = "localhost", port: int = 6333):
    """Initialize and cache Qdrant client with extended timeout for processing."""
    return QdrantClient(host=host, port=port, timeout=60.0)  # Increased to 60 seconds


@st.cache_resource
def load_embedding_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    """Load and cache the embedding model."""
    with st.spinner(f"Loading embedding model: {model_name}..."):
        model = SentenceTransformer(model_name)
        model.eval()
    return model


@st.cache_resource
def init_pdf_processor(use_cleaning: bool = True):
    """Initialize and cache the PDF processor with cleaning options."""
    return PDFProcessor(
        use_ocr=False,  # Set to True if you have Tesseract installed
        extract_tables=True,
        extract_images=False,
        ocr_language='eng'
    )


@st.cache_resource
def get_chunker(_strategy: str, chunk_size: int = 512, **kwargs):
    """Get chunker based on selected strategy."""
    if _strategy == "Semantic + Late (Hybrid)":
        return SemanticLateChunker(
            chunk_size=chunk_size,
            semantic_threshold=kwargs.get('semantic_threshold', 0.5)
        )
    elif _strategy == "Markup + Context (Hybrid)":
        return MarkupContextChunker(
            max_chunk_size=chunk_size,
            context_window=kwargs.get('context_window', 1)
        )
    elif _strategy == "Markup + Semantic + Context (Triple Hybrid)":
        return MarkupSemanticContextChunker(
            chunk_size=chunk_size,
            semantic_threshold=kwargs.get('semantic_threshold', 0.5),
            context_window=kwargs.get('context_window', 2),
            overlap_size=kwargs.get('overlap_size', 100)
        )
    else:
        # Map strategy names to enum values
        strategy_map = {
            "Semantic": ChunkingStrategy.SEMANTIC,
            "Token": ChunkingStrategy.TOKEN,
            "Markup": ChunkingStrategy.MARKUP,
            "Context": ChunkingStrategy.CONTEXT,
            "Late": ChunkingStrategy.LATE
        }
        return UnifiedChunker(
            strategy=strategy_map.get(_strategy, ChunkingStrategy.SEMANTIC),
            chunk_size=chunk_size,
            overlap_size=kwargs.get('overlap_size', 50)
        )


def ensure_collection_exists(client: QdrantClient, collection_name: str, vector_size: int = 384):
    """Ensure the collection exists, create if it doesn't."""
    try:
        client.get_collection(collection_name)
    except:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
        st.info(f"✅ Created new collection: {collection_name}")


def compute_file_hash(file_content: bytes) -> str:
    """
    Compute SHA256 hash of file content for duplicate detection.
    
    Args:
        file_content: Raw file bytes
        
    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(file_content).hexdigest()


def check_duplicate_document(
    client: QdrantClient,
    collection_name: str,
    file_name: str,
    file_hash: str
) -> Optional[Dict]:
    """
    Check if a document already exists in the collection.
    
    Args:
        client: Qdrant client
        collection_name: Collection to check
        file_name: Name of the file
        file_hash: SHA256 hash of file content
        
    Returns:
        Dict with duplicate info if found, None otherwise
    """
    try:
        # Check if collection exists
        try:
            client.get_collection(collection_name)
        except:
            return None  # Collection doesn't exist, no duplicates
        
        # Search for documents with same file name or file hash
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        # Check by file hash (most reliable)
        results_hash = client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="file_hash",
                        match=MatchValue(value=file_hash)
                    )
                ]
            ),
            limit=1,
            with_payload=True
        )
        
        if results_hash[0]:  # Found duplicate by hash
            point = results_hash[0][0]
            return {
                'type': 'exact_match',
                'file_name': point.payload.get('document_name'),
                'file_hash': point.payload.get('file_hash'),
                'upload_date': point.payload.get('upload_date'),
                'chunks': point.payload.get('total_chunks'),
                'document_id': point.payload.get('document_id')
            }
        
        # Check by file name (possible duplicate, different content)
        results_name = client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="document_name",
                        match=MatchValue(value=file_name)
                    )
                ]
            ),
            limit=1,
            with_payload=True
        )
        
        if results_name[0]:  # Found same name, different content
            point = results_name[0][0]
            return {
                'type': 'name_match',
                'file_name': point.payload.get('document_name'),
                'file_hash': point.payload.get('file_hash'),
                'upload_date': point.payload.get('upload_date'),
                'chunks': point.payload.get('total_chunks'),
                'document_id': point.payload.get('document_id')
            }
        
        return None  # No duplicates found
        
    except Exception as e:
        st.warning(f"Could not check for duplicates: {e}")
        return None


def delete_document_by_id(
    client: QdrantClient,
    collection_name: str,
    document_id: str
) -> bool:
    """
    Delete all chunks of a document by its document_id.
    
    Args:
        client: Qdrant client
        collection_name: Collection name
        document_id: Document ID to delete
        
    Returns:
        True if successful
    """
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        client.delete(
            collection_name=collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        )
        return True
    except Exception as e:
        st.error(f"Error deleting document: {e}")
        return False


def process_and_index_pdf(
    pdf_file,
    pdf_processor: PDFProcessor,
    model: SentenceTransformer,
    client: QdrantClient,
    collection_name: str,
    chunking_strategy: str = "Semantic",
    chunk_size: int = 512,
    clean_document_enabled: bool = True,
    remove_toc: bool = True,
    remove_acknowledgements: bool = True,
    remove_references: bool = False,
    skip_duplicate_check: bool = False,
    **chunking_kwargs
) -> Dict:
    """
    Process a PDF file with cleaning and advanced chunking, then index into Qdrant.
    """
    stats = {
        'filename': pdf_file.name,
        'file_size': pdf_file.size,
        'chunks_created': 0,
        'pages_processed': 0,
        'tables_extracted': 0,
        'processing_time': 0,
        'cleaning_time': 0,
        'chunking_time': 0,
        'indexing_time': 0,
        'cleaning_stats': None,
        'errors': [],
        'is_duplicate': False,
        'duplicate_info': None
    }

    try:
        # Get file content and compute hash
        file_content = pdf_file.getvalue()
        file_hash = compute_file_hash(file_content)
        
        # Check for duplicates (unless skipped)
        if not skip_duplicate_check:
            duplicate = check_duplicate_document(
                client,
                collection_name,
                pdf_file.name,
                file_hash
            )
            
            if duplicate:
                stats['is_duplicate'] = True
                stats['duplicate_info'] = duplicate
                return stats  # Return early, don't process
        
        # Generate consistent document ID based on file hash (not timestamp)
        doc_id = hashlib.md5(f"{pdf_file.name}_{file_hash}".encode()).hexdigest()
        
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file_content)
            tmp_path = Path(tmp_file.name)

        # Process PDF
        with st.spinner("📄 Extracting text from PDF..."):
            start_time = time.time()
            pdf_content = pdf_processor.process_pdf(tmp_path)
            stats['processing_time'] = time.time() - start_time

        # Update stats
        stats['pages_processed'] = len(pdf_content.page_contents)
        stats['tables_extracted'] = len(pdf_content.tables)
        
        text = pdf_content.text

        # Clean document if enabled
        if clean_document_enabled and text.strip():
            with st.spinner("🧹 Cleaning document (removing TOC, acknowledgements)..."):
                start_time = time.time()
                text, cleaning_stats = clean_document(
                    text,
                    remove_toc=remove_toc,
                    remove_acknowledgements=remove_acknowledgements,
                    remove_references=remove_references,
                    smart_cleaning=True,
                    verbose=False
                )
                stats['cleaning_time'] = time.time() - start_time
                stats['cleaning_stats'] = {
                    'original_length': cleaning_stats.original_length,
                    'cleaned_length': cleaning_stats.cleaned_length,
                    'reduction_percentage': cleaning_stats.reduction_percentage,
                    'sections_removed': cleaning_stats.sections_removed
                }

        # Chunk the text with advanced chunking
        with st.spinner(f"✂️ Chunking with {chunking_strategy} strategy..."):
            start_time = time.time()
            
            # Validate text length
            if len(text.strip()) < 100:
                st.error(f"⚠️ Document text is too short ({len(text)} characters). Cannot chunk properly.")
                return stats
            
            chunker = get_chunker(chunking_strategy, chunk_size, **chunking_kwargs)
            
            # Chunk based on strategy
            if chunking_strategy in ["Markup + Context (Hybrid)", "Markup + Semantic + Context (Triple Hybrid)"]:
                chunks = chunker.chunk(text, document_type="generic")
            else:
                chunks = chunker.chunk(text)
            
            stats['chunking_time'] = time.time() - start_time
            stats['chunks_created'] = len(chunks)
            stats['chunking_strategy'] = chunking_strategy
            
            # Log chunk size statistics for debugging
            if chunks:
                chunk_sizes = [len(c.text if hasattr(c, 'text') else str(c)) for c in chunks]
                avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes)
                min_chunk_size = min(chunk_sizes)
                max_chunk_size = max(chunk_sizes)
                st.info(f"📊 Chunk sizes: Avg={avg_chunk_size:.0f}, Min={min_chunk_size}, Max={max_chunk_size} characters")

        # Generate document ID
        doc_id = hashlib.md5(f"{pdf_file.name}_{datetime.now()}".encode()).hexdigest()

        # Index chunks into Qdrant (with timeout handling)
        with st.spinner(f"🔍 Indexing {len(chunks)} chunks into Qdrant..."):
            start_time = time.time()
            points = []

            # Show progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, chunk in enumerate(chunks):
                # Update progress every 10 chunks
                if i % 10 == 0:
                    progress_bar.progress(min((i + 1) / len(chunks), 0.99))
                    status_text.text(f"Processing chunk {i + 1}/{len(chunks)}...")
                # Get chunk text
                chunk_text = chunk.text if hasattr(chunk, 'text') else str(chunk)
                
                # Generate embedding (use contextual if available)
                if hasattr(chunk, 'contextual_embedding') and chunk.contextual_embedding is not None:
                    embedding = chunk.contextual_embedding
                elif hasattr(chunk, 'embedding') and chunk.embedding is not None:
                    embedding = chunk.embedding
                else:
                    embedding = model.encode(
                        chunk_text,
                        convert_to_numpy=True,
                        normalize_embeddings=True,
                        show_progress_bar=False
                    )

                # Create point
                point_id = int(hashlib.md5(f"{doc_id}_{i}".encode()).hexdigest()[:16], 16) % (10**9)

                # Prepare metadata
                metadata = {
                    'content': chunk_text,
                    'document_id': doc_id,
                    'file_hash': file_hash,  # Add for duplicate detection
                    'document_name': pdf_file.name,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'source': 'uploaded',
                    'upload_date': datetime.now().isoformat(),
                    'extraction_method': pdf_content.extraction_method,
                    'page_count': stats['pages_processed'],
                    'file_size': pdf_file.size,
                    'chunking_strategy': chunking_strategy,
                    'was_cleaned': clean_document_enabled
                }
                
                # Add chunk-specific metadata
                if hasattr(chunk, 'metadata') and chunk.metadata:
                    metadata.update({
                        f'chunk_{k}': v for k, v in chunk.metadata.items() 
                        if k not in ['content', 'text']
                    })
                
                # Add context if available - STORE THE ACTUAL TEXT!
                if hasattr(chunk, 'context_before') and chunk.context_before:
                    metadata['context_before'] = chunk.context_before  # Store actual context
                    metadata['has_context_before'] = True
                if hasattr(chunk, 'context_after') and chunk.context_after:
                    metadata['context_after'] = chunk.context_after  # Store actual context
                    metadata['has_context_after'] = True
                if hasattr(chunk, 'section_hierarchy') and chunk.section_hierarchy:
                    metadata['section_hierarchy'] = ' > '.join(chunk.section_hierarchy)

                point = PointStruct(
                    id=point_id,
                    vector=embedding.tolist() if hasattr(embedding, 'tolist') else embedding,
                    payload=metadata
                )
                points.append(point)
                
            # Clear progress indicators
            progress_bar.progress(1.0)
            status_text.text(f"Uploading {len(points)} points to Qdrant...")

            # Upload to Qdrant in batches to avoid timeout
            batch_size = 100
            for batch_start in range(0, len(points), batch_size):
                batch_end = min(batch_start + batch_size, len(points))
                batch_points = points[batch_start:batch_end]
                
                client.upsert(
                    collection_name=collection_name,
                    points=batch_points
                )
                status_text.text(f"Uploaded {batch_end}/{len(points)} points...")
            
            status_text.empty()
            
            stats['indexing_time'] = time.time() - start_time

        # Clean up temp file
        tmp_path.unlink()

    except Exception as e:
        stats['errors'].append(str(e))
        st.error(f"Error processing PDF: {e}")

    return stats


def search_documents(
    query: str,
    model: SentenceTransformer,
    client: QdrantClient,
    collection_name: str,
    top_k: int = 5,
    score_threshold: float = 0.5
) -> List[Dict]:
    """Search for similar documents."""
    # Generate query embedding
    query_embedding = model.encode(
        query,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    # Search Qdrant
    results = client.search(
        collection_name=collection_name,
        query_vector=query_embedding.tolist(),
        limit=top_k,
        score_threshold=score_threshold
    )

    # Format results
    formatted_results = []
    for result in results:
        formatted_results.append({
            'score': result.score,
            'content': result.payload.get('content', ''),
            'context_before': result.payload.get('context_before', ''),
            'context_after': result.payload.get('context_after', ''),
            'document_name': result.payload.get('document_name', 'Unknown'),
            'chunk_index': result.payload.get('chunk_index', 0),
            'total_chunks': result.payload.get('total_chunks', 0),
            'chunking_strategy': result.payload.get('chunking_strategy', 'Unknown'),
            'was_cleaned': result.payload.get('was_cleaned', False),
            'section_hierarchy': result.payload.get('section_hierarchy', ''),
            'has_context': result.payload.get('has_context_before', False) or result.payload.get('has_context_after', False)
        })

    return formatted_results


def main():
    """Main application."""
    
    # Header
    st.title("📚 Advanced Document Search System")
    st.markdown("""
    Upload PDFs and search with **advanced chunking strategies** and **automatic document cleaning**!
    
    **New Features**:
    - 🧹 Automatic TOC & acknowledgements removal
    - ✂️ Multiple chunking strategies (Semantic, Context, Late, Markup)
    - 🔄 Hybrid chunking options
    - 📊 Detailed statistics
    """)

    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Qdrant connection
    st.sidebar.subheader("🔌 Qdrant Connection")
    qdrant_host = st.sidebar.text_input("Host", value="localhost")
    qdrant_port = st.sidebar.number_input("Port", value=6333, min_value=1, max_value=65535)
    collection_name = st.sidebar.text_input("Collection Name", value="documents_enhanced")
    
    # Document cleaning options
    st.sidebar.subheader("🧹 Document Cleaning")
    clean_enabled = st.sidebar.checkbox("Enable Cleaning", value=True, 
        help="Remove TOC, acknowledgements, etc.")
    
    if clean_enabled:
        remove_toc = st.sidebar.checkbox("Remove Table of Contents", value=True)
        remove_ack = st.sidebar.checkbox("Remove Acknowledgements", value=True)
        remove_refs = st.sidebar.checkbox("Remove References", value=False, 
            help="Usually better to keep references")
    
    # Chunking strategy
    st.sidebar.subheader("✂️ Chunking Strategy")
    chunking_strategy = st.sidebar.selectbox(
        "Strategy",
        options=[
            "Semantic",
            "Context",
            "Late",
            "Markup",
            "Token",
            "Semantic + Late (Hybrid)",
            "Markup + Context (Hybrid)",
            "Markup + Semantic + Context (Triple Hybrid)"
        ],
        index=7,  # Default to Markup + Semantic + Context (Triple Hybrid)
        help="Choose how to split documents into chunks"
    )
    
    chunk_size = st.sidebar.slider("Chunk Size", min_value=128, max_value=2048, value=256, step=128)
    
    # Strategy-specific options
    chunking_kwargs = {}
    if "Context" in chunking_strategy:
        context_window = st.sidebar.slider("Context Window", min_value=1, max_value=3, value=2,
            help="Number of surrounding chunks to include as context")
        chunking_kwargs['context_window'] = context_window
    
    if "Semantic" in chunking_strategy or chunking_strategy == "Semantic":
        semantic_threshold = st.sidebar.slider("Semantic Threshold", 
            min_value=0.0, max_value=1.0, value=0.5, step=0.05,
            help="Threshold for semantic similarity")
        chunking_kwargs['semantic_threshold'] = semantic_threshold
    
    # Search parameters
    st.sidebar.subheader("🔍 Search Parameters")
    top_k = st.sidebar.slider("Results to return", min_value=1, max_value=20, value=5)
    score_threshold = st.sidebar.slider("Score threshold", 
        min_value=0.0, max_value=1.0, value=0.5, step=0.05)
    
    # Initialize clients
    try:
        client = init_qdrant_client(qdrant_host, qdrant_port)
        model = load_embedding_model()
        pdf_processor = init_pdf_processor()
        ensure_collection_exists(client, collection_name)
        
        # Show connection status
        st.sidebar.success("✅ Connected to Qdrant")
        
        # Get collection info
        try:
            info = client.get_collection(collection_name)
            st.sidebar.metric("Documents Indexed", info.points_count)
        except:
            st.sidebar.warning("Collection not found")
        
    except Exception as e:
        st.sidebar.error(f"❌ Connection Error: {e}")
        st.stop()
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📤 Upload & Index", "🔍 Search", "📊 Statistics"])
    
    with tab1:
        st.header("Upload PDF Documents")
        
        # Multiple file upload
        uploaded_files = st.file_uploader(
            "Choose PDF file(s)",
            type=['pdf'],
            accept_multiple_files=True,  # Enable multiple file selection
            help="Upload one or more PDFs to process and index"
        )
        
        if uploaded_files:
            st.info(f"📁 **{len(uploaded_files)} file(s) selected** ({sum(f.size for f in uploaded_files) / 1024:.1f} KB total)")
            
            # Show file list with selection checkboxes
            st.subheader("Selected Files:")
            
            # Initialize session state for file selection
            if 'selected_files' not in st.session_state:
                st.session_state.selected_files = set()
            
            # Select All / Deselect All buttons
            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                if st.button("✅ Select All", use_container_width=True):
                    st.session_state.selected_files = set(f.name for f in uploaded_files)
                    st.rerun()
            with col2:
                if st.button("❌ Deselect All", use_container_width=True):
                    st.session_state.selected_files = set()
                    st.rerun()
            
            # File selection list
            files_to_process = []
            for uploaded_file in uploaded_files:
                col1, col2 = st.columns([0.1, 0.9])
                with col1:
                    is_selected = st.checkbox(
                        "",
                        value=uploaded_file.name in st.session_state.selected_files,
                        key=f"select_{uploaded_file.name}",
                        label_visibility="collapsed"
                    )
                    if is_selected:
                        st.session_state.selected_files.add(uploaded_file.name)
                        files_to_process.append(uploaded_file)
                    else:
                        st.session_state.selected_files.discard(uploaded_file.name)
                
                with col2:
                    st.text(f"📄 {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
            
            st.divider()
            
            # Process selected files
            if files_to_process:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.info(f"**{len(files_to_process)} file(s) ready to process**")
                with col2:
                    if st.button("🚀 Process Selected", type="primary", use_container_width=True):
                        # Process each selected file
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        all_stats = []
                        total_files = len(files_to_process)
                        
                        for idx, uploaded_file in enumerate(files_to_process):
                            status_text.text(f"Processing {idx + 1}/{total_files}: {uploaded_file.name}")
                            
                            with st.spinner(f"Processing {uploaded_file.name}..."):
                                stats = process_and_index_pdf(
                                    uploaded_file,
                                    pdf_processor,
                                    model,
                                    client,
                                    collection_name,
                                    chunking_strategy=chunking_strategy,
                                    chunk_size=chunk_size,
                                    clean_document_enabled=clean_enabled,
                                    remove_toc=remove_toc if clean_enabled else False,
                                    remove_acknowledgements=remove_ack if clean_enabled else False,
                                    remove_references=remove_refs if clean_enabled else False,
                                    **chunking_kwargs
                                )
                                stats['filename'] = uploaded_file.name
                                all_stats.append(stats)
                            
                            progress_bar.progress((idx + 1) / total_files)
                        
                        status_text.empty()
                        progress_bar.empty()
                        
                        # Show summary
                        st.success(f"✅ Successfully processed {len(files_to_process)} document(s)!")
                        
                        # Aggregate statistics
                        total_pages = sum(s['pages_processed'] for s in all_stats)
                        total_tables = sum(s['tables_extracted'] for s in all_stats)
                        total_chunks = sum(s['chunks_created'] for s in all_stats)
                        total_time = sum(
                            s['processing_time'] + s.get('cleaning_time', 0) + 
                            s.get('chunking_time', 0) + s['indexing_time'] 
                            for s in all_stats
                        )
                        
                        # Display aggregate statistics
                        st.subheader("📊 Batch Processing Summary")
                        col1, col2, col3, col4, col5 = st.columns(5)
                        col1.metric("Files", len(all_stats))
                        col2.metric("Pages", total_pages)
                        col3.metric("Tables", total_tables)
                        col4.metric("Chunks", total_chunks)
                        col5.metric("Total Time", f"{total_time:.2f}s")
                        
                        # Individual file statistics
                        st.subheader("📄 Individual File Statistics")
                        stats_data = []
                        for stats in all_stats:
                            stats_data.append({
                                'File': stats['filename'],
                                'Pages': stats['pages_processed'],
                                'Tables': stats['tables_extracted'],
                                'Chunks': stats['chunks_created'],
                                'Time (s)': f"{stats['processing_time'] + stats.get('cleaning_time', 0) + stats.get('chunking_time', 0) + stats['indexing_time']:.2f}",
                                'Status': '✅ Success' if not stats['errors'] else '❌ Error'
                            })
                        
                        df_stats = pd.DataFrame(stats_data)
                        st.dataframe(df_stats, use_container_width=True)
                        
                        # Clear selection after processing
                        st.session_state.selected_files = set()
                        
                        # Use first file's stats for detailed display (if available)
                        if all_stats:
                            stats = all_stats[0]
                            
                            # Cleaning stats (show for first file as example)
                            if stats.get('cleaning_stats'):
                                st.subheader("🧹 Cleaning Statistics (First File)")
                                col1, col2, col3 = st.columns(3)
                                col1.metric("Original Size", f"{stats['cleaning_stats']['original_length']} chars")
                                col2.metric("Cleaned Size", f"{stats['cleaning_stats']['cleaned_length']} chars")
                                col3.metric("Reduction", f"{stats['cleaning_stats']['reduction_percentage']:.1f}%")
                                
                                if stats['cleaning_stats']['sections_removed']:
                                    st.info(f"**Removed sections**: {', '.join(stats['cleaning_stats']['sections_removed'])}")
                            
                            # Timing breakdown (aggregate for all files)
                            st.subheader("⏱️ Total Processing Time Breakdown")
                            timing_data = {
                                'Step': ['PDF Extraction', 'Cleaning', 'Chunking', 'Indexing'],
                                'Time (s)': [
                                    sum(s['processing_time'] for s in all_stats),
                                    sum(s.get('cleaning_time', 0) for s in all_stats),
                                    sum(s.get('chunking_time', 0) for s in all_stats),
                                    sum(s['indexing_time'] for s in all_stats)
                                ]
                            }
                            fig = px.bar(timing_data, x='Step', y='Time (s)', 
                                        title="Total Processing Time by Step")
                            st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("👆 Select files above using checkboxes, then click 'Process Selected'")
    
    with tab2:
        st.header("Search Documents")
        
        query = st.text_input("Enter your search query:", placeholder="e.g., What is machine learning?")
        
        if st.button("🔍 Search", type="primary") and query:
            with st.spinner("Searching..."):
                results = search_documents(
                    query,
                    model,
                    client,
                    collection_name,
                    top_k=top_k,
                    score_threshold=score_threshold
                )
            
            if results:
                st.success(f"Found {len(results)} results")
                
                for i, result in enumerate(results, 1):
                    with st.expander(f"**Result {i}** - {result['document_name']} (Score: {result['score']:.3f})", expanded=True):
                        # Show metadata first
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Chunk", f"{result['chunk_index'] + 1}/{result['total_chunks']}")
                        col2.metric("Strategy", result['chunking_strategy'])
                        col3.metric("Cleaned", "Yes" if result['was_cleaned'] else "No")
                        
                        if result['section_hierarchy']:
                            st.info(f"📍 **Section**: {result['section_hierarchy']}")
                        
                        st.markdown("---")
                        
                        # Display full content with context
                        if result['context_before']:
                            st.markdown("**📄 Context Before:**")
                            st.markdown(f"<div style='background-color: #f0f0f0; padding: 10px; border-radius: 5px; font-size: 0.9em; color: #666;'>{result['context_before']}</div>", unsafe_allow_html=True)
                            st.markdown("")
                        
                        st.markdown("**📌 Main Content:**")
                        st.markdown(f"<div style='background-color: #e3f2fd; padding: 15px; border-radius: 5px; border-left: 4px solid #2196F3;'>{result['content']}</div>", unsafe_allow_html=True)
                        
                        if result['context_after']:
                            st.markdown("")
                            st.markdown("**📄 Context After:**")
                            st.markdown(f"<div style='background-color: #f0f0f0; padding: 10px; border-radius: 5px; font-size: 0.9em; color: #666;'>{result['context_after']}</div>", unsafe_allow_html=True)
                        
                        # Show total content length
                        total_length = len(result['content'])
                        if result['context_before']:
                            total_length += len(result['context_before'])
                        if result['context_after']:
                            total_length += len(result['context_after'])
                        
                        st.caption(f"📏 Total content length: {total_length} characters | Main chunk: {len(result['content'])} characters")
            else:
                st.warning("No results found. Try adjusting your query or score threshold.")
    
    with tab3:
        st.header("Collection Statistics")
        
        try:
            info = client.get_collection(collection_name)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Points", info.points_count)
            col2.metric("Vector Dimension", info.config.params.vectors.size)
            col3.metric("Distance Metric", info.config.params.vectors.distance)
            
            # Strategy breakdown (if we had this data)
            st.subheader("📊 Performance Metrics")
            st.info("Upload and search documents to see performance metrics!")
            
        except Exception as e:
            st.error(f"Error fetching statistics: {e}")


if __name__ == "__main__":
    main()

