#!/bin/bash

# Run the PDF Document Manager Application

echo "╔══════════════════════════════════════════════╗"
echo "║     PDF Document Management System           ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Qdrant is running
echo -e "${YELLOW}Checking Qdrant connection...${NC}"
nc -zv localhost 6333 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}⚠️  Warning: Qdrant is not running on localhost:6333${NC}"
    echo ""
    echo "To start Qdrant, run:"
    echo -e "${GREEN}docker run -p 6333:6333 -p 6334:6334 -v \$(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant${NC}"
    echo ""
    read -p "Do you want to continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ Qdrant is running${NC}"
fi

# Create necessary directories
echo -e "${YELLOW}Setting up directories...${NC}"
mkdir -p data/pdf_uploads
mkdir -p data/pdf_backups
mkdir -p logs
echo -e "${GREEN}✅ Directories ready${NC}"

# Check for required Python packages
echo -e "${YELLOW}Checking dependencies...${NC}"

# Function to check if a Python package is installed
check_package() {
    python -c "import $1" 2>/dev/null
    return $?
}

# List of required packages
REQUIRED_PACKAGES=(
    "streamlit"
    "sentence_transformers"
    "qdrant_client"
    "pandas"
    "plotly"
    "PyPDF2"
    "pdfplumber"
    "pypdf"
    "pdf2image"
    "pytesseract"
    "PIL"
)

MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    # Handle special cases for package names
    if [[ "$package" == "sentence_transformers" ]]; then
        check_package "sentence_transformers"
    elif [[ "$package" == "qdrant_client" ]]; then
        check_package "qdrant_client"
    elif [[ "$package" == "PIL" ]]; then
        check_package "PIL"
    else
        check_package "$package"
    fi

    if [ $? -ne 0 ]; then
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo -e "${YELLOW}Missing packages detected: ${MISSING_PACKAGES[*]}${NC}"
    echo "Installing required packages..."
    pip install streamlit sentence-transformers qdrant-client pandas plotly \
                PyPDF2 pdfplumber pypdf pdf2image pytesseract pillow

    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install some packages. Please install manually.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ All dependencies installed${NC}"
fi

# Check for Tesseract OCR
echo -e "${YELLOW}Checking Tesseract OCR...${NC}"
if command -v tesseract &> /dev/null; then
    echo -e "${GREEN}✅ Tesseract OCR found${NC}"
else
    echo -e "${YELLOW}⚠️  Tesseract OCR not found. OCR features will be disabled.${NC}"
    echo "To install Tesseract:"
    echo "  Mac: brew install tesseract"
    echo "  Ubuntu: sudo apt-get install tesseract-ocr"
fi

# Display app information
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║              Starting Application             ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "🚀 Features:"
echo "  • Dedicated PDF document collection (separate from PubMed)"
echo "  • Upload and index multiple PDFs"
echo "  • Advanced search with filters"
echo "  • Document management (view, delete)"
echo "  • Categories and tags for organization"
echo "  • Analytics and statistics"
echo "  • Export document list to CSV"
echo ""
echo "📁 Collection: 'pdf_documents' (separate from PubMed data)"
echo ""
echo "🌐 The app will open in your browser automatically."
echo "   If not, navigate to: http://localhost:8501"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""
echo "══════════════════════════════════════════════"
echo ""

# Run the Streamlit app
streamlit run pdf_manager_app.py \
    --server.maxUploadSize=100 \
    --server.enableCORS=true \
    --server.enableXsrfProtection=true