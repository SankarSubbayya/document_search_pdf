# Testing Guide for PDF Document Search System

## 📋 Overview

This guide covers all aspects of testing the PDF Document Search System, including unit tests, integration tests, end-to-end tests, and manual testing procedures.

## 🚀 Quick Start

### Run All Tests
```bash
./run_tests.sh
```

### Run with Coverage
```bash
./run_tests.sh --coverage
```

### Run Specific Test Types
```bash
./run_tests.sh --unit        # Unit tests only
./run_tests.sh --integration # Integration tests only
./run_tests.sh --e2e         # End-to-end tests only
```

## 🧪 Test Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── test_pdf_processor.py    # Unit tests for PDF processing
├── test_vector_operations.py # Integration tests for Qdrant
├── test_streamlit_app.py    # End-to-end tests for Streamlit
└── test_data/              # Test data and fixtures
    ├── pdfs/               # Sample PDF files
    └── outputs/            # Test outputs
```

## 📊 Test Categories

### 1. Unit Tests (`test_pdf_processor.py`)

Tests individual components in isolation:

- **PDF Processor Initialization**
  ```python
  def test_processor_initialization()
  ```
  - Verifies processor configuration
  - Tests OCR settings
  - Validates extraction options

- **Text Extraction Methods**
  ```python
  def test_extract_with_pdfplumber()
  def test_extract_with_pypdf2()
  def test_extract_with_pymupdf()
  ```
  - Tests each extraction library
  - Verifies fallback mechanisms
  - Validates content extraction

- **Scanned PDF Detection**
  ```python
  def test_is_scanned_pdf()
  ```
  - Identifies image-based PDFs
  - Tests OCR triggering logic

- **Metadata Extraction**
  ```python
  def test_extract_pdf_metadata()
  ```
  - Extracts PDF properties
  - Validates metadata structure

### 2. Integration Tests (`test_vector_operations.py`)

Tests interaction with Qdrant vector database:

- **Collection Management**
  ```python
  def test_collection_initialization()
  def test_collection_statistics()
  ```
  - Creates/initializes collections
  - Retrieves collection stats

- **Document Operations**
  ```python
  def test_document_indexing()
  def test_document_deletion()
  def test_batch_upload()
  ```
  - Indexes documents
  - Manages document lifecycle
  - Tests batch operations

- **Search Functionality**
  ```python
  def test_search_with_filters()
  def test_score_based_ranking()
  def test_empty_search_results()
  ```
  - Semantic search
  - Category/tag filtering
  - Result ranking

### 3. End-to-End Tests (`test_streamlit_app.py`)

Tests complete application workflows:

- **Upload Workflow**
  ```python
  def test_pdf_upload_flow()
  ```
  - File upload handling
  - Processing pipeline
  - Error handling

- **Search Workflow**
  ```python
  def test_search_functionality()
  ```
  - Query input
  - Result display
  - Filter application

- **UI Components**
  ```python
  def test_sidebar_configuration()
  def test_tab_navigation()
  def test_result_display()
  ```
  - Configuration options
  - Navigation elements
  - Data visualization

## 🔧 Test Fixtures

### Pytest Fixtures (conftest.py)

```python
@pytest.fixture
def sample_pdf_file()       # Creates test PDF
def mock_qdrant_client()    # Mocks Qdrant client
def mock_embedding_model()  # Mocks ML model
def mock_pdf_processor()    # Mocks PDF processor
def sample_documents()      # Sample document data
def sample_search_results() # Sample search results
```

## 🏃 Running Tests

### Basic Commands

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_pdf_processor.py

# Run specific test function
pytest tests/test_pdf_processor.py::TestPDFProcessor::test_processor_initialization

# Run tests matching pattern
pytest tests/ -k "pdf"

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run with debugging
pytest tests/ --pdb

# Run parallel (requires pytest-xdist)
pytest tests/ -n 4
```

### Using Markers

```bash
# Run only unit tests
pytest tests/ -m unit

# Run only integration tests
pytest tests/ -m integration

# Run tests that don't require Qdrant
pytest tests/ -m "not requires_qdrant"

# Run fast tests only
pytest tests/ -m "not slow"
```

## 🧪 Manual Testing

### 1. Application Launch Test

```bash
# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Run the app
streamlit run pdf_manager_app.py

# Verify:
✓ App launches without errors
✓ UI loads completely
✓ Qdrant connection successful
```

### 2. PDF Upload Test

**Test Cases:**

1. **Valid PDF Upload**
   - Upload a standard PDF
   - Verify processing completes
   - Check chunks are created

2. **Multiple PDFs**
   - Upload 3-5 PDFs simultaneously
   - Monitor progress bars
   - Verify all are indexed

3. **Large PDF**
   - Upload PDF > 10MB
   - Check memory usage
   - Verify chunking works

4. **Scanned PDF**
   - Upload image-based PDF
   - Verify OCR triggers
   - Check text extraction

5. **Corrupted PDF**
   - Upload damaged PDF
   - Verify error handling
   - Check graceful failure

### 3. Search Test

**Test Queries:**

```
1. Single word: "machine"
2. Phrase: "machine learning algorithms"
3. Question: "What is deep learning?"
4. Technical: "neural network architecture"
5. Empty query: ""
6. Special characters: "AI & ML"
```

**Verify:**
- Results relevance
- Scoring accuracy
- Response time
- Filter application

### 4. Document Management Test

1. **View Documents**
   - Navigate to Documents tab
   - Verify list displays
   - Check sorting works

2. **Delete Document**
   - Delete single document
   - Verify removal
   - Check search updates

3. **Export CSV**
   - Export document list
   - Verify CSV format
   - Check data completeness

### 5. Performance Test

```bash
# Upload multiple large PDFs
# Monitor:
- Processing time
- Memory usage
- CPU utilization
- Response times
```

## 📈 Coverage Reports

### Generate Coverage

```bash
# HTML report
pytest tests/ --cov=src --cov=pdf_manager_app --cov-report=html

# Terminal report
pytest tests/ --cov=src --cov-report=term-missing

# XML report (for CI/CD)
pytest tests/ --cov=src --cov-report=xml
```

### View Coverage

```bash
# Open HTML report
open htmlcov/index.html

# Or use Python's HTTP server
cd htmlcov && python -m http.server 8000
# Navigate to http://localhost:8000
```

### Coverage Goals

- **Target:** 80% overall coverage
- **Unit tests:** 90% coverage
- **Integration:** 70% coverage
- **Critical paths:** 100% coverage

## 🐛 Debugging Tests

### Using pytest debugger

```python
# Add breakpoint in test
def test_something():
    import pdb; pdb.set_trace()
    # Test code
```

```bash
# Run with pdb
pytest tests/ --pdb

# Drop to pdb on first failure
pytest tests/ --pdb --maxfail=1
```

### Verbose Output

```bash
# Show print statements
pytest tests/ -s

# Show detailed test output
pytest tests/ -vv

# Show local variables on failure
pytest tests/ --showlocals
```

## 🔄 Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## 🎯 Test Best Practices

### 1. Test Naming
```python
# Good
def test_pdf_extraction_with_valid_file()
def test_search_returns_relevant_results()

# Bad
def test1()
def test_function()
```

### 2. Test Independence
- Each test should be independent
- Use fixtures for setup/teardown
- Don't rely on test execution order

### 3. Mock External Dependencies
```python
@patch('qdrant_client.QdrantClient')
def test_with_mock_qdrant(mock_client):
    # Test without real Qdrant connection
```

### 4. Test Data Management
- Use fixtures for test data
- Clean up after tests
- Don't commit large test files

### 5. Assertions
```python
# Be specific
assert result.status == 'success'
assert len(results) == 10

# Not just
assert result
```

## 🚨 Common Issues

### Issue: Tests fail with ImportError

```bash
# Fix: Add parent directory to path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: Qdrant connection errors

```bash
# Fix: Mock Qdrant for unit tests
# Or start Qdrant for integration tests
docker run -p 6333:6333 qdrant/qdrant
```

### Issue: OCR tests fail

```bash
# Fix: Install Tesseract
brew install tesseract  # macOS
apt-get install tesseract-ocr  # Linux
```

### Issue: Slow tests

```bash
# Fix: Use markers to skip slow tests
pytest tests/ -m "not slow"

# Or run in parallel
pip install pytest-xdist
pytest tests/ -n auto
```

## 📝 Test Checklist

Before committing:

- [ ] All tests pass locally
- [ ] Coverage meets threshold (>80%)
- [ ] No hardcoded paths or credentials
- [ ] Tests are documented
- [ ] Clean up test files
- [ ] Update test documentation

## 🔍 Test Monitoring

### Local Testing Dashboard

```python
# Create test_monitor.py
import subprocess
import time

while True:
    result = subprocess.run(['pytest', 'tests/', '--tb=no'],
                          capture_output=True)

    if result.returncode == 0:
        print("✅ All tests passing")
    else:
        print("❌ Tests failing")

    time.sleep(60)  # Check every minute
```

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://realpython.com/pytest-python-testing/)
- [Streamlit Testing](https://docs.streamlit.io/library/advanced-features/testing)

---

**Remember:** Good tests are as important as good code. They ensure reliability, enable refactoring, and serve as documentation.