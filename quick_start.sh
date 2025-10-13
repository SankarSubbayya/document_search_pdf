#!/bin/bash

# Quick Start Script - Automatically sets up and runs the PDF Manager

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'
BOLD='\033[1m'

echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BOLD}${BLUE}   PDF Document Search - Quick Start           ${NC}"
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════${NC}\n"

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print step
print_step() {
    echo -e "\n${YELLOW}▶ $1${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. Check Python
print_step "Checking Python installation..."
if command_exists python3; then
    print_success "Python found: $(python3 --version)"
else
    print_error "Python not found. Please install Python 3.8+"
    exit 1
fi

# 2. Check/Install UV
print_step "Checking UV package manager..."
if ! command_exists uv; then
    echo "UV not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"

    if command_exists uv; then
        print_success "UV installed successfully"
    else
        echo -e "${YELLOW}UV installation failed. Falling back to pip...${NC}"
        USE_PIP=true
    fi
else
    print_success "UV found: $(uv --version)"
    USE_PIP=false
fi

# 3. Install dependencies
print_step "Installing Python dependencies..."
if [ "$USE_PIP" = true ]; then
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        print_success "Dependencies installed with pip"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
else
    uv sync
    if [ $? -eq 0 ]; then
        print_success "Dependencies installed with UV"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
fi

# 4. Check Docker and Qdrant
print_step "Checking Docker..."
if command_exists docker; then
    print_success "Docker found"

    # Check if Qdrant is running
    if docker ps | grep -q qdrant; then
        print_success "Qdrant is already running"
    else
        print_step "Starting Qdrant..."
        docker run -d -p 6333:6333 -p 6334:6334 \
            -v $(pwd)/qdrant_storage:/qdrant/storage \
            --name qdrant_local \
            qdrant/qdrant 2>/dev/null

        if [ $? -eq 0 ]; then
            print_success "Qdrant started successfully"
        else
            # Try to start existing container
            docker start qdrant_local 2>/dev/null
            if [ $? -eq 0 ]; then
                print_success "Qdrant container restarted"
            else
                print_error "Failed to start Qdrant"
                echo "You can still run the app, but vector search won't work"
            fi
        fi
    fi
else
    print_error "Docker not found. Qdrant requires Docker."
    echo "Install Docker from: https://docs.docker.com/get-docker/"
    echo ""
    echo "You can still browse the app interface, but search won't work without Qdrant"
fi

# 5. Check Streamlit
print_step "Checking Streamlit..."
if command_exists streamlit; then
    print_success "Streamlit found"
else
    if [ "$USE_PIP" = true ]; then
        pip install streamlit
    else
        uv pip install streamlit
    fi
    print_success "Streamlit installed"
fi

# 6. Display app options
echo -e "\n${BOLD}${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BOLD}Select Application to Launch:${NC}\n"
echo "  1) 📁 PDF Manager (Recommended)"
echo "     - Upload and manage your PDFs"
echo "     - Separate collection from PubMed"
echo "     - Full document management"
echo ""
echo "  2) 🔬 PubMed Search"
echo "     - Search medical literature"
echo "     - No upload capability"
echo "     - PubMed data only"
echo ""
echo "  3) 📤 Combined App"
echo "     - Upload PDFs to PubMed collection"
echo "     - Search both sources"
echo "     - Mixed collection"
echo ""
echo "  4) 🧪 Run Tests"
echo "  5) 📖 View Documentation"
echo "  6) ❌ Exit"
echo ""

read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        print_step "Starting PDF Manager App..."
        echo -e "${GREEN}Opening at: http://localhost:8501${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop${NC}\n"
        streamlit run apps/pdf_manager_app.py
        ;;
    2)
        print_step "Starting PubMed Search App..."
        echo -e "${GREEN}Opening at: http://localhost:8501${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop${NC}\n"
        streamlit run apps/streamlit_pubmed_app.py
        ;;
    3)
        print_step "Starting Combined Upload App..."
        echo -e "${GREEN}Opening at: http://localhost:8501${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop${NC}\n"
        streamlit run apps/streamlit_upload_app.py
        ;;
    4)
        print_step "Running tests..."
        if [ "$USE_PIP" = true ]; then
            python -m pytest tests/ -v
        else
            uv run pytest tests/ -v
        fi
        ;;
    5)
        echo -e "\n${BOLD}Documentation:${NC}"
        echo "  • README.md - Main documentation"
        echo "  • HOW_TO_RUN.md - Detailed run instructions"
        echo "  • PROJECT_STRUCTURE.md - File organization"
        echo "  • docs/TESTING.md - Testing guide"
        echo ""
        echo "Opening HOW_TO_RUN.md..."
        if command_exists open; then
            open HOW_TO_RUN.md
        elif command_exists xdg-open; then
            xdg-open HOW_TO_RUN.md
        else
            cat HOW_TO_RUN.md | head -50
        fi
        ;;
    6)
        echo "Exiting..."
        exit 0
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac