#!/usr/bin/env python3
"""
Test script to verify the PubMed Semantic Search setup.

This script checks:
1. Dependencies are installed
2. Docker and Qdrant are running
3. Data is available
4. Search functionality works
"""

import sys
import json
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
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
    else:
        print(f"  {message}")


def test_imports():
    """Test if required packages can be imported."""
    print(f"\n{BOLD}Testing Python Dependencies:{RESET}")

    required_packages = [
        "qdrant_client",
        "sentence_transformers",
        "streamlit",
        "yaml",
        "pandas",
        "numpy",
        "plotly"
    ]

    all_good = True
    for package in required_packages:
        try:
            __import__(package)
            print_status(f"{package} imported successfully", "success")
        except ImportError:
            print_status(f"{package} not found", "error")
            all_good = False

    return all_good


def test_docker_qdrant():
    """Test Docker and Qdrant connectivity."""
    print(f"\n{BOLD}Testing Docker & Qdrant:{RESET}")

    import subprocess

    # Check Docker
    try:
        result = subprocess.run(
            "docker ps | grep qdrant",
            shell=True,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            print_status("Docker container 'qdrant' is running", "success")
        else:
            print_status("Qdrant container not found", "error")
            return False
    except Exception as e:
        print_status(f"Docker check failed: {e}", "error")
        return False

    # Check Qdrant API
    try:
        import requests
        response = requests.get("http://localhost:6333/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            version = data.get('version', 'unknown')
            print_status(f"Qdrant API is responding (version {version})", "success")
        else:
            print_status(f"Qdrant API returned status {response.status_code}", "error")
            return False
    except Exception as e:
        print_status(f"Qdrant API check failed: {e}", "error")
        return False

    # Check collection
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host="localhost", port=6333, timeout=5.0)

        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if "pubmed_documents" in collection_names:
            info = client.get_collection("pubmed_documents")
            print_status(f"Collection 'pubmed_documents' exists with {info.points_count:,} documents", "success")

            if info.points_count == 0:
                print_status("Collection is empty - run indexing", "warning")
                return False
        else:
            print_status("Collection 'pubmed_documents' not found - run indexing", "warning")
            return False

    except Exception as e:
        print_status(f"Collection check failed: {e}", "error")
        return False

    return True


def test_data():
    """Test if data files exist."""
    print(f"\n{BOLD}Testing Data Files:{RESET}")

    import yaml

    # Load config
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    # Check processed data
    processed_dir = Path(config['paths']['documents']['processed'])
    processed_file = processed_dir / "pubmed_200k_rct_processed.jsonl"

    if processed_file.exists():
        size_mb = processed_file.stat().st_size / (1024 * 1024)

        # Count lines
        with open(processed_file, 'r') as f:
            line_count = sum(1 for _ in f)

        print_status(f"Processed data exists: {line_count:,} documents ({size_mb:.1f} MB)", "success")
        return True
    else:
        print_status("Processed data not found - run data download", "error")
        return False


def test_search():
    """Test search functionality."""
    print(f"\n{BOLD}Testing Search Functionality:{RESET}")

    try:
        from sentence_transformers import SentenceTransformer
        from qdrant_client import QdrantClient

        # Initialize
        print_status("Loading embedding model...")
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        client = QdrantClient(host="localhost", port=6333, timeout=5.0)

        # Test query
        query = "diabetes treatment"
        print_status(f"Testing search with query: '{query}'")

        # Create embedding
        query_embedding = model.encode(query, convert_to_numpy=True, normalize_embeddings=True)

        # Search
        from qdrant_client.models import NamedVector
        results = client.query_points(
            collection_name="pubmed_documents",
            query=query_embedding.tolist(),
            limit=3
        ).points

        if results:
            print_status(f"Search returned {len(results)} results", "success")

            # Show top result
            top_result = results[0]
            print_status(f"Top result score: {top_result.score:.4f}")

            # Show snippet
            content = top_result.payload.get('content', '')[:200]
            print_status(f"Content preview: {content}...")

            return True
        else:
            print_status("No search results found", "warning")
            return False

    except Exception as e:
        print_status(f"Search test failed: {e}", "error")
        return False


def main():
    """Run all tests."""
    print(f"{BOLD}{BOLD}")
    print("=" * 60)
    print("    PubMed Semantic Search - System Test")
    print("=" * 60)
    print(f"{RESET}")

    all_tests_passed = True

    # Run tests
    if not test_imports():
        all_tests_passed = False
        print_status("\n→ Fix: Run 'pip install -e .' or 'python setup.py'", "warning")

    if not test_docker_qdrant():
        all_tests_passed = False
        print_status("\n→ Fix: Run 'docker-compose up -d' or 'python setup.py'", "warning")

    if not test_data():
        all_tests_passed = False
        print_status("\n→ Fix: Run 'python setup.py' to download and process data", "warning")

    if test_docker_qdrant() and test_data():
        if not test_search():
            all_tests_passed = False
            print_status("\n→ Fix: Run 'python scripts/index_pubmed_data.py'", "warning")

    # Final status
    print(f"\n{'=' * 60}")

    if all_tests_passed:
        print(f"{GREEN}{BOLD}✓ All tests passed!{RESET}")
        print(f"\nYour system is ready. Run:")
        print(f"  {BOLD}streamlit run app.py{RESET}")
        print(f"\nOr use the CLI:")
        print(f"  {BOLD}python scripts/fast_search.py --interactive{RESET}")
    else:
        print(f"{YELLOW}{BOLD}⚠ Some tests failed{RESET}")
        print(f"\nRun the setup script to fix issues:")
        print(f"  {BOLD}python setup.py{RESET}")

    print(f"{'=' * 60}\n")

    return 0 if all_tests_passed else 1


if __name__ == "__main__":
    sys.exit(main())