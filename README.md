# Simple SLR - Systematic Literature Review Framework

[![Tests](https://github.com/yourusername/simple_slr/workflows/Tests/badge.svg)](https://github.com/yourusername/simple_slr/actions)
[![Coverage](https://codecov.io/gh/yourusername/simple_slr/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/simple_slr)
[![PyPI version](https://badge.fury.io/py/simple-slr.svg)](https://badge.fury.io/py/simple-slr)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern, extensible framework for conducting systematic literature reviews with support for multiple academic databases, intelligent deduplication, and PRISMA-compliant workflows.

## 🚀 Quick Start

### Installation

```bash
# Core installation (minimal dependencies)
pip install simple-slr

# With all features (includes semantic deduplication)
pip install simple-slr[all]

# Development installation
git clone https://github.com/yourusername/simple_slr.git
cd simple_slr
pip install -e ".[dev]"
```

### Basic Usage

```bash
# Search across multiple providers
slr search --config config.yml --queries queries.json --output ./outputs

# Deduplicate results
slr deduplicate --input ./outputs --output ./dedup --strategy conservative

# Export to different formats
slr export --input ./dedup/representatives.jsonl --format bibtex --output citations.bib
```

## ✨ Features

### v1.0 (Current)

- **Multi-Provider Search**: Query 4 academic databases simultaneously
  - OpenAlex - Open scholarly database
  - Crossref - DOI registry
  - arXiv - Preprint server
  - Semantic Scholar - AI-powered search

- **Intelligent Deduplication**: Conservative strategy with:
  - Exact DOI and arXiv ID matching
  - Fuzzy title matching with blocking
  - Year gap validation
  - Author verification

- **Multiple Export Formats**:
  - CSV (spreadsheet-friendly)
  - JSONL (structured data)
  - BibTeX (citation management)

- **PRISMA Compliance**: Generate flowchart data automatically

- **Robust Error Handling**: 
  - Automatic retries with exponential backoff
  - Rate limiting per provider
  - Detailed error logging

### v1.1+ (Planned)

- Semantic deduplication with SPECTER2 embeddings
- Enhanced paper classification
- TUI (Text User Interface)
- REST API

## 📚 Documentation

- [Getting Started](docs/getting-started/quickstart.md)
- [Migration Guide (v0 → v1)](docs/migration/from-v0-to-v1.md)
- [User Guide](docs/user-guide/)
- [API Reference](docs/api-reference/)
- [Developer Guide](docs/developer-guide/)

## 🎯 Example Workflow

```python
from slr.providers.openalex import OpenAlexProvider, ProviderConfig
from slr.core.models import Query
from slr.dedup.strategies.conservative import ConservativeDeduplicator

# Configure provider
config = ProviderConfig(
    name="openalex",
    mailto="your.email@example.com",
    rate_limit=5.0
)

provider = OpenAlexProvider(config)

# Create query
query = Query(
    id="Q01",
    text="machine learning plant disease detection",
    year_min=2019
)

# Search
documents = list(provider.search(query))
print(f"Found {len(documents)} documents")

# Deduplicate
deduplicator = ConservativeDeduplicator(fuzzy_threshold=97)
clusters = deduplicator.deduplicate(documents)
print(f"After deduplication: {len(clusters)} unique papers")
```

## 🔧 Configuration

Create a `config.yml` file:

```yaml
mailto: your.email@example.com
year_min: 2019

providers:
  openalex:
    enabled: true
    rate_limit: 5.0
  crossref:
    enabled: true
    rate_limit: 1.0
  arxiv:
    enabled: true
    rate_limit: 0.5
  semantic_scholar:
    enabled: true
    api_key: ${S2_API_KEY}

deduplication:
  strategy: conservative
  fuzzy_threshold: 97
  max_year_gap: 1

output:
  directory: ./outputs
  formats: [csv, jsonl, bibtex]
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=slr --cov-report=html

# Run specific test file
pytest tests/unit/test_core/test_models.py

# Run benchmarks
pytest tests/benchmarks/ --benchmark-only
```

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/simple_slr.git
cd simple_slr

# Run setup script (Windows)
setup_project.bat

# Or manually:
python -m venv .venv
.venv\Scripts\activate  # On Windows
# source .venv/bin/activate  # On Unix
pip install -e ".[dev]"
pre-commit install
```

## 📊 Project Status

- **Current Version**: v0.9.1-alpha.0 (refactoring in progress)
- **Target v1.0 Release**: January 23, 2026
- **Test Coverage**: Target 80%+
- **Python Support**: 3.10, 3.11, 3.12

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for systematic reviews in agricultural ML/computer vision
- Inspired by PRISMA guidelines for systematic reviews
- Uses excellent open-source libraries: Pydantic, Click, pytest

## 📧 Contact

- GitHub Issues: [Report a bug](https://github.com/yourusername/simple_slr/issues)
- Email: your.email@example.com

---

**Note**: This is version 1.0 - a complete refactor with improved architecture, testing, and documentation. For the legacy version (0.9.0), see the [v0.9.0 branch](https://github.com/yourusername/simple_slr/tree/v0.9.0).

**Migration Guide**: If you're upgrading from v0.9.0, please read [docs/migration/from-v0-to-v1.md](docs/migration/from-v0-to-v1.md).
# EXECUTION PLAN - Ready to Code NOW

**Start Date:** November 14, 2025  
**Target v1.0 Release:** January 23, 2026 (10 weeks)  
**Buffer End Date:** February 13, 2026 (13 weeks max)

---

## 🚀 **IMMEDIATE ACTIONS (Next 30 Minutes)**

### Step 1: Project Structure Setup

Run these commands in your terminal:

```bash
# Create directory structure
mkdir -p slr\core
mkdir -p slr\providers
mkdir -p slr\dedup
mkdir -p slr\utils
mkdir -p slr\export
mkdir -p slr\normalization
mkdir -p tests\unit\test_core
mkdir -p tests\unit\test_providers
mkdir -p tests\unit\test_dedup
mkdir -p tests\integration
mkdir -p tests\fixtures
mkdir -p tests\benchmarks
mkdir -p docs\getting-started
mkdir -p docs\migration
mkdir -p docs\user-guide
mkdir -p docs\developer-guide
mkdir -p docs\api-reference
mkdir -p compat
mkdir -p .github\workflows

# Create __init__.py files
type nul > slr\__init__.py
type nul > slr\core\__init__.py
type nul > slr\providers\__init__.py
type nul > slr\dedup\__init__.py
type nul > slr\utils\__init__.py
type nul > slr\export\__init__.py
type nul > slr\normalization\__init__.py
type nul > tests\__init__.py
type nul > tests\unit\__init__.py
type nul > tests\integration\__init__.py

# Create empty files we'll populate
type nul > slr\core\models.py
type nul > slr\utils\exceptions.py
type nul > slr\utils\logging.py
type nul > slr\utils\rate_limit.py
type nul > slr\utils\retry.py
type nul > slr\utils\config.py
type nul > tests\conftest.py
type nul > tests\fixtures\sample_data.py
```

### Step 2: Create pyproject.toml

Already creating this file for you...

### Step 3: Create GitHub Workflow

Already creating this file for you...

### Step 4: Create Pre-commit Config

Already creating this file for you...

---

## 📅 **WEEK-BY-WEEK SCHEDULE**

### **Week 1: Nov 14 - Nov 20 (Core Models & Infrastructure)**

**Goal:** Foundation without touching existing code

#### Day 1-2 (Nov 14-15): Core Models
- [ ] `slr/core/models.py` - All Pydantic models
  - Document, Query, DocumentCluster, ExternalIds, Author, SearchResult
- [ ] Unit tests for all models
- [ ] Validation tests (invalid data should fail)

#### Day 3 (Nov 16): Exception Hierarchy
- [ ] `slr/utils/exceptions.py` - All custom exceptions
- [ ] `slr/utils/retry.py` - Retry decorator with backoff
- [ ] Tests for retry logic

#### Day 4 (Nov 17): Rate Limiting & Logging
- [ ] `slr/utils/rate_limit.py` - Token bucket implementation
- [ ] `slr/utils/logging.py` - Centralized logging config
- [ ] Tests for rate limiter

#### Day 5 (Nov 18): Configuration System
- [ ] `slr/utils/config.py` - YAML-based config
- [ ] Example `config.yml`
- [ ] Environment variable support

#### Day 6-7 (Nov 19-20): CI/CD & Documentation
- [ ] GitHub Actions workflow (already created)
- [ ] Pre-commit hooks (already created)
- [ ] Initial documentation structure
- [ ] Week 1 review & testing

**Deliverables:**
- ✅ All core models defined with tests
- ✅ Error handling infrastructure
- ✅ CI/CD pipeline running
- ✅ Zero changes to existing scripts

---

### **Week 2: Nov 21 - Nov 27 (Provider Foundation)**

**Goal:** BaseProvider abstraction ready

#### Day 1-2 (Nov 21-22): Base Provider
- [ ] `slr/providers/base.py` - BaseProvider abstract class
- [ ] ProviderConfig model
- [ ] Abstract methods defined
- [ ] Documentation for provider interface

#### Day 3 (Nov 23): Test Fixtures
- [ ] `tests/fixtures/sample_data.py` - Reusable test data
- [ ] Mock API responses for each provider
- [ ] `tests/conftest.py` - Pytest fixtures

#### Day 4-5 (Nov 24-25): Normalization Utilities
- [ ] `slr/normalization/identifiers.py` - DOI, arXiv normalization
- [ ] `slr/normalization/text.py` - Title cleaning
- [ ] `slr/normalization/authors.py` - Author parsing
- [ ] Comprehensive tests

#### Day 6-7 (Nov 26-27): Week 2 Review
- [ ] Integration test: BaseProvider + Config
- [ ] Documentation updates
- [ ] Code review & refactoring

**Deliverables:**
- ✅ BaseProvider ready for implementation
- ✅ Test infrastructure complete
- ✅ Normalization utilities tested

---

### **Week 3: Nov 28 - Dec 4 (OpenAlex Provider)**

**Goal:** Prove the pattern with ONE provider

#### Day 1-3 (Nov 28-30): OpenAlex Implementation
- [ ] `slr/providers/openalex.py` - Full implementation
- [ ] Query translation for OpenAlex
- [ ] Response normalization
- [ ] Error handling integration

#### Day 4 (Dec 1): Testing
- [ ] Unit tests for OpenAlex provider
- [ ] Mock API responses
- [ ] Edge case testing (rate limits, errors)

#### Day 5 (Dec 2): Performance Benchmarking
- [ ] `tests/benchmarks/test_openalex_performance.py`
- [ ] Compare with old implementation
- [ ] Ensure ≤10% performance difference

#### Day 6-7 (Dec 3-4): Documentation & Review
- [ ] Document OpenAlex provider
- [ ] Create example usage
- [ ] Week 3 review

**Deliverables:**
- ✅ Working OpenAlex provider
- ✅ Performance parity with old code
- ✅ Pattern proven for other providers

---

### **Week 4: Dec 5 - Dec 11 (Compatibility Layer)**

**Goal:** Users can use old CLI with new code

#### Day 1-3 (Dec 5-7): Compatibility Wrapper
- [ ] `compat/enhanced_query_script.py` - Wrapper script
- [ ] Translate old CLI args to new API
- [ ] Deprecation warnings
- [ ] Output format compatibility

#### Day 4-5 (Dec 8-9): Migration Guide
- [ ] `docs/migration/from-v0-to-v1.md`
- [ ] Side-by-side CLI comparison
- [ ] Migration checklist
- [ ] FAQ section

#### Day 6-7 (Dec 10-11): Testing & Validation
- [ ] Test old CLI still works
- [ ] Test output format matches
- [ ] User acceptance testing
- [ ] Week 4 review

**Deliverables:**
- ✅ Backwards compatibility maintained
- ✅ Migration guide complete
- ✅ No breaking changes

---

### **Week 5: Dec 12 - Dec 18 (Crossref & arXiv)**

**Goal:** Refactor 2 more providers

#### Day 1-3 (Dec 12-14): Crossref Provider
- [ ] `slr/providers/crossref.py`
- [ ] Query translation
- [ ] Tests & benchmarks

#### Day 4-6 (Dec 15-17): arXiv Provider
- [ ] `slr/providers/arxiv.py`
- [ ] Query translation
- [ ] Tests & benchmarks

#### Day 7 (Dec 18): Week 5 Review
- [ ] Integration tests (multi-provider)
- [ ] Performance validation
- [ ] Documentation updates

**Deliverables:**
- ✅ Crossref provider working
- ✅ arXiv provider working
- ✅ 3/4 providers complete

---

### **Week 6: Dec 19 - Dec 25 (Semantic Scholar & Registry)**

**Goal:** Complete all providers + registry

#### Day 1-3 (Dec 19-21): Semantic Scholar
- [ ] `slr/providers/semantic_scholar.py`
- [ ] Query translation
- [ ] Tests & benchmarks

#### Day 4-5 (Dec 22-23): Provider Registry
- [ ] `slr/providers/registry.py`
- [ ] Factory pattern for provider creation
- [ ] Configuration-based provider selection
- [ ] Tests

#### Day 6-7 (Dec 24-25): Week 6 Review
- [ ] All 4 providers working
- [ ] Multi-provider search test
- [ ] Performance comparison report

**Deliverables:**
- ✅ All 4 providers refactored
- ✅ Provider registry working
- ✅ Comprehensive tests

---

### **Week 7: Dec 26 - Jan 1 (Deduplication)**

**Goal:** Extract current dedup logic to module

#### Day 1-3 (Dec 26-28): Conservative Strategy
- [ ] `slr/dedup/base.py` - Deduplicator interface
- [ ] `slr/dedup/clustering.py` - DSU implementation
- [ ] `slr/dedup/matching.py` - Matching utilities

#### Day 4-5 (Dec 29-30): Conservative Implementation
- [ ] `slr/dedup/strategies/conservative.py`
- [ ] Extract exact current logic
- [ ] Zero behavior changes

#### Day 6-7 (Dec 31 - Jan 1): Testing
- [ ] Unit tests for dedup
- [ ] Compare old vs new output
- [ ] Performance benchmarks
- [ ] Week 7 review

**Deliverables:**
- ✅ Dedup module working
- ✅ Output matches old version exactly
- ✅ Tests prove equivalence

---

### **Week 8: Jan 2 - Jan 8 (Export & Polish)**

**Goal:** Export formats + testing

#### Day 1-2 (Jan 2-3): Export Modules
- [ ] `slr/export/base.py` - Exporter interface
- [ ] `slr/export/csv.py`
- [ ] `slr/export/jsonl.py`
- [ ] `slr/export/bibtex.py`

#### Day 3-4 (Jan 4-5): Integration Testing
- [ ] End-to-end workflow tests
- [ ] Performance testing at scale
- [ ] Memory profiling

#### Day 5-6 (Jan 6-7): Documentation Sprint
- [ ] Complete all user guides
- [ ] API reference (auto-generated)
- [ ] Example notebooks
- [ ] Tutorial videos (optional)

#### Day 7 (Jan 8): Week 8 Review
- [ ] Code coverage report (target: 80%)
- [ ] Documentation completeness check
- [ ] Pre-release checklist

**Deliverables:**
- ✅ All export formats working
- ✅ 80%+ test coverage
- ✅ Documentation complete

---

### **Week 9: Jan 9 - Jan 15 (CLI & Beta Testing)**

**Goal:** New CLI + user testing

#### Day 1-3 (Jan 9-11): CLI Implementation
- [ ] `slr/cli/main.py` - Click-based CLI
- [ ] `slr search` command
- [ ] `slr deduplicate` command
- [ ] `slr export` command

#### Day 4-5 (Jan 12-13): Beta Testing
- [ ] Recruit 3-5 beta testers
- [ ] Create beta testing guide
- [ ] Collect feedback
- [ ] Bug fixes

#### Day 6-7 (Jan 14-15): Polish & Fixes
- [ ] Address beta tester feedback
- [ ] Performance optimization
- [ ] Final bug fixes
- [ ] Week 9 review

**Deliverables:**
- ✅ Working CLI
- ✅ Beta tester approval
- ✅ Critical bugs fixed

---

### **Week 10: Jan 16 - Jan 23 (Release Preparation)**

**Goal:** v1.0.0 release

#### Day 1-2 (Jan 16-17): Release Candidate
- [ ] Tag v1.0.0-rc.1
- [ ] Test installation from PyPI test server
- [ ] Final documentation review

#### Day 3-4 (Jan 18-19): Final Testing
- [ ] Clean install testing
- [ ] Multi-platform testing (Windows/Linux/Mac)
- [ ] Performance validation
- [ ] Security audit

#### Day 5 (Jan 20): Release Prep
- [ ] Update CHANGELOG.md
- [ ] Prepare release notes
- [ ] Create GitHub release draft

#### Day 6 (Jan 21): v1.0.0 Release
- [ ] Tag v1.0.0
- [ ] Publish to PyPI
- [ ] Publish documentation
- [ ] Announcement blog post

#### Day 7 (Jan 22-23): Post-Release
- [ ] Monitor for issues
- [ ] Respond to user questions
- [ ] Celebrate! 🎉

**Deliverables:**
- ✅ v1.0.0 released
- ✅ Documentation published
- ✅ No critical bugs

---

## 📋 **SUCCESS CRITERIA**

### v1.0 Must Have:
- [ ] All 4 providers working (OpenAlex, Crossref, arXiv, S2)
- [ ] Conservative deduplication working
- [ ] Export formats (CSV, JSONL, BibTeX)
- [ ] Backwards compatibility maintained
- [ ] Test coverage ≥ 80%
- [ ] Complete documentation
- [ ] Zero critical bugs
- [ ] Performance within 10% of old version
- [ ] 3+ beta testers approve

### v1.0 Must NOT Have:
- ❌ Semantic deduplication (→ v1.1)
- ❌ Paper classification (→ v2.0)
- ❌ TUI interface (→ v2.0)
- ❌ REST API (→ v2.0)
- ❌ Async providers (→ v2.0)

---

## 🎯 **DAILY ROUTINE**

### Every Coding Day:

1. **Morning (30 min):**
   - Review yesterday's progress
   - Check GitHub Actions status
   - Plan today's tasks

2. **Coding Sessions (3-4 hours):**
   - Write code + tests together
   - Commit frequently (atomic commits)
   - Run tests before committing

3. **Evening (15 min):**
   - Push to GitHub
   - Update progress tracker
   - Plan tomorrow

### Every Week:

- **Friday:** Week review meeting (with yourself or team)
- **Weekend:** Documentation update + planning next week

---

## 🔧 **DEVELOPMENT WORKFLOW**

### Git Workflow:

```bash
# Start a feature
git checkout -b feature/core-models

# Work on it
# ... code, test, commit ...

# Before committing
pre-commit run --all-files

# Commit
git commit -m "feat(core): add Document and Query models"

# Push
git push -u origin feature/core-models

# Create PR (optional if solo)
# Merge when tests pass
```

### Commit Message Convention:

```
feat(scope): add new feature
fix(scope): bug fix
docs(scope): documentation update
test(scope): add tests
refactor(scope): code refactoring
chore(scope): maintenance tasks
```

### Testing Workflow:

```bash
# Run all tests
pytest

# Run specific test
pytest tests/unit/test_core/test_models.py

# Run with coverage
pytest --cov=slr --cov-report=html

# Run benchmarks
pytest tests/benchmarks/ --benchmark-only

# Run only fast tests (during development)
pytest -m "not slow"
```

---

## 📊 **PROGRESS TRACKING**

### Create a GitHub Project Board:

**Columns:**
- 📋 Backlog
- 🏗️ In Progress
- 👀 In Review
- ✅ Done

**Cards for each week's tasks**

### Weekly Metrics to Track:

- [ ] Test coverage percentage
- [ ] Number of tests passing
- [ ] Performance benchmarks
- [ ] Documentation pages completed
- [ ] Bug count (should decrease over time)

---

## 🚨 **RISK MANAGEMENT**

### If You Fall Behind:

**Week 3-4:** Can skip compatibility layer temporarily  
**Week 5-6:** Focus on 3 providers instead of 4 (drop S2 to v1.1)  
**Week 7:** Dedup is critical - DO NOT SKIP  
**Week 8:** Can reduce export formats to CSV + JSONL only  
**Week 9:** Beta testing can be shortened to 3 days  

### Red Flags to Watch:

- ⚠️ Test coverage drops below 70%
- ⚠️ Performance >20% worse than old version
- ⚠️ More than 5 critical bugs in beta
- ⚠️ Documentation <50% complete by Week 8

### Emergency Contacts:

- Stack Overflow for technical issues
- GitHub Discussions for architectural questions
- Reddit r/learnpython for learning

---

## 🎓 **LEARNING RESOURCES**

### If You Need Help With:

**Pydantic:**
- Official docs: https://docs.pydantic.dev/

**Pytest:**
- Official docs: https://docs.pytest.org/

**Click (for CLI):**
- Official docs: https://click.palletsprojects.com/

**Type Hints:**
- mypy docs: https://mypy.readthedocs.io/

**Architecture:**
- Clean Architecture book (Robert C. Martin)
- Cosmic Python: https://www.cosmicpython.com/

---

## ✅ **READY TO START?**

### Your Next 3 Actions:

1. **Run the setup commands** (from "IMMEDIATE ACTIONS" section above)
2. **Install dependencies** (from pyproject.toml I'm creating)
3. **Start coding** `slr/core/models.py`

### Files Being Created for You:

1. `pyproject.toml` - Project configuration
2. `.github/workflows/test.yml` - CI/CD pipeline
3. `.pre-commit-config.yaml` - Code quality hooks
4. `setup_project.bat` - Windows batch script to run all setup
5. `CHANGELOG.md` - Version history
6. `.gitignore` - Ignore patterns

---

## 🎉 **LET'S BUILD THIS!**

The plan is finalized. The structure is clear. The timeline is realistic.

**Start Date:** Today (November 14, 2025)  
**First Milestone:** Core models working by November 20, 2025  
**Release Date:** January 23, 2026

You've got this! 🚀

---

## 📞 **Questions Before Starting?**

If anything is unclear:
1. Check the detailed week-by-week plan above
2. Look at the code examples in PLAN_V2_REVIEW.md
3. Start coding - questions often answer themselves

**Now go create `slr/core/models.py` and let's ship v1.0!**

