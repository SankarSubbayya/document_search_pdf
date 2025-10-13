#!/usr/bin/env python3
"""
Example: Using Qdrant in Local Mode

This demonstrates how to use Qdrant with file-based storage (no server needed).
All vectors are stored in the ./qdrant_db/ directory.
"""

from pathlib import Path
from rich.console import Console
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

console = Console()

def example_basic_rag_local():
    """Example using the basic RAG system (already configured for local mode)."""
    console.print("\n[bold cyan]Example 1: Basic RAG with Local Qdrant[/bold cyan]\n")
    
    from src.retrieval.base_rag import DocumentSearchRAG, Document
    
    # Initialize - automatically uses local mode from config.yaml
    # Storage location: ./qdrant_db/
    rag = DocumentSearchRAG()
    console.print("✅ RAG initialized in LOCAL mode")
    console.print(f"   Storage: {rag.qdrant_client._client._storage_path or './qdrant_db/'}")
    
    # Create sample documents
    docs = [
        Document(
            id="1",
            title="Python Basics",
            content="Python is a high-level programming language known for simplicity.",
            category="Programming"
        ),
        Document(
            id="2", 
            title="Machine Learning",
            content="Machine learning is a subset of AI that learns from data.",
            category="AI"
        )
    ]
    
    # Index documents (stored locally in ./qdrant_db/)
    console.print("\n📝 Indexing documents...")
    rag.index_documents(docs)
    console.print("✅ Documents indexed and stored locally!")
    
    # Search (no server needed)
    console.print("\n🔍 Searching...")
    results = rag.search("What is Python?", top_k=2)
    
    for i, (doc, score) in enumerate(results, 1):
        console.print(f"\n{i}. {doc.title} (score: {score:.3f})")
        console.print(f"   {doc.content[:100]}...")


def example_direct_qdrant_local():
    """Example using Qdrant client directly in local mode."""
    console.print("\n[bold cyan]Example 2: Direct Qdrant Client (Local Mode)[/bold cyan]\n")
    
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    import numpy as np
    
    # Method 1: Local mode with path parameter
    client = QdrantClient(path="./qdrant_db")
    console.print("✅ Qdrant client created in LOCAL mode")
    console.print("   Storage: ./qdrant_db/")
    
    # Create a collection
    collection_name = "test_local"
    
    try:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=128, distance=Distance.COSINE)
        )
        console.print(f"✅ Collection '{collection_name}' created")
    except Exception as e:
        console.print(f"⚠️  Collection might already exist: {e}")
    
    # Add some vectors
    vectors = [
        PointStruct(
            id=1,
            vector=np.random.rand(128).tolist(),
            payload={"text": "First document"}
        ),
        PointStruct(
            id=2,
            vector=np.random.rand(128).tolist(),
            payload={"text": "Second document"}
        )
    ]
    
    client.upsert(collection_name=collection_name, points=vectors)
    console.print(f"✅ Added {len(vectors)} vectors to local storage")
    
    # Verify storage
    info = client.get_collection(collection_name)
    console.print(f"\n📊 Collection info:")
    console.print(f"   Points count: {info.points_count}")
    console.print(f"   Vectors size: {info.config.params.vectors.size}")


def example_check_storage():
    """Check what's stored in the local Qdrant database."""
    console.print("\n[bold cyan]Example 3: Inspect Local Storage[/bold cyan]\n")
    
    from qdrant_client import QdrantClient
    
    client = QdrantClient(path="./qdrant_db")
    
    # List all collections
    collections = client.get_collections()
    console.print(f"📁 Collections in local storage:")
    
    if collections.collections:
        for col in collections.collections:
            info = client.get_collection(col.name)
            console.print(f"\n   • {col.name}")
            console.print(f"     Points: {info.points_count}")
            console.print(f"     Vector size: {info.config.params.vectors.size}")
    else:
        console.print("   (No collections yet)")


def example_local_vs_server():
    """Show the difference between local and server modes."""
    console.print("\n[bold cyan]Example 4: Local vs Server Mode[/bold cyan]\n")
    
    from qdrant_client import QdrantClient
    
    console.print("📝 Two ways to initialize Qdrant:\n")
    
    console.print("1. [green]LOCAL MODE[/green] (file-based, no server):")
    console.print("   ```python")
    console.print("   client = QdrantClient(path='./qdrant_db')")
    console.print("   ```")
    console.print("   ✅ No installation needed")
    console.print("   ✅ Data stored in directory")
    console.print("   ✅ Perfect for development")
    console.print("   ✅ Portable\n")
    
    console.print("2. [yellow]SERVER MODE[/yellow] (requires running Qdrant server):")
    console.print("   ```python")
    console.print("   client = QdrantClient(url='http://localhost:6333')")
    console.print("   ```")
    console.print("   ✅ Better performance")
    console.print("   ✅ Web dashboard")
    console.print("   ✅ Multiple clients")
    console.print("   ❌ Requires Docker/installation\n")
    
    console.print("[bold]Your current setup uses LOCAL MODE! 🎉[/bold]")


def main():
    console.print("\n[bold]═══════════════════════════════════════════════════[/bold]")
    console.print("[bold]        Qdrant Local Mode Examples[/bold]")
    console.print("[bold]═══════════════════════════════════════════════════[/bold]")
    
    try:
        # Run examples
        example_local_vs_server()
        
        console.print("\n" + "─"*50)
        input("\nPress Enter to continue to Example 1...")
        example_basic_rag_local()
        
        console.print("\n" + "─"*50)
        input("\nPress Enter to continue to Example 2...")
        example_direct_qdrant_local()
        
        console.print("\n" + "─"*50)
        input("\nPress Enter to continue to Example 3...")
        example_check_storage()
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Examples interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
    
    console.print("\n[bold green]✓ Examples complete![/bold green]")
    console.print("\n💡 Tips:")
    console.print("   • Check ./qdrant_db/ directory for stored vectors")
    console.print("   • Copy this folder to backup/move your data")
    console.print("   • Delete this folder to start fresh")
    console.print()


if __name__ == "__main__":
    main()

