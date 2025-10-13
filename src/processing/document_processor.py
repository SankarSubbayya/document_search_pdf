"""
Advanced document processing pipeline using docling and chonkie.

This module provides comprehensive document parsing capabilities including:
- Text extraction from various document formats
- Table and image extraction
- Intelligent document chunking
- Metadata preservation
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import DoclingDocument
from chonkie import SemanticChunker, TokenChunker
from chonkie.embeddings import SentenceTransformerEmbeddings
import numpy as np
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ProcessedDocument:
    """Represents a fully processed document with all extracted content."""

    document_id: str
    file_path: str
    title: str
    content: str
    tables: List[Dict[str, Any]]
    images: List[Dict[str, Any]]
    chunks: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    processing_timestamp: str
    file_hash: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


class DocumentProcessor:
    """
    Advanced document processor using docling for parsing and chonkie for chunking.

    Handles extraction of text, tables, images, and metadata from documents,
    then intelligently chunks the content for optimal RAG performance.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        use_semantic_chunking: bool = True,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """
        Initialize the document processor.

        Args:
            chunk_size: Target size for document chunks
            chunk_overlap: Overlap between chunks
            use_semantic_chunking: Use semantic chunking vs token-based
            embedding_model: Model for semantic chunking
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.use_semantic_chunking = use_semantic_chunking

        # Initialize docling converter
        self.converter = DocumentConverter(
            allowed_formats=[
                InputFormat.PDF,
                InputFormat.DOCX,
                InputFormat.HTML,
                InputFormat.PPTX,
                InputFormat.IMAGE,
                InputFormat.MD,
                InputFormat.ASCIIDOC
            ]
        )

        # Initialize chunker
        if use_semantic_chunking:
            embeddings = SentenceTransformerEmbeddings(
                model=embedding_model
            )
            self.chunker = SemanticChunker(
                embedding_model=embeddings,
                chunk_size=chunk_size,
                threshold=0.5
            )
        else:
            self.chunker = TokenChunker(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )

        logger.info(f"Initialized DocumentProcessor with {embedding_model}")

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file for deduplication."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def process_document(
        self,
        file_path: Union[str, Path],
        extract_tables: bool = True,
        extract_images: bool = True,
        category: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> ProcessedDocument:
        """
        Process a single document extracting all content and metadata.

        Args:
            file_path: Path to the document
            extract_tables: Whether to extract tables
            extract_images: Whether to extract images
            category: Optional category for the document
            additional_metadata: Additional metadata to include

        Returns:
            ProcessedDocument with all extracted content
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        logger.info(f"Processing document: {file_path}")

        # Calculate file hash for deduplication
        file_hash = self._calculate_file_hash(str(file_path))

        # Convert document using docling
        result = self.converter.convert(str(file_path))
        doc: DoclingDocument = result.document

        # Extract main text content
        full_text = doc.export_to_text()

        # Extract tables
        tables = []
        if extract_tables and hasattr(doc, 'tables'):
            for table in doc.tables:
                tables.append({
                    'content': table.to_dataframe().to_dict() if hasattr(table, 'to_dataframe') else str(table),
                    'caption': getattr(table, 'caption', ''),
                    'position': getattr(table, 'position', None)
                })

        # Extract images
        images = []
        if extract_images and hasattr(doc, 'figures'):
            for figure in doc.figures:
                images.append({
                    'caption': getattr(figure, 'caption', ''),
                    'position': getattr(figure, 'position', None),
                    'type': getattr(figure, 'type', 'image')
                })

        # Extract metadata
        metadata = {
            'file_name': file_path.name,
            'file_size': file_path.stat().st_size,
            'file_type': file_path.suffix.lower(),
            'category': category,
            'page_count': getattr(doc, 'page_count', None),
            'language': getattr(doc, 'language', None),
            'author': getattr(doc, 'author', None),
            'creation_date': getattr(doc, 'creation_date', None),
            **(additional_metadata or {})
        }

        # Chunk the document
        chunks = self._chunk_document(full_text, metadata)

        # Create document ID
        document_id = f"{file_path.stem}_{file_hash[:8]}"

        return ProcessedDocument(
            document_id=document_id,
            file_path=str(file_path),
            title=getattr(doc, 'title', file_path.stem),
            content=full_text,
            tables=tables,
            images=images,
            chunks=chunks,
            metadata=metadata,
            processing_timestamp=datetime.utcnow().isoformat(),
            file_hash=file_hash
        )

    def _chunk_document(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Chunk document text using configured chunking strategy.

        Args:
            text: Document text to chunk
            metadata: Document metadata to include with chunks

        Returns:
            List of chunks with metadata
        """
        if not text.strip():
            return []

        # Use chonkie to create chunks
        chunks = self.chunker.chunk(text)

        # Format chunks with metadata
        formatted_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_dict = {
                'chunk_id': f"{metadata.get('file_name', 'unknown')}_{i}",
                'chunk_index': i,
                'content': chunk.text if hasattr(chunk, 'text') else str(chunk),
                'start_index': getattr(chunk, 'start_index', None),
                'end_index': getattr(chunk, 'end_index', None),
                'metadata': {
                    **metadata,
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                }
            }
            formatted_chunks.append(chunk_dict)

        return formatted_chunks

    def process_directory(
        self,
        directory_path: Union[str, Path],
        file_patterns: Optional[List[str]] = None,
        recursive: bool = True,
        max_documents: Optional[int] = None,
        skip_duplicates: bool = True
    ) -> List[ProcessedDocument]:
        """
        Process all documents in a directory.

        Args:
            directory_path: Path to directory containing documents
            file_patterns: File patterns to match (e.g., ['*.pdf', '*.docx'])
            recursive: Process subdirectories recursively
            max_documents: Maximum number of documents to process
            skip_duplicates: Skip files with same hash

        Returns:
            List of processed documents
        """
        directory_path = Path(directory_path)
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        # Default file patterns
        if file_patterns is None:
            file_patterns = ['*.pdf', '*.docx', '*.html', '*.md', '*.txt']

        # Find all matching files
        files = []
        for pattern in file_patterns:
            if recursive:
                files.extend(directory_path.rglob(pattern))
            else:
                files.extend(directory_path.glob(pattern))

        # Limit number of documents if specified
        if max_documents:
            files = files[:max_documents]

        logger.info(f"Found {len(files)} documents to process")

        # Process documents
        processed_docs = []
        seen_hashes = set()

        for file_path in tqdm(files, desc="Processing documents"):
            try:
                # Skip if duplicate
                if skip_duplicates:
                    file_hash = self._calculate_file_hash(str(file_path))
                    if file_hash in seen_hashes:
                        logger.info(f"Skipping duplicate: {file_path}")
                        continue
                    seen_hashes.add(file_hash)

                # Process document
                doc = self.process_document(file_path)
                processed_docs.append(doc)

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue

        logger.info(f"Successfully processed {len(processed_docs)} documents")
        return processed_docs

    def save_processed_documents(
        self,
        documents: List[ProcessedDocument],
        output_path: Union[str, Path],
        format: str = "json"
    ):
        """
        Save processed documents to file.

        Args:
            documents: List of processed documents
            output_path: Path to save file
            format: Output format ('json' or 'jsonl')
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            with open(output_path, 'w') as f:
                json.dump(
                    [doc.to_dict() for doc in documents],
                    f,
                    indent=2,
                    default=str
                )
        elif format == "jsonl":
            with open(output_path, 'w') as f:
                for doc in documents:
                    f.write(json.dumps(doc.to_dict(), default=str) + '\n')
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Saved {len(documents)} documents to {output_path}")

    def load_processed_documents(
        self,
        input_path: Union[str, Path]
    ) -> List[ProcessedDocument]:
        """
        Load processed documents from file.

        Args:
            input_path: Path to input file

        Returns:
            List of processed documents
        """
        input_path = Path(input_path)

        documents = []
        if input_path.suffix == '.json':
            with open(input_path, 'r') as f:
                data = json.load(f)
                for doc_dict in data:
                    documents.append(ProcessedDocument(**doc_dict))
        elif input_path.suffix == '.jsonl':
            with open(input_path, 'r') as f:
                for line in f:
                    doc_dict = json.loads(line)
                    documents.append(ProcessedDocument(**doc_dict))

        logger.info(f"Loaded {len(documents)} documents from {input_path}")
        return documents