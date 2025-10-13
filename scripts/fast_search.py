#!/usr/bin/env python3
"""
Fast search script for Qdrant with performance monitoring.

This script optimizes search performance by:
1. Loading the embedding model once and keeping it in memory
2. Measuring time for each operation
3. Using optimized search parameters
"""

import time
import sys
from pathlib import Path
from typing import List, Optional, Dict
import json

from qdrant_client import QdrantClient
from qdrant_client.models import SearchParams
from sentence_transformers import SentenceTransformer
import numpy as np

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


class FastSearcher:
    """Optimized searcher for Qdrant with performance monitoring."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "pubmed_documents",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        cache_embeddings: bool = True
    ):
        """Initialize the fast searcher."""
        print(f"Initializing FastSearcher...")

        # Time client initialization
        start = time.time()
        self.client = QdrantClient(host=host, port=port, timeout=5.0)
        self.collection_name = collection_name
        print(f"  ✓ Qdrant client initialized: {time.time() - start:.3f}s")

        # Time model loading
        start = time.time()
        print(f"  Loading embedding model: {embedding_model}")
        self.embedder = SentenceTransformer(embedding_model)
        # Set to eval mode and optimize
        self.embedder.eval()
        print(f"  ✓ Model loaded: {time.time() - start:.3f}s")

        # Cache for embeddings if enabled
        self.cache_embeddings = cache_embeddings
        self.embedding_cache = {} if cache_embeddings else None

        # Get collection info
        start = time.time()
        info = self.client.get_collection(collection_name)
        self.collection_size = info.points_count
        print(f"  ✓ Collection info retrieved: {time.time() - start:.3f}s")
        print(f"  Collection has {self.collection_size:,} documents")
        print()

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text with caching."""
        # Check cache first
        if self.cache_embeddings and text in self.embedding_cache:
            return self.embedding_cache[text]

        # Generate embedding
        start = time.time()
        embedding = self.embedder.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        elapsed = time.time() - start

        # Cache if enabled
        if self.cache_embeddings:
            self.embedding_cache[text] = embedding

        return embedding, elapsed

    def search(
        self,
        query: str,
        limit: int = 5,
        score_threshold: Optional[float] = None,
        exact: bool = False
    ) -> Dict:
        """
        Perform optimized search with timing information.

        Args:
            query: Search query
            limit: Number of results
            score_threshold: Minimum score threshold
            exact: Whether to use exact search (slower but more accurate)

        Returns:
            Dictionary with results and timing information
        """
        timing = {}

        # Generate query embedding
        embedding_result = self.generate_embedding(query)
        if isinstance(embedding_result, tuple):
            query_embedding, embedding_time = embedding_result
            timing['embedding'] = embedding_time
        else:
            query_embedding = embedding_result
            timing['embedding'] = 0.0

        # Perform Qdrant search
        start = time.time()

        # Use optimized search params
        search_params = SearchParams(
            hnsw_ef=64 if not exact else 128,  # Lower ef for faster search
            exact=exact
        )

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding.tolist(),
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True,
            search_params=search_params
        ).points

        timing['qdrant_search'] = time.time() - start
        timing['total'] = timing['embedding'] + timing['qdrant_search']

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'score': result.score,
                'abstract_id': result.payload.get('abstract_id', 'unknown'),
                'content': result.payload.get('content', '')[:500],
                'labels': result.payload.get('labels', []),
                'source': result.payload.get('source', 'unknown')
            })

        return {
            'results': formatted_results,
            'timing': timing,
            'count': len(formatted_results)
        }

    def benchmark_search(self, query: str, num_iterations: int = 5):
        """Benchmark search performance over multiple iterations."""
        print(f"Benchmarking search for: '{query}'")
        print(f"Running {num_iterations} iterations...")
        print("-" * 50)

        timings = []

        for i in range(num_iterations):
            result = self.search(query, limit=5)
            timings.append(result['timing'])

            print(f"Iteration {i+1}:")
            print(f"  Embedding: {result['timing']['embedding']:.3f}s")
            print(f"  Qdrant:    {result['timing']['qdrant_search']:.3f}s")
            print(f"  Total:     {result['timing']['total']:.3f}s")

        # Calculate statistics
        avg_embedding = np.mean([t['embedding'] for t in timings])
        avg_qdrant = np.mean([t['qdrant_search'] for t in timings])
        avg_total = np.mean([t['total'] for t in timings])

        print("-" * 50)
        print("Average times:")
        print(f"  Embedding: {avg_embedding:.3f}s")
        print(f"  Qdrant:    {avg_qdrant:.3f}s")
        print(f"  Total:     {avg_total:.3f}s")

        if self.cache_embeddings:
            # Run one more time to show cached performance
            print("\nWith cached embedding:")
            result = self.search(query, limit=5)
            print(f"  Embedding: {result['timing']['embedding']:.3f}s (cached)")
            print(f"  Qdrant:    {result['timing']['qdrant_search']:.3f}s")
            print(f"  Total:     {result['timing']['total']:.3f}s")


def main():
    """Main function for fast search."""
    import argparse

    parser = argparse.ArgumentParser(description="Fast search in Qdrant")
    parser.add_argument('query', nargs='?', help='Search query')
    parser.add_argument('--limit', type=int, default=5, help='Number of results')
    parser.add_argument('--host', default='localhost', help='Qdrant host')
    parser.add_argument('--port', type=int, default=6333, help='Qdrant port')
    parser.add_argument('--collection', default='pubmed_documents', help='Collection name')
    parser.add_argument('--benchmark', action='store_true', help='Run benchmark')
    parser.add_argument('--exact', action='store_true', help='Use exact search')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')

    args = parser.parse_args()

    # Initialize searcher
    searcher = FastSearcher(
        host=args.host,
        port=args.port,
        collection_name=args.collection
    )

    if args.benchmark and args.query:
        # Run benchmark
        searcher.benchmark_search(args.query, num_iterations=5)

    elif args.interactive:
        # Interactive mode
        print("Interactive Search Mode (type 'quit' to exit)")
        print("=" * 50)

        while True:
            try:
                query = input("\nSearch query: ").strip()
                if query.lower() in ['quit', 'exit', 'q']:
                    break

                if not query:
                    continue

                # Search with timing
                result = searcher.search(query, limit=args.limit, exact=args.exact)

                # Show timing
                print(f"\nTiming:")
                print(f"  Embedding: {result['timing']['embedding']:.3f}s")
                print(f"  Qdrant:    {result['timing']['qdrant_search']:.3f}s")
                print(f"  Total:     {result['timing']['total']:.3f}s")

                # Show results
                print(f"\nFound {result['count']} results:")
                print("-" * 50)

                for i, res in enumerate(result['results'], 1):
                    print(f"\n{i}. Score: {res['score']:.4f}")
                    print(f"   Abstract: {res['abstract_id']}")
                    print(f"   Labels: {', '.join(res['labels'])}")
                    print(f"   Preview: {res['content'][:150]}...")

            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")

    elif args.query:
        # Single search
        print(f"Searching for: '{args.query}'")
        print("-" * 50)

        result = searcher.search(args.query, limit=args.limit, exact=args.exact)

        # Show timing
        print(f"\nTiming:")
        print(f"  Embedding generation: {result['timing']['embedding']:.3f}s")
        print(f"  Qdrant search:       {result['timing']['qdrant_search']:.3f}s")
        print(f"  Total time:          {result['timing']['total']:.3f}s")

        # Show results
        print(f"\nFound {result['count']} results:")
        print("=" * 50)

        for i, res in enumerate(result['results'], 1):
            print(f"\n{i}. Score: {res['score']:.4f}")
            print(f"   Abstract ID: {res['abstract_id']}")
            print(f"   Labels: {', '.join(res['labels'])}")
            print(f"   Content: {res['content'][:200]}...")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()