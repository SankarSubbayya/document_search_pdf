#!/usr/bin/env python3
"""
Example script for processing documents using docling and chonkie.

This script demonstrates:
1. Processing a directory of documents (PDFs, DOCX, etc.)
2. Extracting text, tables, and images
3. Intelligent chunking with chonkie
4. Storing in database
5. Indexing in vector store
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import argparse
import logging
from rich.console import Console
from rich.progress import track
from rich.table import Table

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.processing.document_processor import DocumentProcessor
from src.retrieval.enhanced_rag import EnhancedDocumentRAG
from src.storage.database_manager import DatabaseManager

# Load environment variables
load_dotenv()

# Initialize console for pretty output
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_document_corpus(
    input_dir: str,
    output_dir: str = "data/processed",
    use_database: bool = True,
    use_semantic_chunking: bool = True,
    chunk_size: int = 512,
    max_documents: int = None
):
    """
    Process a corpus of documents for RAG system.

    Args:
        input_dir: Directory containing documents
        output_dir: Directory for processed output
        use_database: Store in database
        use_semantic_chunking: Use semantic vs token chunking
        chunk_size: Target chunk size
        max_documents: Maximum documents to process
    """
    console.print("[bold cyan]Document Processing Pipeline[/bold cyan]")
    console.print(f"Input directory: {input_dir}")
    console.print(f"Output directory: {output_dir}")
    console.print(f"Chunking method: {'Semantic' if use_semantic_chunking else 'Token-based'}")
    console.print(f"Chunk size: {chunk_size}")

    # Initialize components
    console.print("\n[yellow]Initializing components...[/yellow]")

    # Document processor
    processor = DocumentProcessor(
        chunk_size=chunk_size,
        use_semantic_chunking=use_semantic_chunking
    )

    # Database manager (if enabled)
    db_manager = None
    if use_database:
        db_path = Path(output_dir) / "documents.db"
        db_manager = DatabaseManager(db_type="sqlite", db_path=str(db_path))
        console.print(f"Database: {db_path}")

    # Enhanced RAG system
    rag_system = EnhancedDocumentRAG(
        chunk_size=chunk_size,
        use_semantic_chunking=use_semantic_chunking
    )

    # Process documents
    console.print(f"\n[cyan]Processing documents from {input_dir}...[/cyan]")

    processed_docs = processor.process_directory(
        directory_path=input_dir,
        recursive=True,
        max_documents=max_documents,
        skip_duplicates=True
    )

    console.print(f"[green]Processed {len(processed_docs)} documents[/green]")

    # Save to JSON
    output_path = Path(output_dir) / "processed_documents.json"
    processor.save_processed_documents(processed_docs, output_path, format="json")
    console.print(f"Saved to: {output_path}")

    # Store in database
    if db_manager:
        console.print("\n[yellow]Storing in database...[/yellow]")
        success_count = 0
        for doc in track(processed_docs, description="Inserting documents"):
            if db_manager.insert_document(doc):
                success_count += 1
        console.print(f"[green]Stored {success_count} documents in database[/green]")

    # Index in vector store
    console.print("\n[yellow]Indexing in vector store...[/yellow]")
    stats = rag_system.process_and_index_documents(
        [doc.file_path for doc in processed_docs],
        save_processed=False  # Already saved
    )

    # Display statistics
    display_statistics(processed_docs, stats, db_manager)

    console.print("\n[bold green]✓ Processing complete![/bold green]")
    return processed_docs, stats


def display_statistics(processed_docs, index_stats, db_manager):
    """Display processing statistics."""
    console.print("\n[bold cyan]Processing Statistics[/bold cyan]")

    # Create statistics table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    # Document statistics
    table.add_row("Documents Processed", str(len(processed_docs)))
    table.add_row("Total Chunks", str(index_stats.get('total_chunks', 0)))
    table.add_row("Total Tables", str(index_stats.get('total_tables', 0)))
    table.add_row("Total Images", str(index_stats.get('total_images', 0)))

    # File type breakdown
    file_types = {}
    for doc in processed_docs:
        file_type = doc.metadata.get('file_type', 'unknown')
        file_types[file_type] = file_types.get(file_type, 0) + 1

    for file_type, count in file_types.items():
        table.add_row(f"  {file_type} files", str(count))

    # Database statistics
    if db_manager:
        db_stats = db_manager.get_statistics()
        table.add_row("Database Size", f"{db_stats.get('database_size_mb', 0):.2f} MB")
        table.add_row("Categories", str(len(db_stats.get('categories', []))))

    console.print(table)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Process documents for RAG system using docling and chonkie"
    )
    parser.add_argument(
        "input_dir",
        help="Directory containing documents to process"
    )
    parser.add_argument(
        "--output-dir",
        default="data/processed",
        help="Output directory for processed documents"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=512,
        help="Target chunk size (default: 512)"
    )
    parser.add_argument(
        "--max-documents",
        type=int,
        help="Maximum number of documents to process"
    )
    parser.add_argument(
        "--no-database",
        action="store_true",
        help="Skip database storage"
    )
    parser.add_argument(
        "--token-chunking",
        action="store_true",
        help="Use token-based chunking instead of semantic"
    )

    args = parser.parse_args()

    # Validate input directory
    if not Path(args.input_dir).exists():
        console.print(f"[red]Error: Input directory not found: {args.input_dir}[/red]")
        sys.exit(1)

    # Check OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        console.print("[red]Error: OPENAI_API_KEY not found in environment![/red]")
        console.print("Please create a .env file with your OpenAI API key.")
        sys.exit(1)

    try:
        # Process documents
        process_document_corpus(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            use_database=not args.no_database,
            use_semantic_chunking=not args.token_chunking,
            chunk_size=args.chunk_size,
            max_documents=args.max_documents
        )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.exception("Processing failed")
        sys.exit(1)


if __name__ == "__main__":
    main()