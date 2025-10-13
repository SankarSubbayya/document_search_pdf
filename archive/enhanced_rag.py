"""
Enhanced RAG system integrating docling document processing with vector search.

This module extends the basic RAG system with advanced document processing,
including support for tables, images, and intelligent chunking.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import logging

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
    SearchParams, HnswConfigDiff
)
from sentence_transformers import SentenceTransformer
import openai
from tqdm import tqdm
import numpy as np

from .document_processor import DocumentProcessor, ProcessedDocument
from .document_search import DocumentSearchRAG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedDocumentRAG(DocumentSearchRAG):
    """
    Enhanced RAG system with advanced document processing capabilities.

    Extends the base RAG system with:
    - Docling-based document parsing
    - Chonkie-based intelligent chunking
    - Support for tables and images
    - Improved metadata handling
    - Database persistence
    """

    def __init__(
        self,
        collection_name: str = "enhanced_documents",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        qdrant_url: str = "localhost",
        qdrant_port: int = 6333,
        openai_model: str = "gpt-4",
        chunk_size: int = 512,
        use_semantic_chunking: bool = True
    ):
        """
        Initialize the enhanced RAG system.

        Args:
            collection_name: Name of the Qdrant collection
            embedding_model: Model for generating embeddings
            qdrant_url: Qdrant server URL
            qdrant_port: Qdrant server port
            openai_model: OpenAI model for generation
            chunk_size: Target chunk size for documents
            use_semantic_chunking: Use semantic vs token-based chunking
        """
        super().__init__(
            collection_name=collection_name,
            embedding_model=embedding_model,
            qdrant_url=qdrant_url,
            qdrant_port=qdrant_port,
            openai_model=openai_model
        )

        # Initialize document processor
        self.document_processor = DocumentProcessor(
            chunk_size=chunk_size,
            use_semantic_chunking=use_semantic_chunking,
            embedding_model=embedding_model
        )

        # Enhanced collection configuration
        self._setup_enhanced_collection()

    def _setup_enhanced_collection(self):
        """Setup enhanced collection with additional fields."""
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            if self.collection_name not in [c.name for c in collections.collections]:
                # Create collection with enhanced configuration
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_model.get_sentence_embedding_dimension(),
                        distance=Distance.COSINE
                    ),
                    hnsw_config=HnswConfigDiff(
                        m=16,
                        ef_construct=100
                    )
                )
                logger.info(f"Created enhanced collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error setting up collection: {e}")
            raise

    def process_and_index_documents(
        self,
        document_paths: Union[str, Path, List[Union[str, Path]]],
        batch_size: int = 50,
        category: Optional[str] = None,
        extract_tables: bool = True,
        extract_images: bool = True,
        save_processed: bool = True,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process documents using docling and index them in the vector store.

        Args:
            document_paths: Path(s) to documents or directory
            batch_size: Batch size for indexing
            category: Optional category for documents
            extract_tables: Extract tables from documents
            extract_images: Extract images from documents
            save_processed: Save processed documents to disk
            output_dir: Directory to save processed documents

        Returns:
            Processing statistics
        """
        # Handle different input types
        if isinstance(document_paths, (str, Path)):
            path = Path(document_paths)
            if path.is_dir():
                # Process directory
                processed_docs = self.document_processor.process_directory(
                    path,
                    recursive=True
                )
            else:
                # Process single file
                processed_docs = [
                    self.document_processor.process_document(
                        path,
                        extract_tables=extract_tables,
                        extract_images=extract_images,
                        category=category
                    )
                ]
        else:
            # Process list of files
            processed_docs = []
            for doc_path in document_paths:
                try:
                    doc = self.document_processor.process_document(
                        doc_path,
                        extract_tables=extract_tables,
                        extract_images=extract_images,
                        category=category
                    )
                    processed_docs.append(doc)
                except Exception as e:
                    logger.error(f"Error processing {doc_path}: {e}")

        # Save processed documents if requested
        if save_processed and output_dir:
            output_path = Path(output_dir) / f"processed_docs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.document_processor.save_processed_documents(
                processed_docs,
                output_path
            )

        # Index documents in vector store
        total_chunks = 0
        total_tables = 0
        total_images = 0

        for doc in tqdm(processed_docs, desc="Indexing documents"):
            # Index document chunks
            chunks_indexed = self._index_document_chunks(doc, batch_size)
            total_chunks += chunks_indexed

            # Index tables separately if present
            if doc.tables:
                tables_indexed = self._index_tables(doc)
                total_tables += tables_indexed

            # Track images (for future multimodal support)
            total_images += len(doc.images)

        stats = {
            'documents_processed': len(processed_docs),
            'total_chunks': total_chunks,
            'total_tables': total_tables,
            'total_images': total_images,
            'processing_timestamp': datetime.utcnow().isoformat()
        }

        logger.info(f"Processing complete: {stats}")
        return stats

    def _index_document_chunks(
        self,
        document: ProcessedDocument,
        batch_size: int = 50
    ) -> int:
        """
        Index document chunks in the vector store.

        Args:
            document: Processed document
            batch_size: Batch size for indexing

        Returns:
            Number of chunks indexed
        """
        points = []

        for chunk in document.chunks:
            # Generate embedding for chunk
            embedding = self.embedding_model.encode(chunk['content'])

            # Create point with enhanced metadata
            point = PointStruct(
                id=hash(f"{document.document_id}_{chunk['chunk_id']}") % (2**63),
                vector=embedding.tolist(),
                payload={
                    'document_id': document.document_id,
                    'chunk_id': chunk['chunk_id'],
                    'chunk_index': chunk['chunk_index'],
                    'content': chunk['content'],
                    'title': document.title,
                    'file_path': document.file_path,
                    'file_hash': document.file_hash,
                    'category': chunk['metadata'].get('category'),
                    'file_type': chunk['metadata'].get('file_type'),
                    'has_tables': len(document.tables) > 0,
                    'has_images': len(document.images) > 0,
                    'processing_timestamp': document.processing_timestamp,
                    **chunk['metadata']
                }
            )
            points.append(point)

            # Index in batches
            if len(points) >= batch_size:
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                points = []

        # Index remaining points
        if points:
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )

        return len(document.chunks)

    def _index_tables(self, document: ProcessedDocument) -> int:
        """
        Index tables as separate entities in the vector store.

        Args:
            document: Processed document containing tables

        Returns:
            Number of tables indexed
        """
        points = []

        for i, table in enumerate(document.tables):
            # Convert table to text representation
            table_text = f"Table {i+1}: {table.get('caption', '')}\n{json.dumps(table['content'])}"

            # Generate embedding
            embedding = self.embedding_model.encode(table_text)

            # Create point for table
            point = PointStruct(
                id=hash(f"{document.document_id}_table_{i}") % (2**63),
                vector=embedding.tolist(),
                payload={
                    'document_id': document.document_id,
                    'content_type': 'table',
                    'table_index': i,
                    'content': table_text,
                    'table_data': table['content'],
                    'caption': table.get('caption', ''),
                    'title': document.title,
                    'file_path': document.file_path,
                    'category': document.metadata.get('category'),
                    'processing_timestamp': document.processing_timestamp
                }
            )
            points.append(point)

        if points:
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )

        return len(points)

    def enhanced_search(
        self,
        query: str,
        top_k: int = 5,
        category_filter: Optional[str] = None,
        file_type_filter: Optional[str] = None,
        include_tables: bool = True,
        date_filter: Optional[Dict[str, str]] = None,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Enhanced search with advanced filtering options.

        Args:
            query: Search query
            top_k: Number of results to return
            category_filter: Filter by category
            file_type_filter: Filter by file type (e.g., '.pdf')
            include_tables: Include table results
            date_filter: Filter by processing date
            score_threshold: Minimum similarity score

        Returns:
            List of search results with metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query)

        # Build filter conditions
        filter_conditions = []

        if category_filter:
            filter_conditions.append(
                FieldCondition(
                    key="category",
                    match=MatchValue(value=category_filter)
                )
            )

        if file_type_filter:
            filter_conditions.append(
                FieldCondition(
                    key="file_type",
                    match=MatchValue(value=file_type_filter)
                )
            )

        if not include_tables:
            filter_conditions.append(
                FieldCondition(
                    key="content_type",
                    match=MatchValue(value="chunk")
                )
            )

        # Construct filter
        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Perform search
        results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding.tolist(),
            query_filter=search_filter,
            limit=top_k,
            with_payload=True,
            score_threshold=score_threshold
        )

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'score': result.score,
                'document_id': result.payload.get('document_id'),
                'title': result.payload.get('title'),
                'content': result.payload.get('content'),
                'chunk_id': result.payload.get('chunk_id'),
                'content_type': result.payload.get('content_type', 'chunk'),
                'file_path': result.payload.get('file_path'),
                'category': result.payload.get('category'),
                'metadata': {
                    k: v for k, v in result.payload.items()
                    if k not in ['content', 'document_id', 'title', 'chunk_id']
                }
            })

        return formatted_results

    def enhanced_rag_query(
        self,
        query: str,
        top_k: int = 5,
        include_tables: bool = True,
        use_reranking: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 500,
        **filter_kwargs
    ) -> Dict[str, Any]:
        """
        Enhanced RAG query with advanced features.

        Args:
            query: User query
            top_k: Number of contexts to retrieve
            include_tables: Include table data in context
            use_reranking: Apply reranking to results
            temperature: Generation temperature
            max_tokens: Maximum tokens in response
            **filter_kwargs: Additional search filters

        Returns:
            Generated response with metadata
        """
        # Retrieve relevant contexts
        search_results = self.enhanced_search(
            query=query,
            top_k=top_k * 2 if use_reranking else top_k,
            include_tables=include_tables,
            **filter_kwargs
        )

        # Apply reranking if requested
        if use_reranking and len(search_results) > top_k:
            search_results = self._rerank_results(query, search_results, top_k)

        # Format context for generation
        context_parts = []
        sources = []

        for result in search_results:
            if result['content_type'] == 'table':
                context_parts.append(f"[Table from {result['title']}]\n{result['content']}")
            else:
                context_parts.append(f"[From {result['title']}]\n{result['content']}")

            sources.append({
                'title': result['title'],
                'file_path': result['file_path'],
                'chunk_id': result.get('chunk_id'),
                'score': result['score']
            })

        context = "\n\n---\n\n".join(context_parts)

        # Generate response
        prompt = f"""You are an AI assistant with access to a comprehensive document database.
        Use the following context to answer the user's question accurately and thoroughly.
        If the context contains relevant tables, incorporate that data in your response.

        Context:
        {context}

        User Question: {query}

        Provide a detailed and accurate answer based on the context provided.
        If you're using information from tables, clearly reference them.
        """

        response = openai.chat.completions.create(
            model=self.openai_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant with access to document context."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )

        return {
            'answer': response.choices[0].message.content,
            'sources': sources,
            'total_results': len(search_results),
            'query': query,
            'filters_applied': filter_kwargs
        }

    def _rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Rerank search results using cross-encoder or heuristics.

        Args:
            query: Original query
            results: Search results to rerank
            top_k: Number of results to return

        Returns:
            Reranked results
        """
        # Simple reranking based on multiple factors
        for result in results:
            # Boost score based on various factors
            boost = 1.0

            # Boost if title matches query terms
            if any(term.lower() in result['title'].lower() for term in query.split()):
                boost *= 1.2

            # Boost tables if query seems to ask for data
            if result.get('content_type') == 'table' and any(
                word in query.lower() for word in ['data', 'table', 'statistics', 'numbers']
            ):
                boost *= 1.3

            result['reranked_score'] = result['score'] * boost

        # Sort by reranked score
        results.sort(key=lambda x: x['reranked_score'], reverse=True)

        return results[:top_k]

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the document collection.

        Returns:
            Collection statistics
        """
        collection_info = self.qdrant_client.get_collection(self.collection_name)

        # Get unique documents
        all_points = self.qdrant_client.scroll(
            collection_name=self.collection_name,
            limit=10000,
            with_payload=True
        )[0]

        unique_docs = set()
        unique_categories = set()
        unique_file_types = set()
        table_count = 0

        for point in all_points:
            unique_docs.add(point.payload.get('document_id'))
            if point.payload.get('category'):
                unique_categories.add(point.payload.get('category'))
            if point.payload.get('file_type'):
                unique_file_types.add(point.payload.get('file_type'))
            if point.payload.get('content_type') == 'table':
                table_count += 1

        return {
            'total_vectors': collection_info.points_count,
            'unique_documents': len(unique_docs),
            'unique_categories': list(unique_categories),
            'unique_file_types': list(unique_file_types),
            'table_count': table_count,
            'vector_dimension': collection_info.config.params.vectors.size,
            'distance_metric': collection_info.config.params.vectors.distance
        }