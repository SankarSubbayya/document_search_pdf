"""
Unit tests for PDF processing functionality.
"""

import unittest
from pathlib import Path
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.processing.pdf_processor import PDFProcessor, PDFContent


class TestPDFProcessor(unittest.TestCase):
    """Test cases for PDF processor."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = PDFProcessor(
            use_ocr=False,  # Disable OCR for faster tests
            extract_tables=True,
            extract_images=False
        )
        self.test_data_dir = Path(__file__).parent / "test_data"
        self.test_data_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up after tests."""
        # Clean up any temporary files
        for file in self.test_data_dir.glob("*.pdf"):
            if file.name.startswith("test_"):
                file.unlink()

    def test_processor_initialization(self):
        """Test PDF processor initialization."""
        processor = PDFProcessor(
            use_ocr=True,
            extract_tables=True,
            extract_images=True,
            ocr_language='eng'
        )

        self.assertTrue(processor.extract_tables)
        self.assertTrue(processor.extract_images)
        self.assertEqual(processor.ocr_language, 'eng')
        self.assertEqual(processor.dpi, 300)

    @patch('src.processing.pdf_processor.pdfplumber')
    def test_extract_with_pdfplumber(self, mock_pdfplumber):
        """Test PDF extraction using pdfplumber."""
        # Mock the PDF content
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Test content from PDF"
        mock_page.extract_tables.return_value = []
        mock_pdf.pages = [mock_page]
        mock_pdf.metadata = {
            'Title': 'Test PDF',
            'Author': 'Test Author'
        }

        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            result = self.processor._extract_with_pdfplumber(tmp_path)

            self.assertIsInstance(result, PDFContent)
            self.assertEqual(result.extraction_method, 'pdfplumber')
            self.assertIn("Test content", result.text)
            self.assertEqual(result.metadata['title'], 'Test PDF')
            self.assertEqual(result.metadata['author'], 'Test Author')
        finally:
            tmp_path.unlink()

    @patch('src.processing.pdf_processor.PdfReader')
    def test_extract_with_pypdf2(self, mock_pdf_reader):
        """Test PDF extraction using PyPDF2."""
        # Mock the PDF reader
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Test content from PyPDF2"
        mock_reader.pages = [mock_page]
        mock_reader.metadata = {
            '/Title': 'Test PDF PyPDF2',
            '/Author': 'Test Author PyPDF2'
        }

        mock_pdf_reader.return_value = mock_reader

        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            result = self.processor._extract_with_pypdf2(tmp_path)

            self.assertIsInstance(result, PDFContent)
            self.assertEqual(result.extraction_method, 'pypdf2')
            self.assertIn("Test content from PyPDF2", result.text)
        finally:
            tmp_path.unlink()

    def test_is_scanned_pdf(self):
        """Test detection of scanned PDFs."""
        # Create a mock for pdfplumber
        with patch('src.processing.pdf_processor.pdfplumber') as mock_pdfplumber:
            # Test with text-based PDF (not scanned)
            mock_pdf = MagicMock()
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "This is a long text content that indicates the PDF is not scanned" * 10  # Make it longer than 100 chars
            mock_pdf.pages = [mock_page]
            mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                result = self.processor.is_scanned_pdf(tmp_path)
                self.assertFalse(result)
            finally:
                tmp_path.unlink()

            # Test with scanned PDF (little to no text)
            mock_page.extract_text.return_value = "  "  # Almost empty

            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                result = self.processor.is_scanned_pdf(tmp_path)
                self.assertTrue(result)
            finally:
                tmp_path.unlink()

    def test_extract_pdf_metadata(self):
        """Test metadata extraction from PDF."""
        with patch('src.processing.pdf_processor.pdfplumber') as mock_pdfplumber:
            mock_pdf = MagicMock()
            mock_page = MagicMock()
            mock_page.width = 612
            mock_page.height = 792
            mock_pdf.pages = [mock_page]
            mock_pdf.metadata = {
                'Title': 'Test Document',
                'Author': 'John Doe',
                'CreationDate': '2024-01-01'
            }
            mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp_path = Path(tmp.name)
                # Write some dummy content
                tmp.write(b'%PDF-1.4')

            try:
                metadata = self.processor.extract_pdf_metadata(tmp_path)

                self.assertEqual(metadata['Title'], 'Test Document')
                self.assertEqual(metadata['Author'], 'John Doe')
                self.assertEqual(metadata['pages'], 1)
                self.assertEqual(metadata['page_width'], 612)
                self.assertEqual(metadata['page_height'], 792)
                self.assertIn('file_size', metadata)
            finally:
                tmp_path.unlink()

    def test_process_pdf_with_fallback(self):
        """Test PDF processing with fallback methods."""
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = Path(tmp.name)
            # Write minimal PDF header
            tmp.write(b'%PDF-1.4\n')

        # Mock all extraction methods to simulate failures and fallback
        with patch.object(self.processor, '_extract_with_pdfplumber') as mock_pdfplumber:
            with patch.object(self.processor, '_extract_with_pypdf2') as mock_pypdf2:
                # First method fails
                mock_pdfplumber.side_effect = Exception("pdfplumber failed")

                # Second method succeeds with enough text
                mock_content = PDFContent(
                    text="Fallback extraction successful. " * 10 + "This is a long enough text to pass the validation check for meaningful content extraction from the PDF file.",
                    tables=[],
                    images=[],
                    metadata={'pages': 1},
                    page_contents=[],
                    extraction_method='pypdf2'
                )
                mock_pypdf2.return_value = mock_content

                try:
                    result = self.processor.process_pdf(tmp_path, fallback_methods=True)

                    self.assertEqual(result.extraction_method, 'pypdf2')
                    self.assertIn("Fallback extraction successful", result.text)

                    # Verify fallback was attempted
                    mock_pdfplumber.assert_called_once()
                    mock_pypdf2.assert_called_once()
                finally:
                    tmp_path.unlink()

    def test_file_not_found(self):
        """Test handling of non-existent files."""
        non_existent = Path("/path/to/non/existent/file.pdf")

        with self.assertRaises(FileNotFoundError):
            self.processor.process_pdf(non_existent)


class TestPDFContentDataclass(unittest.TestCase):
    """Test the PDFContent dataclass."""

    def test_pdf_content_creation(self):
        """Test creating PDFContent instances."""
        content = PDFContent(
            text="Sample text",
            tables=[{"data": "table1"}],
            images=[{"data": "image1"}],
            metadata={"title": "Test"},
            page_contents=[{"page": 1, "text": "Page 1"}],
            extraction_method="test_method"
        )

        self.assertEqual(content.text, "Sample text")
        self.assertEqual(len(content.tables), 1)
        self.assertEqual(len(content.images), 1)
        self.assertEqual(content.metadata["title"], "Test")
        self.assertEqual(content.extraction_method, "test_method")


if __name__ == '__main__':
    unittest.main()