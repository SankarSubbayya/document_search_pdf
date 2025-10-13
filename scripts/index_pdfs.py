#!/usr/bin/env python
"""
PDF Document Indexing Script

This script processes PDF files and indexes them into a vector database
for semantic search and retrieval.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Optional
import click
from dotenv import load_dotenv
from tqdm import tqdm
import yaml

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.processing.pdf_processor import PDFProcessor, process_pdf_directory
from src.processing.document_processor import DocumentProcessor
from src.storage.qdrant_manager import QdrantManager
from src.embeddings.embedding_generator import EmbeddingGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class PDFIndexer:
    """Main class for indexing PDF documents."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the PDF indexer with configuration."""
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Initialize components
        self.pdf_processor = PDFProcessor(
            use_ocr=True,
            extract_tables=True,
            extract_images=True
        )

        self.doc_processor = DocumentProcessor(
            chunk_size=self.config['processing']['chunking']['chunk_size'],
            chunk_overlap=self.config['processing']['chunking']['chunk_overlap'],
            use_semantic_chunking=self.config['processing']['chunking']['strategy'] == 'semantic'
        )

        self.embedding_generator = EmbeddingGenerator(
            model_name=self.config['embeddings']['model'],
            device=self.config['embeddings']['device']
        )

        self.vector_store = QdrantManager(
            collection_name=self.config['storage']['vector_store']['collection_name'],
            embedding_dim=self.config['embeddings']['models']['all-MiniLM-L6-v2']['dimensions']
        )

    def index_pdf(self, pdf_path: Path, category: Optional[str] = None) -> bool:
        """
        Index a single PDF file.

        Args:
            pdf_path: Path to the PDF file
            category: Optional category for the document

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Indexing PDF: {pdf_path}")

            # Extract PDF content
            pdf_content = self.pdf_processor.process_pdf(pdf_path)

            # Check if document has sufficient content
            if len(pdf_content.text.strip()) < 100:
                logger.warning(f"Insufficient content in {pdf_path}")
                return False

            # Process with document processor for chunking
            processed_doc = self.doc_processor.process_document(
                pdf_path,
                category=category,
                additional_metadata={
                    'extraction_method': pdf_content.extraction_method,
                    'tables_count': len(pdf_content.tables),
                    'images_count': len(pdf_content.images),
                    'is_scanned': pdf_content.metadata.get('ocr_used', False)
                }
            )

            # Generate embeddings for chunks
            chunk_texts = [chunk['content'] for chunk in processed_doc.chunks]
            embeddings = self.embedding_generator.generate_embeddings(chunk_texts)

            # Prepare documents for vector store
            documents = []
            for i, (chunk, embedding) in enumerate(zip(processed_doc.chunks, embeddings)):
                documents.append({
                    'id': f"{processed_doc.document_id}_chunk_{i}",
                    'content': chunk['content'],
                    'embedding': embedding,
                    'metadata': {
                        **chunk['metadata'],
                        'document_id': processed_doc.document_id,
                        'file_path': str(pdf_path),
                        'chunk_index': i,
                        'pdf_metadata': pdf_content.metadata
                    }
                })

            # Add to vector store
            self.vector_store.add_documents(documents)

            logger.info(f"Successfully indexed {pdf_path} with {len(documents)} chunks")
            return True

        except Exception as e:
            logger.error(f"Error indexing {pdf_path}: {e}")
            return False

    def index_directory(
        self,
        directory_path: Path,
        category: Optional[str] = None,
        recursive: bool = True,
        max_files: Optional[int] = None
    ) -> dict:
        """
        Index all PDFs in a directory.

        Args:
            directory_path: Directory containing PDFs
            category: Category for all documents
            recursive: Process subdirectories
            max_files: Maximum number of files to process

        Returns:
            Statistics dictionary
        """
        # Find all PDF files
        if recursive:
            pdf_files = list(directory_path.rglob("*.pdf"))
        else:
            pdf_files = list(directory_path.glob("*.pdf"))

        # Limit files if specified
        if max_files:
            pdf_files = pdf_files[:max_files]

        logger.info(f"Found {len(pdf_files)} PDF files to index")

        # Statistics
        stats = {
            'total_files': len(pdf_files),
            'successful': 0,
            'failed': 0,
            'scanned_pdfs': 0
        }

        # Process each PDF
        for pdf_file in tqdm(pdf_files, desc="Indexing PDFs"):
            # Check if scanned
            if self.pdf_processor.is_scanned_pdf(pdf_file):
                stats['scanned_pdfs'] += 1
                logger.info(f"Processing scanned PDF with OCR: {pdf_file.name}")

            # Index the PDF
            if self.index_pdf(pdf_file, category):
                stats['successful'] += 1
            else:
                stats['failed'] += 1

        # Log summary
        logger.info("\n" + "="*50)
        logger.info("Indexing Complete!")
        logger.info(f"Total PDFs: {stats['total_files']}")
        logger.info(f"Successfully indexed: {stats['successful']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(f"Scanned PDFs (OCR used): {stats['scanned_pdfs']}")

        return stats


@click.command()
@click.option(
    '--input-dir',
    '-i',
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help='Directory containing PDF files'
)
@click.option(
    '--category',
    '-c',
    type=str,
    default=None,
    help='Category for the documents'
)
@click.option(
    '--recursive',
    '-r',
    is_flag=True,
    default=True,
    help='Process subdirectories recursively'
)
@click.option(
    '--max-files',
    '-m',
    type=int,
    default=None,
    help='Maximum number of files to process'
)
@click.option(
    '--config',
    type=click.Path(exists=True),
    default='config.yaml',
    help='Path to configuration file'
)
@click.option(
    '--reset-collection',
    is_flag=True,
    default=False,
    help='Reset the vector collection before indexing'
)
def main(
    input_dir: Path,
    category: Optional[str],
    recursive: bool,
    max_files: Optional[int],
    config: str,
    reset_collection: bool
):
    """
    Index PDF documents into a vector database for semantic search.

    This script processes PDF files (including scanned PDFs with OCR),
    extracts text content, tables, and metadata, then chunks the content
    and stores it in a vector database for efficient retrieval.
    """
    logger.info("Starting PDF indexing process...")
    logger.info(f"Input directory: {input_dir}")

    # Initialize indexer
    indexer = PDFIndexer(config_path=config)

    # Reset collection if requested
    if reset_collection:
        logger.warning("Resetting vector collection...")
        indexer.vector_store.reset_collection()

    # Index the directory
    stats = indexer.index_directory(
        directory_path=input_dir,
        category=category,
        recursive=recursive,
        max_files=max_files
    )

    # Print final statistics
    click.echo("\n" + "="*50)
    click.echo(click.style("PDF Indexing Complete!", fg='green', bold=True))
    click.echo(f"Total PDFs processed: {stats['total_files']}")
    click.echo(f"Successfully indexed: {stats['successful']}")
    click.echo(f"Failed: {stats['failed']}")
    click.echo(f"Scanned PDFs (OCR): {stats['scanned_pdfs']}")

    # Check collection status
    collection_info = indexer.vector_store.get_collection_info()
    click.echo(f"\nVector Collection Status:")
    click.echo(f"  - Total documents: {collection_info.get('vectors_count', 0)}")
    click.echo(f"  - Collection size: {collection_info.get('points_count', 0)} chunks")

    # Exit with appropriate code
    sys.exit(0 if stats['failed'] == 0 else 1)


if __name__ == "__main__":
    main()