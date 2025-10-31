"""
Hybrid chunking strategies combining multiple approaches.

This module provides combinations of chunking strategies for optimal results:
- Semantic + Late: Smart boundaries with contextual embeddings
- Markup + Context: Structure preservation with surrounding context
"""

import logging
from typing import List, Optional

from chonkie import SemanticChunker
from chonkie.embeddings import SentenceTransformerEmbeddings

from .advanced_chunking import (
    LateChunker,
    ContextChunker,
    MarkupChunker,
    Chunk
)

logger = logging.getLogger(__name__)


class SemanticLateChunker:
    """
    Combines semantic chunking with late chunking.
    
    This gives you:
    - Semantically meaningful chunk boundaries (semantic chunking)
    - Contextual embeddings that include document context (late chunking)
    
    Best for: Maximum retrieval accuracy with intelligent boundaries
    """
    
    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        chunk_size: int = 512,
        semantic_threshold: float = 0.5,
        overlap_size: int = 50,
        max_context_length: int = 8192
    ):
        """
        Initialize semantic + late chunker.
        
        Args:
            embedding_model: Sentence transformer model
            chunk_size: Target chunk size
            semantic_threshold: Similarity threshold for semantic chunking
            overlap_size: Overlap between chunks
            max_context_length: Max length for document embedding
        """
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.semantic_threshold = semantic_threshold
        
        # Create semantic chunker as base
        logger.info("Initializing semantic chunker...")
        embeddings = SentenceTransformerEmbeddings(model=embedding_model)
        self.semantic_chunker = SemanticChunker(
            embedding_model=embeddings,
            chunk_size=chunk_size,
            threshold=semantic_threshold
        )
        
        # Create late chunker
        logger.info("Initializing late chunker...")
        self.late_chunker = LateChunker(
            embedding_model=embedding_model,
            chunk_size=chunk_size,
            overlap_size=overlap_size,
            max_context_length=max_context_length
        )
        
        # Use semantic chunker as the base for late chunker
        self.late_chunker.base_chunker = self.semantic_chunker
        
        logger.info("Semantic + Late chunker initialized")
    
    def chunk(
        self,
        text: str,
        compute_contextual_embeddings: bool = True
    ) -> List[Chunk]:
        """
        Chunk text with semantic boundaries and contextual embeddings.
        
        Args:
            text: Text to chunk
            compute_contextual_embeddings: Whether to compute contextual embeddings
            
        Returns:
            List of chunks with semantic boundaries and contextual embeddings
        """
        logger.info("Chunking with semantic + late strategy...")
        
        chunks = self.late_chunker.chunk(
            text,
            compute_contextual_embeddings=compute_contextual_embeddings
        )
        
        # Update metadata to reflect hybrid strategy
        for chunk in chunks:
            chunk.metadata['chunking_strategy'] = 'semantic_late'
            chunk.metadata['semantic_threshold'] = self.semantic_threshold
        
        logger.info(f"Created {len(chunks)} chunks with semantic boundaries and contextual embeddings")
        return chunks
    
    def chunk_with_sliding_context(
        self,
        text: str,
        context_window_size: int = 3
    ) -> List[Chunk]:
        """
        Chunk with semantic boundaries and sliding window contextual embeddings.
        
        For very long documents, uses sliding window instead of full document.
        
        Args:
            text: Text to chunk
            context_window_size: Size of sliding context window
            
        Returns:
            List of chunks with semantic boundaries and sliding contextual embeddings
        """
        logger.info("Chunking with semantic + late (sliding window)...")
        
        chunks = self.late_chunker.chunk_with_sliding_context(
            text,
            context_window_size=context_window_size
        )
        
        # Update metadata
        for chunk in chunks:
            chunk.metadata['chunking_strategy'] = 'semantic_late_sliding'
            chunk.metadata['semantic_threshold'] = self.semantic_threshold
            chunk.metadata['context_window'] = context_window_size
        
        logger.info(f"Created {len(chunks)} chunks with sliding context")
        return chunks


class MarkupContextChunker:
    """
    Combines markup chunking with context chunking.
    
    This gives you:
    - Structure-aware chunks that preserve document hierarchy (markup)
    - Surrounding context for better understanding (context)
    
    Best for: Structured documents where context across sections matters
    """
    
    def __init__(
        self,
        max_chunk_size: int = 1000,
        min_chunk_size: int = 100,
        preserve_hierarchy: bool = True,
        context_window: int = 1,
        overlap_size: int = 100
    ):
        """
        Initialize markup + context chunker.
        
        Args:
            max_chunk_size: Maximum chunk size
            min_chunk_size: Minimum chunk size
            preserve_hierarchy: Preserve section hierarchy
            context_window: Number of surrounding sections to include as context
            overlap_size: Size of context overlap
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.context_window = context_window
        
        # Initialize markup chunker
        self.markup_chunker = MarkupChunker(
            max_chunk_size=max_chunk_size,
            min_chunk_size=min_chunk_size,
            preserve_hierarchy=preserve_hierarchy
        )
        
        logger.info("Markup + Context chunker initialized")
    
    def chunk(
        self,
        text: str,
        document_type: str = "markdown"
    ) -> List[Chunk]:
        """
        Chunk with markup structure and surrounding context.
        
        Args:
            text: Text to chunk
            document_type: Type of document (markdown, html, generic)
            
        Returns:
            List of chunks with structure and context
        """
        logger.info(f"Chunking {document_type} with markup + context strategy...")
        
        # First, get markup chunks
        markup_chunks = self.markup_chunker.chunk(text, document_type=document_type)
        
        # Then add context from surrounding chunks
        for i, chunk in enumerate(markup_chunks):
            # Add context before
            if i > 0 and self.context_window >= 1:
                before_chunks = []
                for j in range(max(0, i - self.context_window), i):
                    before_chunks.append(markup_chunks[j].text[-100:])
                chunk.context_before = ' ... '.join(before_chunks)
            
            # Add context after
            if i < len(markup_chunks) - 1 and self.context_window >= 1:
                after_chunks = []
                for j in range(i + 1, min(len(markup_chunks), i + 1 + self.context_window)):
                    after_chunks.append(markup_chunks[j].text[:100])
                chunk.context_after = ' ... '.join(after_chunks)
            
            # Update metadata
            chunk.metadata['chunking_strategy'] = 'markup_context'
            chunk.metadata['has_context_before'] = chunk.context_before is not None
            chunk.metadata['has_context_after'] = chunk.context_after is not None
        
        logger.info(f"Created {len(markup_chunks)} chunks with structure and context")
        return markup_chunks


class MarkupSemanticContextChunker:
    """
    Combines Markup + Semantic + Context
    
    This gives you:
    - Structure preservation (markup) - respects document hierarchy
    - Smart semantic boundaries (semantic) - meaningful chunk boundaries
    - Surrounding context (context) - adds text before/after each chunk
    
    Best for: Structured documents where you want semantic boundaries AND context
    Balance: Good quality without the computational cost of Late chunking
    """
    
    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        chunk_size: int = 512,
        semantic_threshold: float = 0.5,
        context_window: int = 2,
        overlap_size: int = 100,
        preserve_hierarchy: bool = True
    ):
        """
        Initialize Markup + Semantic + Context chunker.
        
        Args:
            embedding_model: Sentence transformer model
            chunk_size: Target chunk size
            semantic_threshold: Similarity threshold for semantic chunking
            context_window: Number of chunks before/after to include as context
            overlap_size: Size of context overlap
            preserve_hierarchy: Preserve document hierarchy in metadata
        """
        # Step 1: Markup chunker for structure
        self.markup_chunker = MarkupChunker(
            max_chunk_size=chunk_size * 3,  # Larger sections first
            min_chunk_size=100,
            preserve_hierarchy=preserve_hierarchy
        )
        
        # Step 2: Semantic chunker for smart boundaries
        logger.info("Initializing semantic chunker...")
        embeddings = SentenceTransformerEmbeddings(model=embedding_model)
        self.semantic_chunker = SemanticChunker(
            embedding_model=embeddings,
            chunk_size=chunk_size,
            threshold=semantic_threshold
        )
        
        # Step 3: Context chunker to add surrounding context
        self.context_chunker = ContextChunker(
            chunk_size=chunk_size,
            overlap_size=overlap_size,
            context_window=context_window
        )
        
        self.chunk_size = chunk_size
        logger.info("Markup + Semantic + Context chunker initialized")
    
    def chunk(
        self,
        text: str,
        document_type: str = "markdown"
    ) -> List[Chunk]:
        """
        Chunk with Markup + Semantic + Context.
        
        Process:
        1. Use markup to identify major sections
        2. Within each section, use semantic chunking for boundaries
        3. Add context from surrounding chunks
        
        Args:
            text: Text to chunk
            document_type: Document type (markdown, html, generic)
            
        Returns:
            List of chunks with structure, semantic boundaries, and context
        """
        logger.info("Chunking with Markup + Semantic + Context strategy...")
        
        # Step 1: Get markup sections
        markup_sections = self.markup_chunker.chunk(text, document_type=document_type)
        logger.info(f"Markup chunking created {len(markup_sections)} sections")
        
        # Step 2: Apply semantic chunking within large sections
        semantic_chunks = []
        for section in markup_sections:
            if len(section.text) > self.chunk_size:
                # Use semantic chunking for this section
                try:
                    # Use chonkie's semantic chunker
                    chonkie_chunks = self.semantic_chunker.chunk(section.text)
                    
                    # Convert to our Chunk format and preserve section metadata
                    for idx, chonkie_chunk in enumerate(chonkie_chunks):
                        chunk = Chunk(
                            text=chonkie_chunk.text,
                            chunk_id=f"chunk_{len(semantic_chunks) + idx}",
                            chunk_index=len(semantic_chunks) + idx,
                            start_index=chonkie_chunk.start_index,
                            end_index=chonkie_chunk.end_index,
                            metadata={
                                'parent_section': section.heading,
                                'parent_hierarchy': section.section_hierarchy,
                                'chunking_strategy': 'markup_semantic_context'
                            }
                        )
                        chunk.heading = section.heading
                        chunk.section_hierarchy = section.section_hierarchy
                        semantic_chunks.append(chunk)
                        
                except Exception as e:
                    logger.warning(f"Semantic chunking failed for section, using as-is: {e}")
                    section.metadata['chunking_strategy'] = 'markup_semantic_context'
                    semantic_chunks.append(section)
            else:
                # Section is small enough, keep as is
                section.metadata['chunking_strategy'] = 'markup_semantic_context'
                semantic_chunks.append(section)
        
        logger.info(f"Semantic chunking created {len(semantic_chunks)} chunks")
        
        # Step 3: Add context from surrounding chunks
        chunks_with_context = []
        window = self.context_chunker.context_window
        
        for i, chunk in enumerate(semantic_chunks):
            # Get context before (previous chunks)
            context_before_chunks = semantic_chunks[max(0, i - window):i]
            context_before = ' '.join([c.text for c in context_before_chunks])
            
            # Get context after (next chunks)
            context_after_chunks = semantic_chunks[i + 1:min(len(semantic_chunks), i + window + 1)]
            context_after = ' '.join([c.text for c in context_after_chunks])
            
            # Create new chunk with context
            chunk_with_context = Chunk(
                text=chunk.text,
                chunk_id=f"chunk_ctx_{i}",
                chunk_index=i,
                start_index=chunk.start_index,
                end_index=chunk.end_index,
                metadata=chunk.metadata.copy()
            )
            chunk_with_context.context_before = context_before
            chunk_with_context.context_after = context_after
            chunk_with_context.heading = chunk.heading
            chunk_with_context.section_hierarchy = chunk.section_hierarchy
            
            # Add context metadata
            chunk_with_context.metadata['has_context_before'] = bool(context_before)
            chunk_with_context.metadata['has_context_after'] = bool(context_after)
            chunk_with_context.metadata['context_window'] = window
            
            chunks_with_context.append(chunk_with_context)
        
        logger.info(f"Added context: {len(chunks_with_context)} final chunks")
        return chunks_with_context


class TripleHybridChunker:
    """
    Combines all three: Markup + Semantic + Late
    
    This gives you:
    - Structure preservation (markup)
    - Smart semantic boundaries (semantic)
    - Contextual embeddings (late)
    
    Best for: When you need absolutely maximum quality and have the resources
    Warning: Slowest and most memory-intensive option
    """
    
    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        chunk_size: int = 512,
        semantic_threshold: float = 0.5,
        preserve_hierarchy: bool = True
    ):
        """
        Initialize triple hybrid chunker.
        
        Args:
            embedding_model: Sentence transformer model
            chunk_size: Target chunk size
            semantic_threshold: Similarity threshold
            preserve_hierarchy: Preserve document hierarchy
        """
        self.markup_chunker = MarkupChunker(
            max_chunk_size=chunk_size * 3,  # Larger sections first
            min_chunk_size=100,
            preserve_hierarchy=preserve_hierarchy
        )
        
        self.semantic_late_chunker = SemanticLateChunker(
            embedding_model=embedding_model,
            chunk_size=chunk_size,
            semantic_threshold=semantic_threshold
        )
        
        logger.info("Triple hybrid chunker initialized (Markup + Semantic + Late)")
    
    def chunk(
        self,
        text: str,
        document_type: str = "markdown"
    ) -> List[Chunk]:
        """
        Chunk with all three strategies.
        
        Process:
        1. Use markup to identify major sections
        2. Within each section, use semantic + late chunking
        
        Args:
            text: Text to chunk
            document_type: Document type
            
        Returns:
            List of chunks with structure, semantic boundaries, and contextual embeddings
        """
        logger.info("Chunking with triple hybrid strategy...")
        
        # Step 1: Get markup sections
        sections = self.markup_chunker.chunk(text, document_type=document_type)
        
        # Step 2: Further chunk large sections with semantic + late
        all_chunks = []
        for section in sections:
            if len(section.text) > self.semantic_late_chunker.chunk_size:
                # Use semantic + late for this section
                sub_chunks = self.semantic_late_chunker.chunk(section.text)
                
                # Preserve section metadata
                for sub_chunk in sub_chunks:
                    sub_chunk.metadata['parent_section'] = section.heading
                    sub_chunk.metadata['parent_hierarchy'] = section.section_hierarchy
                    sub_chunk.metadata['chunking_strategy'] = 'markup_semantic_late'
                    sub_chunk.section_hierarchy = section.section_hierarchy
                    
                all_chunks.extend(sub_chunks)
            else:
                # Section is small enough, keep as is
                section.metadata['chunking_strategy'] = 'markup_semantic_late'
                all_chunks.append(section)
        
        logger.info(f"Created {len(all_chunks)} chunks with triple hybrid strategy")
        return all_chunks


def compare_hybrid_strategies(
    text: str,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> dict:
    """
    Compare different hybrid chunking strategies.
    
    Args:
        text: Text to test
        embedding_model: Embedding model to use
        
    Returns:
        Comparison results
    """
    results = {}
    
    strategies = [
        ("semantic_late", SemanticLateChunker(embedding_model=embedding_model)),
        ("markup_context", MarkupContextChunker()),
    ]
    
    for name, chunker in strategies:
        try:
            if name == "markup_context":
                chunks = chunker.chunk(text, document_type="markdown")
            else:
                chunks = chunker.chunk(text)
            
            chunk_sizes = [len(c.text) for c in chunks]
            
            results[name] = {
                'num_chunks': len(chunks),
                'avg_size': sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0,
                'min_size': min(chunk_sizes) if chunk_sizes else 0,
                'max_size': max(chunk_sizes) if chunk_sizes else 0,
                'has_embeddings': any(c.embedding is not None for c in chunks),
                'has_context': any(c.context_before or c.context_after for c in chunks),
                'has_hierarchy': any(c.section_hierarchy for c in chunks)
            }
        except Exception as e:
            logger.error(f"Error with {name}: {e}")
            results[name] = {'error': str(e)}
    
    return results

