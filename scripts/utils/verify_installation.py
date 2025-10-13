#!/usr/bin/env python3
"""
Verification script for PDF Document Search System dependencies.
Run this script to check if all required packages are properly installed.
"""

import sys
import os
from importlib import import_module
from importlib.metadata import version
import subprocess

# ANSI color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}")
    print(f"{BOLD}{BLUE}{text:^60}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 60}{RESET}\n")

def check_module(module_name, display_name=None):
    """Check if a Python module is installed and get its version."""
    if display_name is None:
        display_name = module_name

    try:
        # Special handling for some modules
        if module_name == "PIL":
            import_module("PIL")
            ver = version("pillow")
        elif module_name == "cv2":
            import_module("cv2")
            ver = version("opencv-python")
        elif module_name == "sklearn":
            import_module("sklearn")
            ver = version("scikit-learn")
        else:
            import_module(module_name.replace("-", "_"))
            ver = version(module_name)

        print(f"{GREEN}✅ {display_name:<30} {ver}{RESET}")
        return True
    except (ImportError, Exception) as e:
        print(f"{RED}❌ {display_name:<30} Not installed{RESET}")
        return False

def check_system_command(command, name):
    """Check if a system command is available."""
    try:
        result = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Extract version from output (first line usually contains version)
            version_line = result.stdout.split('\n')[0] if result.stdout else result.stderr.split('\n')[0]
            print(f"{GREEN}✅ {name:<30} {version_line}{RESET}")
            return True
        else:
            print(f"{RED}❌ {name:<30} Not found{RESET}")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(f"{RED}❌ {name:<30} Not found{RESET}")
        return False

def check_docker_and_qdrant():
    """Check if Docker is running and if Qdrant is accessible."""
    print(f"\n{BOLD}Checking Docker and Qdrant:{RESET}")

    # Check Docker
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"{GREEN}✅ Docker is running{RESET}")

            # Check if Qdrant container is running
            if "qdrant" in result.stdout.lower():
                print(f"{GREEN}✅ Qdrant container is running{RESET}")
            else:
                print(f"{YELLOW}⚠️  Qdrant container not found. Run: docker run -p 6333:6333 qdrant/qdrant{RESET}")
        else:
            print(f"{YELLOW}⚠️  Docker is installed but not running{RESET}")
    except FileNotFoundError:
        print(f"{RED}❌ Docker not installed{RESET}")
    except subprocess.TimeoutExpired:
        print(f"{YELLOW}⚠️  Docker check timed out{RESET}")

def main():
    """Main verification function."""
    print_header("PDF Document Search System")
    print_header("Dependency Verification")

    print(f"{BOLD}Python Version:{RESET}")
    print(f"  {sys.version}\n")

    # Core dependencies
    print(f"{BOLD}Core Dependencies:{RESET}")
    core_deps = [
        ("streamlit", "Streamlit"),
        ("pandas", "Pandas"),
        ("numpy", "NumPy"),
        ("yaml", "PyYAML"),
        ("dotenv", "Python-Dotenv"),
    ]

    core_ok = all(check_module(mod, name) for mod, name in core_deps)

    # Vector Database and ML
    print(f"\n{BOLD}Vector Database & ML:{RESET}")
    ml_deps = [
        ("qdrant_client", "Qdrant Client"),
        ("sentence_transformers", "Sentence Transformers"),
        ("sklearn", "Scikit-learn"),
        ("scipy", "SciPy"),
    ]

    ml_ok = all(check_module(mod, name) for mod, name in ml_deps)

    # PDF Processing
    print(f"\n{BOLD}PDF Processing Libraries:{RESET}")
    pdf_deps = [
        ("pypdf", "PyPDF"),
        ("PyPDF2", "PyPDF2"),
        ("pdfplumber", "PDFPlumber"),
        ("pdf2image", "PDF2Image"),
        ("pytesseract", "PyTesseract"),
        ("PIL", "Pillow"),
    ]

    pdf_ok = all(check_module(mod, name) for mod, name in pdf_deps)

    # Optional PDF libraries
    print(f"\n{BOLD}Optional PDF Libraries:{RESET}")
    optional_pdf = [
        ("fitz", "PyMuPDF"),
        ("camelot", "Camelot-py"),
        ("tabula", "Tabula-py"),
    ]

    for mod, name in optional_pdf:
        check_module(mod, name)

    # Document Processing
    print(f"\n{BOLD}Document Processing:{RESET}")
    doc_deps = [
        ("docx", "Python-Docx"),
        ("openpyxl", "OpenPyXL"),
        ("pptx", "Python-PPTX"),
        ("ebooklib", "EbookLib"),
        ("bs4", "BeautifulSoup4"),
        ("html2text", "HTML2Text"),
    ]

    doc_ok = all(check_module(mod, name) for mod, name in doc_deps)

    # Visualization
    print(f"\n{BOLD}Visualization:{RESET}")
    viz_deps = [
        ("plotly", "Plotly"),
        ("matplotlib", "Matplotlib"),
        ("seaborn", "Seaborn"),
    ]

    viz_ok = all(check_module(mod, name) for mod, name in viz_deps)

    # LLM and AI
    print(f"\n{BOLD}LLM and AI:{RESET}")
    llm_deps = [
        ("openai", "OpenAI"),
        ("tiktoken", "Tiktoken"),
        ("langchain", "LangChain"),
        ("langchain_community", "LangChain Community"),
    ]

    llm_ok = all(check_module(mod, name) for mod, name in llm_deps)

    # System Dependencies
    print(f"\n{BOLD}System Dependencies:{RESET}")
    system_deps = [
        ("tesseract", "Tesseract OCR"),
        ("pdftotext", "Poppler (pdftotext)"),
    ]

    system_ok = all(check_system_command(cmd, name) for cmd, name in system_deps)

    # Docker and Qdrant check
    check_docker_and_qdrant()

    # Summary
    print_header("Verification Summary")

    all_core_ok = core_ok and ml_ok and pdf_ok and viz_ok

    if all_core_ok:
        print(f"{GREEN}{BOLD}✅ All core Python dependencies are installed!{RESET}")
    else:
        print(f"{RED}{BOLD}❌ Some core Python dependencies are missing.{RESET}")

    if system_ok:
        print(f"{GREEN}{BOLD}✅ All system dependencies are installed!{RESET}")
    else:
        print(f"{YELLOW}{BOLD}⚠️  Some system dependencies are missing.{RESET}")
        print(f"{YELLOW}   Install them based on your OS:{RESET}")
        print(f"{YELLOW}   macOS: brew install tesseract poppler{RESET}")
        print(f"{YELLOW}   Ubuntu: sudo apt-get install tesseract-ocr poppler-utils{RESET}")

    print(f"\n{BOLD}Installation Commands:{RESET}")
    if not all_core_ok:
        print(f"  {BLUE}# Using UV (recommended):{RESET}")
        print(f"  uv sync")
        print(f"\n  {BLUE}# Using pip:{RESET}")
        print(f"  pip install -r requirements.txt")
        print(f"\n  {BLUE}# Using pip with pyproject.toml:{RESET}")
        print(f"  pip install -e .")

    print(f"\n{BOLD}Next Steps:{RESET}")
    print(f"  1. Start Qdrant: {BLUE}docker run -p 6333:6333 qdrant/qdrant{RESET}")
    print(f"  2. Run the app: {BLUE}streamlit run pdf_manager_app.py{RESET}")
    print(f"  3. Or use the script: {BLUE}./run_pdf_manager.sh{RESET}")

    print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}\n")

if __name__ == "__main__":
    main()