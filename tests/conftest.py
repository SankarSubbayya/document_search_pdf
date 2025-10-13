"""
Pytest configuration and shared fixtures for testing.
"""

import pytest
import tempfile
from pathlib import Path
import shutil
from unittest.mock import Mock, MagicMock
import numpy as np
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"
TEST_DATA_DIR.mkdir(exist_ok=True)


@pytest.fixture(scope="session")
def test_data_dir():
    """Provide test data directory."""
    return TEST_DATA_DIR


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    # Cleanup
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_pdf_content():
    """Create sample PDF content for testing."""
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Arial >> >> >> /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF Content) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000274 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
365
%%EOF"""


@pytest.fixture
def sample_pdf_file(temp_dir, sample_pdf_content):
    """Create a sample PDF file for testing."""
    pdf_path = temp_dir / "test_document.pdf"
    pdf_path.write_bytes(sample_pdf_content)
    return pdf_path


@pytest.fixture
def mock_qdrant_client():
    """Create a mock Qdrant client."""
    client = Mock()

    # Mock collection info
    collection_info = Mock()
    collection_info.points_count = 100
    collection_info.vectors_count = 100
    collection_info.status = "green"
    client.get_collection.return_value = collection_info

    # Mock query results
    mock_point = Mock()
    mock_point.score = 0.95
    mock_point.id = "test_id"
    mock_point.payload = {
        'content': 'Test content',
        'document_name': 'test.pdf',
        'category': 'general',
        'tags': ['test']
    }
    client.query_points.return_value.points = [mock_point]

    # Mock upsert
    client.upsert.return_value = True

    # Mock delete
    client.delete.return_value = True

    return client


@pytest.fixture
def mock_embedding_model():
    """Create a mock embedding model."""
    model = Mock()

    # Mock encode method
    def encode_mock(text, **kwargs):
        # Return consistent embeddings based on text length
        np.random.seed(len(text))
        return np.random.rand(384)

    model.encode = Mock(side_effect=encode_mock)
    model.get_sentence_embedding_dimension.return_value = 384

    return model


@pytest.fixture
def mock_pdf_processor():
    """Create a mock PDF processor."""
    from src.processing.pdf_processor import PDFContent

    processor = Mock()

    # Mock PDF content
    content = PDFContent(
        text="This is test content from the PDF. " * 50,
        tables=[],
        images=[],
        metadata={
            'title': 'Test PDF',
            'author': 'Test Author',
            'pages': 5
        },
        page_contents=[
            {'page': i, 'text': f'Page {i} content', 'char_count': 100}
            for i in range(1, 6)
        ],
        extraction_method='pdfplumber'
    )

    processor.process_pdf.return_value = content
    processor.is_scanned_pdf.return_value = False
    processor.extract_pdf_metadata.return_value = content.metadata

    return processor


@pytest.fixture
def sample_documents():
    """Create sample document data for testing."""
    return [
        {
            'document_id': 'doc1',
            'document_name': 'research_paper.pdf',
            'upload_date': '2024-01-01T12:00:00',
            'page_count': 15,
            'total_chunks': 30,
            'file_size': 2048000,
            'category': 'research',
            'tags': ['ml', 'nlp', 'ai'],
            'extraction_method': 'pdfplumber'
        },
        {
            'document_id': 'doc2',
            'document_name': 'legal_contract.pdf',
            'upload_date': '2024-01-02T14:30:00',
            'page_count': 25,
            'total_chunks': 50,
            'file_size': 3072000,
            'category': 'legal',
            'tags': ['contract', 'agreement'],
            'extraction_method': 'pypdf2'
        },
        {
            'document_id': 'doc3',
            'document_name': 'technical_manual.pdf',
            'upload_date': '2024-01-03T09:15:00',
            'page_count': 100,
            'total_chunks': 200,
            'file_size': 10240000,
            'category': 'technical',
            'tags': ['documentation', 'manual'],
            'extraction_method': 'pymupdf'
        }
    ]


@pytest.fixture
def sample_search_results():
    """Create sample search results for testing."""
    return [
        {
            'score': 0.95,
            'document_name': 'research_paper.pdf',
            'content': 'Machine learning algorithms have revolutionized...',
            'chunk_index': 5,
            'total_chunks': 30,
            'category': 'research',
            'tags': ['ml', 'ai']
        },
        {
            'score': 0.87,
            'document_name': 'technical_manual.pdf',
            'content': 'The neural network architecture consists of...',
            'chunk_index': 42,
            'total_chunks': 200,
            'category': 'technical',
            'tags': ['documentation']
        },
        {
            'score': 0.76,
            'document_name': 'research_paper.pdf',
            'content': 'Deep learning models require substantial...',
            'chunk_index': 12,
            'total_chunks': 30,
            'category': 'research',
            'tags': ['ml', 'nlp']
        }
    ]


@pytest.fixture
def mock_streamlit():
    """Create mock Streamlit components."""
    mock_st = MagicMock()

    # Mock common Streamlit functions
    mock_st.title = Mock()
    mock_st.header = Mock()
    mock_st.write = Mock()
    mock_st.error = Mock()
    mock_st.success = Mock()
    mock_st.info = Mock()
    mock_st.warning = Mock()

    # Mock input components
    mock_st.text_input = Mock(return_value="test input")
    mock_st.number_input = Mock(return_value=10)
    mock_st.selectbox = Mock(return_value="option1")
    mock_st.slider = Mock(return_value=50)
    mock_st.checkbox = Mock(return_value=False)
    mock_st.button = Mock(return_value=False)
    mock_st.file_uploader = Mock(return_value=None)

    # Mock layout components
    mock_st.columns = Mock(return_value=[Mock(), Mock()])
    mock_st.tabs = Mock(return_value=[Mock(), Mock(), Mock()])
    mock_st.expander = Mock()
    mock_st.container = Mock()
    mock_st.sidebar = MagicMock()

    # Mock display components
    mock_st.metric = Mock()
    mock_st.plotly_chart = Mock()
    mock_st.dataframe = Mock()
    mock_st.download_button = Mock()

    # Mock session state
    mock_st.session_state = MagicMock()
    mock_st.session_state.processed_files = []
    mock_st.session_state.search_history = []

    return mock_st


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test."""
    # Create necessary directories
    TEST_DATA_DIR.mkdir(exist_ok=True)
    (TEST_DATA_DIR / "pdfs").mkdir(exist_ok=True)
    (TEST_DATA_DIR / "outputs").mkdir(exist_ok=True)

    yield

    # Cleanup can be added here if needed


@pytest.fixture
def app_config():
    """Provide test configuration."""
    return {
        'vector_store': {
            'collection_name': 'test_pdf_documents',
            'host': 'localhost',
            'port': 6333,
            'vector_size': 384
        },
        'processing': {
            'chunking': {
                'default_size': 512,
                'default_overlap': 50,
                'min_size': 100,
                'max_size': 2000
            },
            'pdf': {
                'use_ocr': False,  # Disable for tests
                'extract_tables': True,
                'extract_images': False
            }
        },
        'categories': [
            'general', 'research', 'documentation',
            'legal', 'financial', 'technical'
        ]
    }


# Markers for different test types
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.slow = pytest.mark.slow
pytest.mark.requires_qdrant = pytest.mark.requires_qdrant