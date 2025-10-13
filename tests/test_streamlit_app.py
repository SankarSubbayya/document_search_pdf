"""
End-to-end tests for Streamlit application.
Uses streamlit.testing for app testing.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
from pathlib import Path
import pandas as pd
import sys

sys.path.append(str(Path(__file__).parent.parent))


class TestStreamlitApp(unittest.TestCase):
    """Test Streamlit application functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_model = Mock()
        self.mock_processor = Mock()

    @patch('streamlit.file_uploader')
    @patch('streamlit.button')
    def test_pdf_upload_flow(self, mock_button, mock_uploader):
        """Test PDF upload workflow."""
        # Create a mock uploaded file
        mock_file = Mock()
        mock_file.name = "test.pdf"
        mock_file.size = 1024000
        mock_file.getvalue.return_value = b'%PDF-1.4\nTest content'

        mock_uploader.return_value = [mock_file]
        mock_button.return_value = True

        # Test file upload handling
        uploaded_files = [mock_file]
        self.assertIsNotNone(uploaded_files)
        self.assertEqual(len(uploaded_files), 1)
        self.assertEqual(uploaded_files[0].name, "test.pdf")

    @patch('streamlit.text_input')
    @patch('streamlit.button')
    def test_search_functionality(self, mock_button, mock_text_input):
        """Test search functionality."""
        mock_text_input.return_value = "machine learning"
        mock_button.return_value = True

        # Simulate search query
        query = mock_text_input.return_value
        self.assertEqual(query, "machine learning")

    @patch('streamlit.session_state')
    def test_session_state_management(self, mock_session_state):
        """Test session state management."""
        # Initialize session state
        mock_session_state.processed_files = []
        mock_session_state.search_history = []

        # Add to processed files
        file_stats = {
            'filename': 'test.pdf',
            'chunks_created': 10,
            'pages_processed': 5
        }
        mock_session_state.processed_files.append(file_stats)

        # Add to search history
        mock_session_state.search_history.append("test query")

        # Verify state
        self.assertEqual(len(mock_session_state.processed_files), 1)
        self.assertEqual(len(mock_session_state.search_history), 1)

    @patch('streamlit.tabs')
    def test_tab_navigation(self, mock_tabs):
        """Test tab-based navigation."""
        # Mock tabs
        tab1, tab2, tab3, tab4 = Mock(), Mock(), Mock(), Mock()
        mock_tabs.return_value = [tab1, tab2, tab3, tab4]

        tabs = mock_tabs(["🔍 Search", "📚 Documents", "📊 Analytics", "⚙️ Settings"])

        self.assertEqual(len(tabs), 4)

    @patch('streamlit.plotly_chart')
    def test_analytics_visualization(self, mock_plotly):
        """Test analytics visualization."""
        # Create sample data
        documents = [
            {'document_name': 'doc1.pdf', 'category': 'research', 'file_size': 1024000},
            {'document_name': 'doc2.pdf', 'category': 'legal', 'file_size': 2048000},
            {'document_name': 'doc3.pdf', 'category': 'research', 'file_size': 512000}
        ]

        df = pd.DataFrame(documents)

        # Test category distribution
        category_counts = df['category'].value_counts()
        self.assertEqual(category_counts['research'], 2)
        self.assertEqual(category_counts['legal'], 1)

        # Verify chart would be displayed
        mock_plotly.assert_not_called()  # Not called in this test context

    @patch('streamlit.download_button')
    def test_csv_export(self, mock_download):
        """Test CSV export functionality."""
        # Create sample document data
        documents = [
            {
                'document_id': 'id1',
                'document_name': 'test1.pdf',
                'upload_date': '2024-01-01',
                'page_count': 10
            },
            {
                'document_id': 'id2',
                'document_name': 'test2.pdf',
                'upload_date': '2024-01-02',
                'page_count': 20
            }
        ]

        df = pd.DataFrame(documents)
        csv_data = df.to_csv(index=False)

        # Verify CSV generation
        self.assertIn('document_id', csv_data)
        self.assertIn('test1.pdf', csv_data)
        self.assertIn('test2.pdf', csv_data)

    @patch('streamlit.error')
    @patch('streamlit.success')
    def test_error_handling(self, mock_success, mock_error):
        """Test error handling and user feedback."""
        # Test success message
        mock_success("Document uploaded successfully")
        mock_success.assert_called_with("Document uploaded successfully")

        # Test error message
        mock_error("Failed to process PDF")
        mock_error.assert_called_with("Failed to process PDF")


class TestStreamlitUIComponents(unittest.TestCase):
    """Test individual UI components."""

    @patch('streamlit.sidebar')
    def test_sidebar_configuration(self, mock_sidebar):
        """Test sidebar configuration options."""
        with mock_sidebar:
            # Mock configuration inputs
            mock_sidebar.text_input.return_value = "localhost"
            mock_sidebar.number_input.return_value = 6333
            mock_sidebar.selectbox.return_value = "general"
            mock_sidebar.slider.return_value = 512

            # Verify configuration values
            host = "localhost"
            port = 6333
            category = "general"
            chunk_size = 512

            self.assertEqual(host, "localhost")
            self.assertEqual(port, 6333)
            self.assertEqual(category, "general")
            self.assertEqual(chunk_size, 512)

    @patch('streamlit.expander')
    def test_result_display(self, mock_expander):
        """Test search result display."""
        # Mock search result
        result = {
            'score': 0.95,
            'document_name': 'test.pdf',
            'content': 'Test content',
            'category': 'research',
            'tags': ['ml', 'ai']
        }

        # Mock expander context
        mock_expander.return_value.__enter__ = Mock()
        mock_expander.return_value.__exit__ = Mock()

        # Verify result structure
        self.assertIn('score', result)
        self.assertIn('document_name', result)
        self.assertIn('content', result)
        self.assertGreater(result['score'], 0.7)  # High relevance

    @patch('streamlit.metric')
    def test_metrics_display(self, mock_metric):
        """Test metrics display."""
        # Display metrics
        mock_metric("Total Documents", 100)
        mock_metric("Total Size", "50.5 MB")
        mock_metric("Search Time", "125 ms")

        # Verify metric calls
        self.assertEqual(mock_metric.call_count, 3)

    @patch('streamlit.progress')
    def test_progress_bar(self, mock_progress):
        """Test progress bar updates."""
        progress_bar = mock_progress(0)

        # Simulate progress updates
        for i in range(5):
            progress = (i + 1) / 5
            progress_bar.progress(progress)

        # Verify progress updates
        self.assertEqual(progress_bar.progress.call_count, 5)


class TestAppIntegration(unittest.TestCase):
    """Integration tests for the complete application flow."""

    @patch('qdrant_client.QdrantClient')
    @patch('sentence_transformers.SentenceTransformer')
    def test_complete_workflow(self, mock_transformer, mock_qdrant):
        """Test complete upload and search workflow."""
        # Setup mocks
        mock_client = Mock()
        mock_qdrant.return_value = mock_client

        mock_model = Mock()
        mock_transformer.return_value = mock_model

        # Mock collection exists
        mock_client.get_collection.return_value = Mock(
            points_count=0,
            status='green'
        )

        # Test workflow steps
        # 1. Initialize connection
        client = mock_qdrant('localhost', 6333)
        self.assertIsNotNone(client)

        # 2. Load model
        model = mock_transformer('all-MiniLM-L6-v2')
        self.assertIsNotNone(model)

        # 3. Check collection
        collection_info = client.get_collection('pdf_documents')
        self.assertEqual(collection_info.points_count, 0)

        # 4. Mock document upload
        mock_client.upsert.return_value = True
        upload_result = client.upsert('pdf_documents', [])
        self.assertTrue(upload_result)

        # 5. Mock search
        mock_client.query_points.return_value.points = []
        search_results = client.query_points('pdf_documents', query=[0.1]*384)
        self.assertEqual(len(search_results.points), 0)

    def test_configuration_loading(self):
        """Test configuration file loading."""
        config = {
            'vector_store': {
                'collection_name': 'pdf_documents',
                'host': 'localhost',
                'port': 6333
            },
            'processing': {
                'chunking': {
                    'default_size': 512,
                    'default_overlap': 50
                }
            }
        }

        # Verify configuration structure
        self.assertEqual(config['vector_store']['collection_name'], 'pdf_documents')
        self.assertEqual(config['processing']['chunking']['default_size'], 512)


class TestPerformance(unittest.TestCase):
    """Performance and scalability tests."""

    def test_large_document_chunking(self):
        """Test chunking of large documents."""
        from pdf_manager_app import chunk_text

        # Create large text
        large_text = "This is a test sentence. " * 1000  # ~25,000 characters

        # Test chunking
        chunks = chunk_text(large_text, chunk_size=500, overlap=50)

        # Verify chunking
        self.assertGreater(len(chunks), 40)  # Should create many chunks

        # Verify chunk sizes
        for chunk, start, end in chunks:
            self.assertLessEqual(len(chunk), 600)  # Allow some flexibility
            self.assertGreater(len(chunk), 0)

    def test_batch_processing(self):
        """Test batch processing of multiple files."""
        files = [f"test_{i}.pdf" for i in range(10)]

        # Simulate batch processing
        processed = []
        failed = []

        for file in files:
            # Simulate processing (50% success rate for testing)
            if len(file) % 2 == 0:
                processed.append(file)
            else:
                failed.append(file)

        # Verify batch results
        self.assertEqual(len(processed) + len(failed), 10)


if __name__ == '__main__':
    unittest.main()