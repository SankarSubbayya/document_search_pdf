#!/usr/bin/env python3
"""
Main script to download and prepare the PubMed 200k RCT dataset.

This script:
1. Downloads the dataset directly from GitHub (no API key required)
2. Processes it for use in the RAG system
3. Saves it to the configured data directory
"""

import sys
import logging
from pathlib import Path
import yaml

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.data.dataset_downloader import DatasetDownloader, download_pubmed_dataset_direct
from src.data.pubmed_processor import PubMedDatasetProcessor, prepare_pubmed_for_rag

logger = logging.getLogger(__name__)


def main():
    """Main function to download and prepare PubMed 200k RCT dataset."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Download and prepare PubMed RCT dataset (no API key required)"
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--size',
        choices=['200k', '20k'],
        default='20k',
        help='Dataset size to download (20k is smaller and downloads faster)'
    )
    parser.add_argument(
        '--force-download',
        action='store_true',
        help='Force re-download even if dataset exists'
    )
    parser.add_argument(
        '--max-documents',
        type=int,
        help='Maximum number of documents to process per split (for testing)'
    )
    parser.add_argument(
        '--skip-download',
        action='store_true',
        help='Skip download and only process existing files'
    )
    parser.add_argument(
        '--skip-processing',
        action='store_true',
        help='Skip processing and only download files'
    )
    parser.add_argument(
        '--sample',
        type=int,
        help='Create a sample dataset with N examples per split for testing'
    )

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Load configuration
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    data_dir = Path(config['paths']['data_dir'])

    # Determine dataset directory based on size
    if args.size == '20k':
        dataset_name = 'pubmed_20k_rct'
    else:
        dataset_name = 'pubmed_200k_rct'

    dataset_dir = data_dir / dataset_name
    processed_dir = Path(config['paths']['documents']['processed'])

    print("\n" + "="*60)
    print(f"PubMed {args.size} RCT Dataset Setup")
    print("="*60)
    print("✓ No Kaggle API key required!")
    print("✓ Downloading directly from GitHub")
    print("="*60)

    # Step 1: Download dataset
    if not args.skip_download:
        print(f"\n[1/2] Downloading {args.size} dataset from GitHub...")
        print("-" * 40)

        try:
            downloader = DatasetDownloader(args.config)

            # Download with fallback
            dataset_path = downloader.download_with_fallback(
                primary_size=args.size,
                fallback_size='20k' if args.size == '200k' else '200k',
                force_download=args.force_download
            )

            print(f"\nDataset downloaded to: {dataset_path}")

            # List downloaded files
            for f in dataset_path.glob('*.txt'):
                size_mb = f.stat().st_size / (1024 * 1024)

                # Count lines
                with open(f, 'r', encoding='utf-8') as file:
                    line_count = sum(1 for _ in file)

                print(f"  - {f.name}: {line_count:,} lines ({size_mb:.2f} MB)")

            # Create sample if requested
            if args.sample:
                print(f"\nCreating sample dataset with {args.sample} examples per split...")
                sample_path = downloader.create_sample_dataset(
                    source_dir=dataset_path,
                    sample_size=args.sample,
                    output_name='sample'
                )
                print(f"Sample dataset created at: {sample_path}")
                # Use sample for processing
                dataset_path = sample_path

        except Exception as e:
            logger.error(f"Failed to download dataset: {str(e)}")
            print("\n" + "!"*60)
            print("ERROR: Dataset download failed!")
            print(f"Error details: {str(e)}")
            print("\nPlease check your internet connection and try again.")
            print("You can also try the smaller 20k dataset with --size 20k")
            print("!"*60)
            return 1
    else:
        print("\n[1/2] Skipping download (using existing dataset)")
        dataset_path = dataset_dir

        if not dataset_path.exists():
            print(f"ERROR: Dataset directory does not exist: {dataset_path}")
            print("Please run without --skip-download to download the dataset first")
            return 1

    # Step 2: Process dataset
    if not args.skip_processing:
        print("\n[2/2] Processing dataset for RAG system...")
        print("-" * 40)

        try:
            output_file = prepare_pubmed_for_rag(
                dataset_dir=dataset_path,
                output_dir=processed_dir,
                max_documents=args.max_documents
            )

            print(f"\nProcessed dataset saved to: {output_file}")

            # Show sample of processed data
            print("\n" + "="*60)
            print("Sample Processed Documents:")
            print("-" * 40)

            import json
            with open(output_file, 'r') as f:
                for i, line in enumerate(f):
                    if i >= 2:  # Show first 2 documents
                        break

                    doc = json.loads(line)
                    print(f"\nDocument {i+1}:")
                    print(f"  ID: {doc['id']}")
                    print(f"  Source: {doc['source']}")
                    print(f"  Content Length: {len(doc['content'])} characters")
                    print(f"  Sections: {doc['metadata'].get('labels', [])}")

                    # Show first 200 characters of content
                    preview = doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content']
                    print(f"  Preview: {preview}")

        except Exception as e:
            logger.error(f"Failed to process dataset: {str(e)}")
            print(f"\nERROR: Failed to process dataset: {str(e)}")
            return 1
    else:
        print("\n[2/2] Skipping processing")
        output_file = processed_dir / f'{dataset_name}_processed.jsonl'

    # Summary
    print("\n" + "="*60)
    print("Setup Complete!")
    print("="*60)
    print("\nDataset Information:")
    print(f"  - Size: {args.size}")
    print(f"  - Location: {dataset_path}")
    print(f"  - Processed file: {output_file}")

    print("\nNext steps:")
    print("1. The dataset is ready for indexing into your RAG system")
    print("2. Use the processed file for document indexing")
    print("3. Run your document indexing pipeline to add these documents to the vector store")

    print("\nExample usage:")
    print(f"  python main.py index --input {output_file}")

    print("\nQuick test with sample data:")
    print("  python src/data/download_and_prepare.py --size 20k --sample 10")
    print("="*60)

    return 0


if __name__ == "__main__":
    sys.exit(main())