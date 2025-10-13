# Search Features Guide

Both PDF Manager and Upload apps now include advanced search controls for fine-tuning your document searches.

## Available Search Options

### 1. Number of Results Slider
- **Location**: Search Filters section (PDF Manager) / Sidebar (Upload App)
- **Range**: 1-50 documents
- **Default**: 10 documents
- **Purpose**: Control how many documents are returned in search results

### 2. Minimum Similarity Score
- **Location**: Search Filters section (PDF Manager) / Sidebar (Upload App)
- **Range**: 0.0 to 1.0
- **Default**: 0.0 (show all results)
- **Purpose**: Filter out low-relevance results
- **How it works**:
  - 0.0 = Show all results regardless of relevance
  - 0.5 = Only show results with >50% similarity
  - 0.7 = Only show highly relevant results (>70% similarity)
  - 1.0 = Only perfect or near-perfect matches

### 3. Exact Search Mode
- **Location**: Search Filters section (both apps)
- **Default**: Off (Fast approximate search)
- **Purpose**: Toggle between fast approximate and exact search
- **Trade-offs**:
  - Fast Mode: Quick results, good for most searches
  - Exact Mode: Slower but 100% accurate, best for critical searches

## How to Use

### PDF Manager App
1. Enter your search query
2. Click "🎯 Search Filters" to expand options
3. Adjust settings:
   - **Number of Results**: Slide to set max documents (1-50)
   - **Minimum Similarity Score**: Set relevance threshold (0.0-1.0)
   - **Category**: Filter by document category
   - **Exact Search**: Toggle for precision vs speed
4. Click "🔍 Search" to execute

### Upload App
1. Search settings are in the sidebar
2. Adjust before searching:
   - **Maximum Results**: 1-50 documents
   - **Score Threshold**: 0.0-1.0 relevance filter
   - **Document Source**: all/pubmed/uploaded
   - **Exact Search Mode**: On/Off
3. Enter query and click "🚀 Search"

## Understanding Similarity Scores

The similarity score indicates how closely a document matches your query:

| Score Range | Indicator | Meaning |
|------------|-----------|----------|
| 0.8 - 1.0 | 🟢 | Highly relevant - strong match |
| 0.5 - 0.8 | 🟡 | Moderately relevant - decent match |
| 0.0 - 0.5 | 🔴 | Low relevance - weak match |

## Tips for Better Searches

1. **Start broad**: Begin with score threshold at 0.0 to see all results
2. **Refine gradually**: Increase threshold if too many irrelevant results
3. **Use exact search**: When looking for specific technical terms or phrases
4. **Adjust result count**: More results for exploratory searches, fewer for focused queries
5. **Combine filters**: Use category/source filters with score threshold for precision

## Example Use Cases

### Finding Highly Relevant Documents
- Set similarity score to 0.7+
- Limit results to 5-10
- Use exact search for technical queries

### Exploratory Research
- Keep score threshold at 0.0
- Set results to 20-30
- Use fast search mode
- Review score distribution

### Specific Document Lookup
- Use exact search mode
- Set high similarity threshold (0.8+)
- Limit to 3-5 results
- Add category/source filters

## Running the Apps

```bash
# PDF Manager App (separate PDF collection)
uv run streamlit run apps/pdf_manager_app.py

# Upload + PubMed App (mixed collection)
uv run streamlit run apps/streamlit_upload_app.py
```

Both apps now provide full control over search precision and result quantity!