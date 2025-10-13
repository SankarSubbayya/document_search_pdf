#!/bin/bash

# Simple launcher script for all applications

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'
BOLD='\033[1m'

echo -e "${BOLD}${BLUE}PDF Document Search System${NC}"
echo "============================"
echo ""
echo "Select an application to run:"
echo ""
echo "  1) PDF Manager (Separate Collection)"
echo "  2) PubMed Search"
echo "  3) Combined Upload + PubMed Search"
echo "  4) Run Tests"
echo "  5) Start Qdrant"
echo "  6) Exit"
echo ""
read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        echo -e "${GREEN}Starting PDF Manager...${NC}"
        streamlit run apps/pdf_manager_app.py
        ;;
    2)
        echo -e "${GREEN}Starting PubMed Search...${NC}"
        streamlit run apps/streamlit_pubmed_app.py
        ;;
    3)
        echo -e "${GREEN}Starting Combined App...${NC}"
        streamlit run apps/streamlit_upload_app.py
        ;;
    4)
        echo -e "${GREEN}Running Tests...${NC}"
        ./scripts/runners/run_tests.sh
        ;;
    5)
        echo -e "${GREEN}Starting Qdrant...${NC}"
        docker run -p 6333:6333 -p 6334:6334 \
            -v $(pwd)/qdrant_storage:/qdrant/storage \
            qdrant/qdrant
        ;;
    6)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo -e "${YELLOW}Invalid choice. Please run again and select 1-6.${NC}"
        exit 1
        ;;
esac