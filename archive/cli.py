"""Command-line interface for Document Search RAG."""

import click
import os
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from dotenv import load_dotenv

from .document_search import DocumentSearchRAG

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Document Search RAG - A tutorial for Retrieval Augmented Generation."""
    load_dotenv()


@cli.command()
@click.option(
    "--json-path",
    "-j",
    default="data/documents.json",
    help="Path to JSON file containing documents",
)
@click.option(
    "--config",
    "-c",
    default="config.yaml",
    help="Path to configuration file",
)
def index(json_path: str, config: str):
    """Index documents from a JSON file."""
    if not os.path.exists(json_path):
        console.print(f"[red]Error: File '{json_path}' not found![/red]")
        return
    
    try:
        rag = DocumentSearchRAG(config_path=config)
        documents = rag.load_documents_from_json(json_path)
        
        console.print(f"[cyan]Found {len(documents)} documents to index[/cyan]")
        
        if Confirm.ask("Do you want to clear existing documents first?"):
            rag.clear_collection()
        
        rag.index_documents(documents)
        console.print("[green]✓ Indexing complete![/green]")
        
    except Exception as e:
        console.print(f"[red]Error during indexing: {e}[/red]")


@cli.command()
@click.option(
    "--config",
    "-c",
    default="config.yaml",
    help="Path to configuration file",
)
@click.option(
    "--top-k",
    "-k",
    default=5,
    help="Number of documents to retrieve",
)
@click.option(
    "--category",
    "-cat",
    default=None,
    help="Filter by category",
)
def search(config: str, top_k: int, category: str):
    """Interactive search interface."""
    try:
        rag = DocumentSearchRAG(config_path=config)
        
        console.print("[bold cyan]Document Search RAG - Interactive Mode[/bold cyan]")
        console.print("Type 'quit' or 'exit' to stop\n")
        
        while True:
            query = Prompt.ask("[bold]Enter your question")
            
            if query.lower() in ["quit", "exit"]:
                console.print("[yellow]Goodbye![/yellow]")
                break
            
            console.print("\n[cyan]Searching...[/cyan]")
            
            try:
                result = rag.rag_query(
                    query=query,
                    top_k=top_k,
                    category_filter=category,
                    show_sources=True
                )
                
                console.print(f"\n[bold green]Answer:[/bold green]\n{result['answer']}\n")
                
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]\n")
    
    except Exception as e:
        console.print(f"[red]Error initializing RAG: {e}[/red]")


@cli.command()
@click.option(
    "--config",
    "-c",
    default="config.yaml",
    help="Path to configuration file",
)
def clear(config: str):
    """Clear all indexed documents."""
    if Confirm.ask("Are you sure you want to clear all documents?"):
        try:
            rag = DocumentSearchRAG(config_path=config)
            rag.clear_collection()
            console.print("[green]✓ All documents cleared![/green]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.argument("query")
@click.option(
    "--config",
    "-c",
    default="config.yaml",
    help="Path to configuration file",
)
@click.option(
    "--top-k",
    "-k",
    default=5,
    help="Number of documents to retrieve",
)
@click.option(
    "--category",
    "-cat",
    default=None,
    help="Filter by category",
)
@click.option(
    "--no-sources",
    is_flag=True,
    help="Don't show source documents",
)
def query(query: str, config: str, top_k: int, category: str, no_sources: bool):
    """Query the document search system."""
    try:
        rag = DocumentSearchRAG(config_path=config)
        
        console.print(f"[cyan]Searching for: {query}[/cyan]\n")
        
        result = rag.rag_query(
            query=query,
            top_k=top_k,
            category_filter=category,
            show_sources=not no_sources
        )
        
        console.print(f"\n[bold green]Answer:[/bold green]\n{result['answer']}\n")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()

