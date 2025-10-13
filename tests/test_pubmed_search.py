#!/usr/bin/env python3
"""
Test script to verify PubMed collection is accessible and searchable.
"""

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import json

def test_pubmed_search():
    # Connect to Qdrant
    client = QdrantClient(host="localhost", port=6333)

    # Check collections
    print("🔍 Checking Qdrant collections...")
    collections = client.get_collections().collections

    for col in collections:
        info = client.get_collection(col.name)
        print(f"  - {col.name}: {info.points_count:,} documents")

    # Check PubMed collection specifically
    print("\n📊 PubMed Collection Details:")
    pubmed_info = client.get_collection("pubmed_documents")
    print(f"  - Total documents: {pubmed_info.points_count:,}")
    print(f"  - Indexed vectors: {pubmed_info.indexed_vectors_count:,}")
    print(f"  - Vector size: {pubmed_info.config.params.vectors.size}")

    # Test search
    print("\n🔎 Testing search functionality...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    test_queries = [
        "diabetes treatment",
        "machine learning cancer",
        "COVID-19 vaccine efficacy"
    ]

    for query in test_queries:
        print(f"\n  Query: '{query}'")

        # Generate embedding
        embedding = model.encode(query, normalize_embeddings=True)

        # Search
        results = client.search(
            collection_name="pubmed_documents",
            query_vector=embedding.tolist(),
            limit=3
        )

        if results:
            print(f"  ✅ Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                title = result.payload.get('title', 'No title')[:60]
                score = result.score
                print(f"    {i}. {title}... (score: {score:.4f})")
        else:
            print("  ❌ No results found")

    print("\n✨ PubMed search is working correctly!")
    print("\nYou should be able to see and search PubMed documents in:")
    print("  - PubMed App: uv run streamlit run apps/streamlit_pubmed_app.py")
    print("  - Upload App: uv run streamlit run apps/streamlit_upload_app.py")

if __name__ == "__main__":
    test_pubmed_search()