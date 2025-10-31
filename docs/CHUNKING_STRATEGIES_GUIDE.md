# Advanced Chunking Strategies Guide

This guide explains how to use the three advanced chunking strategies in your RAG system:

1. **Markup Chunking** - Structure-aware chunking based on document markup
2. **Context Chunking** - Chunks with surrounding context for better retrieval
3. **Late Chunking** - Embeddings computed before chunking for context preservation

## Overview

### Why Advanced Chunking Matters

Traditional chunking methods (simple token-based or semantic) can lose important information:
- **Context across chunk boundaries** - Related information split across chunks
- **Document structure** - Headings and hierarchical relationships lost
- **Semantic coherence** - Embeddings computed without full context

Advanced chunking strategies address these limitations.

---

## 1. Markup Chunking

### What It Does
Chunks documents based on their structural markup (headings, sections, paragraphs) rather than arbitrary character counts.

### Benefits
✅ Preserves document structure  
✅ Maintains semantic units (sections stay together)  
✅ Includes hierarchical context (e.g., "Chapter 1 > Section 1.2")  
✅ Better for structured documents  

### Best For
- Technical documentation
- Academic papers
- Markdown/HTML documents
- Reports with clear sections

### How to Use

```python
from src.processing.advanced_chunking import MarkupChunker

# Initialize chunker
chunker = MarkupChunker(
    max_chunk_size=1000,        # Maximum characters per chunk
    min_chunk_size=100,         # Minimum characters per chunk
    preserve_hierarchy=True     # Include section hierarchy
)

# Chunk a markdown document
markdown_text = """
# Introduction
This is the introduction section...

## Background
Some background information...

### Related Work
Discussion of related research...
"""

chunks = chunker.chunk(markdown_text, document_type="markdown")

# Access chunk information
for chunk in chunks:
    print(f"Heading: {chunk.heading}")
    print(f"Hierarchy: {' > '.join(chunk.section_hierarchy)}")
    print(f"Text: {chunk.text}")
    print(f"Metadata: {chunk.metadata}")
```

### Supported Document Types
- `markdown` - Markdown files with # headings
- `html` - HTML with h1-h6 tags and structural elements
- `generic` - Plain text (falls back to paragraph-based chunking)

### Configuration in config.yaml

```yaml
processing:
  chunking:
    strategy: markup
    chunk_size: 1000
    
    markup:
      enabled: true
      preserve_hierarchy: true
      document_type: markdown  # or html, generic
```

---

## 2. Context Chunking

### What It Does
Adds surrounding context (text from previous and next chunks) to each chunk for better semantic understanding.

### Benefits
✅ Preserves context across chunk boundaries  
✅ Improves retrieval accuracy  
✅ Helps with ambiguous references  
✅ Better semantic understanding  

### Best For
- Long documents with interconnected ideas
- Documents with many cross-references
- Narrative or flowing text
- Cases where context is crucial

### How to Use

```python
from src.processing.advanced_chunking import ContextChunker
from chonkie import SemanticChunker
from chonkie.embeddings import SentenceTransformerEmbeddings

# Create base chunker (can be semantic or token-based)
embeddings = SentenceTransformerEmbeddings(
    model="sentence-transformers/all-MiniLM-L6-v2"
)
base_chunker = SemanticChunker(
    embedding_model=embeddings,
    chunk_size=512,
    threshold=0.5
)

# Initialize context chunker
chunker = ContextChunker(
    chunk_size=512,
    overlap_size=100,
    context_window=2,           # Include 2 chunks before/after
    base_chunker=base_chunker
)

# Chunk with context
text = "Your long document text here..."
chunks = chunker.chunk(text)

# Access context information
for chunk in chunks:
    print(f"Context Before: {chunk.context_before}")
    print(f"Main Content: {chunk.text}")
    print(f"Context After: {chunk.context_after}")
    
    # Get full context (with markers)
    full_context = chunker.get_full_context(chunk)
    print(f"Full Context: {full_context}")
```

### Context Window

The `context_window` parameter controls how many surrounding chunks to include:

- `context_window=1` - Include 1 chunk before and 1 after
- `context_window=2` - Include 2 chunks before and 2 after
- `context_window=3` - Include 3 chunks before and 3 after

**Trade-off**: Larger windows provide more context but increase storage and processing time.

### Configuration in config.yaml

```yaml
processing:
  chunking:
    strategy: context
    chunk_size: 512
    chunk_overlap: 50
    
    context:
      enabled: true
      context_window: 2
      overlap_size: 100
```

---

## 3. Late Chunking

### What It Does
Computes embeddings for the full document (or large sections) FIRST, then chunks the text while preserving contextual information by blending chunk embeddings with document embeddings.

### Benefits
✅ Embeddings include full document context  
✅ Better semantic coherence  
✅ Improved retrieval accuracy  
✅ Preserves global document meaning  

### Best For
- Documents where global context is important
- Technical documents with specialized terminology
- Cases where chunk boundaries are artificial
- When retrieval accuracy is critical

### How to Use

#### Standard Late Chunking

```python
from src.processing.advanced_chunking import LateChunker

# Initialize late chunker
chunker = LateChunker(
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    chunk_size=512,
    overlap_size=50,
    max_context_length=8192  # Max tokens for document embedding
)

# Chunk with contextual embeddings
text = "Your document text here..."
chunks = chunker.chunk(
    text,
    compute_contextual_embeddings=True
)

# Access embeddings
for chunk in chunks:
    print(f"Text: {chunk.text}")
    print(f"Chunk Embedding Shape: {chunk.embedding.shape}")
    print(f"Contextual Embedding Shape: {chunk.contextual_embedding.shape}")
    
    # The contextual embedding is a blend:
    # 70% chunk embedding + 30% full document embedding
```

#### Sliding Window Late Chunking

For very long documents, use sliding window instead of full document:

```python
# Chunk with sliding context window
chunks = chunker.chunk_with_sliding_context(
    text,
    context_window_size=3  # Use 3 chunks before/after for context
)

# Each chunk's embedding is influenced by nearby chunks
# More efficient than full document embedding for long texts
```

### Embedding Blending

Late chunking blends two embeddings:

1. **Chunk Embedding** (70%) - Embedding of just the chunk text
2. **Document Embedding** (30%) - Embedding of full document (or context window)

This creates a **contextual embedding** that:
- Understands the chunk content
- Preserves global document context
- Improves retrieval accuracy

### Configuration in config.yaml

```yaml
processing:
  chunking:
    strategy: late
    chunk_size: 512
    chunk_overlap: 50
    
    late:
      enabled: true
      compute_contextual: true
      use_sliding_window: false
      context_window_size: 3
      max_context_length: 8192
```

---

## Using the Unified Chunker

For easy switching between strategies, use the `UnifiedChunker`:

```python
from src.processing.advanced_chunking import (
    UnifiedChunker,
    ChunkingStrategy
)

# Choose your strategy
strategies = [
    ChunkingStrategy.MARKUP,
    ChunkingStrategy.CONTEXT,
    ChunkingStrategy.LATE,
    ChunkingStrategy.SEMANTIC,
    ChunkingStrategy.TOKEN
]

# Initialize with desired strategy
chunker = UnifiedChunker(
    strategy=ChunkingStrategy.LATE,
    chunk_size=512,
    overlap_size=50,
    embedding_model="sentence-transformers/all-MiniLM-L6-v2"
)

# Chunk text
text = "Your document text..."
chunks = chunker.chunk(text)

# Convert to dictionary format for storage
chunk_dicts = chunker.chunk_to_dict(chunks)

# Save to database or vector store
for chunk_dict in chunk_dicts:
    # chunk_dict contains all necessary information
    # including embeddings, context, hierarchy, etc.
    pass
```

---

## Integration with Document Processor

To integrate advanced chunking into your existing `DocumentProcessor`:

```python
from src.processing.document_processor import DocumentProcessor
from src.processing.advanced_chunking import (
    UnifiedChunker,
    ChunkingStrategy
)

# Update the DocumentProcessor to use advanced chunking
class EnhancedDocumentProcessor(DocumentProcessor):
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        chunking_strategy: ChunkingStrategy = ChunkingStrategy.CONTEXT,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        # Initialize with unified chunker
        self.unified_chunker = UnifiedChunker(
            strategy=chunking_strategy,
            chunk_size=chunk_size,
            overlap_size=chunk_overlap,
            embedding_model=embedding_model
        )
        
        # Keep other initialization code
        super().__init__(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            use_semantic_chunking=False,  # We'll use unified chunker
            embedding_model=embedding_model
        )
    
    def _chunk_document(self, text: str, metadata: dict) -> list:
        """Override chunking method to use advanced strategies."""
        # Use unified chunker
        chunks = self.unified_chunker.chunk(text)
        
        # Format for your system
        formatted_chunks = []
        for chunk in chunks:
            chunk_dict = {
                'chunk_id': chunk.chunk_id,
                'chunk_index': chunk.chunk_index,
                'content': chunk.text,
                'start_index': chunk.start_index,
                'end_index': chunk.end_index,
                'metadata': {
                    **metadata,
                    **chunk.metadata,
                    'chunk_index': chunk.chunk_index
                }
            }
            
            # Add optional fields
            if chunk.context_before:
                chunk_dict['context_before'] = chunk.context_before
            if chunk.context_after:
                chunk_dict['context_after'] = chunk.context_after
            if chunk.section_hierarchy:
                chunk_dict['section_hierarchy'] = chunk.section_hierarchy
            if chunk.embedding is not None:
                chunk_dict['embedding'] = chunk.embedding
            if chunk.contextual_embedding is not None:
                chunk_dict['contextual_embedding'] = chunk.contextual_embedding
            
            formatted_chunks.append(chunk_dict)
        
        return formatted_chunks
```

---

## Comparison: Which Strategy to Use?

| Strategy | Pros | Cons | Best For |
|----------|------|------|----------|
| **Markup** | Preserves structure, semantic units intact | Requires structured documents | Technical docs, reports |
| **Context** | Cross-boundary context, better retrieval | Larger storage requirements | Long narratives, flowing text |
| **Late** | Global context, best embeddings | More computation, memory intensive | Critical accuracy needs |
| **Semantic** | Balanced, general purpose | May split semantic units | General documents |
| **Token** | Fast, predictable | No semantic awareness | Quick prototyping |

### Recommendation by Document Type

- **Technical Documentation**: Markup → Context
- **Academic Papers**: Markup → Late
- **News Articles**: Context → Semantic
- **Books/Long Form**: Context → Late
- **Chat Logs/Unstructured**: Semantic → Token

---

## Running the Demo

To see all strategies in action:

```bash
# Run the demo script
python examples/chunking_strategies_demo.py
```

The demo will show:
1. Markup chunking with hierarchy
2. Context chunking with surrounding text
3. Late chunking with embeddings
4. Unified chunker interface
5. Strategy comparison

---

## Performance Considerations

### Computational Cost (Low to High)
1. Token Chunking (fastest)
2. Semantic Chunking
3. Markup Chunking
4. Context Chunking
5. Late Chunking (slowest, most accurate)

### Memory Usage (Low to High)
1. Token Chunking
2. Semantic Chunking
3. Markup Chunking
4. Context Chunking
5. Late Chunking (highest)

### Retrieval Accuracy (Low to High)
1. Token Chunking
2. Semantic Chunking
3. Markup Chunking
4. Context Chunking
5. Late Chunking (best)

---

## Best Practices

### 1. Choose Strategy Based on Document Type
- Structured documents → Markup
- Long connected text → Context
- Critical accuracy → Late

### 2. Tune Parameters
```python
# For shorter documents
chunk_size = 256
context_window = 1

# For longer documents
chunk_size = 512
context_window = 2

# For very long documents
chunk_size = 1024
context_window = 3
use_sliding_window = True
```

### 3. Combine Strategies
```python
# Use markup for initial chunking, then add context
# Use context chunks with late chunking embeddings
```

### 4. Monitor Performance
```python
from src.processing.advanced_chunking import compare_chunking_strategies

# Compare strategies on your data
results = compare_chunking_strategies(your_text)
print(results)
```

### 5. Storage Optimization

For late chunking with embeddings:
```python
# Store only contextual embedding if space is limited
# You can always recompute chunk-only embeddings later
if chunk.contextual_embedding is not None:
    store_embedding(chunk.contextual_embedding)
```

---

## Troubleshooting

### Issue: Out of Memory with Late Chunking
**Solution**: Use sliding window instead of full document
```python
chunks = chunker.chunk_with_sliding_context(text, context_window_size=2)
```

### Issue: Markup Chunking Not Finding Structure
**Solution**: Verify document format and adjust document_type
```python
chunks = chunker.chunk(text, document_type="generic")  # Fallback
```

### Issue: Context Window Too Large
**Solution**: Reduce context_window parameter
```python
chunker = ContextChunker(context_window=1)  # Instead of 2 or 3
```

### Issue: Slow Processing
**Solution**: 
1. Reduce chunk_size
2. Use simpler base chunker (token instead of semantic)
3. Disable contextual embeddings for late chunking

---

## Further Reading

- [Chunking Strategies in RAG](https://www.llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex)
- [Late Chunking Paper](https://arxiv.org/abs/2409.04701)
- [Context-Aware Retrieval](https://www.pinecone.io/learn/chunking-strategies/)

---

## Support

For questions or issues:
1. Check the demo script: `examples/chunking_strategies_demo.py`
2. Review configuration: `config.yaml`
3. See implementation: `src/processing/advanced_chunking.py`

