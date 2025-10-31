# Examples Directory

This directory contains example scripts demonstrating advanced features of the document search system.

## Available Examples

### 1. Chunking Strategies Demo (`chunking_strategies_demo.py`)

**Purpose**: Demonstrates three advanced chunking strategies for RAG systems.

**What it shows**:
- **Markup Chunking**: Structure-aware chunking based on document headings and sections
- **Context Chunking**: Chunks with surrounding context for better retrieval
- **Late Chunking**: Contextual embeddings computed before chunking
- **Unified Interface**: Easy switching between strategies
- **Strategy Comparison**: Side-by-side comparison with statistics

**How to run**:
```bash
cd /Users/sankar/sankar/courses/llm/document_search_pdf
python examples/chunking_strategies_demo.py
```

**Output**: Interactive demo showing each chunking strategy with example documents.

---

## Related Scripts

### Process with Advanced Chunking (`scripts/process_with_advanced_chunking.py`)

Production-ready script for processing documents with advanced chunking and storing in Qdrant.

**Usage**:
```bash
# Process with context chunking
python scripts/process_with_advanced_chunking.py \
    --strategy context \
    --input /path/to/documents \
    --chunk-size 512 \
    --collection my_documents

# Process with late chunking (best accuracy)
python scripts/process_with_advanced_chunking.py \
    --strategy late \
    --input /path/to/documents \
    --collection my_documents

# Process with markup chunking (for structured docs)
python scripts/process_with_advanced_chunking.py \
    --strategy markup \
    --input /path/to/documents \
    --collection my_documents

# Process and test search
python scripts/process_with_advanced_chunking.py \
    --strategy context \
    --input /path/to/documents \
    --query "What is machine learning?"
```

---

## Documentation

For detailed information about chunking strategies:

- **Full Guide**: [`docs/CHUNKING_STRATEGIES_GUIDE.md`](../docs/CHUNKING_STRATEGIES_GUIDE.md)
- **Quick Reference**: [`docs/CHUNKING_QUICK_REFERENCE.md`](../docs/CHUNKING_QUICK_REFERENCE.md)

---

## Quick Start

### 1. Install Dependencies

Make sure you have the required packages:

```bash
pip install chonkie sentence-transformers docling qdrant-client
```

### 2. Run the Demo

```bash
python examples/chunking_strategies_demo.py
```

### 3. Try Different Strategies

Experiment with each strategy on your own data:

```python
from src.processing.advanced_chunking import UnifiedChunker, ChunkingStrategy

# Your document text
with open('your_document.md', 'r') as f:
    text = f.read()

# Try different strategies
strategies = [
    ChunkingStrategy.MARKUP,
    ChunkingStrategy.CONTEXT,
    ChunkingStrategy.LATE
]

for strategy in strategies:
    chunker = UnifiedChunker(strategy=strategy, chunk_size=512)
    chunks = chunker.chunk(text)
    print(f"{strategy.value}: {len(chunks)} chunks")
```

---

## Examples Overview

### Markup Chunking Example

```python
from src.processing.advanced_chunking import MarkupChunker

chunker = MarkupChunker(max_chunk_size=1000, preserve_hierarchy=True)
chunks = chunker.chunk(markdown_text, document_type="markdown")

for chunk in chunks:
    print(f"Section: {' > '.join(chunk.section_hierarchy)}")
    print(f"Content: {chunk.text[:100]}...")
```

**Best for**: Technical documentation, academic papers, structured content

---

### Context Chunking Example

```python
from src.processing.advanced_chunking import ContextChunker

chunker = ContextChunker(
    chunk_size=512,
    overlap_size=100,
    context_window=2  # Include 2 chunks before/after
)
chunks = chunker.chunk(text)

for chunk in chunks:
    if chunk.context_before:
        print(f"Previous context: {chunk.context_before}")
    print(f"Main content: {chunk.text}")
    if chunk.context_after:
        print(f"Next context: {chunk.context_after}")
```

**Best for**: Long narratives, flowing text, interconnected content

---

### Late Chunking Example

```python
from src.processing.advanced_chunking import LateChunker

chunker = LateChunker(
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    chunk_size=512
)
chunks = chunker.chunk(text, compute_contextual_embeddings=True)

for chunk in chunks:
    print(f"Text: {chunk.text[:100]}...")
    print(f"Embedding shape: {chunk.embedding.shape}")
    print(f"Contextual embedding shape: {chunk.contextual_embedding.shape}")
```

**Best for**: Critical accuracy needs, global context important

---

## Configuration

You can configure chunking strategies in `config.yaml`:

```yaml
processing:
  chunking:
    strategy: context  # Choose: semantic, token, markup, context, late
    chunk_size: 512
    chunk_overlap: 50
    
    markup:
      enabled: true
      preserve_hierarchy: true
    
    context:
      enabled: true
      context_window: 2
    
    late:
      enabled: true
      compute_contextual: true
      use_sliding_window: false
```

---

## Performance Comparison

| Strategy | Speed | Memory | Accuracy | Best For |
|----------|-------|--------|----------|----------|
| Token | ⚡⚡⚡⚡⚡ | 💾 | ⭐⭐ | Quick prototyping |
| Semantic | ⚡⚡⚡⚡ | 💾💾 | ⭐⭐⭐ | General purpose |
| Markup | ⚡⚡⚡ | 💾 | ⭐⭐⭐ | Structured docs |
| Context | ⚡⚡ | 💾💾 | ⭐⭐⭐⭐ | Long narratives |
| Late | ⚡ | 💾💾💾 | ⭐⭐⭐⭐⭐ | Maximum accuracy |

---

## Troubleshooting

### Issue: ImportError for chonkie or docling

**Solution**:
```bash
pip install chonkie docling sentence-transformers
```

### Issue: Out of memory with late chunking

**Solution**: Use sliding window instead:
```python
chunks = chunker.chunk_with_sliding_context(text, context_window_size=2)
```

### Issue: Demo script not found

**Solution**: Make sure you're in the project root:
```bash
cd /Users/sankar/sankar/courses/llm/document_search_pdf
python examples/chunking_strategies_demo.py
```

---

## Contributing

To add new examples:

1. Create a new Python file in this directory
2. Add a descriptive docstring at the top
3. Update this README with usage instructions
4. Test your example thoroughly

---

## Support

For questions or issues:
- Check the full documentation: `docs/CHUNKING_STRATEGIES_GUIDE.md`
- Review the implementation: `src/processing/advanced_chunking.py`
- Run the demo: `python examples/chunking_strategies_demo.py`

