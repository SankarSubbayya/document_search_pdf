#!/usr/bin/env python3
"""
Index PubMed data from the new location into Qdrant.
Uses paths: /Users/sankar/sankar/courses/llm/data/pubmed/
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import the existing indexer
from index_pubmed_data import PubMedIndexer, main as original_main
import argparse
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# New default paths
NEW_DATA_PATH = Path('/Users/sankar/sankar/courses/llm/data/pubmed')
PROCESSED_FILE = NEW_DATA_PATH / 'processed' / 'pubmed_200k_rct_processed.jsonl'
RAW_DATA_PATH = NEW_DATA_PATH / 'raw'


def main():
    """Main function with updated paths."""
    parser = argparse.ArgumentParser(
        description="Index PubMed data from new location into Qdrant"
    )
    parser.add_argument(
        '--input',
        type=Path,
        default=PROCESSED_FILE,
        help=f'Path to processed JSONL file (default: {PROCESSED_FILE})'
    )
    parser.add_argument(
        '--host',
        default='localhost',
        help='Qdrant host'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=6333,
        help='Qdrant port'
    )
    parser.add_argument(
        '--collection',
        default='pubmed_documents',
        help='Collection name'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for indexing'
    )
    parser.add_argument(
        '--max-documents',
        type=int,
        help='Maximum number of documents to index'
    )
    parser.add_argument(
        '--recreate',
        action='store_true',
        help='Recreate collection if it exists'
    )
    parser.add_argument(
        '--search',
        help='Test search after indexing'
    )

    args = parser.parse_args()

    # Check if input file exists
    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        logger.info(f"Looking for processed data in: {PROCESSED_FILE}")

        # Check if raw data exists
        if RAW_DATA_PATH.exists():
            raw_files = list(RAW_DATA_PATH.glob('*.txt'))
            if raw_files:
                logger.info(f"Found raw data files in {RAW_DATA_PATH}:")
                for f in raw_files:
                    logger.info(f"  - {f.name}")
                logger.info("\nTo process the raw data, run:")
                logger.info(f"  python src/data/pubmed_processor_tsv.py --dataset-dir {RAW_DATA_PATH} --output-dir {NEW_DATA_PATH / 'processed'}")
        sys.exit(1)

    print("\n" + "="*60)
    print("PubMed Data Indexer (New Location)")
    print("="*60)
    print(f"Data path: {NEW_DATA_PATH}")
    print(f"Input file: {args.input}")
    print(f"Qdrant: {args.host}:{args.port}")
    print(f"Collection: {args.collection}")
    print("="*60)

    # Create indexer
    indexer = PubMedIndexer(
        host=args.host,
        port=args.port,
        collection_name=args.collection,
        batch_size=args.batch_size
    )

    # Ensure collection exists
    indexer.ensure_collection(recreate=args.recreate)

    # Load documents
    print("\nLoading documents...")
    documents = indexer.load_documents(args.input, max_documents=args.max_documents)

    if not documents:
        logger.error("No documents to index")
        sys.exit(1)

    # Index documents
    print(f"\nIndexing {len(documents)} documents...")
    start_time = datetime.now()

    num_indexed = indexer.index_documents(documents, show_progress=True)

    elapsed_time = (datetime.now() - start_time).total_seconds()
    docs_per_sec = num_indexed / elapsed_time if elapsed_time > 0 else 0

    # Get collection info
    info = indexer.get_collection_info()

    print("\n" + "="*60)
    print("Indexing Complete!")
    print("="*60)
    print(f"Documents indexed: {num_indexed}")
    print(f"Time elapsed: {elapsed_time:.2f} seconds")
    print(f"Speed: {docs_per_sec:.1f} docs/second")
    print(f"Collection points: {info['points_count']}")
    print(f"Collection status: {info['status']}")
    print("="*60)

    # Test search if requested
    if args.search:
        print(f"\nTesting search with query: '{args.search}'")
        print("-"*40)

        results = indexer.search(args.search, limit=3)

        for i, result in enumerate(results, 1):
            print(f"\n{i}. Score: {result['score']:.4f}")
            print(f"   Abstract ID: {result['abstract_id']}")
            print(f"   Labels: {', '.join(result['labels'])}")
            print(f"   Content: {result['content'][:200]}...")

        print("\n" + "="*60)

    print("\nData locations:")
    print(f"  Raw data: {RAW_DATA_PATH}")
    print(f"  Processed data: {NEW_DATA_PATH / 'processed'}")
    print("\nNext steps:")
    print("1. View collection in Qdrant dashboard: http://localhost:6333/dashboard")
    print("2. Run Streamlit app: streamlit run app.py")
    print("3. Search documents: python scripts/fast_search.py --interactive")
    print("="*60)


if __name__ == "__main__":
    main()