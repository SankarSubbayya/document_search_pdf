"""
Vector store abstraction for managing embeddings and similarity search.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
    SearchParams, HnswConfigDiff
)

from ..config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Abstraction layer for vector database operations.
    Currently supports Qdrant, can be extended for other vector databases.
    """

    def __init__(
        self,
        collection_name: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        vector_size: Optional[int] = None
    ):
        """
        Initialize vector store connection.

        Args:
            collection_name: Name of the collection
            host: Vector store host
            port: Vector store port
            vector_size: Dimension of vectors
        """
        self.collection_name = collection_name or settings.vector_store.collection_name
        self.host = host or settings.vector_store.qdrant_host
        self.port = port or settings.vector_store.qdrant_port
        self.vector_size = vector_size or settings.vector_store.vector_size

        # Initialize client based on vector store type
        if settings.vector_store.type == "qdrant":
            self._init_qdrant()
        else:
            raise ValueError(f"Unsupported vector store type: {settings.vector_store.type}")

    def _init_qdrant(self):
        """Initialize Qdrant client and collection."""
        self.client = QdrantClient(
            host=self.host,
            port=self.port,
            api_key=settings.vector_store.qdrant_api_key
        )

        # Create or verify collection
        self._ensure_collection_exists()
        logger.info(f"Connected to Qdrant at {self.host}:{self.port}")

    def _ensure_collection_exists(self):
        """Ensure the collection exists, create if not."""
        try:
            collections = self.client.get_collections()
            if self.collection_name not in [c.name for c in collections.collections]:
                self.create_collection()
        except Exception as e:
            logger.error(f"Error checking collection: {e}")
            raise

    def create_collection(self):
        """Create a new collection with optimized settings."""
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.vector_size,
                distance=Distance.COSINE
            ),
            hnsw_config=HnswConfigDiff(
                m=16,
                ef_construct=100,
                full_scan_threshold=10000
            )
        )
        logger.info(f"Created collection: {self.collection_name}")

    def insert_vectors(
        self,
        vectors: List[np.ndarray],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[int]] = None,
        batch_size: int = 100
    ) -> int:
        """
        Insert vectors with payloads into the collection.

        Args:
            vectors: List of vector embeddings
            payloads: List of metadata payloads
            ids: Optional list of IDs
            batch_size: Batch size for insertion

        Returns:
            Number of vectors inserted
        """
        if len(vectors) != len(payloads):
            raise ValueError("Number of vectors must match number of payloads")

        # Generate IDs if not provided
        if ids is None:
            ids = [hash(str(payload)) % (2**63) for payload in payloads]

        # Create points
        points = []
        for i, (vector, payload, point_id) in enumerate(zip(vectors, payloads, ids)):
            point = PointStruct(
                id=point_id,
                vector=vector.tolist() if isinstance(vector, np.ndarray) else vector,
                payload=payload
            )
            points.append(point)

            # Insert in batches
            if len(points) >= batch_size or i == len(vectors) - 1:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                points = []

        logger.info(f"Inserted {len(vectors)} vectors into {self.collection_name}")
        return len(vectors)

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.

        Args:
            query_vector: Query embedding
            top_k: Number of results to return
            filters: Optional filters for search
            score_threshold: Minimum similarity score

        Returns:
            List of search results with scores and payloads
        """
        # Build filter conditions
        filter_conditions = []
        if filters:
            for key, value in filters.items():
                filter_conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )

        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Perform search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector.tolist() if isinstance(query_vector, np.ndarray) else query_vector,
            query_filter=search_filter,
            limit=top_k,
            with_payload=True,
            score_threshold=score_threshold
        )

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'id': result.id,
                'score': result.score,
                'payload': result.payload
            })

        return formatted_results

    def delete_collection(self):
        """Delete the entire collection."""
        self.client.delete_collection(collection_name=self.collection_name)
        logger.info(f"Deleted collection: {self.collection_name}")

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        info = self.client.get_collection(self.collection_name)
        return {
            'name': self.collection_name,
            'vector_size': info.config.params.vectors.size,
            'points_count': info.points_count,
            'indexed_vectors_count': info.indexed_vectors_count,
            'status': info.status
        }

    def update_payload(
        self,
        point_id: int,
        payload: Dict[str, Any]
    ):
        """Update the payload of a specific point."""
        self.client.set_payload(
            collection_name=self.collection_name,
            payload=payload,
            points=[point_id]
        )

    def delete_points(self, point_ids: List[int]):
        """Delete specific points from the collection."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=point_ids
        )
        logger.info(f"Deleted {len(point_ids)} points from {self.collection_name}")

    def retrieve_points(self, point_ids: List[int]) -> List[Dict[str, Any]]:
        """Retrieve specific points by their IDs."""
        results = self.client.retrieve(
            collection_name=self.collection_name,
            ids=point_ids,
            with_payload=True,
            with_vectors=False
        )

        return [
            {
                'id': point.id,
                'payload': point.payload
            }
            for point in results
        ]