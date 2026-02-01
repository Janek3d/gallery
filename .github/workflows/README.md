# GitHub Actions Workflows

This directory contains GitHub Actions workflows for CI/CD.

## Workflows

### `tests.yml` (Enabled)

Runs the full test suite (unit + e2e with Playwright) on every pull request and push to main branches.

**Features:**
- Tests on Python 3.11 and 3.12
- **uv** for installs with dependency cache (`enable-cache: true`, keyed by `uv.lock`)
- **Playwright** for e2e: Chromium only; browser binaries cached (`~/.cache/ms-playwright`, keyed by `uv.lock`); on cache hit only OS deps are installed
- Uses SQLite (no external database required)
- Generates coverage reports
- Uploads test results as artifacts
- Optional Codecov integration

**Triggers:**
- Pull requests to `main`, `master`, or `develop`
- Pushes to `main`, `master`, or `develop`

### `tests.yml.disabled` (Legacy / Disabled)

Previous test workflow (pip-based, no Playwright). Superseded by `tests.yml`.

### `lint.yml.disabled` (Currently Disabled)

Runs code quality checks (optional - can be enabled when you add linting tools).

**Features:**
- Checks code formatting with `black`
- Checks import sorting with `isort`
- Runs `ruff` for linting

**Note:** Currently set to not fail the build (`|| true`). Remove this when you're ready to enforce linting.

## Setup

### Codecov (Optional)

If you want to use Codecov for coverage tracking:

1. Sign up at [codecov.io](https://codecov.io)
2. Add your repository
3. The workflow will automatically upload coverage reports

If you don't want Codecov, the workflow will still work - it just won't upload coverage (the step is set to `continue-on-error: true`).

## Customization

### Enable Lint Workflow

To enable the lint workflow, rename `lint.yml.disabled` → `lint.yml`.

### Add More Python Versions

Edit `.github/workflows/tests.yml`:

```yaml
matrix:
  python-version: ["3.11", "3.12", "3.13"]
```

### Add PostgreSQL for Integration Tests

Uncomment the PostgreSQL service section in `tests.yml` if you need it for integration tests.

### Enable Linting Enforcement

Edit `.github/workflows/lint.yml` (after enabling) and remove `|| true` from the commands to make linting failures block PRs.
