# Quick Test Commands Reference

## Basic Test Commands

```bash
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test accounts
python manage.py test documents
python manage.py test spreadsheets
python manage.py test notifications
python manage.py test collaboration

# Run specific test class
python manage.py test documents.tests.DocumentModelTests

# Run specific test method
python manage.py test documents.tests.DocumentModelTests.test_document_creation
```

## Using Test Runner Script

```bash
# Run all tests
./run_tests.sh

# Run tests for specific app
./run_tests.sh -a documents
./run_tests.sh -a accounts

# Verbose output
./run_tests.sh -v

# With coverage
./run_tests.sh -c

# Help
./run_tests.sh -h
```

## Coverage Commands

```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run --source='.' manage.py test

# View coverage report
coverage report

# Generate HTML report
coverage html
# Open htmlcov/index.html in browser
```

## Test Output Options

```bash
# Verbose output (level 2)
python manage.py test --verbosity=2

# Keep test database (for debugging)
python manage.py test --keepdb

# Run tests in parallel (faster)
python manage.py test --parallel

# Fail fast (stop on first failure)
python manage.py test --failfast
```

## Test Specific Features

```bash
# Test only model tests
python manage.py test documents.tests.DocumentModelTests

# Test only API tests
python manage.py test documents.tests.DocumentAPITests

# Test only permission tests
python manage.py test documents.tests.DocumentPermissionModelTests
```

## Prerequisites

Before running tests, ensure:

1. **Virtual environment is activated**
   ```bash
   source venv/bin/activate
   ```

2. **Redis is running** (for WebSocket tests)
   ```bash
   redis-server
   ```

3. **Dependencies are installed**
   ```bash
   pip install -r requirements.txt
   ```

## Expected Test Counts

- **accounts**: ~10 tests
- **documents**: ~25 tests
- **spreadsheets**: ~15 tests
- **notifications**: ~8 tests
- **collaboration**: ~8 tests (requires Redis)

**Total**: ~66 tests

## Troubleshooting

```bash
# If tests fail with database errors
python manage.py migrate

# If WebSocket tests fail
redis-cli ping  # Should return PONG

# If import errors occur
pip install -r requirements.txt
```

