#!/usr/bin/env python3
"""Quick integration test for the document search system."""

from pathlib import Path
from rich.console import Console
from rich.table import Table
import sys
import traceback

console = Console()

def test_imports():
    """Test that all modules can be imported."""
    console.print("\n[bold cyan]🧪 Module Import Tests[/bold cyan]\n")
    
    tests = [
        ("DocumentProcessor", "src.document_processor", "DocumentProcessor"),
        ("DatabaseManager", "src.database_manager", "DatabaseManager"),
        ("EnhancedDocumentRAG", "src.enhanced_rag", "EnhancedDocumentRAG"),
        ("DocumentSearchRAG", "src.document_search", "DocumentSearchRAG"),
    ]
    
    results = []
    for name, module, cls in tests:
        try:
            exec(f"from {module} import {cls}")
            results.append((name, "✅ Pass", ""))
        except Exception as e:
            results.append((name, "❌ Fail", str(e)[:50]))
    
    table = Table(title="Import Tests")
    table.add_column("Module", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Error", style="red")
    
    for name, status, error in results:
        table.add_row(name, status, error)
    
    console.print(table)
    return all("✅" in r[1] for r in results)

def test_document_processor():
    """Test document processing."""
    console.print("\n[yellow]📄 Document Processor Test[/yellow]")
    try:
        from src.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        console.print("✅ DocumentProcessor initialized")
        
        test_docs = Path("test_documents")
        if test_docs.exists():
            md_files = list(test_docs.glob("*.md"))
            txt_files = list(test_docs.glob("*.txt"))
            all_files = md_files + txt_files
            
            if all_files:
                console.print(f"   Found {len(all_files)} test documents")
                
                # Process first document
                result = processor.process_document(all_files[0])
                console.print(f"✅ Processed: {result.title}")
                console.print(f"   - Chunks: {len(result.chunks)}")
                console.print(f"   - Tables: {len(result.tables)}")
                console.print(f"   - Word count: {result.metadata.get('word_count', 0)}")
                return True
            else:
                console.print("⚠️  No documents found in test_documents/")
                return False
        else:
            console.print("⚠️  test_documents/ directory not found")
            return False
    except Exception as e:
        console.print(f"❌ Error: {e}")
        traceback.print_exc()
        return False

def test_database_manager():
    """Test database operations."""
    console.print("\n[yellow]🗄️  Database Manager Test[/yellow]")
    try:
        from src.database_manager import DatabaseManager
        
        db = DatabaseManager(db_path=":memory:")  # Use in-memory DB for testing
        console.print("✅ Database initialized (in-memory)")
        
        # Get stats
        stats = db.get_statistics()
        console.print(f"   - Documents: {stats.get('total_documents', 0)}")
        console.print(f"   - Chunks: {stats.get('total_chunks', 0)}")
        console.print(f"   - Tables: {stats.get('total_tables', 0)}")
        
        return True
    except Exception as e:
        console.print(f"❌ Error: {e}")
        traceback.print_exc()
        return False

def test_basic_rag():
    """Test basic RAG functionality."""
    console.print("\n[yellow]🤖 Basic RAG Test[/yellow]")
    try:
        from src.document_search import Document
        from sentence_transformers import SentenceTransformer
        
        console.print("✅ Testing embeddings without full RAG initialization")
        
        # Test embedder directly (doesn't need OpenAI)
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        console.print("✅ SentenceTransformer loaded")
        
        # Create a test document
        doc = Document(
            id="test_1",
            title="Test Document",
            content="This is a test document about machine learning and AI.",
            category="Test"
        )
        
        # Test embedding (no API call)
        embedding = embedder.encode(doc.content, convert_to_numpy=True)
        console.print(f"✅ Embedding created (dimension: {len(embedding)})")
        
        return True
    except Exception as e:
        console.print(f"❌ Error: {e}")
        traceback.print_exc()
        return False

def main():
    console.print("\n[bold cyan]" + "="*60 + "[/bold cyan]")
    console.print("[bold cyan]   Document Search RAG - Integration Tests[/bold cyan]")
    console.print("[bold cyan]" + "="*60 + "[/bold cyan]\n")
    
    results = {}
    
    # Run tests
    results['imports'] = test_imports()
    results['database'] = test_database_manager()
    results['basic_rag'] = test_basic_rag()
    results['processor'] = test_document_processor()
    
    # Summary
    console.print("\n[bold cyan]" + "="*60 + "[/bold cyan]")
    console.print("[bold]Test Summary:[/bold]")
    
    table = Table()
    table.add_column("Test", style="cyan")
    table.add_column("Result", style="bold")
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        table.add_row(test_name.replace('_', ' ').title(), status)
    
    console.print(table)
    
    total = len(results)
    passed = sum(results.values())
    console.print(f"\n[bold]Results: {passed}/{total} tests passed[/bold]")
    
    if passed == total:
        console.print("\n[bold green]✓ All tests passed![/bold green]\n")
        return 0
    else:
        console.print("\n[bold red]✗ Some tests failed[/bold red]\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())

