# Advanced Chunking Strategies - Implementation Summary

This document summarizes the implementation of three advanced chunking strategies for your RAG system.

## 📦 What's Been Added

### 1. New Module: `src/processing/advanced_chunking.py`
Complete implementation of three advanced chunking strategies:

#### **Markup Chunking (`MarkupChunker`)**
- Structure-aware chunking based on document markup (headings, sections)
- Preserves hierarchical relationships
- Supports Markdown, HTML, and generic text
- Best for: Technical documentation, academic papers

#### **Context Chunking (`ContextChunker`)**
- Adds surrounding context (previous/next chunks) to each chunk
- Improves cross-boundary understanding
- Configurable context window size
- Best for: Long narratives, interconnected content

#### **Late Chunking (`LateChunker`)**
- Computes embeddings for full document before chunking
- Creates contextual embeddings (blend of chunk + document)
- Supports sliding window for long documents
- Best for: Maximum retrieval accuracy

#### **Unified Interface (`UnifiedChunker`)**
- Single interface for all chunking strategies
- Easy switching between strategies
- Consistent API
- Includes comparison utilities

### 2. Demo Script: `examples/chunking_strategies_demo.py`
Interactive demonstration showing:
- How each strategy works
- Practical examples with sample documents
- Strategy comparison with statistics
- Usage patterns and best practices

### 3. Production Script: `scripts/process_with_advanced_chunking.py`
Ready-to-use script for:
- Processing documents with any chunking strategy
- Storing in Qdrant vector database
- Batch processing of directories
- Search functionality with strategy-specific features

### 4. Documentation

#### **Comprehensive Guide** (`docs/CHUNKING_STRATEGIES_GUIDE.md`)
- Detailed explanation of each strategy
- Benefits and use cases
- Code examples
- Integration instructions
- Performance considerations
- Troubleshooting

#### **Quick Reference** (`docs/CHUNKING_QUICK_REFERENCE.md`)
- Quick comparison table
- Code snippets
- Decision tree for strategy selection
- Common parameters
- Pro tips

### 5. Updated Configuration: `config.yaml`
Extended chunking configuration section:
```yaml
processing:
  chunking:
    strategy: semantic  # Now supports: markup, context, late
    
    markup:
      enabled: false
      preserve_hierarchy: true
      document_type: markdown
    
    context:
      enabled: false
      context_window: 2
      overlap_size: 100
    
    late:
      enabled: false
      compute_contextual: true
      use_sliding_window: false
      context_window_size: 3
```

---

## 🚀 Quick Start

### Run the Demo
```bash
cd /Users/sankar/sankar/courses/llm/document_search_pdf
python examples/chunking_strategies_demo.py
```

### Process Documents with Context Chunking
```bash
python scripts/process_with_advanced_chunking.py \
    --strategy context \
    --input /path/to/documents \
    --chunk-size 512 \
    --collection my_documents
```

### Use in Your Code
```python
from src.processing.advanced_chunking import UnifiedChunker, ChunkingStrategy

# Initialize chunker with desired strategy
chunker = UnifiedChunker(
    strategy=ChunkingStrategy.CONTEXT,  # or MARKUP, LATE
    chunk_size=512,
    overlap_size=50
)

# Chunk your text
text = "Your document text..."
chunks = chunker.chunk(text)

# Access chunk information
for chunk in chunks:
    print(f"Text: {chunk.text}")
    print(f"Metadata: {chunk.metadata}")
    if chunk.context_before:
        print(f"Context: {chunk.context_before}")
```

---

## 📊 Strategy Comparison

| Feature | Markup | Context | Late |
|---------|--------|---------|------|
| **Speed** | Fast ⚡⚡⚡ | Medium ⚡⚡ | Slow ⚡ |
| **Memory** | Low 💾 | Medium 💾💾 | High 💾💾💾 |
| **Accuracy** | Good ⭐⭐⭐ | Very Good ⭐⭐⭐⭐ | Excellent ⭐⭐⭐⭐⭐ |
| **Setup** | Simple | Moderate | Complex |
| **Storage** | Standard | +20-30% | +40-50% |

### When to Use Each

**Markup Chunking**:
- ✅ Structured documents (Markdown, HTML)
- ✅ Need to preserve document hierarchy
- ✅ Technical documentation
- ✅ Academic papers with sections

**Context Chunking**:
- ✅ Long documents with flowing text
- ✅ Cross-references between sections
- ✅ Need balanced performance/accuracy
- ✅ Narrative or connected content

**Late Chunking**:
- ✅ Maximum retrieval accuracy required
- ✅ Global document context is crucial
- ✅ Technical documents with specialized terms
- ✅ Have computational resources available

---

## 🔧 Integration Examples

### 1. With Existing DocumentProcessor

```python
from src.processing.document_processor import DocumentProcessor
from src.processing.advanced_chunking import LateChunker

class EnhancedProcessor(DocumentProcessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.late_chunker = LateChunker(chunk_size=512)
    
    def _chunk_document(self, text, metadata):
        # Use late chunking instead of default
        chunks = self.late_chunker.chunk(text)
        
        # Format for your system
        formatted = []
        for chunk in chunks:
            formatted.append({
                'content': chunk.text,
                'embedding': chunk.contextual_embedding,
                'metadata': {**metadata, **chunk.metadata}
            })
        return formatted
```

### 2. With Qdrant Storage

```python
from src.processing.advanced_chunking import ContextChunker
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

# Initialize
chunker = ContextChunker(chunk_size=512, context_window=2)
client = QdrantClient(host="localhost", port=6333)

# Process and store
text = "Your document..."
chunks = chunker.chunk(text)

points = []
for i, chunk in enumerate(chunks):
    # Get embedding
    embedding = model.encode(chunk.text)
    
    # Create point with context
    point = PointStruct(
        id=i,
        vector=embedding.tolist(),
        payload={
            'text': chunk.text,
            'context_before': chunk.context_before,
            'context_after': chunk.context_after,
            'metadata': chunk.metadata
        }
    )
    points.append(point)

client.upsert(collection_name="documents", points=points)
```

### 3. Hybrid Approach

```python
from src.processing.advanced_chunking import MarkupChunker, LateChunker

# First, use markup to preserve structure
markup_chunker = MarkupChunker(max_chunk_size=2000)
sections = markup_chunker.chunk(markdown_text, document_type="markdown")

# Then, apply late chunking to large sections
late_chunker = LateChunker(chunk_size=512)

all_chunks = []
for section in sections:
    if len(section.text) > 512:
        # Further chunk large sections with late chunking
        sub_chunks = late_chunker.chunk(section.text)
        for sub_chunk in sub_chunks:
            # Preserve section hierarchy
            sub_chunk.metadata['section'] = section.heading
            sub_chunk.metadata['hierarchy'] = section.section_hierarchy
            all_chunks.append(sub_chunk)
    else:
        all_chunks.append(section)
```

---

## 📈 Performance Tips

### 1. Memory Optimization

For late chunking with long documents:
```python
# Use sliding window instead of full document
chunks = late_chunker.chunk_with_sliding_context(
    text,
    context_window_size=2  # Smaller window = less memory
)
```

### 2. Speed Optimization

For faster processing:
```python
# Start with markup for structure
markup_chunks = markup_chunker.chunk(text)

# Then add context only where needed
for chunk in markup_chunks:
    if chunk.needs_more_context:  # Your logic
        enhanced = context_chunker.chunk(chunk.text)
```

### 3. Storage Optimization

Store only what you need:
```python
# For late chunking, store contextual embedding only
chunk_data = {
    'text': chunk.text,
    'embedding': chunk.contextual_embedding,  # Not both embeddings
    'metadata': chunk.metadata
}
```

---

## 🔍 Features by Strategy

### Markup Chunking Features
- ✅ Hierarchical section tracking
- ✅ Heading preservation
- ✅ Structure-aware splits
- ✅ Path to section (e.g., "Ch1 > Sec1.2 > SubSec1.2.1")
- ✅ Configurable min/max chunk sizes
- ✅ Multiple document type support

### Context Chunking Features
- ✅ Before/after context
- ✅ Configurable context window (1-3+ chunks)
- ✅ Flexible overlap size
- ✅ Works with any base chunker (semantic/token)
- ✅ `get_full_context()` helper method
- ✅ Context inclusion flags in metadata

### Late Chunking Features
- ✅ Full document embeddings
- ✅ Contextual embeddings (blended)
- ✅ Sliding window mode for long documents
- ✅ Configurable blend ratio (70/30 default)
- ✅ Both chunk and contextual embeddings available
- ✅ Automatic normalization

---

## 📝 Configuration Reference

### Markup Chunking
```yaml
markup:
  enabled: true
  max_chunk_size: 1000
  min_chunk_size: 100
  preserve_hierarchy: true
  document_type: markdown  # or html, generic
```

### Context Chunking
```yaml
context:
  enabled: true
  chunk_size: 512
  overlap_size: 100
  context_window: 2  # Number of surrounding chunks
```

### Late Chunking
```yaml
late:
  enabled: true
  chunk_size: 512
  overlap_size: 50
  compute_contextual: true
  use_sliding_window: false
  context_window_size: 3
  max_context_length: 8192
```

---

## 🎯 Decision Tree

```
What type of documents do you have?

├─ Structured (Markdown/HTML with headings)
│  └─ Use MARKUP chunking
│     └─ Need maximum accuracy too?
│        └─ YES: Apply LATE chunking to markup chunks
│        └─ NO: Use MARKUP alone
│
├─ Long narratives / flowing text
│  └─ Are resources constrained?
│     ├─ YES: Use CONTEXT chunking
│     └─ NO: Use LATE chunking
│
└─ General mixed content
   └─ Is accuracy critical?
      ├─ YES: Use LATE chunking
      └─ NO: Use CONTEXT chunking
```

---

## 🧪 Testing Your Strategy

Run the comparison tool:
```python
from src.processing.advanced_chunking import compare_chunking_strategies

# Load your sample document
with open('sample_document.txt', 'r') as f:
    text = f.read()

# Compare all strategies
results = compare_chunking_strategies(text)

# Review statistics
for strategy, stats in results.items():
    print(f"\n{strategy}:")
    print(f"  Chunks: {stats['num_chunks']}")
    print(f"  Avg size: {stats['avg_chunk_size']:.0f}")
    print(f"  Accuracy features: ", end='')
    if stats['has_embeddings']:
        print("✓ Embeddings", end=' ')
    if stats['has_context']:
        print("✓ Context", end=' ')
    if stats['has_hierarchy']:
        print("✓ Hierarchy", end='')
```

---

## 📚 Additional Resources

### Files Added
- `src/processing/advanced_chunking.py` - Core implementation
- `examples/chunking_strategies_demo.py` - Interactive demo
- `scripts/process_with_advanced_chunking.py` - Production script
- `docs/CHUNKING_STRATEGIES_GUIDE.md` - Comprehensive guide
- `docs/CHUNKING_QUICK_REFERENCE.md` - Quick reference
- `examples/README.md` - Examples documentation

### Dependencies Required
```bash
pip install chonkie sentence-transformers docling qdrant-client numpy tqdm
```

### Documentation
- **Full Guide**: `docs/CHUNKING_STRATEGIES_GUIDE.md`
- **Quick Reference**: `docs/CHUNKING_QUICK_REFERENCE.md`
- **Examples**: `examples/README.md`

---

## 🎉 Next Steps

1. **Try the Demo**:
   ```bash
   python examples/chunking_strategies_demo.py
   ```

2. **Test on Your Data**:
   ```bash
   python scripts/process_with_advanced_chunking.py \
       --strategy context \
       --input /path/to/your/docs \
       --query "test query"
   ```

3. **Integrate into Your Pipeline**:
   - Review integration examples above
   - Choose appropriate strategy for your documents
   - Update your document processor
   - Configure in `config.yaml`

4. **Optimize**:
   - Run comparison on your documents
   - Tune chunk_size and overlap parameters
   - Monitor performance and accuracy
   - Adjust strategy as needed

---

## 💬 Support

If you have questions:
1. Check the comprehensive guide: `docs/CHUNKING_STRATEGIES_GUIDE.md`
2. Review the quick reference: `docs/CHUNKING_QUICK_REFERENCE.md`
3. Run the demo: `python examples/chunking_strategies_demo.py`
4. See working examples in `examples/` directory

Happy chunking! 🚀

