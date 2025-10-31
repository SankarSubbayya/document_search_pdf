#!/usr/bin/env python3
"""
Simple Qdrant Database Viewer
Quick utility to view your indexed documents
"""

from qdrant_client import QdrantClient
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

def view_database(host: str = "localhost", port: int = 6333):
    """View Qdrant database contents"""
    
    try:
        # Connect
        console.print(f"[cyan]Connecting to Qdrant at {host}:{port}...[/cyan]")
        client = QdrantClient(host=host, port=port)
        
        # List collections
        collections = client.get_collections()
        console.print(f"\n[green]✓ Connected successfully![/green]")
        console.print(f"[yellow]Found {len(collections.collections)} collection(s)[/yellow]\n")
        
        if not collections.collections:
            console.print("[red]No collections found. Upload some documents first![/red]")
            return
        
        # Display each collection
        for collection in collections.collections:
            name = collection.name
            
            # Get collection info
            info = client.get_collection(name)
            
            # Create header
            console.print(Panel(
                f"[bold cyan]Collection: {name}[/bold cyan]",
                box=box.DOUBLE
            ))
            
            # Stats table
            stats_table = Table(show_header=True, header_style="bold magenta")
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="yellow")
            
            stats_table.add_row("Points (chunks)", str(info.points_count))
            stats_table.add_row("Vector Dimension", str(info.config.params.vectors.size))
            stats_table.add_row("Distance Metric", info.config.params.vectors.distance.name)
            
            console.print(stats_table)
            console.print()
            
            # Get sample points
            if info.points_count > 0:
                console.print("[cyan]📄 Sample Documents:[/cyan]\n")
                
                points, _ = client.scroll(
                    collection_name=name,
                    limit=10,
                    with_payload=True,
                    with_vectors=False
                )
                
                # Group by document
                docs = {}
                for point in points:
                    doc_name = point.payload.get('document_name', 'Unknown')
                    if doc_name not in docs:
                        docs[doc_name] = {
                            'chunks': 0,
                            'strategy': point.payload.get('chunking_strategy', 'N/A'),
                            'cleaned': point.payload.get('was_cleaned', False),
                            'sample_content': point.payload.get('content', '')[:150]
                        }
                    docs[doc_name]['chunks'] += 1
                
                # Display documents table
                docs_table = Table(show_header=True, header_style="bold green", box=box.ROUNDED)
                docs_table.add_column("Document Name", style="cyan", no_wrap=False, width=30)
                docs_table.add_column("Chunks", justify="right", style="yellow")
                docs_table.add_column("Strategy", style="magenta")
                docs_table.add_column("Cleaned", justify="center", style="green")
                
                for doc_name, data in docs.items():
                    docs_table.add_row(
                        doc_name,
                        str(data['chunks']) + "+",
                        data['strategy'],
                        "✓" if data['cleaned'] else "✗"
                    )
                
                console.print(docs_table)
                console.print()
                
                # Show sample content
                sample_doc = list(docs.items())[0]
                console.print(Panel(
                    f"[dim]{sample_doc[1]['sample_content']}...[/dim]",
                    title=f"[cyan]Sample Content from: {sample_doc[0]}[/cyan]",
                    border_style="blue"
                ))
                
            else:
                console.print("[yellow]Collection is empty[/yellow]")
            
            console.print("\n" + "="*80 + "\n")
        
        # Show web dashboard link
        console.print(Panel(
            f"[bold green]🌐 Web Dashboard:[/bold green]\n"
            f"[cyan]http://localhost:{port}/dashboard[/cyan]\n\n"
            f"[dim]Open this URL in your browser for full interactive access![/dim]",
            title="[yellow]Quick Links[/yellow]",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        console.print("\n[yellow]Is Qdrant running?[/yellow]")
        console.print("[cyan]Start it with: docker-compose up -d qdrant[/cyan]")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="View Qdrant database contents")
    parser.add_argument("--host", default="localhost", help="Qdrant host")
    parser.add_argument("--port", type=int, default=6333, help="Qdrant port")
    
    args = parser.parse_args()
    view_database(args.host, args.port)



