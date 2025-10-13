"""
Enhanced Streamlit application with PDF upload and indexing capabilities.

This app provides:
- PDF upload functionality
- Real-time document processing and indexing
- Semantic search across both uploaded and existing documents
- Document management interface
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

# Import PDF processor
from src.processing.pdf_processor import PDFProcessor, PDFContent


# Page configuration
st.set_page_config(
    page_title="Document Search with Upload",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def init_qdrant_client(host: str = "localhost", port: int = 6333):
    """Initialize and cache Qdrant client."""
    return QdrantClient(host=host, port=port, timeout=5.0)


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
        extract_images=False,  # Disable image extraction for now
        ocr_language='eng'
    )


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_collection_info(_client: QdrantClient, collection_name: str):
    """Get and cache collection information."""
    try:
        info = _client.get_collection(collection_name)
        return {
            'status': 'connected',
            'points_count': info.points_count,
            'vectors_count': info.vectors_count if info.vectors_count else info.points_count,
            'status_color': info.status
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'points_count': 0,
            'vectors_count': 0
        }


def ensure_collection_exists(client: QdrantClient, collection_name: str, vector_size: int = 384):
    """Ensure the collection exists, create if it doesn't."""
    try:
        client.get_collection(collection_name)
    except:
        # Collection doesn't exist, create it
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
        st.info(f"Created new collection: {collection_name}")


@st.cache_data(ttl=60)  # Cache for 1 minute
def generate_embedding(_model: SentenceTransformer, text: str):
    """Generate embedding for text with caching."""
    embedding = _model.encode(
        text,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    )
    return embedding


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: The text to chunk
        chunk_size: Maximum size of each chunk in characters
        overlap: Number of characters to overlap between chunks

    Returns:
        List of text chunks
    """
    # Split into sentences (simple approach)
    sentences = text.replace('\n\n', '\n').split('. ')

    chunks = []
    current_chunk = []
    current_size = 0

    for sentence in sentences:
        sentence = sentence.strip() + '.'
        sentence_size = len(sentence)

        if current_size + sentence_size > chunk_size and current_chunk:
            # Join current chunk and add to chunks
            chunk_text = ' '.join(current_chunk)
            chunks.append(chunk_text)

            # Create overlap by keeping last few sentences
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
        else:
            current_chunk.append(sentence)
            current_size += sentence_size

    # Add remaining chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


def process_and_index_pdf(
    pdf_file,
    pdf_processor: PDFProcessor,
    model: SentenceTransformer,
    client: QdrantClient,
    collection_name: str,
    chunk_size: int = 512,
    overlap: int = 50
) -> Dict:
    """
    Process a PDF file and index it into Qdrant.

    Args:
        pdf_file: Uploaded PDF file from Streamlit
        pdf_processor: PDF processor instance
        model: Embedding model
        client: Qdrant client
        collection_name: Name of the collection
        chunk_size: Size of text chunks
        overlap: Overlap between chunks

    Returns:
        Processing statistics
    """
    stats = {
        'filename': pdf_file.name,
        'file_size': pdf_file.size,
        'chunks_created': 0,
        'pages_processed': 0,
        'tables_extracted': 0,
        'processing_time': 0,
        'indexing_time': 0,
        'errors': []
    }

    try:
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_file.getvalue())
            tmp_path = Path(tmp_file.name)

        # Process PDF
        start_time = time.time()
        pdf_content = pdf_processor.process_pdf(tmp_path)
        stats['processing_time'] = time.time() - start_time

        # Update stats
        stats['pages_processed'] = len(pdf_content.page_contents)
        stats['tables_extracted'] = len(pdf_content.tables)

        # Chunk the text
        chunks = chunk_text(pdf_content.text, chunk_size, overlap)
        stats['chunks_created'] = len(chunks)

        # Generate document ID
        doc_id = hashlib.md5(f"{pdf_file.name}_{datetime.now()}".encode()).hexdigest()

        # Index chunks into Qdrant
        start_time = time.time()
        points = []

        for i, chunk in enumerate(chunks):
            # Generate embedding
            embedding = generate_embedding(model, chunk)

            # Create point
            point_id = hashlib.md5(f"{doc_id}_{i}".encode()).hexdigest()

            # Prepare metadata
            metadata = {
                'content': chunk,
                'document_id': doc_id,
                'document_name': pdf_file.name,
                'chunk_index': i,
                'total_chunks': len(chunks),
                'source': 'uploaded',
                'upload_date': datetime.now().isoformat(),
                'extraction_method': pdf_content.extraction_method,
                'page_count': stats['pages_processed'],
                'file_size': pdf_file.size
            }

            # Add document metadata if available
            if pdf_content.metadata:
                metadata['pdf_metadata'] = {
                    'title': pdf_content.metadata.get('title', ''),
                    'author': pdf_content.metadata.get('author', ''),
                    'creation_date': str(pdf_content.metadata.get('creation_date', ''))
                }

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

        # Clean up temp file
        tmp_path.unlink()

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
    source_filter: Optional[str] = None
) -> Dict:
    """Perform semantic search on documents with optional source filtering."""
    timing = {}

    # Generate query embedding
    start_time = time.time()
    query_embedding = generate_embedding(model, query)
    timing['embedding'] = time.time() - start_time

    # Perform Qdrant search
    start_time = time.time()

    search_params = SearchParams(
        hnsw_ef=128,
        exact=exact
    )

    # Build filter conditions if needed
    filter_conditions = None
    if source_filter and source_filter != "all":
        filter_conditions = {
            "must": [
                {"key": "source", "match": {"value": source_filter}}
            ]
        }

    results = client.query_points(
        collection_name=collection_name,
        query=query_embedding.tolist(),
        limit=limit,
        score_threshold=score_threshold,
        with_payload=True,
        search_params=search_params,
        query_filter=filter_conditions
    ).points

    timing['search'] = time.time() - start_time
    timing['total'] = timing['embedding'] + timing['search']

    # Format results
    formatted_results = []
    for result in results:
        # Handle both PubMed and uploaded documents
        if result.payload.get('source') == 'uploaded':
            formatted_results.append({
                'score': result.score,
                'document_name': result.payload.get('document_name', 'Unknown'),
                'content': result.payload.get('content', ''),
                'chunk_index': result.payload.get('chunk_index', 0),
                'total_chunks': result.payload.get('total_chunks', 1),
                'source': 'uploaded',
                'upload_date': result.payload.get('upload_date', ''),
                'extraction_method': result.payload.get('extraction_method', ''),
                'pdf_metadata': result.payload.get('pdf_metadata', {})
            })
        else:
            # PubMed document
            formatted_results.append({
                'score': result.score,
                'abstract_id': result.payload.get('abstract_id', 'unknown'),
                'content': result.payload.get('content', ''),
                'labels': result.payload.get('labels', []),
                'source': result.payload.get('source', 'pubmed'),
                'num_sentences': result.payload.get('num_sentences', 0),
                'split': result.payload.get('split', 'unknown')
            })

    return {
        'results': formatted_results,
        'timing': timing,
        'count': len(formatted_results)
    }


def display_result_card(result: Dict, index: int):
    """Display a single result as an expandable card."""
    score_color = "🟢" if result['score'] > 0.7 else "🟡" if result['score'] > 0.5 else "🔴"

    # Different display for uploaded vs PubMed documents
    if result.get('source') == 'uploaded':
        title = f"{score_color} **Result {index}** - 📄 {result['document_name']} (Chunk {result['chunk_index'] + 1}/{result['total_chunks']})"
    else:
        title = f"{score_color} **Result {index}** - Abstract ID: {result.get('abstract_id', 'unknown')}"

    title += f" (Score: {result['score']:.4f})"

    with st.expander(title, expanded=(index <= 3)):
        # Create columns for metadata
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Relevance Score", f"{result['score']:.4f}")

        with col2:
            if result.get('source') == 'uploaded':
                st.metric("Source", "📄 Uploaded PDF")
            else:
                st.metric("Source", "📚 PubMed")

        with col3:
            if result.get('source') == 'uploaded':
                st.metric("Extraction", result.get('extraction_method', 'N/A'))
            else:
                st.metric("Dataset Split", result.get('split', 'unknown').upper())

        # Display additional metadata
        if result.get('source') == 'uploaded' and result.get('pdf_metadata'):
            metadata = result['pdf_metadata']
            if metadata.get('title'):
                st.write(f"**Title:** {metadata['title']}")
            if metadata.get('author'):
                st.write(f"**Author:** {metadata['author']}")
            if result.get('upload_date'):
                st.write(f"**Uploaded:** {result['upload_date'][:10]}")

        # Display labels for PubMed documents
        elif result.get('labels'):
            st.write("**Sections:**")
            labels_html = " ".join([
                f'<span style="background-color: #e1e4e8; padding: 3px 8px; '
                f'border-radius: 12px; margin-right: 5px; font-size: 0.9em;">{label}</span>'
                for label in result['labels']
            ])
            st.markdown(labels_html, unsafe_allow_html=True)

        # Display content
        st.write("**Content:**")
        st.text_area(
            "Content",
            value=result['content'],
            height=200,
            disabled=True,
            label_visibility="collapsed"
        )


def main():
    """Main Streamlit application."""

    # Header
    st.title("📚 Document Search with PDF Upload")
    st.markdown(
        "Upload your own PDFs and search across both your documents and the PubMed dataset"
    )

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Connection settings
        with st.expander("🔌 Connection Settings", expanded=False):
            host = st.text_input("Qdrant Host", value="localhost")
            port = st.number_input("Qdrant Port", value=6333, min_value=1, max_value=65535)
            collection_name = st.text_input("Collection Name", value="pubmed_documents")

        # Initialize clients
        try:
            client = init_qdrant_client(host, port)
            model = load_embedding_model()
            pdf_processor = init_pdf_processor()

            # Ensure collection exists
            ensure_collection_exists(client, collection_name, vector_size=384)

            model_loaded = True
        except Exception as e:
            st.error(f"Failed to initialize: {str(e)}")
            model_loaded = False
            return

        # PDF Upload Section
        st.header("📤 Upload PDFs")
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload one or more PDF files to index them for search"
        )

        # Chunking settings
        with st.expander("📄 Document Processing Settings"):
            chunk_size = st.slider(
                "Chunk Size (characters)",
                min_value=100,
                max_value=2000,
                value=512,
                step=50,
                help="Size of text chunks for indexing"
            )

            chunk_overlap = st.slider(
                "Chunk Overlap (characters)",
                min_value=0,
                max_value=200,
                value=50,
                step=10,
                help="Number of characters to overlap between chunks"
            )

            use_ocr = st.checkbox(
                "Enable OCR for scanned PDFs",
                value=True,
                help="Use OCR to extract text from scanned PDF images"
            )

        # Process uploaded files
        if uploaded_files and st.button("🚀 Process & Index PDFs", type="primary"):
            with st.spinner("Processing PDFs..."):
                total_stats = {
                    'total_files': len(uploaded_files),
                    'successful': 0,
                    'failed': 0,
                    'total_chunks': 0,
                    'total_pages': 0,
                    'total_time': 0
                }

                # Process each file
                progress_bar = st.progress(0)
                status_text = st.empty()

                for i, pdf_file in enumerate(uploaded_files):
                    status_text.text(f"Processing: {pdf_file.name}")

                    stats = process_and_index_pdf(
                        pdf_file=pdf_file,
                        pdf_processor=pdf_processor,
                        model=model,
                        client=client,
                        collection_name=collection_name,
                        chunk_size=chunk_size,
                        overlap=chunk_overlap
                    )

                    if not stats['errors']:
                        total_stats['successful'] += 1
                        total_stats['total_chunks'] += stats['chunks_created']
                        total_stats['total_pages'] += stats['pages_processed']
                        total_stats['total_time'] += stats['processing_time'] + stats['indexing_time']
                    else:
                        total_stats['failed'] += 1

                    progress_bar.progress((i + 1) / len(uploaded_files))

                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()

                # Show summary
                if total_stats['successful'] > 0:
                    st.success(f"✅ Successfully processed {total_stats['successful']} files")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Chunks", total_stats['total_chunks'])
                    with col2:
                        st.metric("Total Pages", total_stats['total_pages'])
                    with col3:
                        st.metric("Processing Time", f"{total_stats['total_time']:.1f}s")

                if total_stats['failed'] > 0:
                    st.warning(f"⚠️ Failed to process {total_stats['failed']} files")

                # Clear cache to reflect new documents
                get_collection_info.clear()

        # Search settings with visual controls
        st.subheader("🎛️ Search Controls")

        # Number of Documents Knob
        st.markdown("#### 📊 Documents to Return")
        max_results = st.select_slider(
            "",
            options=[1, 3, 5, 10, 15, 20, 25, 30, 40, 50],
            value=10,
            key="sidebar_doc_count"
        )
        # Visual indicator
        st.markdown(f"""
        <div style='text-align: center; padding: 8px; background: linear-gradient(90deg, #007bff, #00ff88);
                    border-radius: 10px; color: white; font-size: 1.2em; font-weight: bold;'>
            📄 {max_results} Documents
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Score Threshold Knob
        st.markdown("#### 🎯 Similarity Threshold")
        score_threshold = st.slider(
            "",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.05,
            format="%.2f",
            key="sidebar_score"
        )
        # Visual indicator with color coding
        if score_threshold == 0:
            threshold_text = "Show All Results"
            color = "#28a745"
        elif score_threshold < 0.5:
            threshold_text = f"Min: {score_threshold:.0%}"
            color = "#ffc107"
        else:
            threshold_text = f"Min: {score_threshold:.0%}"
            color = "#dc3545"

        st.markdown(f"""
        <div style='text-align: center; padding: 8px; background: {color};
                    border-radius: 10px; color: white; font-size: 1.2em; font-weight: bold;'>
            {threshold_text}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Additional Filters
        st.markdown("#### ⚙️ Filter Options")

        source_filter = st.selectbox(
            "Document Source",
            options=["all", "pubmed", "uploaded"],
            index=0,
            help="Filter search by document source"
        )

        exact_search = st.checkbox(
            "🎯 Exact Search Mode",
            value=False,
            help="Enable exact search (slower but 100% accurate)"
        )

        # Visual mode indicator
        search_mode = "🔴 Exact Mode" if exact_search else "🟢 Fast Mode"
        mode_color = "#dc3545" if exact_search else "#28a745"
        st.markdown(f"""
        <div style='text-align: center; padding: 6px; background: {mode_color};
                    border-radius: 8px; color: white; font-weight: bold;'>
            {search_mode}
        </div>
        """, unsafe_allow_html=True)

        # Collection info
        st.subheader("📊 Collection Info")
        if model_loaded:
            info = get_collection_info(client, collection_name)

            if info['status'] == 'connected':
                st.success("✅ Connected to Qdrant")
                st.metric("Total Documents", f"{info['points_count']:,}")

                # Try to get document statistics
                try:
                    # Sample query to get document counts by source
                    sample_results = client.scroll(
                        collection_name=collection_name,
                        limit=100,
                        with_payload=True
                    )[0]

                    sources = {}
                    for point in sample_results:
                        source = point.payload.get('source', 'unknown')
                        sources[source] = sources.get(source, 0) + 1

                    if sources:
                        st.write("**Document Sources:**")
                        for source, count in sources.items():
                            if source == 'uploaded':
                                st.write(f"  📄 Uploaded: ~{count}")
                            elif source == 'pubmed':
                                st.write(f"  📚 PubMed: ~{count}")
                            else:
                                st.write(f"  📖 {source}: ~{count}")
                except:
                    pass
            else:
                st.error(f"❌ Connection Error: {info.get('error', 'Unknown')}")

        # Sample queries
        st.subheader("💡 Sample Queries")
        sample_queries = [
            "machine learning in healthcare",
            "deep learning applications",
            "natural language processing",
            "computer vision techniques",
            "data preprocessing methods",
            "model evaluation metrics",
            "transfer learning",
            "neural network architectures"
        ]

        selected_sample = st.selectbox(
            "Try a sample query:",
            [""] + sample_queries,
            index=0
        )

    # Main content area
    col1, col2 = st.columns([3, 1])

    with col1:
        # Search input
        query = st.text_input(
            "🔍 Enter your search query:",
            value=selected_sample if selected_sample else "",
            placeholder="Search across all documents...",
            key="search_query"
        )

    with col2:
        # Search button
        st.write("")  # Add spacing
        search_button = st.button(
            "🚀 Search",
            type="primary",
            use_container_width=True,
            disabled=not model_loaded
        )

    # Search history in session state
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []

    # Perform search
    if (search_button or query) and query.strip() and model_loaded:

        # Add to search history
        if query not in st.session_state.search_history:
            st.session_state.search_history.insert(0, query)
            st.session_state.search_history = st.session_state.search_history[:10]

        # Progress bar
        search_mode = "🎯 Exact Search" if exact_search else "⚡ Fast Search"
        filter_text = f" (filtering: {source_filter})" if source_filter != "all" else ""
        with st.spinner(f"{search_mode}{filter_text} in progress..."):
            # Perform search
            search_result = search_documents(
                client=client,
                model=model,
                query=query,
                collection_name=collection_name,
                limit=max_results,
                score_threshold=score_threshold if score_threshold > 0 else None,
                exact=exact_search,
                source_filter=source_filter if source_filter != "all" else None
            )

        # Display timing information
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "⚡ Total Time",
                f"{search_result['timing']['total']*1000:.1f} ms"
            )
        with col2:
            st.metric(
                "🧠 Embedding Time",
                f"{search_result['timing']['embedding']*1000:.1f} ms"
            )
        with col3:
            st.metric(
                "🔍 Search Time",
                f"{search_result['timing']['search']*1000:.1f} ms"
            )
        with col4:
            mode_label = "🎯 Exact" if exact_search else "⚡ Fast"
            st.metric("Search Mode", mode_label)

        st.divider()

        # Display results
        if search_result['count'] > 0:
            st.success(f"Found {search_result['count']} relevant documents")

            # Create tabs for different views
            tab1, tab2, tab3 = st.tabs(["📄 Results", "📊 Analysis", "📈 Score Distribution"])

            with tab1:
                # Display each result as a card
                for i, result in enumerate(search_result['results'], 1):
                    display_result_card(result, i)

            with tab2:
                # Analysis view
                st.subheader("Results Analysis")

                # Create DataFrame for analysis
                df = pd.DataFrame(search_result['results'])

                # Score statistics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Avg Score", f"{df['score'].mean():.4f}")
                with col2:
                    st.metric("Max Score", f"{df['score'].max():.4f}")
                with col3:
                    st.metric("Min Score", f"{df['score'].min():.4f}")
                with col4:
                    st.metric("Std Dev", f"{df['score'].std():.4f}")

                # Source distribution
                if 'source' in df.columns:
                    source_counts = df['source'].value_counts()

                    fig = px.pie(
                        values=source_counts.values,
                        names=source_counts.index,
                        title="Document Sources in Results"
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with tab3:
                # Score distribution
                st.subheader("Score Distribution")

                df = pd.DataFrame(search_result['results'])

                # Create histogram
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=df['score'],
                    nbinsx=20,
                    name='Score Distribution',
                    marker_color='lightblue',
                    opacity=0.7
                ))

                fig.update_layout(
                    title="Distribution of Relevance Scores",
                    xaxis_title="Relevance Score",
                    yaxis_title="Number of Documents",
                    showlegend=False,
                    height=400
                )

                st.plotly_chart(fig, use_container_width=True)

                # Score vs Rank plot
                fig2 = px.line(
                    x=range(1, len(df) + 1),
                    y=df['score'],
                    title="Score vs Rank",
                    labels={'x': 'Rank', 'y': 'Relevance Score'},
                    markers=True
                )
                fig2.update_layout(height=400)
                st.plotly_chart(fig2, use_container_width=True)

        else:
            st.warning("No results found. Try adjusting your query or lowering the score threshold.")

    # Search history
    if st.session_state.search_history:
        with st.sidebar:
            st.subheader("🕐 Recent Searches")
            for hist_query in st.session_state.search_history:
                if st.button(f"↻ {hist_query}", key=f"hist_{hist_query}"):
                    st.session_state.search_query = hist_query
                    st.rerun()

    # Footer
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: gray; font-size: 0.9em;'>
        Document Search with PDF Upload | Powered by Qdrant & Sentence Transformers<br>
        Upload your PDFs and search across all documents
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()