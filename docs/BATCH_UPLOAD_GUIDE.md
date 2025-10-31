# 📚 Batch Upload Feature - User Guide

## Overview

The Enhanced Streamlit App now supports **multiple file uploads** with **Select All** functionality for batch processing!

---

## 🚀 Features

### ✅ Multiple File Selection
- Upload multiple PDFs at once
- Select which files to process using checkboxes
- **"Select All"** button to quickly select all files
- **"Deselect All"** button to clear selection

### 📊 Batch Processing
- Process multiple files in one go
- Real-time progress indicator
- Aggregate statistics across all files
- Individual file statistics table

### 📈 Enhanced Statistics
- Total metrics (files, pages, tables, chunks, time)
- Per-file breakdown table
- Success/error status for each file
- Aggregate timing charts

---

## 🎯 How to Use

### Step 1: Launch the App

```bash
streamlit run apps/streamlit_upload_app_enhanced.py
```

Or use the helper script:

```bash
bash run_enhanced_app.sh
```

### Step 2: Upload Multiple Files

1. Click the **"Browse files"** button
2. Select multiple PDFs (hold Ctrl/Cmd for multi-select in file dialog)
3. Or drag & drop multiple files

### Step 3: Select Files to Process

Three ways to select:

#### Option A: Select All
Click **"✅ Select All"** button to select all uploaded files

#### Option B: Deselect All
Click **"❌ Deselect All"** to clear all selections

#### Option C: Individual Selection
Use checkboxes next to each file to select specific ones

### Step 4: Process Selected Files

1. Click **"🚀 Process Selected"**
2. Watch the progress bar
3. Review batch processing summary

---

## 📊 Batch Processing Output

### Aggregate Metrics
- **Files**: Total number of files processed
- **Pages**: Total pages across all PDFs
- **Tables**: Total tables extracted
- **Chunks**: Total chunks created
- **Total Time**: Cumulative processing time

### Individual File Statistics Table

| File | Pages | Tables | Chunks | Time (s) | Status |
|------|-------|--------|--------|----------|--------|
| doc1.pdf | 25 | 3 | 45 | 12.5 | ✅ Success |
| doc2.pdf | 18 | 1 | 32 | 8.3 | ✅ Success |

### Detailed Statistics
- Cleaning statistics (first file as example)
- Total processing time breakdown chart
- Step-by-step timing for all files combined

---

## 💡 Tips & Best Practices

### 1. **Large Batch Processing**
- For 10+ files, consider processing in smaller batches
- Monitor system memory usage
- Each file is processed sequentially for stability

### 2. **File Selection Strategy**
- Use "Select All" for full batch processing
- Use individual checkboxes to skip problematic files
- Deselect files you've already processed

### 3. **Configuration**
- Set chunking strategy **before** uploading files
- All selected files use the same configuration
- Configure cleaning options in sidebar

### 4. **Error Handling**
- Files with errors show ❌ status in the table
- Other files continue processing
- Check individual error messages in the table

### 5. **Performance**
- Progress bar shows current file being processed
- Status text shows: "Processing 3/10: filename.pdf"
- Total time includes all files

---

## 🎨 UI Features

### File List Display
```
📁 5 file(s) selected (12.5 MB total)

Selected Files:
┌──────────────────────────────────────────┐
│ ✅ Select All    ❌ Deselect All         │
├──────────────────────────────────────────┤
│ ☑ 📄 document1.pdf (2.3 MB)              │
│ ☑ 📄 document2.pdf (3.1 MB)              │
│ ☐ 📄 document3.pdf (1.8 MB)              │
│ ☑ 📄 document4.pdf (4.2 MB)              │
│ ☑ 📄 document5.pdf (1.1 MB)              │
└──────────────────────────────────────────┘

4 file(s) ready to process
              [🚀 Process Selected]
```

### Progress Indicator
```
Processing 3/5: document3.pdf
█████████░░░░░░░░░░░░ 60%
```

### Results Summary
```
✅ Successfully processed 4 document(s)!

📊 Batch Processing Summary
┌──────┬───────┬────────┬────────┬────────────┐
│Files │ Pages │ Tables │ Chunks │ Total Time │
├──────┼───────┼────────┼────────┼────────────┤
│  4   │  86   │   8    │  156   │   45.2s    │
└──────┴───────┴────────┴────────┴────────────┘
```

---

## 🔧 Technical Details

### File Processing Flow
1. User uploads multiple files
2. Files appear in selection list
3. User selects files via checkboxes or "Select All"
4. User clicks "Process Selected"
5. Each file is processed sequentially:
   - PDF extraction
   - Document cleaning (if enabled)
   - Chunking (selected strategy)
   - Vector embedding
   - Qdrant indexing
6. Progress updates after each file
7. Summary statistics displayed

### Session State Management
```python
st.session_state.selected_files = set()  # Tracks selected files
```

- Persists across reruns
- Cleared after successful processing
- Survives UI interactions

### Memory Considerations
- Files are processed one at a time
- Previous file is released before next file
- Embeddings cached efficiently
- Progress bar updates to free memory

---

## 🆚 Comparison: Single vs Batch Upload

| Feature | Single Upload | Batch Upload (New) |
|---------|--------------|-------------------|
| Files at once | 1 | Unlimited |
| File selection | Auto-process | Checkbox selection |
| Select All | N/A | ✅ Available |
| Progress tracking | Single spinner | Progress bar + counter |
| Statistics | Per file | Aggregate + per file |
| Error handling | Stops on error | Continues processing |
| Time efficiency | N/A | Process multiple files in one session |

---

## 🎯 Use Cases

### 1. **Research Paper Collection**
Upload 20 research papers, select all, process with semantic chunking

### 2. **Document Library Migration**
Upload entire folder, select all, index with context chunking

### 3. **Selective Processing**
Upload 10 files, manually select 5 to test different chunking strategies

### 4. **Re-indexing**
Upload files, deselect already processed ones, process only new ones

### 5. **Quality Control**
Upload files, process few at a time to review cleaning/chunking results

---

## 📝 Example Workflow

### Scenario: Index 15 Research Papers

1. **Configure** (Sidebar)
   - Chunking: Semantic + Late (Hybrid)
   - Chunk size: 512
   - Enable cleaning: ✓
   - Remove TOC: ✓

2. **Upload Files**
   - Click "Browse files"
   - Select all 15 PDFs
   - Files appear in list

3. **Select All**
   - Click "✅ Select All"
   - All 15 files checked

4. **Process**
   - Click "🚀 Process Selected"
   - Watch progress: "Processing 1/15..."
   - Wait ~3 minutes (depends on file size)

5. **Review Results**
   - Batch summary: 15 files, 380 pages, 45 tables, 890 chunks
   - Individual table shows each file's stats
   - All files show "✅ Success"

6. **Search**
   - Go to "🔍 Search" tab
   - Query across all 15 documents
   - See results with full context

---

## 🚀 Quick Start Commands

```bash
# Start Qdrant
docker-compose up -d qdrant

# Launch app
streamlit run apps/streamlit_upload_app_enhanced.py

# Or use helper script
bash run_enhanced_app.sh
```

---

## 🐛 Troubleshooting

### Issue: "Select All" doesn't work
**Solution**: Refresh the page (Ctrl+R), files should persist

### Issue: Processing stops mid-batch
**Solution**: Check logs for errors, processed files are already indexed

### Issue: Can't select files
**Solution**: Make sure files are uploaded first (shows file count)

### Issue: Progress bar stuck
**Solution**: Large files take time, check terminal for progress logs

### Issue: Out of memory
**Solution**: Process fewer files at once (5-10 at a time)

---

## 🎉 What's New

**Previous Version:**
- Single file upload only
- Manual re-upload for each file
- No progress tracking
- Basic statistics

**New Version:**
- ✅ Multiple file uploads
- ✅ Select All / Deselect All buttons
- ✅ Checkbox selection per file
- ✅ Batch processing with progress bar
- ✅ Aggregate statistics
- ✅ Individual file statistics table
- ✅ Error handling per file
- ✅ Total time tracking
- ✅ Memory efficient processing

---

## 📚 Related Documentation

- **[Chunking Strategies](CHUNKING_STRATEGIES_GUIDE.md)** - Configure chunking
- **[Document Cleaning](DOCUMENT_CLEANING_SUMMARY.md)** - Cleaning options
- **[Action Plan](ACTION_PLAN.md)** - Re-indexing existing documents
- **[Enhanced App Guide](RUN_ENHANCED_APP.md)** - Full app features

---

## 🤝 Feedback & Support

Happy batch processing! 🎉

**Key Benefit**: Process your entire document collection in minutes instead of hours!



