#!/bin/bash

# Run the Enhanced Streamlit App
# This script starts the enhanced document search app with all new features

echo "🚀 Starting Enhanced Document Search App..."
echo ""
echo "New Features:"
echo "  ✅ Document Cleaning (remove TOC, acknowledgements)"
echo "  ✅ Advanced Chunking (Semantic, Context, Late, Markup)"
echo "  ✅ Hybrid Strategies (Semantic+Late, Markup+Context)"
echo "  ✅ Statistics & Visualizations"
echo ""

# Check if Qdrant is running
echo "🔍 Checking Qdrant connection..."
if ! curl -s http://localhost:6333/collections > /dev/null 2>&1; then
    echo "⚠️  Qdrant not running! Starting Qdrant..."
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d qdrant
    else
        echo "❌ Please start Qdrant manually:"
        echo "   docker-compose up -d qdrant"
        echo ""
        echo "Or install docker-compose first."
        exit 1
    fi
    echo "⏳ Waiting for Qdrant to start..."
    sleep 3
fi

echo "✅ Qdrant is running!"
echo ""

# Run the app
echo "🎯 Launching Streamlit app..."
echo "📍 App will open at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Run with uv if available, otherwise use python
if command -v uv &> /dev/null; then
    uv run streamlit run apps/streamlit_upload_app_enhanced.py
else
    python3 -m streamlit run apps/streamlit_upload_app_enhanced.py
fi


