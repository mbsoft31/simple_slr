# Simple SLR Development Makefile
# Cross-platform compatible (use 'make' on Unix, 'make' via Git Bash on Windows)

.PHONY: help install install-dev test test-unit test-integration test-cov test-watch lint format type-check quality clean docs serve-docs build publish

# Default target
.DEFAULT_GOAL := help

# Colors for output (works on Unix/Mac, degrades gracefully on Windows)
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Simple SLR Development Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# Installation
install: ## Install package in normal mode
	pip install -e .

install-dev: ## Install package with development dependencies
	pip install -e ".[dev]"

# Testing
test: ## Run all tests
	pytest

test-unit: ## Run only unit tests
	pytest tests/unit -v

test-integration: ## Run only integration tests
	pytest tests/integration -v

test-cov: ## Run tests with coverage report
	pytest --cov=slr --cov-report=html --cov-report=term-missing

test-cov-xml: ## Run tests with XML coverage (for CI)
	pytest --cov=slr --cov-report=xml --cov-report=term

test-watch: ## Run tests in watch mode (requires pytest-watch)
	pytest-watch

test-fast: ## Run tests without slow tests
	pytest -m "not slow"

test-verbose: ## Run tests with verbose output
	pytest -vv -s

# Code Quality
lint: ## Run linting checks
	flake8 slr tests --max-line-length=100 --extend-ignore=E203
	@echo "$(GREEN)✓ Linting passed$(NC)"

format: ## Format code with black and isort
	black slr tests
	isort slr tests
	@echo "$(GREEN)✓ Code formatted$(NC)"

format-check: ## Check if code needs formatting
	black --check slr tests
	isort --check-only slr tests

type-check: ## Run type checking with mypy
	mypy slr
	@echo "$(GREEN)✓ Type checking passed$(NC)"

quality: format lint type-check ## Run all quality checks
	@echo "$(GREEN)✓ All quality checks passed$(NC)"

# Pre-commit
pre-commit-install: ## Install pre-commit hooks
	pre-commit install

pre-commit-run: ## Run pre-commit on all files
	pre-commit run --all-files

# Cleaning
clean: ## Clean generated files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .tox/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type f -name '*~' -delete
	@echo "$(GREEN)✓ Cleaned$(NC)"

clean-outputs: ## Clean output directories
	rm -rf outputs/*/
	@echo "$(GREEN)✓ Output directories cleaned$(NC)"

# Documentation
docs: ## Build documentation
	@echo "Documentation target - to be implemented"

serve-docs: ## Serve documentation locally
	@echo "Documentation serving - to be implemented"

# Building and Publishing
build: clean ## Build distribution packages
	python -m build
	@echo "$(GREEN)✓ Build complete$(NC)"

publish-test: build ## Publish to TestPyPI
	python -m twine upload --repository testpypi dist/*

publish: build ## Publish to PyPI
	python -m twine upload dist/*

# Development workflow
dev-setup: install-dev pre-commit-install ## Complete development setup
	@echo "$(GREEN)✓ Development environment ready$(NC)"

check: format lint type-check test-fast ## Quick check before commit
	@echo "$(GREEN)✓ All checks passed - ready to commit!$(NC)"

ci: format-check lint type-check test-cov-xml ## Run CI checks locally
	@echo "$(GREEN)✓ CI checks passed$(NC)"

# Benchmarks
benchmark: ## Run performance benchmarks
	pytest tests/benchmarks/ --benchmark-only

# Coverage reports
coverage-html: test-cov ## Generate HTML coverage report and open it
	@echo "$(GREEN)Coverage report generated at htmlcov/index.html$(NC)"

# Version management
version: ## Show current version
	@python -c "import tomli; print(tomli.load(open('pyproject.toml', 'rb'))['project']['version'])"

# Quick run commands (legacy compatibility)
run-search: ## Run search with example config
	python -m slr.cli search --config config.example.yml --queries queries.yml

run-dedup: ## Run deduplication
	python -m slr.cli deduplicate --input outputs/ --output dedup_results/

# Database/Cache management
reset-cache: ## Clear any caches
	rm -rf .cache/
	@echo "$(GREEN)✓ Cache cleared$(NC)"

dupes:
	$(PYTHON) duplicate_checker.py --input $(OUTDIR)/global_dedup.csv --out potential_duplicates.csv --threshold 0.86

bibtex:
	$(PYTHON) bibtex_export.py --input $(OUTDIR)/global_dedup.csv --out refs.bib

clean:
	rm -rf $(OUTDIR) streams __pycache__ .pytest_cache
