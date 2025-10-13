"""
Kaggle dataset downloader for PubMed 200k RCT dataset.

This module provides functionality to download and extract the PubMed 200k RCT
dataset from Kaggle and place it in the configured data directory.
"""

import os
import json
import zipfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import yaml

logger = logging.getLogger(__name__)


class KaggleDownloader:
    """
    Handles downloading datasets from Kaggle with proper authentication
    and extraction to configured directories.
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the Kaggle downloader with configuration.

        Args:
            config_path: Path to the YAML configuration file
        """
        self.config = self._load_config(config_path)
        self.data_dir = Path(self.config['paths']['data_dir'])
        self.kaggle_config = self.config.get('kaggle', {})
        self._setup_kaggle_auth()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_kaggle_auth(self):
        """
        Set up Kaggle API authentication from configuration or environment.

        The Kaggle API requires either:
        1. A kaggle.json file in ~/.kaggle/
        2. Environment variables KAGGLE_USERNAME and KAGGLE_KEY
        """
        # Check if credentials are in config
        username = self.kaggle_config.get('username')
        key = self.kaggle_config.get('api_key')

        # Fall back to environment variables
        if not username:
            username = os.environ.get('KAGGLE_USERNAME')
        if not key:
            key = os.environ.get('KAGGLE_KEY')

        # Set environment variables for kaggle API
        if username and key:
            os.environ['KAGGLE_USERNAME'] = username
            os.environ['KAGGLE_KEY'] = key
            logger.info("Kaggle API credentials configured")
        else:
            # Check if kaggle.json exists
            kaggle_json = Path.home() / '.kaggle' / 'kaggle.json'
            if not kaggle_json.exists():
                logger.warning(
                    "No Kaggle credentials found. Please either:\n"
                    "1. Set KAGGLE_USERNAME and KAGGLE_KEY environment variables\n"
                    "2. Place kaggle.json in ~/.kaggle/\n"
                    "3. Add credentials to config.yaml under 'kaggle' section"
                )

    def download_pubmed_200k_rct(
        self,
        dataset_name: str = "mathewjoseph/pubmed-200k-rct",
        extract: bool = True,
        force_download: bool = False
    ) -> Path:
        """
        Download the PubMed 200k RCT dataset from Kaggle.

        Args:
            dataset_name: Kaggle dataset identifier (owner/dataset-name)
            extract: Whether to extract ZIP files after download
            force_download: Force re-download even if files exist

        Returns:
            Path to the downloaded/extracted dataset directory
        """
        try:
            # Import kaggle API
            import kaggle
            from kaggle.api.kaggle_api_extended import KaggleApi

        except ImportError:
            logger.error(
                "Kaggle API not installed. Please run: pip install kaggle"
            )
            raise ImportError(
                "Please install kaggle package: pip install kaggle"
            )

        # Create dataset directory
        dataset_dir = self.data_dir / 'pubmed_200k_rct'
        dataset_dir.mkdir(parents=True, exist_ok=True)

        # Check if already downloaded
        if dataset_dir.exists() and any(dataset_dir.iterdir()) and not force_download:
            logger.info(f"Dataset already exists at {dataset_dir}")
            return dataset_dir

        try:
            # Initialize Kaggle API
            api = KaggleApi()
            api.authenticate()

            logger.info(f"Downloading dataset: {dataset_name}")

            # Download dataset
            api.dataset_download_files(
                dataset_name,
                path=str(dataset_dir),
                unzip=extract
            )

            logger.info(f"Dataset downloaded to {dataset_dir}")

            # List downloaded files
            self._list_dataset_files(dataset_dir)

            return dataset_dir

        except Exception as e:
            logger.error(f"Failed to download dataset: {str(e)}")
            raise

    def _list_dataset_files(self, dataset_dir: Path):
        """List all files in the downloaded dataset."""
        files = []
        for file_path in dataset_dir.rglob('*'):
            if file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                files.append({
                    'path': str(file_path.relative_to(dataset_dir)),
                    'size_mb': round(size_mb, 2)
                })

        logger.info(f"Downloaded {len(files)} files:")
        for file_info in files:
            logger.info(f"  - {file_info['path']} ({file_info['size_mb']} MB)")

    def extract_dataset_files(self, dataset_dir: Path, file_pattern: str = "*.zip"):
        """
        Extract any compressed files in the dataset directory.

        Args:
            dataset_dir: Path to the dataset directory
            file_pattern: Pattern for files to extract
        """
        zip_files = list(dataset_dir.glob(file_pattern))

        for zip_file in zip_files:
            logger.info(f"Extracting {zip_file.name}")

            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                # Extract to a subdirectory with the same name as the zip file
                extract_dir = dataset_dir / zip_file.stem
                extract_dir.mkdir(exist_ok=True)
                zip_ref.extractall(extract_dir)

            logger.info(f"Extracted to {extract_dir}")

    def prepare_dataset_for_processing(self, dataset_dir: Path) -> Dict[str, Path]:
        """
        Prepare the PubMed 200k RCT dataset for processing.

        The dataset typically contains:
        - train.txt: Training data
        - test.txt: Test data
        - dev.txt: Development/validation data

        Args:
            dataset_dir: Path to the dataset directory

        Returns:
            Dictionary mapping dataset splits to file paths
        """
        dataset_files = {}

        # Expected files in PubMed 200k RCT
        expected_files = ['train.txt', 'test.txt', 'dev.txt']

        for filename in expected_files:
            # Search for the file recursively
            file_paths = list(dataset_dir.rglob(filename))

            if file_paths:
                dataset_files[filename.split('.')[0]] = file_paths[0]
                logger.info(f"Found {filename} at {file_paths[0]}")
            else:
                logger.warning(f"Could not find {filename} in dataset")

        return dataset_files

    def load_dataset_info(self, dataset_dir: Path) -> Dict[str, Any]:
        """
        Load and return information about the downloaded dataset.

        Args:
            dataset_dir: Path to the dataset directory

        Returns:
            Dictionary containing dataset information
        """
        info = {
            'name': 'PubMed 200k RCT',
            'description': 'Sequential sentence classification dataset from PubMed abstracts',
            'location': str(dataset_dir),
            'files': {},
            'stats': {}
        }

        # Get file information
        dataset_files = self.prepare_dataset_for_processing(dataset_dir)

        for split_name, file_path in dataset_files.items():
            if file_path.exists():
                # Count lines in file
                with open(file_path, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)

                info['files'][split_name] = {
                    'path': str(file_path),
                    'size_mb': round(file_path.stat().st_size / (1024 * 1024), 2),
                    'lines': line_count
                }

        # Calculate total stats
        info['stats']['total_files'] = len(info['files'])
        info['stats']['total_size_mb'] = sum(
            f['size_mb'] for f in info['files'].values()
        )
        info['stats']['total_lines'] = sum(
            f['lines'] for f in info['files'].values()
        )

        return info


def download_pubmed_200k_rct(
    config_path: str = "config.yaml",
    force_download: bool = False
) -> Path:
    """
    Convenience function to download PubMed 200k RCT dataset.

    Args:
        config_path: Path to configuration file
        force_download: Force re-download even if exists

    Returns:
        Path to the downloaded dataset
    """
    downloader = KaggleDownloader(config_path)
    dataset_dir = downloader.download_pubmed_200k_rct(
        force_download=force_download
    )

    # Get dataset information
    info = downloader.load_dataset_info(dataset_dir)

    # Pretty print the information
    print("\n" + "="*50)
    print("Dataset Downloaded Successfully!")
    print("="*50)
    print(f"Name: {info['name']}")
    print(f"Location: {info['location']}")
    print(f"\nFiles:")
    for split_name, file_info in info['files'].items():
        print(f"  - {split_name}: {file_info['lines']:,} lines ({file_info['size_mb']} MB)")
    print(f"\nTotal: {info['stats']['total_lines']:,} lines ({info['stats']['total_size_mb']:.2f} MB)")
    print("="*50)

    return dataset_dir


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(
        description="Download PubMed 200k RCT dataset from Kaggle"
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

    # Download the dataset
    try:
        dataset_path = download_pubmed_200k_rct(
            config_path=args.config,
            force_download=args.force
        )
        print(f"\nDataset ready at: {dataset_path}")
    except Exception as e:
        logger.error(f"Failed to download dataset: {str(e)}")
        exit(1)