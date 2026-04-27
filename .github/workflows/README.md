# GitHub Actions CI/CD Configuration

This directory contains GitHub Actions workflows for automated testing, linting, and deployment.

## Workflows

### tests.yml
- **Trigger**: Push to `main`/`develop` or PR against `main`/`develop`
- **Python Versions**: 3.9, 3.10, 3.11, 3.12, 3.13
- **Actions**:
  - Run pytest with coverage
  - Upload coverage to Codecov
  - Support test matrix for multiple Python versions

### lint.yml
- **Trigger**: Push to `main`/`develop` or PR against `main`/`develop`
- **Checks**:
  - ruff linting
  - black code formatting
  - isort import sorting
- **Python**: 3.11 (latest stable)

### type-check.yml
- **Trigger**: Push to `main`/`develop` or PR against `main`/`develop`
- **Actions**:
  - mypy type checking on sophon package
- **Python**: 3.11

### build.yml
- **Trigger**: Push to `main`/`develop` or tags matching `v*`, or PR
- **Actions**:
  - Build wheel and source distributions
  - Check distribution with twine
  - Upload artifacts

### ci.yml
- **Trigger**: Push to `main`/`develop` or PR
- **Purpose**: Central CI status check for branch protection

### publish.yml
- **Trigger**: Release published or manual workflow dispatch
- **Actions**:
  - Build distributions
  - Publish to PyPI using OIDC
- **Environment**: `release` (requires configuration)

## Branch Protection Setup

Recommended branch protection rules for `main`:

```
Status checks that must pass:
- Tests (all Python versions)
- Lint
- Type Check
- Build
- CI (optional, for overall status)

Other rules:
- Require branches to be up to date before merging
- Require pull request reviews before merging (1+ reviews)
- Require code owner reviews (if CODEOWNERS exists)
- Require status checks to pass before merging
```

## PyPI Release Setup

To enable PyPI publishing:

1. Create environment at: `https://github.com/studiobutter/Sophon.py/settings/environments`
2. Name it `release`
3. Optional: Set deployment branches to `main` only
4. Create PyPI trusted publisher:
   - Go to https://pypi.org/manage/account/publishing/
   - Add pending publisher for:
     - PyPI Project Name: `sophon-py`
     - Owner: `studiobutter`
     - Repository: `Sophon.py`
     - Workflow name: `publish.yml`
     - Environment name: `release`

## Codecov Integration

Coverage reports are automatically uploaded to Codecov. Add the badge to README.md:

```markdown
[![codecov](https://codecov.io/gh/studiobutter/Sophon.py/branch/main/graph/badge.svg)](https://codecov.io/gh/studiobutter/Sophon.py)
```

## Local Testing

Test workflows locally with act:

```bash
# Install act: https://nektosact.com/

# Run all workflows
act

# Run specific workflow
act -j test

# Run with specific event
act pull_request
```

## Troubleshooting

### Tests fail on specific Python version
- Check [supported version matrix](tests.yml#L17)
- Update test environment requirements if needed

### Build fails
- Ensure `setup.py` and `pyproject.toml` are properly configured
- Check for missing files referenced in `MANIFEST.in`

### Linting fails
- Run locally: `black sophon tests examples`, `ruff check sophon tests examples`
- Ensure isort configuration matches in `pyproject.toml`

### Type check fails
- Run locally: `mypy sophon`
- Check mypy configuration in `pyproject.toml`
