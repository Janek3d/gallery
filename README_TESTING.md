# Testing Guide

This project uses **pytest** with **pytest-django** for testing.

## Database Configuration

**Tests use SQLite** (in-memory) instead of PostgreSQL for faster execution. This is automatically configured in `app/config/test_settings.py`. No PostgreSQL connection is required to run tests.

The test settings file (`config/test_settings.py`) overrides the production database configuration to use SQLite, preventing connection attempts to the PostgreSQL host "db" during tests.

## Setup

### Install Dependencies

```bash
pip install -e ".[dev]"
```

Or install pytest dependencies separately:

```bash
pip install pytest pytest-django pytest-cov pytest-xdist factory-boy faker
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Tests with Coverage

```bash
pytest --cov=app --cov-report=html
```

This will generate an HTML coverage report in `htmlcov/index.html`.

### Run Specific Tests

```bash
# Run tests in a specific file
pytest app/gallery/tests/test_models.py

# Run a specific test class
pytest app/gallery/tests/test_models.py::TestGalleryModel

# Run a specific test function
pytest app/gallery/tests/test_models.py::TestGalleryModel::test_create_gallery
```

### Run Tests in Parallel

```bash
pytest -n auto  # Uses pytest-xdist
```

### Run Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## Test Structure

```
app/
├── tests/
│   ├── conftest.py          # Shared fixtures
│   ├── __init__.py
│   └── gallery/
│       ├── __init__.py
│       ├── test_models.py   # Model tests
│       ├── test_views.py     # View tests
│       └── test_utils.py     # Utility function tests
└── config/
    └── test_settings.py     # Test-specific Django settings (uses SQLite)
```

## Available Fixtures

### User Fixtures

- `user` - Creates a test user
- `admin_user` - Creates an admin user
- `authenticated_client` - Django test client with logged-in user
- `authenticated_api_client` - DRF API client with authenticated user

### Django Fixtures

- `db` - Database access (auto-enabled for all tests)
- `client` - Django test client
- `api_client` - DRF API client
- `request_factory` - Request factory for testing views
- `settings_override` - Override Django settings in tests

### Celery Fixtures

- `celery_config` - Configure Celery for testing (synchronous execution)
- `celery_worker_parameters` - Celery worker parameters

## Writing Tests

### Example: Model Test

```python
import pytest
from gallery.models import Gallery

@pytest.mark.django_db
class TestGalleryModel:
    def test_create_gallery(self, user):
        gallery = Gallery.objects.create(
            owner=user,
            name="Test Gallery"
        )
        assert gallery.name == "Test Gallery"
```

### Example: View Test

```python
import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_gallery_list_view(authenticated_client):
    url = reverse('gallery:gallery_list')
    response = authenticated_client.get(url)
    assert response.status_code == 200
```

### Example: API Test

```python
import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
def test_create_gallery_api(authenticated_api_client, user):
    url = reverse('gallery:gallery-list')
    data = {
        'name': 'Test Gallery',
        'gallery_type': 'private'
    }
    response = authenticated_api_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
```

## Test Markers

Use markers to categorize tests:

```python
@pytest.mark.slow
def test_slow_operation():
    pass

@pytest.mark.integration
def test_integration():
    pass

@pytest.mark.unit
def test_unit():
    pass
```

## Configuration

Test configuration is in:
- `pytest.ini` - Main pytest configuration (points to `config.test_settings`)
- `pyproject.toml` - Project metadata and optional dependencies
- `app/config/test_settings.py` - Test-specific Django settings (SQLite, no external services)
- `app/tests/conftest.py` - Shared fixtures

## Coverage

Coverage reports are generated automatically when running tests. View the HTML report:

```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html  # On macOS
# or
start htmlcov/index.html  # On Windows
```

## Continuous Integration

For CI/CD, you can run:

```bash
pytest --cov=app --cov-report=xml --junitxml=junit.xml
```

This generates:
- `coverage.xml` - Coverage report for CI
- `junit.xml` - Test results in JUnit format

## Tips

1. **Use fixtures** - Don't create test data manually, use fixtures
2. **Mark slow tests** - Use `@pytest.mark.slow` for tests that take time
3. **Use factories** - Consider using `factory-boy` for complex test data
4. **Test isolation** - Each test gets a fresh database transaction
5. **Parallel testing** - Use `pytest-xdist` for faster test runs
