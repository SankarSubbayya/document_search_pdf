# Project Structure

Complete guide to the Document Search RAG project organization and components.

## 📂 Directory Overview

```
document_search/
├── src/                          # Source code
│   ├── retrieval/               # RAG implementations
│   ├── processing/              # Document processing
│   ├── storage/                 # Database & vector store
│   ├── config/                  # Configuration management
│   ├── core/                    # Core pipeline components
│   ├── data/                    # Dataset utilities
│   └── utils/                   # Utility functions
├── examples/                     # Working examples
├── tests/                        # Test suite
├── test_documents/              # Sample documents
├── docs/                         # Documentation
├── qdrant_db/                   # Local vector database
├── data/                         # Downloaded datasets
├── scripts/                      # Utility scripts
├── config.yaml                  # Main configuration
├── pyproject.toml               # Project dependencies
└── README.md                    # Project overview
```

## 🔍 Detailed Structure

### `src/` - Source Code

#### `src/retrieval/` - RAG Implementations

**`base_rag.py`** - Simple RAG Implementation
- `class DocumentSearchRAG` - Main RAG class
- `class Document` - Document data structure
- Methods:
  - `embed_text()` - Generate embeddings
  - `index_documents()` - Store documents
  - `search()` - Find similar documents
  - `generate_answer()` - Use LLM for answers
  - `rag_query()` - Complete RAG pipeline

**`enhanced_rag.py`** - Advanced RAG Implementation
- `class EnhancedDocumentRAG(DocumentSearchRAG)` - Extends base RAG
- Additional features:
  - Document processing with Docling
  - Intelligent chunking with Chonkie
  - Table extraction and indexing
  - Advanced search filters
  - Result reranking
- Methods:
  - `process_and_index_documents()` - Parse and index
  - `enhanced_search()` - Advanced filtering
  - `enhanced_rag_query()` - RAG with reranking
  - `_index_document_chunks()` - Chunk indexing
  - `_index_tables()` - Table indexing
  - `_rerank_results()` - Improve relevance

#### `src/processing/` - Document Processing

**`document_processor.py`** - Document Parser & Chunker
- `class DocumentProcessor` - Main processor
- `class ProcessedDocument` - Processed document structure
- Features:
  - Multi-format parsing (PDF, DOCX, PPTX, HTML, MD, TXT)
  - Table extraction
  - Image cataloging
  - Semantic chunking
  - Token-based chunking
- Dependencies:
  - Docling for parsing
  - Chonkie for chunking

#### `src/storage/` - Storage Layer

**`database_manager.py`** - Database Management
- `class DatabaseManager` - SQLite/PostgreSQL manager
- Features:
  - Document metadata storage
  - Chunk management
  - Table storage
  - Processing history
  - Statistics and reporting
- Tables:
  - `documents` - Document metadata
  - `chunks` - Document chunks
  - `extracted_tables` - Tables from documents
  - `extracted_images` - Image catalog
  - `processing_history` - Audit trail

**`vector_store.py`** - Vector Database Wrapper
- `class VectorStore` - Qdrant client wrapper
- Features:
  - Collection management
  - Batch operations
  - Search with filters
  - Local and server modes

#### `src/config/` - Configuration

**`settings.py`** - Configuration Management
- Load and validate configuration
- Environment variable handling
- Default settings
- Configuration validation

#### `src/core/` - Core Components

**`pipeline.py`** - Processing Pipeline
- Document ingestion pipeline
- Batch processing
- Error handling
- Progress tracking

**`rag_system.py`** - Main RAG System
- Unified RAG interface
- Component orchestration
- System initialization

#### `src/data/` - Dataset Utilities

**`dataset_downloader.py`** - Dataset Download
- Download PubMed RCT datasets
- Verify downloads
- Handle different sizes (20k, 200k)

**`pubmed_processor.py`** - PubMed Data Processing
- Parse PubMed RCT format
- Convert to RAG-ready format
- Handle labels (BACKGROUND, METHODS, etc.)

### `examples/` - Example Scripts

**`process_documents.py`** - Document Processing Example
- Shows how to process documents
- Extract tables and images
- Store in database
- Index in vector store

**`query_enhanced_rag.py`** - Query Example
- Interactive query interface
- Shows search results
- Generates answers
- Displays sources

**`use_local_qdrant.py`** - Qdrant Demo
- Local Qdrant setup
- Collection management
- Basic operations
- Statistics

### `tests/` - Test Suite

**`test_document_search.py`** - Main Tests
- Test Document class
- Test DocumentSearchRAG
- Test all methods
- Mocked dependencies
- **Status**: 13/13 passing, 82% coverage

### `test_documents/` - Sample Files

Sample documents for testing:
- `machine_learning_basics.md`
- `deep_learning_guide.md`
- `nlp_techniques.txt`

## 🔧 Configuration Files

### `config.yaml` - Main Configuration

```yaml
# Embedding settings
embedding_model: "all-MiniLM-L6-v2"

# Vector database
qdrant_path: "./qdrant_db"
collection_name: "documents"

# Search settings
default_top_k: 5
similarity_threshold: 0.7

# LLM settings
default_model: "gpt-3.5-turbo"
default_temperature: 0.7
max_tokens: 500

# System prompt
system_prompt: |
  You are a helpful AI assistant...
```

### `pyproject.toml` - Dependencies

```toml
[project]
name = "document-search-rag"
version = "0.1.0"
dependencies = [
    "qdrant-client>=1.7.0",
    "openai>=1.0.0",
    "sentence-transformers>=2.2.0",
    "pyyaml>=6.0",
    "python-dotenv>=1.0.0",
    "docling>=2.55.1",
    "chonkie>=1.3.1",
    "rich>=13.0.0",
    "click>=8.1.0",
    # ... more dependencies
]
```

### `.env` - Environment Variables

```bash
OPENAI_API_KEY=your_key_here
# Optional: Other API keys
# Optional: Database credentials
```

## 📊 Data Flow

### Document Indexing Flow

```
1. Input Documents
   ↓
2. DocumentProcessor (Docling)
   ├─→ Parse document
   ├─→ Extract tables
   └─→ Extract images
   ↓
3. Chonkie Chunker
   ├─→ Semantic chunks
   └─→ Token chunks
   ↓
4. SentenceTransformer
   └─→ Generate embeddings
   ↓
5. Storage
   ├─→ Qdrant (vectors)
   └─→ SQLite (metadata)
```

### Query Flow

```
1. User Query
   ↓
2. Embed Query
   ↓
3. Vector Search (Qdrant)
   ├─→ Apply filters
   └─→ Top-K results
   ↓
4. Rerank (optional)
   ↓
5. LLM Generation
   └─→ Context + Query → Answer
   ↓
6. Return with Sources
```

## 🔄 Import Structure

### Correct Import Paths

```python
# Base RAG
from src.retrieval.base_rag import DocumentSearchRAG, Document

# Enhanced RAG
from src.retrieval.enhanced_rag import EnhancedDocumentRAG

# Document Processing
from src.processing.document_processor import DocumentProcessor

# Database
from src.storage.database_manager import DatabaseManager

# Vector Store
from src.storage.vector_store import VectorStore
```

### Common Import Patterns

```python
# For scripts
from src.retrieval.enhanced_rag import EnhancedDocumentRAG

# For tests
from src.retrieval.base_rag import DocumentSearchRAG

# For configuration
from src.config.settings import load_config
```

## 🗄️ Storage Layout

### Qdrant Database (`qdrant_db/`)

```
qdrant_db/
├── meta.json                    # Database metadata
└── collections/
    ├── documents/               # Main collection
    │   ├── segments/           # Vector segments
    │   └── ...
    └── enhanced_documents/      # Enhanced collection
        └── ...
```

### SQLite Database

Tables structure:
```sql
-- documents table
CREATE TABLE documents (
    document_id TEXT PRIMARY KEY,
    title TEXT,
    file_path TEXT,
    category TEXT,
    word_count INTEGER,
    processing_timestamp DATETIME,
    file_hash TEXT
);

-- chunks table
CREATE TABLE chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT,
    chunk_index INTEGER,
    content TEXT,
    chunk_size INTEGER,
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);

-- extracted_tables
CREATE TABLE extracted_tables (
    table_id TEXT PRIMARY KEY,
    document_id TEXT,
    table_data TEXT,
    caption TEXT,
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);
```

## 📦 Dependency Map

```
document-search-rag
├── Core ML
│   ├── sentence-transformers  # Embeddings
│   ├── openai                # LLM
│   └── torch                 # PyTorch (via sentence-transformers)
├── Document Processing
│   ├── docling              # Document parsing
│   └── chonkie              # Text chunking
├── Storage
│   ├── qdrant-client        # Vector database
│   └── (built-in sqlite3)   # Metadata database
├── Utilities
│   ├── rich                 # Terminal output
│   ├── click                # CLI
│   ├── pyyaml               # Configuration
│   └── python-dotenv        # Environment variables
└── Development
    ├── pytest               # Testing
    ├── pytest-cov           # Coverage
    └── black                # Code formatting
```

## 🎯 Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **base_rag.py** | Core RAG implementation |
| **enhanced_rag.py** | Advanced RAG features |
| **document_processor.py** | Parse and chunk documents |
| **database_manager.py** | Store metadata |
| **vector_store.py** | Manage vector database |
| **pipeline.py** | Orchestrate processing |
| **settings.py** | Configuration management |

## 📝 File Naming Conventions

- **Classes**: PascalCase (e.g., `DocumentSearchRAG`)
- **Functions**: snake_case (e.g., `process_documents`)
- **Files**: snake_case (e.g., `document_processor.py`)
- **Constants**: UPPER_CASE (e.g., `DEFAULT_MODEL`)
- **Private methods**: _leading_underscore (e.g., `_index_chunks`)

## 🔍 Finding Components

### Need to...

**Parse documents?**
→ `src/processing/document_processor.py`

**Do simple RAG?**
→ `src/retrieval/base_rag.py`

**Do advanced RAG?**
→ `src/retrieval/enhanced_rag.py`

**Store metadata?**
→ `src/storage/database_manager.py`

**Manage vectors?**
→ `src/storage/vector_store.py`

**Configure system?**
→ `config.yaml` or `src/config/settings.py`

**See examples?**
→ `examples/` directory

**Run tests?**
→ `tests/test_document_search.py`

## 🚀 Quick Reference

### Start Here
1. Read `README.md`
2. Check `docs/index.md`
3. Review `examples/`
4. Run tests
5. Explore `src/`

### Key Files
- Entry point: `src/retrieval/enhanced_rag.py`
- Configuration: `config.yaml`
- Tests: `tests/test_document_search.py`
- Examples: `examples/`

---

**Now you know where everything is! 🗺️**
