#!/usr/bin/env python3
"""
Example of using hybrid chunking strategies.

This shows how to combine:
- Semantic + Late chunking
- Markup + Context chunking
- Triple hybrid (all three)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processing.hybrid_chunking import (
    SemanticLateChunker,
    MarkupContextChunker,
    TripleHybridChunker,
    compare_hybrid_strategies
)


def demo_semantic_late():
    """Demo: Semantic boundaries + Contextual embeddings"""
    print("\n" + "="*80)
    print("SEMANTIC + LATE CHUNKING")
    print("="*80)
    
    text = """
    Machine learning is a subset of artificial intelligence. It focuses on 
    building systems that can learn from data. Deep learning is a specialized 
    branch of machine learning using neural networks.
    
    Neural networks consist of layers of interconnected nodes. Each node 
    processes information and passes it to the next layer. The network learns 
    by adjusting connection weights based on training data.
    
    Transformers revolutionized natural language processing. They use 
    self-attention mechanisms to process sequences. This allows them to 
    capture long-range dependencies effectively.
    """
    
    # Initialize semantic + late chunker
    chunker = SemanticLateChunker(
        chunk_size=200,
        semantic_threshold=0.5
    )
    
    # Chunk the text
    chunks = chunker.chunk(text)
    
    print(f"\nCreated {len(chunks)} chunks\n")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"--- Chunk {i} ---")
        print(f"Text: {chunk.text[:100]}...")
        print(f"Strategy: {chunk.metadata['chunking_strategy']}")
        if chunk.contextual_embedding is not None:
            print(f"Contextual Embedding Shape: {chunk.contextual_embedding.shape}")
            print("✓ Has contextual understanding from full document")
        print()


def demo_markup_context():
    """Demo: Structure preservation + Surrounding context"""
    print("\n" + "="*80)
    print("MARKUP + CONTEXT CHUNKING")
    print("="*80)
    
    markdown_text = """
# Introduction to AI

Artificial intelligence is transforming technology and society.

## Machine Learning

Machine learning enables systems to learn from data without explicit programming.

### Supervised Learning

Supervised learning uses labeled data to train models for prediction tasks.

### Unsupervised Learning

Unsupervised learning discovers patterns in unlabeled data automatically.

## Deep Learning

Deep learning uses neural networks with multiple layers for complex pattern recognition.
"""
    
    # Initialize markup + context chunker
    chunker = MarkupContextChunker(
        max_chunk_size=500,
        context_window=1
    )
    
    # Chunk the markdown
    chunks = chunker.chunk(markdown_text, document_type="markdown")
    
    print(f"\nCreated {len(chunks)} chunks\n")
    
    for i, chunk in enumerate(chunks[:3], 1):  # Show first 3
        print(f"--- Chunk {i} ---")
        print(f"Heading: {chunk.heading}")
        if chunk.section_hierarchy:
            print(f"Hierarchy: {' > '.join(chunk.section_hierarchy)}")
        
        if chunk.context_before:
            print(f"\nContext Before: ...{chunk.context_before[-50:]}")
        
        print(f"\nMain Content: {chunk.text[:100]}...")
        
        if chunk.context_after:
            print(f"\nContext After: {chunk.context_after[:50]}...")
        
        print()


def demo_triple_hybrid():
    """Demo: Structure + Semantic + Late (maximum quality)"""
    print("\n" + "="*80)
    print("TRIPLE HYBRID CHUNKING (Markup + Semantic + Late)")
    print("="*80)
    
    markdown_text = """
# Machine Learning Guide

This guide covers fundamental concepts in machine learning.

## Supervised Learning Algorithms

Supervised learning trains models using labeled examples. The model learns 
to map inputs to known outputs. Common algorithms include decision trees, 
random forests, support vector machines, and neural networks.

Decision trees split data based on feature values. They create a tree 
structure where each node represents a decision point. Random forests 
combine multiple decision trees for better accuracy.

## Neural Network Architecture

Neural networks consist of interconnected layers of nodes. Each connection 
has a weight that determines signal strength. The network processes input 
through these layers to produce output.

Deep neural networks have many hidden layers. This depth allows them to 
learn complex hierarchical features. Convolutional layers are specialized 
for image processing. Recurrent layers handle sequential data effectively.
"""
    
    # Initialize triple hybrid
    chunker = TripleHybridChunker(
        chunk_size=150,
        semantic_threshold=0.5
    )
    
    # Chunk with all three strategies
    chunks = chunker.chunk(markdown_text, document_type="markdown")
    
    print(f"\nCreated {len(chunks)} chunks\n")
    
    for i, chunk in enumerate(chunks[:3], 1):
        print(f"--- Chunk {i} ---")
        print(f"Strategy: {chunk.metadata['chunking_strategy']}")
        
        if chunk.section_hierarchy:
            print(f"Structure: {' > '.join(chunk.section_hierarchy)}")
        
        print(f"Content: {chunk.text[:80]}...")
        
        if chunk.contextual_embedding is not None:
            print(f"Contextual Embedding: {chunk.contextual_embedding.shape}")
        
        print()


def compare_strategies():
    """Compare hybrid strategies"""
    print("\n" + "="*80)
    print("COMPARING HYBRID STRATEGIES")
    print("="*80)
    
    text = """
# Deep Learning

Deep learning uses neural networks with multiple layers. These networks can 
learn complex patterns from large amounts of data.

## Convolutional Networks

CNNs are designed for processing grid-like data such as images. They use 
convolution operations to extract features from input data.

## Recurrent Networks

RNNs process sequential data by maintaining hidden states. This allows them 
to capture temporal dependencies in the data.
"""
    
    results = compare_hybrid_strategies(text)
    
    print("\nResults:\n")
    for strategy, stats in results.items():
        print(f"{strategy.upper()}:")
        if 'error' in stats:
            print(f"  Error: {stats['error']}")
        else:
            print(f"  Chunks: {stats['num_chunks']}")
            print(f"  Avg size: {stats['avg_size']:.0f} chars")
            print(f"  Embeddings: {'✓' if stats['has_embeddings'] else '✗'}")
            print(f"  Context: {'✓' if stats['has_context'] else '✗'}")
            print(f"  Hierarchy: {'✓' if stats['has_hierarchy'] else '✗'}")
        print()


def main():
    """Run all demos"""
    print("\n" + "="*80)
    print(" HYBRID CHUNKING STRATEGIES DEMO")
    print("="*80)
    
    try:
        demo_semantic_late()
        input("\nPress Enter to continue to Markup + Context demo...")
        
        demo_markup_context()
        input("\nPress Enter to continue to Triple Hybrid demo...")
        
        demo_triple_hybrid()
        input("\nPress Enter to see strategy comparison...")
        
        compare_strategies()
        
        print("\n" + "="*80)
        print(" Demo Complete! 🎉")
        print("="*80)
        print("\nYou can now use these hybrid strategies in your RAG system!")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

