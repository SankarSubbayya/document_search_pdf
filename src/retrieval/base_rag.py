"""
Document Search RAG Implementation

This module provides a complete RAG (Retrieval Augmented Generation) implementation
for document search, including embedding, vector storage, and generation capabilities.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from openai import OpenAI
from tqdm import tqdm
import yaml
from rich.console import Console
from rich.table import Table

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()


@dataclass
class Document:
    """Represents a document with its content and metadata."""
    id: str
    content: str
    title: str
    category: Optional[str] = None
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentSearchRAG:
    """Main RAG implementation for document search."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the RAG system with configuration."""
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.embedder = SentenceTransformer(
            self.config.get("embedding_model", "all-MiniLM-L6-v2")
        )
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            path=self.config.get("qdrant_path", "./qdrant_db")
        )
        
        # Initialize OpenAI client
        self.openai_client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        self.collection_name = self.config.get("collection_name", "documents")
        self.embedding_dim = self.embedder.get_sentence_embedding_dimension()
        
        # Create collection if it doesn't exist
        self._create_collection_if_not_exists()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def _create_collection_if_not_exists(self):
        """Create Qdrant collection if it doesn't exist."""
        collections = self.qdrant_client.get_collections().collections
        collection_names = [col.name for col in collections]
        
        if self.collection_name not in collection_names:
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection: {self.collection_name}")
    
    def embed_text(self, text: str) -> np.ndarray:
        """Convert text to embedding vector."""
        return self.embedder.encode(text, convert_to_numpy=True)
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Convert multiple texts to embedding vectors."""
        return self.embedder.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    
    def index_documents(self, documents: List[Document], batch_size: int = 100):
        """Index documents into the vector database."""
        console.print(f"[bold green]Indexing {len(documents)} documents...[/bold green]")
        
        # Prepare texts for embedding
        texts = [doc.content for doc in documents]
        
        # Generate embeddings
        embeddings = self.embed_texts(texts)
        
        # Prepare points for Qdrant
        points = []
        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            payload = {
                "id": doc.id,
                "title": doc.title,
                "content": doc.content,
                "category": doc.category,
                "source": doc.source,
            }
            if doc.metadata:
                payload.update(doc.metadata)
            
            points.append(
                PointStruct(
                    id=i,
                    vector=embedding.tolist(),
                    payload=payload
                )
            )
        
        # Upload to Qdrant in batches
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
        
        console.print(f"[bold green]Successfully indexed {len(documents)} documents![/bold green]")
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        category_filter: Optional[str] = None
    ) -> List[Tuple[Document, float]]:
        """Search for documents similar to the query."""
        # Embed the query
        query_embedding = self.embed_text(query)
        
        # Prepare filter if category is specified
        query_filter = None
        if category_filter:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="category",
                        match=MatchValue(value=category_filter)
                    )
                ]
            )
        
        # Search in Qdrant
        results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding.tolist(),
            limit=top_k,
            query_filter=query_filter
        )
        
        # Convert results to Document objects
        documents_with_scores = []
        for result in results:
            doc = Document(
                id=result.payload["id"],
                title=result.payload["title"],
                content=result.payload["content"],
                category=result.payload.get("category"),
                source=result.payload.get("source"),
                metadata={k: v for k, v in result.payload.items() 
                         if k not in ["id", "title", "content", "category", "source"]}
            )
            documents_with_scores.append((doc, result.score))
        
        return documents_with_scores
    
    def generate_answer(
        self,
        query: str,
        context_documents: List[Document],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7
    ) -> str:
        """Generate an answer using the LLM with retrieved context."""
        # Prepare context
        context = "\n\n".join([
            f"Document {i+1} (Title: {doc.title}):\n{doc.content}"
            for i, doc in enumerate(context_documents)
        ])
        
        # Prepare system prompt
        system_prompt = self.config.get(
            "system_prompt",
            "You are a helpful assistant that answers questions based on the provided context. "
            "Always cite the document number when using information from a specific document."
        )
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {query}\n\n"
                          f"Please answer the question based on the provided context."
            }
        ]
        
        # Generate response
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    def rag_query(
        self,
        query: str,
        top_k: int = 5,
        category_filter: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        show_sources: bool = True
    ) -> Dict[str, Any]:
        """Complete RAG pipeline: search and generate answer."""
        # Search for relevant documents
        search_results = self.search(query, top_k, category_filter)
        
        if not search_results:
            return {
                "answer": "I couldn't find any relevant documents to answer your question.",
                "sources": []
            }
        
        # Extract documents from search results
        documents = [doc for doc, _ in search_results]
        
        # Generate answer
        answer = self.generate_answer(query, documents, model, temperature)
        
        # Prepare response
        response = {
            "answer": answer,
            "sources": []
        }
        
        if show_sources:
            # Create sources table
            table = Table(title="Retrieved Sources")
            table.add_column("Score", style="cyan")
            table.add_column("Title", style="magenta")
            table.add_column("Category", style="green")
            table.add_column("Preview", style="white")
            
            for doc, score in search_results:
                preview = doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
                table.add_row(
                    f"{score:.3f}",
                    doc.title,
                    doc.category or "N/A",
                    preview
                )
                
                response["sources"].append({
                    "title": doc.title,
                    "category": doc.category,
                    "score": score,
                    "content": doc.content
                })
            
            console.print(table)
        
        return response
    
    def load_documents_from_json(self, json_path: str) -> List[Document]:
        """Load documents from a JSON file."""
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        documents = []
        for item in data:
            doc = Document(
                id=item["id"],
                title=item["title"],
                content=item["content"],
                category=item.get("category"),
                source=item.get("source"),
                metadata=item.get("metadata", {})
            )
            documents.append(doc)
        
        return documents
    
    def clear_collection(self):
        """Clear all documents from the collection."""
        try:
            self.qdrant_client.delete_collection(self.collection_name)
            self._create_collection_if_not_exists()
            console.print(f"[bold yellow]Cleared collection: {self.collection_name}[/bold yellow]")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")


def main():
    """Example usage of the DocumentSearchRAG system."""
    # Initialize RAG system
    rag = DocumentSearchRAG()
    
    # Example: Create and index some sample documents
    sample_documents = [
        Document(
            id="1",
            title="Introduction to Machine Learning",
            content="Machine learning is a subset of artificial intelligence that focuses on the development of algorithms that can learn from and make predictions or decisions based on data.",
            category="AI/ML",
            source="tutorial"
        ),
        Document(
            id="2",
            title="Python Programming Basics",
            content="Python is a high-level, interpreted programming language known for its simplicity and readability. It's widely used in web development, data science, and automation.",
            category="Programming",
            source="tutorial"
        ),
        Document(
            id="3",
            title="Natural Language Processing",
            content="NLP is a field of AI that focuses on the interaction between computers and human language. It involves tasks like text classification, sentiment analysis, and language translation.",
            category="AI/ML",
            source="tutorial"
        ),
    ]
    
    # Index documents
    rag.index_documents(sample_documents)
    
    # Example query
    query = "What is machine learning?"
    console.print(f"\n[bold blue]Query:[/bold blue] {query}")
    
    # Perform RAG query
    result = rag.rag_query(query, top_k=3)
    
    console.print(f"\n[bold green]Answer:[/bold green]\n{result['answer']}")


if __name__ == "__main__":
    main()

