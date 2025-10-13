#!/usr/bin/env python3
"""
Load PubMed 200k RCT data into Qdrant vector database.
This script creates and populates the 'pubmed_documents' collection.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import logging
from tqdm import tqdm

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_pubmed_data(
    data_file: str = "data/pubmed/processed/pubmed_200k_rct_processed.jsonl",
    host: str = "localhost",
    port: int = 6333,
    collection_name: str = "pubmed_documents",
    batch_size: int = 100,
    max_documents: int = None,
    recreate: bool = True
):
    """
    Load PubMed data into Qdrant.

    Args:
        data_file: Path to the processed JSONL file
        host: Qdrant host
        port: Qdrant port
        collection_name: Name of the collection
        batch_size: Batch size for indexing
        max_documents: Maximum number of documents to index (None for all)
        recreate: Whether to recreate the collection
    """

    # Check if data file exists
    data_path = Path(data_file)
    if not data_path.exists():
        logger.error(f"Data file not found: {data_file}")
        logger.info("Please run the data preparation script first:")
        logger.info("  python src/data/download_and_prepare.py")
        return False

    # Initialize Qdrant client
    logger.info(f"Connecting to Qdrant at {host}:{port}")
    try:
        client = QdrantClient(host=host, port=port, timeout=10)
        # Test connection
        collections = client.get_collections()
        logger.info(f"Connected! Found {len(collections.collections)} collections")
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant: {e}")
        logger.info("Please ensure Qdrant is running:")
        logger.info("  docker run -p 6333:6333 qdrant/qdrant")
        return False

    # Initialize embedding model
    logger.info("Loading embedding model...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    vector_size = model.get_sentence_embedding_dimension()
    logger.info(f"Model loaded. Embedding dimension: {vector_size}")

    # Check if collection exists
    existing_collections = [c.name for c in collections.collections]
    collection_exists = collection_name in existing_collections

    if collection_exists:
        if recreate:
            logger.info(f"Deleting existing collection: {collection_name}")
            client.delete_collection(collection_name)
        else:
            # Get existing collection info
            info = client.get_collection(collection_name)
            logger.info(f"Using existing collection: {collection_name}")
            logger.info(f"Current points: {info.points_count}")

            if info.points_count > 0:
                response = input("Collection already has data. Continue anyway? (y/n): ")
                if response.lower() != 'y':
                    logger.info("Aborted by user")
                    return False

    # Create collection if needed
    if recreate or not collection_exists:
        logger.info(f"Creating collection: {collection_name}")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )
        logger.info("Collection created successfully")

    # Load and index documents
    logger.info(f"Loading documents from: {data_file}")

    documents = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                doc = json.loads(line)
                documents.append(doc)
                if max_documents and len(documents) >= max_documents:
                    break

    logger.info(f"Loaded {len(documents)} documents")

    if not documents:
        logger.warning("No documents to index")
        return False

    # Process in batches
    logger.info(f"Indexing documents in batches of {batch_size}...")

    total_indexed = 0
    failed = 0

    with tqdm(total=len(documents), desc="Indexing") as pbar:
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]

            try:
                # Prepare texts for embedding
                texts = []
                for doc in batch:
                    # Combine title and abstract for embedding
                    title = doc.get('title', '').strip()
                    abstract = doc.get('abstract', '').strip()

                    if title and abstract:
                        text = f"{title}\n\n{abstract}"
                    elif title:
                        text = title
                    elif abstract:
                        text = abstract
                    else:
                        text = "No content available"

                    texts.append(text)

                # Generate embeddings
                embeddings = model.encode(
                    texts,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                    normalize_embeddings=True
                )

                # Create points
                points = []
                for j, (doc, embedding) in enumerate(zip(batch, embeddings)):
                    # Create point ID (using document index)
                    point_id = i + j

                    # Prepare payload
                    payload = {
                        "pmid": doc.get("pmid", ""),
                        "title": doc.get("title", ""),
                        "abstract": doc.get("abstract", ""),
                        "authors": doc.get("authors", []),
                        "journal": doc.get("journal", ""),
                        "year": doc.get("year", 0),
                        "doi": doc.get("doi", ""),
                        "pub_types": doc.get("pub_types", []),
                        "mesh_terms": doc.get("mesh_terms", []),
                        "keywords": doc.get("keywords", []),
                        "source": "pubmed",
                        "document_type": "research_article"
                    }

                    points.append(
                        PointStruct(
                            id=point_id,
                            vector=embedding.tolist(),
                            payload=payload
                        )
                    )

                # Upload to Qdrant
                client.upsert(
                    collection_name=collection_name,
                    points=points,
                    wait=True
                )

                total_indexed += len(points)
                pbar.update(len(batch))

            except Exception as e:
                logger.error(f"Error processing batch {i//batch_size}: {e}")
                failed += len(batch)
                pbar.update(len(batch))

    # Final statistics
    logger.info("\n" + "="*50)
    logger.info("Indexing Complete!")
    logger.info(f"Total documents indexed: {total_indexed}")

    if failed > 0:
        logger.warning(f"Failed documents: {failed}")

    # Verify collection
    collection_info = client.get_collection(collection_name)
    logger.info(f"Collection '{collection_name}' now has {collection_info.points_count} documents")

    # Test search
    logger.info("\nTesting search with sample query...")
    test_query = "machine learning cancer treatment"
    query_embedding = model.encode(test_query, normalize_embeddings=True)

    results = client.search(
        collection_name=collection_name,
        query_vector=query_embedding.tolist(),
        limit=3
    )

    if results:
        logger.info(f"✅ Search working! Found {len(results)} results for '{test_query}':")
        for i, result in enumerate(results, 1):
            title = result.payload.get('title', 'No title')[:80]
            logger.info(f"  {i}. {title}... (score: {result.score:.4f})")
    else:
        logger.warning("No search results found")

    logger.info("\n✨ PubMed data successfully loaded!")
    logger.info(f"You can now use the PubMed search in your Streamlit apps")
    logger.info("Run: uv run streamlit run apps/streamlit_pubmed_app.py")

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load PubMed data into Qdrant")
    parser.add_argument("--host", default="localhost", help="Qdrant host")
    parser.add_argument("--port", type=int, default=6333, help="Qdrant port")
    parser.add_argument("--collection", default="pubmed_documents", help="Collection name")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for indexing")
    parser.add_argument("--max-docs", type=int, help="Maximum documents to index (for testing)")
    parser.add_argument("--no-recreate", action="store_true", help="Don't recreate existing collection")
    parser.add_argument("--data-file", default="data/pubmed/processed/pubmed_200k_rct_processed.jsonl",
                       help="Path to processed JSONL file")

    args = parser.parse_args()

    success = load_pubmed_data(
        data_file=args.data_file,
        host=args.host,
        port=args.port,
        collection_name=args.collection,
        batch_size=args.batch_size,
        max_documents=args.max_docs,
        recreate=not args.no_recreate
    )

    sys.exit(0 if success else 1)