# Testing with UV - Fast Python Testing Guide

## 🚀 Why UV for Testing?

UV is a blazingly fast Python package installer and resolver written in Rust. It's **10-100x faster** than pip and provides excellent testing workflows.

### Benefits:
- ⚡ **Lightning fast** dependency installation
- 🔒 **Lockfile support** for reproducible environments
- 🎯 **Precise dependency resolution**
- 📦 **Built-in virtual environment management**
- 🔄 **Automatic dependency syncing**

## 📋 Quick Start

### Install UV

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

### Run Tests with UV

```bash
# Quick test run
uv run pytest

# With our custom script
./test_with_uv.sh
```

## 🧪 UV Testing Commands

### Basic Test Execution

```bash
# Run all tests
uv run pytest tests/

# Run specific test file
uv run pytest tests/test_pdf_processor.py

# Run specific test
uv run pytest tests/test_pdf_processor.py::TestPDFProcessor::test_processor_initialization

# Run with verbose output
uv run pytest -v tests/

# Run with quiet output
uv run pytest -q tests/
```

### Coverage Testing

```bash
# Run with coverage
uv run pytest --cov=src --cov=pdf_manager_app tests/

# Generate HTML coverage report
uv run pytest --cov=src --cov-report=html tests/

# View coverage in terminal
uv run pytest --cov=src --cov-report=term-missing tests/
```

### Parallel Testing

```bash
# First install pytest-xdist
uv pip install pytest-xdist

# Run tests in parallel (auto-detect CPUs)
uv run pytest -n auto tests/

# Run with specific number of workers
uv run pytest -n 4 tests/
```

### Watch Mode

```bash
# Install pytest-watch
uv pip install pytest-watch

# Run tests in watch mode
uv run ptw tests/

# Watch specific directory
uv run ptw tests/ -- -v

# Watch with coverage
uv run ptw -- --cov=src tests/
```

## 🎯 Test Categories with UV

### Run by Markers

```bash
# Unit tests only
uv run pytest -m unit tests/

# Integration tests only
uv run pytest -m integration tests/

# E2E tests only
uv run pytest -m e2e tests/

# Exclude slow tests
uv run pytest -m "not slow" tests/

# Tests that don't require Qdrant
uv run pytest -m "not requires_qdrant" tests/
```

### Run by Pattern

```bash
# Run tests matching pattern
uv run pytest -k "pdf" tests/

# Exclude tests matching pattern
uv run pytest -k "not slow" tests/

# Complex patterns
uv run pytest -k "pdf and not ocr" tests/
```

## 📦 Environment Management with UV

### Create and Sync Environment

```bash
# Create virtual environment
uv venv

# Activate it (macOS/Linux)
source .venv/bin/activate

# Activate it (Windows)
.venv\Scripts\activate

# Sync all dependencies from pyproject.toml
uv sync

# Sync with dev dependencies
uv sync --dev

# Sync with extras
uv sync --extra pdf-advanced
uv sync --all-extras
```

### Install Test Dependencies

```bash
# Core testing packages
uv pip install pytest pytest-cov pytest-mock

# Additional testing tools
uv pip install pytest-asyncio  # Async test support
uv pip install pytest-xdist    # Parallel execution
uv pip install pytest-watch    # Watch mode
uv pip install pytest-benchmark # Performance testing
uv pip install pytest-timeout   # Test timeouts
uv pip install pytest-env       # Environment variables
```

## 🔧 UV Configuration

### pyproject.toml Setup

Our `pyproject.toml` is already configured for UV:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--strict-markers",
    "--tb=short",
    "--cov=src",
    "--cov=pdf_manager_app",
    "--cov-report=term-missing",
    "--cov-report=html",
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "slow: Slow tests",
    "requires_qdrant: Tests that require Qdrant",
]
```

### UV-specific Settings

```bash
# Set Python version for UV
uv python pin 3.10

# Use specific Python version
uv sync --python 3.10

# Clear UV cache
uv cache clean

# Show UV configuration
uv config
```

## 🏃 Advanced UV Testing Workflows

### 1. Continuous Testing

```bash
# Run tests on file changes
uv run ptw tests/ -- --cov=src

# With notifications (requires pytest-notifier)
uv pip install pytest-notifier
uv run ptw -- --notify tests/
```

### 2. Test Debugging

```bash
# Drop to debugger on failure
uv run pytest --pdb tests/

# Drop to debugger on first failure
uv run pytest -x --pdb tests/

# Show local variables on failure
uv run pytest -l tests/

# Detailed traceback
uv run pytest --tb=long tests/
```

### 3. Performance Testing

```bash
# Install benchmark plugin
uv pip install pytest-benchmark

# Run with benchmarks
uv run pytest --benchmark-only tests/

# Compare benchmarks
uv run pytest --benchmark-compare tests/
```

### 4. Test Reporting

```bash
# Generate JUnit XML (for CI/CD)
uv run pytest --junitxml=report.xml tests/

# Generate JSON report
uv pip install pytest-json-report
uv run pytest --json-report --json-report-file=report.json tests/

# Generate HTML report
uv pip install pytest-html
uv run pytest --html=report.html --self-contained-html tests/
```

## 🎭 Mock Testing with UV

```bash
# Install mocking libraries
uv pip install pytest-mock responses faker

# Run tests with mocks
uv run pytest tests/test_vector_operations.py -v

# Test with real services (skip mocks)
uv run pytest tests/ -v --no-mock
```

## 🔄 CI/CD with UV

### GitHub Actions

```yaml
name: Tests with UV

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Install UV
      run: curl -LsSf https://astral.sh/uv/install.sh | sh

    - name: Set up Python with UV
      run: |
        uv python pin 3.10
        uv venv

    - name: Install dependencies
      run: uv sync --dev

    - name: Run tests
      run: uv run pytest tests/ --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### Local CI Simulation

```bash
# Simulate CI environment locally
uv venv --clear
uv sync --dev
uv run pytest tests/ --cov=src --cov-report=xml
```

## 📊 Test Metrics with UV

### Coverage Goals

```bash
# Check if coverage meets threshold
uv run pytest --cov=src --cov-fail-under=80 tests/

# Generate coverage badge
uv pip install coverage-badge
uv run coverage-badge -o coverage.svg
```

### Test Statistics

```bash
# Show test durations
uv run pytest --durations=10 tests/

# Profile slow tests
uv run pytest --profile tests/

# Generate test report
uv run pytest --report tests/
```

## 🐛 Troubleshooting UV Tests

### Common Issues

#### Issue: UV command not found

```bash
# Add to PATH
export PATH="$HOME/.cargo/bin:$PATH"

# Or reinstall
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Issue: Dependencies not syncing

```bash
# Clear cache and resync
uv cache clean
uv sync --refresh
```

#### Issue: Tests can't find modules

```bash
# Ensure you're using uv run
uv run pytest tests/  # ✅ Correct
pytest tests/         # ❌ May fail
```

#### Issue: Slow first run

```bash
# UV caches dependencies, first run is slower
# Subsequent runs will be much faster

# Pre-cache dependencies
uv sync
uv pip install -r requirements.txt
```

## 🎯 UV Testing Best Practices

### 1. Always Use UV Run

```bash
# Good
uv run pytest tests/
uv run python -m pytest tests/

# Bad (might use wrong environment)
pytest tests/
python -m pytest tests/
```

### 2. Lock Dependencies

```bash
# Generate lock file
uv pip freeze > requirements-lock.txt

# Or use UV's native locking (coming soon)
uv lock
```

### 3. Clean Testing

```bash
# Fresh environment for testing
uv venv --clear
uv sync
uv run pytest tests/
```

### 4. Fast Iteration

```bash
# Use watch mode for development
uv run ptw tests/ -- -x

# Use parallel execution for speed
uv run pytest -n auto tests/
```

## 📝 Custom UV Test Script

Our `test_with_uv.sh` provides:

```bash
# Run all tests
./test_with_uv.sh

# Unit tests with coverage
./test_with_uv.sh --unit --coverage

# Watch mode
./test_with_uv.sh --watch

# Parallel execution
./test_with_uv.sh --parallel

# Verbose output
./test_with_uv.sh -v
```

## 🚀 Performance Comparison

| Operation | pip | UV | Speedup |
|-----------|-----|-----|---------|
| Install deps | 45s | 3s | 15x |
| Create venv | 3s | 0.1s | 30x |
| Sync deps | 30s | 2s | 15x |
| Run tests | Same | Same | - |

## 📚 Resources

- [UV Documentation](https://github.com/astral-sh/uv)
- [UV Python Guide](https://docs.astral.sh/uv/guides/python/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Plugins](https://docs.pytest.org/en/latest/reference/plugin_list.html)

---

**Pro Tip:** UV's speed makes it perfect for CI/CD pipelines and rapid development cycles. The faster your tests run, the more often you'll run them!