"""
Download PubMed 200k RCT dataset using kagglehub (no API key required).

This module uses kagglehub which handles authentication automatically
and doesn't require manual API key configuration.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
import json

logger = logging.getLogger(__name__)


class KaggleHubDownloader:
    """
    Download datasets using kagglehub - no API key configuration needed.
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the downloader with configuration.

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

    def download_pubmed_200k_rct(self, force_download: bool = False) -> Path:
        """
        Download the PubMed 200k RCT dataset using kagglehub.

        Args:
            force_download: Force re-download even if dataset exists

        Returns:
            Path to the dataset directory
        """
        try:
            import kagglehub
        except ImportError:
            logger.error("kagglehub not installed. Please run: pip install kagglehub")
            raise ImportError("Please install kagglehub: pip install kagglehub")

        # Target directory for the dataset
        target_dir = self.data_dir / 'pubmed_200k_rct'

        # Check if already exists
        if target_dir.exists() and any(target_dir.iterdir()) and not force_download:
            logger.info(f"Dataset already exists at {target_dir}")
            self._verify_dataset(target_dir)
            return target_dir

        logger.info("Downloading PubMed 200k RCT dataset using kagglehub...")
        logger.info("This may take a few minutes on first download...")

        try:
            # Download using kagglehub - note the corrected dataset name
            # The dataset name should be "mathewjoseph/pubmed-200k-rct" not "matthewjansen/pubmed-200k-rtc"
            downloaded_path = kagglehub.dataset_download("mathewjoseph/pubmed-200k-rct")

            logger.info(f"Downloaded to kagglehub cache: {downloaded_path}")

            # Copy to our data directory
            target_dir.mkdir(parents=True, exist_ok=True)

            # Copy all files from the downloaded directory
            downloaded_path = Path(downloaded_path)
            for file_path in downloaded_path.glob('*'):
                dest_path = target_dir / file_path.name
                logger.info(f"Copying {file_path.name} to {dest_path}")
                shutil.copy2(file_path, dest_path)

            logger.info(f"Dataset copied to {target_dir}")
            self._verify_dataset(target_dir)

            return target_dir

        except Exception as e:
            logger.error(f"Failed to download dataset: {str(e)}")

            # Try alternative dataset name if the first one fails
            try:
                logger.info("Trying alternative dataset name...")
                downloaded_path = kagglehub.dataset_download("matthewjansen/pubmed-200k-rtc")

                logger.info(f"Downloaded to kagglehub cache: {downloaded_path}")

                # Copy to our data directory
                target_dir.mkdir(parents=True, exist_ok=True)

                # Copy all files from the downloaded directory
                downloaded_path = Path(downloaded_path)
                for file_path in downloaded_path.glob('*'):
                    dest_path = target_dir / file_path.name
                    logger.info(f"Copying {file_path.name} to {dest_path}")
                    shutil.copy2(file_path, dest_path)

                logger.info(f"Dataset copied to {target_dir}")
                self._verify_dataset(target_dir)

                return target_dir

            except Exception as e2:
                logger.error(f"Alternative download also failed: {str(e2)}")
                raise

    def _verify_dataset(self, dataset_dir: Path):
        """
        Verify the downloaded dataset files.

        Args:
            dataset_dir: Path to the dataset directory
        """
        logger.info("Verifying dataset files...")

        expected_files = ['train.txt', 'dev.txt', 'test.txt']
        found_files = []

        for file_name in dataset_dir.glob('*.txt'):
            size_mb = file_name.stat().st_size / (1024 * 1024)

            # Count lines and verify format
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    line_count = 0
                    first_line = None
                    for i, line in enumerate(f):
                        if i == 0:
                            first_line = line.strip()
                        line_count += 1

                    # Verify JSON format
                    if first_line:
                        data = json.loads(first_line)
                        has_sentences = 'sentences' in data
                        has_labels = 'labels' in data

                        logger.info(
                            f"  {file_name.name}: {line_count:,} lines ({size_mb:.2f} MB) "
                            f"- Valid format: {has_sentences and has_labels}"
                        )
                    else:
                        logger.warning(f"  {file_name.name}: Empty file")

                found_files.append(file_name.name)

            except Exception as e:
                logger.error(f"Error verifying {file_name.name}: {str(e)}")

        # Check if we have all expected files
        for expected in expected_files:
            if expected not in [f.name for f in dataset_dir.glob('*.txt')]:
                logger.warning(f"Missing expected file: {expected}")

        logger.info(f"Found {len(found_files)} dataset files")


def download_pubmed_200k_with_kagglehub(
    config_path: str = "config.yaml",
    force_download: bool = False
) -> Path:
    """
    Convenience function to download PubMed 200k RCT using kagglehub.

    Args:
        config_path: Path to configuration file
        force_download: Force re-download even if exists

    Returns:
        Path to the downloaded dataset
    """
    downloader = KaggleHubDownloader(config_path)
    dataset_path = downloader.download_pubmed_200k_rct(force_download)

    print("\n" + "="*50)
    print("Dataset Downloaded Successfully!")
    print("="*50)
    print(f"Location: {dataset_path}")
    print("\nFiles:")
    for f in dataset_path.glob('*.txt'):
        size_mb = f.stat().st_size / (1024 * 1024)
        with open(f, 'r') as file:
            lines = sum(1 for _ in file)
        print(f"  - {f.name}: {lines:,} lines ({size_mb:.2f} MB)")
    print("="*50)

    return dataset_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Download PubMed 200k RCT dataset using kagglehub (no API key needed)"
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-download even if dataset exists'
    )

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        dataset_path = download_pubmed_200k_with_kagglehub(
            config_path=args.config,
            force_download=args.force
        )
        print(f"\nDataset ready for processing at: {dataset_path}")
        print("\nNext step: Process the dataset for your RAG system:")
        print(f"python src/data/download_and_prepare.py --skip-download")
    except Exception as e:
        logger.error(f"Failed to download dataset: {str(e)}")
        print("\nPlease install kagglehub first:")
        print("pip install kagglehub")
        exit(1)