# 🔬 Streamlit App User Guide

## Overview

The Streamlit app provides a beautiful, user-friendly web interface for searching the PubMed document collection using semantic search.

## Features

- 🔍 **Semantic Search** - Natural language queries
- ⚡ **Fast Search Mode** - HNSW approximate search (~95% accurate, 2-5ms)
- 🎯 **Exact Search Mode** - Brute force search (100% accurate, 10-50ms)
- 📊 **Visual Analytics** - Score distributions, section analysis
- 🕐 **Search History** - Quick access to recent queries
- ⚙️ **Configurable Settings** - Adjust results, thresholds, and more

---

## Quick Start

### 1. Start Qdrant Server

```bash
# Using Docker
docker run -p 6333:6333 qdrant/qdrant

# Or start local Qdrant if already configured
```

### 2. Launch the App

```bash
# Using uv
uv run streamlit run app.py

# Or with regular Python (if venv activated)
streamlit run app.py
```

### 3. Access the App

Open your browser to: **http://localhost:8501**

---

## Using the App

### Basic Search

1. **Enter your query** in the search box
   ```
   Example: "diabetes prevention strategies"
   ```

2. **Click "🚀 Search"** or press Enter

3. **View results** with:
   - Relevance scores
   - Abstract content
   - Section labels
   - Timing information

### Search Settings (Sidebar)

#### 📊 Maximum Results
- **Slider**: 1-50 results
- **Default**: 10
- **Use**: Adjust how many documents to retrieve

#### 🎯 Minimum Score Threshold
- **Slider**: 0.0 - 1.0
- **Default**: 0.0 (show all)
- **Use**: Filter out low-relevance results
- **Tip**: Set to 0.5-0.6 for high-quality results only

#### 🎯 Exact Search Mode
- **Toggle**: Enable/Disable
- **Default**: Disabled (Fast Mode)
- **Fast Mode**: ⚡ HNSW approximate search (faster)
- **Exact Mode**: 🎯 Brute force search (slower, 100% accurate)

---

## Fast Mode vs Exact Mode

### When to Use Fast Mode ⚡ (Default)

✅ **Best for**:
- Regular searches
- Interactive exploration
- Quick lookups
- Production use
- Large result sets

**Performance**:
- Search time: 2-5ms
- Accuracy: ~95-98%
- Scales to millions of documents

**Example**:
```
Query: "HIV treatment"
⚡ Fast Mode: 3.2ms | Found 10 results | Score: 0.87
```

### When to Use Exact Mode 🎯

✅ **Best for**:
- Critical research
- Quality assurance
- Benchmarking
- Small collections
- Maximum accuracy needed

**Performance**:
- Search time: 10-50ms
- Accuracy: 100%
- Slower on large collections

**Example**:
```
Query: "HIV treatment"
🎯 Exact Mode: 28.5ms | Found 10 results | Score: 0.88
```

### How to Enable Exact Search

**In the App**:
1. Look at the **left sidebar**
2. Under "🔍 Search Settings"
3. Check the box: **"🎯 Exact Search Mode"**
4. Run your search

**Visual Indicator**:
- The search spinner will show: "🎯 Exact Search in progress..."
- Results will display: **"🎯 Exact"** mode badge (blue)
- Compare timing with Fast Mode

---

## Sample Queries

Try these example queries:

### Medical Research
- `HIV treatment effectiveness`
- `diabetes prevention strategies`
- `cancer immunotherapy clinical trials`
- `COVID-19 vaccine efficacy`

### Disease Management
- `hypertension management`
- `cardiovascular disease prevention`
- `antibiotic resistance mechanisms`

### Mental Health
- `mental health interventions`
- `depression treatment outcomes`
- `anxiety disorder therapies`

### Public Health
- `vaccination programs effectiveness`
- `obesity prevention strategies`
- `smoking cessation methods`

---

## Understanding Results

### Result Card Components

Each result displays:

```
🟢 Result 1 - Abstract ID: 12345678 (Score: 0.8534)
├─ Relevance Score: 0.8534 (higher = more relevant)
├─ Sentences: 15
├─ Dataset Split: TRAIN
├─ Sections: BACKGROUND, METHODS, RESULTS
└─ Abstract Content: Full text of the abstract...
```

### Score Interpretation

| Score Range | Quality | Color |
|-------------|---------|-------|
| 0.80 - 1.00 | Excellent match | 🟢 Green |
| 0.50 - 0.79 | Good match | 🟡 Yellow |
| 0.00 - 0.49 | Weak match | 🔴 Red |

### Timing Metrics

```
⚡ Total Time: 47.3 ms
   ├─ 🧠 Embedding Time: 43.8 ms (generating query vector)
   └─ 🔍 Search Time: 3.5 ms (Qdrant search)
```

**Typical Performance**:
- **Embedding**: 40-50ms (first search), 0ms (cached)
- **Fast Search**: 2-5ms
- **Exact Search**: 10-50ms
- **Total (Fast)**: 42-55ms
- **Total (Exact)**: 50-100ms

---

## Analysis Tabs

### 📄 Results Tab
- Expandable cards for each result
- Full abstract content
- Metadata and labels

### 📊 Analysis Tab
- **Score Statistics**: Avg, Max, Min, Std Dev
- **Section Distribution**: Bar chart of abstract sections
- Helps understand result composition

### 📈 Score Distribution Tab
- **Histogram**: Distribution of relevance scores
- **Score vs Rank**: How scores decrease with rank
- Useful for quality assessment

---

## Advanced Features

### Connection Settings

Click **"🔌 Connection Settings"** in sidebar:

```
Qdrant Host: localhost
Qdrant Port: 6333
Collection Name: pubmed_documents
```

**Use when**:
- Connecting to remote Qdrant server
- Using different collection
- Custom port configurations

### Search History

- **Location**: Bottom of sidebar
- **Capacity**: Last 10 searches
- **Use**: Click any previous query to re-run it

### Collection Info

Shows in sidebar:
```
✅ Connected to Qdrant
Documents: 20,000
Collection Status: GREEN
```

---

## Comparing Fast vs Exact Mode

### Side-by-Side Test

1. **Run search in Fast Mode**:
   - Uncheck "🎯 Exact Search Mode"
   - Search: "machine learning"
   - Note the timing and top results

2. **Run same search in Exact Mode**:
   - Check "🎯 Exact Search Mode"
   - Search: "machine learning"
   - Compare timing and results

### Expected Differences

**Timing**:
```
Fast Mode:  Search Time: 3.2ms  | Total: 47.5ms
Exact Mode: Search Time: 28.1ms | Total: 72.3ms
```

**Results**:
```
Fast Mode:  Top 5 usually match Exact Mode's top 5
Exact Mode: Guaranteed best matches
```

**Accuracy**:
- Fast: 4-5 out of 5 results match exact mode
- Exact: 5 out of 5 (by definition)

---

## Troubleshooting

### "Connection Error" in Sidebar

**Problem**: Cannot connect to Qdrant

**Solutions**:
1. Check Qdrant is running:
   ```bash
   docker ps | grep qdrant
   ```
2. Verify port 6333 is open
3. Check connection settings in sidebar

### "No results found"

**Problem**: Query returns 0 results

**Solutions**:
1. Lower the score threshold to 0
2. Try a different query
3. Check collection has documents:
   - Look at "Documents" count in sidebar

### Slow Performance

**Problem**: Searches take >1 second

**Solutions**:
1. Use Fast Mode (uncheck Exact Search)
2. Check Qdrant server health
3. Reduce number of results
4. Check network connection (if remote Qdrant)

### Model Loading Takes Too Long

**Problem**: "Loading embedding model" takes >30 seconds

**Solutions**:
1. First load is slow (downloads model)
2. Subsequent loads are cached (fast)
3. Check internet connection for initial download
4. Model is cached in `~/.cache/torch/sentence_transformers/`

---

## Performance Tips

### For Faster Searches

1. ✅ **Use Fast Mode** (default)
2. ✅ **Enable caching** (automatic in app)
3. ✅ **Use lower result limits** (10 instead of 50)
4. ✅ **Run Qdrant locally** (not remote)

### For Better Accuracy

1. ✅ **Use Exact Mode** for critical queries
2. ✅ **Increase score threshold** (filter weak results)
3. ✅ **Review multiple results** (not just top 1)
4. ✅ **Try query variations** (different phrasings)

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Search (when in query box) |
| `Tab` | Navigate fields |
| `Esc` | Clear focus |

---

## Command Line Options

### Basic Launch
```bash
streamlit run app.py
```

### Custom Port
```bash
streamlit run app.py --server.port 8080
```

### Custom Host (allow remote access)
```bash
streamlit run app.py --server.address 0.0.0.0
```

### Disable Auto-open Browser
```bash
streamlit run app.py --server.headless true
```

### All Options
```bash
streamlit run app.py \
  --server.port 8080 \
  --server.address 0.0.0.0 \
  --server.headless true \
  --theme.base light
```

---

## Example Workflow

### Research Workflow

1. **Exploratory Search** (Fast Mode):
   ```
   Query: "diabetes treatment"
   Mode: ⚡ Fast
   Results: 20
   Threshold: 0.0
   ```

2. **Refine Search** (add threshold):
   ```
   Query: "diabetes type 2 insulin therapy"
   Mode: ⚡ Fast
   Results: 10
   Threshold: 0.6
   ```

3. **Final Validation** (Exact Mode):
   ```
   Query: "type 2 diabetes insulin therapy outcomes"
   Mode: 🎯 Exact
   Results: 10
   Threshold: 0.7
   ```

4. **Analyze Results**:
   - Review Analysis tab
   - Check score distribution
   - Export findings

---

## Screenshot Guide

### Main Interface
```
┌─────────────────────────────────────────────────┐
│ 🔬 PubMed Semantic Search                       │
├─────────────────────────────────────────────────┤
│                                                 │
│ 🔍 [Enter your search query...        ] 🚀     │
│                                                 │
├─────────────────────────────────────────────────┤
│ ⚡47ms  🧠44ms  🔍3ms  ⚡Fast                    │
├─────────────────────────────────────────────────┤
│                                                 │
│ 📄 Results | 📊 Analysis | 📈 Distribution     │
│                                                 │
│ 🟢 Result 1 - Abstract ID: 12345 (0.8534)      │
│ 🟢 Result 2 - Abstract ID: 67890 (0.8421)      │
│ ...                                             │
└─────────────────────────────────────────────────┘
```

### Sidebar
```
┌──────────────────────┐
│ ⚙️ Configuration     │
├──────────────────────┤
│ 🔍 Search Settings   │
│                      │
│ Max Results: [10]    │
│                      │
│ Score Threshold:     │
│ [■■□□□□□□□□] 0.0     │
│                      │
│ ☑️ 🎯 Exact Search   │
│                      │
├──────────────────────┤
│ 📊 Collection Info   │
│ ✅ Connected         │
│ Documents: 20,000    │
└──────────────────────┘
```

---

## FAQ

### Q: What's the difference between Fast and Exact mode?

**A**: 
- **Fast Mode**: Uses HNSW approximate search. ~95% accurate, 2-5ms search time.
- **Exact Mode**: Brute force search. 100% accurate, 10-50ms search time.

### Q: When should I use Exact mode?

**A**: Use Exact mode for:
- Critical research requiring maximum accuracy
- Benchmarking and quality assurance
- Small collections where speed difference is minimal
- When you need guaranteed best results

### Q: Why is the first search slow?

**A**: First search loads and caches the embedding model (~1-2 seconds). Subsequent searches are fast.

### Q: Can I compare Fast vs Exact results?

**A**: Yes! Run the same query twice:
1. First with Fast Mode (unchecked box)
2. Then with Exact Mode (checked box)
Compare the results and timing.

### Q: Does Exact mode give different results?

**A**: Usually 4-5 out of top 5 results are the same. Exact mode guarantees finding THE best matches, but Fast mode is very close.

### Q: How do I make searches faster?

**A**:
- Use Fast Mode (default)
- Reduce result limit (10 instead of 50)
- Run Qdrant locally
- Embedding is cached automatically

---

## Support

For issues or questions:
1. Check this guide
2. Review troubleshooting section
3. Check Qdrant connection
4. Verify collection has documents

---

**Happy Searching! 🔬**

