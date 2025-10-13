"""
Streamlit application for PubMed document search using Qdrant.

This app provides a fast, user-friendly interface for semantic search
across the PubMed 200k RCT dataset.
"""

import streamlit as st
import time
from typing import Dict, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from qdrant_client import QdrantClient
from qdrant_client.models import SearchParams
from sentence_transformers import SentenceTransformer


# Page configuration
st.set_page_config(
    page_title="PubMed Semantic Search",
    page_icon="🔬",
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


def search_documents(
    client: QdrantClient,
    model: SentenceTransformer,
    query: str,
    collection_name: str,
    limit: int = 10,
    score_threshold: Optional[float] = None,
    exact: bool = False
) -> Dict:
    """Perform semantic search on documents."""
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

    results = client.query_points(
        collection_name=collection_name,
        query=query_embedding.tolist(),
        limit=limit,
        score_threshold=score_threshold,
        with_payload=True,
        search_params=search_params
    ).points

    timing['search'] = time.time() - start_time
    timing['total'] = timing['embedding'] + timing['search']

    # Format results
    formatted_results = []
    for result in results:
        formatted_results.append({
            'score': result.score,
            'abstract_id': result.payload.get('abstract_id', 'unknown'),
            'content': result.payload.get('content', ''),
            'labels': result.payload.get('labels', []),
            'source': result.payload.get('source', 'unknown'),
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

    with st.expander(
        f"{score_color} **Result {index}** - Abstract ID: {result['abstract_id']} "
        f"(Score: {result['score']:.4f})",
        expanded=(index <= 3)  # Expand first 3 results
    ):
        # Create two columns for metadata
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Relevance Score", f"{result['score']:.4f}")

        with col2:
            st.metric("Sentences", result.get('num_sentences', 'N/A'))

        with col3:
            st.metric("Dataset Split", result.get('split', 'unknown').upper())

        # Display labels as tags
        if result['labels']:
            st.write("**Sections:**")
            labels_html = " ".join([
                f'<span style="background-color: #e1e4e8; padding: 3px 8px; '
                f'border-radius: 12px; margin-right: 5px; font-size: 0.9em;">{label}</span>'
                for label in result['labels']
            ])
            st.markdown(labels_html, unsafe_allow_html=True)

        # Display content
        st.write("**Abstract Content:**")
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
    st.title("🔬 PubMed Semantic Search")
    st.markdown(
        "Fast semantic search across the PubMed 200k RCT dataset using Qdrant vector database"
    )

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Connection settings
        with st.expander("🔌 Connection Settings", expanded=False):
            host = st.text_input("Qdrant Host", value="localhost")
            port = st.number_input("Qdrant Port", value=6333, min_value=1, max_value=65535)
            collection_name = st.text_input("Collection Name", value="pubmed_documents")

        # Search settings
        st.subheader("🔍 Search Settings")
        max_results = st.slider(
            "Maximum Results",
            min_value=1,
            max_value=50,
            value=10,
            step=1
        )

        score_threshold = st.slider(
            "Minimum Score Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.05,
            help="Only show results with score above this threshold (0 = show all)"
        )

        exact_search = st.checkbox(
            "🎯 Exact Search Mode",
            value=False,
            help="Enable exact search (slower but 100% accurate). Fast mode uses HNSW approximation (faster, ~95% accurate)."
        )

        # Initialize clients
        try:
            client = init_qdrant_client(host, port)
            model = load_embedding_model()
            model_loaded = True
        except Exception as e:
            st.error(f"Failed to initialize: {str(e)}")
            model_loaded = False
            return

        # Collection info
        st.subheader("📊 Collection Info")
        if model_loaded:
            info = get_collection_info(client, collection_name)

            if info['status'] == 'connected':
                st.success("✅ Connected to Qdrant")
                st.metric("Documents", f"{info['points_count']:,}")
                st.metric("Collection Status", info['status_color'].upper())
            else:
                st.error(f"❌ Connection Error: {info.get('error', 'Unknown')}")

        # Add sample queries
        st.subheader("💡 Sample Queries")
        sample_queries = [
            "HIV treatment effectiveness",
            "diabetes prevention strategies",
            "cancer immunotherapy clinical trials",
            "COVID-19 vaccine efficacy",
            "hypertension management",
            "mental health interventions",
            "cardiovascular disease prevention",
            "antibiotic resistance"
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
            placeholder="e.g., HIV treatment, cancer immunotherapy, diabetes prevention...",
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
        with st.spinner(f"{search_mode} in progress..."):
            # Perform search
            search_result = search_documents(
                client=client,
                model=model,
                query=query,
                collection_name=collection_name,
                limit=max_results,
                score_threshold=score_threshold if score_threshold > 0 else None,
                exact=exact_search
            )

        # Display timing information and search mode
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
            mode_color = "blue" if exact_search else "green"
            st.markdown(
                f"**Search Mode**<br><span style='color: {mode_color}; font-size: 1.5em;'>{mode_label}</span>",
                unsafe_allow_html=True
            )

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

                # Labels distribution
                if 'labels' in df.columns:
                    all_labels = []
                    for labels_list in df['labels']:
                        all_labels.extend(labels_list)

                    if all_labels:
                        label_counts = pd.Series(all_labels).value_counts()

                        fig = px.bar(
                            x=label_counts.index,
                            y=label_counts.values,
                            title="Section Distribution in Results",
                            labels={'x': 'Section', 'y': 'Count'},
                            color=label_counts.values,
                            color_continuous_scale='viridis'
                        )
                        st.plotly_chart(fig, use_container_width=True)

            with tab3:
                # Score distribution
                st.subheader("Score Distribution")

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
        PubMed Semantic Search | Powered by Qdrant & Sentence Transformers<br>
        Dataset: PubMed 200k RCT | Model: all-MiniLM-L6-v2
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()