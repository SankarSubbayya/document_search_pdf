# PDF Upload Feature for Document Search

## Overview

The enhanced Streamlit application now includes PDF upload functionality, allowing you to:
- Upload your own PDF documents
- Process and index them automatically
- Search across both uploaded documents and the existing PubMed dataset
- View detailed analytics and search results

## Features

### 📤 PDF Upload & Processing
- **Multiple file upload**: Upload one or more PDF files at once
- **Automatic text extraction**: Uses multiple extraction methods (pdfplumber, PyPDF2, PyMuPDF)
- **OCR support**: Automatically detects and processes scanned PDFs using OCR
- **Smart chunking**: Splits documents into semantic chunks with configurable size and overlap
- **Metadata extraction**: Extracts and stores PDF metadata (title, author, creation date, etc.)

### 🔍 Enhanced Search
- **Unified search**: Search across both uploaded PDFs and PubMed documents
- **Source filtering**: Filter results by document source (uploaded/PubMed/all)
- **Relevance scoring**: Results ranked by semantic similarity
- **Fast & exact modes**: Choose between fast approximate or exact search

### 📊 Analytics & Visualization
- **Search timing metrics**: View embedding and search performance
- **Score distribution**: Visualize relevance scores across results
- **Source analysis**: See distribution of results by document source
- **Document statistics**: Track total documents, chunks, and processing stats

## Quick Start

### 1. Prerequisites

```bash
# Install required Python packages
pip install streamlit sentence-transformers qdrant-client pandas plotly
pip install PyPDF2 pdfplumber pypdf pdf2image pytesseract pillow

# For OCR support (optional but recommended)
# Mac:
brew install tesseract

# Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# For PDF to image conversion (required for OCR)
# Mac:
brew install poppler

# Ubuntu/Debian:
sudo apt-get install poppler-utils
```

### 2. Start Qdrant Vector Database

```bash
# Using Docker (recommended)
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant
```

### 3. Run the Application

```bash
# Using the provided script
./run_app_with_upload.sh

# Or directly with streamlit
streamlit run app_with_upload.py
```

The app will open automatically in your browser at `http://localhost:8501`

## Using the PDF Upload Feature

### Step 1: Upload PDFs
1. In the sidebar, locate the "📤 Upload PDFs" section
2. Click "Browse files" to select one or more PDF files
3. Configure processing settings:
   - **Chunk Size**: How large each text segment should be (default: 512 characters)
   - **Chunk Overlap**: How much text should overlap between chunks (default: 50 characters)
   - **Enable OCR**: Process scanned PDFs (enabled by default)

### Step 2: Process & Index
1. Click the "🚀 Process & Index PDFs" button
2. Wait for processing to complete (progress bar shows status)
3. View processing statistics (chunks created, pages processed, etc.)

### Step 3: Search Your Documents
1. Enter a search query in the main search box
2. Optionally filter by document source:
   - **All**: Search all documents
   - **Uploaded**: Only search your uploaded PDFs
   - **PubMed**: Only search PubMed documents
3. Adjust search settings:
   - **Maximum Results**: Number of results to return
   - **Score Threshold**: Minimum relevance score
   - **Exact Search**: Use exact vs approximate search

### Step 4: View Results
Results are displayed in three tabs:
- **📄 Results**: Expandable cards with document content and metadata
- **📊 Analysis**: Statistics and source distribution
- **📈 Score Distribution**: Visualization of relevance scores

## Configuration

### Document Processing Settings

Edit the chunking parameters in the sidebar:
- **Chunk Size**: Larger chunks preserve more context but may reduce precision
- **Chunk Overlap**: Higher overlap ensures continuity but increases storage

### Collection Management

The app uses the same Qdrant collection for both uploaded and PubMed documents. Documents are distinguished by the `source` field in their metadata.

### Advanced Configuration

For advanced settings, modify the initialization parameters in `app_with_upload.py`:

```python
# PDF Processor settings
pdf_processor = PDFProcessor(
    use_ocr=True,           # Enable/disable OCR
    extract_tables=True,    # Extract tables from PDFs
    extract_images=False,   # Extract images (disabled for performance)
    ocr_language='eng',     # OCR language
    dpi=300                # DPI for PDF to image conversion
)

# Embedding model
model_name = "sentence-transformers/all-MiniLM-L6-v2"  # Fast, efficient model
# Alternative: "sentence-transformers/all-mpnet-base-v2" # More accurate but slower
```

## Troubleshooting

### Common Issues

1. **"Tesseract not found" warning**
   - Install Tesseract OCR: `brew install tesseract` (Mac) or `apt-get install tesseract-ocr` (Linux)
   - OCR will be disabled but text PDFs will still work

2. **PDF processing fails**
   - Check PDF file isn't corrupted
   - Ensure sufficient disk space for temporary files
   - Try reducing chunk size for large documents

3. **Slow processing for scanned PDFs**
   - OCR is computationally intensive
   - Consider disabling OCR if not needed
   - Process fewer files at once

4. **Qdrant connection error**
   - Ensure Qdrant is running: `docker ps | grep qdrant`
   - Check port 6333 is not blocked
   - Verify host/port settings in sidebar

### Performance Tips

1. **For faster processing**:
   - Disable OCR if PDFs contain extractable text
   - Use smaller chunk sizes
   - Process files in smaller batches

2. **For better search quality**:
   - Use larger chunk sizes (1000-1500 characters)
   - Increase chunk overlap (100-150 characters)
   - Enable exact search mode for critical queries

3. **For large document collections**:
   - Consider using a more powerful embedding model
   - Increase Qdrant's memory allocation
   - Use batch processing for initial indexing

## API Integration

The processed documents can also be accessed programmatically:

```python
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# Connect to Qdrant
client = QdrantClient(host="localhost", port=6333)

# Search for uploaded documents
results = client.query_points(
    collection_name="pubmed_documents",
    query=model.encode("your search query"),
    query_filter={
        "must": [{"key": "source", "match": {"value": "uploaded"}}]
    },
    limit=10
)
```

## File Support

### Fully Supported
- Standard PDF files with extractable text
- Scanned PDFs (with OCR enabled)
- PDFs with mixed content (text + images)
- Multi-page documents

### Limitations
- Maximum file size: Limited by available memory
- Password-protected PDFs: Not supported
- Corrupted PDFs: Will fail processing
- Complex layouts: May lose formatting

## Next Steps

- **Bulk Processing**: Use the `index_pdfs.py` script for bulk PDF indexing
- **Custom Collections**: Create separate collections for different document sets
- **Advanced Search**: Implement faceted search and metadata filtering
- **Export Results**: Add functionality to export search results
- **Document Management**: Add delete/update capabilities for uploaded documents

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the logs in the console
3. Ensure all dependencies are correctly installed
4. Verify Qdrant is running and accessible