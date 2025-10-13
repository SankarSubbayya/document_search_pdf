#!/bin/bash

# Test runner script for PDF Document Search System

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}${BOLD}     PDF Document Search System - Test Suite           ${NC}"
echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════════${NC}\n"

# Function to print section headers
print_section() {
    echo -e "\n${YELLOW}${BOLD}▶ $1${NC}"
    echo -e "${YELLOW}$( printf '═%.0s' {1..60} )${NC}"
}

# Check if pytest is installed
if ! python -m pytest --version &> /dev/null; then
    echo -e "${RED}❌ pytest is not installed${NC}"
    echo -e "${YELLOW}Installing pytest and related packages...${NC}"
    pip install pytest pytest-cov pytest-asyncio pytest-mock
fi

# Parse command line arguments
TEST_TYPE="all"
COVERAGE=false
VERBOSE=false
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
        --help|-h)
            echo "Usage: ./run_tests.sh [options]"
            echo ""
            echo "Options:"
            echo "  --unit          Run only unit tests"
            echo "  --integration   Run only integration tests"
            echo "  --e2e           Run only end-to-end tests"
            echo "  --coverage      Generate coverage report"
            echo "  --verbose, -v   Verbose output"
            echo "  --help, -h      Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run_tests.sh                    # Run all tests"
            echo "  ./run_tests.sh --unit             # Run unit tests only"
            echo "  ./run_tests.sh --coverage         # Run with coverage report"
            echo "  ./run_tests.sh --unit --verbose   # Run unit tests with verbose output"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Set pytest options
PYTEST_OPTS=""

if [ "$VERBOSE" = true ]; then
    PYTEST_OPTS="$PYTEST_OPTS -v"
else
    PYTEST_OPTS="$PYTEST_OPTS -q"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_OPTS="$PYTEST_OPTS --cov=src --cov=pdf_manager_app --cov-report=term-missing --cov-report=html"
fi

# Create test data directory if it doesn't exist
mkdir -p tests/test_data/pdfs
mkdir -p tests/test_data/outputs

# Display test configuration
print_section "Test Configuration"
echo -e "Test Type: ${GREEN}$TEST_TYPE${NC}"
echo -e "Coverage: ${GREEN}$COVERAGE${NC}"
echo -e "Verbose: ${GREEN}$VERBOSE${NC}"

# Check if Qdrant is running (for integration tests)
if [ "$TEST_TYPE" = "integration" ] || [ "$TEST_TYPE" = "all" ]; then
    print_section "Checking Dependencies"
    echo -n "Checking Qdrant connection... "
    if nc -zv localhost 6333 &>/dev/null; then
        echo -e "${GREEN}✅ Connected${NC}"
    else
        echo -e "${YELLOW}⚠️  Not connected${NC}"
        echo -e "${YELLOW}Integration tests may fail without Qdrant running${NC}"
        echo -e "${YELLOW}Start Qdrant with: docker run -p 6333:6333 qdrant/qdrant${NC}"
    fi
fi

# Run tests based on type
print_section "Running Tests"

case $TEST_TYPE in
    unit)
        echo -e "Running ${BLUE}unit tests${NC}..."
        python -m pytest tests/test_pdf_processor.py $PYTEST_OPTS
        RESULT=$?
        ;;
    integration)
        echo -e "Running ${BLUE}integration tests${NC}..."
        python -m pytest tests/test_vector_operations.py $PYTEST_OPTS
        RESULT=$?
        ;;
    e2e)
        echo -e "Running ${BLUE}end-to-end tests${NC}..."
        python -m pytest tests/test_streamlit_app.py $PYTEST_OPTS
        RESULT=$?
        ;;
    all)
        echo -e "Running ${BLUE}all tests${NC}..."
        python -m pytest tests/ $PYTEST_OPTS $MARKERS
        RESULT=$?
        ;;
esac

# Display results
print_section "Test Results"

if [ $RESULT -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✅ All tests passed!${NC}"
else
    echo -e "${RED}${BOLD}❌ Some tests failed${NC}"
fi

# Display coverage report location if generated
if [ "$COVERAGE" = true ]; then
    print_section "Coverage Report"
    echo -e "HTML coverage report generated at: ${BLUE}htmlcov/index.html${NC}"
    echo -e "To view the report, run: ${BLUE}open htmlcov/index.html${NC}"
fi

# Run specific test file examples
print_section "Additional Test Commands"
echo "Run specific test file:"
echo -e "  ${BLUE}python -m pytest tests/test_pdf_processor.py -v${NC}"
echo ""
echo "Run specific test function:"
echo -e "  ${BLUE}python -m pytest tests/test_pdf_processor.py::TestPDFProcessor::test_processor_initialization -v${NC}"
echo ""
echo "Run with debugging:"
echo -e "  ${BLUE}python -m pytest tests/ -v --pdb${NC}"
echo ""
echo "Run tests matching pattern:"
echo -e "  ${BLUE}python -m pytest tests/ -k 'pdf' -v${NC}"

echo -e "\n${BLUE}${BOLD}═══════════════════════════════════════════════════════${NC}\n"

exit $RESULT