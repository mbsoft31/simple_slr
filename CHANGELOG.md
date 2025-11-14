# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New modular architecture with `slr/` package
- Pydantic models for data validation (Document, Query, Cluster)
- Token bucket rate limiting for API calls
- Comprehensive error handling with custom exceptions
- Retry decorator with exponential backoff
- Centralized logging configuration
- YAML-based configuration system
- BaseProvider abstraction for search providers
- Normalization utilities for identifiers, text, and authors
- CLI interface with Click
- Pre-commit hooks for code quality
- Comprehensive test suite with pytest
- CI/CD pipeline with GitHub Actions
- Documentation with MkDocs

### Changed
- Refactored providers to use BaseProvider abstraction
- Improved query translation logic for each provider
- Better error messages and debugging information

### Deprecated
- `enhanced_query_script.py` - Use `slr search` command instead
- `deduplicate_providers.py` - Use `slr deduplicate` command instead
- Direct script execution - Use CLI commands instead

### Migration Guide
See `docs/migration/from-v0-to-v1.md` for detailed migration instructions.

---

## [0.9.0] - 2025-11-14

### Added
- Initial monolithic implementation
- Multi-provider search (OpenAlex, Crossref, arXiv, Semantic Scholar)
- Conservative deduplication strategy
- Export to CSV, JSONL, BibTeX formats
- PRISMA flowchart support
- Basic screening workflow

### Notes
This is the last version before the v1.0 refactor. All functionality is preserved
in the new architecture with backwards compatibility maintained through wrapper scripts.

