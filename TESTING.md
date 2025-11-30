# Testing Guide for DocsHub

This document provides comprehensive information about testing in DocsHub.

## Test Structure

Tests are organized by Django app, with each app having its own `tests.py` file:

- **accounts/tests.py**: User authentication and profile management
- **documents/tests.py**: Document models, API endpoints, permissions, sharing
- **spreadsheets/tests.py**: Spreadsheet models, API endpoints, permissions
- **notifications/tests.py**: Notification models and API endpoints
- **collaboration/tests.py**: WebSocket consumer tests (requires Redis)

## Running Tests

### Basic Commands

```bash
# Run all tests
python manage.py test

# Run tests for a specific app
python manage.py test accounts
python manage.py test documents
python manage.py test spreadsheets
python manage.py test notifications
python manage.py test collaboration

# Run a specific test class
python manage.py test documents.tests.DocumentModelTests

# Run a specific test method
python manage.py test documents.tests.DocumentModelTests.test_document_creation
```

### Using the Test Runner Script

```bash
# Run all tests
./run_tests.sh

# Run tests for specific app
./run_tests.sh -a documents

# Run with verbose output
./run_tests.sh -v

# Run with coverage report
./run_tests.sh -c
```

### Test Coverage

To generate coverage reports:

```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run --source='.' manage.py test

# View coverage report
coverage report

# Generate HTML coverage report
coverage html
# Open htmlcov/index.html in your browser
```

## Test Categories

### 1. Model Tests

Test Django model functionality:
- Model creation
- Model relationships
- Model methods
- Model validation

Example:
```python
def test_document_creation(self):
    doc = Document.objects.create(
        owner=self.owner,
        title='Test Document',
        content='<p>Test</p>'
    )
    self.assertEqual(doc.title, 'Test Document')
```

### 2. API Tests

Test REST API endpoints:
- Authentication requirements
- Permission checks
- Request/response formats
- Error handling

Example:
```python
def test_document_create(self):
    self.client.force_authenticate(user=self.owner)
    data = {'title': 'New Document'}
    response = self.client.post('/api/documents/', data, format='json')
    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
```

### 3. Permission Tests

Test role-based access control:
- Owner permissions
- Editor permissions
- Commenter permissions
- Viewer permissions

Example:
```python
def test_document_update_viewer(self):
    # Viewer should not be able to update
    DocumentPermission.objects.create(
        document=self.document,
        user=self.user,
        role='viewer'
    )
    self.client.force_authenticate(user=self.user)
    response = self.client.post(f'/api/documents/{self.document.id}/update/', ...)
    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
```

### 4. WebSocket Tests

Test real-time collaboration (requires Redis):
- WebSocket connections
- Message broadcasting
- User presence
- Content synchronization

Note: WebSocket tests require:
- Redis server running
- `channels.testing` package available

## Test Database

Django automatically creates a separate test database for running tests. This database:
- Is created before tests run
- Is destroyed after tests complete
- Is isolated from your development database
- Uses SQLite by default (even if you use PostgreSQL in development)

## Test Fixtures

Tests use `setUp()` methods to create test data:

```python
def setUp(self):
    self.owner = User.objects.create_user(
        username='owner',
        email='owner@example.com',
        password='pass123'
    )
    self.document = Document.objects.create(
        owner=self.owner,
        title='Test Document',
        content='<p>Test</p>'
    )
```

## Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Cleanup**: Use `setUp()` and `tearDown()` for test data
3. **Naming**: Use descriptive test method names (e.g., `test_document_create_success`)
4. **Assertions**: Use specific assertions (e.g., `assertEqual` instead of `assertTrue`)
5. **Coverage**: Aim for high test coverage, especially for critical business logic

## Common Test Patterns

### Testing Authentication

```python
def test_endpoint_requires_authentication(self):
    response = self.client.get('/api/documents/')
    self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
```

### Testing Permissions

```python
def test_only_owner_can_delete(self):
    self.client.force_authenticate(user=self.user)
    response = self.client.post(f'/api/documents/{self.document.id}/delete/')
    self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
```

### Testing Error Cases

```python
def test_create_with_missing_fields(self):
    self.client.force_authenticate(user=self.owner)
    data = {}  # Missing required fields
    response = self.client.post('/api/documents/', data, format='json')
    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
```

## Troubleshooting

### Tests Fail with Database Errors

- Ensure migrations are up to date: `python manage.py migrate`
- Check that test database can be created
- Verify database permissions

### WebSocket Tests Fail

- Ensure Redis is running: `redis-server`
- Check Redis connection: `redis-cli ping`
- Verify `channels.testing` is installed

### Import Errors

- Ensure virtual environment is activated
- Install all dependencies: `pip install -r requirements.txt`
- Check Python path and imports

### Slow Tests

- Use `TransactionTestCase` only when needed (for database transactions)
- Use `TestCase` for most tests (faster, uses transactions)
- Consider using test fixtures for large datasets

## Continuous Integration

For CI/CD pipelines, you can run tests with:

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Run tests
python manage.py test --noinput

# Generate coverage
coverage run --source='.' manage.py test
coverage report
```

## Test Statistics

To see test statistics:

```bash
python manage.py test --verbosity=2
```

This shows:
- Number of tests run
- Number of tests passed
- Number of tests failed
- Execution time

## Writing New Tests

When adding new features, always write corresponding tests:

1. **Model changes**: Test model methods and relationships
2. **API endpoints**: Test all endpoints with various scenarios
3. **Permissions**: Test all permission levels
4. **Edge cases**: Test error conditions and boundary cases

Example template:

```python
class MyNewFeatureTests(TestCase):
    def setUp(self):
        # Set up test data
        pass
    
    def test_feature_success_case(self):
        # Test successful operation
        pass
    
    def test_feature_error_case(self):
        # Test error handling
        pass
    
    def test_feature_permission_check(self):
        # Test permission requirements
        pass
```

## Resources

- [Django Testing Documentation](https://docs.djangoproject.com/en/stable/topics/testing/)
- [Django REST Framework Testing](https://www.django-rest-framework.org/api-guide/testing/)
- [Channels Testing](https://channels.readthedocs.io/en/stable/testing.html)

