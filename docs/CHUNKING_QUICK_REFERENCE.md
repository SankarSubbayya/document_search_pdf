# Chunking Strategies Quick Reference

## 📋 Quick Comparison

| Feature | Markup | Context | Late |
|---------|--------|---------|------|
| **Speed** | ⚡⚡⚡ Fast | ⚡⚡ Medium | ⚡ Slow |
| **Memory** | 💾 Low | 💾💾 Medium | 💾💾💾 High |
| **Accuracy** | ⭐⭐⭐ Good | ⭐⭐⭐⭐ Very Good | ⭐⭐⭐⭐⭐ Excellent |
| **Best For** | Structured docs | Long narratives | Critical accuracy |

---

## 🚀 Quick Start

### Markup Chunking (Structure-Aware)
```python
from src.processing.advanced_chunking import MarkupChunker

chunker = MarkupChunker(max_chunk_size=1000)
chunks = chunker.chunk(text, document_type="markdown")
```

### Context Chunking (With Surrounding Context)
```python
from src.processing.advanced_chunking import ContextChunker

chunker = ContextChunker(chunk_size=512, context_window=2)
chunks = chunker.chunk(text)
```

### Late Chunking (Contextual Embeddings)
```python
from src.processing.advanced_chunking import LateChunker

chunker = LateChunker(chunk_size=512)
chunks = chunker.chunk(text, compute_contextual_embeddings=True)
```

### Unified Interface (Easy Switching)
```python
from src.processing.advanced_chunking import UnifiedChunker, ChunkingStrategy

chunker = UnifiedChunker(strategy=ChunkingStrategy.LATE, chunk_size=512)
chunks = chunker.chunk(text)
```

---

## ⚙️ Configuration

### In config.yaml

```yaml
processing:
  chunking:
    strategy: late  # Options: semantic, token, markup, context, late
    
    markup:
      enabled: true
      preserve_hierarchy: true
      document_type: markdown
    
    context:
      enabled: true
      context_window: 2
      overlap_size: 100
    
    late:
      enabled: true
      compute_contextual: true
      use_sliding_window: false
      context_window_size: 3
```

---

## 📊 When to Use Each Strategy

### Use Markup When:
✅ You have structured documents (Markdown, HTML)  
✅ Preserving document hierarchy is important  
✅ Documents have clear sections/headings  
✅ Speed is important  

### Use Context When:
✅ Context across chunk boundaries matters  
✅ You have long, flowing text  
✅ Documents have many cross-references  
✅ Balanced speed/accuracy trade-off needed  

### Use Late When:
✅ Retrieval accuracy is critical  
✅ Global document context is important  
✅ You need the best embeddings  
✅ Computational resources available  

---

## 🔧 Common Parameters

```python
# Chunk size (characters)
chunk_size = 512          # Standard
chunk_size = 256          # Small (for precise retrieval)
chunk_size = 1024         # Large (for comprehensive context)

# Overlap size
overlap_size = 50         # Standard (10% of chunk_size)
overlap_size = 100        # High overlap (20%)

# Context window (for Context/Late chunking)
context_window = 1        # Minimal context
context_window = 2        # Standard (recommended)
context_window = 3        # Maximum context
```

---

## 💡 Pro Tips

### 1. Start Simple, Then Optimize
```python
# Start with semantic chunking
strategy = ChunkingStrategy.SEMANTIC

# If accuracy is insufficient, try context
strategy = ChunkingStrategy.CONTEXT

# For best results, use late
strategy = ChunkingStrategy.LATE
```

### 2. Combine Strategies
```python
# Use markup to preserve structure, then add context
markup_chunker = MarkupChunker()
markup_chunks = markup_chunker.chunk(text, document_type="markdown")

# Then apply context to markup chunks
# (Implementation in advanced_chunking.py)
```

### 3. Tune for Your Data
```python
from src.processing.advanced_chunking import compare_chunking_strategies

# Test different strategies on your documents
results = compare_chunking_strategies(your_sample_text)
print(results)
```

### 4. Storage Optimization
```python
# For late chunking, store contextual embedding only
chunk_dict = {
    'text': chunk.text,
    'embedding': chunk.contextual_embedding  # More informative
}

# You can always recompute chunk-only embeddings later
```

---

## 🎯 Decision Tree

```
Do you have structured documents (Markdown/HTML)?
  ├─ YES → Use MARKUP chunking
  └─ NO → Is retrieval accuracy critical?
        ├─ YES → Use LATE chunking
        └─ NO → Do you need cross-boundary context?
              ├─ YES → Use CONTEXT chunking
              └─ NO → Use SEMANTIC chunking
```

---

## 📝 Code Examples

### Example 1: Process PDF with Late Chunking
```python
from src.processing.pdf_processor import PDFProcessor
from src.processing.advanced_chunking import LateChunker

# Extract PDF content
pdf_processor = PDFProcessor()
pdf_content = pdf_processor.process_pdf("document.pdf")

# Chunk with late chunking
chunker = LateChunker(chunk_size=512)
chunks = chunker.chunk(pdf_content.text)

# Store with embeddings
for chunk in chunks:
    store_in_vector_db(
        text=chunk.text,
        embedding=chunk.contextual_embedding
    )
```

### Example 2: Process Markdown with Markup Chunking
```python
from src.processing.advanced_chunking import MarkupChunker

# Read markdown file
with open("document.md", "r") as f:
    text = f.read()

# Chunk by structure
chunker = MarkupChunker(max_chunk_size=1000, preserve_hierarchy=True)
chunks = chunker.chunk(text, document_type="markdown")

# Access hierarchy
for chunk in chunks:
    print(f"Section: {' > '.join(chunk.section_hierarchy)}")
    print(f"Content: {chunk.text}")
```

### Example 3: Compare All Strategies
```python
from src.processing.advanced_chunking import UnifiedChunker, ChunkingStrategy

strategies = [
    ChunkingStrategy.MARKUP,
    ChunkingStrategy.CONTEXT,
    ChunkingStrategy.LATE
]

for strategy in strategies:
    chunker = UnifiedChunker(strategy=strategy, chunk_size=512)
    chunks = chunker.chunk(your_text)
    
    print(f"\n{strategy.value}:")
    print(f"  Chunks: {len(chunks)}")
    print(f"  Avg size: {sum(len(c.text) for c in chunks) / len(chunks):.0f}")
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Out of memory with late chunking | Use `chunk_with_sliding_context()` instead |
| Markup not detecting structure | Set `document_type="generic"` for fallback |
| Chunks too small/large | Adjust `chunk_size` parameter |
| Slow processing | Reduce `context_window` or use simpler strategy |
| Poor retrieval results | Try late chunking with `compute_contextual=True` |

---

## 📚 Additional Resources

- **Full Guide**: `docs/CHUNKING_STRATEGIES_GUIDE.md`
- **Demo Script**: `examples/chunking_strategies_demo.py`
- **Implementation**: `src/processing/advanced_chunking.py`
- **Config**: `config.yaml` (processing.chunking section)

---

## 🎓 Key Concepts

### Markup Chunking
- Chunks based on **document structure**
- Preserves **hierarchical relationships**
- Best for **structured documents**

### Context Chunking
- Adds **surrounding text** to each chunk
- Improves **cross-boundary understanding**
- Best for **connected narratives**

### Late Chunking
- Computes **embeddings first**, then chunks
- Creates **contextual embeddings**
- Best for **maximum accuracy**

---

**Run the demo to see all strategies in action:**
```bash
python examples/chunking_strategies_demo.py
```

