#!/bin/bash
# Start Qdrant using Docker

echo "Starting Qdrant vector database..."

docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest

echo "✅ Qdrant started!"
echo "   - REST API: http://localhost:6333"
echo "   - gRPC API: http://localhost:6334"
echo "   - Dashboard: http://localhost:6333/dashboard"
echo ""
echo "To stop: docker stop qdrant"
echo "To remove: docker rm qdrant"

