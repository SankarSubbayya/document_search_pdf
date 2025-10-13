"""
Dataset downloader for PubMed 200k RCT dataset without Kaggle API.

This module provides functionality to download the PubMed 200k RCT dataset
from alternative sources without requiring Kaggle authentication.
"""

import os
import json
import zipfile
import tarfile
import gzip
import shutil
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
import yaml
import hashlib

logger = logging.getLogger(__name__)


class DatasetDownloader:
    """
    Handles downloading datasets from direct URLs without authentication.
    """

    # Alternative sources for PubMed 200k RCT dataset
    DATASET_SOURCES = {
        'pubmed_200k_rct': {
            'github': {
                'base_url': 'https://raw.githubusercontent.com/Franck-Dernoncourt/pubmed-rct/master/PubMed_200k_RCT/',
                'files': {
                    'train.txt': 'train.txt',
                    'dev.txt': 'dev.txt',
                    'test.txt': 'test.txt'
                }
            },
            'github_20k': {
                'base_url': 'https://raw.githubusercontent.com/Franck-Dernoncourt/pubmed-rct/master/PubMed_20k_RCT_numbers_replaced_with_at_sign/',
                'files': {
                    'train.txt': 'train.txt',
                    'dev.txt': 'dev.txt',
                    'test.txt': 'test.txt'
                }
            }
        }
    }

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the dataset downloader with configuration.

        Args:
            config_path: Path to the YAML configuration file
        """
        self.config = self._load_config(config_path)
        self.data_dir = Path(self.config['paths']['data_dir'])
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def download_file(self, url: str, dest_path: Path, chunk_size: int = 8192) -> bool:
        """
        Download a file from URL to destination path.

        Args:
            url: URL to download from
            dest_path: Destination file path
            chunk_size: Download chunk size

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Downloading from {url}")

            # Create parent directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Download with progress indication
            with urllib.request.urlopen(url) as response:
                total_size = response.headers.get('Content-Length')

                if total_size:
                    total_size = int(total_size)
                    logger.info(f"File size: {total_size / (1024*1024):.2f} MB")

                downloaded = 0
                with open(dest_path, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size and downloaded % (chunk_size * 100) == 0:
                            progress = (downloaded / total_size) * 100
                            logger.info(f"Progress: {progress:.1f}%")

            logger.info(f"Downloaded successfully to {dest_path}")
            return True

        except urllib.error.HTTPError as e:
            logger.error(f"HTTP Error {e.code}: {e.reason}")
            return False
        except Exception as e:
            logger.error(f"Download failed: {str(e)}")
            return False

    def download_pubmed_200k_rct(
        self,
        dataset_size: str = '200k',
        force_download: bool = False
    ) -> Path:
        """
        Download the PubMed RCT dataset from GitHub.

        Args:
            dataset_size: '200k' for full dataset or '20k' for smaller version
            force_download: Force re-download even if files exist

        Returns:
            Path to the downloaded dataset directory
        """
        # Determine which dataset to download
        if dataset_size == '200k':
            source_key = 'github'
            dataset_name = 'pubmed_200k_rct'
        elif dataset_size == '20k':
            source_key = 'github_20k'
            dataset_name = 'pubmed_20k_rct'
        else:
            raise ValueError(f"Invalid dataset size: {dataset_size}. Use '200k' or '20k'")

        # Create dataset directory
        dataset_dir = self.data_dir / dataset_name
        dataset_dir.mkdir(parents=True, exist_ok=True)

        # Get source configuration
        source_config = self.DATASET_SOURCES['pubmed_200k_rct'][source_key]
        base_url = source_config['base_url']
        files_to_download = source_config['files']

        # Check if already downloaded
        existing_files = [dataset_dir / fname for fname in files_to_download.keys()]
        if all(f.exists() for f in existing_files) and not force_download:
            logger.info(f"Dataset already exists at {dataset_dir}")
            self._verify_dataset_files(dataset_dir, files_to_download.keys())
            return dataset_dir

        # Download each file
        logger.info(f"Downloading PubMed {dataset_size} RCT dataset...")
        success_count = 0

        for local_name, remote_name in files_to_download.items():
            url = base_url + remote_name
            dest_path = dataset_dir / local_name

            if dest_path.exists() and not force_download:
                logger.info(f"File {local_name} already exists, skipping")
                success_count += 1
                continue

            if self.download_file(url, dest_path):
                success_count += 1
            else:
                logger.warning(f"Failed to download {local_name}")

        if success_count == len(files_to_download):
            logger.info(f"Successfully downloaded all {success_count} files")
            self._verify_dataset_files(dataset_dir, files_to_download.keys())
        else:
            logger.warning(f"Downloaded {success_count}/{len(files_to_download)} files")

        return dataset_dir

    def _verify_dataset_files(self, dataset_dir: Path, expected_files: List[str]):
        """
        Verify the downloaded dataset files.

        Args:
            dataset_dir: Path to dataset directory
            expected_files: List of expected file names
        """
        logger.info("Verifying dataset files...")

        for filename in expected_files:
            file_path = dataset_dir / filename

            if not file_path.exists():
                logger.warning(f"Missing file: {filename}")
                continue

            # Check file size and line count
            size_mb = file_path.stat().st_size / (1024 * 1024)

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)

                logger.info(f"  {filename}: {line_count:,} lines ({size_mb:.2f} MB)")

                # Verify it's valid JSON lines format
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line:
                        data = json.loads(first_line)
                        if 'sentences' in data and 'labels' in data:
                            logger.info(f"    ✓ Valid format detected")
                        else:
                            logger.warning(f"    ⚠ Unexpected format")

            except Exception as e:
                logger.error(f"Error verifying {filename}: {str(e)}")

    def download_with_fallback(
        self,
        primary_size: str = '200k',
        fallback_size: str = '20k',
        force_download: bool = False
    ) -> Path:
        """
        Try to download the primary dataset, fall back to alternative if it fails.

        Args:
            primary_size: Primary dataset size to try
            fallback_size: Fallback dataset size if primary fails
            force_download: Force re-download

        Returns:
            Path to the downloaded dataset
        """
        logger.info(f"Attempting to download {primary_size} dataset...")

        try:
            # Try primary dataset
            dataset_dir = self.download_pubmed_200k_rct(
                dataset_size=primary_size,
                force_download=force_download
            )

            # Verify we got all files
            if primary_size == '200k':
                expected_files = ['train.txt', 'dev.txt', 'test.txt']
            else:
                expected_files = ['train.txt', 'dev.txt', 'test.txt']

            if all((dataset_dir / f).exists() for f in expected_files):
                return dataset_dir

        except Exception as e:
            logger.warning(f"Failed to download {primary_size} dataset: {str(e)}")

        # Try fallback
        logger.info(f"Falling back to {fallback_size} dataset...")
        return self.download_pubmed_200k_rct(
            dataset_size=fallback_size,
            force_download=force_download
        )

    def create_sample_dataset(
        self,
        source_dir: Path,
        sample_size: int = 100,
        output_name: str = 'sample'
    ) -> Path:
        """
        Create a sample dataset for testing.

        Args:
            source_dir: Source dataset directory
            sample_size: Number of samples per split
            output_name: Name for sample dataset

        Returns:
            Path to sample dataset directory
        """
        sample_dir = self.data_dir / f'pubmed_rct_{output_name}'
        sample_dir.mkdir(parents=True, exist_ok=True)

        for filename in ['train.txt', 'dev.txt', 'test.txt']:
            source_file = source_dir / filename

            if not source_file.exists():
                continue

            dest_file = sample_dir / filename

            with open(source_file, 'r', encoding='utf-8') as f_in:
                with open(dest_file, 'w', encoding='utf-8') as f_out:
                    for i, line in enumerate(f_in):
                        if i >= sample_size:
                            break
                        f_out.write(line)

            logger.info(f"Created sample {filename} with {sample_size} entries")

        return sample_dir


def download_pubmed_dataset_direct(
    config_path: str = "config.yaml",
    dataset_size: str = '20k',
    force_download: bool = False
) -> Path:
    """
    Convenience function to download PubMed RCT dataset without Kaggle.

    Args:
        config_path: Path to configuration file
        dataset_size: '200k' for full or '20k' for smaller dataset
        force_download: Force re-download even if exists

    Returns:
        Path to the downloaded dataset
    """
    downloader = DatasetDownloader(config_path)

    # Try download with fallback
    dataset_dir = downloader.download_with_fallback(
        primary_size=dataset_size,
        fallback_size='20k' if dataset_size == '200k' else '200k',
        force_download=force_download
    )

    print("\n" + "="*50)
    print("Dataset Downloaded Successfully!")
    print("="*50)
    print(f"Location: {dataset_dir}")

    # List files
    for f in dataset_dir.glob('*.txt'):
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  - {f.name}: {size_mb:.2f} MB")

    print("="*50)

    return dataset_dir


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Download PubMed RCT dataset without Kaggle API"
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
        help='Dataset size (20k is smaller and faster to download)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-download even if dataset exists'
    )
    parser.add_argument(
        '--sample',
        type=int,
        help='Create a sample dataset with N examples per split'
    )

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Download the dataset
    try:
        dataset_path = download_pubmed_dataset_direct(
            config_path=args.config,
            dataset_size=args.size,
            force_download=args.force
        )

        # Create sample if requested
        if args.sample:
            downloader = DatasetDownloader(args.config)
            sample_path = downloader.create_sample_dataset(
                source_dir=dataset_path,
                sample_size=args.sample
            )
            print(f"\nSample dataset created at: {sample_path}")

        print(f"\nDataset ready at: {dataset_path}")
    except Exception as e:
        logger.error(f"Failed to download dataset: {str(e)}")
        exit(1)