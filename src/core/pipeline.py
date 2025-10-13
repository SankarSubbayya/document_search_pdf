"""
Main document processing pipeline orchestrator.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import json

from ..config import settings
from ..processing import DocumentProcessor, ProcessedDocument
from ..storage import DatabaseManager, VectorStore
from ..retrieval import EnhancedDocumentRAG

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of document processing pipeline."""
    documents_processed: int
    chunks_created: int
    tables_extracted: int
    images_extracted: int
    errors: List[str]
    processing_time: float


class DocumentPipeline:
    """
    Orchestrates the complete document processing pipeline.

    This class coordinates:
    1. Document ingestion and processing (docling)
    2. Intelligent chunking (chonkie)
    3. Database storage (SQLite/PostgreSQL)
    4. Vector indexing (Qdrant)
    5. RAG system initialization
    """

    def __init__(self):
        """Initialize pipeline components."""
        logger.info("Initializing Document Pipeline")

        # Initialize components
        self.processor = DocumentProcessor(
            chunk_size=settings.processing.chunk_size,
            chunk_overlap=settings.processing.chunk_overlap,
            use_semantic_chunking=settings.processing.use_semantic_chunking
        )

        # Initialize storage
        self.db_manager = DatabaseManager(
            db_type=settings.database.type,
            db_path=settings.database.sqlite_path if settings.database.type == "sqlite" else None,
            connection_params={
                "host": settings.database.postgres_host,
                "port": settings.database.postgres_port,
                "database": settings.database.postgres_db,
                "user": settings.database.postgres_user,
                "password": settings.database.postgres_password
            } if settings.database.type == "postgresql" else None
        )

        # Initialize vector store
        self.vector_store = VectorStore(
            collection_name=settings.vector_store.collection_name,
            host=settings.vector_store.qdrant_host,
            port=settings.vector_store.qdrant_port,
            vector_size=settings.vector_store.vector_size
        )

        # Initialize RAG system
        self.rag_system = EnhancedDocumentRAG(
            collection_name=settings.vector_store.collection_name,
            embedding_model=settings.embedding.model,
            qdrant_url=settings.vector_store.qdrant_host,
            qdrant_port=settings.vector_store.qdrant_port,
            openai_model=settings.llm.openai_model,
            chunk_size=settings.processing.chunk_size,
            use_semantic_chunking=settings.processing.use_semantic_chunking
        )

        logger.info("Document Pipeline initialized successfully")

    def process_documents(
        self,
        input_path: Union[str, Path, List[Union[str, Path]]],
        category: Optional[str] = None,
        extract_tables: bool = True,
        extract_images: bool = True,
        batch_size: int = 50,
        max_documents: Optional[int] = None
    ) -> PipelineResult:
        """
        Process documents through the complete pipeline.

        Args:
            input_path: Path to documents or directory
            category: Optional category for classification
            extract_tables: Extract tables from documents
            extract_images: Extract images from documents
            batch_size: Batch size for processing
            max_documents: Maximum number of documents to process

        Returns:
            PipelineResult with processing statistics
        """
        import time
        start_time = time.time()

        logger.info(f"Starting document processing for: {input_path}")

        # Determine input type and get file list
        files = self._get_file_list(input_path, max_documents)

        if not files:
            logger.warning("No files found to process")
            return PipelineResult(
                documents_processed=0,
                chunks_created=0,
                tables_extracted=0,
                images_extracted=0,
                errors=["No files found"],
                processing_time=0
            )

        # Process documents
        processed_docs = []
        errors = []

        for file_path in files:
            try:
                logger.info(f"Processing: {file_path}")
                doc = self.processor.process_document(
                    file_path,
                    extract_tables=extract_tables,
                    extract_images=extract_images,
                    category=category
                )
                processed_docs.append(doc)

                # Store in database
                self.db_manager.insert_document(doc)

            except Exception as e:
                error_msg = f"Error processing {file_path}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Index in vector store
        if processed_docs:
            logger.info("Indexing documents in vector store")
            stats = self.rag_system.process_and_index_documents(
                [Path(doc.file_path) for doc in processed_docs],
                batch_size=batch_size,
                save_processed=False  # Already saved to DB
            )
        else:
            stats = {'total_chunks': 0, 'total_tables': 0, 'total_images': 0}

        processing_time = time.time() - start_time

        result = PipelineResult(
            documents_processed=len(processed_docs),
            chunks_created=stats.get('total_chunks', 0),
            tables_extracted=stats.get('total_tables', 0),
            images_extracted=stats.get('total_images', 0),
            errors=errors,
            processing_time=processing_time
        )

        logger.info(f"Processing complete: {result.documents_processed} documents in {processing_time:.2f}s")

        return result

    def _get_file_list(
        self,
        input_path: Union[str, Path, List[Union[str, Path]]],
        max_documents: Optional[int] = None
    ) -> List[Path]:
        """Get list of files to process."""
        files = []

        if isinstance(input_path, list):
            files = [Path(p) for p in input_path]
        else:
            path = Path(input_path)
            if path.is_file():
                files = [path]
            elif path.is_dir():
                # Get all supported files from directory
                for pattern in settings.app.supported_formats:
                    files.extend(path.rglob(f"*{pattern}"))

        # Limit number of files if specified
        if max_documents:
            files = files[:max_documents]

        return files

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents.

        Args:
            query: Search query
            top_k: Number of results
            filters: Optional filters

        Returns:
            List of search results
        """
        return self.rag_system.enhanced_search(
            query=query,
            top_k=top_k,
            category_filter=filters.get('category') if filters else None,
            file_type_filter=filters.get('file_type') if filters else None
        )

    def generate_answer(
        self,
        query: str,
        top_k: int = 5,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate an answer using RAG.

        Args:
            query: User question
            top_k: Number of contexts to retrieve
            temperature: Generation temperature

        Returns:
            Generated answer with sources
        """
        return self.rag_system.enhanced_rag_query(
            query=query,
            top_k=top_k,
            temperature=temperature
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        db_stats = self.db_manager.get_statistics()
        vector_stats = self.vector_store.get_collection_info()

        return {
            'database': db_stats,
            'vector_store': vector_stats
        }

    def close(self):
        """Close all connections."""
        self.db_manager.close()
        logger.info("Pipeline connections closed")