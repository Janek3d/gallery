# GitHub Actions Workflows

This directory contains GitHub Actions workflows for CI/CD.

**Note:** Workflows are currently disabled (renamed to `.disabled`). To enable them, rename the files back to `.yml`.

## Workflows

### `tests.yml.disabled` (Currently Disabled)

Runs the test suite on every pull request and push to main branches.

**Features:**
- Tests on Python 3.11 and 3.12
- Uses SQLite (no external database required)
- Generates coverage reports
- Uploads test results as artifacts
- Optional Codecov integration

**Triggers:**
- Pull requests to `main`, `master`, or `develop`
- Pushes to `main`, `master`, or `develop`

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

### Enable Workflows

To enable the workflows, rename:
- `tests.yml.disabled` → `tests.yml`
- `lint.yml.disabled` → `lint.yml`

### Add More Python Versions

Edit `.github/workflows/tests.yml` (after enabling):

```yaml
matrix:
  python-version: ["3.11", "3.12", "3.13"]
```

### Add PostgreSQL for Integration Tests

Uncomment the PostgreSQL service section in `tests.yml` if you need it for integration tests.

### Enable Linting Enforcement

Edit `.github/workflows/lint.yml` (after enabling) and remove `|| true` from the commands to make linting failures block PRs.
