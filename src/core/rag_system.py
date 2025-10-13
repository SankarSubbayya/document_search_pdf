"""
Simplified RAG system interface.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path

from .pipeline import DocumentPipeline
from ..config import settings


class RAGSystem:
    """
    High-level interface for the Document Search RAG system.

    Provides simplified methods for common operations:
    - Document processing
    - Search
    - Question answering
    """

    def __init__(self):
        """Initialize the RAG system."""
        self.pipeline = DocumentPipeline()

    def add_documents(
        self,
        path: str,
        category: Optional[str] = None,
        max_documents: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Add documents to the system.

        Args:
            path: Path to documents or directory
            category: Optional category
            max_documents: Maximum documents to process

        Returns:
            Processing statistics
        """
        result = self.pipeline.process_documents(
            input_path=path,
            category=category,
            max_documents=max_documents
        )

        return {
            'success': len(result.errors) == 0,
            'documents_processed': result.documents_processed,
            'chunks_created': result.chunks_created,
            'tables_extracted': result.tables_extracted,
            'processing_time': f"{result.processing_time:.2f}s",
            'errors': result.errors
        }

    def search(
        self,
        query: str,
        limit: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents.

        Args:
            query: Search query
            limit: Number of results
            category: Optional category filter

        Returns:
            Search results
        """
        filters = {'category': category} if category else None
        results = self.pipeline.search(query, top_k=limit, filters=filters)

        # Simplify results for end users
        return [
            {
                'title': r.get('title', 'Unknown'),
                'content': r.get('content', ''),
                'score': r.get('score', 0),
                'source': Path(r.get('file_path', '')).name if r.get('file_path') else 'Unknown'
            }
            for r in results
        ]

    def ask(
        self,
        question: str,
        context_limit: int = 5,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Ask a question and get an answer.

        Args:
            question: Question to answer
            context_limit: Number of contexts to use
            temperature: Generation temperature

        Returns:
            Answer with sources
        """
        response = self.pipeline.generate_answer(
            query=question,
            top_k=context_limit,
            temperature=temperature
        )

        # Simplify response
        return {
            'answer': response.get('answer', 'No answer generated'),
            'sources': [
                {
                    'title': s.get('title', 'Unknown'),
                    'file': Path(s.get('file_path', '')).name if s.get('file_path') else 'Unknown',
                    'relevance': f"{s.get('score', 0):.2%}"
                }
                for s in response.get('sources', [])
            ],
            'query': question
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        stats = self.pipeline.get_statistics()

        return {
            'total_documents': stats['database'].get('total_documents', 0),
            'total_chunks': stats['database'].get('total_chunks', 0),
            'total_tables': stats['database'].get('total_tables', 0),
            'categories': stats['database'].get('categories', []),
            'vector_count': stats['vector_store'].get('points_count', 0),
            'index_status': stats['vector_store'].get('status', 'unknown')
        }

    def clear(self):
        """Clear all data from the system."""
        # Clear vector store
        self.pipeline.vector_store.delete_collection()
        self.pipeline.vector_store.create_collection()

        # Note: Database clearing would need to be implemented
        # For now, just log
        print("System cleared. Note: Database tables preserved for safety.")

    def close(self):
        """Close the system properly."""
        self.pipeline.close()