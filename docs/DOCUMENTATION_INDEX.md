# 📚 Documentation Index

**Complete guide to all documentation in this project.**

---

## 🚀 Start Here

### New to the Project?
1. **[README.md](README.md)** - Project overview and quick start
2. **[QUICK_START.md](QUICK_START.md)** - 5-minute setup guide
3. **[Getting Started Guide](docs/getting-started/installation.md)** - Detailed installation

### Want to Use the System?
1. **[Batch Upload Guide](BATCH_UPLOAD_GUIDE.md)** - Upload multiple PDFs
2. **[Chunking Strategies Guide](docs/CHUNKING_STRATEGIES_GUIDE.md)** - Choose chunking method
3. **[Document Cleaning Guide](docs/DOCUMENT_CLEANING_GUIDE.md)** - Clean documents

---

## 📖 Core Documentation

### Getting Started (Level: Beginner)

| Document | Description | Time to Read |
|----------|-------------|--------------|
| [Quick Start](QUICK_START.md) | Fastest way to get running | 5 min |
| [Installation Guide](docs/getting-started/installation.md) | Complete installation steps | 15 min |
| [How to Run](docs/getting-started/how-to-run.md) | Running all applications | 10 min |
| [Qdrant Quick Start](docs/QDRANT_QUICK_START.md) | Setting up Qdrant database | 10 min |

### User Guides (Level: Intermediate)

| Document | Description | Time to Read |
|----------|-------------|--------------|
| **Upload & Processing** | | |
| [Batch Upload Guide](BATCH_UPLOAD_GUIDE.md) | Upload multiple files at once | 10 min |
| [Chunking Strategies](docs/CHUNKING_STRATEGIES_GUIDE.md) | All chunking methods explained | 20 min |
| [Chunking Quick Reference](docs/CHUNKING_QUICK_REFERENCE.md) | Quick code examples | 5 min |
| [Document Cleaning](docs/DOCUMENT_CLEANING_GUIDE.md) | Clean documents before indexing | 15 min |
| **Search & Management** | | |
| [Search Features](docs/user-guide/search-features.md) | Advanced search capabilities | 10 min |
| [PDF Manager](docs/user-guide/pdf-manager.md) | Document management app | 10 min |
| [Streamlit Apps Guide](docs/user-guide/streamlit-apps.md) | All Streamlit apps | 15 min |

### Utilities & Tools (Level: Practical)

| Tool | Purpose | Documentation |
|------|---------|---------------|
| `view_qdrant.py` | View indexed documents | Run with `--help` |
| `delete_documents.py` | Delete documents from index | See code comments |
| `scripts/test_qdrant_connection.py` | Test Qdrant setup | Run to see output |
| `scripts/index_pdfs.py` | Batch index PDFs | See script header |

---

## 🏗️ Architecture & Development

### System Architecture (Level: Advanced)

| Document | Description | For Whom |
|----------|-------------|----------|
| [System Architecture](docs/architecture/system-architecture.md) | Overall system design | Developers |
| [Project Structure](PROJECT_STRUCTURE.md) | File organization | Developers |
| [Enhanced RAG](docs/architecture/enhanced-rag.md) | RAG system details | AI Engineers |
| [Base RAG](docs/architecture/base-rag.md) | Basic RAG implementation | AI Engineers |

### Development Guides (Level: Advanced)

| Document | Description | For Whom |
|----------|-------------|----------|
| [Testing Guide](docs/development/testing.md) | Running tests | Developers |
| [Testing with UV](docs/development/testing-with-uv.md) | UV-specific testing | Developers |
| [MkDocs Guide](docs/development/mkdocs-guide.md) | Documentation site | Contributors |
| [Cleanup Summary](docs/development/cleanup-summary.md) | Code cleanup notes | Maintainers |

---

## 🛠️ Troubleshooting & Support

### Common Issues

| Issue | Document | Quick Fix |
|-------|----------|-----------|
| Qdrant not connecting | [Troubleshooting](docs/troubleshooting/fixes-summary.md) | `docker-compose up -d qdrant` |
| Import errors | [Installation Guide](docs/getting-started/installation.md) | `uv sync` |
| Search results too short | [Fixes Summary](docs/troubleshooting/fixes-summary.md) | Re-index documents |
| Memory issues | [Batch Upload Guide](BATCH_UPLOAD_GUIDE.md) | Process fewer files |

### Troubleshooting Docs

| Document | Description | When to Use |
|----------|-------------|-------------|
| [Fixes Summary](docs/troubleshooting/fixes-summary.md) | All known issues and fixes | When something breaks |
| [Connection Troubleshooting](TROUBLESHOOT_CONNECTION.md) | Connection problems | Can't connect to Qdrant |
| [Qdrant Local Guide](docs/QDRANT_LOCAL_GUIDE.md) | Local Qdrant setup | Setting up Qdrant |

---

## 📊 Feature-Specific Guides

### Chunking Strategies

| Document | Description | Best For |
|----------|-------------|----------|
| [Complete Guide](docs/CHUNKING_STRATEGIES_GUIDE.md) | All strategies explained | Learning |
| [Quick Reference](docs/CHUNKING_QUICK_REFERENCE.md) | Code snippets | Quick implementation |
| [Visual Comparison](docs/CHUNKING_VISUAL_COMPARISON.md) | Visual examples | Understanding differences |
| [Installation](docs/INSTALLATION_CHUNKING.md) | Installing chunking libs | Setup |

**Related Files:**
- `src/processing/advanced_chunking.py` - Implementation
- `src/processing/hybrid_chunking.py` - Hybrid strategies
- `examples/chunking_strategies_demo.py` - Examples

### Document Cleaning

| Document | Description | Best For |
|----------|-------------|----------|
| [Cleaning Guide](docs/DOCUMENT_CLEANING_GUIDE.md) | Complete cleaning documentation | Learning |
| [Cleaning Summary](DOCUMENT_CLEANING_SUMMARY.md) | Quick overview | Quick reference |

**Related Files:**
- `src/processing/document_cleaner.py` - Implementation
- `examples/document_cleaning_example.py` - Examples

### Batch Upload

| Document | Description | Best For |
|----------|-------------|----------|
| [Batch Upload Guide](BATCH_UPLOAD_GUIDE.md) | Complete batch upload docs | Using batch upload |

**Related Files:**
- `apps/streamlit_upload_app_enhanced.py` - Implementation

---

## 📚 Reference Documentation

### Configuration Files

| File | Purpose | Documentation |
|------|---------|---------------|
| `config.yaml` | Main configuration | See inline comments |
| `config/pdf_config.yaml` | PDF-specific config | See inline comments |
| `docker-compose.yml` | Docker services | See inline comments |
| `pyproject.toml` | Python project config | See inline comments |

### Example Code

| Example | Purpose | Location |
|---------|---------|----------|
| Chunking demo | Try all chunking strategies | `examples/chunking_strategies_demo.py` |
| Hybrid chunking | Combine multiple strategies | `examples/hybrid_chunking_example.py` |
| Document cleaning | Clean documents | `examples/document_cleaning_example.py` |

---

## 🗂️ Documentation by Topic

### Topic: Getting Started
- README.md
- QUICK_START.md
- docs/getting-started/installation.md
- docs/getting-started/how-to-run.md

### Topic: Uploading Documents
- BATCH_UPLOAD_GUIDE.md
- docs/user-guide/pdf-manager.md
- docs/user-guide/streamlit-apps.md

### Topic: Chunking
- docs/CHUNKING_STRATEGIES_GUIDE.md
- docs/CHUNKING_QUICK_REFERENCE.md
- docs/CHUNKING_VISUAL_COMPARISON.md
- docs/INSTALLATION_CHUNKING.md

### Topic: Document Cleaning
- docs/DOCUMENT_CLEANING_GUIDE.md
- DOCUMENT_CLEANING_SUMMARY.md

### Topic: Searching
- docs/user-guide/search-features.md
- docs/architecture/enhanced-rag.md

### Topic: Qdrant
- docs/QDRANT_QUICK_START.md
- docs/QDRANT_LOCAL_GUIDE.md
- TROUBLESHOOT_CONNECTION.md

### Topic: Development
- PROJECT_STRUCTURE.md
- docs/architecture/system-architecture.md
- docs/development/testing.md
- docs/development/testing-with-uv.md

### Topic: Troubleshooting
- docs/troubleshooting/fixes-summary.md
- TROUBLESHOOT_CONNECTION.md

---

## 📦 Documentation by User Role

### For End Users
**You want to:** Use the system to search documents

**Read:**
1. README.md
2. QUICK_START.md
3. BATCH_UPLOAD_GUIDE.md
4. docs/CHUNKING_STRATEGIES_GUIDE.md
5. docs/user-guide/search-features.md

### For Administrators
**You want to:** Set up and maintain the system

**Read:**
1. docs/getting-started/installation.md
2. docs/QDRANT_QUICK_START.md
3. docs/troubleshooting/fixes-summary.md
4. TROUBLESHOOT_CONNECTION.md

### For Developers
**You want to:** Understand and modify the code

**Read:**
1. PROJECT_STRUCTURE.md
2. docs/architecture/system-architecture.md
3. docs/development/testing.md
4. docs/architecture/enhanced-rag.md
5. Source code in `src/`

### For AI Engineers
**You want to:** Understand the RAG pipeline

**Read:**
1. docs/architecture/enhanced-rag.md
2. docs/CHUNKING_STRATEGIES_GUIDE.md
3. docs/DOCUMENT_CLEANING_GUIDE.md
4. Source code in `src/processing/` and `src/retrieval/`

---

## 🗄️ Archived Documentation

**Location:** `docs/archive_readmes/`

These are older versions or outdated documentation kept for reference:
- `docs/archive_readmes/README_PDF.md` - Old PDF readme
- `docs/archive_readmes/README_PDF_UPLOAD.md` - Old upload readme

**Note:** These are superseded by current documentation.

---

## 📝 Temporary/Fix Documentation

These document specific fixes or temporary issues:

| Document | Purpose | Status |
|----------|---------|--------|
| ACTION_PLAN.md | Re-indexing after fix | Temporary |
| CRITICAL_FIX_REINDEX_REQUIRED.md | Critical fix notice | Temporary |
| SEARCH_RESULTS_FIX.md | Search results fix | Resolved |
| STREAMLIT_INTEGRATION_SUMMARY.md | Integration notes | Reference |

**Note:** Read these if you encounter related issues.

---

## 🔍 Finding What You Need

### "I want to..."

**...get started quickly**
→ [QUICK_START.md](QUICK_START.md)

**...upload multiple PDFs**
→ [BATCH_UPLOAD_GUIDE.md](BATCH_UPLOAD_GUIDE.md)

**...understand chunking strategies**
→ [docs/CHUNKING_STRATEGIES_GUIDE.md](docs/CHUNKING_STRATEGIES_GUIDE.md)

**...clean my documents**
→ [docs/DOCUMENT_CLEANING_GUIDE.md](docs/DOCUMENT_CLEANING_GUIDE.md)

**...search my documents**
→ [docs/user-guide/search-features.md](docs/user-guide/search-features.md)

**...delete documents**
→ Run `python delete_documents.py`

**...view what's indexed**
→ Run `python view_qdrant.py`

**...understand the architecture**
→ [docs/architecture/system-architecture.md](docs/architecture/system-architecture.md)

**...run tests**
→ [docs/development/testing.md](docs/development/testing.md)

**...troubleshoot issues**
→ [docs/troubleshooting/fixes-summary.md](docs/troubleshooting/fixes-summary.md)

---

## 📈 Documentation Statistics

- **Total Documentation Files:** 50+ markdown files
- **Main Guides:** 15 comprehensive guides
- **Example Scripts:** 6 working examples
- **Utility Scripts:** 10+ helper tools
- **Architecture Docs:** 3 detailed documents
- **Getting Started Guides:** 4 beginner-friendly guides

---

## 🤝 Contributing to Documentation

### Adding New Documentation

1. Place in appropriate `docs/` subdirectory
2. Update this index
3. Add cross-references
4. Update README.md if major feature

### Documentation Standards

- Use clear, descriptive titles
- Include table of contents for long docs
- Add code examples where relevant
- Cross-reference related documents
- Keep language simple and accessible

---

## 📞 Need Help?

1. **Check this index** for relevant documentation
2. **Run diagnostics:** `python scripts/test_qdrant_connection.py`
3. **View indexed data:** `python view_qdrant.py`
4. **Check troubleshooting:** [docs/troubleshooting/fixes-summary.md](docs/troubleshooting/fixes-summary.md)

---

## 🎯 Most Frequently Read

Based on typical user journey:

1. **README.md** - Everyone starts here
2. **QUICK_START.md** - Fast setup
3. **BATCH_UPLOAD_GUIDE.md** - Upload documents
4. **docs/CHUNKING_STRATEGIES_GUIDE.md** - Choose strategy
5. **docs/user-guide/search-features.md** - Search effectively

---

**Last Updated:** December 2024

**Note:** This index is maintained manually. If you find broken links or missing documentation, please report it.

**Happy Reading! 📚**



