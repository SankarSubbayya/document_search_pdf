# 🚀 How to Run the PDF Document Search Applications

> ## ⚠️ CRITICAL: Always Use `uv run`
>
> **NEVER run:**
> ```bash
> streamlit run apps/pdf_manager_app.py  # ❌ WRONG - Will cause import errors!
> ```
>
> **ALWAYS run:**
> ```bash
> uv run streamlit run apps/pdf_manager_app.py  # ✅ CORRECT
> ```
>
> Running without `uv run` will cause `ModuleNotFoundError: No module named 'PyPDF2'` and other import errors.
> This project uses UV for dependency management - all commands MUST be prefixed with `uv run`.

## 📋 Prerequisites

### 1. Install Dependencies

```bash
# Option A: Using UV (Fastest - REQUIRED for proper execution)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# Option B: Using pip (Alternative - may have issues)
pip install -r requirements.txt
```

### 2. Start Qdrant Vector Database

```bash
# Option A: Using Docker (Recommended)
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant

# Option B: Using Docker Compose
docker-compose up -d

# Option C: Using the script
./scripts/runners/start_qdrant.sh
```

### 3. Set Up Environment Variables (Optional)

```bash
# Copy sample environment file
cp sample.env .env

# Edit .env and add your API keys if needed
# Note: The apps work without OpenAI API key for basic PDF processing
```

## 🎯 Running the Applications

### Method 1: Interactive Menu (Easiest)

```bash
./run_apps.sh
```

This will show a menu:
```
1) PDF Manager (Separate Collection)
2) PubMed Search
3) Combined Upload + PubMed Search
4) Run Tests
5) Start Qdrant
6) Exit
```

### Method 2: Direct Commands

#### 📁 PDF Manager App (Recommended for PDF Management)
```bash
# This app manages PDFs in a SEPARATE collection from PubMed
uv run streamlit run apps/pdf_manager_app.py

# Or use the dedicated script (which uses UV automatically)
./scripts/runners/run_pdf_manager.sh
```

**Features:**
- Upload and index PDF documents
- Search your PDFs with semantic search
- Manage documents (view, delete, export)
- Separate collection (`pdf_documents`) - won't mix with PubMed data
- Categories and tags for organization
- Analytics dashboard

**Access:** http://localhost:8501

#### 🔬 PubMed Search App
```bash
# Search the PubMed 200k dataset
uv run streamlit run apps/streamlit_pubmed_app.py

# Or use the script (which uses UV automatically)
./scripts/runners/run_app.sh
```

**Features:**
- Search PubMed medical abstracts
- Fast semantic search
- No upload capability (PubMed only)
- Uses `pubmed_documents` collection

**Access:** http://localhost:8501

#### 📤 Combined Upload + PubMed App
```bash
# Upload PDFs AND search PubMed (mixed collection)
uv run streamlit run apps/streamlit_upload_app.py

# Or use the script
./scripts/runners/run_app_with_upload.sh
```

**Features:**
- Upload PDFs to PubMed collection
- Search both uploaded PDFs and PubMed
- Documents are MIXED in same collection
- Good for augmenting PubMed with your documents

**Access:** http://localhost:8501

## 🔧 Troubleshooting

### Issue: "Qdrant connection failed"

```bash
# Check if Qdrant is running
docker ps | grep qdrant

# If not running, start it:
docker run -p 6333:6333 qdrant/qdrant
```

### Issue: "Module not found"

```bash
# Install dependencies
uv sync  # or pip install -r requirements.txt

# Verify installation
python scripts/utils/verify_installation.py
```

### Issue: "Streamlit not found"

```bash
# Install streamlit
pip install streamlit

# Or with uv
uv pip install streamlit
```

### Issue: Port already in use

```bash
# Kill existing streamlit process
pkill streamlit

# Or run on different port
streamlit run apps/pdf_manager_app.py --server.port 8502
```

## 📊 Quick Test

### 1. Test PDF Processing
```bash
# Run test script
python scripts/utils/test_pdf_processing.py
```

### 2. Test Qdrant Connection
```bash
# Check connection
python scripts/test_qdrant_connection.py
```

### 3. Run Full Test Suite
```bash
# Using UV
uv run pytest tests/

# Using script
./scripts/runners/run_tests.sh
```

## 🎨 Application Comparison

| Feature | PDF Manager | PubMed Search | Combined Upload |
|---------|------------|---------------|-----------------|
| **Collection** | `pdf_documents` | `pubmed_documents` | `pubmed_documents` |
| **Upload PDFs** | ✅ Yes | ❌ No | ✅ Yes |
| **Search PubMed** | ❌ No | ✅ Yes | ✅ Yes |
| **Document Management** | ✅ Full | ❌ None | ⚠️ Limited |
| **Categories/Tags** | ✅ Yes | ❌ No | ❌ No |
| **Analytics** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Best For** | Managing your PDFs | Searching medical lit | Augmenting PubMed |

## 🚦 Quick Start Commands

```bash
# 1. Start Qdrant (required)
docker run -p 6333:6333 qdrant/qdrant &

# 2. Install dependencies (if not done)
uv sync

# 3. Run PDF Manager (recommended)
streamlit run apps/pdf_manager_app.py

# 4. Upload a PDF
# - Click "Browse files" in sidebar
# - Select PDF
# - Click "Process & Index"

# 5. Search
# - Enter query in search box
# - Click "Search"
```

## 📝 First Time Setup

```bash
# 1. Clone and enter directory
cd document_search_pdf

# 2. Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start Qdrant
docker run -p 6333:6333 qdrant/qdrant &

# 5. Run the PDF Manager
streamlit run apps/pdf_manager_app.py

# 6. Open browser to http://localhost:8501
```

## 🔄 Switching Between Apps

You can run multiple apps on different ports:

```bash
# Terminal 1: PDF Manager on port 8501
uv run streamlit run apps/pdf_manager_app.py

# Terminal 2: PubMed Search on port 8502
uv run streamlit run apps/streamlit_pubmed_app.py --server.port 8502

# Terminal 3: Combined on port 8503
uv run streamlit run apps/streamlit_upload_app.py --server.port 8503
```

## 📊 Monitoring

### Check Qdrant Collections
```bash
# View collections
curl http://localhost:6333/collections

# Check specific collection
curl http://localhost:6333/collections/pdf_documents
curl http://localhost:6333/collections/pubmed_documents
```

### View Logs
```bash
# Streamlit logs (in terminal where app is running)
# Qdrant logs
docker logs $(docker ps -q --filter ancestor=qdrant/qdrant)
```

## 🛑 Stopping Services

```bash
# Stop Streamlit app
# Press Ctrl+C in the terminal running the app

# Stop Qdrant
docker stop $(docker ps -q --filter ancestor=qdrant/qdrant)

# Or stop all Docker containers
docker-compose down
```

## 💡 Tips

1. **For PDF Management**: Use `pdf_manager_app.py` - it keeps your PDFs separate
2. **For Medical Research**: Use `streamlit_pubmed_app.py` - optimized for PubMed
3. **For Testing**: Upload small PDFs first to test the system
4. **For Performance**: Keep Qdrant running in the background
5. **For Development**: Use `--server.runOnSave true` flag with streamlit

## 📚 Next Steps

1. Upload your first PDF in the PDF Manager
2. Try searching for content
3. Explore the analytics tab
4. Export your document list
5. Test different search queries

---

**Need Help?**
- Check [TESTING.md](docs/TESTING.md) for testing
- See [PDF_MANAGER_README.md](docs/PDF_MANAGER_README.md) for detailed PDF features
- Review [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for file locations