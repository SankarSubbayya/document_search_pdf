#!/usr/bin/env python3
"""
Quick demo showing Qdrant local mode in action.
No server installation needed!
"""

from qdrant_client import QdrantClient
from rich.console import Console
from rich.panel import Panel
from pathlib import Path

console = Console()

def main():
    console.print(Panel.fit(
        "[bold cyan]Qdrant Local Mode Demo[/bold cyan]\n"
        "No server needed! Everything stored in ./qdrant_db/",
        border_style="cyan"
    ))
    
    # Initialize Qdrant in local mode
    console.print("\n[yellow]Step 1: Initialize Qdrant (local mode)[/yellow]")
    client = QdrantClient(path="./qdrant_db")
    console.print("✅ Connected to local Qdrant")
    console.print(f"   Storage location: ./qdrant_db/")
    
    # Check storage directory
    storage_path = Path("./qdrant_db")
    if storage_path.exists():
        size_mb = sum(f.stat().st_size for f in storage_path.rglob('*') if f.is_file()) / 1024 / 1024
        console.print(f"   Current size: {size_mb:.2f} MB")
    
    # List collections
    console.print("\n[yellow]Step 2: List existing collections[/yellow]")
    collections = client.get_collections()
    
    if collections.collections:
        console.print(f"✅ Found {len(collections.collections)} collection(s):")
        for col in collections.collections:
            info = client.get_collection(col.name)
            console.print(f"   • {col.name}: {info.points_count} vectors")
    else:
        console.print("   (No collections yet - run your RAG system to create some!)")
    
    console.print("\n[bold green]✓ Qdrant is working in local mode![/bold green]")
    console.print("\n💡 What this means:")
    console.print("   • No Docker or server needed")
    console.print("   • All data stored in ./qdrant_db/ folder")
    console.print("   • Just use your Python code normally")
    console.print("   • Copy folder to backup/share data")
    
    console.print("\n[bold]Next steps:[/bold]")
    console.print("   1. Run: python quick_test.py")
    console.print("   2. Run: python examples/use_local_qdrant.py")
    console.print("   3. Check ./qdrant_db/ folder to see your vectors!")

if __name__ == "__main__":
    main()

