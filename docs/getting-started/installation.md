# Installation Guide

This guide covers how to install all dependencies for the PDF Document Search System using various package managers.

## 🚀 Quick Start with UV (Recommended)

[UV](https://github.com/astral-sh/uv) is a fast Python package installer and resolver written in Rust.

### Install UV

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

### Install Dependencies with UV

```bash
# Navigate to project directory
cd /Users/sankar/sankar/courses/llm/document_search_pdf

# Install all dependencies from pyproject.toml
uv sync

# Or install specific groups
uv sync --all-extras  # Install everything including optional deps

# Install with dev dependencies
uv sync --dev

# Install with advanced PDF processing
uv sync --extra pdf-advanced
```

### Create Virtual Environment with UV

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies in the venv
uv pip sync pyproject.toml
```

## 📦 Alternative: Using pip

### Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install from requirements.txt

```bash
pip install -r requirements.txt
```

### Install from pyproject.toml

```bash
# Install package in editable mode with all dependencies
pip install -e .

# Install with optional dependencies
pip install -e ".[dev]"
pip install -e ".[pdf-advanced]"
pip install -e ".[ml-extras]"

# Install everything
pip install -e ".[dev,pdf-advanced,ml-extras,db-extras]"
```

## 🐍 Using conda/mamba

### Create Environment

```bash
# Create conda environment
conda create -n pdf-search python=3.10
conda activate pdf-search

# Install dependencies
pip install -r requirements.txt
```

## 🔧 System Dependencies

Some packages require system-level dependencies:

### macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Tesseract for OCR
brew install tesseract

# Poppler for PDF to image conversion
brew install poppler

# Optional: PyMuPDF dependencies
brew install mupdf-tools
```

### Ubuntu/Debian

```bash
# Update package list
sudo apt-get update

# Tesseract for OCR
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# Poppler for PDF to image conversion
sudo apt-get install poppler-utils

# Development dependencies for Python packages
sudo apt-get install python3-dev libpq-dev

# Optional: PyMuPDF dependencies
sudo apt-get install mupdf-tools
```

### Windows

```bash
# Using Chocolatey
choco install tesseract
choco install poppler

# Or download and install manually:
# Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
# Poppler: http://blog.alivate.com.au/poppler-windows/
```

## 🎯 Minimal Installation

If you only need the core functionality:

```bash
# Core dependencies only
pip install streamlit qdrant-client sentence-transformers \
    pandas numpy pyyaml pypdf2 pdfplumber plotly
```

## 🚨 Troubleshooting

### UV Issues

```bash
# Clear UV cache
uv cache clean

# Reinstall with verbose output
uv sync -v

# Use specific Python version
uv sync --python 3.10
```

### Missing System Dependencies

If you get errors about missing libraries:

```bash
# Check if Tesseract is installed
tesseract --version

# Check if Poppler is installed
pdftotext -v

# Install missing dependencies based on your OS (see above)
```

### Package Conflicts

```bash
# Create fresh environment
rm -rf .venv venv
uv venv
source .venv/bin/activate
uv sync

# Or with pip
python -m venv venv_fresh
source venv_fresh/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Memory Issues with Large Models

If you run out of memory when loading models:

```bash
# Set environment variable to limit model cache
export SENTENCE_TRANSFORMERS_HOME=/path/to/cache
export TRANSFORMERS_CACHE=/path/to/cache

# Limit PyTorch threads
export OMP_NUM_THREADS=4
```

## 📋 Verification

After installation, verify everything works:

```python
# Test script: verify_installation.py
import sys
print(f"Python: {sys.version}")

try:
    import streamlit
    print(f"✅ Streamlit: {streamlit.__version__}")
except ImportError:
    print("❌ Streamlit not installed")

try:
    import qdrant_client
    print(f"✅ Qdrant Client: {qdrant_client.__version__}")
except ImportError:
    print("❌ Qdrant Client not installed")

try:
    import sentence_transformers
    print(f"✅ Sentence Transformers: {sentence_transformers.__version__}")
except ImportError:
    print("❌ Sentence Transformers not installed")

try:
    import pypdf
    print(f"✅ PyPDF: {pypdf.__version__}")
except ImportError:
    print("❌ PyPDF not installed")

try:
    import pdfplumber
    print(f"✅ PDFPlumber: {pdfplumber.__version__}")
except ImportError:
    print("❌ PDFPlumber not installed")

try:
    import pytesseract
    print(f"✅ PyTesseract: {pytesseract.__version__}")
    # Test Tesseract binary
    pytesseract.get_tesseract_version()
    print("✅ Tesseract OCR binary found")
except Exception as e:
    print(f"❌ PyTesseract or Tesseract OCR issue: {e}")

print("\n✨ Run the verification: python verify_installation.py")
```

## 🎉 Ready to Run!

Once everything is installed:

```bash
# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Run the PDF Manager app
streamlit run pdf_manager_app.py

# Or use the launch script
./run_pdf_manager.sh
```

## 📦 Export Dependencies

To export current environment dependencies:

```bash
# With UV
uv pip freeze > requirements-frozen.txt

# With pip
pip freeze > requirements-frozen.txt

# Export conda environment
conda env export > environment.yml
```

## 🔄 Update Dependencies

```bash
# With UV
uv sync --upgrade

# With pip
pip install --upgrade -r requirements.txt

# Update specific package
uv pip install --upgrade streamlit
```

## 💡 Tips

1. **Use UV for speed**: UV is significantly faster than pip, especially for large dependency trees

2. **Virtual environments are crucial**: Always use a virtual environment to avoid conflicts

3. **Pin versions for production**: Use exact versions in production deployments

4. **Cache models**: Set up model caching to avoid re-downloading:
   ```bash
   export TRANSFORMERS_CACHE=~/.cache/transformers
   export SENTENCE_TRANSFORMERS_HOME=~/.cache/sentence-transformers
   ```

5. **Use Docker for consistency**: Consider using Docker for production deployments to ensure consistency across environments

## 📝 Notes

- The `pyproject.toml` file is the modern standard for Python projects
- `requirements.txt` is provided for compatibility
- UV combines the speed of Rust with Python package management
- All PDF processing libraries are included for maximum compatibility
- OCR support requires system-level Tesseract installation