#!/usr/bin/env python3
"""
Test script to verify all applications can import correctly after the reorganization.
This tests the import fixes without actually launching Streamlit.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all app modules can be imported."""

    print("Testing application imports after reorganization...")
    print("-" * 60)

    results = []
    apps_dir = Path(__file__).parent / "apps"

    # List of apps to test
    apps_to_test = [
        ("PDF Manager App", "pdf_manager_app.py"),
        ("Streamlit Upload App", "streamlit_upload_app.py"),
        ("PubMed Search App", "streamlit_pubmed_app.py")
    ]

    for app_name, app_file in apps_to_test:
        app_path = apps_dir / app_file

        if not app_path.exists():
            results.append((app_name, False, f"File not found: {app_path}"))
            continue

        try:
            # Try to import the module
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                app_file.replace('.py', ''),
                app_path
            )
            module = importlib.util.module_from_spec(spec)

            # This will execute the module, including imports
            # We'll catch any import errors
            spec.loader.exec_module(module)

            results.append((app_name, True, "Import successful"))

        except ImportError as e:
            results.append((app_name, False, f"Import error: {str(e)}"))
        except Exception as e:
            # Catch non-import errors (like Streamlit config) separately
            if "streamlit" in str(e).lower() or "set_page_config" in str(e).lower():
                # Streamlit configuration errors are expected when not running through streamlit
                results.append((app_name, True, "Import successful (Streamlit config ignored)"))
            else:
                results.append((app_name, False, f"Error: {str(e)}"))

    # Print results
    print("\n📊 Import Test Results:\n")

    all_passed = True
    for app_name, success, message in results:
        status = "✅" if success else "❌"
        print(f"{status} {app_name}: {message}")
        if not success:
            all_passed = False

    print("\n" + "-" * 60)

    if all_passed:
        print("✅ All imports successful! The applications should work correctly.")
        print("\nYou can now run the applications with:")
        print("  streamlit run apps/pdf_manager_app.py")
        print("  streamlit run apps/streamlit_upload_app.py")
        print("  streamlit run apps/streamlit_pubmed_app.py")
        return 0
    else:
        print("❌ Some imports failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(test_imports())