#!/usr/bin/env python3
"""Quick test to verify the application is ready to run."""

import sys
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def check_import(module_name, display_name=None):
    """Check if a module can be imported."""
    if display_name is None:
        display_name = module_name
    try:
        __import__(module_name)
        print(f"{GREEN}✅ {display_name}{RESET}")
        return True
    except ImportError as e:
        print(f"{RED}❌ {display_name}: {e}{RESET}")
        return False

def check_file(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"{GREEN}✅ {description}{RESET}")
        return True
    else:
        print(f"{RED}❌ {description} not found at {filepath}{RESET}")
        return False

def check_qdrant():
    """Check Qdrant connection."""
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host="localhost", port=6333, timeout=2)
        collections = client.get_collections()
        print(f"{GREEN}✅ Qdrant connected{RESET}")
        return True
    except Exception as e:
        print(f"{YELLOW}⚠️  Qdrant not accessible: {e}{RESET}")
        print(f"{YELLOW}   You can still browse the UI, but search won't work{RESET}")
        return False

print(f"\n{BOLD}🔍 Application Readiness Check{RESET}")
print("=" * 40)

print(f"\n{BOLD}1. Core Dependencies:{RESET}")
all_good = True
all_good &= check_import("streamlit", "Streamlit")
all_good &= check_import("pandas", "Pandas")
all_good &= check_import("plotly", "Plotly")
all_good &= check_import("qdrant_client", "Qdrant Client")
all_good &= check_import("sentence_transformers", "Sentence Transformers")

print(f"\n{BOLD}2. PDF Processing:{RESET}")
all_good &= check_import("pypdf", "PyPDF")
all_good &= check_import("pdfplumber", "PDFPlumber")
all_good &= check_import("pdf2image", "PDF2Image")

print(f"\n{BOLD}3. Application Files:{RESET}")
all_good &= check_file("apps/pdf_manager_app.py", "PDF Manager App")
all_good &= check_file("apps/streamlit_pubmed_app.py", "PubMed App")
all_good &= check_file("apps/streamlit_upload_app.py", "Upload App")

print(f"\n{BOLD}4. Configuration:{RESET}")
all_good &= check_file("config.yaml", "Main Config")
all_good &= check_file("requirements.txt", "Requirements")

print(f"\n{BOLD}5. Vector Database:{RESET}")
qdrant_ok = check_qdrant()

print("\n" + "=" * 40)
if all_good and qdrant_ok:
    print(f"{GREEN}{BOLD}✅ All systems ready! You can run the apps.{RESET}")
    print(f"\n{BOLD}Quick Start Commands:{RESET}")
    print("  ./quick_start.sh                    # Interactive launcher")
    print("  streamlit run apps/pdf_manager_app.py  # PDF Manager")
    print("  ./run_apps.sh                       # App selector")
elif all_good:
    print(f"{YELLOW}{BOLD}⚠️  Apps can run but Qdrant is not available.{RESET}")
    print(f"\nStart Qdrant with:")
    print("  docker run -p 6333:6333 qdrant/qdrant")
    print(f"\nYou can still run apps to browse the UI:")
    print("  streamlit run apps/pdf_manager_app.py")
else:
    print(f"{RED}{BOLD}❌ Some dependencies are missing.{RESET}")
    print(f"\nInstall with:")
    print("  uv sync  # or pip install -r requirements.txt")

sys.exit(0 if all_good else 1)