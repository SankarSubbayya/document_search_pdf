#!/usr/bin/env python3
"""
Example script for querying the enhanced RAG system.

Demonstrates:
1. Loading processed documents
2. Performing enhanced searches
3. Using table and image data
4. Advanced filtering options
5. Database queries
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.retrieval.enhanced_rag import EnhancedDocumentRAG
from src.storage.database_manager import DatabaseManager

# Load environment variables
load_dotenv()

# Initialize console
console = Console()


def query_rag_system(
    query: str,
    top_k: int = 5,
    category: str = None,
    file_type: str = None,
    include_tables: bool = True,
    show_sources: bool = True,
    use_database: bool = False,
    db_path: str = None
):
    """
    Query the enhanced RAG system.

    Args:
        query: User query
        top_k: Number of results
        category: Category filter
        file_type: File type filter
        include_tables: Include table results
        show_sources: Show source documents
        use_database: Use database for metadata
        db_path: Database path
    """
    # Initialize RAG system
    console.print("[cyan]Initializing Enhanced RAG System...[/cyan]")
    rag_system = EnhancedDocumentRAG()

    # Initialize database if requested
    db_manager = None
    if use_database and db_path:
        db_manager = DatabaseManager(db_type="sqlite", db_path=db_path)
        console.print(f"Using database: {db_path}")

    # Display query information
    console.print("\n[bold cyan]Query Information[/bold cyan]")
    info_table = Table(show_header=False)
    info_table.add_column("Field", style="cyan")
    info_table.add_column("Value", style="white")

    info_table.add_row("Query", query)
    info_table.add_row("Top K", str(top_k))
    if category:
        info_table.add_row("Category", category)
    if file_type:
        info_table.add_row("File Type", file_type)
    info_table.add_row("Include Tables", "Yes" if include_tables else "No")

    console.print(info_table)

    # Perform search
    console.print("\n[yellow]Searching documents...[/yellow]")

    search_results = rag_system.enhanced_search(
        query=query,
        top_k=top_k * 2,  # Get more for reranking
        category_filter=category,
        file_type_filter=file_type,
        include_tables=include_tables
    )

    if not search_results:
        console.print("[red]No results found![/red]")
        return

    console.print(f"[green]Found {len(search_results)} relevant chunks[/green]")

    # Display search results
    if show_sources:
        console.print("\n[bold cyan]Search Results[/bold cyan]")
        for i, result in enumerate(search_results[:top_k], 1):
            # Create result panel
            content = f"""
**Score:** {result['score']:.4f}
**Document:** {result.get('title', 'Unknown')}
**Type:** {result.get('content_type', 'chunk')}
**File:** {result.get('file_path', 'Unknown')}

{result['content'][:300]}{'...' if len(result['content']) > 300 else ''}
            """
            panel = Panel(
                Markdown(content),
                title=f"Result {i}",
                border_style="blue"
            )
            console.print(panel)

    # Generate RAG response
    console.print("\n[yellow]Generating response...[/yellow]")

    response = rag_system.enhanced_rag_query(
        query=query,
        top_k=top_k,
        include_tables=include_tables,
        use_reranking=True,
        category_filter=category,
        file_type_filter=file_type
    )

    # Display the answer
    console.print("\n[bold green]Generated Answer[/bold green]")
    answer_panel = Panel(
        Markdown(response['answer']),
        title="Answer",
        border_style="green"
    )
    console.print(answer_panel)

    # Display sources
    if show_sources and response.get('sources'):
        console.print("\n[bold cyan]Source Documents[/bold cyan]")
        source_table = Table(show_header=True, header_style="bold magenta")
        source_table.add_column("Title", style="cyan")
        source_table.add_column("File", style="white")
        source_table.add_column("Score", style="green")

        for source in response['sources']:
            source_table.add_row(
                source.get('title', 'Unknown'),
                Path(source.get('file_path', 'Unknown')).name,
                f"{source.get('score', 0):.4f}"
            )

        console.print(source_table)

    # Show database statistics if available
    if db_manager:
        stats = db_manager.get_statistics()
        console.print(f"\n[dim]Database contains {stats['total_documents']} documents, "
                     f"{stats['total_chunks']} chunks[/dim]")

    return response


def interactive_mode():
    """Run in interactive query mode."""
    console.print("[bold cyan]Enhanced RAG Interactive Mode[/bold cyan]")
    console.print("Type 'quit' or 'exit' to stop\n")

    rag_system = EnhancedDocumentRAG()

    while True:
        try:
            # Get user query
            query = console.input("[bold]Enter your query:[/bold] ")

            if query.lower() in ['quit', 'exit']:
                console.print("[yellow]Goodbye![/yellow]")
                break

            if not query.strip():
                continue

            # Process query
            response = rag_system.enhanced_rag_query(
                query=query,
                top_k=5,
                include_tables=True,
                use_reranking=True
            )

            # Display answer
            console.print("\n[bold green]Answer:[/bold green]")
            console.print(Markdown(response['answer']))
            console.print("\n" + "="*60 + "\n")

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Query the enhanced RAG system"
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Query to search for"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=5,
        help="Number of results to retrieve (default: 5)"
    )
    parser.add_argument(
        "--category", "-c",
        help="Filter by category"
    )
    parser.add_argument(
        "--file-type", "-t",
        help="Filter by file type (e.g., .pdf)"
    )
    parser.add_argument(
        "--no-tables",
        action="store_true",
        help="Exclude table results"
    )
    parser.add_argument(
        "--no-sources",
        action="store_true",
        help="Don't show source documents"
    )
    parser.add_argument(
        "--database", "-d",
        help="Path to database file"
    )

    args = parser.parse_args()

    # Check OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        console.print("[red]Error: OPENAI_API_KEY not found in environment![/red]")
        console.print("Please create a .env file with your OpenAI API key.")
        sys.exit(1)

    # Run in interactive mode
    if args.interactive:
        interactive_mode()
    elif args.query:
        # Single query mode
        query_rag_system(
            query=args.query,
            top_k=args.top_k,
            category=args.category,
            file_type=args.file_type,
            include_tables=not args.no_tables,
            show_sources=not args.no_sources,
            use_database=bool(args.database),
            db_path=args.database
        )
    else:
        console.print("[red]Please provide a query or use --interactive mode[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()