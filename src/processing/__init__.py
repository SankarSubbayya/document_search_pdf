"""Document processing module with docling and chonkie integration."""

# Make docling imports optional - only import if needed
try:
    from .document_processor import DocumentProcessor, ProcessedDocument
    __all__ = ["DocumentProcessor", "ProcessedDocument", "PDFProcessor", "PDFContent"]
except ImportError:
    # If docling is not available, only expose PDF processor
    __all__ = ["PDFProcessor", "PDFContent"]

# PDF processor is always available
from .pdf_processor import PDFProcessor, PDFContent