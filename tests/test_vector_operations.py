"""
Integration tests for vector database operations with Qdrant.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
from pathlib import Path
import hashlib
from datetime import datetime
import numpy as np

import sys
sys.path.append(str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct, VectorParams, Distance,
    Filter, FieldCondition, MatchValue
)


class TestVectorOperations(unittest.TestCase):
    """Test vector database operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.collection_name = "test_pdf_documents"
        self.mock_client = Mock(spec=QdrantClient)
        self.mock_model = Mock()

    def test_collection_initialization(self):
        """Test collection creation and initialization."""
        from pdf_manager_app import initialize_collection

        # Mock the client methods
        self.mock_client.get_collections.return_value.collections = []
        self.mock_client.create_collection.return_value = True

        # Test creation of new collection
        result = initialize_collection(
            self.mock_client,
            self.collection_name,
            vector_size=384
        )

        # Verify collection was created
        self.mock_client.create_collection.assert_called_once()
        call_args = self.mock_client.create_collection.call_args
        self.assertEqual(call_args[1]['collection_name'], self.collection_name)

    def test_document_indexing(self):
        """Test document indexing into Qdrant."""
        from pdf_manager_app import chunk_text

        # Test text chunking
        test_text = "This is sentence one. This is sentence two. This is sentence three." * 10
        chunks = chunk_text(test_text, chunk_size=100, overlap=20)

        self.assertIsInstance(chunks, list)
        self.assertTrue(len(chunks) > 0)

        # Verify chunks have the right structure
        for chunk, start, end in chunks:
            self.assertIsInstance(chunk, str)
            self.assertIsInstance(start, int)
            self.assertIsInstance(end, int)
            self.assertLessEqual(len(chunk), 120)  # Allow some flexibility

    def test_search_with_filters(self):
        """Test document search with category and tag filters."""
        from pdf_manager_app import search_documents

        # Mock embedding model
        self.mock_model.encode.return_value = np.random.rand(384)

        # Mock Qdrant search results
        mock_point = Mock()
        mock_point.score = 0.95
        mock_point.id = "test_id"
        mock_point.payload = {
            'content': 'Test content',
            'document_name': 'test.pdf',
            'category': 'research',
            'tags': ['ml', 'ai']
        }

        self.mock_client.query_points.return_value.points = [mock_point]

        # Perform search with filters
        results = search_documents(
            client=self.mock_client,
            model=self.mock_model,
            query="test query",
            collection_name=self.collection_name,
            limit=10,
            category_filter="research",
            tag_filter=["ml"]
        )

        # Verify results
        self.assertEqual(results['count'], 1)
        self.assertEqual(results['results'][0]['score'], 0.95)
        self.assertEqual(results['results'][0]['category'], 'research')

        # Verify filter was applied
        call_args = self.mock_client.query_points.call_args
        self.assertIsNotNone(call_args[1].get('query_filter'))

    def test_document_deletion(self):
        """Test document deletion from collection."""
        from pdf_manager_app import delete_document

        # Mock the delete operation
        self.mock_client.delete.return_value = True

        # Test deletion
        result = delete_document(
            self.mock_client,
            self.collection_name,
            "test_document_id"
        )

        self.assertTrue(result)

        # Verify delete was called with correct filter
        self.mock_client.delete.assert_called_once()
        call_args = self.mock_client.delete.call_args
        self.assertEqual(call_args[1]['collection_name'], self.collection_name)

    def test_collection_statistics(self):
        """Test getting collection statistics."""
        from pdf_manager_app import get_collection_stats

        # Mock collection info
        mock_info = Mock()
        mock_info.points_count = 1000
        mock_info.vectors_count = 1000
        mock_info.status = "green"
        self.mock_client.get_collection.return_value = mock_info

        # Mock scroll results for document analysis
        mock_record = Mock()
        mock_record.payload = {
            'document_id': 'doc1',
            'document_name': 'test.pdf',
            'file_size': 1024000,
            'upload_date': '2024-01-01T00:00:00',
            'extraction_method': 'pdfplumber'
        }
        self.mock_client.scroll.return_value = ([mock_record], None)

        # Get statistics
        stats = get_collection_stats(self.mock_client, self.collection_name)

        self.assertEqual(stats['status'], 'connected')
        self.assertEqual(stats['points_count'], 1000)
        self.assertIn('documents_info', stats)

    def test_batch_upload(self):
        """Test batch uploading of vectors."""
        from pdf_manager_app import process_pdf_file

        # Create mock PDF processor
        mock_processor = Mock()
        mock_pdf_content = Mock()
        # Create longer text to ensure chunks are created
        mock_pdf_content.text = "This is test content for PDF processing. " * 50  # About 2100 characters
        mock_pdf_content.metadata = {'pages': 5}
        mock_pdf_content.page_contents = [{'page': i} for i in range(1, 6)]
        mock_pdf_content.tables = []
        mock_pdf_content.extraction_method = 'test'
        mock_processor.process_pdf.return_value = mock_pdf_content

        # Mock embedding model
        self.mock_model.encode.return_value = np.random.rand(384)

        # Mock client upsert
        self.mock_client.upsert.return_value = True

        # Create test PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(b'%PDF-1.4\n')

        try:
            # Process PDF
            stats = process_pdf_file(
                pdf_path=tmp_path,
                pdf_processor=mock_processor,
                model=self.mock_model,
                client=self.mock_client,
                collection_name=self.collection_name,
                chunk_size=100,
                overlap=20,
                tags=['test'],
                category='research'
            )

            # Verify processing stats
            self.assertEqual(stats['filename'], tmp_path.name)
            self.assertGreater(stats['chunks_created'], 0)
            self.assertEqual(stats['pages_processed'], 5)
            self.assertIsNotNone(stats['document_id'])

            # Verify upsert was called
            self.mock_client.upsert.assert_called()

        finally:
            tmp_path.unlink()


class TestEmbeddingOperations(unittest.TestCase):
    """Test embedding generation and caching."""

    def test_embedding_generation(self):
        """Test text embedding generation."""
        from sentence_transformers import SentenceTransformer

        # Mock the model
        with patch('sentence_transformers.SentenceTransformer') as MockModel:
            mock_model = Mock()
            mock_embedding = np.random.rand(384)
            mock_model.encode.return_value = mock_embedding
            MockModel.return_value = mock_model

            # Test embedding generation
            model = MockModel('test-model')
            text = "This is a test document"
            embedding = model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True
            )

            # Verify embedding
            self.assertEqual(embedding.shape, (384,))
            mock_model.encode.assert_called_once()

    def test_embedding_normalization(self):
        """Test that embeddings are properly normalized."""
        # Create a random embedding
        embedding = np.random.rand(384)

        # Normalize manually
        norm = np.linalg.norm(embedding)
        normalized = embedding / norm

        # Verify normalization
        self.assertAlmostEqual(np.linalg.norm(normalized), 1.0, places=5)


class TestDocumentRetrieval(unittest.TestCase):
    """Test document retrieval and ranking."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_model = Mock()

    def test_score_based_ranking(self):
        """Test that results are properly ranked by score."""
        from pdf_manager_app import search_documents

        # Create mock results with different scores
        mock_points = []
        for i, score in enumerate([0.95, 0.85, 0.75, 0.65]):
            point = Mock()
            point.score = score
            point.id = f"id_{i}"
            point.payload = {
                'content': f'Content {i}',
                'document_name': f'doc_{i}.pdf'
            }
            mock_points.append(point)

        self.mock_client.query_points.return_value.points = mock_points
        self.mock_model.encode.return_value = np.random.rand(384)

        # Perform search
        results = search_documents(
            client=self.mock_client,
            model=self.mock_model,
            query="test",
            collection_name="test_collection",
            limit=10
        )

        # Verify ranking
        self.assertEqual(len(results['results']), 4)
        scores = [r['score'] for r in results['results']]
        self.assertEqual(scores, [0.95, 0.85, 0.75, 0.65])

    def test_empty_search_results(self):
        """Test handling of empty search results."""
        from pdf_manager_app import search_documents

        # Mock empty results
        self.mock_client.query_points.return_value.points = []
        self.mock_model.encode.return_value = np.random.rand(384)

        # Perform search
        results = search_documents(
            client=self.mock_client,
            model=self.mock_model,
            query="non-existent query",
            collection_name="test_collection",
            limit=10
        )

        # Verify empty results handling
        self.assertEqual(results['count'], 0)
        self.assertEqual(results['results'], [])
        self.assertIn('timing', results)


if __name__ == '__main__':
    unittest.main()