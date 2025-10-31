#!/usr/bin/env python3
"""
Example of using document cleaning to remove TOC, acknowledgements, etc.

This shows how to clean documents before processing/chunking.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processing.document_cleaner import (
    DocumentCleaner,
    SmartDocumentCleaner,
    clean_document
)


def demo_basic_cleaning():
    """Demo: Basic document cleaning"""
    print("\n" + "="*80)
    print("BASIC DOCUMENT CLEANING")
    print("="*80)
    
    # Sample document with TOC and acknowledgements
    document = """
Machine Learning Guide

Table of Contents

1. Introduction ..................... 1
2. Machine Learning Basics .......... 5
   2.1 Supervised Learning .......... 7
   2.2 Unsupervised Learning ........ 12
3. Deep Learning .................... 20
4. Applications ..................... 30

Acknowledgements

I would like to thank my advisors for their guidance and support throughout
this research. Special thanks to the lab members who provided valuable feedback.

1. Introduction

Machine learning is a subset of artificial intelligence that enables systems
to learn from data. This guide covers fundamental concepts and applications.

2. Machine Learning Basics

Machine learning algorithms can be categorized into supervised and unsupervised
learning approaches. Each has its own use cases and advantages.

2.1 Supervised Learning

Supervised learning uses labeled data to train models for prediction tasks.
Common algorithms include decision trees and neural networks.
"""
    
    print(f"Original length: {len(document)} characters\n")
    
    # Clean the document
    cleaned_text, stats = clean_document(
        document,
        remove_toc=True,
        remove_acknowledgements=True,
        verbose=True
    )
    
    print(f"\n--- Cleaning Stats ---")
    print(f"Original: {stats.original_length} chars")
    print(f"Cleaned: {stats.cleaned_length} chars")
    print(f"Removed: {stats.reduction_percentage:.1f}%")
    print(f"Sections removed: {', '.join(stats.sections_removed)}")
    
    print(f"\n--- Cleaned Document ---")
    print(cleaned_text[:500])
    print("...")


def demo_smart_cleaning():
    """Demo: Smart document cleaning with better detection"""
    print("\n" + "="*80)
    print("SMART DOCUMENT CLEANING")
    print("="*80)
    
    document = """
Deep Learning Research Paper

Contents

Chapter 1: Background ............... 3
Chapter 2: Methodology .............. 15
    2.1 Architecture Design ......... 18
    2.2 Training Process ............ 22
Chapter 3: Results .................. 30
References .......................... 45

Acknowledgments

The authors are grateful to the research community for their valuable
contributions. We would like to acknowledge the funding support from XYZ.

Chapter 1: Background

Deep learning has revolutionized computer vision and natural language
processing. This chapter provides background on neural network architectures.

Neural networks consist of layers of interconnected nodes that process
information hierarchically.

Chapter 2: Methodology

Our approach uses a novel architecture combining convolutional and
recurrent layers.

References

[1] Smith et al. (2020) Deep Learning Fundamentals
[2] Jones et al. (2021) Advanced Neural Networks
"""
    
    # Use smart cleaning
    cleaner = SmartDocumentCleaner(
        remove_toc=True,
        remove_acknowledgements=True,
        remove_references=True  # Also remove references
    )
    
    cleaned_text, stats = cleaner.clean(document, verbose=True)
    
    print(f"\n--- Cleaning Stats ---")
    print(f"Removed: {stats.reduction_percentage:.1f}%")
    print(f"Sections removed: {', '.join(stats.sections_removed)}")
    
    print(f"\n--- Cleaned Document (First 400 chars) ---")
    print(cleaned_text[:400])


def demo_detect_sections():
    """Demo: Detect what sections are in a document"""
    print("\n" + "="*80)
    print("SECTION DETECTION")
    print("="*80)
    
    document = """
Research Paper Title

Table of Contents
1. Introduction
2. Related Work
3. Methods

Abstract
This paper presents a novel approach...

Acknowledgements
We thank our collaborators...

1. Introduction
Machine learning is rapidly evolving...

References
[1] Smith 2020
[2] Jones 2021

Appendix A
Additional Results
"""
    
    cleaner = DocumentCleaner()
    sections = cleaner.detect_sections(document)
    
    print("Detected sections:")
    for section_name, line_numbers in sections.items():
        print(f"  {section_name}: Found at line(s) {line_numbers}")
    
    print(f"\nTotal sections found: {len(sections)}")


def demo_with_pdf():
    """Demo: Clean a PDF document"""
    print("\n" + "="*80)
    print("CLEANING PDF DOCUMENT")
    print("="*80)
    
    # This would work with a real PDF
    print("Example: Clean a PDF before chunking\n")
    
    print("```python")
    print("""from src.processing.pdf_processor import PDFProcessor
from src.processing.document_cleaner import clean_document

# Extract PDF text
pdf_processor = PDFProcessor()
pdf_content = pdf_processor.process_pdf("research_paper.pdf")

# Clean the text (remove TOC, acknowledgements)
cleaned_text, stats = clean_document(
    pdf_content.text,
    remove_toc=True,
    remove_acknowledgements=True,
    remove_references=False,  # Keep references
    verbose=True
)

print(f"Removed {stats.reduction_percentage:.1f}% of content")
print(f"Sections removed: {stats.sections_removed}")

# Now chunk the cleaned text
from src.processing.advanced_chunking import UnifiedChunker, ChunkingStrategy

chunker = UnifiedChunker(strategy=ChunkingStrategy.CONTEXT)
chunks = chunker.chunk(cleaned_text)

print(f"Created {len(chunks)} chunks from cleaned document")
""")
    print("```")


def demo_custom_cleaning():
    """Demo: Custom cleaning configuration"""
    print("\n" + "="*80)
    print("CUSTOM CLEANING CONFIGURATION")
    print("="*80)
    
    document = """
Book Title

Table of Contents
Chapter 1 .... 1
Chapter 2 .... 20

Acknowledgments
Many thanks to...

Chapter 1: Introduction
Content here...

Appendix A
Extra material...

References
Bibliography...
"""
    
    # Create custom cleaner
    cleaner = DocumentCleaner(
        remove_toc=True,
        remove_acknowledgements=True,
        remove_references=True,
        remove_appendices=True,  # Also remove appendices
        remove_headers_footers=True
    )
    
    cleaned_text, stats = cleaner.clean(document, verbose=True)
    
    print(f"\nCleaned document length: {stats.cleaned_length} chars")
    print(f"Removed: {', '.join(stats.sections_removed)}")


def main():
    """Run all demos"""
    print("\n" + "="*80)
    print(" DOCUMENT CLEANING EXAMPLES")
    print("="*80)
    print("\nRemove TOC, acknowledgements, and other non-essential sections")
    print("before chunking for better retrieval quality!\n")
    
    try:
        demo_basic_cleaning()
        input("\nPress Enter to continue to Smart Cleaning demo...")
        
        demo_smart_cleaning()
        input("\nPress Enter to see Section Detection...")
        
        demo_detect_sections()
        input("\nPress Enter to see PDF example...")
        
        demo_with_pdf()
        input("\nPress Enter to see Custom Configuration...")
        
        demo_custom_cleaning()
        
        print("\n" + "="*80)
        print(" Demo Complete! 🎉")
        print("="*80)
        print("\nYou can now clean documents before chunking!")
        print("\nUsage:")
        print("  from src.processing.document_cleaner import clean_document")
        print("  cleaned_text, stats = clean_document(text, verbose=True)")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

