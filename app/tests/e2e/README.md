# E2E tests (Playwright + pytest-django)

End-to-end tests run in a real browser against the Django live server.

## Setup

1. Install dev dependencies (includes `pytest-playwright`):

   ```bash
   uv sync --extra dev
   # or: pip install -e ".[dev]"
   ```

2. Install Playwright browsers (once):

   ```bash
   playwright install chromium
   ```

## Run

- All e2e tests:
  ```bash
  pytest app/tests/e2e -m e2e -v
  ```

- Single test:
  ```bash
  pytest app/tests/e2e/test_login_and_create_gallery.py -m e2e -v
  ```

- Skip e2e in normal runs:
  ```bash
  pytest -m "not e2e"
  ```

## Test: login and create gallery

`test_login_and_create_gallery`:

1. Opens `/accounts/login/`, fills email and password, submits.
2. Goes to `/galleries/create/`, fills name and description, submits.
3. Asserts redirect to gallery list and the new gallery name is visible.

Uses a fixture-created user (`e2e@example.com` / `e2epass123`) and `live_server` from pytest-django.
