#!/usr/bin/env python3
"""
Triple Hybrid Chunking Example: Markup + Semantic + Context

This example demonstrates combining three powerful chunking strategies:
1. Markup: Respects document structure (headings, sections)
2. Semantic: Creates chunks at semantically meaningful boundaries
3. Context: Adds surrounding text before/after each chunk

Best for: Structured documents (research papers, books, manuals) where you want
         high-quality chunks with surrounding context for better retrieval.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processing.hybrid_chunking import MarkupSemanticContextChunker
from rich.console import Console
from rich.panel import Panel
from rich import box

console = Console()


# Sample markdown document
SAMPLE_DOCUMENT = """
# Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed. It has revolutionized many industries.

## Supervised Learning

Supervised learning involves training a model on labeled data. The model learns to map inputs to outputs based on example input-output pairs.

### Classification

Classification is a type of supervised learning where the output is a categorical variable. Common algorithms include logistic regression, decision trees, and neural networks.

### Regression

Regression is used when the output is a continuous variable. Linear regression is one of the simplest and most widely used regression algorithms.

## Unsupervised Learning

Unsupervised learning deals with unlabeled data. The model tries to find patterns and relationships in the data without explicit guidance.

### Clustering

Clustering groups similar data points together. K-means is a popular clustering algorithm that partitions data into k clusters.

### Dimensionality Reduction

Dimensionality reduction techniques like PCA reduce the number of features while preserving important information.

## Deep Learning

Deep learning uses neural networks with multiple layers to learn complex patterns. It has achieved remarkable success in image recognition and natural language processing.

""".strip()


def main():
    """Demonstrate Markup + Semantic + Context chunking."""
    
    console.print(Panel(
        "[bold cyan]Triple Hybrid Chunking Demo[/bold cyan]\n"
        "[yellow]Markup + Semantic + Context[/yellow]",
        box=box.DOUBLE
    ))
    
    # Initialize chunker
    console.print("\n[cyan]Initializing MarkupSemanticContextChunker...[/cyan]")
    chunker = MarkupSemanticContextChunker(
        chunk_size=200,  # Smaller chunks for demo
        semantic_threshold=0.5,
        context_window=1,  # Include 1 chunk before/after
        overlap_size=50
    )
    
    # Chunk the document
    console.print("[cyan]Processing document...[/cyan]\n")
    chunks = chunker.chunk(SAMPLE_DOCUMENT, document_type="markdown")
    
    console.print(f"[green]✓ Created {len(chunks)} chunks[/green]\n")
    
    # Display chunks with their properties
    for i, chunk in enumerate(chunks, 1):
        console.print(Panel(
            f"[bold]Chunk {i}/{len(chunks)}[/bold]\n\n"
            f"[dim]Hierarchy: {chunk.section_hierarchy or 'Root'}[/dim]\n"
            f"[dim]Size: {len(chunk.text)} characters[/dim]\n\n"
            f"[yellow]Context Before ({len(chunk.context_before)} chars):[/yellow]\n"
            f"[dim]{chunk.context_before[:100]}...[/dim]\n\n"
            f"[green]Main Content ({len(chunk.text)} chars):[/green]\n"
            f"{chunk.text}\n\n"
            f"[yellow]Context After ({len(chunk.context_after)} chars):[/yellow]\n"
            f"[dim]{chunk.context_after[:100]}...[/dim]",
            title=f"[cyan]{chunk.heading or 'Document'}[/cyan]",
            border_style="blue"
        ))
        console.print()
    
    # Show statistics
    console.print(Panel(
        f"[bold]Statistics[/bold]\n\n"
        f"Total chunks: {len(chunks)}\n"
        f"Avg chunk size: {sum(len(c.text) for c in chunks) / len(chunks):.0f} chars\n"
        f"Chunks with context before: {sum(1 for c in chunks if c.context_before)}\n"
        f"Chunks with context after: {sum(1 for c in chunks if c.context_after)}\n"
        f"Chunks with hierarchy: {sum(1 for c in chunks if c.section_hierarchy)}",
        title="[green]Summary[/green]"
    ))
    
    # Explain the process
    console.print("\n[bold cyan]What Happened:[/bold cyan]\n")
    console.print("1. [yellow]Markup chunking[/yellow] identified document structure:")
    console.print("   • Main headings (#)")
    console.print("   • Subsections (##)")
    console.print("   • Sub-subsections (###)")
    console.print()
    console.print("2. [yellow]Semantic chunking[/yellow] refined boundaries within sections:")
    console.print("   • Split large sections at semantically meaningful points")
    console.print("   • Preserved coherent ideas within chunks")
    console.print()
    console.print("3. [yellow]Context addition[/yellow] enhanced each chunk:")
    console.print("   • Added text from previous chunk (context before)")
    console.print("   • Added text from next chunk (context after)")
    console.print("   • Better understanding when retrieving")
    
    # Show benefits
    console.print("\n[bold green]Benefits:[/bold green]")
    console.print("✓ Respects document structure (section boundaries)")
    console.print("✓ Semantic coherence within chunks")
    console.print("✓ Context helps retrieval accuracy")
    console.print("✓ No LLM required - fast and cost-effective")
    console.print("✓ Balances quality and performance")


def compare_with_simple():
    """Compare with simple token-based chunking."""
    from src.processing.advanced_chunking import UnifiedChunker, ChunkingStrategy
    
    console.print("\n\n[bold cyan]Comparison with Simple Token Chunking:[/bold cyan]\n")
    
    # Simple token chunking
    simple_chunker = UnifiedChunker(
        strategy=ChunkingStrategy.TOKEN,
        chunk_size=200
    )
    simple_chunks = simple_chunker.chunk(SAMPLE_DOCUMENT)
    
    # Triple hybrid
    hybrid_chunker = MarkupSemanticContextChunker(
        chunk_size=200,
        context_window=1
    )
    hybrid_chunks = hybrid_chunker.chunk(SAMPLE_DOCUMENT)
    
    # Compare
    console.print(f"[yellow]Token Chunking:[/yellow]")
    console.print(f"  Chunks: {len(simple_chunks)}")
    console.print(f"  With hierarchy: {sum(1 for c in simple_chunks if getattr(c, 'section_hierarchy', None))}")
    console.print(f"  With context: {sum(1 for c in simple_chunks if getattr(c, 'context_before', None))}")
    console.print()
    
    console.print(f"[green]Triple Hybrid Chunking:[/green]")
    console.print(f"  Chunks: {len(hybrid_chunks)}")
    console.print(f"  With hierarchy: {sum(1 for c in hybrid_chunks if c.section_hierarchy)}")
    console.print(f"  With context: {sum(1 for c in hybrid_chunks if c.context_before)}")
    console.print()
    
    console.print("[bold]Winner:[/bold] Triple Hybrid - More semantic, structured, and context-rich! 🏆")


if __name__ == "__main__":
    main()
    
    # Optional: Show comparison
    if "-compare" in sys.argv:
        compare_with_simple()
    
    console.print("\n[dim]Run with -compare flag to see comparison with simple chunking[/dim]")



