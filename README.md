# PDF Document Search System

A comprehensive RAG (Retrieval-Augmented Generation) system for PDF document search with vector database integration.

## 🚀 Quick Start

### Installation

```bash
# Install UV (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Or use pip
pip install -r requirements.txt
```

### Run Applications

```bash
# PDF Manager (separate collection)
streamlit run apps/pdf_manager_app.py

# PubMed Search
streamlit run apps/streamlit_pubmed_app.py

# Combined Upload + Search
streamlit run apps/streamlit_upload_app.py
```

### Run Tests

```bash
# Using UV
uv run pytest tests/

# Using script
./scripts/runners/run_tests.sh
```

## 📚 Features

- **PDF Processing**: Multiple extraction methods with OCR support
- **Vector Search**: Semantic search using Qdrant
- **Document Management**: Upload, index, search, and manage PDFs
- **Dual Collections**: Separate collections for PDFs and PubMed data
- **Web Interface**: Clean Streamlit UI

## 📁 Project Structure

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed layout.

## 📖 Documentation

- [Testing Guide](docs/TESTING.md)
- [Installation Guide](docs/INSTALLATION.md)
- [API Documentation](docs/README.md)

## 🐳 Docker Support

```bash
# Start Qdrant
docker-compose up -d

# Or manually
docker run -p 6333:6333 qdrant/qdrant
```

## 📄 License

MIT License - See LICENSE file for details.
