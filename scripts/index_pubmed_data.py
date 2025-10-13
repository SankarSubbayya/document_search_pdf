#!/usr/bin/env python3
"""
Index processed PubMed 200k RCT data into Qdrant vector database.

This script reads the processed JSONL file and indexes documents into Qdrant
with embeddings generated using sentence-transformers.
"""

import json
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from tqdm import tqdm
import numpy as np
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchParams
)
from sentence_transformers import SentenceTransformer
import yaml

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PubMedIndexer:
    """Index PubMed documents into Qdrant vector database."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "documents",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        batch_size: int = 100
    ):
        """
        Initialize the indexer.

        Args:
            host: Qdrant host
            port: Qdrant port
            collection_name: Name of the collection to use
            embedding_model: Name of the sentence transformer model
            batch_size: Batch size for processing
        """
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
        self.batch_size = batch_size

        # Load embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embedder = SentenceTransformer(embedding_model)
        self.vector_size = self.embedder.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self.vector_size}")

    def ensure_collection(self, recreate: bool = False):
        """
        Ensure the collection exists with proper configuration.

        Args:
            recreate: Whether to recreate the collection if it exists
        """
        collections = self.client.get_collections()
        exists = any(c.name == self.collection_name for c in collections.collections)

        if exists:
            if recreate:
                logger.info(f"Recreating collection '{self.collection_name}'")
                self.client.delete_collection(self.collection_name)
            else:
                logger.info(f"Using existing collection '{self.collection_name}'")
                return

        # Create collection with optimized settings for search
        logger.info(f"Creating collection '{self.collection_name}'")
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.vector_size,
                distance=Distance.COSINE,
                on_disk=False  # Keep in memory for faster search
            )
        )
        logger.info(f"Collection '{self.collection_name}' created successfully")

    def load_documents(self, jsonl_path: Path, max_documents: Optional[int] = None) -> List[Dict]:
        """
        Load documents from JSONL file.

        Args:
            jsonl_path: Path to the JSONL file
            max_documents: Maximum number of documents to load

        Returns:
            List of document dictionaries
        """
        documents = []

        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if max_documents and i >= max_documents:
                    break

                try:
                    doc = json.loads(line)
                    documents.append(doc)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse line {i+1}: {e}")

        logger.info(f"Loaded {len(documents)} documents from {jsonl_path}")
        return documents

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings

        Returns:
            Numpy array of embeddings
        """
        embeddings = self.embedder.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True  # Normalize for cosine similarity
        )
        return embeddings

    def index_documents(
        self,
        documents: List[Dict],
        start_id: int = 0,
        show_progress: bool = True
    ) -> int:
        """
        Index documents into Qdrant.

        Args:
            documents: List of document dictionaries
            start_id: Starting ID for points
            show_progress: Whether to show progress bar

        Returns:
            Number of documents indexed
        """
        total_indexed = 0
        points_buffer = []

        # Process in batches
        progress_bar = tqdm(
            range(0, len(documents), self.batch_size),
            desc="Indexing documents",
            disable=not show_progress
        )

        for batch_start in progress_bar:
            batch_end = min(batch_start + self.batch_size, len(documents))
            batch_docs = documents[batch_start:batch_end]

            # Extract texts for embedding
            texts = [doc.get('content', '') for doc in batch_docs]

            # Generate embeddings
            embeddings = self.generate_embeddings(texts)

            # Create points
            for i, (doc, embedding) in enumerate(zip(batch_docs, embeddings)):
                point_id = start_id + batch_start + i

                # Prepare payload
                payload = {
                    'document_id': doc.get('id', f'doc_{point_id}'),
                    'source': doc.get('source', 'unknown'),
                    'content': doc.get('content', ''),
                    'indexed_at': datetime.now().isoformat()
                }

                # Add metadata fields
                if 'metadata' in doc:
                    metadata = doc['metadata']
                    payload['split'] = metadata.get('split', 'unknown')
                    payload['abstract_id'] = metadata.get('abstract_id', '')
                    payload['num_sentences'] = metadata.get('num_sentences', 0)
                    payload['labels'] = metadata.get('labels', [])

                    # Add section fields for filtering
                    for key, value in metadata.items():
                        if key.startswith('section_'):
                            payload[key] = value

                points_buffer.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding.tolist(),
                        payload=payload
                    )
                )

            # Upload points when buffer is full
            if len(points_buffer) >= self.batch_size:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points_buffer,
                    wait=True
                )
                total_indexed += len(points_buffer)
                points_buffer = []

                progress_bar.set_postfix({'indexed': total_indexed})

        # Upload remaining points
        if points_buffer:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points_buffer,
                wait=True
            )
            total_indexed += len(points_buffer)

        logger.info(f"Successfully indexed {total_indexed} documents")
        return total_indexed

    def search(
        self,
        query: str,
        limit: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar documents.

        Args:
            query: Search query
            limit: Number of results to return
            filter_dict: Optional filters

        Returns:
            List of search results
        """
        # Generate query embedding
        query_embedding = self.generate_embeddings([query])[0]

        # Build filter if provided
        query_filter = None
        if filter_dict:
            conditions = []
            for key, value in filter_dict.items():
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
            query_filter = Filter(must=conditions)

        # Search
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding.tolist(),
            limit=limit,
            query_filter=query_filter,
            with_payload=True,
            search_params=SearchParams(
                hnsw_ef=128,  # Higher ef = more accurate but slower
                exact=False   # Use approximate search
            )
        ).points

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'id': result.id,
                'score': result.score,
                'document_id': result.payload.get('document_id'),
                'abstract_id': result.payload.get('abstract_id'),
                'content': result.payload.get('content', '')[:500],  # First 500 chars
                'labels': result.payload.get('labels', []),
                'source': result.payload.get('source')
            })

        return formatted_results

    def get_collection_info(self):
        """Get information about the collection."""
        info = self.client.get_collection(self.collection_name)
        return {
            'name': self.collection_name,
            'vectors_count': info.vectors_count,
            'points_count': info.points_count,
            'status': info.status,
            'vector_size': self.vector_size
        }


def main():
    """Main function to index PubMed data."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Index PubMed 200k RCT data into Qdrant"
    )
    parser.add_argument(
        '--input',
        type=Path,
        default=Path('/Users/sankar/sankar/courses/llm/data/pubmed/processed/pubmed_200k_rct_processed.jsonl'),
        help='Path to processed JSONL file'
    )
    parser.add_argument(
        '--host',
        default='localhost',
        help='Qdrant host'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=6333,
        help='Qdrant port'
    )
    parser.add_argument(
        '--collection',
        default='pubmed_documents',
        help='Collection name'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for indexing'
    )
    parser.add_argument(
        '--max-documents',
        type=int,
        help='Maximum number of documents to index'
    )
    parser.add_argument(
        '--recreate',
        action='store_true',
        help='Recreate collection if it exists'
    )
    parser.add_argument(
        '--search',
        help='Test search after indexing'
    )

    args = parser.parse_args()

    # Check if input file exists
    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    print("\n" + "="*60)
    print("PubMed Data Indexer for Qdrant")
    print("="*60)
    print(f"Input file: {args.input}")
    print(f"Qdrant: {args.host}:{args.port}")
    print(f"Collection: {args.collection}")
    print("="*60)

    # Create indexer
    indexer = PubMedIndexer(
        host=args.host,
        port=args.port,
        collection_name=args.collection,
        batch_size=args.batch_size
    )

    # Ensure collection exists
    indexer.ensure_collection(recreate=args.recreate)

    # Load documents
    print("\nLoading documents...")
    documents = indexer.load_documents(args.input, max_documents=args.max_documents)

    if not documents:
        logger.error("No documents to index")
        sys.exit(1)

    # Index documents
    print(f"\nIndexing {len(documents)} documents...")
    start_time = datetime.now()

    num_indexed = indexer.index_documents(documents, show_progress=True)

    elapsed_time = (datetime.now() - start_time).total_seconds()
    docs_per_sec = num_indexed / elapsed_time if elapsed_time > 0 else 0

    # Get collection info
    info = indexer.get_collection_info()

    print("\n" + "="*60)
    print("Indexing Complete!")
    print("="*60)
    print(f"Documents indexed: {num_indexed}")
    print(f"Time elapsed: {elapsed_time:.2f} seconds")
    print(f"Speed: {docs_per_sec:.1f} docs/second")
    print(f"Collection points: {info['points_count']}")
    print(f"Collection status: {info['status']}")
    print("="*60)

    # Test search if requested
    if args.search:
        print(f"\nTesting search with query: '{args.search}'")
        print("-"*40)

        results = indexer.search(args.search, limit=3)

        for i, result in enumerate(results, 1):
            print(f"\n{i}. Score: {result['score']:.4f}")
            print(f"   Abstract ID: {result['abstract_id']}")
            print(f"   Labels: {', '.join(result['labels'])}")
            print(f"   Content: {result['content'][:200]}...")

        print("\n" + "="*60)

    print("\nNext steps:")
    print("1. View collection in Qdrant dashboard: http://localhost:6333/dashboard")
    print(f"2. Search documents: python scripts/index_pubmed_data.py --search 'your query'")
    print("3. Use the RAG system: python main.py search 'your query'")
    print("="*60)


if __name__ == "__main__":
    main()