"""
Django test settings for gallery project.

This settings file is used specifically for running tests.
It uses SQLite instead of PostgreSQL and disables unnecessary features.
"""
# Import all settings first
from .settings import *  # noqa: F401, F403

# Override database to use SQLite for tests
# This MUST be after the import to override the PostgreSQL config from settings.py
# This prevents trying to connect to PostgreSQL host "db" during test setup
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # In-memory SQLite for fastest tests
    }
}

# Disable migrations during tests (faster)
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# Speed up password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable caching for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Disable email sending during tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Use database session backend for tests (more reliable than cache with DummyCache)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Disable logging during tests (optional, for cleaner output)
LOGGING_CONFIG = None

# Celery configuration for tests (synchronous execution)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'

# Disable external services
USE_S3 = False

# Test-specific settings
DEBUG = False
SECRET_KEY = 'test-secret-key-for-testing-only'  # Not used in production
