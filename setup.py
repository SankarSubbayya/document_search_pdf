#!/usr/bin/env python3
"""
Automated setup script for PubMed Semantic Search System.

This script handles:
1. Checking and downloading the PubMed dataset if not available
2. Setting up Docker and Qdrant if not running
3. Creating embeddings and indexing documents

Run this after cloning the repository to set everything up automatically.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
import json
import yaml
import shutil

# Add src to path
sys.path.append(str(Path(__file__).parent))

# Color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_status(message, status="info"):
    """Print colored status messages."""
    if status == "success":
        print(f"{GREEN}✓{RESET} {message}")
    elif status == "error":
        print(f"{RED}✗{RESET} {message}")
    elif status == "warning":
        print(f"{YELLOW}⚠{RESET} {message}")
    elif status == "info":
        print(f"{BLUE}ℹ{RESET} {message}")
    elif status == "header":
        print(f"\n{BOLD}{message}{RESET}")
        print("=" * len(message))

def run_command(command, capture_output=False, check=True):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=capture_output,
            text=True,
            check=check
        )
        return result.stdout if capture_output else True
    except subprocess.CalledProcessError as e:
        if check:
            print_status(f"Command failed: {command}", "error")
            print(e.stderr if hasattr(e, 'stderr') else str(e))
        return None

def check_prerequisites():
    """Check if required software is installed."""
    print_status("Checking Prerequisites", "header")

    prerequisites = {
        "Python": "python3 --version",
        "Docker": "docker --version",
        "Git": "git --version"
    }

    all_good = True
    for name, command in prerequisites.items():
        result = run_command(command, capture_output=True, check=False)
        if result:
            print_status(f"{name} is installed", "success")
        else:
            print_status(f"{name} is not installed - please install it first", "error")
            all_good = False

    return all_good

def check_docker_running():
    """Check if Docker daemon is running."""
    print_status("Checking Docker Status", "header")

    result = run_command("docker ps", capture_output=True, check=False)
    if result is not None:
        print_status("Docker is running", "success")
        return True
    else:
        print_status("Docker is not running", "warning")

        # Try to start Docker Desktop on macOS
        if sys.platform == "darwin":
            print_status("Attempting to start Docker Desktop on macOS...", "info")
            run_command("open -a Docker", check=False)

            # Wait for Docker to start
            for i in range(30):
                time.sleep(2)
                if run_command("docker ps", capture_output=True, check=False):
                    print_status("Docker started successfully", "success")
                    return True
                print(".", end="", flush=True)
            print()

        print_status("Please start Docker manually and run this script again", "error")
        return False

def setup_qdrant():
    """Set up Qdrant in Docker container."""
    print_status("Setting up Qdrant Vector Database", "header")

    # Check if Qdrant is already running
    result = run_command("docker ps | grep qdrant", capture_output=True, check=False)
    if result:
        print_status("Qdrant container found, checking health...", "info")

        # Check if Qdrant API is healthy
        health_check = run_command(
            'curl -s -f http://localhost:6333/',
            capture_output=True,
            check=False
        )
        if health_check:
            print_status("Qdrant container is healthy", "success")
            return True
        else:
            print_status("Qdrant container is unhealthy, restarting...", "warning")
            run_command("docker restart qdrant", check=False)

            # Wait for restart
            for i in range(15):
                time.sleep(2)
                health_check = run_command(
                    'curl -s -f http://localhost:6333/health',
                    capture_output=True,
                    check=False
                )
                if health_check:
                    print_status("Qdrant restarted successfully", "success")
                    return True
                print(".", end="", flush=True)
            print()

            print_status("Failed to restart Qdrant, removing container...", "warning")
            run_command("docker stop qdrant", check=False)
            run_command("docker rm qdrant", check=False)

    # Check if docker-compose.yml exists
    if not Path("docker-compose.yml").exists():
        print_status("Creating docker-compose.yml", "info")
        docker_compose_content = """version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    ports:
      - "6333:6333"  # REST API
      - "6334:6334"  # gRPC API
    volumes:
      - ./qdrant_storage:/qdrant/storage:z
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
"""
        with open("docker-compose.yml", "w") as f:
            f.write(docker_compose_content)

    # Start Qdrant using docker-compose
    print_status("Starting Qdrant container...", "info")
    if run_command("docker-compose up -d qdrant"):
        # Wait for Qdrant to be healthy
        print_status("Waiting for Qdrant to be ready...", "info")
        for i in range(30):
            time.sleep(2)
            result = run_command(
                'curl -s -f http://localhost:6333/health',
                capture_output=True,
                check=False
            )
            if result:
                print_status("Qdrant is ready", "success")
                return True
            print(".", end="", flush=True)
        print()

    print_status("Failed to start Qdrant", "error")
    return False

def check_and_download_data():
    """Check if PubMed data exists, download if not."""
    print_status("Checking PubMed Dataset", "header")

    # Load configuration
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    # Check if data directory exists
    data_path = Path(config['paths']['datasets']['pubmed_200k_rct'])
    processed_path = Path(config['paths']['documents']['processed'])

    # Check if processed data exists
    processed_file = processed_path / "pubmed_200k_rct_processed.jsonl"
    if processed_file.exists():
        size_mb = processed_file.stat().st_size / (1024 * 1024)
        print_status(f"Processed data exists ({size_mb:.1f} MB)", "success")

        # Count lines in processed file
        with open(processed_file, 'r') as f:
            line_count = sum(1 for _ in f)
        print_status(f"Found {line_count:,} processed documents", "info")

        if line_count > 0:
            return True

    # Check if raw data exists
    if data_path.exists() and (data_path / "train.txt").exists():
        print_status("Raw data exists but not processed", "warning")
        should_process = input("Would you like to process the raw data? (y/n): ")
        if should_process.lower() == 'y':
            return process_raw_data(data_path, processed_path)

    # No data found - download it
    print_status("Dataset not found. Downloading...", "warning")

    # Ask user for dataset size preference
    print("\nChoose dataset size:")
    print("1. Small sample (1,000 documents) - Quick setup for testing")
    print("2. Medium (10,000 documents) - Good for development")
    print("3. Full 20k subset (20,000 documents) - Smaller complete dataset")
    print("4. Full 200k dataset (195,654 documents) - Complete dataset (1.5GB)")

    choice = input("\nEnter your choice (1-4) [default: 1]: ").strip() or "1"

    size_map = {
        "1": ("20k", 1000),
        "2": ("20k", 10000),
        "3": ("20k", None),
        "4": ("200k", None)
    }

    if choice not in size_map:
        print_status("Invalid choice, using small sample", "warning")
        choice = "1"

    dataset_size, max_docs = size_map[choice]

    # Download using the download_and_prepare script
    print_status(f"Downloading {dataset_size} dataset...", "info")

    cmd = f"python src/data/download_and_prepare.py --size {dataset_size}"
    if max_docs:
        cmd += f" --max-documents {max_docs}"

    if run_command(cmd):
        print_status("Dataset downloaded and processed successfully", "success")
        return True
    else:
        # Try alternative download method with kagglehub
        print_status("Trying alternative download method...", "info")
        if run_command("python src/data/kagglehub_downloader.py"):
            return process_raw_data(data_path, processed_path)

    return False

def process_raw_data(raw_path, processed_path):
    """Process raw data into JSONL format."""
    print_status("Processing raw data...", "info")

    cmd = f"python src/data/pubmed_processor_tsv.py --dataset-dir {raw_path} --output-dir {processed_path}"

    if run_command(cmd):
        print_status("Data processed successfully", "success")
        return True
    else:
        print_status("Failed to process data", "error")
        return False

def check_qdrant_collection():
    """Check if Qdrant collection exists and has data."""
    print_status("Checking Qdrant Collection", "header")

    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host="localhost", port=6333, timeout=5.0)

        # Check if collection exists
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if "pubmed_documents" in collection_names:
            info = client.get_collection("pubmed_documents")
            points_count = info.points_count
            print_status(f"Collection exists with {points_count:,} documents", "success")

            if points_count > 0:
                return True
            else:
                print_status("Collection is empty, needs indexing", "warning")
        else:
            print_status("Collection does not exist", "warning")
    except Exception as e:
        print_status(f"Could not connect to Qdrant: {str(e)}", "warning")

    return False

def create_embeddings_and_index():
    """Create embeddings and index documents into Qdrant."""
    print_status("Creating Embeddings and Indexing", "header")

    # Load configuration
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    processed_file = Path(config['paths']['documents']['processed']) / "pubmed_200k_rct_processed.jsonl"

    if not processed_file.exists():
        print_status("No processed data found to index", "error")
        return False

    # Count documents
    with open(processed_file, 'r') as f:
        doc_count = sum(1 for _ in f)

    print_status(f"Found {doc_count:,} documents to index", "info")

    # Ask user how many to index
    if doc_count > 10000:
        print("\nHow many documents would you like to index?")
        print(f"1. Small sample (1,000) - Quick, ~2 seconds")
        print(f"2. Medium (10,000) - ~20 seconds")
        print(f"3. Large (50,000) - ~2 minutes")
        print(f"4. All ({doc_count:,}) - ~6 minutes")

        choice = input("\nEnter your choice (1-4) [default: 1]: ").strip() or "1"

        max_docs_map = {
            "1": 1000,
            "2": 10000,
            "3": 50000,
            "4": None
        }

        max_docs = max_docs_map.get(choice, 1000)
    else:
        max_docs = None

    # Run indexing
    print_status("Starting indexing process...", "info")
    print_status("This will download the embedding model on first run (~25MB)", "info")

    cmd = "python scripts/index_pubmed_data.py --recreate"
    if max_docs:
        cmd += f" --max-documents {max_docs}"

    if run_command(cmd):
        print_status(f"Successfully indexed documents", "success")
        return True
    else:
        print_status("Failed to index documents", "error")
        return False

def install_dependencies():
    """Install Python dependencies."""
    print_status("Installing Python Dependencies", "header")

    # Check if uv is available
    if run_command("uv --version", capture_output=True, check=False):
        print_status("Using uv for dependency installation", "info")
        if run_command("uv pip install -e ."):
            print_status("Dependencies installed successfully", "success")
            return True
    else:
        print_status("Using pip for dependency installation", "info")
        if run_command("pip install -e ."):
            print_status("Dependencies installed successfully", "success")
            return True

    print_status("Failed to install dependencies", "error")
    return False

def main():
    """Main setup function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Automated setup for PubMed Semantic Search System"
    )
    parser.add_argument(
        '--skip-deps',
        action='store_true',
        help='Skip dependency installation'
    )
    parser.add_argument(
        '--skip-docker',
        action='store_true',
        help='Skip Docker and Qdrant setup'
    )
    parser.add_argument(
        '--force-index',
        action='store_true',
        help='Force re-indexing even if collection exists'
    )

    args = parser.parse_args()

    print(f"{BOLD}{BLUE}")
    print("=" * 60)
    print("    PubMed Semantic Search - Automated Setup")
    print("=" * 60)
    print(f"{RESET}\n")

    # Track setup status
    setup_complete = True

    # 1. Check prerequisites
    if not check_prerequisites():
        print_status("\nPlease install missing prerequisites and run again", "error")
        return 1

    # 2. Install Python dependencies
    if not args.skip_deps:
        if not install_dependencies():
            setup_complete = False
    else:
        print_status("Skipping dependency installation", "info")

    # 3. Check and start Docker
    if not args.skip_docker:
        if not check_docker_running():
            setup_complete = False

        # 4. Setup Qdrant
        if not setup_qdrant():
            setup_complete = False
    else:
        print_status("Skipping Docker and Qdrant setup", "info")

    # 5. Check and download data
    if not check_and_download_data():
        setup_complete = False

    # 6. Check Qdrant collection and index if needed
    if not args.skip_docker:
        if args.force_index or not check_qdrant_collection():
            print_status("Need to create embeddings and index documents", "info")
            if not create_embeddings_and_index():
                setup_complete = False

    # Final status
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    if setup_complete:
        print_status("Setup Complete!", "header")
        print(f"\n{GREEN}✓ All components are ready!{RESET}\n")
        print("You can now run the application:")
        print(f"  {BOLD}streamlit run app.py{RESET}")
        print("\nOr use the CLI for search:")
        print(f"  {BOLD}python scripts/fast_search.py --interactive{RESET}")
        print("\nAccess Qdrant dashboard at:")
        print(f"  {BOLD}http://localhost:6333/dashboard{RESET}")
    else:
        print_status("Setup Incomplete", "header")
        print(f"\n{YELLOW}Some components need attention.{RESET}")
        print("Please fix the issues above and run setup again.")
        print("\nFor manual setup, see:")
        print(f"  {BOLD}docs/GETTING_STARTED.md{RESET}")

    print(f"\n{'=' * 60}\n")

    return 0 if setup_complete else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Setup interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Unexpected error: {str(e)}{RESET}")
        sys.exit(1)