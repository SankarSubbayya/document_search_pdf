# PDF Document Search System

A specialized RAG (Retrieval-Augmented Generation) system focused on processing, indexing, and searching PDF documents, including support for scanned PDFs with OCR.

## Features

### PDF Processing
- **Multiple extraction methods**: Uses pdfplumber, PyPDF2, pypdf, and PyMuPDF for robust text extraction
- **OCR support**: Automatically detects and processes scanned PDFs using Tesseract OCR
- **Table extraction**: Extracts and preserves table structures from PDFs
- **Image extraction**: Identifies and extracts images with metadata
- **Layout preservation**: Maintains document structure and formatting
- **Metadata extraction**: Captures document properties, author, creation date, etc.

### Document Processing
- **Intelligent chunking**: Semantic or token-based document chunking
- **Multi-format support**: Handles PDF, DOCX, TXT, MD, HTML files
- **Batch processing**: Efficiently process entire directories of PDFs
- **Deduplication**: Automatically skips duplicate documents based on content hash

### Vector Search
- **Semantic search**: Find relevant content using natural language queries
- **Hybrid search**: Combines semantic and keyword-based search
- **Metadata filtering**: Filter results by document type, date, category
- **Result ranking**: Intelligent reranking for improved relevance

## Installation

### Prerequisites

1. **Python 3.8+**
2. **Tesseract OCR** (for scanned PDFs):
   ```bash
   # macOS
   brew install tesseract

   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr

   # Windows
   # Download from: https://github.com/UB-Mannheim/tesseract/wiki
   ```

3. **Poppler** (for pdf2image):
   ```bash
   # macOS
   brew install poppler

   # Ubuntu/Debian
   sudo apt-get install poppler-utils

   # Windows
   # Download from: https://github.com/oschwartz10612/poppler-windows/releases/
   ```

### Setup

1. **Clone the repository**:
   ```bash
   cd document_search_pdf
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp sample.env .env
   # Edit .env with your API keys
   ```

5. **Start Qdrant vector database**:
   ```bash
   ./start_qdrant.sh  # Or use Docker Compose
   ```

## Usage

### Index PDF Documents

#### Basic Usage
```bash
python index_pdfs.py -i /path/to/pdf/directory
```

#### With Options
```bash
# Index with category and limit
python index_pdfs.py -i /path/to/pdfs -c "research-papers" -m 100

# Non-recursive (current directory only)
python index_pdfs.py -i /path/to/pdfs --no-recursive

# Reset collection before indexing
python index_pdfs.py -i /path/to/pdfs --reset-collection
```

### Process PDFs Programmatically

```python
from src.processing.pdf_processor import PDFProcessor

# Initialize processor
processor = PDFProcessor(
    use_ocr=True,  # Enable OCR for scanned PDFs
    extract_tables=True,
    extract_images=True
)

# Process a single PDF
pdf_content = processor.process_pdf("document.pdf")

# Check if PDF is scanned
is_scanned = processor.is_scanned_pdf("document.pdf")

# Extract with layout preservation
text_with_layout = processor.extract_text_with_layout("document.pdf")
```

### Search Documents

```python
from src.retrieval.searcher import DocumentSearcher

# Initialize searcher
searcher = DocumentSearcher()

# Search for content
results = searcher.search(
    query="machine learning algorithms",
    top_k=5,
    filter_category="research-papers"
)

# Display results
for result in results:
    print(f"Score: {result['score']}")
    print(f"Content: {result['content'][:200]}...")
    print(f"Source: {result['metadata']['file_path']}")
    print("-" * 50)
```

## Project Structure

```
document_search_pdf/
├── src/
│   ├── processing/
│   │   ├── document_processor.py    # General document processing
│   │   └── pdf_processor.py         # Specialized PDF handling
│   ├── embeddings/
│   │   └── embedding_generator.py   # Generate vector embeddings
│   ├── storage/
│   │   ├── qdrant_manager.py       # Vector database management
│   │   └── document_store.py       # Document storage
│   └── retrieval/
│       └── searcher.py             # Search functionality
├── index_pdfs.py                   # Main PDF indexing script
├── config.yaml                     # Configuration file
├── requirements.txt                # Python dependencies
└── README_PDF.md                   # This file
```

## Configuration

Edit `config.yaml` to customize:

- **PDF Processing**:
  ```yaml
  processing:
    pdf:
      use_ocr: true
      ocr_language: 'eng'
      extract_tables: true
      extract_images: true
      dpi: 300  # For OCR quality
  ```

- **Chunking Strategy**:
  ```yaml
  chunking:
    strategy: semantic  # or 'token'
    chunk_size: 512
    chunk_overlap: 50
  ```

- **Vector Store**:
  ```yaml
  vector_store:
    type: qdrant
    collection_name: pdf_documents
  ```

## Advanced Features

### OCR Configuration

For multilingual OCR support:
```python
processor = PDFProcessor(
    ocr_language='eng+fra+deu'  # English, French, German
)
```

### Custom Extraction

```python
# Extract only specific pages
pdf_content = processor.process_pdf(
    "document.pdf",
    page_range=(1, 10)  # Pages 1-10
)

# Extract with custom DPI for better OCR
processor = PDFProcessor(dpi=600)  # Higher quality
```

### Batch Processing

```python
from src.processing.pdf_processor import process_pdf_directory

# Process entire directory
stats = process_pdf_directory(
    directory_path="/path/to/pdfs",
    output_dir="/path/to/output",
    use_ocr=True,
    recursive=True
)

print(f"Processed: {stats['processed']} PDFs")
print(f"Scanned: {stats['scanned']} PDFs")
print(f"Tables extracted: {stats['total_tables']}")
```

## Performance Optimization

### For Large PDF Collections

1. **Parallel Processing**:
   ```yaml
   processing:
     batch:
       max_workers: 8  # Increase for more parallelism
   ```

2. **Memory Management**:
   ```yaml
   performance:
     memory:
       max_memory_gb: 16
       clear_cache_interval: 100
   ```

3. **Caching**:
   ```yaml
   embeddings:
     cache_embeddings: true
   ```

### For Scanned PDFs

1. **OCR Optimization**:
   - Pre-process images for better OCR accuracy
   - Use appropriate DPI (300-600)
   - Select correct language models

2. **Fallback Methods**:
   - System automatically tries multiple extraction methods
   - Falls back to OCR when text extraction fails

## Troubleshooting

### Common Issues

1. **OCR not working**:
   ```bash
   # Check Tesseract installation
   tesseract --version

   # Install language packs
   sudo apt-get install tesseract-ocr-[lang]
   ```

2. **Memory issues with large PDFs**:
   - Process in smaller batches
   - Reduce DPI for OCR
   - Enable memory cleanup in config

3. **Poor text extraction**:
   - Try different extraction methods
   - Increase OCR DPI
   - Pre-process PDFs to improve quality

## API Documentation

### PDF Processor API

```python
class PDFProcessor:
    def process_pdf(file_path, fallback_methods=True) -> PDFContent
    def is_scanned_pdf(file_path) -> bool
    def extract_text_with_layout(file_path) -> str
    def extract_pdf_metadata(file_path) -> dict
```

### PDFContent Structure

```python
@dataclass
class PDFContent:
    text: str                    # Extracted text
    tables: List[Dict]          # Extracted tables
    images: List[Dict]          # Image metadata
    metadata: Dict              # Document metadata
    page_contents: List[Dict]   # Per-page content
    extraction_method: str      # Method used
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the [FAQ](docs/FAQ.md)
- Review the [documentation](docs/)