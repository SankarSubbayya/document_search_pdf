# File Documentation - PubMed Semantic Search System

## 📱 Application Layer

### **app.py**
- **Purpose**: Streamlit web application for semantic search
- **Key Features**:
  - Interactive search interface with real-time results
  - Performance metrics display (embedding & search times)
  - Search history tracking
  - Results visualization (score distribution, section analysis)
  - Cached model loading for performance
- **Dependencies**: streamlit, plotly, qdrant-client, sentence-transformers
- **Usage**: `streamlit run app.py`

### **main.py**
- **Purpose**: CLI entry point for the RAG system
- **Commands**:
  - `process`: Process documents into the system
  - `search`: Search for documents
  - `ask`: Ask questions with context
  - `stats`: Show system statistics
  - `interactive`: Interactive mode
- **Usage**: `python main.py [command] [options]`

### **run_app.sh**
- **Purpose**: Launcher script for Streamlit application
- **Features**:
  - Checks Docker/Qdrant status
  - Verifies collection exists
  - Offers to index sample data if needed
  - Launches Streamlit with proper settings
- **Usage**: `./run_app.sh`

## 🔧 Scripts Directory

### **index_pubmed_data.py**
- **Purpose**: Index PubMed documents into Qdrant vector database
- **Key Functions**:
  - `PubMedIndexer`: Main indexer class
  - `ensure_collection()`: Create/verify Qdrant collection
  - `generate_embeddings()`: Create 384-dim vectors
  - `index_documents()`: Batch upload to Qdrant
- **Performance**: ~550 documents/second
- **Usage**: `python scripts/index_pubmed_data.py --max-documents 1000`

### **fast_search.py**
- **Purpose**: Optimized search interface with performance monitoring
- **Features**:
  - Embedding caching for repeated queries
  - Performance timing breakdown
  - Interactive and batch modes
  - Benchmark functionality
- **Key Class**: `FastSearcher`
- **Usage**: `python scripts/fast_search.py --interactive`

### **test_qdrant_connection.py**
- **Purpose**: Test and manage Qdrant connections
- **Functions**:
  - Test connection to Qdrant
  - Create/delete collections
  - Verify vector operations
  - Display collection statistics
- **Usage**: `python scripts/test_qdrant_connection.py --create-collection documents`

### **qdrant_setup.sh**
- **Purpose**: Docker container management for Qdrant
- **Features**:
  - Interactive menu system
  - Start/stop/remove container
  - Backup/restore data
  - View logs and status
- **Usage**: `./scripts/qdrant_setup.sh [start|stop|status]`

### **verify_paths.py**
- **Purpose**: Verify data migration and path configuration
- **Checks**:
  - Configuration file paths
  - New data location existence
  - Symlink verification
  - Old directory cleanup
  - Script default paths
- **Usage**: `python scripts/verify_paths.py`

### **cleanup_old_data.sh**
- **Purpose**: Remove old data directories after migration
- **Safety**: Requires explicit confirmation
- **Usage**: `./scripts/cleanup_old_data.sh`

## 📦 Source Code (src/)

### config/

#### **settings.py**
- **Purpose**: Configuration management system
- **Classes**:
  - `DatabaseConfig`: Database settings
  - `VectorStoreConfig`: Qdrant configuration
  - `ProcessingConfig`: Document processing settings
  - `EmbeddingConfig`: Model configuration
  - `LLMConfig`: LLM settings
  - `ApplicationConfig`: Main app configuration
  - `Settings`: Global settings manager
- **Features**: Environment variable support, directory creation

### core/

#### **rag_system.py**
- **Purpose**: High-level RAG system interface
- **Class**: `RAGSystem`
- **Methods**:
  - `add_documents()`: Add documents to system
  - `search()`: Search for relevant documents
  - `ask()`: Question answering with context
  - `get_stats()`: System statistics
- **Usage**: Primary API for RAG operations

#### **pipeline.py**
- **Purpose**: Document processing pipeline
- **Class**: `DocumentPipeline`
- **Features**:
  - Document loading and parsing
  - Chunking strategies
  - Embedding generation
  - Vector store integration

### data/

#### **kagglehub_downloader.py**
- **Purpose**: Download PubMed dataset using kagglehub (no API key)
- **Class**: `KaggleHubDownloader`
- **Methods**:
  - `download_pubmed_200k_rct()`: Main download function
  - `_verify_dataset()`: Verify downloaded files
- **Features**: Automatic authentication, progress tracking

#### **dataset_downloader.py**
- **Purpose**: Alternative downloader from GitHub
- **Class**: `DatasetDownloader`
- **Sources**: GitHub repositories with direct URLs
- **Features**: No authentication required, fallback support

#### **download_and_prepare.py**
- **Purpose**: Main script to download and process dataset
- **Features**:
  - Combines download and processing
  - Multiple dataset size options (20k/200k)
  - Sample dataset creation
- **Usage**: `python src/data/download_and_prepare.py --size 20k`

#### **pubmed_processor_tsv.py**
- **Purpose**: Process PubMed TSV format data
- **Class**: `PubMedDatasetProcessorTSV`
- **Input Format**: Tab-separated with ###ID headers
- **Output**: Structured JSONL with sections
- **Methods**:
  - `parse_dataset_file()`: Parse TSV format
  - `process_to_documents()`: Convert to documents
  - `create_training_dataset()`: Create JSONL output

#### **pubmed_processor.py**
- **Purpose**: Process PubMed JSON format (legacy)
- **Class**: `PubMedDatasetProcessor`
- **Note**: Used for older JSON format datasets

### processing/

#### **document_processor.py**
- **Purpose**: Document parsing and chunking
- **Features**:
  - Multiple format support (PDF, DOCX, TXT, etc.)
  - Intelligent chunking strategies
  - Metadata extraction
  - Table processing

### retrieval/

#### **base_rag.py**
- **Purpose**: Base RAG implementation
- **Features**:
  - Basic retrieval logic
  - Context management
  - Response generation

#### **enhanced_rag.py**
- **Purpose**: Enhanced RAG with advanced features
- **Enhancements**:
  - Reranking
  - Multi-query strategies
  - Context optimization

### storage/

#### **database_manager.py**
- **Purpose**: Database operations for metadata
- **Databases**: SQLite, PostgreSQL support
- **Features**:
  - Document metadata storage
  - Query history
  - Statistics tracking

#### **vector_store.py**
- **Purpose**: Vector store abstraction layer
- **Backends**: Qdrant, Weaviate, Pinecone
- **Operations**:
  - Collection management
  - Vector operations
  - Search functionality

## 🧪 Tests

### **test_system.py**
- **Purpose**: System integration tests
- **Coverage**: End-to-end pipeline testing

### **test_minimal.py**
- **Purpose**: Minimal functionality tests
- **Focus**: Core features verification

### **test_quick.py**
- **Purpose**: Quick smoke tests
- **Runtime**: <30 seconds

### **test_document_search.py**
- **Purpose**: Document search functionality tests
- **Coverage**: Search algorithms, ranking

## 📐 Configuration Files

### **config.yaml**
- **Purpose**: Main configuration file
- **Sections**:
  - `paths`: Data and storage paths
  - `processing`: Document processing settings
  - `storage`: Database and vector store config
  - `embeddings`: Model configuration
  - `llm`: LLM settings
  - `retrieval`: Search parameters
  - `kaggle`: Dataset download config
- **Format**: YAML with extensive comments

### **docker-compose.yml**
- **Purpose**: Docker service definitions
- **Services**:
  - `qdrant`: Vector database container
- **Ports**: 6333 (REST), 6334 (gRPC)
- **Volumes**: Persistent storage mapping

### **pyproject.toml**
- **Purpose**: Python project configuration
- **Sections**:
  - `[project]`: Package metadata
  - `dependencies`: Required packages
  - `[project.optional-dependencies]`: Dev/docs deps
  - `[tool.*]`: Tool configurations (black, isort, mypy, pytest)

## 📊 Data Structure

### **Input Data Format** (TSV)
```
###24491034
BACKGROUND<tab>The emergence of HIV...
METHODS<tab>This study is designed...
```

### **Processed JSONL Format**
```json
{
  "id": "pubmed_24491034",
  "source": "pubmed_200k_rct_train",
  "content": "Structured text with sections...",
  "metadata": {
    "split": "train",
    "abstract_id": "24491034",
    "num_sentences": 11,
    "labels": ["BACKGROUND", "METHODS", "CONCLUSIONS"],
    "section_background": "...",
    "section_methods": "..."
  }
}
```

### **Qdrant Payload Structure**
```json
{
  "document_id": "pubmed_24491034",
  "abstract_id": "24491034",
  "content": "Full text content",
  "labels": ["BACKGROUND", "METHODS"],
  "source": "pubmed_200k_rct_train",
  "split": "train",
  "num_sentences": 11,
  "indexed_at": "2024-10-10T..."
}
```

## 🔄 Typical Workflows

### 1. **Initial Setup**
```bash
# Start Docker
open -a Docker

# Start Qdrant
docker-compose up -d qdrant

# Download dataset
python src/data/download_and_prepare.py --size 20k

# Index documents
python scripts/index_pubmed_data.py --max-documents 1000

# Launch UI
streamlit run app.py
```

### 2. **Search Operations**
```python
# CLI Search
python scripts/fast_search.py "HIV treatment"

# Interactive Search
python scripts/fast_search.py --interactive

# Web UI
streamlit run app.py
```

### 3. **Data Management**
```bash
# Verify paths
python scripts/verify_paths.py

# Backup Qdrant
./scripts/qdrant_setup.sh backup

# Clean old data
./scripts/cleanup_old_data.sh
```

## 📝 Environment Variables

### **Required**
- None (all have defaults)

### **Optional**
- `KAGGLE_USERNAME`: Kaggle API username
- `KAGGLE_KEY`: Kaggle API key
- `OPENAI_API_KEY`: OpenAI API key
- `QDRANT_API_KEY`: Qdrant API key
- `EMBEDDING_MODEL`: Model name
- `EMBEDDING_DEVICE`: cpu/cuda/mps

## 🎯 Key Design Decisions

1. **No API Key Required**: Uses kagglehub for downloads
2. **Local First**: Everything runs locally by default
3. **Docker for Services**: Qdrant in container for isolation
4. **Cached Embeddings**: Performance optimization
5. **Batch Processing**: Efficient indexing
6. **Multiple Interfaces**: CLI, Web, Python API
7. **Centralized Data**: Single data directory for all projects

## 🚀 Performance Tips

1. **Use MPS on Mac**: Set device to 'mps' for M1/M2
2. **Batch Index**: Process documents in batches
3. **Cache Models**: Keep models in memory
4. **Use Symlinks**: Fast access to central data
5. **Monitor Memory**: ~4GB recommended

## 🐛 Troubleshooting

### Common Issues
1. **Docker not running**: Start Docker Desktop
2. **Collection not found**: Run indexing script
3. **Slow first search**: Model loading (normal)
4. **Memory errors**: Reduce batch size
5. **Path errors**: Run verify_paths.py

---

*Generated: October 2024*
*Version: 1.0.0*
*Dataset: PubMed 200k RCT*