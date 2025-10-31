# Installing Advanced Chunking Strategies

Complete installation guide for using markup, context, and late chunking in your RAG system.

---

## 📋 Prerequisites

- Python 3.8 or higher
- pip or conda package manager
- Existing document_search_pdf project

---

## 🚀 Quick Installation

### Step 1: Install Required Packages

```bash
# Navigate to project directory
cd /Users/sankar/sankar/courses/llm/document_search_pdf

# Install dependencies
pip install chonkie sentence-transformers docling qdrant-client numpy tqdm pyyaml
```

### Step 2: Verify Installation

```bash
# Test import
python -c "from src.processing.advanced_chunking import UnifiedChunker; print('✓ Installation successful!')"
```

### Step 3: Run Demo

```bash
# Run the interactive demo
python examples/chunking_strategies_demo.py
```

If the demo runs successfully, you're all set! 🎉

---

## 📦 Detailed Package Information

### Core Dependencies

#### 1. **chonkie** (Chunking library)
```bash
pip install chonkie
```
- Provides `SemanticChunker` and `TokenChunker`
- Used as base chunkers for advanced strategies
- Includes embedding utilities

#### 2. **sentence-transformers** (Embedding models)
```bash
pip install sentence-transformers
```
- Provides embedding models for semantic search
- Default model: `all-MiniLM-L6-v2` (384 dimensions)
- Alternative: `all-mpnet-base-v2` (768 dimensions, better quality)

#### 3. **docling** (Document processing)
```bash
pip install docling
```
- Advanced document parsing
- Handles PDF, DOCX, HTML, Markdown
- Extracts tables, images, and metadata

#### 4. **qdrant-client** (Vector database)
```bash
pip install qdrant-client
```
- Client for Qdrant vector database
- Required for storage and retrieval
- Local or cloud deployment support

#### 5. **numpy** (Numerical operations)
```bash
pip install numpy
```
- Array operations for embeddings
- Vector normalization and blending
- Required for late chunking

---

## 🔧 Optional Dependencies

### For PDF Processing
```bash
# If not already installed
pip install PyPDF2 pdfplumber pypdf pymupdf pdf2image pytesseract pillow
```

### For OCR Support (optional)
```bash
# Install Tesseract OCR (system-level)
# macOS:
brew install tesseract

# Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# Then install Python wrapper:
pip install pytesseract
```

---

## 🐳 Docker Installation (Alternative)

If you prefer Docker:

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install chunking dependencies
RUN pip install chonkie sentence-transformers docling qdrant-client

# Copy application
COPY . .

CMD ["python", "examples/chunking_strategies_demo.py"]
```

Build and run:
```bash
docker build -t document-search-chunking .
docker run -it document-search-chunking
```

---

## 📝 Requirements File

Add to your `requirements.txt`:

```txt
# Advanced Chunking Dependencies
chonkie>=0.1.0
sentence-transformers>=2.2.0
docling>=1.0.0
qdrant-client>=1.7.0
numpy>=1.21.0
tqdm>=4.65.0
pyyaml>=6.0

# Existing dependencies
PyPDF2>=3.0.0
pdfplumber>=0.10.0
pypdf>=3.17.0
```

Install all at once:
```bash
pip install -r requirements.txt
```

---

## 🧪 Verification Tests

### Test 1: Import Check
```python
# test_imports.py
try:
    from src.processing.advanced_chunking import (
        MarkupChunker,
        ContextChunker,
        LateChunker,
        UnifiedChunker,
        ChunkingStrategy
    )
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import failed: {e}")
```

### Test 2: Chunking Test
```python
# test_chunking.py
from src.processing.advanced_chunking import UnifiedChunker, ChunkingStrategy

text = "This is a test document. It has multiple sentences. We want to chunk it properly."

for strategy in [ChunkingStrategy.MARKUP, ChunkingStrategy.CONTEXT, ChunkingStrategy.LATE]:
    try:
        chunker = UnifiedChunker(strategy=strategy, chunk_size=100)
        chunks = chunker.chunk(text)
        print(f"✓ {strategy.value}: {len(chunks)} chunks created")
    except Exception as e:
        print(f"✗ {strategy.value} failed: {e}")
```

### Test 3: Qdrant Connection
```python
# test_qdrant.py
from qdrant_client import QdrantClient

try:
    client = QdrantClient(host="localhost", port=6333)
    collections = client.get_collections()
    print(f"✓ Qdrant connected: {len(collections.collections)} collections")
except Exception as e:
    print(f"✗ Qdrant connection failed: {e}")
    print("  Make sure Qdrant is running: docker-compose up -d")
```

Run all tests:
```bash
python test_imports.py && python test_chunking.py && python test_qdrant.py
```

---

## 🔍 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'chonkie'"

**Solution**:
```bash
pip install chonkie
# or
pip install --upgrade chonkie
```

### Issue: "No module named 'sentence_transformers'"

**Solution**:
```bash
pip install sentence-transformers
```

On first run, models will download automatically (~100MB).

### Issue: "Could not connect to Qdrant"

**Solution**:
```bash
# Start Qdrant using Docker
docker-compose up -d qdrant

# Or install locally
docker pull qdrant/qdrant
docker run -p 6333:6333 qdrant/qdrant
```

### Issue: "Out of memory with late chunking"

**Solution 1**: Use sliding window
```python
chunks = late_chunker.chunk_with_sliding_context(text, context_window_size=2)
```

**Solution 2**: Reduce chunk size
```python
chunker = LateChunker(chunk_size=256)  # Instead of 512
```

**Solution 3**: Process in batches
```python
# Process documents in smaller batches
for batch in batch_documents(documents, batch_size=10):
    process_batch(batch)
```

### Issue: "ImportError: cannot import name 'SentenceTransformerEmbeddings'"

**Solution**: Update chonkie
```bash
pip install --upgrade chonkie
```

### Issue: "Slow embedding computation"

**Solution**: Use GPU if available
```python
from sentence_transformers import SentenceTransformer

# Force GPU usage
model = SentenceTransformer('all-MiniLM-L6-v2', device='cuda')

# Or MPS for Mac M1/M2
model = SentenceTransformer('all-MiniLM-L6-v2', device='mps')
```

---

## 🎯 Model Selection

### Small & Fast (Recommended for Most)
```python
embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
# Size: 384 dimensions
# Speed: Very fast
# Quality: Good
```

### Medium Quality
```python
embedding_model = "sentence-transformers/all-mpnet-base-v2"
# Size: 768 dimensions
# Speed: Medium
# Quality: Better
```

### High Quality (If resources available)
```python
embedding_model = "sentence-transformers/all-distilroberta-v1"
# Size: 768 dimensions
# Speed: Slower
# Quality: Best
```

---

## 📊 System Requirements

### Minimum Requirements
- **RAM**: 4GB
- **Storage**: 2GB free (for models)
- **CPU**: Dual-core processor
- **Python**: 3.8+

### Recommended for Late Chunking
- **RAM**: 8GB or more
- **Storage**: 5GB free
- **CPU**: Quad-core or better
- **GPU**: Optional but helpful (CUDA or MPS)

### For Large-Scale Processing
- **RAM**: 16GB+
- **Storage**: 10GB+
- **CPU**: 8+ cores
- **GPU**: NVIDIA GPU with 4GB+ VRAM

---

## ⚙️ Configuration

After installation, configure in `config.yaml`:

```yaml
processing:
  chunking:
    # Choose your strategy
    strategy: context  # markup, context, or late
    
    chunk_size: 512
    chunk_overlap: 50
    
    # Strategy-specific settings
    markup:
      enabled: false
      preserve_hierarchy: true
      document_type: markdown
    
    context:
      enabled: true
      context_window: 2
      overlap_size: 100
    
    late:
      enabled: false
      compute_contextual: true
      use_sliding_window: false
      context_window_size: 3

embeddings:
  model: sentence-transformers/all-MiniLM-L6-v2
  device: cpu  # or cuda, mps
  batch_size: 32
```

---

## 🚀 Next Steps

1. **Verify Installation**:
   ```bash
   python examples/chunking_strategies_demo.py
   ```

2. **Process Your Documents**:
   ```bash
   python scripts/process_with_advanced_chunking.py \
       --strategy context \
       --input /path/to/docs
   ```

3. **Read the Guides**:
   - Quick Reference: `docs/CHUNKING_QUICK_REFERENCE.md`
   - Full Guide: `docs/CHUNKING_STRATEGIES_GUIDE.md`
   - Visual Comparison: `docs/CHUNKING_VISUAL_COMPARISON.md`

---

## 📞 Support

If you encounter issues:

1. Check this troubleshooting section
2. Verify all dependencies are installed: `pip list | grep -E "(chonkie|sentence|docling|qdrant)"`
3. Run verification tests above
4. Check the full documentation in `docs/`

---

## ✅ Installation Checklist

- [ ] Python 3.8+ installed
- [ ] All pip packages installed (`pip install -r requirements.txt`)
- [ ] Qdrant running (if using vector storage)
- [ ] Demo runs successfully
- [ ] Test scripts pass
- [ ] Configuration updated

Once all checked, you're ready to use advanced chunking! 🎉

