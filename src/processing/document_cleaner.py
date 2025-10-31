"""
Document cleaning and preprocessing utilities.

This module provides tools to clean documents before chunking by removing:
- Table of Contents
- Acknowledgements
- References/Bibliography
- Headers/Footers
- Boilerplate text
- Other non-essential sections
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CleaningStats:
    """Statistics about document cleaning."""
    original_length: int
    cleaned_length: int
    sections_removed: List[str]
    lines_removed: int
    
    @property
    def reduction_percentage(self) -> float:
        """Calculate percentage of content removed."""
        if self.original_length == 0:
            return 0.0
        removed = self.original_length - self.cleaned_length
        return (removed / self.original_length) * 100


class DocumentCleaner:
    """
    Cleans documents by removing non-essential sections.
    
    Removes common sections like:
    - Table of Contents (TOC)
    - Acknowledgements
    - References/Bibliography
    - Appendices (optional)
    - Headers/Footers
    - Page numbers
    """
    
    # Common section headers to remove
    TOC_PATTERNS = [
        r'^table of contents?$',
        r'^contents?$',
        r'^toc$',
        r'^\d+\.\s*table of contents',
        r'^list of (figures|tables|illustrations)',
    ]
    
    ACKNOWLEDGEMENT_PATTERNS = [
        r'^acknowledgements?$',
        r'^acknowledgments?$',
        r'^thanks?$',
        r'^\d+\.\s*acknowledgements?',
    ]
    
    REFERENCE_PATTERNS = [
        r'^references?$',
        r'^bibliography$',
        r'^works? cited$',
        r'^citations?$',
        r'^\d+\.\s*references?',
    ]
    
    APPENDIX_PATTERNS = [
        r'^appendix\s*[a-z]?$',
        r'^appendices$',
        r'^\d+\.\s*appendix',
    ]
    
    FOOTER_PATTERNS = [
        r'^\d+\s*$',  # Page numbers
        r'^page\s+\d+\s*$',
        r'^-\s*\d+\s*-$',
    ]
    
    def __init__(
        self,
        remove_toc: bool = True,
        remove_acknowledgements: bool = True,
        remove_references: bool = False,  # Often want to keep references
        remove_appendices: bool = False,
        remove_headers_footers: bool = True,
        min_section_lines: int = 3  # Min lines in a section to process
    ):
        """
        Initialize document cleaner.
        
        Args:
            remove_toc: Remove table of contents
            remove_acknowledgements: Remove acknowledgements section
            remove_references: Remove references/bibliography
            remove_appendices: Remove appendices
            remove_headers_footers: Remove headers and footers
            min_section_lines: Minimum lines in a section
        """
        self.remove_toc = remove_toc
        self.remove_acknowledgements = remove_acknowledgements
        self.remove_references = remove_references
        self.remove_appendices = remove_appendices
        self.remove_headers_footers = remove_headers_footers
        self.min_section_lines = min_section_lines
        
        # Compile patterns for efficiency
        self.toc_regex = self._compile_patterns(self.TOC_PATTERNS)
        self.ack_regex = self._compile_patterns(self.ACKNOWLEDGEMENT_PATTERNS)
        self.ref_regex = self._compile_patterns(self.REFERENCE_PATTERNS)
        self.app_regex = self._compile_patterns(self.APPENDIX_PATTERNS)
        self.footer_regex = self._compile_patterns(self.FOOTER_PATTERNS)
    
    def _compile_patterns(self, patterns: List[str]) -> re.Pattern:
        """Compile multiple patterns into a single regex."""
        combined = '|'.join(f'({p})' for p in patterns)
        return re.compile(combined, re.IGNORECASE | re.MULTILINE)
    
    def clean(self, text: str, verbose: bool = False) -> Tuple[str, CleaningStats]:
        """
        Clean document text by removing non-essential sections.
        
        Args:
            text: Document text to clean
            verbose: Log detailed cleaning steps
            
        Returns:
            Tuple of (cleaned_text, cleaning_stats)
        """
        original_length = len(text)
        sections_removed = []
        
        if verbose:
            logger.info("Starting document cleaning...")
        
        # Step 1: Remove table of contents
        if self.remove_toc:
            text, removed = self._remove_section(
                text, 
                self.toc_regex,
                "Table of Contents"
            )
            if removed:
                sections_removed.append("Table of Contents")
                if verbose:
                    logger.info("✓ Removed Table of Contents")
        
        # Step 2: Remove acknowledgements
        if self.remove_acknowledgements:
            text, removed = self._remove_section(
                text,
                self.ack_regex,
                "Acknowledgements"
            )
            if removed:
                sections_removed.append("Acknowledgements")
                if verbose:
                    logger.info("✓ Removed Acknowledgements")
        
        # Step 3: Remove references
        if self.remove_references:
            text, removed = self._remove_section(
                text,
                self.ref_regex,
                "References"
            )
            if removed:
                sections_removed.append("References")
                if verbose:
                    logger.info("✓ Removed References")
        
        # Step 4: Remove appendices
        if self.remove_appendices:
            text, removed = self._remove_section(
                text,
                self.app_regex,
                "Appendix"
            )
            if removed:
                sections_removed.append("Appendix")
                if verbose:
                    logger.info("✓ Removed Appendix")
        
        # Step 5: Remove headers and footers
        if self.remove_headers_footers:
            text = self._remove_headers_footers(text)
            sections_removed.append("Headers/Footers")
            if verbose:
                logger.info("✓ Removed Headers/Footers")
        
        # Step 6: Clean up extra whitespace
        text = self._clean_whitespace(text)
        
        # Calculate stats
        cleaned_length = len(text)
        lines_removed = original_length - cleaned_length
        
        stats = CleaningStats(
            original_length=original_length,
            cleaned_length=cleaned_length,
            sections_removed=sections_removed,
            lines_removed=lines_removed
        )
        
        if verbose:
            logger.info(f"Cleaning complete: {stats.reduction_percentage:.1f}% content removed")
        
        return text, stats
    
    def _remove_section(
        self,
        text: str,
        pattern: re.Pattern,
        section_name: str
    ) -> Tuple[str, bool]:
        """
        Remove a section from the document.
        
        Args:
            text: Document text
            pattern: Regex pattern to match section header
            section_name: Name of section (for logging)
            
        Returns:
            Tuple of (cleaned_text, was_removed)
        """
        lines = text.split('\n')
        cleaned_lines = []
        skip_until_next_section = False
        removed = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check if this line is a section header to remove
            if pattern.match(line_stripped):
                skip_until_next_section = True
                removed = True
                continue
            
            # Check if we've reached a new section
            if skip_until_next_section:
                # Look for next major section (markdown heading or numbered section)
                if self._is_section_header(line_stripped):
                    skip_until_next_section = False
                else:
                    continue  # Skip this line
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines), removed
    
    def _is_section_header(self, line: str) -> bool:
        """
        Check if a line is a section header.
        
        Args:
            line: Line to check
            
        Returns:
            True if line is a section header
        """
        if not line:
            return False
        
        # Markdown headers
        if line.startswith('#'):
            return True
        
        # Numbered sections (e.g., "1. Introduction", "2.1 Background")
        if re.match(r'^\d+\.(\d+\.)*\s+[A-Z]', line):
            return True
        
        # All caps headers (common in academic papers)
        if line.isupper() and len(line.split()) <= 5:
            return True
        
        # Underlined headers
        if re.match(r'^[=\-]{3,}$', line):
            return True
        
        return False
    
    def _remove_headers_footers(self, text: str) -> str:
        """
        Remove headers and footers (page numbers, etc.).
        
        Args:
            text: Document text
            
        Returns:
            Cleaned text
        """
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip if matches footer pattern
            if self.footer_regex.match(line_stripped):
                continue
            
            # Skip very short lines at start/end of paragraphs (likely headers/footers)
            if len(line_stripped) < 3:
                continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _clean_whitespace(self, text: str) -> str:
        """
        Clean up excessive whitespace.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        # Remove multiple blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in text.split('\n')]
        
        # Remove leading/trailing whitespace from document
        text = '\n'.join(lines).strip()
        
        return text
    
    def detect_sections(self, text: str) -> Dict[str, List[int]]:
        """
        Detect which sections are present in the document.
        
        Args:
            text: Document text
            
        Returns:
            Dictionary mapping section names to line numbers
        """
        lines = text.split('\n')
        sections = {
            'Table of Contents': [],
            'Acknowledgements': [],
            'References': [],
            'Appendix': []
        }
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            if self.toc_regex.match(line_stripped):
                sections['Table of Contents'].append(i)
            
            if self.ack_regex.match(line_stripped):
                sections['Acknowledgements'].append(i)
            
            if self.ref_regex.match(line_stripped):
                sections['References'].append(i)
            
            if self.app_regex.match(line_stripped):
                sections['Appendix'].append(i)
        
        # Remove empty sections
        sections = {k: v for k, v in sections.items() if v}
        
        return sections


class SmartDocumentCleaner(DocumentCleaner):
    """
    Enhanced document cleaner with ML-based section detection.
    
    Uses heuristics to better identify sections to remove:
    - Detects TOC by looking for page number patterns
    - Detects acknowledgements by common phrases
    - Better handling of multi-page sections
    """
    
    # Common TOC indicators
    TOC_INDICATORS = [
        r'\.\.\.',  # Dots in TOC
        r'\d+\s*$',  # Ends with page number
        r'chapter\s+\d+',
        r'section\s+\d+',
    ]
    
    # Common acknowledgement phrases
    ACK_PHRASES = [
        'would like to thank',
        'grateful to',
        'special thanks',
        'like to acknowledge',
        'indebted to',
    ]
    
    def clean(self, text: str, verbose: bool = False) -> Tuple[str, CleaningStats]:
        """
        Clean document with smart detection.
        
        Args:
            text: Document text
            verbose: Log detailed steps
            
        Returns:
            Tuple of (cleaned_text, cleaning_stats)
        """
        original_length = len(text)
        sections_removed = []
        
        if verbose:
            logger.info("Starting smart document cleaning...")
        
        # Detect sections first
        detected_sections = self.detect_sections(text)
        if verbose and detected_sections:
            logger.info(f"Detected sections: {list(detected_sections.keys())}")
        
        # Use parent class cleaning
        text, stats = super().clean(text, verbose=False)
        
        # Additional smart cleaning
        if self.remove_toc:
            text = self._smart_remove_toc(text)
        
        if self.remove_acknowledgements:
            text = self._smart_remove_acknowledgements(text)
        
        # Clean whitespace
        text = self._clean_whitespace(text)
        
        # Update stats
        cleaned_length = len(text)
        lines_removed = original_length - cleaned_length
        
        stats = CleaningStats(
            original_length=original_length,
            cleaned_length=cleaned_length,
            sections_removed=stats.sections_removed,
            lines_removed=lines_removed
        )
        
        if verbose:
            logger.info(f"Smart cleaning complete: {stats.reduction_percentage:.1f}% removed")
        
        return text, stats
    
    def _smart_remove_toc(self, text: str) -> str:
        """
        Smart TOC removal using pattern matching.
        
        Args:
            text: Document text
            
        Returns:
            Text with TOC removed
        """
        lines = text.split('\n')
        toc_start = -1
        toc_end = -1
        
        # Find TOC start
        for i, line in enumerate(lines):
            if self.toc_regex.match(line.strip()):
                toc_start = i
                break
        
        if toc_start == -1:
            return text
        
        # Find TOC end (look for lines with dots and numbers)
        toc_pattern = re.compile('|'.join(self.TOC_INDICATORS), re.IGNORECASE)
        consecutive_non_toc = 0
        
        for i in range(toc_start + 1, min(toc_start + 100, len(lines))):
            line = lines[i].strip()
            
            if toc_pattern.search(line):
                toc_end = i
                consecutive_non_toc = 0
            else:
                consecutive_non_toc += 1
                
            # If we see 5 consecutive non-TOC lines, TOC has ended
            if consecutive_non_toc >= 5:
                break
        
        # Remove TOC section
        if toc_end > toc_start:
            del lines[toc_start:toc_end + 1]
        
        return '\n'.join(lines)
    
    def _smart_remove_acknowledgements(self, text: str) -> str:
        """
        Smart acknowledgements removal using phrase detection.
        
        Args:
            text: Document text
            
        Returns:
            Text with acknowledgements removed
        """
        lines = text.split('\n')
        ack_start = -1
        ack_end = -1
        
        # Find acknowledgements start
        for i, line in enumerate(lines):
            line_lower = line.strip().lower()
            
            if self.ack_regex.match(line_lower):
                ack_start = i
                break
            
            # Also check for acknowledgement phrases
            for phrase in self.ACK_PHRASES:
                if phrase in line_lower:
                    ack_start = i
                    break
            
            if ack_start != -1:
                break
        
        if ack_start == -1:
            return text
        
        # Find acknowledgements end (usually 1-2 paragraphs)
        blank_lines = 0
        for i in range(ack_start + 1, min(ack_start + 50, len(lines))):
            if not lines[i].strip():
                blank_lines += 1
            else:
                blank_lines = 0
            
            # End of acknowledgements (2 consecutive blank lines or new section)
            if blank_lines >= 2 or self._is_section_header(lines[i].strip()):
                ack_end = i
                break
        
        # Remove acknowledgements section
        if ack_end > ack_start:
            del lines[ack_start:ack_end]
        
        return '\n'.join(lines)


def clean_document(
    text: str,
    remove_toc: bool = True,
    remove_acknowledgements: bool = True,
    remove_references: bool = False,
    smart_cleaning: bool = True,
    verbose: bool = False
) -> Tuple[str, CleaningStats]:
    """
    Convenience function to clean a document.
    
    Args:
        text: Document text
        remove_toc: Remove table of contents
        remove_acknowledgements: Remove acknowledgements
        remove_references: Remove references/bibliography
        smart_cleaning: Use smart cleaning (better detection)
        verbose: Log cleaning steps
        
    Returns:
        Tuple of (cleaned_text, cleaning_stats)
    """
    if smart_cleaning:
        cleaner = SmartDocumentCleaner(
            remove_toc=remove_toc,
            remove_acknowledgements=remove_acknowledgements,
            remove_references=remove_references
        )
    else:
        cleaner = DocumentCleaner(
            remove_toc=remove_toc,
            remove_acknowledgements=remove_acknowledgements,
            remove_references=remove_references
        )
    
    return cleaner.clean(text, verbose=verbose)

