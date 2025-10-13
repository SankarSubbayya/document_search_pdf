"""Retrieval and RAG module for document search."""

from .base_rag import DocumentSearchRAG

# Make enhanced_rag optional since it depends on document_processor
try:
    from .enhanced_rag import EnhancedDocumentRAG
    __all__ = ["DocumentSearchRAG", "EnhancedDocumentRAG"]
except ImportError:
    # Enhanced RAG requires optional dependencies (docling)
    __all__ = ["DocumentSearchRAG"]
    EnhancedDocumentRAG = None