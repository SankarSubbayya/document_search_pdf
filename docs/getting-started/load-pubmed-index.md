# 🏥 Loading PubMed Index into Qdrant

## Overview

The PubMed index contains 200,000 medical research articles from randomized controlled trials (RCTs). This guide shows you how to load this data into Qdrant for semantic search.

## Prerequisites

### 1. Ensure Qdrant is Running
```bash
# Check if Qdrant is running
curl http://localhost:6333/collections

# If not running, start it:
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant
```

### 2. Check Data File Exists
```bash
# The PubMed data file should exist at:
ls -lh data/pubmed/processed/pubmed_200k_rct_processed.jsonl

# File size should be ~726MB
# If missing, run: python src/data/download_and_prepare.py
```

## 🚀 Quick Start - Load PubMed Index

### Option 1: Load Full Dataset (Recommended)
```bash
# Load all 200,000 documents
uv run python load_pubmed_data.py

# This will:
# - Create 'pubmed_documents' collection
# - Index all 200k documents
# - Take ~15-30 minutes depending on your system
```

### Option 2: Load Sample for Testing
```bash
# Load only first 1,000 documents for quick testing
uv run python load_pubmed_data.py --max-docs 1000

# Takes ~1-2 minutes
```

### Option 3: Custom Configuration
```bash
# Custom settings
uv run python load_pubmed_data.py \
    --host localhost \
    --port 6333 \
    --collection pubmed_documents \
    --batch-size 100 \
    --max-docs 10000
```

## 📊 What Gets Indexed

Each PubMed document includes:
- **PMID**: PubMed ID
- **Title**: Article title
- **Abstract**: Full abstract text
- **Authors**: List of authors
- **Journal**: Publication journal
- **Year**: Publication year
- **DOI**: Digital Object Identifier
- **Publication Types**: Article types (RCT, Clinical Trial, etc.)
- **MeSH Terms**: Medical Subject Headings
- **Keywords**: Article keywords

## 🔍 Verify the Index

### Check Collection Status
```bash
# Using curl
curl http://localhost:6333/collections/pubmed_documents

# Or using Python
uv run python -c "
from qdrant_client import QdrantClient
client = QdrantClient('localhost', 6333)
info = client.get_collection('pubmed_documents')
print(f'Documents indexed: {info.points_count}')
"
```

### Test Search
```bash
# Quick search test
uv run python -c "
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

client = QdrantClient('localhost', 6333)
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

query = 'diabetes treatment machine learning'
embedding = model.encode(query)

results = client.search(
    collection_name='pubmed_documents',
    query_vector=embedding.tolist(),
    limit=3
)

for r in results:
    print(f\"Score: {r.score:.4f} - {r.payload.get('title', 'No title')[:80]}...\")
"
```

## 🎯 Using the PubMed Search in Streamlit

Once indexed, you can use the PubMed search in multiple apps:

### 1. Dedicated PubMed Search App
```bash
uv run streamlit run apps/streamlit_pubmed_app.py
```
- Search only PubMed articles
- Medical/research focused
- No upload capability

### 2. Combined Upload + PubMed App
```bash
uv run streamlit run apps/streamlit_upload_app.py
```
- Search both PubMed and uploaded PDFs
- Mixed collection
- Can filter by source

### 3. Check in Apps
The apps will show:
- Collection status in sidebar
- Number of documents indexed
- Search functionality enabled

## ⏱️ Loading Times

| Documents | Approximate Time | Memory Usage |
|-----------|-----------------|--------------|
| 1,000 | 1-2 minutes | ~500 MB |
| 10,000 | 5-10 minutes | ~1 GB |
| 50,000 | 15-25 minutes | ~2 GB |
| 200,000 (full) | 30-60 minutes | ~4 GB |

## 🔧 Troubleshooting

### "Data file not found"
```bash
# Download and prepare the data first
uv run python src/data/download_and_prepare.py
```

### "Failed to connect to Qdrant"
```bash
# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Or check if it's running on different port
docker ps | grep qdrant
```

### "Collection already exists"
```bash
# Option 1: Add to existing collection
uv run python load_pubmed_data.py --no-recreate

# Option 2: Recreate collection (deletes existing data)
uv run python load_pubmed_data.py --recreate
```

### Memory Issues
```bash
# Reduce batch size
uv run python load_pubmed_data.py --batch-size 50

# Or load in chunks
uv run python load_pubmed_data.py --max-docs 50000
# Then append more:
uv run python load_pubmed_data.py --no-recreate --max-docs 50000
```

## 📈 Monitor Progress

The script shows:
- Progress bar during indexing
- Documents processed
- Indexing speed (docs/sec)
- Final statistics
- Test search results

## 🎉 Success Indicators

When successfully loaded, you'll see:
```
✨ PubMed data successfully loaded!
Collection 'pubmed_documents' now has 200000 documents
✅ Search working! Found 3 results for 'machine learning cancer treatment':
  1. Deep Learning Approaches for Cancer Detection... (score: 0.8234)
  2. Machine Learning in Oncology: A Systematic Review... (score: 0.7891)
  3. AI-Driven Personalized Medicine in Cancer... (score: 0.7456)
```

## 🔄 Re-indexing

To re-index with updated data:
```bash
# Delete and recreate
uv run python load_pubmed_data.py --recreate

# Or manually delete first
curl -X DELETE http://localhost:6333/collections/pubmed_documents
uv run python load_pubmed_data.py
```

## 📚 Next Steps

After loading the PubMed index:
1. Test search in the Streamlit apps
2. Adjust search parameters (threshold, document count)
3. Combine with your own PDF uploads
4. Use the visual search controls for better results

The PubMed index provides a rich medical knowledge base for RAG applications!