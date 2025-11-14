# 🎉 PROJECT READY TO START!

## ✅ **Setup Complete**

Your project is now fully initialized and ready for development!

### 📂 **Project Structure Created**

```
simple_slr/
├── slr/                    ← Your code goes here
│   ├── core/              ← Models (START HERE)
│   ├── providers/         ← Provider implementations
│   ├── dedup/             ← Deduplication logic
│   ├── utils/             ← Utilities
│   ├── export/            ← Export formats
│   ├── normalization/     ← Text normalization
│   └── cli/               ← Command-line interface
├── tests/                  ← All tests
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── benchmarks/
├── docs/                   ← Documentation
└── .github/workflows/      ← CI/CD (already configured!)
```

### 🔧 **Tools Installed**

- ✅ Python 3.14.0
- ✅ Virtual environment (.venv)
- ✅ All dependencies installed
- ✅ Pre-commit hooks configured
- ✅ GitHub Actions CI/CD ready
- ✅ pytest, black, isort, mypy, flake8
- ✅ MkDocs for documentation

---

## 🚀 **START CODING NOW - Week 1, Day 1**

### **Today's Goal: Create Core Models**

**File to create:** `slr/core/models.py`

**What to implement:**

1. `ExternalIds` - Paper identifiers (DOI, arXiv, etc.)
2. `Author` - Author information
3. `Document` - Main paper model
4. `Query` - Search query model
5. `DocumentCluster` - Deduplication cluster
6. `SearchResult` - Container for search results

### **Step-by-Step Instructions:**

#### 1. Open `slr/core/models.py` in your editor

#### 2. Start with the template below:

```python
"""Core data models for Simple SLR framework."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ExternalIds(BaseModel):
    """All possible paper identifiers."""

    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    pubmed_id: Optional[str] = None
    openalex_id: Optional[str] = None
    s2_id: Optional[str] = None

    @field_validator("doi")
    @classmethod
    def normalize_doi(cls, v: Optional[str]) -> Optional[str]:
        """Normalize DOI by removing URL prefixes."""
        if not v:
            return None
        import re

        # Remove https://doi.org/ or http://dx.doi.org/ prefixes
        v = re.sub(r"^https?://(dx\.)?doi\.org/", "", v, flags=re.IGNORECASE)
        # Remove doi: prefix
        v = re.sub(r"^doi:\s*", "", v, flags=re.IGNORECASE)
        return v.strip().lower() if v else None


class Author(BaseModel):
    """Author information."""

    family_name: str
    given_name: Optional[str] = None
    orcid: Optional[str] = None

    @property
    def full_name(self) -> str:
        """Get full author name."""
        if self.given_name:
            return f"{self.given_name} {self.family_name}"
        return self.family_name


class Document(BaseModel):
    """Unified document representation across all providers."""

    # Required fields
    title: str
    year: Optional[int] = None
    provider: str  # openalex, crossref, arxiv, s2
    provider_id: str

    # External identifiers
    external_ids: ExternalIds = Field(default_factory=ExternalIds)

    # Optional metadata
    abstract: Optional[str] = None
    authors: List[Author] = Field(default_factory=list)
    venue: Optional[str] = None
    url: Optional[str] = None
    language: Optional[str] = None
    cited_by_count: Optional[int] = None

    # Search context
    query_id: Optional[str] = None
    query_text: Optional[str] = None
    retrieved_at: Optional[datetime] = None

    # Deduplication (populated later)
    cluster_id: Optional[int] = None

    # Raw data for debugging
    raw_data: Optional[Dict[str, Any]] = Field(default=None, exclude=True)

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class Query(BaseModel):
    """Search query specification."""

    id: str  # Q01, Q02, etc.
    text: str  # Boolean query string
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    language: str = "en"
    max_results: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentCluster(BaseModel):
    """Deduplication cluster result."""

    cluster_id: int
    representative: Document
    members: List[Document]

    # Aggregated info
    all_dois: List[str] = Field(default_factory=list)
    all_arxiv_ids: List[str] = Field(default_factory=list)
    provider_counts: Dict[str, int] = Field(default_factory=dict)

    @property
    def size(self) -> int:
        """Get cluster size."""
        return len(self.members)

    @property
    def confidence(self) -> float:
        """Get deduplication confidence."""
        # 1.0 if exact ID match, lower for fuzzy
        if len(self.all_dois) >= 2 or len(self.all_arxiv_ids) >= 2:
            return 1.0
        return 0.95  # Default for fuzzy matches


class SearchResult(BaseModel):
    """Container for search results."""

    query: Query
    documents: List[Document]
    total_found: int
    provider: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    errors: List[str] = Field(default_factory=list)
```

#### 3. Create tests: `tests/unit/test_core/test_models.py`

```python
"""Tests for core models."""

import pytest
from datetime import datetime
from slr.core.models import (
    Author,
    Document,
    DocumentCluster,
    ExternalIds,
    Query,
    SearchResult,
)


def test_external_ids_doi_normalization():
    """Test that DOI normalization removes prefixes."""
    # Test with https://doi.org/ prefix
    ids1 = ExternalIds(doi="https://doi.org/10.1234/test")
    assert ids1.doi == "10.1234/test"

    # Test with doi: prefix
    ids2 = ExternalIds(doi="doi: 10.1234/TEST")
    assert ids2.doi == "10.1234/test"

    # Test with no prefix
    ids3 = ExternalIds(doi="10.1234/test")
    assert ids3.doi == "10.1234/test"


def test_author_full_name():
    """Test author full name property."""
    # With given name
    author1 = Author(given_name="John", family_name="Doe")
    assert author1.full_name == "John Doe"

    # Without given name
    author2 = Author(family_name="Smith")
    assert author2.full_name == "Smith"


def test_document_creation():
    """Test document model creation."""
    doc = Document(
        title="Test Paper",
        year=2020,
        provider="openalex",
        provider_id="W123456",
        external_ids=ExternalIds(doi="10.1234/test"),
    )

    assert doc.title == "Test Paper"
    assert doc.year == 2020
    assert doc.provider == "openalex"
    assert doc.external_ids.doi == "10.1234/test"


def test_query_creation():
    """Test query model creation."""
    query = Query(
        id="Q01",
        text="machine learning plant disease",
        year_min=2019,
    )

    assert query.id == "Q01"
    assert query.text == "machine learning plant disease"
    assert query.year_min == 2019
    assert query.language == "en"  # Default


def test_document_cluster_properties():
    """Test cluster properties."""
    doc1 = Document(
        title="Test",
        provider="openalex",
        provider_id="1",
        external_ids=ExternalIds(doi="10.1234/test"),
    )
    doc2 = Document(
        title="Test",
        provider="crossref",
        provider_id="2",
        external_ids=ExternalIds(doi="10.1234/test"),
    )

    cluster = DocumentCluster(
        cluster_id=1,
        representative=doc1,
        members=[doc1, doc2],
        all_dois=["10.1234/test"],
    )

    assert cluster.size == 2
    assert cluster.confidence == 1.0  # Exact DOI match


def test_search_result_creation():
    """Test search result container."""
    query = Query(id="Q01", text="test")
    doc = Document(title="Test", provider="openalex", provider_id="1")

    result = SearchResult(
        query=query,
        documents=[doc],
        total_found=1,
        provider="openalex",
    )

    assert result.query.id == "Q01"
    assert len(result.documents) == 1
    assert result.provider == "openalex"
    assert isinstance(result.timestamp, datetime)
```

#### 4. Run the tests:

```bash
pytest tests/unit/test_core/test_models.py -v
```

#### 5. Check code quality:

```bash
# Format code
black slr/core/models.py tests/unit/test_core/test_models.py

# Sort imports
isort slr/core/models.py tests/unit/test_core/test_models.py

# Check types
mypy slr/core/models.py

# Lint
flake8 slr/core/models.py
```

---

## ⏱️ **Your Schedule for Today (Day 1)**

- [ ] **10:00-12:00** - Implement models in `slr/core/models.py`
- [ ] **12:00-13:00** - Lunch break
- [ ] **13:00-15:00** - Write tests in `tests/unit/test_core/test_models.py`
- [ ] **15:00-16:00** - Run tests, fix issues
- [ ] **16:00-16:30** - Code quality checks (black, isort, mypy, flake8)
- [ ] **16:30-17:00** - Commit and push

### Commit Message:
```bash
git add slr/core/models.py tests/unit/test_core/test_models.py
git commit -m "feat(core): add Document, Query, and Cluster models with tests"
git push
```

---

## 📚 **Resources**

### Pydantic Documentation
- https://docs.pydantic.dev/latest/

### Pytest Documentation
- https://docs.pytest.org/

### Quick Commands

```bash
# Activate virtual environment
.venv\Scripts\activate

# Run tests
pytest

# Run tests with coverage
pytest --cov=slr

# Run specific test
pytest tests/unit/test_core/test_models.py::test_document_creation

# Format all code
black slr tests

# Check types
mypy slr

# View test coverage report
pytest --cov=slr --cov-report=html
# Then open htmlcov/index.html
```

---

## 🎯 **Success Criteria for Today**

- [ ] All 6 models defined in `slr/core/models.py`
- [ ] At least 6 tests passing
- [ ] Code formatted with black
- [ ] Imports sorted with isort
- [ ] No mypy errors
- [ ] No flake8 warnings
- [ ] Committed and pushed to GitHub

---

## 🆘 **Need Help?**

### Common Issues:

**Import errors?**
```bash
# Make sure package is installed in editable mode
pip install -e .
```

**Tests not found?**
```bash
# Make sure __init__.py exists in test directories
# Already created by setup script!
```

**Pre-commit hooks failing?**
```bash
# Run formatters manually first
black slr tests
isort slr tests
```

---

## 🎉 **YOU'RE READY TO CODE!**

**Current Status:**
- ✅ Project structure created
- ✅ Dependencies installed
- ✅ CI/CD configured
- ✅ Pre-commit hooks active
- ✅ Documentation template ready

**Next Step:**
👉 **Open `slr/core/models.py` and start coding!**

---

**Good luck! You've got this! 🚀**

Remember: The execution plan is in `EXECUTION_PLAN.md` - follow it day by day.

**Target:** v1.0.0 by January 23, 2026 (10 weeks)

