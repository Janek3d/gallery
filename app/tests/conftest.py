"""
Pytest configuration and shared fixtures for Django tests.
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

User = get_user_model()


@pytest.fixture(scope="function")
def db_access(db):
    """
    Fixture to ensure database access is available.
    This is a wrapper around pytest-django's db fixture.
    """
    return db


@pytest.fixture
def user(db):
    """
    Create a test user.
    """
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def admin_user(db):
    """
    Create an admin user.
    """
    return User.objects.create_superuser(
        username="testuser",
        email="admin@example.com",
        password="adminpass123",
    )


@pytest.fixture
def authenticated_client(client, user):
    """
    Create an authenticated client with a logged-in user.
    """
    client.force_login(user)
    return client


@pytest.fixture
def request_factory():
    """
    Create a request factory for testing views.
    """
    return RequestFactory()


@pytest.fixture
def api_client():
    """
    Create a DRF API client for testing API views.
    """
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_api_client(api_client, user):
    """
    Create an authenticated DRF API client.
    """
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Automatically enable database access for all tests.
    This ensures all tests can access the database without needing @pytest.mark.django_db.
    """
    pass


@pytest.fixture
def settings_override(settings):
    """
    Helper fixture to override Django settings in tests.
    
    Usage:
        def test_something(settings_override):
            settings_override.DEBUG = True
            # ... test code ...
    """
    return settings


@pytest.fixture
def celery_config():
    """
    Configure Celery for testing (use in-memory broker).
    """
    return {
        'task_always_eager': True,  # Execute tasks synchronously
        'task_eager_propagates': True,
        'broker_url': 'memory://',
        'result_backend': 'cache+memory://',
    }


@pytest.fixture
def celery_worker_parameters():
    """
    Parameters for Celery worker in tests.
    """
    return {
        'perform_ping_check': False,
    }
