# 📚 Advanced Document Search & RAG System

A production-ready RAG (Retrieval-Augmented Generation) system featuring advanced chunking strategies, document cleaning, batch processing, and semantic search.

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28%2B-red.svg)](https://streamlit.io/)
[![Qdrant](https://img.shields.io/badge/qdrant-vector%20db-green.svg)](https://qdrant.tech/)

---

## ✨ Key Features

### 🎯 Advanced Chunking Strategies
- **Semantic Chunking**: AI-powered semantic boundary detection
- **Context Chunking**: Adds surrounding context for better retrieval
- **Late Chunking**: Contextual embeddings for improved accuracy
- **Markup Chunking**: Structure-aware document splitting
- **Hybrid Chunking**: Combine multiple strategies

### 🧹 Smart Document Cleaning
- Remove table of contents automatically
- Strip acknowledgements and references
- Clean headers and footers
- Smart section detection

### 📤 Batch Processing
- Upload multiple PDFs at once
- Select All / Deselect All functionality
- Progress tracking with real-time statistics
- Individual and aggregate metrics

### 🔍 Advanced Search
- Semantic vector search using Sentence Transformers
- Heuristic reranking with diversity scoring
- Contextual result display
- Configurable score thresholds

### 🗑️ Document Management
- View all indexed documents
- Delete documents from index
- Interactive Qdrant dashboard
- Collection statistics

---

## 🚀 Quick Start

### 1. Installation

```bash
# Install UV (recommended - fast package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone <repository-url>
cd document_search_pdf

# Install dependencies
uv sync

# Or use pip
pip install -r requirements.txt
```

### 2. Start Qdrant Vector Database

```bash
# Using Docker Compose (recommended)
docker-compose up -d qdrant

# Or standalone Docker
docker run -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

**Verify Qdrant is running:**
- Dashboard: http://localhost:6333/dashboard
- REST API: http://localhost:6333

### 3. Launch Applications

#### Enhanced Upload App (Recommended)
```bash
streamlit run apps/streamlit_upload_app_enhanced.py
```

**Features:**
- ✅ Multiple file upload with batch processing
- ✅ All chunking strategies (Semantic, Context, Late, Markup, Hybrid)
- ✅ Document cleaning options
- ✅ Real-time statistics and visualizations
- ✅ Full context display in search results

#### PDF Manager App
```bash
streamlit run apps/pdf_manager_app.py
```

**Features:**
- ✅ Document management (view, delete)
- ✅ Advanced search with filters
- ✅ Separate collection for PDFs
- ✅ Metadata management

#### PubMed Search App
```bash
streamlit run apps/streamlit_pubmed_app.py
```

**Features:**
- ✅ Search pre-indexed PubMed articles
- ✅ Scientific paper search
- ✅ Citation information

---

## 📖 Documentation

### Getting Started
- **[Quick Start Guide](docs/QUICK_START.md)** - 5-minute setup
- **[Installation Guide](docs/INSTALLATION_CHUNKING.md)** - Detailed installation
- **[How to Run](docs/RUN_ENHANCED_APP.md)** - Running applications

### User Guides
- **[Batch Upload Guide](docs/BATCH_UPLOAD_GUIDE.md)** - Upload multiple files
- **[Chunking Strategies Guide](docs/CHUNKING_STRATEGIES_GUIDE.md)** - Choose chunking method
- **[Document Cleaning Guide](docs/DOCUMENT_CLEANING_GUIDE.md)** - Clean documents
- **[Search Features](docs/user-guide/search-features.md)** - Advanced search
- **[PDF Manager](docs/user-guide/pdf-manager.md)** - Document management
- **[Streamlit Apps](docs/user-guide/streamlit-apps.md)** - Application overview

### Utilities & Tools
- **[View Qdrant Database](view_qdrant.py)** - Inspect indexed documents
- **[Delete Documents](delete_documents.py)** - Remove documents from index
- **[Test Connection](scripts/test_qdrant_connection.py)** - Verify setup

### Architecture & Development
- **[System Architecture](docs/architecture/system-architecture.md)** - Overall design
- **[Project Structure](docs/PROJECT_STRUCTURE.md)** - File organization
- **[Testing Guide](docs/development/testing.md)** - Run tests

### Troubleshooting
- **[Troubleshooting Guide](docs/troubleshooting/fixes-summary.md)** - Common issues
- **[Qdrant Quick Start](docs/QDRANT_QUICK_START.md)** - Qdrant setup help
- **[Connection Troubleshooting](docs/TROUBLESHOOT_CONNECTION.md)** - Connection issues

---

## 💡 Common Use Cases

### 1. Index Your Document Collection

```bash
# Start the enhanced app
streamlit run apps/streamlit_upload_app_enhanced.py

# In the UI:
# 1. Configure chunking strategy (sidebar)
# 2. Upload multiple PDFs
# 3. Click "Select All"
# 4. Click "Process Selected"
# 5. Wait for batch processing to complete
```

### 2. Search Indexed Documents

```bash
# Use the search tab in any app
# Enter query: "What is machine learning?"
# View results with full context
# Adjust score threshold for precision/recall
```

### 3. View & Manage Documents

```bash
# Option A: Use PDF Manager App
streamlit run apps/pdf_manager_app.py

# Option B: Use Python utility
python view_qdrant.py

# Option C: Use Qdrant Dashboard
# Open: http://localhost:6333/dashboard
```

### 4. Delete Documents from Index

```bash
# Interactive deletion
python delete_documents.py

# Command-line deletion
python delete_documents.py --collection documents --document-name "file.pdf"

# Delete entire collection (careful!)
python delete_documents.py --collection documents --delete-collection
```

---

## 🎯 Chunking Strategies Comparison

| Strategy | Use Case | Context Aware | LLM Required |
|----------|----------|---------------|--------------|
| **Semantic** | General purpose, good quality | ✓ | ✗ |
| **Context** | When surrounding text matters | ✓✓ | ✗ |
| **Late** | Best retrieval accuracy | ✓✓✓ | ✗ |
| **Markup** | Structured documents (headings) | ✓ | ✗ |
| **Token** | Simple, fast chunking | ✗ | ✗ |
| **Semantic + Late** | High-quality hybrid | ✓✓✓ | ✗ |
| **Markup + Context** | Structured with context | ✓✓ | ✗ |

**Recommendation:** Start with **Semantic** for general use, upgrade to **Semantic + Late** for best quality.

---

## 📊 Project Statistics

- **5 Streamlit Applications** (Enhanced, PDF Manager, PubMed, Upload, Legacy)
- **8 Chunking Strategies** (5 base + 3 hybrid)
- **4 Document Cleaning Methods**
- **3 Search Applications**
- **20+ Utility Scripts**
- **Full Test Coverage** (pytest-based)

---

## 🛠️ Technology Stack

### Core Technologies
- **Python 3.8+** - Programming language
- **Streamlit** - Web UI framework
- **Qdrant** - Vector database
- **Sentence Transformers** - Embedding models
- **Docker** - Containerization

### Key Libraries
- **PyPDF2** / **pdfplumber** - PDF extraction
- **docling** - Document parsing
- **chonkie** - Advanced chunking
- **rich** - Terminal UI
- **plotly** - Visualizations
- **pytest** - Testing

---

## 📁 Project Structure

```
document_search_pdf/
├── apps/                          # Streamlit applications
│   ├── streamlit_upload_app_enhanced.py  # ✨ Enhanced app (recommended)
│   ├── pdf_manager_app.py        # Document management
│   ├── streamlit_pubmed_app.py   # PubMed search
│   └── streamlit_upload_app.py   # Legacy upload app
├── src/                           # Core source code
│   ├── processing/                # Document processing
│   │   ├── advanced_chunking.py   # Chunking strategies
│   │   ├── hybrid_chunking.py     # Hybrid strategies
│   │   ├── document_cleaner.py    # Document cleaning
│   │   ├── document_processor.py  # Main processor
│   │   └── pdf_processor.py       # PDF extraction
│   ├── retrieval/                 # Search & retrieval
│   │   ├── base_rag.py           # Base RAG system
│   │   └── enhanced_rag.py       # Enhanced with reranking
│   └── storage/                   # Vector storage
│       └── vector_store.py       # Qdrant interface
├── scripts/                       # Utility scripts
│   ├── index_pdfs.py             # Batch indexing
│   ├── test_qdrant_connection.py # Connection test
│   └── runners/                  # Shell scripts
├── docs/                          # Documentation
│   ├── getting-started/          # Getting started guides
│   ├── user-guide/               # User guides
│   ├── architecture/             # System architecture
│   └── troubleshooting/          # Troubleshooting
├── tests/                         # Test suite
├── config.yaml                    # Main configuration
├── docker-compose.yml             # Docker setup
├── view_qdrant.py                # View database utility
├── delete_documents.py           # Delete utility
└── README.md                     # This file
```

---

## 🔧 Configuration

Edit `config.yaml` to customize:

```yaml
processing:
  # Chunking strategy
  chunking:
    strategy: semantic  # semantic, token, markup, context, late
    chunk_size: 512
    chunk_overlap: 50
  
  # Document cleaning
  cleaning:
    enabled: true
    remove_toc: true
    remove_acknowledgements: true
    remove_references: false

qdrant:
  host: localhost
  port: 6333
  collection_name: documents

embeddings:
  model_name: "sentence-transformers/all-MiniLM-L6-v2"
  batch_size: 32
```

---

## 🧪 Testing

```bash
# Run all tests
uv run pytest tests/

# Run specific test file
uv run pytest tests/test_document_search.py

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html

# Use test script
./scripts/runners/run_tests.sh
```

---

## 🚦 System Requirements

### Minimum
- Python 3.8+
- 4GB RAM
- Docker (for Qdrant)

### Recommended
- Python 3.10+
- 8GB+ RAM
- SSD storage
- GPU (optional, for faster embeddings)

---

## 🐛 Troubleshooting

### Qdrant Not Running
```bash
# Check if Qdrant is running
curl http://localhost:6333/collections

# Start Qdrant
docker-compose up -d qdrant

# Check logs
docker-compose logs qdrant
```

### Import Errors
```bash
# Reinstall dependencies
uv sync

# Or with pip
pip install -r requirements.txt --force-reinstall
```

### Search Results Too Short
**Issue:** Search results showing only 5-10 words

**Solution:** Re-index documents after updating to latest version (context now stored properly)

```bash
# Delete old collection
python delete_documents.py --collection documents --delete-collection

# Re-upload documents using enhanced app
streamlit run apps/streamlit_upload_app_enhanced.py
```

### Memory Issues with Batch Upload
- Process fewer files at once (5-10 instead of 50+)
- Close other applications
- Increase Docker memory limit

**More help:** See [Troubleshooting Guide](docs/troubleshooting/fixes-summary.md)

---

## 📚 Additional Resources

### Scripts & Utilities
- `view_qdrant.py` - View indexed documents
- `delete_documents.py` - Delete documents interactively
- `scripts/index_pdfs.py` - Batch index PDFs from folder
- `scripts/test_qdrant_connection.py` - Test Qdrant setup

### Example Code
- `examples/chunking_strategies_demo.py` - Chunking examples
- `examples/hybrid_chunking_example.py` - Hybrid chunking
- `examples/document_cleaning_example.py` - Cleaning examples

### Configuration Files
- `config.yaml` - Main configuration
- `config/pdf_config.yaml` - PDF-specific config
- `docker-compose.yml` - Docker setup
- `pyproject.toml` - Python project config

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📄 License

MIT License - See LICENSE file for details.

---

## 🔗 Links

- **Qdrant:** https://qdrant.tech/
- **Streamlit:** https://streamlit.io/
- **Sentence Transformers:** https://www.sbert.net/
- **UV Package Manager:** https://github.com/astral-sh/uv

---

## 🆘 Getting Help

1. Check the [Documentation](docs/)
2. Review [Troubleshooting Guide](docs/troubleshooting/fixes-summary.md)
3. Run diagnostic: `python scripts/test_qdrant_connection.py`
4. Open an issue on GitHub

---

## 🎉 Quick Tips

💡 **Tip 1:** Use the Enhanced Upload App for the best experience with all latest features

💡 **Tip 2:** Start with Semantic chunking, then experiment with Context or Late chunking

💡 **Tip 3:** Enable document cleaning to remove TOC and acknowledgements for cleaner search results

💡 **Tip 4:** Use batch upload with "Select All" to process entire document collections quickly

💡 **Tip 5:** Check Qdrant dashboard (http://localhost:6333/dashboard) to monitor your index

---

**Happy Document Searching! 🚀**
