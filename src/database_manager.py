"""
Database manager for persistent document storage using SQLite and PostgreSQL.

This module provides database abstraction for storing processed documents,
metadata, and managing large document collections efficiently.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict
import hashlib

try:
    import psycopg2
    from psycopg2.extras import Json, RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

from .document_processor import ProcessedDocument

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Abstract database manager for document storage.
    Supports SQLite for local storage and PostgreSQL for production.
    """

    def __init__(
        self,
        db_type: str = "sqlite",
        db_path: Optional[str] = None,
        connection_params: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize database manager.

        Args:
            db_type: Database type ('sqlite' or 'postgresql')
            db_path: Path for SQLite database
            connection_params: Connection parameters for PostgreSQL
        """
        self.db_type = db_type
        self.connection = None

        if db_type == "sqlite":
            self._init_sqlite(db_path or "documents.db")
        elif db_type == "postgresql" and POSTGRES_AVAILABLE:
            self._init_postgresql(connection_params)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        self._create_tables()

    def _init_sqlite(self, db_path: str):
        """Initialize SQLite connection."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row
        logger.info(f"Connected to SQLite database: {self.db_path}")

    def _init_postgresql(self, connection_params: Dict[str, Any]):
        """Initialize PostgreSQL connection."""
        if not POSTGRES_AVAILABLE:
            raise ImportError("psycopg2 not installed. Install with: pip install psycopg2-binary")

        self.connection = psycopg2.connect(**connection_params)
        logger.info("Connected to PostgreSQL database")

    def _create_tables(self):
        """Create database tables for document storage."""
        if self.db_type == "sqlite":
            self._create_sqlite_tables()
        else:
            self._create_postgresql_tables()

    def _create_sqlite_tables(self):
        """Create SQLite tables."""
        cursor = self.connection.cursor()

        # Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                file_hash TEXT NOT NULL UNIQUE,
                title TEXT,
                content TEXT,
                category TEXT,
                file_type TEXT,
                file_size INTEGER,
                page_count INTEGER,
                processing_timestamp TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSON
            )
        """)

        # Chunks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                start_index INTEGER,
                end_index INTEGER,
                embedding BLOB,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
            )
        """)

        # Tables extraction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extracted_tables (
                table_id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                table_index INTEGER,
                caption TEXT,
                content JSON,
                position TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
            )
        """)

        # Images extraction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extracted_images (
                image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                image_index INTEGER,
                caption TEXT,
                image_type TEXT,
                position TEXT,
                file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
            )
        """)

        # Processing history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT,
                documents_processed INTEGER,
                chunks_created INTEGER,
                tables_extracted INTEGER,
                images_extracted INTEGER,
                processing_time_seconds REAL,
                status TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(file_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tables_document ON extracted_tables(document_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_document ON extracted_images(document_id)")

        self.connection.commit()
        logger.info("SQLite tables created successfully")

    def _create_postgresql_tables(self):
        """Create PostgreSQL tables."""
        cursor = self.connection.cursor()

        # Enable extensions
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")

        # Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                file_hash TEXT NOT NULL UNIQUE,
                title TEXT,
                content TEXT,
                category TEXT,
                file_type TEXT,
                file_size BIGINT,
                page_count INTEGER,
                processing_timestamp TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB
            )
        """)

        # Chunks table with vector support
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                start_index INTEGER,
                end_index INTEGER,
                embedding vector(384),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tables extraction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extracted_tables (
                table_id SERIAL PRIMARY KEY,
                document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
                table_index INTEGER,
                caption TEXT,
                content JSONB,
                position TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Images extraction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extracted_images (
                image_id SERIAL PRIMARY KEY,
                document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
                image_index INTEGER,
                caption TEXT,
                image_type TEXT,
                position TEXT,
                file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Processing history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_history (
                id SERIAL PRIMARY KEY,
                batch_id TEXT,
                documents_processed INTEGER,
                chunks_created INTEGER,
                tables_extracted INTEGER,
                images_extracted INTEGER,
                processing_time_seconds REAL,
                status TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(file_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops)")

        self.connection.commit()
        logger.info("PostgreSQL tables created successfully")

    def insert_document(self, document: ProcessedDocument) -> bool:
        """
        Insert a processed document into the database.

        Args:
            document: ProcessedDocument object

        Returns:
            Success status
        """
        cursor = self.connection.cursor()

        try:
            # Check if document already exists
            if self.db_type == "sqlite":
                cursor.execute(
                    "SELECT document_id FROM documents WHERE file_hash = ?",
                    (document.file_hash,)
                )
            else:
                cursor.execute(
                    "SELECT document_id FROM documents WHERE file_hash = %s",
                    (document.file_hash,)
                )

            if cursor.fetchone():
                logger.info(f"Document already exists: {document.document_id}")
                return False

            # Insert document
            if self.db_type == "sqlite":
                cursor.execute("""
                    INSERT INTO documents (
                        document_id, file_path, file_hash, title, content,
                        category, file_type, file_size, page_count,
                        processing_timestamp, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    document.document_id,
                    document.file_path,
                    document.file_hash,
                    document.title,
                    document.content,
                    document.metadata.get('category'),
                    document.metadata.get('file_type'),
                    document.metadata.get('file_size'),
                    document.metadata.get('page_count'),
                    document.processing_timestamp,
                    json.dumps(document.metadata)
                ))

                # Insert chunks
                for chunk in document.chunks:
                    cursor.execute("""
                        INSERT INTO chunks (
                            chunk_id, document_id, chunk_index, content,
                            start_index, end_index, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        chunk['chunk_id'],
                        document.document_id,
                        chunk['chunk_index'],
                        chunk['content'],
                        chunk.get('start_index'),
                        chunk.get('end_index'),
                        json.dumps(chunk.get('metadata', {}))
                    ))

                # Insert tables
                for i, table in enumerate(document.tables):
                    cursor.execute("""
                        INSERT INTO extracted_tables (
                            document_id, table_index, caption, content, position
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        document.document_id,
                        i,
                        table.get('caption'),
                        json.dumps(table.get('content')),
                        table.get('position')
                    ))

                # Insert images
                for i, image in enumerate(document.images):
                    cursor.execute("""
                        INSERT INTO extracted_images (
                            document_id, image_index, caption, image_type, position
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        document.document_id,
                        i,
                        image.get('caption'),
                        image.get('type'),
                        image.get('position')
                    ))

            else:  # PostgreSQL
                cursor.execute("""
                    INSERT INTO documents (
                        document_id, file_path, file_hash, title, content,
                        category, file_type, file_size, page_count,
                        processing_timestamp, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    document.document_id,
                    document.file_path,
                    document.file_hash,
                    document.title,
                    document.content,
                    document.metadata.get('category'),
                    document.metadata.get('file_type'),
                    document.metadata.get('file_size'),
                    document.metadata.get('page_count'),
                    document.processing_timestamp,
                    Json(document.metadata)
                ))

                # Similar insertions for PostgreSQL...

            self.connection.commit()
            logger.info(f"Successfully inserted document: {document.document_id}")
            return True

        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error inserting document: {e}")
            return False

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by ID.

        Args:
            document_id: Document identifier

        Returns:
            Document data or None
        """
        cursor = self.connection.cursor()

        if self.db_type == "sqlite":
            cursor.execute("""
                SELECT * FROM documents WHERE document_id = ?
            """, (document_id,))
        else:
            cursor.execute("""
                SELECT * FROM documents WHERE document_id = %s
            """, (document_id,))

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def search_documents(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        file_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search documents with filters.

        Args:
            query: Text search query
            category: Category filter
            file_type: File type filter
            limit: Maximum results
            offset: Result offset

        Returns:
            List of matching documents
        """
        cursor = self.connection.cursor()

        # Build query
        conditions = []
        params = []

        if query:
            conditions.append("(title LIKE ? OR content LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])

        if category:
            conditions.append("category = ?")
            params.append(category)

        if file_type:
            conditions.append("file_type = ?")
            params.append(file_type)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        sql = f"""
            SELECT document_id, file_path, title, category, file_type,
                   file_size, page_count, processing_timestamp
            FROM documents
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        if self.db_type == "postgresql":
            sql = sql.replace("?", "%s")

        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Database statistics
        """
        cursor = self.connection.cursor()

        stats = {}

        # Document count
        cursor.execute("SELECT COUNT(*) as count FROM documents")
        stats['total_documents'] = cursor.fetchone()['count']

        # Chunk count
        cursor.execute("SELECT COUNT(*) as count FROM chunks")
        stats['total_chunks'] = cursor.fetchone()['count']

        # Table count
        cursor.execute("SELECT COUNT(*) as count FROM extracted_tables")
        stats['total_tables'] = cursor.fetchone()['count']

        # Image count
        cursor.execute("SELECT COUNT(*) as count FROM extracted_images")
        stats['total_images'] = cursor.fetchone()['count']

        # Categories
        cursor.execute("SELECT DISTINCT category FROM documents WHERE category IS NOT NULL")
        stats['categories'] = [row['category'] for row in cursor.fetchall()]

        # File types
        cursor.execute("SELECT DISTINCT file_type FROM documents WHERE file_type IS NOT NULL")
        stats['file_types'] = [row['file_type'] for row in cursor.fetchall()]

        # Storage size (SQLite only, skip for in-memory)
        if self.db_type == "sqlite" and self.db_path != ":memory:":
            try:
                stats['database_size_mb'] = Path(self.db_path).stat().st_size / (1024 * 1024)
            except FileNotFoundError:
                stats['database_size_mb'] = 0

        return stats

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")