#!/usr/bin/env python3
"""
Process documents using advanced chunking strategies and store in Qdrant.

This script demonstrates how to integrate markup, context, and late chunking
with your existing document processing pipeline.

Usage:
    python scripts/process_with_advanced_chunking.py --strategy late --input /path/to/docs
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processing.advanced_chunking import (
    UnifiedChunker,
    ChunkingStrategy,
    Chunk
)
from src.processing.pdf_processor import PDFProcessor
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import yaml
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AdvancedDocumentProcessor:
    """
    Document processor that integrates advanced chunking strategies
    with Qdrant vector storage.
    """
    
    def __init__(
        self,
        chunking_strategy: ChunkingStrategy = ChunkingStrategy.CONTEXT,
        chunk_size: int = 512,
        overlap_size: int = 50,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "documents_advanced"
    ):
        """
        Initialize the advanced document processor.
        
        Args:
            chunking_strategy: Which chunking strategy to use
            chunk_size: Target chunk size
            overlap_size: Overlap between chunks
            embedding_model: Sentence transformer model
            qdrant_host: Qdrant server host
            qdrant_port: Qdrant server port
            collection_name: Name of Qdrant collection
        """
        self.chunking_strategy = chunking_strategy
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        
        # Initialize chunker
        logger.info(f"Initializing {chunking_strategy.value} chunker...")
        self.chunker = UnifiedChunker(
            strategy=chunking_strategy,
            chunk_size=chunk_size,
            overlap_size=overlap_size,
            embedding_model=embedding_model
        )
        
        # Initialize embedding model (for non-late chunking strategies)
        if chunking_strategy != ChunkingStrategy.LATE:
            logger.info(f"Loading embedding model: {embedding_model}")
            self.embedding_model = SentenceTransformer(embedding_model)
        else:
            self.embedding_model = None  # Late chunker computes its own
        
        # Initialize PDF processor
        self.pdf_processor = PDFProcessor(
            use_ocr=False,
            extract_tables=True,
            extract_images=True
        )
        
        # Initialize Qdrant client
        logger.info(f"Connecting to Qdrant at {qdrant_host}:{qdrant_port}")
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.collection_name = collection_name
        
        # Create collection if it doesn't exist
        self._setup_collection()
    
    def _setup_collection(self):
        """Set up Qdrant collection."""
        collections = self.qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self.collection_name not in collection_names:
            logger.info(f"Creating collection: {self.collection_name}")
            
            # Determine vector size
            if self.embedding_model:
                vector_size = self.embedding_model.get_sentence_embedding_dimension()
            else:
                # For late chunking, use default model size
                vector_size = 384  # all-MiniLM-L6-v2 size
            
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Collection created with vector size: {vector_size}")
        else:
            logger.info(f"Using existing collection: {self.collection_name}")
    
    def process_document(
        self,
        file_path: Path,
        document_type: str = "generic"
    ) -> List[PointStruct]:
        """
        Process a single document and return Qdrant points.
        
        Args:
            file_path: Path to document
            document_type: Type of document (for markup chunking)
            
        Returns:
            List of Qdrant points ready for insertion
        """
        logger.info(f"Processing: {file_path.name}")
        
        # Extract text based on file type
        if file_path.suffix.lower() == '.pdf':
            pdf_content = self.pdf_processor.process_pdf(file_path)
            text = pdf_content.text
            base_metadata = {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'file_type': 'pdf',
                'extraction_method': pdf_content.extraction_method,
                'pages': pdf_content.metadata.get('pages', 0)
            }
        else:
            # For text/markdown files
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            base_metadata = {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'file_type': file_path.suffix.lower()
            }
        
        if not text.strip():
            logger.warning(f"No text extracted from {file_path.name}")
            return []
        
        # Chunk the document
        logger.info(f"Chunking with {self.chunking_strategy.value} strategy...")
        
        chunk_kwargs = {}
        if self.chunking_strategy == ChunkingStrategy.MARKUP:
            chunk_kwargs['document_type'] = document_type
        
        chunks = self.chunker.chunk(text, **chunk_kwargs)
        logger.info(f"Created {len(chunks)} chunks")
        
        # Convert chunks to Qdrant points
        points = []
        for i, chunk in enumerate(chunks):
            # Get embedding
            if chunk.contextual_embedding is not None:
                # Late chunking - use contextual embedding
                embedding = chunk.contextual_embedding
            elif chunk.embedding is not None:
                # Late chunking - use chunk embedding
                embedding = chunk.embedding
            else:
                # Other strategies - compute embedding
                embedding = self.embedding_model.encode(
                    chunk.text,
                    convert_to_numpy=True
                )
            
            # Prepare metadata
            point_metadata = {
                **base_metadata,
                'chunk_id': chunk.chunk_id,
                'chunk_index': chunk.chunk_index,
                'chunk_text': chunk.text,
                'chunking_strategy': self.chunking_strategy.value,
                'chunk_size': len(chunk.text),
                'start_index': chunk.start_index,
                'end_index': chunk.end_index
            }
            
            # Add strategy-specific metadata
            if chunk.context_before:
                point_metadata['has_context_before'] = True
                point_metadata['context_before'] = chunk.context_before
            
            if chunk.context_after:
                point_metadata['has_context_after'] = True
                point_metadata['context_after'] = chunk.context_after
            
            if chunk.section_hierarchy:
                point_metadata['section_hierarchy'] = chunk.section_hierarchy
                point_metadata['section_path'] = ' > '.join(chunk.section_hierarchy)
            
            if chunk.heading:
                point_metadata['heading'] = chunk.heading
            
            # Create point
            point = PointStruct(
                id=hash(f"{file_path.name}_{i}") & 0x7FFFFFFF,  # Positive int
                vector=embedding.tolist(),
                payload=point_metadata
            )
            
            points.append(point)
        
        return points
    
    def process_directory(
        self,
        directory_path: Path,
        file_patterns: List[str] = None,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Process all documents in a directory and store in Qdrant.
        
        Args:
            directory_path: Path to directory
            file_patterns: File patterns to match
            batch_size: Batch size for Qdrant insertion
            
        Returns:
            Processing statistics
        """
        if file_patterns is None:
            file_patterns = ['*.pdf', '*.txt', '*.md']
        
        # Find all matching files
        files = []
        for pattern in file_patterns:
            files.extend(directory_path.rglob(pattern))
        
        logger.info(f"Found {len(files)} documents to process")
        
        # Statistics
        stats = {
            'total_files': len(files),
            'processed': 0,
            'failed': 0,
            'total_chunks': 0,
            'total_points': 0
        }
        
        # Process each file
        all_points = []
        
        for file_path in tqdm(files, desc="Processing documents"):
            try:
                # Determine document type
                if file_path.suffix.lower() in ['.md', '.markdown']:
                    document_type = 'markdown'
                elif file_path.suffix.lower() in ['.html', '.htm']:
                    document_type = 'html'
                else:
                    document_type = 'generic'
                
                # Process document
                points = self.process_document(file_path, document_type)
                
                all_points.extend(points)
                stats['processed'] += 1
                stats['total_chunks'] += len(points)
                
                # Insert in batches
                if len(all_points) >= batch_size:
                    self._insert_points(all_points)
                    stats['total_points'] += len(all_points)
                    all_points = []
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                stats['failed'] += 1
        
        # Insert remaining points
        if all_points:
            self._insert_points(all_points)
            stats['total_points'] += len(all_points)
        
        return stats
    
    def _insert_points(self, points: List[PointStruct]):
        """Insert points into Qdrant."""
        if not points:
            return
        
        logger.info(f"Inserting {len(points)} points into Qdrant...")
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        logger.info("Insertion complete")
    
    def search(
        self,
        query: str,
        limit: int = 5,
        include_context: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks.
        
        Args:
            query: Search query
            limit: Number of results
            include_context: Include surrounding context in results
            
        Returns:
            List of search results
        """
        # Compute query embedding
        if self.embedding_model:
            query_embedding = self.embedding_model.encode(query)
        else:
            # For late chunking, use the same model
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            query_embedding = model.encode(query)
        
        # Search Qdrant
        results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding.tolist(),
            limit=limit
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_result = {
                'score': result.score,
                'text': result.payload['chunk_text'],
                'metadata': {
                    'file_name': result.payload.get('file_name'),
                    'heading': result.payload.get('heading'),
                    'section_path': result.payload.get('section_path'),
                    'chunk_index': result.payload.get('chunk_index'),
                    'strategy': result.payload.get('chunking_strategy')
                }
            }
            
            # Add context if available and requested
            if include_context:
                if result.payload.get('has_context_before'):
                    formatted_result['context_before'] = result.payload.get('context_before')
                if result.payload.get('has_context_after'):
                    formatted_result['context_after'] = result.payload.get('context_after')
            
            formatted_results.append(formatted_result)
        
        return formatted_results


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Process documents with advanced chunking strategies"
    )
    parser.add_argument(
        '--strategy',
        type=str,
        choices=['markup', 'context', 'late', 'semantic', 'token'],
        default='context',
        help='Chunking strategy to use'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Input directory containing documents'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=512,
        help='Target chunk size'
    )
    parser.add_argument(
        '--overlap',
        type=int,
        default=50,
        help='Chunk overlap size'
    )
    parser.add_argument(
        '--collection',
        type=str,
        default='documents_advanced',
        help='Qdrant collection name'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for insertion'
    )
    parser.add_argument(
        '--query',
        type=str,
        help='Optional: Search query after processing'
    )
    
    args = parser.parse_args()
    
    # Convert strategy string to enum
    strategy_map = {
        'markup': ChunkingStrategy.MARKUP,
        'context': ChunkingStrategy.CONTEXT,
        'late': ChunkingStrategy.LATE,
        'semantic': ChunkingStrategy.SEMANTIC,
        'token': ChunkingStrategy.TOKEN
    }
    strategy = strategy_map[args.strategy]
    
    # Initialize processor
    logger.info(f"Initializing processor with {args.strategy} chunking...")
    processor = AdvancedDocumentProcessor(
        chunking_strategy=strategy,
        chunk_size=args.chunk_size,
        overlap_size=args.overlap,
        collection_name=args.collection
    )
    
    # Process documents
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        return
    
    logger.info(f"Processing documents from: {input_path}")
    stats = processor.process_directory(
        input_path,
        batch_size=args.batch_size
    )
    
    # Print statistics
    print("\n" + "="*60)
    print("PROCESSING COMPLETE")
    print("="*60)
    print(f"Strategy: {args.strategy}")
    print(f"Total files: {stats['total_files']}")
    print(f"Successfully processed: {stats['processed']}")
    print(f"Failed: {stats['failed']}")
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Total points in Qdrant: {stats['total_points']}")
    print("="*60)
    
    # Optional: Test search
    if args.query:
        print(f"\n🔍 Testing search with query: '{args.query}'")
        results = processor.search(args.query, limit=3)
        
        for i, result in enumerate(results, 1):
            print(f"\n--- Result {i} (Score: {result['score']:.4f}) ---")
            print(f"File: {result['metadata']['file_name']}")
            if result['metadata'].get('heading'):
                print(f"Heading: {result['metadata']['heading']}")
            if result['metadata'].get('section_path'):
                print(f"Section: {result['metadata']['section_path']}")
            print(f"Text: {result['text'][:200]}...")


if __name__ == "__main__":
    main()

