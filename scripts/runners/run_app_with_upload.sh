#!/bin/bash

# Run the enhanced Streamlit app with PDF upload functionality

echo "Starting Document Search App with PDF Upload..."
echo "==========================================="
echo ""

# Check if Qdrant is running
echo "Checking Qdrant connection..."
nc -zv localhost 6333 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Qdrant doesn't seem to be running on localhost:6333"
    echo "Please start Qdrant first with: docker run -p 6333:6333 qdrant/qdrant"
    echo ""
fi

# Check for required Python packages
echo "Checking required packages..."
python -c "import streamlit" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required packages..."
    pip install streamlit sentence-transformers qdrant-client pandas plotly \
                PyPDF2 pdfplumber pypdf pdf2image pytesseract pillow
fi

# Run the enhanced app
echo ""
echo "Starting Streamlit app..."
echo "The app will open in your browser automatically."
echo "If not, navigate to http://localhost:8501"
echo ""
echo "Features:"
echo "  📤 Upload PDF files for indexing"
echo "  🔍 Search across uploaded and existing documents"
echo "  📊 View search analytics and statistics"
echo "  🎯 Filter by document source (uploaded/PubMed)"
echo ""
echo "Press Ctrl+C to stop the server"
echo "==========================================="
echo ""

streamlit run app_with_upload.py