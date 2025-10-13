#!/usr/bin/env python3
"""
Test Qdrant connection and setup collections for the document search RAG system.
"""

import sys
import logging
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    CollectionInfo
)
import yaml

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QdrantManager:
    """Manage Qdrant collections and connections."""

    def __init__(self, host: str = "localhost", port: int = 6333, api_key: str = None):
        """
        Initialize Qdrant manager.

        Args:
            host: Qdrant host
            port: Qdrant port
            api_key: Optional API key for authentication
        """
        self.host = host
        self.port = port
        self.client = QdrantClient(host=host, port=port, api_key=api_key)

    def test_connection(self) -> bool:
        """Test connection to Qdrant."""
        try:
            # Try to get collections
            collections = self.client.get_collections()
            logger.info(f"Successfully connected to Qdrant at {self.host}:{self.port}")
            logger.info(f"Found {len(collections.collections)} collections")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {str(e)}")
            return False

    def create_collection(
        self,
        collection_name: str,
        vector_size: int = 384,
        distance: Distance = Distance.COSINE,
        on_disk: bool = False
    ):
        """
        Create a new collection or recreate if exists.

        Args:
            collection_name: Name of the collection
            vector_size: Size of the vectors
            distance: Distance metric to use
            on_disk: Whether to store vectors on disk
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            exists = any(c.name == collection_name for c in collections.collections)

            if exists:
                logger.info(f"Collection '{collection_name}' already exists")
                response = input("Do you want to recreate it? (y/N): ")
                if response.lower() == 'y':
                    self.client.delete_collection(collection_name)
                    logger.info(f"Deleted existing collection '{collection_name}'")
                else:
                    logger.info("Keeping existing collection")
                    return

            # Create collection with simplified config (no optimizer/wal config to avoid version issues)
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance,
                    on_disk=on_disk
                )
            )

            logger.info(f"Created collection '{collection_name}' with vector size {vector_size}")

        except Exception as e:
            logger.error(f"Failed to create collection: {str(e)}")
            raise

    def get_collection_info(self, collection_name: str):
        """Get information about a collection."""
        try:
            info = self.client.get_collection(collection_name)
            logger.info(f"\nCollection '{collection_name}' info:")
            logger.info(f"  - Status: {info.status}")
            logger.info(f"  - Vectors count: {info.vectors_count}")
            logger.info(f"  - Points count: {info.points_count}")
            logger.info(f"  - Segments count: {info.segments_count}")

            if info.config and info.config.params and info.config.params.vectors:
                vectors_config = info.config.params.vectors
                if hasattr(vectors_config, 'size'):
                    logger.info(f"  - Vector size: {vectors_config.size}")
                if hasattr(vectors_config, 'distance'):
                    logger.info(f"  - Distance metric: {vectors_config.distance}")

            return info
        except Exception as e:
            logger.error(f"Failed to get collection info: {str(e)}")
            return None

    def list_collections(self):
        """List all collections."""
        try:
            collections = self.client.get_collections()
            logger.info("\n" + "="*50)
            logger.info("Available Collections:")
            logger.info("="*50)

            if not collections.collections:
                logger.info("No collections found")
            else:
                for coll in collections.collections:
                    logger.info(f"  - {coll.name}")

            logger.info("="*50)
            return collections.collections
        except Exception as e:
            logger.error(f"Failed to list collections: {str(e)}")
            return []

    def test_insert_and_search(self, collection_name: str, vector_size: int = 384):
        """Test inserting and searching vectors."""
        import numpy as np

        try:
            logger.info(f"\nTesting insert and search on collection '{collection_name}'...")

            # Create test vectors
            test_vectors = [
                np.random.rand(vector_size).tolist() for _ in range(5)
            ]

            # Insert test points
            points = [
                PointStruct(
                    id=i,
                    vector=vector,
                    payload={
                        "text": f"Test document {i}",
                        "source": "test",
                        "metadata": {"test": True}
                    }
                )
                for i, vector in enumerate(test_vectors)
            ]

            self.client.upsert(
                collection_name=collection_name,
                points=points
            )

            logger.info(f"Inserted {len(points)} test points")

            # Search for similar vectors
            search_result = self.client.query_points(
                collection_name=collection_name,
                query=test_vectors[0],
                limit=3
            ).points

            logger.info(f"Search results (top 3):")
            for result in search_result:
                logger.info(f"  - ID: {result.id}, Score: {result.score:.4f}")

            # Clean up test data
            self.client.delete(
                collection_name=collection_name,
                points_selector=list(range(len(points)))
            )
            logger.info("Cleaned up test data")

            return True

        except Exception as e:
            logger.error(f"Test failed: {str(e)}")
            return False


def main():
    """Main function to test Qdrant setup."""
    import argparse

    parser = argparse.ArgumentParser(description="Test and manage Qdrant connection")
    parser.add_argument('--host', default='localhost', help='Qdrant host')
    parser.add_argument('--port', type=int, default=6333, help='Qdrant port')
    parser.add_argument('--api-key', help='API key for authentication')
    parser.add_argument(
        '--create-collection',
        help='Create a new collection with given name'
    )
    parser.add_argument(
        '--vector-size',
        type=int,
        default=384,
        help='Vector size for new collection'
    )
    parser.add_argument(
        '--test-collection',
        help='Test insert and search on collection'
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to config file'
    )

    args = parser.parse_args()

    # Load config if available
    if Path(args.config).exists():
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)

        qdrant_config = config.get('storage', {}).get('qdrant', {})
        host = qdrant_config.get('host', args.host)
        port = qdrant_config.get('port', args.port)
        api_key = qdrant_config.get('api_key', args.api_key)
    else:
        host = args.host
        port = args.port
        api_key = args.api_key

    # Create manager
    manager = QdrantManager(host=host, port=port, api_key=api_key)

    print("\n" + "="*60)
    print("Qdrant Connection Test")
    print("="*60)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print("="*60)

    # Test connection
    if not manager.test_connection():
        print("\n❌ Failed to connect to Qdrant!")
        print("\nPlease ensure:")
        print("1. Qdrant Docker container is running")
        print("2. Run: docker-compose up -d qdrant")
        print("3. Or use: bash scripts/qdrant_setup.sh start")
        sys.exit(1)

    print("✅ Successfully connected to Qdrant!")

    # List collections
    manager.list_collections()

    # Create collection if requested
    if args.create_collection:
        manager.create_collection(
            collection_name=args.create_collection,
            vector_size=args.vector_size
        )

        # Get collection info
        manager.get_collection_info(args.create_collection)

        # Test the collection
        manager.test_insert_and_search(
            collection_name=args.create_collection,
            vector_size=args.vector_size
        )

    # Test specific collection
    elif args.test_collection:
        info = manager.get_collection_info(args.test_collection)
        if info:
            # Get vector size from collection config
            vector_size = args.vector_size
            if info.config and info.config.params and info.config.params.vectors:
                if hasattr(info.config.params.vectors, 'size'):
                    vector_size = info.config.params.vectors.size

            manager.test_insert_and_search(
                collection_name=args.test_collection,
                vector_size=vector_size
            )

    print("\n" + "="*60)
    print("Qdrant is ready for use!")
    print("="*60)
    print("\nQuick commands:")
    print("  - Start Qdrant: docker-compose up -d qdrant")
    print("  - Stop Qdrant: docker-compose stop qdrant")
    print("  - View logs: docker logs -f qdrant")
    print("  - Dashboard: http://localhost:6333/dashboard")
    print("="*60)


if __name__ == "__main__":
    main()