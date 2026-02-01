"""
Pytest fixtures for E2E tests (Playwright + Django live server).

Requires: pytest-playwright, pytest-django. Run with:
  pytest app/tests/e2e -m e2e
  playwright install chromium   # first-time browser install
"""
import pytest
from django.contrib.auth import get_user_model
import os

User = get_user_model()
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
@pytest.fixture
def e2e_user(db):
    """Create a user for E2E login. Email login is used (allauth)."""
    return User.objects.create_user(
        username="e2etest",
        email="e2e@example.com",
        password="e2epass123",
    )


@pytest.fixture
def e2e_login_credentials(e2e_user):
    """Return (email, password) for E2E login."""
    return ("e2e@example.com", "e2epass123")
