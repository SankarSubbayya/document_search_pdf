# Document Cleaning Guide

## Overview

Document cleaning removes non-essential sections from documents before chunking and indexing. This improves:
- **Retrieval Quality**: No irrelevant content in search results
- **Storage Efficiency**: Smaller index size
- **Processing Speed**: Fewer chunks to process

---

## What Gets Removed

✅ **Table of Contents**
- "Table of Contents", "Contents", "TOC"
- Chapter/section listings with page numbers
- Lists of figures, tables, illustrations

✅ **Acknowledgements**
- "Acknowledgements", "Acknowledgments"
- "Thanks", "Special Thanks"
- Funding statements

❓ **References** (Optional, usually kept)
- "References", "Bibliography"
- "Works Cited", "Citations"

❓ **Appendices** (Optional, usually kept)
- "Appendix A/B/C"
- Supplementary materials

✅ **Headers/Footers**
- Page numbers
- Running headers
- Document footers

---

## Quick Start

### Option 1: Automatic (Integrated)

Document cleaning is **automatically enabled** in the `DocumentProcessor`:

```python
from src.processing.document_processor import DocumentProcessor

# Create processor (cleaning enabled by default)
processor = DocumentProcessor(
    clean_documents=True,          # Enable cleaning
    remove_toc=True,               # Remove TOC
    remove_acknowledgements=True,  # Remove acknowledgements
    remove_references=False        # Keep references
)

# Process document - cleaning happens automatically
doc = processor.process_document("research_paper.pdf")

# Check what was removed
if 'sections_removed' in doc.metadata:
    print(f"Removed: {doc.metadata['sections_removed']}")
    print(f"Content reduced: {doc.metadata['content_removed_pct']}%")
```

### Option 2: Manual Cleaning

For more control, clean text manually:

```python
from src.processing.document_cleaner import clean_document

# Read document
with open('document.txt', 'r') as f:
    text = f.read()

# Clean it
cleaned_text, stats = clean_document(
    text,
    remove_toc=True,
    remove_acknowledgements=True,
    remove_references=False,
    smart_cleaning=True,
    verbose=True
)

print(f"Original: {stats.original_length} chars")
print(f"Cleaned: {stats.cleaned_length} chars")
print(f"Removed: {stats.reduction_percentage:.1f}%")
print(f"Sections: {stats.sections_removed}")
```

---

## Configuration

### In `config.yaml`

```yaml
processing:
  cleaning:
    enabled: true                      # Enable/disable cleaning
    remove_toc: true                   # Remove table of contents
    remove_acknowledgements: true      # Remove acknowledgements
    remove_references: false           # Keep references
    remove_appendices: false           # Keep appendices
    smart_cleaning: true               # Use smart detection
```

---

## Cleaning Strategies

### Basic Cleaning
Uses regex patterns to match section headers:

```python
from src.processing.document_cleaner import DocumentCleaner

cleaner = DocumentCleaner(
    remove_toc=True,
    remove_acknowledgements=True,
    remove_references=False
)

cleaned_text, stats = cleaner.clean(text)
```

**Pros**: Fast, simple  
**Cons**: May miss variations

### Smart Cleaning (Recommended)
Uses enhanced detection with context analysis:

```python
from src.processing.document_cleaner import SmartDocumentCleaner

cleaner = SmartDocumentCleaner(
    remove_toc=True,
    remove_acknowledgements=True,
    remove_references=False
)

cleaned_text, stats = cleaner.clean(text, verbose=True)
```

**Pros**: Better detection, handles variations  
**Cons**: Slightly slower

---

## Examples

### Example 1: Clean PDF Before Chunking

```python
from src.processing.pdf_processor import PDFProcessor
from src.processing.document_cleaner import clean_document
from src.processing.advanced_chunking import UnifiedChunker, ChunkingStrategy

# Step 1: Extract PDF text
pdf_processor = PDFProcessor()
pdf_content = pdf_processor.process_pdf("research_paper.pdf")

# Step 2: Clean the text
cleaned_text, stats = clean_document(
    pdf_content.text,
    remove_toc=True,
    remove_acknowledgements=True,
    verbose=True
)

print(f"Removed {stats.reduction_percentage:.1f}% of content")
print(f"Sections removed: {stats.sections_removed}")

# Step 3: Chunk the cleaned text
chunker = UnifiedChunker(strategy=ChunkingStrategy.CONTEXT)
chunks = chunker.chunk(cleaned_text)

print(f"Created {len(chunks)} chunks from cleaned document")
```

### Example 2: Detect Sections First

```python
from src.processing.document_cleaner import DocumentCleaner

cleaner = DocumentCleaner()
sections = cleaner.detect_sections(text)

print("Found sections:")
for section_name, line_numbers in sections.items():
    print(f"  {section_name}: line(s) {line_numbers}")

# Now decide what to remove
if 'Table of Contents' in sections:
    print("TOC detected - will remove")
```

### Example 3: Custom Configuration

```python
from src.processing.document_cleaner import DocumentCleaner

# Custom cleaner for academic papers
cleaner = DocumentCleaner(
    remove_toc=True,
    remove_acknowledgements=True,
    remove_references=False,    # Keep references (important for academic papers)
    remove_appendices=False,    # Keep appendices
    remove_headers_footers=True,
    min_section_lines=5         # Larger sections only
)

cleaned_text, stats = cleaner.clean(document_text, verbose=True)
```

---

## Patterns Recognized

### Table of Contents Patterns

- "Table of Contents"
- "Contents"
- "TOC"
- Lines with dots and page numbers: `Chapter 1 ........... 5`
- "List of Figures", "List of Tables"

### Acknowledgements Patterns

- "Acknowledgements" / "Acknowledgments"
- "Thanks"
- Common phrases:
  - "would like to thank"
  - "grateful to"
  - "special thanks"
  - "like to acknowledge"

### References Patterns

- "References"
- "Bibliography"
- "Works Cited"
- "Citations"

### Appendix Patterns

- "Appendix A", "Appendix B", etc.
- "Appendices"

---

## Detection Logic

### Smart TOC Detection

The smart cleaner looks for:
1. Section header matching TOC patterns
2. Lines with dots leading to page numbers
3. Chapter/section listings
4. Stops when consecutive non-TOC lines found

### Smart Acknowledgements Detection

Looks for:
1. Section header matching acknowledgement patterns
2. Common phrases like "would like to thank"
3. Stops at next major section or after 1-2 paragraphs

---

## Statistics and Monitoring

```python
cleaned_text, stats = clean_document(text, verbose=True)

# Access statistics
print(f"Original length: {stats.original_length}")
print(f"Cleaned length: {stats.cleaned_length}")
print(f"Reduction: {stats.reduction_percentage:.1f}%")
print(f"Sections removed: {', '.join(stats.sections_removed)}")
print(f"Lines removed: {stats.lines_removed}")
```

---

## Best Practices

### 1. **Always Enable for Academic Papers**
```yaml
cleaning:
  enabled: true
  remove_toc: true
  remove_acknowledgements: true
  remove_references: false  # Keep references
```

### 2. **Be Careful with References**
References are often important context:
- For academic work: **Keep** them
- For technical docs: **Keep** them
- For general documents: Can remove

### 3. **Test Before Production**
```python
# Test on a few documents first
cleaner = SmartDocumentCleaner()
cleaned, stats = cleaner.clean(test_doc, verbose=True)

# Review what was removed
print(f"Removed: {stats.sections_removed}")
print(f"Percentage: {stats.reduction_percentage:.1f}%")

# Manually verify cleaned text looks good
```

### 4. **Monitor Cleaning Stats**
```python
# Log cleaning statistics
if 'sections_removed' in metadata:
    logger.info(f"Document cleaned: {metadata['sections_removed']}")
    logger.info(f"Content reduced: {metadata['content_removed_pct']}%")
```

---

## Integration with Existing Pipeline

### With DocumentProcessor (Automatic)

```python
from src.processing.document_processor import DocumentProcessor

processor = DocumentProcessor(
    clean_documents=True,  # Enable cleaning
    remove_toc=True,
    remove_acknowledgements=True,
    chunk_size=512
)

# Cleaning happens automatically during processing
doc = processor.process_document("paper.pdf")
```

### With Processing Script

```python
python scripts/process_with_advanced_chunking.py \
    --strategy context \
    --input /path/to/pdfs \
    --collection clean_documents
```

Cleaning is automatically enabled based on config.yaml settings.

---

## Troubleshooting

### Issue: TOC Not Detected

**Solution**: Use smart cleaning
```python
from src.processing.document_cleaner import SmartDocumentCleaner

cleaner = SmartDocumentCleaner()  # Better detection
cleaned_text, stats = cleaner.clean(text)
```

### Issue: Too Much Content Removed

**Solution**: Check what was removed
```python
sections = cleaner.detect_sections(text)
print(f"Will remove: {list(sections.keys())}")

# Disable specific cleaners if needed
cleaner = DocumentCleaner(
    remove_toc=True,
    remove_acknowledgements=False,  # Keep acknowledgements
    remove_references=False
)
```

### Issue: Important Content Removed

**Solution**: Adjust patterns or disable cleaning
```python
# Option 1: Disable for specific document types
if document_type == 'report':
    processor = DocumentProcessor(clean_documents=False)

# Option 2: Keep more sections
cleaner = DocumentCleaner(
    remove_toc=True,
    remove_acknowledgements=False,
    remove_references=False,
    remove_appendices=False
)
```

---

## Examples to Run

```bash
# Run the demo
python examples/document_cleaning_example.py

# Test on your documents
python -c "
from src.processing.document_processor import DocumentProcessor
processor = DocumentProcessor(clean_documents=True)
doc = processor.process_document('your_file.pdf')
print(f'Removed: {doc.metadata.get(\"sections_removed\", [])}')
"
```

---

## Summary

✅ **Automatic Cleaning**: Enabled by default in DocumentProcessor  
✅ **Smart Detection**: Uses enhanced patterns and context  
✅ **Configurable**: Control what gets removed  
✅ **Statistics**: Monitor what was cleaned  
✅ **Production Ready**: Integrated into your pipeline  

**Result**: Cleaner documents → Better retrieval → Happier users! 🎉


