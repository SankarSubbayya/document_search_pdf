#!/bin/bash

# Test runner script using UV for PDF Document Search System

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}${BOLD}║     Testing with UV - Fast Python Package Manager    ║${NC}"
echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════════════╝${NC}\n"

# Function to print section headers
print_section() {
    echo -e "\n${YELLOW}${BOLD}▶ $1${NC}"
    echo -e "${YELLOW}$(printf '═%.0s' {1..50})${NC}"
}

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ UV is not installed${NC}"
    echo -e "${YELLOW}Installing UV...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Add to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"

    if ! command -v uv &> /dev/null; then
        echo -e "${RED}Failed to install UV. Please install manually:${NC}"
        echo -e "${BLUE}curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
        exit 1
    fi
fi

# Display UV version
print_section "UV Environment"
echo -e "UV Version: ${GREEN}$(uv --version)${NC}"

# Parse command line arguments
TEST_TYPE="all"
COVERAGE=false
VERBOSE=false
WATCH=false
PARALLEL=false
MARKERS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            TEST_TYPE="unit"
            MARKERS="-m unit"
            shift
            ;;
        --integration)
            TEST_TYPE="integration"
            MARKERS="-m integration"
            shift
            ;;
        --e2e)
            TEST_TYPE="e2e"
            MARKERS="-m e2e"
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --watch)
            WATCH=true
            shift
            ;;
        --parallel|-n)
            PARALLEL=true
            shift
            ;;
        --help|-h)
            echo "Usage: ./test_with_uv.sh [options]"
            echo ""
            echo "Options:"
            echo "  --unit          Run only unit tests"
            echo "  --integration   Run only integration tests"
            echo "  --e2e           Run only end-to-end tests"
            echo "  --coverage      Generate coverage report"
            echo "  --verbose, -v   Verbose output"
            echo "  --watch         Watch mode (re-run on file changes)"
            echo "  --parallel, -n  Run tests in parallel"
            echo "  --help, -h      Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./test_with_uv.sh                       # Run all tests"
            echo "  ./test_with_uv.sh --unit --coverage     # Unit tests with coverage"
            echo "  ./test_with_uv.sh --watch               # Watch mode"
            echo "  ./test_with_uv.sh --parallel            # Run tests in parallel"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Ensure virtual environment exists
print_section "Setting Up Environment"

if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    uv venv
fi

echo -e "${GREEN}✓ Virtual environment ready${NC}"

# Install dependencies if needed
print_section "Installing Dependencies"

echo -e "${YELLOW}Syncing dependencies with uv...${NC}"
uv sync

# Install test dependencies
echo -e "${YELLOW}Installing test dependencies...${NC}"
uv pip install pytest pytest-cov pytest-asyncio pytest-mock pytest-xdist pytest-watch

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Build pytest command
PYTEST_CMD="uv run pytest"

# Add options
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
else
    PYTEST_CMD="$PYTEST_CMD -q"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=src --cov=pdf_manager_app --cov-report=term-missing --cov-report=html"
fi

if [ "$PARALLEL" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -n auto"
fi

if [ "$MARKERS" != "" ]; then
    PYTEST_CMD="$PYTEST_CMD $MARKERS"
fi

# Display test configuration
print_section "Test Configuration"
echo -e "Test Type: ${GREEN}$TEST_TYPE${NC}"
echo -e "Coverage: ${GREEN}$COVERAGE${NC}"
echo -e "Verbose: ${GREEN}$VERBOSE${NC}"
echo -e "Watch Mode: ${GREEN}$WATCH${NC}"
echo -e "Parallel: ${GREEN}$PARALLEL${NC}"
echo -e "Command: ${BLUE}$PYTEST_CMD${NC}"

# Create test directories if needed
mkdir -p tests/test_data/pdfs tests/test_data/outputs

# Run tests
print_section "Running Tests"

if [ "$WATCH" = true ]; then
    echo -e "${YELLOW}Starting watch mode... (Press Ctrl+C to stop)${NC}"

    # Use pytest-watch if available
    if uv pip list | grep -q pytest-watch; then
        case $TEST_TYPE in
            unit)
                uv run ptw tests/test_pdf_processor.py -- $PYTEST_OPTS
                ;;
            integration)
                uv run ptw tests/test_vector_operations.py -- $PYTEST_OPTS
                ;;
            e2e)
                uv run ptw tests/test_streamlit_app.py -- $PYTEST_OPTS
                ;;
            all)
                uv run ptw tests/ -- $PYTEST_OPTS
                ;;
        esac
    else
        echo -e "${YELLOW}Installing pytest-watch...${NC}"
        uv pip install pytest-watch
        uv run ptw tests/ -- $PYTEST_OPTS
    fi
else
    # Regular test execution
    case $TEST_TYPE in
        unit)
            echo -e "${CYAN}Running unit tests...${NC}"
            $PYTEST_CMD tests/test_pdf_processor.py
            RESULT=$?
            ;;
        integration)
            echo -e "${CYAN}Running integration tests...${NC}"
            $PYTEST_CMD tests/test_vector_operations.py
            RESULT=$?
            ;;
        e2e)
            echo -e "${CYAN}Running end-to-end tests...${NC}"
            $PYTEST_CMD tests/test_streamlit_app.py
            RESULT=$?
            ;;
        all)
            echo -e "${CYAN}Running all tests...${NC}"
            $PYTEST_CMD tests/
            RESULT=$?
            ;;
    esac
fi

# Display results (if not in watch mode)
if [ "$WATCH" = false ]; then
    print_section "Test Results"

    if [ $RESULT -eq 0 ]; then
        echo -e "${GREEN}${BOLD}✅ All tests passed!${NC}"
    else
        echo -e "${RED}${BOLD}❌ Some tests failed${NC}"
    fi

    # Display coverage report location if generated
    if [ "$COVERAGE" = true ]; then
        print_section "Coverage Report"
        echo -e "HTML report: ${BLUE}htmlcov/index.html${NC}"
        echo -e "View report: ${BLUE}uv run python -m http.server 8000 --directory htmlcov${NC}"
    fi
fi

echo -e "\n${CYAN}${BOLD}╚══════════════════════════════════════════════════════╝${NC}\n"

exit ${RESULT:-0}