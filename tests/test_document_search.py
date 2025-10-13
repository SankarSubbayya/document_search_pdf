"""Tests for the Document Search RAG implementation."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
import os

from src.retrieval.base_rag import Document, DocumentSearchRAG


class TestDocument:
    """Test the Document dataclass."""
    
    def test_document_creation(self):
        """Test creating a document with all fields."""
        doc = Document(
            id="test_1",
            title="Test Title",
            content="Test content",
            category="Test Category",
            source="Test Source",
            metadata={"key": "value"}
        )
        
        assert doc.id == "test_1"
        assert doc.title == "Test Title"
        assert doc.content == "Test content"
        assert doc.category == "Test Category"
        assert doc.source == "Test Source"
        assert doc.metadata == {"key": "value"}
    
    def test_document_minimal(self):
        """Test creating a document with minimal fields."""
        doc = Document(
            id="test_2",
            title="Test Title",
            content="Test content"
        )
        
        assert doc.id == "test_2"
        assert doc.title == "Test Title"
        assert doc.content == "Test content"
        assert doc.category is None
        assert doc.source is None
        assert doc.metadata is None


class TestDocumentSearchRAG:
    """Test the DocumentSearchRAG class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a temporary config file."""
        config = {
            "embedding_model": "all-MiniLM-L6-v2",
            "qdrant_path": "./test_qdrant_db",
            "collection_name": "test_documents",
            "system_prompt": "Test prompt"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(config, f)
            return f.name
    
    @pytest.fixture
    def rag_instance(self, mock_config):
        """Create a RAG instance with mocked dependencies."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            with patch('src.retrieval.base_rag.QdrantClient'):
                with patch('src.retrieval.base_rag.SentenceTransformer') as mock_st:
                    # Mock the embedding dimension method
                    mock_embedder = Mock()
                    mock_embedder.get_sentence_embedding_dimension = Mock(return_value=384)
                    mock_st.return_value = mock_embedder
                    
                    rag = DocumentSearchRAG(config_path=mock_config)
                    return rag
    
    def test_initialization(self, rag_instance):
        """Test RAG initialization."""
        assert rag_instance.collection_name == "test_documents"
        assert rag_instance.embedding_dim == 384
        assert rag_instance.config["system_prompt"] == "Test prompt"
    
    def test_embed_text(self, rag_instance):
        """Test text embedding."""
        # Mock the embedding
        mock_embedding = np.random.rand(384)
        rag_instance.embedder.encode = Mock(return_value=mock_embedding)
        
        result = rag_instance.embed_text("Test text")
        
        rag_instance.embedder.encode.assert_called_once_with("Test text", convert_to_numpy=True)
        np.testing.assert_array_equal(result, mock_embedding)
    
    def test_embed_texts(self, rag_instance):
        """Test batch text embedding."""
        texts = ["Text 1", "Text 2", "Text 3"]
        mock_embeddings = np.random.rand(3, 384)
        rag_instance.embedder.encode = Mock(return_value=mock_embeddings)
        
        result = rag_instance.embed_texts(texts)
        
        rag_instance.embedder.encode.assert_called_once_with(
            texts, 
            convert_to_numpy=True, 
            show_progress_bar=True
        )
        np.testing.assert_array_equal(result, mock_embeddings)
    
    def test_index_documents(self, rag_instance):
        """Test document indexing."""
        documents = [
            Document(id="1", title="Doc 1", content="Content 1"),
            Document(id="2", title="Doc 2", content="Content 2", category="Test")
        ]
        
        mock_embeddings = np.random.rand(2, 384)
        rag_instance.embedder.encode = Mock(return_value=mock_embeddings)
        rag_instance.qdrant_client.upsert = Mock()
        
        rag_instance.index_documents(documents)
        
        # Check embeddings were created
        rag_instance.embedder.encode.assert_called_once()
        
        # Check upsert was called
        rag_instance.qdrant_client.upsert.assert_called()
        
        # Verify the points structure
        call_args = rag_instance.qdrant_client.upsert.call_args
        assert call_args[1]["collection_name"] == "test_documents"
        points = call_args[1]["points"]
        assert len(points) == 2
        assert points[0].payload["id"] == "1"
        assert points[1].payload["category"] == "Test"
    
    def test_search(self, rag_instance):
        """Test document search."""
        query = "test query"
        mock_embedding = np.random.rand(384)
        rag_instance.embedder.encode = Mock(return_value=mock_embedding)
        
        # Mock search results
        mock_results = [
            Mock(
                payload={"id": "1", "title": "Doc 1", "content": "Content 1"},
                score=0.95
            ),
            Mock(
                payload={"id": "2", "title": "Doc 2", "content": "Content 2", "category": "Test"},
                score=0.85
            )
        ]
        rag_instance.qdrant_client.search = Mock(return_value=mock_results)
        
        results = rag_instance.search(query, top_k=2)
        
        # Verify search was called correctly
        rag_instance.qdrant_client.search.assert_called_once()
        call_args = rag_instance.qdrant_client.search.call_args[1]
        assert call_args["collection_name"] == "test_documents"
        assert call_args["limit"] == 2
        
        # Verify results
        assert len(results) == 2
        assert results[0][0].id == "1"
        assert results[0][1] == 0.95
        assert results[1][0].category == "Test"
    
    def test_generate_answer(self, rag_instance):
        """Test answer generation."""
        with patch('src.retrieval.base_rag.OpenAI') as mock_openai:
            # Mock the OpenAI response
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Generated answer"))]
            mock_openai.return_value.chat.completions.create.return_value = mock_response
            
            # Re-initialize with mocked OpenAI
            rag_instance.openai_client = mock_openai()
            
            documents = [
                Document(id="1", title="Doc 1", content="Content 1"),
                Document(id="2", title="Doc 2", content="Content 2")
            ]
            
            answer = rag_instance.generate_answer("Test query", documents)
            
            assert answer == "Generated answer"
            
            # Verify the call
            create_call = rag_instance.openai_client.chat.completions.create
            create_call.assert_called_once()
            call_args = create_call.call_args[1]
            assert call_args["model"] == "gpt-3.5-turbo"
            assert len(call_args["messages"]) == 2
    
    def test_rag_query(self, rag_instance):
        """Test complete RAG query."""
        # Mock search results
        mock_doc = Document(id="1", title="Test Doc", content="Test content")
        rag_instance.search = Mock(return_value=[(mock_doc, 0.95)])
        
        # Mock answer generation
        rag_instance.generate_answer = Mock(return_value="Test answer")
        
        with patch('src.retrieval.base_rag.Console'):
            result = rag_instance.rag_query("Test query", show_sources=False)
        
        assert result["answer"] == "Test answer"
        assert len(result["sources"]) == 0
        
        # Verify calls
        rag_instance.search.assert_called_once_with("Test query", 5, None)
        rag_instance.generate_answer.assert_called_once()
    
    def test_load_documents_from_json(self, rag_instance):
        """Test loading documents from JSON."""
        test_data = [
            {
                "id": "1",
                "title": "Title 1",
                "content": "Content 1",
                "category": "Category 1"
            },
            {
                "id": "2",
                "title": "Title 2",
                "content": "Content 2",
                "metadata": {"key": "value"}
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            documents = rag_instance.load_documents_from_json(temp_path)
            
            assert len(documents) == 2
            assert documents[0].id == "1"
            assert documents[0].category == "Category 1"
            assert documents[1].metadata == {"key": "value"}
        finally:
            os.unlink(temp_path)
    
    def test_clear_collection(self, rag_instance):
        """Test clearing the collection."""
        rag_instance.qdrant_client.delete_collection = Mock()
        rag_instance._create_collection_if_not_exists = Mock()
        
        with patch('src.retrieval.base_rag.Console'):
            rag_instance.clear_collection()
        
        rag_instance.qdrant_client.delete_collection.assert_called_once_with("test_documents")
        rag_instance._create_collection_if_not_exists.assert_called_once()
    
    def test_search_with_category_filter(self, rag_instance):
        """Test search with category filtering."""
        mock_embedding = np.random.rand(384)
        rag_instance.embedder.encode = Mock(return_value=mock_embedding)
        rag_instance.qdrant_client.search = Mock(return_value=[])
        
        rag_instance.search("query", category_filter="Test Category")
        
        # Verify filter was applied
        call_args = rag_instance.qdrant_client.search.call_args[1]
        assert call_args["query_filter"] is not None
        
    def test_error_handling(self, rag_instance):
        """Test error handling in various scenarios."""
        # Test with no search results
        rag_instance.search = Mock(return_value=[])
        
        with patch('src.retrieval.base_rag.Console'):
            result = rag_instance.rag_query("No results query")
        
        assert "couldn't find any relevant documents" in result["answer"].lower()
        assert len(result["sources"]) == 0

