#!/bin/bash
# Test runner script for DocsHub
# This script runs all tests with proper configuration

echo "🧪 DocsHub Test Runner"
echo "======================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Warning: Virtual environment not activated${NC}"
    echo "Activating virtual environment..."
    source venv/bin/activate 2>/dev/null || {
        echo -e "${RED}❌ Error: Could not activate virtual environment${NC}"
        echo "Please activate it manually: source venv/bin/activate"
        exit 1
    }
fi

# Check if Redis is running (needed for WebSocket tests)
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Warning: Redis is not running${NC}"
    echo "Some tests (WebSocket) may fail without Redis"
    echo "Start Redis with: redis-server"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Parse command line arguments
TEST_APP=""
VERBOSE=""
COVERAGE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--app)
            TEST_APP="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE="--verbosity=2"
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -h|--help)
            echo "Usage: ./run_tests.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -a, --app APP        Run tests for specific app (accounts, documents, etc.)"
            echo "  -v, --verbose        Verbose output"
            echo "  -c, --coverage       Run with coverage report"
            echo "  -h, --help           Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run_tests.sh                    # Run all tests"
            echo "  ./run_tests.sh -a documents       # Run only document tests"
            echo "  ./run_tests.sh -v                 # Run with verbose output"
            echo "  ./run_tests.sh -c                 # Run with coverage"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Run tests
echo -e "${GREEN}Running tests...${NC}"
echo ""

if [ "$COVERAGE" = true ]; then
    # Check if coverage is installed
    if ! python -c "import coverage" 2>/dev/null; then
        echo -e "${YELLOW}Installing coverage...${NC}"
        pip install coverage
    fi
    
    # Run tests with coverage
    coverage run --source='.' manage.py test $TEST_APP $VERBOSE
    TEST_RESULT=$?
    
    if [ $TEST_RESULT -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ All tests passed!${NC}"
        echo ""
        echo "Generating coverage report..."
        coverage report
        echo ""
        echo "Generating HTML coverage report..."
        coverage html
        echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
    else
        echo -e "${RED}❌ Some tests failed${NC}"
    fi
else
    # Run tests normally
    python manage.py test $TEST_APP $VERBOSE
    TEST_RESULT=$?
    
    if [ $TEST_RESULT -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ All tests passed!${NC}"
    else
        echo -e "${RED}❌ Some tests failed${NC}"
    fi
fi

echo ""
echo "======================"
exit $TEST_RESULT

