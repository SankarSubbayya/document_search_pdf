"""
Centralized configuration management for the Document Search RAG system.
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    type: str = "sqlite"
    sqlite_path: str = "data/documents.db"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "documents"
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None


@dataclass
class VectorStoreConfig:
    """Vector store configuration settings."""
    type: str = "qdrant"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: Optional[str] = None
    collection_name: str = "documents"
    vector_size: int = 384


@dataclass
class ProcessingConfig:
    """Document processing configuration."""
    chunk_size: int = 512
    chunk_overlap: int = 50
    use_semantic_chunking: bool = True
    max_chunk_size: int = 1000
    min_chunk_size: int = 100


@dataclass
class EmbeddingConfig:
    """Embedding model configuration."""
    model: str = "sentence-transformers/all-MiniLM-L6-v2"
    device: str = "cpu"
    batch_size: int = 32
    normalize_embeddings: bool = True


@dataclass
class LLMConfig:
    """LLM configuration for generation."""
    provider: str = "openai"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 500
    top_p: float = 1.0


@dataclass
class ApplicationConfig:
    """Main application configuration."""
    # Paths
    project_root: Path = Path(__file__).parent.parent.parent
    data_dir: Path = project_root / "data"
    processed_dir: Path = data_dir / "processed"
    uploads_dir: Path = data_dir / "uploads"
    logs_dir: Path = project_root / "logs"

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Processing
    max_file_size_mb: int = 100
    supported_formats: list = None

    # Performance
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    max_workers: int = 4

    def __post_init__(self):
        """Initialize default values and create directories."""
        if self.supported_formats is None:
            self.supported_formats = [
                ".pdf", ".docx", ".txt", ".md",
                ".html", ".epub", ".pptx"
            ]

        # Create necessary directories
        for dir_path in [self.data_dir, self.processed_dir,
                         self.uploads_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)


class Settings:
    """Global settings manager."""

    def __init__(self):
        """Initialize all configuration components."""
        self.app = ApplicationConfig()
        self.database = self._load_database_config()
        self.vector_store = self._load_vector_store_config()
        self.processing = self._load_processing_config()
        self.embedding = self._load_embedding_config()
        self.llm = self._load_llm_config()

    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration from environment."""
        return DatabaseConfig(
            type=os.getenv("DB_TYPE", "sqlite"),
            sqlite_path=os.getenv("SQLITE_PATH", "data/documents.db"),
            postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
            postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
            postgres_db=os.getenv("POSTGRES_DB", "documents"),
            postgres_user=os.getenv("POSTGRES_USER"),
            postgres_password=os.getenv("POSTGRES_PASSWORD")
        )

    def _load_vector_store_config(self) -> VectorStoreConfig:
        """Load vector store configuration from environment."""
        return VectorStoreConfig(
            type=os.getenv("VECTOR_STORE_TYPE", "qdrant"),
            qdrant_host=os.getenv("QDRANT_HOST", "localhost"),
            qdrant_port=int(os.getenv("QDRANT_PORT", "6333")),
            qdrant_api_key=os.getenv("QDRANT_API_KEY"),
            collection_name=os.getenv("COLLECTION_NAME", "documents"),
            vector_size=int(os.getenv("VECTOR_SIZE", "384"))
        )

    def _load_processing_config(self) -> ProcessingConfig:
        """Load processing configuration from environment."""
        return ProcessingConfig(
            chunk_size=int(os.getenv("CHUNK_SIZE", "512")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "50")),
            use_semantic_chunking=os.getenv("USE_SEMANTIC_CHUNKING", "true").lower() == "true",
            max_chunk_size=int(os.getenv("MAX_CHUNK_SIZE", "1000")),
            min_chunk_size=int(os.getenv("MIN_CHUNK_SIZE", "100"))
        )

    def _load_embedding_config(self) -> EmbeddingConfig:
        """Load embedding configuration from environment."""
        return EmbeddingConfig(
            model=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
            device=os.getenv("EMBEDDING_DEVICE", "cpu"),
            batch_size=int(os.getenv("EMBEDDING_BATCH_SIZE", "32")),
            normalize_embeddings=os.getenv("NORMALIZE_EMBEDDINGS", "true").lower() == "true"
        )

    def _load_llm_config(self) -> LLMConfig:
        """Load LLM configuration from environment."""
        return LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "500")),
            top_p=float(os.getenv("LLM_TOP_P", "1.0"))
        )

    def to_dict(self) -> dict:
        """Convert settings to dictionary."""
        return {
            "app": self.app.__dict__,
            "database": self.database.__dict__,
            "vector_store": self.vector_store.__dict__,
            "processing": self.processing.__dict__,
            "embedding": self.embedding.__dict__,
            "llm": self.llm.__dict__
        }


# Global settings instance
settings = Settings()