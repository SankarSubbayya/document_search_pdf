#!/usr/bin/env python3
"""
Verify all paths are correctly configured after data migration.
"""

import sys
from pathlib import Path
import yaml
import json

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def check_path(path: Path, description: str) -> bool:
    """Check if a path exists and report status."""
    if path.exists():
        if path.is_file():
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"{GREEN}✓{RESET} {description}: {path} ({size_mb:.1f} MB)")
        else:
            file_count = len(list(path.glob('*')))
            print(f"{GREEN}✓{RESET} {description}: {path} ({file_count} items)")
        return True
    else:
        print(f"{RED}✗{RESET} {description}: {path} (NOT FOUND)")
        return False

def main():
    """Main verification function."""
    print("\n" + "="*60)
    print("Path Verification for PubMed Data Migration")
    print("="*60)

    # Load configuration
    config_path = Path('config.yaml')
    if not config_path.exists():
        print(f"{RED}Error: config.yaml not found{RESET}")
        return 1

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    print("\n1. Configuration File Settings:")
    print("-" * 40)

    # Check configured paths
    processed_path = Path(config['paths']['documents']['processed'])
    raw_path = Path(config['paths']['datasets']['pubmed_200k_rct'])

    print(f"  Processed dir in config: {processed_path}")
    print(f"  Raw data dir in config: {raw_path}")

    print("\n2. New Data Location:")
    print("-" * 40)

    # Check new location
    new_base = Path('/Users/sankar/sankar/courses/llm/data/pubmed')
    all_good = True

    all_good &= check_path(new_base, "Base directory")
    all_good &= check_path(new_base / 'raw', "Raw data directory")
    all_good &= check_path(new_base / 'raw' / 'train.txt', "Training file")
    all_good &= check_path(new_base / 'raw' / 'dev.txt', "Dev file")
    all_good &= check_path(new_base / 'raw' / 'test.txt', "Test file")
    all_good &= check_path(new_base / 'processed', "Processed directory")
    all_good &= check_path(
        new_base / 'processed' / 'pubmed_200k_rct_processed.jsonl',
        "Processed JSONL"
    )

    print("\n3. Symlink Check:")
    print("-" * 40)

    symlink = Path('data/pubmed')
    if symlink.is_symlink():
        target = symlink.resolve()
        print(f"{GREEN}✓{RESET} Symlink exists: data/pubmed -> {target}")
        all_good &= target == new_base
    else:
        print(f"{RED}✗{RESET} Symlink not found: data/pubmed")
        all_good = False

    print("\n4. Old Directories (should be removed):")
    print("-" * 40)

    old_dirs = [
        'data/processed',
        'data/pubmed_200k_rct',
        'data/pubmed_20k_rct',
        'data/pubmed_rct_sample'
    ]

    for old_dir in old_dirs:
        path = Path(old_dir)
        if path.exists():
            print(f"{YELLOW}⚠{RESET}  Still exists: {old_dir}")
            all_good = False
        else:
            print(f"{GREEN}✓{RESET} Removed: {old_dir}")

    print("\n5. Script Default Paths:")
    print("-" * 40)

    # Check script defaults
    scripts_to_check = [
        ('scripts/index_pubmed_data.py', '/Users/sankar/sankar/courses/llm/data/pubmed/processed/pubmed_200k_rct_processed.jsonl'),
        ('scripts/index_pubmed_new.py', '/Users/sankar/sankar/courses/llm/data/pubmed/processed/pubmed_200k_rct_processed.jsonl'),
        ('src/data/pubmed_processor_tsv.py', '/Users/sankar/sankar/courses/llm/data/pubmed/raw')
    ]

    for script, expected_path in scripts_to_check:
        script_path = Path(script)
        if script_path.exists():
            with open(script_path, 'r') as f:
                content = f.read()
                if expected_path in content:
                    print(f"{GREEN}✓{RESET} {script}: Uses new path")
                else:
                    print(f"{YELLOW}⚠{RESET}  {script}: May use old path")
        else:
            print(f"{YELLOW}⚠{RESET}  {script}: Not found")

    print("\n" + "="*60)
    if all_good:
        print(f"{GREEN}✅ All paths verified successfully!{RESET}")
        print("\nYou can now:")
        print("1. Index data: uv run python scripts/index_pubmed_data.py")
        print("2. Search data: uv run python scripts/fast_search.py --interactive")
        print("3. Run Streamlit: streamlit run app.py")
    else:
        print(f"{YELLOW}⚠ Some issues found. Please review above.{RESET}")
    print("="*60)

    return 0 if all_good else 1


if __name__ == "__main__":
    sys.exit(main())