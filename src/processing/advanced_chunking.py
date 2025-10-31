"""
Advanced chunking strategies for document processing.

This module implements three advanced chunking approaches:
1. Markup Chunking - Structure-aware chunking based on document markup
2. Context Chunking - Chunks with surrounding context for better retrieval
3. Late Chunking - Embeddings computed before chunking for context preservation
"""

import re
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum

from chonkie import SemanticChunker, TokenChunker
from chonkie.embeddings import SentenceTransformerEmbeddings
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class ChunkingStrategy(Enum):
    """Available chunking strategies."""
    MARKUP = "markup"
    CONTEXT = "context"
    LATE = "late"
    SEMANTIC = "semantic"
    TOKEN = "token"


@dataclass
class Chunk:
    """Enhanced chunk with metadata and context."""
    text: str
    chunk_id: str
    chunk_index: int
    start_index: int
    end_index: int
    metadata: Dict[str, Any]
    # Context chunking fields
    context_before: Optional[str] = None
    context_after: Optional[str] = None
    # Markup chunking fields
    section_hierarchy: Optional[List[str]] = None
    heading: Optional[str] = None
    # Late chunking fields
    embedding: Optional[np.ndarray] = None
    contextual_embedding: Optional[np.ndarray] = None


class MarkupChunker:
    """
    Chunks documents based on structural markup (headings, sections, etc.).
    
    This is particularly useful for:
    - Technical documentation
    - Academic papers
    - Structured reports
    - Markdown/HTML documents
    """
    
    def __init__(
        self,
        max_chunk_size: int = 1000,
        min_chunk_size: int = 100,
        preserve_hierarchy: bool = True
    ):
        """
        Initialize markup chunker.
        
        Args:
            max_chunk_size: Maximum characters per chunk
            min_chunk_size: Minimum characters per chunk
            preserve_hierarchy: Include section hierarchy in metadata
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.preserve_hierarchy = preserve_hierarchy
        
    def chunk(self, text: str, document_type: str = "markdown") -> List[Chunk]:
        """
        Chunk document based on markup structure.
        
        Args:
            text: Document text to chunk
            document_type: Type of document (markdown, html, etc.)
            
        Returns:
            List of structured chunks
        """
        if document_type == "markdown":
            return self._chunk_markdown(text)
        elif document_type == "html":
            return self._chunk_html(text)
        else:
            return self._chunk_generic(text)
    
    def _chunk_markdown(self, text: str) -> List[Chunk]:
        """Chunk markdown document based on headings."""
        chunks = []
        lines = text.split('\n')
        
        current_section = []
        section_hierarchy = []
        current_heading = None
        chunk_index = 0
        char_index = 0
        
        heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
        
        for line in lines:
            match = heading_pattern.match(line)
            
            if match:
                # Save previous section if it exists
                if current_section:
                    section_text = '\n'.join(current_section)
                    if len(section_text.strip()) >= self.min_chunk_size:
                        chunks.append(self._create_chunk(
                            text=section_text,
                            chunk_index=chunk_index,
                            start_index=char_index - len(section_text),
                            end_index=char_index,
                            heading=current_heading,
                            hierarchy=section_hierarchy.copy()
                        ))
                        chunk_index += 1
                    current_section = []
                
                # Update hierarchy
                level = len(match.group(1))
                heading_text = match.group(2).strip()
                
                # Adjust hierarchy based on heading level
                section_hierarchy = section_hierarchy[:level-1] + [heading_text]
                current_heading = heading_text
                
                current_section.append(line)
            else:
                current_section.append(line)
                
            char_index += len(line) + 1  # +1 for newline
            
            # If section is too large, chunk it further
            if len('\n'.join(current_section)) > self.max_chunk_size:
                section_text = '\n'.join(current_section)
                sub_chunks = self._split_large_section(
                    section_text,
                    chunk_index,
                    char_index - len(section_text),
                    current_heading,
                    section_hierarchy
                )
                chunks.extend(sub_chunks)
                chunk_index += len(sub_chunks)
                current_section = []
        
        # Add final section
        if current_section:
            section_text = '\n'.join(current_section)
            if len(section_text.strip()) >= self.min_chunk_size:
                chunks.append(self._create_chunk(
                    text=section_text,
                    chunk_index=chunk_index,
                    start_index=char_index - len(section_text),
                    end_index=char_index,
                    heading=current_heading,
                    hierarchy=section_hierarchy
                ))
        
        return chunks
    
    def _chunk_html(self, text: str) -> List[Chunk]:
        """Chunk HTML document based on structural elements."""
        # Simple HTML chunking - can be enhanced with BeautifulSoup
        html_section_pattern = re.compile(
            r'<(h[1-6]|section|article|div)[^>]*>(.*?)</\1>',
            re.DOTALL | re.IGNORECASE
        )
        
        chunks = []
        matches = list(html_section_pattern.finditer(text))
        
        for i, match in enumerate(matches):
            section_text = match.group(0)
            if len(section_text.strip()) >= self.min_chunk_size:
                chunks.append(self._create_chunk(
                    text=section_text,
                    chunk_index=i,
                    start_index=match.start(),
                    end_index=match.end(),
                    heading=None,
                    hierarchy=[]
                ))
        
        return chunks if chunks else self._chunk_generic(text)
    
    def _chunk_generic(self, text: str) -> List[Chunk]:
        """Fallback chunking for plain text."""
        paragraphs = text.split('\n\n')
        chunks = []
        chunk_index = 0
        char_index = 0
        
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            if current_size + para_size > self.max_chunk_size and current_chunk:
                # Save current chunk
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append(self._create_chunk(
                    text=chunk_text,
                    chunk_index=chunk_index,
                    start_index=char_index - current_size,
                    end_index=char_index,
                    heading=None,
                    hierarchy=[]
                ))
                chunk_index += 1
                current_chunk = []
                current_size = 0
            
            current_chunk.append(para)
            current_size += para_size
            char_index += para_size + 2  # +2 for \n\n
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(self._create_chunk(
                text=chunk_text,
                chunk_index=chunk_index,
                start_index=char_index - current_size,
                end_index=char_index,
                heading=None,
                hierarchy=[]
            ))
        
        return chunks
    
    def _split_large_section(
        self,
        text: str,
        base_index: int,
        start_char: int,
        heading: Optional[str],
        hierarchy: List[str]
    ) -> List[Chunk]:
        """Split large sections into smaller chunks."""
        chunks = []
        paragraphs = text.split('\n\n')
        
        current_chunk = []
        current_size = 0
        chunk_offset = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            if current_size + para_size > self.max_chunk_size and current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append(self._create_chunk(
                    text=chunk_text,
                    chunk_index=base_index + chunk_offset,
                    start_index=start_char,
                    end_index=start_char + current_size,
                    heading=heading,
                    hierarchy=hierarchy
                ))
                chunk_offset += 1
                start_char += current_size + 2
                current_chunk = []
                current_size = 0
            
            current_chunk.append(para)
            current_size += para_size + 2
        
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(self._create_chunk(
                text=chunk_text,
                chunk_index=base_index + chunk_offset,
                start_index=start_char,
                end_index=start_char + current_size,
                heading=heading,
                hierarchy=hierarchy
            ))
        
        return chunks
    
    def _create_chunk(
        self,
        text: str,
        chunk_index: int,
        start_index: int,
        end_index: int,
        heading: Optional[str],
        hierarchy: List[str]
    ) -> Chunk:
        """Create a chunk with metadata."""
        return Chunk(
            text=text,
            chunk_id=f"markup_chunk_{chunk_index}",
            chunk_index=chunk_index,
            start_index=start_index,
            end_index=end_index,
            heading=heading,
            section_hierarchy=hierarchy if self.preserve_hierarchy else None,
            metadata={
                'chunking_strategy': 'markup',
                'heading': heading,
                'hierarchy_depth': len(hierarchy),
                'section_path': ' > '.join(hierarchy) if hierarchy else None
            }
        )


class ContextChunker:
    """
    Chunks with surrounding context for improved retrieval.
    
    Each chunk includes:
    - Main content
    - Context before (previous chunk overlap)
    - Context after (next chunk overlap)
    
    This helps with:
    - Better semantic understanding
    - Improved retrieval accuracy
    - Context preservation across chunk boundaries
    """
    
    def __init__(
        self,
        chunk_size: int = 512,
        overlap_size: int = 100,
        context_window: int = 2,  # Number of surrounding chunks to include
        base_chunker: Optional[Union[SemanticChunker, TokenChunker]] = None
    ):
        """
        Initialize context chunker.
        
        Args:
            chunk_size: Target size for main chunk
            overlap_size: Overlap between chunks
            context_window: Number of surrounding chunks to include as context
            base_chunker: Base chunker to use (semantic or token)
        """
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.context_window = context_window
        
        if base_chunker is None:
            # Default to token chunker
            self.base_chunker = TokenChunker(
                chunk_size=chunk_size,
                chunk_overlap=overlap_size
            )
        else:
            self.base_chunker = base_chunker
    
    def chunk(self, text: str) -> List[Chunk]:
        """
        Chunk text with surrounding context.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of chunks with context
        """
        # First, create base chunks
        base_chunks = self.base_chunker.chunk(text)
        
        # Then add context to each chunk
        enhanced_chunks = []
        
        for i, chunk in enumerate(base_chunks):
            # Get context before (from previous chunks)
            context_before = None
            if i > 0:
                before_texts = []
                for j in range(max(0, i - self.context_window), i):
                    before_chunk = base_chunks[j]
                    chunk_text = before_chunk.text if hasattr(before_chunk, 'text') else str(before_chunk)
                    before_texts.append(chunk_text[-self.overlap_size:])
                context_before = ' ... '.join(before_texts)
            
            # Get context after (from next chunks)
            context_after = None
            if i < len(base_chunks) - 1:
                after_texts = []
                for j in range(i + 1, min(len(base_chunks), i + 1 + self.context_window)):
                    after_chunk = base_chunks[j]
                    chunk_text = after_chunk.text if hasattr(after_chunk, 'text') else str(after_chunk)
                    after_texts.append(chunk_text[:self.overlap_size])
                context_after = ' ... '.join(after_texts)
            
            # Create enhanced chunk
            chunk_text = chunk.text if hasattr(chunk, 'text') else str(chunk)
            
            enhanced_chunk = Chunk(
                text=chunk_text,
                chunk_id=f"context_chunk_{i}",
                chunk_index=i,
                start_index=getattr(chunk, 'start_index', 0),
                end_index=getattr(chunk, 'end_index', len(chunk_text)),
                context_before=context_before,
                context_after=context_after,
                metadata={
                    'chunking_strategy': 'context',
                    'has_context_before': context_before is not None,
                    'has_context_after': context_after is not None,
                    'total_chunks': len(base_chunks)
                }
            )
            
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks
    
    def get_full_context(self, chunk: Chunk) -> str:
        """
        Get the full text including context before and after.
        
        Args:
            chunk: Chunk with context
            
        Returns:
            Full text with context
        """
        parts = []
        
        if chunk.context_before:
            parts.append(f"[Context Before]: {chunk.context_before}")
        
        parts.append(chunk.text)
        
        if chunk.context_after:
            parts.append(f"[Context After]: {chunk.context_after}")
        
        return '\n\n'.join(parts)


class LateChunker:
    """
    Late chunking strategy - compute embeddings first, then chunk.
    
    This approach:
    1. Computes embeddings for the full document or large sections
    2. Chunks the text while preserving embedding context
    3. Creates contextual embeddings for each chunk based on full document
    
    Benefits:
    - Better semantic coherence
    - Preserves global document context
    - More accurate embeddings for retrieval
    """
    
    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        chunk_size: int = 512,
        overlap_size: int = 50,
        max_context_length: int = 8192  # Maximum context for embedding model
    ):
        """
        Initialize late chunker.
        
        Args:
            embedding_model: Sentence transformer model for embeddings
            chunk_size: Target chunk size
            overlap_size: Overlap between chunks
            max_context_length: Maximum context length for embedding model
        """
        self.embedding_model = SentenceTransformer(embedding_model)
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.max_context_length = max_context_length
        
        # Token chunker for splitting
        self.base_chunker = TokenChunker(
            chunk_size=chunk_size,
            chunk_overlap=overlap_size
        )
    
    def chunk(
        self,
        text: str,
        compute_contextual_embeddings: bool = True
    ) -> List[Chunk]:
        """
        Apply late chunking - embed first, then chunk.
        
        Args:
            text: Text to chunk
            compute_contextual_embeddings: Whether to compute contextual embeddings
            
        Returns:
            List of chunks with embeddings
        """
        # Step 1: Compute embedding for the full document (or truncated version)
        truncated_text = text[:self.max_context_length] if len(text) > self.max_context_length else text
        full_document_embedding = self.embedding_model.encode(
            truncated_text,
            convert_to_numpy=True
        )
        
        # Step 2: Create base chunks
        base_chunks = self.base_chunker.chunk(text)
        
        # Step 3: Create enhanced chunks with embeddings
        enhanced_chunks = []
        
        for i, chunk in enumerate(base_chunks):
            chunk_text = chunk.text if hasattr(chunk, 'text') else str(chunk)
            
            # Compute chunk-specific embedding
            chunk_embedding = self.embedding_model.encode(
                chunk_text,
                convert_to_numpy=True
            )
            
            # Compute contextual embedding (weighted combination)
            contextual_embedding = None
            if compute_contextual_embeddings:
                # Blend chunk embedding with document embedding
                # Weight: 70% chunk, 30% document context
                contextual_embedding = (
                    0.7 * chunk_embedding + 0.3 * full_document_embedding
                )
                # Normalize
                contextual_embedding = contextual_embedding / np.linalg.norm(contextual_embedding)
            
            enhanced_chunk = Chunk(
                text=chunk_text,
                chunk_id=f"late_chunk_{i}",
                chunk_index=i,
                start_index=getattr(chunk, 'start_index', 0),
                end_index=getattr(chunk, 'end_index', len(chunk_text)),
                embedding=chunk_embedding,
                contextual_embedding=contextual_embedding,
                metadata={
                    'chunking_strategy': 'late',
                    'has_contextual_embedding': contextual_embedding is not None,
                    'embedding_dim': len(chunk_embedding),
                    'total_chunks': len(base_chunks)
                }
            )
            
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks
    
    def chunk_with_sliding_context(
        self,
        text: str,
        context_window_size: int = 3
    ) -> List[Chunk]:
        """
        Late chunking with sliding context window.
        
        Instead of using the full document embedding, use a sliding window
        of surrounding chunks for context.
        
        Args:
            text: Text to chunk
            context_window_size: Number of chunks before/after to include
            
        Returns:
            List of chunks with sliding context embeddings
        """
        # Create base chunks first
        base_chunks = self.base_chunker.chunk(text)
        
        enhanced_chunks = []
        
        for i, chunk in enumerate(base_chunks):
            chunk_text = chunk.text if hasattr(chunk, 'text') else str(chunk)
            
            # Get surrounding context
            start_idx = max(0, i - context_window_size)
            end_idx = min(len(base_chunks), i + context_window_size + 1)
            
            context_chunks = []
            for j in range(start_idx, end_idx):
                ctx_chunk = base_chunks[j]
                ctx_text = ctx_chunk.text if hasattr(ctx_chunk, 'text') else str(ctx_chunk)
                context_chunks.append(ctx_text)
            
            # Combine context
            context_text = ' '.join(context_chunks)
            
            # Compute embeddings
            chunk_embedding = self.embedding_model.encode(
                chunk_text,
                convert_to_numpy=True
            )
            
            context_embedding = self.embedding_model.encode(
                context_text[:self.max_context_length],
                convert_to_numpy=True
            )
            
            # Create contextual embedding (blend)
            contextual_embedding = (
                0.6 * chunk_embedding + 0.4 * context_embedding
            )
            contextual_embedding = contextual_embedding / np.linalg.norm(contextual_embedding)
            
            enhanced_chunk = Chunk(
                text=chunk_text,
                chunk_id=f"late_sliding_{i}",
                chunk_index=i,
                start_index=getattr(chunk, 'start_index', 0),
                end_index=getattr(chunk, 'end_index', len(chunk_text)),
                embedding=chunk_embedding,
                contextual_embedding=contextual_embedding,
                metadata={
                    'chunking_strategy': 'late_sliding',
                    'context_window': context_window_size,
                    'has_contextual_embedding': True,
                    'total_chunks': len(base_chunks)
                }
            )
            
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks


class UnifiedChunker:
    """
    Unified interface for all chunking strategies.
    
    Allows easy switching between different chunking approaches.
    """
    
    def __init__(
        self,
        strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC,
        chunk_size: int = 512,
        overlap_size: int = 50,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        **kwargs
    ):
        """
        Initialize unified chunker.
        
        Args:
            strategy: Chunking strategy to use
            chunk_size: Target chunk size
            overlap_size: Overlap between chunks
            embedding_model: Model for embeddings
            **kwargs: Additional strategy-specific parameters
        """
        self.strategy = strategy
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        
        # Initialize appropriate chunker
        if strategy == ChunkingStrategy.MARKUP:
            self.chunker = MarkupChunker(
                max_chunk_size=chunk_size,
                min_chunk_size=kwargs.get('min_chunk_size', 100),
                preserve_hierarchy=kwargs.get('preserve_hierarchy', True)
            )
        elif strategy == ChunkingStrategy.CONTEXT:
            embeddings = SentenceTransformerEmbeddings(model=embedding_model)
            base_chunker = SemanticChunker(
                embedding_model=embeddings,
                chunk_size=chunk_size,
                threshold=kwargs.get('threshold', 0.5)
            )
            self.chunker = ContextChunker(
                chunk_size=chunk_size,
                overlap_size=overlap_size,
                context_window=kwargs.get('context_window', 2),
                base_chunker=base_chunker
            )
        elif strategy == ChunkingStrategy.LATE:
            self.chunker = LateChunker(
                embedding_model=embedding_model,
                chunk_size=chunk_size,
                overlap_size=overlap_size,
                max_context_length=kwargs.get('max_context_length', 8192)
            )
        elif strategy == ChunkingStrategy.SEMANTIC:
            embeddings = SentenceTransformerEmbeddings(model=embedding_model)
            self.chunker = SemanticChunker(
                embedding_model=embeddings,
                chunk_size=chunk_size,
                threshold=kwargs.get('threshold', 0.5)
            )
        else:  # TOKEN
            self.chunker = TokenChunker(
                chunk_size=chunk_size,
                chunk_overlap=overlap_size
            )
        
        logger.info(f"Initialized UnifiedChunker with strategy: {strategy.value}")
    
    def chunk(self, text: str, **kwargs) -> List[Chunk]:
        """
        Chunk text using the configured strategy.
        
        Args:
            text: Text to chunk
            **kwargs: Strategy-specific parameters
            
        Returns:
            List of chunks
        """
        if self.strategy == ChunkingStrategy.MARKUP:
            return self.chunker.chunk(
                text,
                document_type=kwargs.get('document_type', 'markdown')
            )
        elif self.strategy == ChunkingStrategy.LATE:
            use_sliding = kwargs.get('use_sliding_context', False)
            if use_sliding:
                return self.chunker.chunk_with_sliding_context(
                    text,
                    context_window_size=kwargs.get('context_window_size', 3)
                )
            else:
                return self.chunker.chunk(text)
        else:
            return self.chunker.chunk(text)
    
    def chunk_to_dict(self, chunks: List[Chunk]) -> List[Dict[str, Any]]:
        """
        Convert chunks to dictionary format for storage.
        
        Args:
            chunks: List of chunks
            
        Returns:
            List of chunk dictionaries
        """
        result = []
        for chunk in chunks:
            chunk_dict = {
                'text': chunk.text,
                'chunk_id': chunk.chunk_id,
                'chunk_index': chunk.chunk_index,
                'start_index': chunk.start_index,
                'end_index': chunk.end_index,
                'metadata': chunk.metadata
            }
            
            # Add optional fields if present
            if chunk.context_before:
                chunk_dict['context_before'] = chunk.context_before
            if chunk.context_after:
                chunk_dict['context_after'] = chunk.context_after
            if chunk.section_hierarchy:
                chunk_dict['section_hierarchy'] = chunk.section_hierarchy
            if chunk.heading:
                chunk_dict['heading'] = chunk.heading
            if chunk.embedding is not None:
                chunk_dict['embedding'] = chunk.embedding.tolist()
            if chunk.contextual_embedding is not None:
                chunk_dict['contextual_embedding'] = chunk.contextual_embedding.tolist()
            
            result.append(chunk_dict)
        
        return result


def compare_chunking_strategies(
    text: str,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> Dict[str, Any]:
    """
    Compare different chunking strategies on the same text.
    
    Args:
        text: Text to chunk
        embedding_model: Model for embeddings
        
    Returns:
        Comparison statistics for each strategy
    """
    results = {}
    
    strategies = [
        (ChunkingStrategy.MARKUP, {}),
        (ChunkingStrategy.CONTEXT, {}),
        (ChunkingStrategy.LATE, {}),
        (ChunkingStrategy.SEMANTIC, {}),
        (ChunkingStrategy.TOKEN, {})
    ]
    
    for strategy, kwargs in strategies:
        try:
            chunker = UnifiedChunker(
                strategy=strategy,
                chunk_size=512,
                overlap_size=50,
                embedding_model=embedding_model
            )
            
            chunks = chunker.chunk(text, **kwargs)
            
            # Calculate statistics
            chunk_sizes = [len(c.text) for c in chunks]
            
            results[strategy.value] = {
                'num_chunks': len(chunks),
                'avg_chunk_size': np.mean(chunk_sizes) if chunk_sizes else 0,
                'min_chunk_size': min(chunk_sizes) if chunk_sizes else 0,
                'max_chunk_size': max(chunk_sizes) if chunk_sizes else 0,
                'std_chunk_size': np.std(chunk_sizes) if chunk_sizes else 0,
                'has_embeddings': any(c.embedding is not None for c in chunks),
                'has_context': any(c.context_before is not None or c.context_after is not None for c in chunks),
                'has_hierarchy': any(c.section_hierarchy is not None for c in chunks)
            }
        except Exception as e:
            logger.error(f"Error with {strategy.value}: {e}")
            results[strategy.value] = {'error': str(e)}
    
    return results

