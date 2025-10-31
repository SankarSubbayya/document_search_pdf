# ⚡ Quick Start Guide

**Get up and running in 5 minutes!**

---

## Step 1: Install Dependencies (2 minutes)

```bash
# Install UV (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

**Alternative (using pip):**
```bash
pip install -r requirements.txt
```

---

## Step 2: Start Qdrant (1 minute)

```bash
# Start Qdrant vector database
docker-compose up -d qdrant
```

**Verify it's running:**
- Open: http://localhost:6333/dashboard
- You should see the Qdrant dashboard

**Don't have Docker?**
```bash
# Install Docker: https://docs.docker.com/get-docker/
# Or use Docker Desktop
```

---

## Step 3: Launch the App (30 seconds)

```bash
# Launch the enhanced upload app
streamlit run apps/streamlit_upload_app_enhanced.py
```

**Your browser will open automatically** at `http://localhost:8501`

---

## Step 4: Upload Your First Document (1 minute)

In the Streamlit app:

1. **Configure** (sidebar):
   - Chunking Strategy: `Semantic` (default is good)
   - Enable Document Cleaning: ✓
   
2. **Upload**:
   - Click "Browse files"
   - Select one or more PDF files
   - Click "Select All"
   - Click "🚀 Process Selected"

3. **Wait** for processing to complete (~10 seconds per document)

---

## Step 5: Search Your Documents (30 seconds)

1. Click the **"🔍 Search"** tab

2. Enter a query:
   ```
   What is machine learning?
   ```

3. Click **"🔍 Search"**

4. View results with full context!

---

## 🎉 You're Done!

**What you just did:**
- ✅ Installed the system
- ✅ Started the vector database
- ✅ Launched the web application
- ✅ Uploaded and indexed PDF documents
- ✅ Performed semantic search

---

## 🚀 Next Steps

### Explore More Features

**Upload More Documents:**
```bash
# Use batch upload to process entire folders
# Select multiple PDFs, click "Select All", process!
```

**Try Different Chunking Strategies:**
- Semantic (default) - Good for general use
- Context - Adds surrounding context
- Late - Best quality (slower)
- Semantic + Late - Hybrid approach

**View Your Index:**
```bash
# See what's indexed
python view_qdrant.py
```

**Manage Documents:**
```bash
# Delete documents from index
python delete_documents.py

# Or use the PDF Manager app
streamlit run apps/pdf_manager_app.py
```

---

## 📚 Learn More

- **[Full README](README.md)** - Complete project overview
- **[Batch Upload Guide](BATCH_UPLOAD_GUIDE.md)** - Upload multiple files
- **[Chunking Guide](docs/CHUNKING_STRATEGIES_GUIDE.md)** - Understand chunking
- **[Documentation Index](DOCUMENTATION_INDEX.md)** - All documentation

---

## 🆘 Troubleshooting

### Qdrant Not Running?

```bash
# Check if Qdrant is running
curl http://localhost:6333/collections

# If not, start it
docker-compose up -d qdrant

# Check logs
docker-compose logs qdrant
```

### Import Errors?

```bash
# Reinstall dependencies
uv sync

# Or with pip
pip install -r requirements.txt --force-reinstall
```

### Port Already in Use?

```bash
# Streamlit uses port 8501 by default
# Kill process using the port
lsof -ti:8501 | xargs kill -9

# Or specify different port
streamlit run apps/streamlit_upload_app_enhanced.py --server.port 8502
```

### Need More Help?

```bash
# Run system diagnostics
python scripts/test_qdrant_connection.py

# Check troubleshooting guide
cat docs/troubleshooting/fixes-summary.md
```

---

## 💡 Quick Tips

**Tip 1:** Use the Enhanced Upload App for the best experience
```bash
streamlit run apps/streamlit_upload_app_enhanced.py
```

**Tip 2:** Enable document cleaning to remove TOC and acknowledgements
- Check "Enable Document Cleaning" in sidebar

**Tip 3:** Start with Semantic chunking, experiment later
- It's fast and works well for most documents

**Tip 4:** Use "Select All" for batch processing
- Upload 10 PDFs, click "Select All", process in one go!

**Tip 5:** Monitor your index in the Qdrant dashboard
- http://localhost:6333/dashboard

---

## 📊 What Happens Behind the Scenes?

When you upload a PDF:

1. **Extract Text** - PDF content is extracted
2. **Clean** - TOC, acknowledgements removed (if enabled)
3. **Chunk** - Text split into semantic chunks
4. **Embed** - Chunks converted to vector embeddings
5. **Index** - Stored in Qdrant vector database

When you search:

1. **Query Embedding** - Your query → vector
2. **Similarity Search** - Find closest vectors
3. **Rerank** - Improve result quality
4. **Display** - Show results with context

---

## 🎯 Common First Commands

```bash
# Start everything
docker-compose up -d qdrant
streamlit run apps/streamlit_upload_app_enhanced.py

# View indexed documents
python view_qdrant.py

# Delete documents
python delete_documents.py

# Test connection
python scripts/test_qdrant_connection.py

# Run tests
uv run pytest tests/
```

---

## 📈 Typical Workflow

```
1. Start Qdrant
   ↓
2. Launch Streamlit app
   ↓
3. Configure chunking & cleaning
   ↓
4. Upload PDFs (batch or single)
   ↓
5. Process & index
   ↓
6. Search & explore
   ↓
7. Manage documents (view, delete)
```

---

## 🎓 Learning Path

**Beginner (You are here!):**
- ✅ Quick Start (this guide)
- → [Full README](README.md)
- → [Batch Upload Guide](BATCH_UPLOAD_GUIDE.md)

**Intermediate:**
- → [Chunking Strategies](docs/CHUNKING_STRATEGIES_GUIDE.md)
- → [Document Cleaning](docs/DOCUMENT_CLEANING_GUIDE.md)
- → [Search Features](docs/user-guide/search-features.md)

**Advanced:**
- → [System Architecture](docs/architecture/system-architecture.md)
- → [Development Guide](docs/development/testing.md)
- → Source code in `src/`

---

## 🔥 Pro Tips

**Fastest Upload:**
1. Configure once in sidebar
2. Upload all PDFs at once
3. Click "Select All"
4. Let it run - go grab coffee ☕

**Best Search Results:**
1. Enable document cleaning
2. Use Semantic or Semantic+Late chunking
3. Adjust score threshold if too many/few results
4. Read the context around main content

**Efficient Management:**
1. Use `view_qdrant.py` to see what's indexed
2. Use `delete_documents.py` for bulk deletion
3. Check Qdrant dashboard for statistics
4. Re-index when switching chunking strategies

---

## ✅ Checklist

Before you start:
- [ ] Python 3.8+ installed
- [ ] Docker installed and running
- [ ] Dependencies installed (`uv sync`)
- [ ] Qdrant running (http://localhost:6333/dashboard)
- [ ] Streamlit app launched

If all checked, you're ready to go! 🚀

---

## 📞 Still Need Help?

1. Check [Documentation Index](DOCUMENTATION_INDEX.md)
2. Read [Troubleshooting Guide](docs/troubleshooting/fixes-summary.md)
3. Run diagnostics: `python scripts/test_qdrant_connection.py`
4. Review logs: `docker-compose logs qdrant`

---

**Total Time:** ~5 minutes from zero to searching documents

**Happy Searching! 🎉**



