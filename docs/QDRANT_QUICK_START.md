# Qdrant Local Mode - Quick Start

## ✅ **You're Already Using It!**

Your project uses Qdrant in **local/embedded mode** - no server installation needed!

---

## 🎯 **How It Works**

### **Local Mode (Current Setup)**

```python
from qdrant_client import QdrantClient

# This line stores everything in ./qdrant_db/ directory
client = QdrantClient(path="./qdrant_db")
```

**That's it!** All vectors are stored as files in the `qdrant_db/` folder.

---

## 📂 **Where Is Data Stored?**

```
document_search/
├── qdrant_db/              ← All your vectors stored here!
│   ├── meta.json
│   ├── collections/
│   │   └── documents/      ← Your collections
│   └── ...
```

**To backup:** Copy the `qdrant_db/` folder  
**To reset:** Delete the `qdrant_db/` folder  
**To share:** Zip and send the `qdrant_db/` folder

---

## 🚀 **Quick Examples**

### **1. Basic Usage (Your Current Code)**

```python
from src.document_search import DocumentSearchRAG, Document

# Already configured for local mode!
rag = DocumentSearchRAG()

# Index documents (stored in ./qdrant_db/)
doc = Document(id="1", title="Test", content="Hello world")
rag.index_documents([doc])

# Search (reads from ./qdrant_db/)
results = rag.search("hello", top_k=5)
```

### **2. Direct Qdrant Client**

```python
from qdrant_client import QdrantClient

# Local mode
client = QdrantClient(path="./qdrant_db")

# List collections
collections = client.get_collections()
print(collections)
```

### **3. Check What's Stored**

```python
from qdrant_client import QdrantClient

client = QdrantClient(path="./qdrant_db")

# Get info about a collection
info = client.get_collection("documents")
print(f"Points stored: {info.points_count}")
```

---

## 🔄 **Local vs Server Mode**

| Feature | Local Mode ✅ (Current) | Server Mode |
|---------|----------------------|-------------|
| Installation | None needed | Docker/Binary |
| Storage | Files in directory | Server database |
| Performance | Good for dev | Better for production |
| UI Dashboard | No | Yes (http://localhost:6333/dashboard) |
| Multiple Clients | No | Yes |
| **Best For** | Development, Testing | Production, Large Scale |

---

## 💡 **Common Operations**

### **View Collections**
```bash
source .venv/bin/activate
python -c "
from qdrant_client import QdrantClient
client = QdrantClient(path='./qdrant_db')
for col in client.get_collections().collections:
    print(col.name)
"
```

### **Get Collection Stats**
```bash
python -c "
from qdrant_client import QdrantClient
client = QdrantClient(path='./qdrant_db')
info = client.get_collection('documents')
print(f'Points: {info.points_count}')
print(f'Vector size: {info.config.params.vectors.size}')
"
```

### **Clear a Collection**
```bash
python -c "
from qdrant_client import QdrantClient
client = QdrantClient(path='./qdrant_db')
client.delete_collection('documents')
print('Collection deleted!')
"
```

---

## 📚 **Run the Example**

```bash
source .venv/bin/activate
python examples/use_local_qdrant.py
```

This will show you:
- How local mode works
- How to index and search
- How to inspect storage
- Comparison with server mode

---

## 🎉 **Bottom Line**

**You don't need to install anything!** 

Qdrant local mode is already working in your project. Just use your RAG classes and everything is stored in `./qdrant_db/`.

Want to try it? Run:
```bash
source .venv/bin/activate
python quick_test.py
```

This will test your RAG system with local Qdrant storage!

