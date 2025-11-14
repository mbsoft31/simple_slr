# Contributing to Simple SLR

Thank you for your interest in contributing to Simple SLR! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the maintainers.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- A GitHub account

### Setting Up Development Environment

1. **Fork and clone the repository:**

```bash
git clone https://github.com/YOUR_USERNAME/simple_slr.git
cd simple_slr
```

2. **Create a virtual environment:**

```bash
python -m venv .venv

# On Windows
.venv\Scripts\activate

# On Unix/MacOS
source .venv/bin/activate
```

3. **Install development dependencies:**

```bash
make install-dev
# or
pip install -e ".[dev]"
```

4. **Install pre-commit hooks:**

```bash
make pre-commit-install
# or
pre-commit install
```

5. **Verify installation:**

```bash
make test
```

## Development Workflow

### 1. Create a Branch

Create a branch for your work:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/changes

### 2. Make Changes

Follow these guidelines:

- **Write tests first** (TDD approach recommended)
- **Keep changes focused** - one feature/fix per PR
- **Follow code standards** (see below)
- **Update documentation** as needed
- **Add/update tests** for your changes

### 3. Run Quality Checks

Before committing:

```bash
# Run all checks
make check

# Or individually:
make format        # Format code
make lint          # Check linting
make type-check    # Type checking
make test-fast     # Run quick tests
```

### 4. Commit Changes

Follow conventional commits:

```bash
git commit -m "feat(providers): add OpenAlex rate limiting"
git commit -m "fix(dedup): handle edge case in fuzzy matching"
git commit -m "docs: update API reference for retry decorator"
git commit -m "test: add integration tests for crossref provider"
```

Commit types:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `test` - Tests
- `refactor` - Code refactoring
- `perf` - Performance improvement
- `chore` - Maintenance

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Standards

### Code Style

We use:
- **Black** for code formatting (line length: 100)
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

Run formatters:
```bash
make format
```

### Type Hints

All functions should have type hints:

```python
from typing import List, Optional

def fetch_papers(
    query: str,
    year_min: Optional[int] = None
) -> List[Document]:
    """Fetch papers matching query.
    
    Args:
        query: Search query string
        year_min: Minimum publication year
    
    Returns:
        List of matching documents
    """
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def complex_function(param1: str, param2: int) -> bool:
    """Short description.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When param2 is negative
    
    Example:
        >>> complex_function("test", 42)
        True
    """
    ...
```

### Error Handling

Use custom exceptions from `slr.utils.exceptions`:

```python
from slr.utils.exceptions import ProviderError, ValidationError

def fetch_data(url: str) -> dict:
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.HTTPError as e:
        raise ProviderError(
            "openalex",
            f"Failed to fetch data: {e}",
            status_code=e.response.status_code
        )
```

### Logging

Use structured logging:

```python
from slr.utils import get_logger

logger = get_logger(__name__)

def process_data(data: dict) -> None:
    logger.info("Processing data", extra={"count": len(data)})
    try:
        # Process data
        logger.debug("Processing step 1 complete")
    except Exception as e:
        logger.error("Processing failed", exc_info=True)
        raise
```

## Testing

### Writing Tests

- **Test file naming:** `test_<module>.py`
- **Test class naming:** `Test<ClassName>`
- **Test function naming:** `test_<description>`

Example:

```python
import pytest
from slr.utils import retry_with_backoff, NetworkError

class TestRetryWithBackoff:
    """Tests for retry_with_backoff decorator."""
    
    def test_success_on_first_attempt(self):
        """Test successful execution without retries."""
        @retry_with_backoff(max_retries=3)
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"
    
    def test_retry_on_network_error(self):
        """Test retry behavior on network errors."""
        attempts = []
        
        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def failing_function():
            attempts.append(1)
            if len(attempts) < 3:
                raise NetworkError("test", "Connection failed")
            return "success"
        
        result = failing_function()
        assert result == "success"
        assert len(attempts) == 3
```

### Running Tests

```bash
# All tests
make test

# Unit tests only
make test-unit

# With coverage
make test-cov

# Watch mode (auto-rerun on file changes)
make test-watch

# Fast tests only (skip slow ones)
make test-fast

# Specific test file
pytest tests/unit/test_core/test_models.py

# Specific test
pytest tests/unit/test_core/test_models.py::TestDocument::test_creation
```

### Test Markers

Use markers to categorize tests:

```python
import pytest

@pytest.mark.unit
def test_unit_functionality():
    ...

@pytest.mark.integration
def test_integration_with_api():
    ...

@pytest.mark.slow
def test_slow_operation():
    ...

@pytest.mark.provider
def test_provider_specific():
    ...
```

Run specific markers:
```bash
pytest -m unit           # Only unit tests
pytest -m "not slow"     # Skip slow tests
pytest -m integration    # Only integration tests
```

### Fixtures

Create reusable fixtures in `conftest.py`:

```python
import pytest
from slr.core import SLRConfig

@pytest.fixture
def sample_config():
    """Provide a sample configuration."""
    return SLRConfig(
        mailto="test@example.com",
        year_min=2020,
        year_max=2023
    )

@pytest.fixture
def mock_provider(mocker):
    """Provide a mocked provider."""
    return mocker.Mock(spec=OpenAlexProvider)
```

## Documentation

### Updating Documentation

When making changes:

1. **Update docstrings** in code
2. **Update README.md** if needed
3. **Update CHANGELOG.md** with your changes
4. **Add examples** to relevant docs

### Documentation Structure

```
docs/
├── getting-started/
│   ├── installation.md
│   ├── quickstart.md
│   └── configuration.md
├── user-guide/
│   ├── providers.md
│   ├── deduplication.md
│   └── export.md
├── api-reference/
│   ├── core.md
│   ├── providers.md
│   └── utils.md
└── developer-guide/
    ├── architecture.md
    ├── contributing.md
    └── testing.md
```

## Submitting Changes

### Pull Request Process

1. **Ensure all tests pass:**
```bash
make ci
```

2. **Update CHANGELOG.md:**
```markdown
## [Unreleased]

### Added
- New feature description (#PR_NUMBER)

### Fixed
- Bug fix description (#PR_NUMBER)
```

3. **Create Pull Request:**
   - Use descriptive title
   - Reference related issues
   - Provide detailed description
   - Include screenshots if UI changes
   - Check all boxes in PR template

4. **Respond to review feedback:**
   - Make requested changes
   - Reply to comments
   - Re-request review when ready

### PR Title Format

```
<type>(<scope>): <description>

Examples:
feat(providers): add rate limiting to OpenAlex
fix(dedup): correct fuzzy matching threshold
docs(api): update provider documentation
test(core): add tests for Document model
```

### Review Criteria

Your PR will be reviewed for:

- **Functionality** - Does it work as intended?
- **Tests** - Are there adequate tests?
- **Code Quality** - Does it follow standards?
- **Documentation** - Is it well documented?
- **Performance** - Does it impact performance?
- **Compatibility** - Is it backwards compatible?

## Questions?

- **General questions:** Open a GitHub Discussion
- **Bug reports:** Open a GitHub Issue
- **Security issues:** Email maintainers directly
- **Feature requests:** Open a GitHub Issue with [Feature Request] tag

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

Thank you for contributing to Simple SLR! 🎉

