# 📚 Documentation Structure

This document describes the organized documentation structure for the Document Search RAG project.

## 📁 Documentation Organization

All documentation has been organized into the `docs/` directory with the following structure:

```
docs/
├── index.md                           # Main documentation homepage
├── DOCUMENTATION_STRUCTURE.md         # This file
│
├── getting-started/                   # Setup and installation guides
│   ├── how-to-run.md                 # Application launch instructions
│   ├── installation.md               # Dependency installation
│   ├── load-pubmed-index.md          # PubMed data setup
│   └── install-tesseract.md          # OCR setup guide
│
├── user-guide/                        # User documentation
│   ├── pdf-manager.md                # PDF Manager app guide
│   ├── streamlit-apps.md             # Streamlit interfaces
│   ├── search-features.md            # Search capabilities
│   └── new-layout.md                 # UI updates and controls
│
├── architecture/                      # Technical architecture
│   ├── system-architecture.md        # Overall system design
│   ├── base-rag.md                   # Base RAG implementation
│   └── enhanced-rag.md               # Enhanced RAG features
│
├── development/                       # Developer guides
│   ├── testing.md                    # Testing documentation
│   ├── testing-with-uv.md            # UV-specific testing
│   ├── mkdocs-guide.md               # Documentation system
│   └── cleanup-summary.md            # Code organization
│
└── troubleshooting/                   # Problem solving
    ├── fix-summary.md                 # Common fixes
    └── fixes-summary.md               # Additional solutions
```

## 📋 What Was Moved

### From Root Directory to docs/
The following files were relocated from the project root to organized subdirectories:

#### Getting Started
- `HOW_TO_RUN.md` → `docs/getting-started/how-to-run.md`
- `LOAD_PUBMED_INDEX.md` → `docs/getting-started/load-pubmed-index.md`
- `INSTALL_TESSERACT.md` → `docs/getting-started/install-tesseract.md`

#### User Guide
- `SEARCH_FEATURES.md` → `docs/user-guide/search-features.md`
- `NEW_LAYOUT.md` → `docs/user-guide/new-layout.md`

#### Architecture
- `BASE_RAG_EXPLANATION.md` → `docs/architecture/base-rag.md`
- `ENHANCED_RAG_EXPLANATION.md` → `docs/architecture/enhanced-rag.md`

#### Development
- `MKDOCS_GUIDE.md` → `docs/development/mkdocs-guide.md`
- `CLEANUP_SUMMARY.md` → `docs/development/cleanup-summary.md`

#### Troubleshooting
- `FIX_SUMMARY.md` → `docs/troubleshooting/fix-summary.md`

### Existing docs/ Files Reorganized
- `docs/INSTALLATION.md` → `docs/getting-started/installation.md`
- `docs/TESTING.md` → `docs/development/testing.md`
- `docs/TESTING_WITH_UV.md` → `docs/development/testing-with-uv.md`
- `docs/ARCHITECTURE.md` → `docs/architecture/system-architecture.md`
- `docs/PDF_MANAGER_README.md` → `docs/user-guide/pdf-manager.md`
- `docs/STREAMLIT_APP.md` → `docs/user-guide/streamlit-apps.md`

## 🧪 Test Files Organization

All test files have been moved to the `tests/` directory:

```
tests/
├── __init__.py
├── conftest.py                      # Pytest configuration
├── test_app_imports.py              # App import verification
├── test_app_ready.py                # App readiness tests
├── test_document_search.py          # Document search tests
├── test_pdf_processor.py            # PDF processing tests
├── test_pubmed_search.py            # PubMed search tests
├── test_setup.py                    # Setup verification
├── test_streamlit_app.py            # Streamlit app tests
├── test_vector_operations.py        # Vector operation tests
└── test_visual_controls.py          # UI control tests
```

## 📖 Using MkDocs

The documentation can be served using MkDocs:

```bash
# Serve documentation locally
uv run mkdocs serve

# Build static documentation
uv run mkdocs build

# Deploy to GitHub Pages
uv run mkdocs gh-deploy
```

The `mkdocs.yml` file has been updated to reflect the new documentation structure.

## 🔗 Benefits of Organization

1. **Logical Structure**: Documentation grouped by purpose
2. **Easy Navigation**: Clear categories for different users
3. **MkDocs Ready**: Properly structured for documentation generation
4. **Maintainable**: Easy to find and update specific docs
5. **Professional**: Standard documentation structure

## 📝 Files Kept in Root

Some files remain in the root for visibility:
- `README.md` - Project introduction
- `PROJECT_STRUCTURE.md` - File organization reference
- Configuration files (`mkdocs.yml`, `pyproject.toml`, etc.)

## 🚀 Accessing Documentation

### Local Development
```bash
# View with MkDocs
uv run mkdocs serve
# Open http://localhost:8000
```

### Direct File Access
All documentation is in `docs/` with clear subdirectory organization.

### GitHub
Documentation is viewable directly on GitHub with proper markdown rendering.

## 📋 Next Steps

1. Update any broken links in documentation
2. Add API reference documentation
3. Create additional user guides as needed
4. Consider versioning for documentation

The documentation is now professionally organized and ready for both development and production use!