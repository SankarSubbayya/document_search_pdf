"""
Enhanced PDF document processing with multiple extraction methods.

This module provides specialized PDF processing capabilities including:
- Multiple PDF parsing libraries for robust extraction
- OCR support for scanned PDFs
- Advanced table and image extraction
- Layout preservation and structure detection
"""

import os
import io
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
import hashlib

# PDF processing libraries
import PyPDF2
import pdfplumber
from pypdf import PdfReader
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import numpy as np

# For advanced extraction
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class PDFContent:
    """Container for extracted PDF content."""
    text: str
    tables: List[Dict[str, Any]]
    images: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    page_contents: List[Dict[str, Any]]
    extraction_method: str


class PDFProcessor:
    """
    Enhanced PDF processor with multiple extraction methods and OCR support.
    """

    def __init__(
        self,
        use_ocr: bool = True,
        extract_tables: bool = True,
        extract_images: bool = True,
        ocr_language: str = 'eng',
        dpi: int = 300
    ):
        """
        Initialize the PDF processor.

        Args:
            use_ocr: Enable OCR for scanned PDFs
            extract_tables: Extract tables from PDFs
            extract_images: Extract images from PDFs
            ocr_language: Language for OCR (default: English)
            dpi: DPI for PDF to image conversion
        """
        self.use_ocr = use_ocr
        self.extract_tables = extract_tables
        self.extract_images = extract_images
        self.ocr_language = ocr_language
        self.dpi = dpi

        # Check for tesseract availability
        if use_ocr:
            try:
                pytesseract.get_tesseract_version()
                self.ocr_available = True
            except:
                logger.info("Tesseract OCR not found - this is OK for regular PDFs. OCR is only needed for scanned documents.")
                self.ocr_available = False
                self.use_ocr = False

    def process_pdf(
        self,
        file_path: Union[str, Path],
        fallback_methods: bool = True
    ) -> PDFContent:
        """
        Process a PDF file using multiple extraction methods.

        Args:
            file_path: Path to the PDF file
            fallback_methods: Try alternative methods if primary fails

        Returns:
            PDFContent with all extracted content
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        logger.info(f"Processing PDF: {file_path}")

        # Try primary extraction with pdfplumber
        try:
            content = self._extract_with_pdfplumber(file_path)
            if content and len(content.text.strip()) > 100:
                return content
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")

        # Fallback methods
        if fallback_methods:
            # Try PyPDF2
            try:
                content = self._extract_with_pypdf2(file_path)
                if content and len(content.text.strip()) > 100:
                    return content
            except Exception as e:
                logger.warning(f"PyPDF2 extraction failed: {e}")

            # Try PyMuPDF if available
            if PYMUPDF_AVAILABLE:
                try:
                    content = self._extract_with_pymupdf(file_path)
                    if content and len(content.text.strip()) > 100:
                        return content
                except Exception as e:
                    logger.warning(f"PyMuPDF extraction failed: {e}")

            # Last resort: OCR
            if self.use_ocr and self.ocr_available:
                try:
                    content = self._extract_with_ocr(file_path)
                    return content
                except Exception as e:
                    logger.error(f"OCR extraction failed: {e}")

        raise Exception(f"Failed to extract content from PDF: {file_path}")

    def _extract_with_pdfplumber(self, file_path: Path) -> PDFContent:
        """Extract content using pdfplumber."""
        text_content = []
        tables = []
        images = []
        page_contents = []
        metadata = {}

        with pdfplumber.open(file_path) as pdf:
            # Extract metadata
            if pdf.metadata:
                metadata = {
                    'title': pdf.metadata.get('Title', ''),
                    'author': pdf.metadata.get('Author', ''),
                    'subject': pdf.metadata.get('Subject', ''),
                    'creator': pdf.metadata.get('Creator', ''),
                    'producer': pdf.metadata.get('Producer', ''),
                    'creation_date': str(pdf.metadata.get('CreationDate', '')),
                    'modification_date': str(pdf.metadata.get('ModDate', '')),
                    'pages': len(pdf.pages)
                }

            # Process each page
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text() or ""
                text_content.append(page_text)

                # Extract tables
                if self.extract_tables:
                    page_tables = page.extract_tables()
                    for table_idx, table in enumerate(page_tables or []):
                        tables.append({
                            'page': page_num,
                            'table_index': table_idx,
                            'data': table,
                            'rows': len(table),
                            'columns': len(table[0]) if table else 0
                        })

                # Extract images info
                if self.extract_images and hasattr(page, 'images'):
                    for img_idx, img in enumerate(page.images or []):
                        images.append({
                            'page': page_num,
                            'image_index': img_idx,
                            'bbox': img.get('bbox', []),
                            'width': img.get('width', 0),
                            'height': img.get('height', 0)
                        })

                # Store page content
                page_contents.append({
                    'page': page_num,
                    'text': page_text,
                    'tables_count': len(page_tables) if page_tables else 0,
                    'images_count': len(page.images) if hasattr(page, 'images') and page.images else 0,
                    'char_count': len(page_text)
                })

        return PDFContent(
            text='\n\n'.join(text_content),
            tables=tables,
            images=images,
            metadata=metadata,
            page_contents=page_contents,
            extraction_method='pdfplumber'
        )

    def _extract_with_pypdf2(self, file_path: Path) -> PDFContent:
        """Extract content using PyPDF2."""
        text_content = []
        page_contents = []
        metadata = {}

        with open(file_path, 'rb') as file:
            pdf_reader = PdfReader(file)

            # Extract metadata
            if pdf_reader.metadata:
                metadata = {
                    'title': pdf_reader.metadata.get('/Title', ''),
                    'author': pdf_reader.metadata.get('/Author', ''),
                    'subject': pdf_reader.metadata.get('/Subject', ''),
                    'creator': pdf_reader.metadata.get('/Creator', ''),
                    'producer': pdf_reader.metadata.get('/Producer', ''),
                    'pages': len(pdf_reader.pages)
                }

            # Extract text from each page
            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                text_content.append(page_text)

                page_contents.append({
                    'page': page_num,
                    'text': page_text,
                    'char_count': len(page_text)
                })

        return PDFContent(
            text='\n\n'.join(text_content),
            tables=[],  # PyPDF2 doesn't extract tables
            images=[],  # PyPDF2 doesn't extract images directly
            metadata=metadata,
            page_contents=page_contents,
            extraction_method='pypdf2'
        )

    def _extract_with_pymupdf(self, file_path: Path) -> PDFContent:
        """Extract content using PyMuPDF."""
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF is not installed")

        text_content = []
        tables = []
        images = []
        page_contents = []
        metadata = {}

        doc = fitz.open(file_path)

        # Extract metadata
        metadata = doc.metadata
        metadata['pages'] = doc.page_count

        # Process each page
        for page_num, page in enumerate(doc, 1):
            # Extract text
            page_text = page.get_text()
            text_content.append(page_text)

            # Extract tables (if available)
            if self.extract_tables and hasattr(page, 'find_tables'):
                page_tables = page.find_tables()
                for table_idx, table in enumerate(page_tables):
                    tables.append({
                        'page': page_num,
                        'table_index': table_idx,
                        'data': table.extract(),
                        'bbox': table.bbox
                    })

            # Extract images
            if self.extract_images:
                image_list = page.get_images()
                for img_idx, img in enumerate(image_list):
                    images.append({
                        'page': page_num,
                        'image_index': img_idx,
                        'xref': img[0]
                    })

            page_contents.append({
                'page': page_num,
                'text': page_text,
                'tables_count': len(page_tables) if 'page_tables' in locals() else 0,
                'images_count': len(image_list) if 'image_list' in locals() else 0,
                'char_count': len(page_text)
            })

        doc.close()

        return PDFContent(
            text='\n\n'.join(text_content),
            tables=tables,
            images=images,
            metadata=metadata,
            page_contents=page_contents,
            extraction_method='pymupdf'
        )

    def _extract_with_ocr(self, file_path: Path) -> PDFContent:
        """Extract content using OCR."""
        logger.info(f"Using OCR to extract text from {file_path}")

        # Convert PDF to images
        images = convert_from_path(file_path, dpi=self.dpi)

        text_content = []
        page_contents = []

        for page_num, image in enumerate(images, 1):
            # Perform OCR on each page
            page_text = pytesseract.image_to_string(
                image,
                lang=self.ocr_language
            )
            text_content.append(page_text)

            page_contents.append({
                'page': page_num,
                'text': page_text,
                'char_count': len(page_text),
                'extraction_method': 'ocr'
            })

        return PDFContent(
            text='\n\n'.join(text_content),
            tables=[],  # OCR doesn't extract structured tables
            images=[],  # Images are converted to text
            metadata={'pages': len(images), 'ocr_used': True},
            page_contents=page_contents,
            extraction_method='ocr'
        )

    def extract_text_with_layout(self, file_path: Path) -> str:
        """
        Extract text while preserving layout structure.

        Args:
            file_path: Path to PDF file

        Returns:
            Text with preserved layout
        """
        if PYMUPDF_AVAILABLE:
            doc = fitz.open(file_path)
            text = []

            for page in doc:
                # Extract text with layout preservation
                text.append(page.get_text("text", sort=True))

            doc.close()
            return '\n\n'.join(text)
        else:
            # Fallback to pdfplumber
            with pdfplumber.open(file_path) as pdf:
                text = []
                for page in pdf.pages:
                    page_text = page.extract_text_simple(
                        x_tolerance=3,
                        y_tolerance=3
                    )
                    if page_text:
                        text.append(page_text)
                return '\n\n'.join(text)

    def is_scanned_pdf(self, file_path: Path) -> bool:
        """
        Check if a PDF is scanned (image-based) or has extractable text.

        Args:
            file_path: Path to PDF file

        Returns:
            True if PDF appears to be scanned
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                # Check first few pages for text
                pages_to_check = min(3, len(pdf.pages))
                total_chars = 0

                for i in range(pages_to_check):
                    text = pdf.pages[i].extract_text() or ""
                    total_chars += len(text.strip())

                # If very little text is found, likely scanned
                return total_chars < 100
        except:
            return True

    def extract_pdf_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from PDF.

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary of metadata
        """
        metadata = {}

        try:
            with pdfplumber.open(file_path) as pdf:
                if pdf.metadata:
                    metadata.update(pdf.metadata)

                # Add additional info
                metadata['pages'] = len(pdf.pages)
                metadata['file_size'] = file_path.stat().st_size
                metadata['is_scanned'] = self.is_scanned_pdf(file_path)

                # Get page dimensions
                if pdf.pages:
                    first_page = pdf.pages[0]
                    metadata['page_width'] = first_page.width
                    metadata['page_height'] = first_page.height
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")

        return metadata


def process_pdf_directory(
    directory_path: Union[str, Path],
    output_dir: Union[str, Path],
    use_ocr: bool = True,
    recursive: bool = True
) -> Dict[str, Any]:
    """
    Process all PDFs in a directory.

    Args:
        directory_path: Directory containing PDFs
        output_dir: Directory for processed output
        use_ocr: Enable OCR for scanned PDFs
        recursive: Process subdirectories

    Returns:
        Processing statistics
    """
    directory_path = Path(directory_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize processor
    processor = PDFProcessor(use_ocr=use_ocr)

    # Find all PDFs
    if recursive:
        pdf_files = list(directory_path.rglob("*.pdf"))
    else:
        pdf_files = list(directory_path.glob("*.pdf"))

    logger.info(f"Found {len(pdf_files)} PDF files")

    # Process statistics
    stats = {
        'total_files': len(pdf_files),
        'processed': 0,
        'failed': 0,
        'scanned': 0,
        'total_pages': 0,
        'total_tables': 0,
        'total_images': 0
    }

    # Process each PDF
    for pdf_file in pdf_files:
        try:
            logger.info(f"Processing: {pdf_file.name}")

            # Check if scanned
            if processor.is_scanned_pdf(pdf_file):
                stats['scanned'] += 1
                logger.info(f"  -> Detected as scanned PDF")

            # Process PDF
            content = processor.process_pdf(pdf_file)

            # Update statistics
            stats['processed'] += 1
            stats['total_pages'] += content.metadata.get('pages', 0)
            stats['total_tables'] += len(content.tables)
            stats['total_images'] += len(content.images)

            # Save extracted content
            output_file = output_dir / f"{pdf_file.stem}_extracted.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content.text)

            logger.info(f"  -> Saved to: {output_file}")

        except Exception as e:
            logger.error(f"Failed to process {pdf_file}: {e}")
            stats['failed'] += 1

    # Log summary
    logger.info("\n" + "="*50)
    logger.info("Processing Complete!")
    logger.info(f"Total files: {stats['total_files']}")
    logger.info(f"Successfully processed: {stats['processed']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Scanned PDFs: {stats['scanned']}")
    logger.info(f"Total pages: {stats['total_pages']}")
    logger.info(f"Total tables extracted: {stats['total_tables']}")
    logger.info(f"Total images found: {stats['total_images']}")

    return stats