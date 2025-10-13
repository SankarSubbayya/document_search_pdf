# PDF Document Management System

A dedicated Streamlit application for managing PDF documents with a **separate vector store collection**, completely independent from your PubMed data.

## 🎯 Key Features

### Separate Collection
- **Dedicated vector store**: Uses `pdf_documents` collection (separate from `pubmed_documents`)
- **Independent management**: Your PDFs are completely isolated from PubMed data
- **No mixing**: Search results are PDF-only when using this app

### Document Management
- **📤 Upload**: Batch upload multiple PDFs with progress tracking
- **🔍 Search**: Semantic search with advanced filtering
- **📁 Organize**: Categories and tags for document organization
- **🗑️ Delete**: Remove individual documents or clear entire collection
- **📊 Analytics**: Visualize collection statistics and trends
- **💾 Export**: Download document list as CSV

### Advanced Processing
- **Smart chunking**: Configurable chunk size and overlap
- **Multiple extraction methods**: Automatic fallback for difficult PDFs
- **OCR support**: Process scanned PDFs automatically
- **Metadata extraction**: Preserve PDF title, author, creation date
- **Table detection**: Extract and index table information

## 🚀 Quick Start

### 1. Start Qdrant

```bash
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant
```

### 2. Run the PDF Manager

```bash
./run_pdf_manager.sh
```

The app will open at `http://localhost:8501`

## 📋 System Architecture

### Collection Separation

```
Qdrant Vector Database
├── pdf_documents/          # Your PDF collection (THIS APP)
│   ├── Document chunks
│   ├── Metadata
│   └── Embeddings
│
└── pubmed_documents/       # PubMed collection (SEPARATE)
    ├── PubMed abstracts
    └── Research data
```

### Data Flow

```
PDF Upload → Text Extraction → Chunking → Embedding → Vector Storage
     ↓              ↓             ↓           ↓            ↓
  Original     OCR if needed   Smart      ML Model    Qdrant DB
   Files        Available     Splitting  Processing   (pdf_documents)
```

## 📁 File Structure

```
document_search_pdf/
├── pdf_manager_app.py      # Main application (THIS APP)
├── run_pdf_manager.sh      # Launch script
├── pdf_config.yaml         # Configuration
├── data/
│   ├── pdf_uploads/        # Uploaded PDFs
│   └── pdf_backups/        # Backup storage
└── logs/
    └── pdf_manager.log     # Application logs
```

## 🎨 User Interface

### Main Sections

#### 1. Search Tab
- **Query Input**: Natural language search
- **Filters**: Category, tags, result limit
- **Results**: Expandable cards with highlights
- **Timing**: Performance metrics

#### 2. Documents Tab
- **Document List**: All indexed PDFs
- **Sorting**: By date, name, size, pages
- **Filtering**: Search by document name
- **Actions**: View details, delete documents

#### 3. Analytics Tab
- **Metrics**: Total documents, size, pages, chunks
- **Visualizations**:
  - Category distribution (pie chart)
  - File size histogram
  - Upload timeline
  - Extraction methods used

#### 4. Settings Tab
- **Collection Management**: Refresh stats, clear all
- **Export**: Download document list as CSV
- **Storage**: View and clean upload directory

### Sidebar Features
- **Connection Settings**: Configure Qdrant
- **Upload Section**: Drag & drop PDFs
- **Document Settings**: Category, tags
- **Processing Options**: Chunk size, overlap
- **Collection Stats**: Real-time metrics

## 🔧 Configuration

### Document Categories
- General
- Research
- Documentation
- Legal
- Financial
- Technical
- Educational
- Medical
- Other

### Processing Settings

```yaml
# In pdf_config.yaml
chunking:
  default_size: 512      # Characters per chunk
  default_overlap: 50    # Overlap between chunks

pdf:
  use_ocr: true         # Enable OCR for scanned PDFs
  extract_tables: true  # Extract table information
  dpi: 300             # Resolution for OCR
```

### Search Settings

```yaml
search:
  default_limit: 10     # Results per search
  max_limit: 100       # Maximum allowed results
  hnsw_ef: 128         # HNSW search parameter
```

## 📝 Usage Examples

### Uploading Documents

1. Click "Browse files" in sidebar
2. Select one or more PDFs
3. Choose category and add tags
4. Configure chunk settings
5. Click "Process & Index"
6. Monitor progress bar

### Searching Documents

1. Enter search query
2. Optional: Set filters
   - Category: research, legal, etc.
   - Max results: 1-100
   - Exact search: on/off
3. Click Search
4. Review results with scores

### Managing Documents

1. Go to Documents tab
2. Browse or filter list
3. Click 🗑️ to delete individual docs
4. Use Settings tab for bulk operations

## 🛠️ Advanced Features

### Chunk Position Tracking
Each chunk stores its position in the original document:
- `char_start`: Starting character position
- `char_end`: Ending character position
- Enables precise location references

### Metadata Preservation
PDF metadata is extracted and stored:
- Title, Author, Subject
- Creation and modification dates
- Creator and producer information

### Multi-Method Extraction
Automatic fallback chain:
1. **pdfplumber**: Primary method
2. **PyPDF2**: Secondary fallback
3. **PyMuPDF**: If available
4. **OCR**: Last resort for scanned PDFs

### Smart Chunking
- Sentence-aware splitting
- Configurable overlap
- Preserves context between chunks
- Position tracking for references

## 🚨 Troubleshooting

### Common Issues

#### "Qdrant not running"
```bash
# Start Qdrant with Docker
docker run -p 6333:6333 qdrant/qdrant
```

#### "OCR not working"
```bash
# Install Tesseract
# Mac:
brew install tesseract

# Ubuntu:
sudo apt-get install tesseract-ocr
```

#### "PDF processing failed"
- Check PDF isn't corrupted
- Ensure sufficient disk space
- Try reducing chunk size
- Check logs for details

#### "Search returns no results"
- Verify documents are indexed
- Check collection statistics
- Try broader search terms
- Adjust score threshold

### Performance Tips

#### For Faster Processing
- Disable OCR if not needed
- Use smaller chunk sizes
- Process fewer files at once
- Increase batch size in config

#### For Better Search Quality
- Use larger chunks (1000-1500 chars)
- Increase overlap (100-150 chars)
- Add relevant tags
- Use appropriate categories

#### For Large Collections
- Regular cleanup of upload directory
- Export document list for backup
- Monitor storage usage
- Consider pagination for document list

## 📊 Collection Statistics

The app provides real-time statistics:
- **Total Chunks**: Vector count in collection
- **Unique Documents**: Number of PDFs
- **Average File Size**: Collection average
- **Extraction Methods**: Methods used
- **Upload Timeline**: Historical view

## 🔐 Security Considerations

- **File Size Limit**: 100MB default
- **File Type Validation**: PDF only
- **Isolated Collection**: Separate from other data
- **No External Access**: Local deployment
- **Clean Upload Directory**: Regular maintenance

## 🔄 Backup & Recovery

### Export Documents List
1. Go to Settings tab
2. Click "Export Document List to CSV"
3. Save the CSV file

### Backup Vector Store
```bash
# Backup Qdrant data
cp -r qdrant_storage qdrant_backup_$(date +%Y%m%d)
```

### Clean Upload Directory
1. Go to Settings tab
2. View storage information
3. Click "Clean Upload Directory"

## 🎯 Best Practices

### Document Organization
- Use consistent categories
- Add descriptive tags
- Keep related documents together
- Regular cleanup of old documents

### Search Optimization
- Use specific keywords
- Leverage category filters
- Adjust chunk size for document type
- Monitor search performance metrics

### Collection Maintenance
- Regular statistics refresh
- Export document lists periodically
- Clean upload directory
- Monitor collection growth

## 📈 Future Enhancements

Potential improvements:
- Document versioning
- Collaborative features
- Advanced ACL/permissions
- API endpoint for programmatic access
- Scheduled indexing
- Document relationships/linking
- Full-text highlighting in results
- Custom embedding models

## 🆘 Support

### Logs
Check `logs/pdf_manager.log` for detailed information

### Configuration
Edit `pdf_config.yaml` for customization

### Debug Mode
Set logging level to DEBUG in config:
```yaml
logging:
  level: DEBUG
```

## 📄 License

This PDF Document Management System is part of your document search project and maintains the same license terms.

---

**Note**: This application uses a completely separate vector collection (`pdf_documents`) from your PubMed data (`pubmed_documents`). Your uploaded PDFs will never mix with or appear in PubMed searches, and vice versa.