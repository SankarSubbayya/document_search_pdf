#!/bin/bash

# Script to run the Streamlit PubMed Search application

echo "=================================================="
echo "     PubMed Semantic Search Application"
echo "=================================================="
echo ""

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    echo "   Run: open -a Docker"
    exit 1
fi

# Check if Qdrant is running
if ! docker ps | grep -q qdrant; then
    echo "⚠️  Qdrant container is not running."
    echo "Starting Qdrant..."
    docker-compose up -d qdrant

    # Wait for Qdrant to be ready
    echo "Waiting for Qdrant to be ready..."
    sleep 5

    # Check health
    max_attempts=30
    attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f http://localhost:6333/health > /dev/null 2>&1; then
            echo "✅ Qdrant is ready!"
            break
        fi

        attempt=$((attempt + 1))
        if [ $attempt -eq $max_attempts ]; then
            echo "❌ Qdrant failed to start properly."
            exit 1
        fi

        echo -n "."
        sleep 1
    done
else
    echo "✅ Qdrant is already running"
fi

# Check if collection exists
echo ""
echo "Checking Qdrant collection..."
collection_exists=$(curl -s http://localhost:6333/collections | python3 -c "
import sys, json
data = json.load(sys.stdin)
collections = data.get('result', {}).get('collections', [])
print('yes' if any(c['name'] == 'pubmed_documents' for c in collections) else 'no')
" 2>/dev/null)

if [ "$collection_exists" = "no" ]; then
    echo "⚠️  Collection 'pubmed_documents' not found."
    echo ""
    echo "Would you like to index some sample documents? (y/n)"
    read -r response

    if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
        echo "Indexing 1000 sample documents..."
        uv run python scripts/index_pubmed_data.py --max-documents 1000
    else
        echo "Please index documents first using:"
        echo "  uv run python scripts/index_pubmed_data.py --max-documents 1000"
        exit 1
    fi
else
    # Get document count
    doc_count=$(curl -s http://localhost:6333/collections/pubmed_documents | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('result', {}).get('points_count', 0))
" 2>/dev/null)

    echo "✅ Collection found with $doc_count documents"
fi

# Install dependencies if needed
echo ""
echo "Checking dependencies..."
if ! uv pip list 2>/dev/null | grep -q streamlit; then
    echo "Installing Streamlit and dependencies..."
    uv pip install streamlit plotly
fi

# Launch Streamlit
echo ""
echo "=================================================="
echo "     Launching Streamlit Application"
echo "=================================================="
echo ""
echo "The app will open in your browser automatically."
echo "If not, navigate to: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the application"
echo "=================================================="
echo ""

# Run Streamlit
uv run streamlit run app.py \
    --server.address localhost \
    --server.port 8501 \
    --browser.serverAddress localhost \
    --browser.gatherUsageStats false \
    --theme.primaryColor "#1f77b4" \
    --theme.backgroundColor "#ffffff" \
    --theme.secondaryBackgroundColor "#f0f2f6" \
    --theme.textColor "#262730"