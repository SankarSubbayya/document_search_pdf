"""
PDF Document Management System - Streamlit Application

A dedicated application for managing PDF documents with:
- Separate vector store collection
- Document upload, indexing, and management
- Advanced search and filtering
- Document deletion and metadata editing
- Collection statistics and analytics
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import time
import tempfile
from typing import Dict, Optional, List, Union, Tuple
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import hashlib
import json
from datetime import datetime
import shutil

from qdrant_client import QdrantClient
from qdrant_client.models import (
    SearchParams, PointStruct, VectorParams, Distance,
    Filter, FieldCondition, MatchValue, Range
)
from sentence_transformers import SentenceTransformer

# Import PDF processor
from src.processing.pdf_processor import PDFProcessor, PDFContent


# Page configuration
st.set_page_config(
    page_title="PDF Document Manager",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
PDF_COLLECTION_NAME = "pdf_documents"  # Separate collection for PDFs
UPLOAD_DIR = Path("./data/pdf_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@st.cache_resource
def init_qdrant_client(host: str = "localhost", port: int = 6333):
    """Initialize and cache Qdrant client."""
    return QdrantClient(host=host, port=port, timeout=10.0)


@st.cache_resource
def load_embedding_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    """Load and cache the embedding model."""
    with st.spinner(f"Loading embedding model: {model_name}..."):
        model = SentenceTransformer(model_name)
        model.eval()
    return model


@st.cache_resource
def init_pdf_processor():
    """Initialize and cache the PDF processor."""
    return PDFProcessor(
        use_ocr=True,
        extract_tables=True,
        extract_images=False,
        ocr_language='eng'
    )


def initialize_collection(client: QdrantClient, collection_name: str, vector_size: int = 384):
    """Initialize collection with proper configuration."""
    try:
        # Check if collection exists
        collections = client.get_collections().collections
        exists = any(col.name == collection_name for col in collections)

        if not exists:
            # Create new collection
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            st.success(f"✅ Created new collection: {collection_name}")
            return True
        return False
    except Exception as e:
        st.error(f"Error initializing collection: {e}")
        return False


def get_collection_stats(client: QdrantClient, collection_name: str) -> Dict:
    """Get detailed collection statistics."""
    try:
        info = client.get_collection(collection_name)

        # Get sample of documents to analyze
        sample_size = min(1000, info.points_count) if info.points_count else 0
        documents_info = {}

        if sample_size > 0:
            # Scroll through documents to get statistics
            records, _ = client.scroll(
                collection_name=collection_name,
                limit=sample_size,
                with_payload=True,
                with_vectors=False
            )

            # Analyze documents
            unique_docs = set()
            total_chunks = 0
            file_sizes = []
            upload_dates = []
            extraction_methods = {}

            for record in records:
                payload = record.payload
                doc_id = payload.get('document_id')
                if doc_id:
                    unique_docs.add(doc_id)

                total_chunks += 1

                if payload.get('file_size'):
                    file_sizes.append(payload['file_size'])

                if payload.get('upload_date'):
                    upload_dates.append(payload['upload_date'])

                method = payload.get('extraction_method', 'unknown')
                extraction_methods[method] = extraction_methods.get(method, 0) + 1

            documents_info = {
                'unique_documents': len(unique_docs),
                'total_chunks': total_chunks,
                'avg_file_size': sum(file_sizes) / len(file_sizes) if file_sizes else 0,
                'extraction_methods': extraction_methods,
                'oldest_upload': min(upload_dates) if upload_dates else None,
                'newest_upload': max(upload_dates) if upload_dates else None
            }

        return {
            'status': 'connected',
            'points_count': info.points_count,
            'vectors_count': info.vectors_count if info.vectors_count else info.points_count,
            'status_color': info.status,
            'documents_info': documents_info
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'points_count': 0,
            'vectors_count': 0,
            'documents_info': {}
        }


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[Tuple[str, int, int]]:
    """
    Split text into overlapping chunks with position tracking.

    Returns:
        List of tuples: (chunk_text, start_position, end_position)
    """
    if not text:
        return []

    # Clean text
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Split into sentences (simple approach)
    sentences = text.replace('\n\n', '\n').split('. ')

    chunks = []
    current_chunk = []
    current_size = 0
    current_start = 0

    for i, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if sentence and not sentence.endswith('.'):
            sentence += '.'

        sentence_size = len(sentence)

        if current_size + sentence_size > chunk_size and current_chunk:
            # Join current chunk and add to chunks
            chunk_text = ' '.join(current_chunk)
            chunks.append((chunk_text, current_start, current_start + len(chunk_text)))

            # Create overlap
            overlap_sentences = []
            overlap_size = 0
            for sent in reversed(current_chunk):
                if overlap_size + len(sent) <= overlap:
                    overlap_sentences.insert(0, sent)
                    overlap_size += len(sent)
                else:
                    break

            current_chunk = overlap_sentences + [sentence]
            current_size = sum(len(s) for s in current_chunk)
            current_start = current_start + len(chunk_text) - overlap_size
        else:
            current_chunk.append(sentence)
            current_size += sentence_size

    # Add remaining chunk
    if current_chunk:
        chunk_text = ' '.join(current_chunk)
        chunks.append((chunk_text, current_start, current_start + len(chunk_text)))

    return chunks


def process_pdf_file(
    pdf_path: Path,
    pdf_processor: PDFProcessor,
    model: SentenceTransformer,
    client: QdrantClient,
    collection_name: str,
    chunk_size: int = 512,
    overlap: int = 50,
    tags: List[str] = None,
    category: str = "general"
) -> Dict:
    """Process and index a single PDF file."""

    stats = {
        'filename': pdf_path.name,
        'file_size': pdf_path.stat().st_size,
        'chunks_created': 0,
        'pages_processed': 0,
        'tables_extracted': 0,
        'processing_time': 0,
        'indexing_time': 0,
        'document_id': None,
        'errors': []
    }

    try:
        # Process PDF
        start_time = time.time()
        pdf_content = pdf_processor.process_pdf(pdf_path)
        stats['processing_time'] = time.time() - start_time

        # Update stats
        stats['pages_processed'] = len(pdf_content.page_contents)
        stats['tables_extracted'] = len(pdf_content.tables)

        # Generate unique document ID
        doc_id = hashlib.md5(f"{pdf_path.name}_{datetime.now()}".encode()).hexdigest()
        stats['document_id'] = doc_id

        # Chunk the text with positions
        chunks_with_positions = chunk_text(pdf_content.text, chunk_size, overlap)
        stats['chunks_created'] = len(chunks_with_positions)

        # Index chunks into Qdrant
        start_time = time.time()
        points = []

        for i, (chunk_content, start_pos, end_pos) in enumerate(chunks_with_positions):
            # Generate embedding
            embedding = model.encode(
                chunk_content,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False
            )

            # Create point ID
            point_id = hashlib.md5(f"{doc_id}_{i}".encode()).hexdigest()

            # Prepare metadata
            metadata = {
                'content': chunk_content,
                'document_id': doc_id,
                'document_name': pdf_path.name,
                'chunk_index': i,
                'total_chunks': len(chunks_with_positions),
                'char_start': start_pos,
                'char_end': end_pos,
                'upload_date': datetime.now().isoformat(),
                'extraction_method': pdf_content.extraction_method,
                'page_count': stats['pages_processed'],
                'file_size': stats['file_size'],
                'category': category,
                'tags': tags or [],
                'file_path': str(pdf_path)
            }

            # Add PDF metadata
            if pdf_content.metadata:
                metadata['pdf_metadata'] = {
                    'title': pdf_content.metadata.get('title', ''),
                    'author': pdf_content.metadata.get('author', ''),
                    'subject': pdf_content.metadata.get('subject', ''),
                    'creator': pdf_content.metadata.get('creator', ''),
                    'creation_date': str(pdf_content.metadata.get('creation_date', '')),
                    'modification_date': str(pdf_content.metadata.get('modification_date', ''))
                }

            # Add table information if chunk contains tables
            if pdf_content.tables:
                # Check if this chunk might contain table data
                tables_in_chunk = []
                for table in pdf_content.tables:
                    # Simple heuristic: check if table page matches chunk position
                    if table.get('page', 0) <= (i * stats['pages_processed'] / len(chunks_with_positions)) + 1:
                        tables_in_chunk.append({
                            'page': table.get('page'),
                            'rows': table.get('rows', 0),
                            'columns': table.get('columns', 0)
                        })
                if tables_in_chunk:
                    metadata['tables'] = tables_in_chunk

            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload=metadata
                )
            )

        # Upload to Qdrant in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]
            client.upsert(
                collection_name=collection_name,
                points=batch
            )

        stats['indexing_time'] = time.time() - start_time

    except Exception as e:
        stats['errors'].append(str(e))
        st.error(f"Error processing PDF: {e}")

    return stats


def search_documents(
    client: QdrantClient,
    model: SentenceTransformer,
    query: str,
    collection_name: str,
    limit: int = 10,
    score_threshold: Optional[float] = None,
    exact: bool = False,
    category_filter: Optional[str] = None,
    tag_filter: Optional[List[str]] = None
) -> Dict:
    """Search documents with advanced filtering."""

    timing = {}

    # Generate query embedding
    start_time = time.time()
    query_embedding = model.encode(
        query,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    )
    timing['embedding'] = time.time() - start_time

    # Build filter conditions
    filter_conditions = []

    if category_filter and category_filter != "all":
        filter_conditions.append(
            FieldCondition(key="category", match=MatchValue(value=category_filter))
        )

    if tag_filter:
        for tag in tag_filter:
            filter_conditions.append(
                FieldCondition(key="tags", match=MatchValue(value=tag))
            )

    query_filter = Filter(must=filter_conditions) if filter_conditions else None

    # Perform search
    start_time = time.time()

    search_params = SearchParams(
        hnsw_ef=128 if not exact else 0,
        exact=exact
    )

    results = client.query_points(
        collection_name=collection_name,
        query=query_embedding.tolist(),
        limit=limit,
        score_threshold=score_threshold,
        with_payload=True,
        search_params=search_params,
        query_filter=query_filter
    ).points

    timing['search'] = time.time() - start_time
    timing['total'] = timing['embedding'] + timing['search']

    # Format results
    formatted_results = []
    for result in results:
        formatted_results.append({
            'score': result.score,
            'point_id': result.id,
            **result.payload
        })

    return {
        'results': formatted_results,
        'timing': timing,
        'count': len(formatted_results)
    }


def get_document_list(client: QdrantClient, collection_name: str) -> List[Dict]:
    """Get list of unique documents in the collection."""
    try:
        # Scroll through all documents
        all_records, _ = client.scroll(
            collection_name=collection_name,
            limit=10000,  # Adjust based on your needs
            with_payload=True,
            with_vectors=False
        )

        # Group by document
        documents = {}
        for record in all_records:
            doc_id = record.payload.get('document_id')
            if doc_id and doc_id not in documents:
                documents[doc_id] = {
                    'document_id': doc_id,
                    'document_name': record.payload.get('document_name', 'Unknown'),
                    'upload_date': record.payload.get('upload_date', ''),
                    'page_count': record.payload.get('page_count', 0),
                    'total_chunks': record.payload.get('total_chunks', 0),
                    'file_size': record.payload.get('file_size', 0),
                    'category': record.payload.get('category', 'general'),
                    'tags': record.payload.get('tags', []),
                    'extraction_method': record.payload.get('extraction_method', 'unknown'),
                    'pdf_metadata': record.payload.get('pdf_metadata', {})
                }

        return list(documents.values())
    except Exception as e:
        st.error(f"Error getting document list: {e}")
        return []


def delete_document(client: QdrantClient, collection_name: str, document_id: str) -> bool:
    """Delete all chunks of a document from the collection."""
    try:
        # Delete all points with this document_id
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


def display_result_card(result: Dict, index: int):
    """Display a search result as an expandable card."""
    score_color = "🟢" if result['score'] > 0.7 else "🟡" if result['score'] > 0.5 else "🔴"

    title = f"{score_color} **Result {index}** - 📄 {result['document_name']}"
    if result.get('chunk_index') is not None:
        title += f" (Chunk {result['chunk_index'] + 1}/{result.get('total_chunks', '?')})"
    title += f" (Score: {result['score']:.4f})"

    with st.expander(title, expanded=(index <= 3)):
        # Metadata columns
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Relevance Score", f"{result['score']:.4f}")

        with col2:
            st.metric("Category", result.get('category', 'general').title())

        with col3:
            st.metric("Pages", result.get('page_count', 'N/A'))

        # Tags
        if result.get('tags'):
            st.write("**Tags:**")
            tags_html = " ".join([
                f'<span style="background-color: #007bff; color: white; padding: 3px 8px; '
                f'border-radius: 12px; margin-right: 5px; font-size: 0.9em;">{tag}</span>'
                for tag in result['tags']
            ])
            st.markdown(tags_html, unsafe_allow_html=True)

        # PDF Metadata
        if result.get('pdf_metadata'):
            metadata = result['pdf_metadata']
            metadata_items = []
            if metadata.get('title'):
                metadata_items.append(f"**Title:** {metadata['title']}")
            if metadata.get('author'):
                metadata_items.append(f"**Author:** {metadata['author']}")
            if metadata.get('subject'):
                metadata_items.append(f"**Subject:** {metadata['subject']}")

            if metadata_items:
                st.write(" | ".join(metadata_items))

        # Upload info
        if result.get('upload_date'):
            st.write(f"**Uploaded:** {result['upload_date'][:10]} | **Method:** {result.get('extraction_method', 'unknown')}")

        # Content
        st.write("**Content:**")
        st.text_area(
            "Content",
            value=result['content'],
            height=200,
            disabled=True,
            label_visibility="collapsed"
        )

        # Position in document
        if result.get('char_start') is not None:
            st.caption(f"Position in document: characters {result['char_start']}-{result['char_end']}")


def main():
    """Main application."""

    st.title("📁 PDF Document Management System")
    st.markdown("Upload, index, search, and manage your PDF documents in a dedicated vector store")

    # Initialize session state
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = []
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    if 'selected_documents' not in st.session_state:
        st.session_state.selected_documents = []

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Connection settings
        with st.expander("🔌 Database Connection", expanded=False):
            host = st.text_input("Qdrant Host", value="localhost")
            port = st.number_input("Qdrant Port", value=6333, min_value=1, max_value=65535)

        # Initialize connections
        try:
            client = init_qdrant_client(host, port)
            model = load_embedding_model()
            pdf_processor = init_pdf_processor()

            # Initialize collection
            initialize_collection(client, PDF_COLLECTION_NAME, vector_size=384)

            model_loaded = True
        except Exception as e:
            st.error(f"Failed to initialize: {str(e)}")
            model_loaded = False
            return

        # Search Controls - Above Collection Statistics
        st.header("🎛️ Search Controls")

        # Number of Documents control
        st.markdown("#### 📊 Number of Documents")
        max_results = st.select_slider(
            "Documents to return",
            options=[1, 3, 5, 10, 15, 20, 25, 30, 40, 50],
            value=10,
            key="sidebar_doc_count",
            label_visibility="collapsed"
        )
        # Visual indicator
        st.markdown(f"""
        <div style='text-align: center; padding: 8px; background: linear-gradient(90deg, #007bff, #00ff88);
                    border-radius: 10px; color: white; font-size: 1.2em; font-weight: bold;'>
            {max_results} Documents
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Similarity Threshold control
        st.markdown("#### 🎯 Similarity Threshold")
        score_threshold = st.slider(
            "Minimum similarity",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.05,
            format="%.2f",
            key="sidebar_score",
            label_visibility="collapsed"
        )
        # Visual indicator with color coding
        if score_threshold == 0:
            threshold_text = "Show All"
            color = "#28a745"
        elif score_threshold < 0.5:
            threshold_text = f"{score_threshold:.0%} Min"
            color = "#ffc107"
        else:
            threshold_text = f"{score_threshold:.0%} Min"
            color = "#dc3545"

        st.markdown(f"""
        <div style='text-align: center; padding: 8px; background: {color};
                    border-radius: 10px; color: white; font-size: 1.2em; font-weight: bold;'>
            {threshold_text}
        </div>
        """, unsafe_allow_html=True)

        # Additional filters
        st.markdown("#### ⚙️ Filters")
        category_filter = st.selectbox(
            "Category",
            options=["all", "general", "research", "documentation", "legal", "financial", "technical", "other"],
            index=0,
            key="sidebar_category"
        )

        exact_search = st.checkbox(
            "🎯 Exact Search Mode",
            value=False,
            key="sidebar_exact",
            help="Slower but 100% accurate"
        )

        st.markdown("---")

        # Collection statistics
        st.header("📊 Collection Statistics")
        if model_loaded:
            stats = get_collection_stats(client, PDF_COLLECTION_NAME)

            if stats['status'] == 'connected':
                st.success("✅ Connected to Qdrant")

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Chunks", f"{stats['points_count']:,}")
                with col2:
                    st.metric("Status", stats['status_color'].upper())

                if stats['documents_info']:
                    info = stats['documents_info']
                    st.metric("Unique Documents", info['unique_documents'])

                    if info.get('avg_file_size'):
                        avg_size_mb = info['avg_file_size'] / (1024 * 1024)
                        st.metric("Avg File Size", f"{avg_size_mb:.1f} MB")

                    if info.get('extraction_methods'):
                        st.write("**Extraction Methods:**")
                        for method, count in info['extraction_methods'].items():
                            st.caption(f"  • {method}: {count} chunks")
            else:
                st.error(f"❌ {stats.get('error', 'Connection failed')}")

        # Upload section
        st.header("📤 Upload PDFs")

        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload one or more PDF files"
        )

        # Document settings
        with st.expander("📝 Document Settings"):
            category = st.selectbox(
                "Category",
                options=["general", "research", "documentation", "legal", "financial", "technical", "other"],
                index=0
            )

            tags_input = st.text_input(
                "Tags (comma-separated)",
                placeholder="e.g., machine-learning, nlp, 2024",
                help="Add tags to help organize and filter documents"
            )
            tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else []

            chunk_size = st.slider(
                "Chunk Size",
                min_value=100,
                max_value=2000,
                value=512,
                step=50
            )

            chunk_overlap = st.slider(
                "Chunk Overlap",
                min_value=0,
                max_value=200,
                value=50,
                step=10
            )

            save_originals = st.checkbox(
                "Save original PDFs",
                value=True,
                help="Keep a copy of uploaded PDFs in the data folder"
            )

        # Process button
        if uploaded_files and st.button("🚀 Process & Index", type="primary", use_container_width=True):
            with st.spinner("Processing PDFs..."):
                total_stats = {
                    'total_files': len(uploaded_files),
                    'successful': 0,
                    'failed': 0,
                    'total_chunks': 0,
                    'total_pages': 0
                }

                progress_bar = st.progress(0)
                status_text = st.empty()

                for i, pdf_file in enumerate(uploaded_files):
                    status_text.text(f"Processing: {pdf_file.name}")

                    # Save to temp file
                    temp_path = UPLOAD_DIR / pdf_file.name
                    with open(temp_path, 'wb') as f:
                        f.write(pdf_file.getvalue())

                    # Process PDF
                    stats = process_pdf_file(
                        pdf_path=temp_path,
                        pdf_processor=pdf_processor,
                        model=model,
                        client=client,
                        collection_name=PDF_COLLECTION_NAME,
                        chunk_size=chunk_size,
                        overlap=chunk_overlap,
                        tags=tags,
                        category=category
                    )

                    if not stats['errors']:
                        total_stats['successful'] += 1
                        total_stats['total_chunks'] += stats['chunks_created']
                        total_stats['total_pages'] += stats['pages_processed']
                        st.session_state.processed_files.append(stats)

                        # Keep original if requested
                        if not save_originals:
                            temp_path.unlink()
                    else:
                        total_stats['failed'] += 1
                        temp_path.unlink()  # Remove failed file

                    progress_bar.progress((i + 1) / len(uploaded_files))

                progress_bar.empty()
                status_text.empty()

                # Show results
                if total_stats['successful'] > 0:
                    st.success(f"✅ Processed {total_stats['successful']} files")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Chunks", total_stats['total_chunks'])
                    with col2:
                        st.metric("Total Pages", total_stats['total_pages'])

                if total_stats['failed'] > 0:
                    st.warning(f"⚠️ Failed: {total_stats['failed']} files")

                # Refresh stats by updating session state
                if 'last_refresh' in st.session_state:
                    st.session_state.last_refresh = time.time()

    # Main area - Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Search", "📚 Documents", "📊 Analytics", "⚙️ Settings"])

    # Search Tab
    with tab1:
        st.header("Search Documents")

        # Clean search interface - just the search box
        col1, col2 = st.columns([3, 1])

        with col1:
            query = st.text_input(
                "Enter your search query",
                placeholder="Search your PDF documents...",
                key="search_input"
            )

        with col2:
            st.write("")  # Spacing
            search_btn = st.button("🔍 Search", type="primary", use_container_width=True)

        # Show current search settings as info
        if max_results or score_threshold:
            settings_col1, settings_col2, settings_col3, settings_col4 = st.columns(4)
            with settings_col1:
                st.info(f"📊 Max Results: {max_results}")
            with settings_col2:
                if score_threshold == 0:
                    st.success(f"🎯 Threshold: Show All")
                else:
                    st.warning(f"🎯 Threshold: {score_threshold:.0%}")
            with settings_col3:
                if category_filter != "all":
                    st.info(f"📁 Category: {category_filter}")
                else:
                    st.info(f"📁 Category: All")
            with settings_col4:
                if exact_search:
                    st.error(f"🎯 Mode: Exact")
                else:
                    st.success(f"⚡ Mode: Fast")

        st.divider()

        # Perform search
        if (search_btn or query) and query.strip() and model_loaded:
            with st.spinner("Searching..."):
                results = search_documents(
                    client=client,
                    model=model,
                    query=query,
                    collection_name=PDF_COLLECTION_NAME,
                    limit=max_results,
                    score_threshold=score_threshold if score_threshold > 0 else None,
                    exact=exact_search,
                    category_filter=category_filter
                )

            # Display timing
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Results Found", results['count'])
            with col2:
                st.metric("Search Time", f"{results['timing']['search']*1000:.1f} ms")
            with col3:
                st.metric("Total Time", f"{results['timing']['total']*1000:.1f} ms")

            st.divider()

            # Display results
            if results['count'] > 0:
                for i, result in enumerate(results['results'], 1):
                    display_result_card(result, i)
            else:
                st.info("No results found. Try adjusting your search query or filters.")

            # Add to search history
            if query not in st.session_state.search_history:
                st.session_state.search_history.insert(0, query)
                st.session_state.search_history = st.session_state.search_history[:10]

    # Documents Tab
    with tab2:
        st.header("Document Library")

        # Get document list
        documents = get_document_list(client, PDF_COLLECTION_NAME)

        if documents:
            # Document controls
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                search_filter = st.text_input(
                    "Filter documents",
                    placeholder="Type to filter by name...",
                    key="doc_filter"
                )

            with col2:
                sort_by = st.selectbox(
                    "Sort by",
                    options=["upload_date", "document_name", "file_size", "page_count"],
                    index=0
                )

            with col3:
                sort_order = st.radio(
                    "Order",
                    options=["desc", "asc"],
                    horizontal=True
                )

            # Filter and sort documents
            if search_filter:
                documents = [d for d in documents if search_filter.lower() in d['document_name'].lower()]

            # Sort documents
            reverse = (sort_order == "desc")
            if sort_by == "upload_date":
                documents.sort(key=lambda x: x.get('upload_date', ''), reverse=reverse)
            elif sort_by == "document_name":
                documents.sort(key=lambda x: x.get('document_name', ''), reverse=reverse)
            elif sort_by == "file_size":
                documents.sort(key=lambda x: x.get('file_size', 0), reverse=reverse)
            elif sort_by == "page_count":
                documents.sort(key=lambda x: x.get('page_count', 0), reverse=reverse)

            st.divider()

            # Display documents
            for doc in documents:
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])

                    with col1:
                        st.write(f"📄 **{doc['document_name']}**")
                        if doc.get('tags'):
                            st.caption(f"Tags: {', '.join(doc['tags'])}")

                    with col2:
                        st.caption(f"📁 {doc.get('category', 'general').title()}")

                    with col3:
                        size_mb = doc.get('file_size', 0) / (1024 * 1024)
                        st.caption(f"💾 {size_mb:.1f} MB")

                    with col4:
                        st.caption(f"📃 {doc.get('page_count', 0)} pages")

                    with col5:
                        if st.button("🗑️", key=f"del_{doc['document_id']}", help="Delete document"):
                            if delete_document(client, PDF_COLLECTION_NAME, doc['document_id']):
                                st.success(f"Deleted: {doc['document_name']}")
                                st.rerun()

                    # Additional info
                    with st.expander("More info"):
                        if doc.get('pdf_metadata'):
                            meta = doc['pdf_metadata']
                            if meta.get('title'):
                                st.write(f"**Title:** {meta['title']}")
                            if meta.get('author'):
                                st.write(f"**Author:** {meta['author']}")

                        st.write(f"**Upload Date:** {doc.get('upload_date', 'Unknown')[:10]}")
                        st.write(f"**Chunks:** {doc.get('total_chunks', 0)}")
                        st.write(f"**Extraction:** {doc.get('extraction_method', 'unknown')}")
                        st.write(f"**Document ID:** `{doc['document_id']}`")

                    st.divider()

            # Summary
            st.info(f"Total: {len(documents)} documents")
        else:
            st.info("No documents in the collection. Upload some PDFs to get started!")

    # Analytics Tab
    with tab3:
        st.header("Collection Analytics")

        if documents:
            # Convert to DataFrame
            df = pd.DataFrame(documents)

            # Basic metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Documents", len(df))

            with col2:
                total_size = df['file_size'].sum() / (1024 * 1024)
                st.metric("Total Size", f"{total_size:.1f} MB")

            with col3:
                st.metric("Total Pages", df['page_count'].sum())

            with col4:
                st.metric("Total Chunks", df['total_chunks'].sum())

            st.divider()

            # Visualizations
            col1, col2 = st.columns(2)

            with col1:
                # Category distribution
                if 'category' in df.columns:
                    category_counts = df['category'].value_counts()
                    fig = px.pie(
                        values=category_counts.values,
                        names=category_counts.index,
                        title="Documents by Category"
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                # File size distribution
                fig = px.histogram(
                    df,
                    x='file_size',
                    nbins=20,
                    title="File Size Distribution",
                    labels={'file_size': 'File Size (bytes)', 'count': 'Number of Documents'}
                )
                st.plotly_chart(fig, use_container_width=True)

            # Upload timeline
            if 'upload_date' in df.columns:
                df['upload_date_parsed'] = pd.to_datetime(df['upload_date'])
                df_sorted = df.sort_values('upload_date_parsed')

                fig = px.line(
                    x=df_sorted['upload_date_parsed'],
                    y=range(1, len(df_sorted) + 1),
                    title="Document Upload Timeline",
                    labels={'x': 'Upload Date', 'y': 'Cumulative Documents'}
                )
                st.plotly_chart(fig, use_container_width=True)

            # Extraction methods
            if 'extraction_method' in df.columns:
                method_counts = df['extraction_method'].value_counts()
                fig = px.bar(
                    x=method_counts.index,
                    y=method_counts.values,
                    title="Extraction Methods Used",
                    labels={'x': 'Method', 'y': 'Number of Documents'}
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No documents to analyze. Upload some PDFs first!")

    # Settings Tab
    with tab4:
        st.header("System Settings")

        # Collection management
        st.subheader("Collection Management")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Refresh Collection Stats", use_container_width=True):
                # Force refresh by updating session state
                if 'last_refresh' in st.session_state:
                    st.session_state.last_refresh = time.time()
                st.success("Stats refreshed!")
                st.rerun()

        with col2:
            if st.button("🗑️ Clear All Documents", type="secondary", use_container_width=True):
                if st.checkbox("I understand this will delete all documents"):
                    try:
                        client.delete_collection(PDF_COLLECTION_NAME)
                        initialize_collection(client, PDF_COLLECTION_NAME, vector_size=384)
                        st.success("All documents deleted!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error clearing collection: {e}")

        st.divider()

        # Export/Import
        st.subheader("Export & Backup")

        if st.button("📥 Export Document List to CSV"):
            if documents:
                df = pd.DataFrame(documents)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"pdf_documents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No documents to export")

        st.divider()

        # Storage info
        st.subheader("Storage Information")

        if UPLOAD_DIR.exists():
            files = list(UPLOAD_DIR.glob("*.pdf"))
            total_size = sum(f.stat().st_size for f in files) / (1024 * 1024)

            st.write(f"**Upload Directory:** `{UPLOAD_DIR}`")
            st.write(f"**Stored PDFs:** {len(files)} files")
            st.write(f"**Total Size:** {total_size:.1f} MB")

            if files and st.button("🧹 Clean Upload Directory"):
                for f in files:
                    f.unlink()
                st.success(f"Removed {len(files)} files")
                st.rerun()

    # Search history in sidebar
    if st.session_state.search_history:
        with st.sidebar:
            st.divider()
            st.subheader("🕐 Recent Searches")
            for hist_query in st.session_state.search_history[:5]:
                if st.button(f"↻ {hist_query}", key=f"hist_{hist_query}", use_container_width=True):
                    st.session_state.search_input = hist_query
                    st.rerun()


if __name__ == "__main__":
    main()