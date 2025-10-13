# Documentation Index

Welcome to the Document Search RAG System documentation.

## 📖 Documentation Overview

### Core Documentation

1. **[Project Structure](PROJECT_STRUCTURE.md)**
   - Complete architecture overview
   - Module responsibilities
   - Design principles
   - Extension points

2. **[Enhanced Features Guide](README_ENHANCED.md)**
   - Advanced capabilities
   - Docling and Chonkie integration details
   - Performance optimization
   - Benchmarks and best practices

3. **[API Reference](api_reference.md)**
   - Python API documentation
   - CLI commands
   - Configuration options

### Setup Guides

4. **[Qdrant Local Setup](QDRANT_LOCAL_GUIDE.md)**
   - Installing Qdrant locally
   - Docker setup
   - Configuration tips

5. **[Qdrant Quick Start](QDRANT_QUICK_START.md)**
   - Getting started with vector search
   - Basic operations
   - Example queries

### Tutorials

6. **[Processing Large Document Collections](tutorials/large_corpus_processing.md)**
   - Handling 1000+ documents
   - Batch processing strategies
   - Memory optimization

7. **[Custom Document Processors](tutorials/custom_processors.md)**
   - Extending the document processor
   - Adding new file formats
   - Custom chunking strategies

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Document Corpus (1000+ docs)            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Docling Parser                            │
│  • Text, Table & Image Extraction                            │
│  • Multi-format Support                                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Chonkie Chunker                           │
│  • Semantic & Token-based Chunking                           │
│  • Configurable Overlap                                      │
└────────────┬───────────────────────────┬────────────────────┘
              │                           │
              ▼                           ▼
┌──────────────────────────┐  ┌──────────────────────────────┐
│    SQLite/PostgreSQL     │  │      Qdrant Vector DB        │
│  • Document Metadata     │  │  • Vector Embeddings         │
│  • Tables & Images       │  │  • Similarity Search         │
└──────────────────────────┘  └──────────────────────────────┘
              │                           │
              └───────────┬───────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    RAG System                                │
│  • Query Processing                                          │
│  • Context Retrieval                                         │
│  • Answer Generation                                         │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Links

- [Main README](../README.md) - Getting started
- [Configuration Guide](configuration.md) - Environment setup
- [API Examples](examples.md) - Code examples
- [Troubleshooting](troubleshooting.md) - Common issues

## 📊 Performance Metrics

| Component | Metric | Performance |
|-----------|--------|-------------|
| Document Processing | Speed | 500-1000 docs/hour |
| Chunking | Throughput | 10,000 chunks/min |
| Vector Indexing | Speed | 50,000 vectors/min |
| Search | Latency | <500ms |
| RAG Generation | Response Time | 2-5 seconds |

## 🔧 Configuration Files

- `.env` - Environment variables
- `src/config/settings.py` - Application settings
- `docker-compose.yml` - Docker services

## 📝 Contributing

See our [Contributing Guide](CONTRIBUTING.md) for information on:
- Code style
- Testing requirements
- PR process
- Development setup

## 📄 License

This project is licensed under the MIT License.