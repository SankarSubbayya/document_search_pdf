#!/usr/bin/env python3
"""
Delete Documents from Qdrant Index
Simple utility to remove specific documents or clear collections
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm, Prompt
from rich import box
import sys

console = Console()


def list_documents(client: QdrantClient, collection_name: str):
    """List all documents in the collection"""
    try:
        # Scroll through all points
        all_points, _ = client.scroll(
            collection_name=collection_name,
            limit=10000,
            with_payload=True,
            with_vectors=False
        )
        
        # Group by document
        documents = {}
        for point in all_points:
            doc_id = point.payload.get('document_id')
            doc_name = point.payload.get('document_name', 'Unknown')
            
            if doc_id not in documents:
                documents[doc_id] = {
                    'name': doc_name,
                    'chunks': 0,
                    'strategy': point.payload.get('chunking_strategy', 'N/A'),
                    'cleaned': point.payload.get('was_cleaned', False),
                    'upload_date': point.payload.get('upload_date', 'Unknown')
                }
            documents[doc_id]['chunks'] += 1
        
        return documents
    
    except Exception as e:
        console.print(f"[red]Error listing documents: {e}[/red]")
        return {}


def delete_document_by_id(client: QdrantClient, collection_name: str, document_id: str):
    """Delete a specific document by its ID"""
    try:
        client.delete(
            collection_name=collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        )
        return True
    except Exception as e:
        console.print(f"[red]Error deleting document: {e}[/red]")
        return False


def delete_document_by_name(client: QdrantClient, collection_name: str, document_name: str):
    """Delete a specific document by its name"""
    try:
        client.delete(
            collection_name=collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_name",
                        match=MatchValue(value=document_name)
                    )
                ]
            )
        )
        return True
    except Exception as e:
        console.print(f"[red]Error deleting document: {e}[/red]")
        return False


def delete_collection(client: QdrantClient, collection_name: str):
    """Delete entire collection"""
    try:
        client.delete_collection(collection_name)
        return True
    except Exception as e:
        console.print(f"[red]Error deleting collection: {e}[/red]")
        return False


def interactive_delete(host: str = "localhost", port: int = 6333):
    """Interactive deletion interface"""
    
    console.print("\n[bold cyan]🗑️  Qdrant Document Deletion Utility[/bold cyan]\n")
    
    try:
        # Connect
        client = QdrantClient(host=host, port=port)
        
        # List collections
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if not collection_names:
            console.print("[yellow]No collections found![/yellow]")
            return
        
        console.print("[green]Available collections:[/green]")
        for i, name in enumerate(collection_names, 1):
            console.print(f"  {i}. {name}")
        
        # Select collection
        collection_choice = Prompt.ask(
            "\n[cyan]Select collection number[/cyan]",
            default="1"
        )
        
        try:
            collection_name = collection_names[int(collection_choice) - 1]
        except (ValueError, IndexError):
            console.print("[red]Invalid selection![/red]")
            return
        
        console.print(f"\n[cyan]Working with collection: {collection_name}[/cyan]\n")
        
        # List documents
        documents = list_documents(client, collection_name)
        
        if not documents:
            console.print("[yellow]No documents found in this collection![/yellow]")
            return
        
        # Display documents table
        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Document Name", style="yellow", no_wrap=False)
        table.add_column("Chunks", justify="right", style="green")
        table.add_column("Strategy", style="blue")
        table.add_column("Cleaned", justify="center")
        table.add_column("Upload Date", style="dim")
        
        doc_list = list(documents.items())
        for i, (doc_id, doc_info) in enumerate(doc_list, 1):
            table.add_row(
                str(i),
                doc_info['name'][:50],
                str(doc_info['chunks']),
                doc_info['strategy'],
                "✓" if doc_info['cleaned'] else "✗",
                doc_info['upload_date'][:10]
            )
        
        console.print(table)
        console.print(f"\n[green]Total: {len(documents)} documents[/green]\n")
        
        # Deletion options
        console.print("[bold]Deletion Options:[/bold]")
        console.print("  1. Delete specific document(s)")
        console.print("  2. Delete entire collection")
        console.print("  3. Cancel")
        
        choice = Prompt.ask("[cyan]Your choice[/cyan]", default="3")
        
        if choice == "1":
            # Delete specific documents
            doc_numbers = Prompt.ask(
                "[cyan]Enter document number(s) to delete (comma-separated)[/cyan]"
            )
            
            try:
                indices = [int(n.strip()) for n in doc_numbers.split(',')]
                
                for idx in indices:
                    if 1 <= idx <= len(doc_list):
                        doc_id, doc_info = doc_list[idx - 1]
                        
                        if Confirm.ask(f"[yellow]Delete '{doc_info['name']}'?[/yellow]"):
                            if delete_document_by_id(client, collection_name, doc_id):
                                console.print(f"[green]✓ Deleted: {doc_info['name']} ({doc_info['chunks']} chunks)[/green]")
                            else:
                                console.print(f"[red]✗ Failed to delete: {doc_info['name']}[/red]")
                    else:
                        console.print(f"[red]Invalid document number: {idx}[/red]")
            
            except ValueError:
                console.print("[red]Invalid input format![/red]")
        
        elif choice == "2":
            # Delete entire collection
            if Confirm.ask(f"[red bold]⚠️  Delete ENTIRE collection '{collection_name}'? This cannot be undone![/red bold]"):
                if delete_collection(client, collection_name):
                    console.print(f"[green]✓ Collection '{collection_name}' deleted![/green]")
                else:
                    console.print("[red]✗ Failed to delete collection[/red]")
        
        else:
            console.print("[yellow]Cancelled[/yellow]")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("\n[yellow]Is Qdrant running?[/yellow]")
        console.print("[cyan]Start it with: docker-compose up -d qdrant[/cyan]")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Delete documents from Qdrant")
    parser.add_argument("--host", default="localhost", help="Qdrant host")
    parser.add_argument("--port", type=int, default=6333, help="Qdrant port")
    parser.add_argument("--collection", help="Collection name")
    parser.add_argument("--document-id", help="Document ID to delete")
    parser.add_argument("--document-name", help="Document name to delete")
    parser.add_argument("--delete-collection", action="store_true", help="Delete entire collection")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    
    args = parser.parse_args()
    
    # Non-interactive mode
    if args.collection and (args.document_id or args.document_name or args.delete_collection):
        try:
            client = QdrantClient(host=args.host, port=args.port)
            
            if args.delete_collection:
                if args.yes or Confirm.ask(f"Delete collection '{args.collection}'?"):
                    if delete_collection(client, args.collection):
                        console.print(f"[green]✓ Deleted collection: {args.collection}[/green]")
                    else:
                        sys.exit(1)
            
            elif args.document_id:
                if args.yes or Confirm.ask(f"Delete document ID '{args.document_id}'?"):
                    if delete_document_by_id(client, args.collection, args.document_id):
                        console.print(f"[green]✓ Deleted document: {args.document_id}[/green]")
                    else:
                        sys.exit(1)
            
            elif args.document_name:
                if args.yes or Confirm.ask(f"Delete document '{args.document_name}'?"):
                    if delete_document_by_name(client, args.collection, args.document_name):
                        console.print(f"[green]✓ Deleted document: {args.document_name}[/green]")
                    else:
                        sys.exit(1)
        
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
    
    else:
        # Interactive mode
        interactive_delete(args.host, args.port)


if __name__ == "__main__":
    main()



