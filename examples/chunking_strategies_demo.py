"""
Demo script showing how to use different chunking strategies:
- Markup Chunking
- Context Chunking  
- Late Chunking

Run this to see practical examples of each approach.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processing.advanced_chunking import (
    MarkupChunker,
    ContextChunker,
    LateChunker,
    UnifiedChunker,
    ChunkingStrategy,
    compare_chunking_strategies
)
import json


def demo_markup_chunking():
    """Demonstrate markup chunking with a Markdown document."""
    print("\n" + "="*80)
    print("MARKUP CHUNKING DEMO")
    print("="*80)
    
    # Sample markdown document
    markdown_text = """
# Machine Learning Fundamentals

Machine learning is a subset of artificial intelligence that enables systems to learn from data.

## Supervised Learning

Supervised learning uses labeled data to train models.

### Classification

Classification is used to predict discrete categories. Common algorithms include:
- Decision Trees
- Random Forests
- Neural Networks

### Regression

Regression predicts continuous values. Popular methods are:
- Linear Regression
- Polynomial Regression
- Ridge Regression

## Unsupervised Learning

Unsupervised learning finds patterns in unlabeled data.

### Clustering

Clustering groups similar data points together. Key algorithms:
- K-Means
- DBSCAN
- Hierarchical Clustering

### Dimensionality Reduction

Reduces the number of features while preserving information:
- PCA (Principal Component Analysis)
- t-SNE
- UMAP

## Deep Learning

Deep learning uses neural networks with multiple layers to learn complex patterns.

### Convolutional Neural Networks

CNNs are excellent for image processing tasks. They consist of:
- Convolutional layers
- Pooling layers
- Fully connected layers

### Recurrent Neural Networks

RNNs process sequential data and have memory of previous inputs.
"""
    
    # Initialize markup chunker
    chunker = MarkupChunker(
        max_chunk_size=500,
        min_chunk_size=50,
        preserve_hierarchy=True
    )
    
    # Chunk the document
    chunks = chunker.chunk(markdown_text, document_type="markdown")
    
    print(f"\n📊 Created {len(chunks)} chunks from the document\n")
    
    # Display chunks with hierarchy
    for i, chunk in enumerate(chunks[:5], 1):  # Show first 5 chunks
        print(f"\n--- Chunk {i} ---")
        print(f"Heading: {chunk.heading or 'None'}")
        if chunk.section_hierarchy:
            print(f"Hierarchy: {' > '.join(chunk.section_hierarchy)}")
        print(f"Size: {len(chunk.text)} characters")
        print(f"Preview: {chunk.text[:150]}...")
        print(f"Metadata: {json.dumps(chunk.metadata, indent=2)}")
    
    return chunks


def demo_context_chunking():
    """Demonstrate context chunking."""
    print("\n" + "="*80)
    print("CONTEXT CHUNKING DEMO")
    print("="*80)
    
    # Sample text
    text = """
    The transformer architecture revolutionized natural language processing when it was introduced in 2017.
    Unlike previous models that processed text sequentially, transformers use self-attention mechanisms.
    
    Self-attention allows the model to weigh the importance of different words in the input sequence.
    This enables the model to capture long-range dependencies more effectively than RNNs or LSTMs.
    
    The attention mechanism computes three vectors for each input: queries, keys, and values.
    These vectors are used to calculate attention scores that determine how much focus to place on other words.
    
    BERT, introduced by Google in 2018, was one of the first models to demonstrate the power of transformers.
    It uses bidirectional training to understand context from both left and right sides of each word.
    
    GPT models, on the other hand, use unidirectional attention and are trained to predict the next word.
    This autoregressive approach makes them particularly good at text generation tasks.
    """
    
    # Initialize context chunker
    chunker = ContextChunker(
        chunk_size=200,  # Smaller chunks for demo
        overlap_size=50,
        context_window=1  # Include 1 chunk before and after
    )
    
    # Chunk with context
    chunks = chunker.chunk(text)
    
    print(f"\n📊 Created {len(chunks)} chunks with surrounding context\n")
    
    # Display chunks with context
    for i, chunk in enumerate(chunks[:3], 1):  # Show first 3 chunks
        print(f"\n--- Chunk {i} ---")
        print(f"Size: {len(chunk.text)} characters")
        
        if chunk.context_before:
            print(f"\n📍 Context Before:")
            print(f"  {chunk.context_before}")
        
        print(f"\n📄 Main Content:")
        print(f"  {chunk.text[:200]}...")
        
        if chunk.context_after:
            print(f"\n📍 Context After:")
            print(f"  {chunk.context_after}")
        
        # Show full context
        full_context = chunker.get_full_context(chunk)
        print(f"\n🔍 Full Context Length: {len(full_context)} characters")
    
    return chunks


def demo_late_chunking():
    """Demonstrate late chunking with contextual embeddings."""
    print("\n" + "="*80)
    print("LATE CHUNKING DEMO")
    print("="*80)
    
    # Sample text
    text = """
    Retrieval-Augmented Generation (RAG) is a technique that combines information retrieval with text generation.
    The process begins by retrieving relevant documents from a knowledge base using semantic search.
    These retrieved documents provide context that helps the language model generate more accurate responses.
    
    The key advantage of RAG is that it allows models to access up-to-date information without retraining.
    Instead of relying solely on the model's parametric knowledge, RAG augments it with external sources.
    This makes the system more flexible and reduces the risk of hallucinations.
    
    Vector databases like Qdrant, Pinecone, and Weaviate are commonly used to store document embeddings.
    These databases enable fast similarity search to find the most relevant documents for a given query.
    The quality of embeddings is crucial for retrieval performance.
    """
    
    # Initialize late chunker
    chunker = LateChunker(
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        chunk_size=150,
        overlap_size=30
    )
    
    print("\n🔄 Computing embeddings for full document first...")
    
    # Standard late chunking
    chunks = chunker.chunk(text, compute_contextual_embeddings=True)
    
    print(f"\n📊 Created {len(chunks)} chunks with embeddings\n")
    
    # Display chunks with embedding info
    for i, chunk in enumerate(chunks[:3], 1):  # Show first 3 chunks
        print(f"\n--- Chunk {i} ---")
        print(f"Size: {len(chunk.text)} characters")
        print(f"Text Preview: {chunk.text[:150]}...")
        
        if chunk.embedding is not None:
            print(f"\n🧮 Embeddings:")
            print(f"  - Chunk Embedding Shape: {chunk.embedding.shape}")
            print(f"  - First 5 values: {chunk.embedding[:5]}")
        
        if chunk.contextual_embedding is not None:
            print(f"\n  - Contextual Embedding Shape: {chunk.contextual_embedding.shape}")
            print(f"  - First 5 values: {chunk.contextual_embedding[:5]}")
            print(f"  - This embedding blends chunk + document context")
    
    # Demo sliding window context
    print("\n" + "-"*80)
    print("LATE CHUNKING WITH SLIDING WINDOW")
    print("-"*80)
    
    sliding_chunks = chunker.chunk_with_sliding_context(text, context_window_size=2)
    
    print(f"\n📊 Created {len(sliding_chunks)} chunks with sliding window context\n")
    print("Each chunk's embedding is influenced by 2 chunks before and after")
    
    return chunks


def demo_unified_chunker():
    """Demonstrate unified chunker interface."""
    print("\n" + "="*80)
    print("UNIFIED CHUNKER DEMO")
    print("="*80)
    
    text = """
# RAG System Architecture

A Retrieval-Augmented Generation system consists of three main components.

## Document Ingestion

The ingestion pipeline processes and indexes documents:
- Extract text from various formats
- Chunk documents into smaller pieces
- Generate embeddings for each chunk
- Store in vector database

## Retrieval System

The retrieval system finds relevant information:
- Convert user query to embedding
- Search vector database for similar chunks
- Rank and filter results
- Return top-k most relevant chunks

## Generation System

The generation system produces the final answer:
- Combine query with retrieved context
- Send to language model
- Generate coherent response
- Include citations to sources
"""
    
    strategies = [
        (ChunkingStrategy.MARKUP, "Structure-aware chunking"),
        (ChunkingStrategy.CONTEXT, "Chunks with surrounding context"),
        (ChunkingStrategy.LATE, "Embeddings computed before chunking"),
        (ChunkingStrategy.SEMANTIC, "Semantic similarity-based chunking"),
        (ChunkingStrategy.TOKEN, "Token count-based chunking")
    ]
    
    print("\n🔄 Comparing all chunking strategies...\n")
    
    for strategy, description in strategies:
        print(f"\n--- {strategy.value.upper()} ---")
        print(f"Description: {description}")
        
        try:
            chunker = UnifiedChunker(
                strategy=strategy,
                chunk_size=300,
                overlap_size=50
            )
            
            chunks = chunker.chunk(text)
            
            # Convert to dict for storage
            chunk_dicts = chunker.chunk_to_dict(chunks)
            
            print(f"✓ Created {len(chunks)} chunks")
            print(f"  - Avg size: {sum(len(c.text) for c in chunks) / len(chunks):.0f} chars")
            print(f"  - Has embeddings: {any(c.embedding is not None for c in chunks)}")
            print(f"  - Has context: {any(c.context_before or c.context_after for c in chunks)}")
            print(f"  - Has hierarchy: {any(c.section_hierarchy for c in chunks)}")
            
        except Exception as e:
            print(f"✗ Error: {e}")


def demo_strategy_comparison():
    """Compare all strategies with statistics."""
    print("\n" + "="*80)
    print("STRATEGY COMPARISON")
    print("="*80)
    
    text = """
# Deep Learning

Deep learning is a subset of machine learning based on artificial neural networks.

## Neural Networks

Neural networks consist of layers of interconnected nodes that process information.

### Feedforward Networks

These are the simplest type of artificial neural network. Information moves in one direction.

### Convolutional Networks

CNNs are specialized for processing grid-like data such as images. They use convolution operations.

## Training

Training involves adjusting weights to minimize loss. Common techniques include:
- Gradient Descent
- Backpropagation
- Learning Rate Scheduling
"""
    
    print("\n🔄 Running comprehensive comparison...\n")
    
    results = compare_chunking_strategies(text)
    
    print("\n📊 RESULTS:\n")
    
    for strategy, stats in results.items():
        print(f"\n{strategy.upper()}:")
        if 'error' in stats:
            print(f"  Error: {stats['error']}")
        else:
            print(f"  - Number of chunks: {stats['num_chunks']}")
            print(f"  - Average size: {stats['avg_chunk_size']:.0f} chars")
            print(f"  - Size range: {stats['min_chunk_size']} - {stats['max_chunk_size']}")
            print(f"  - Size std dev: {stats['std_chunk_size']:.2f}")
            print(f"  - Has embeddings: {'✓' if stats['has_embeddings'] else '✗'}")
            print(f"  - Has context: {'✓' if stats['has_context'] else '✗'}")
            print(f"  - Has hierarchy: {'✓' if stats['has_hierarchy'] else '✗'}")


def main():
    """Run all demos."""
    print("\n" + "="*80)
    print(" ADVANCED CHUNKING STRATEGIES DEMO")
    print("="*80)
    print("\nThis demo shows three advanced chunking techniques:")
    print("  1. Markup Chunking - Structure-aware chunking based on document markup")
    print("  2. Context Chunking - Chunks with surrounding context for better retrieval")
    print("  3. Late Chunking - Embeddings computed before chunking for context preservation")
    
    try:
        # Run individual demos
        demo_markup_chunking()
        input("\nPress Enter to continue to Context Chunking demo...")
        
        demo_context_chunking()
        input("\nPress Enter to continue to Late Chunking demo...")
        
        demo_late_chunking()
        input("\nPress Enter to continue to Unified Chunker demo...")
        
        demo_unified_chunker()
        input("\nPress Enter to see strategy comparison...")
        
        demo_strategy_comparison()
        
        print("\n" + "="*80)
        print(" Demo complete! 🎉")
        print("="*80)
        print("\nYou can now integrate these chunking strategies into your RAG system.")
        print("See config.yaml for configuration options.")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

