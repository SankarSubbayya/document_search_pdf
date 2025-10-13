"""Document Search RAG - A simple tutorial for Retrieval Augmented Generation."""

# Make imports optional to avoid dependency issues
try:
    from .retrieval.base_rag import DocumentSearchRAG, Document
    __all__ = ["DocumentSearchRAG", "Document"]
except ImportError:
    # If retrieval modules aren't available, that's OK for apps that don't need them
    __all__ = []
    DocumentSearchRAG = None
    Document = None

__version__ = "0.1.0"

