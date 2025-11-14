MAILTO ?= you@example.com
S2_KEY ?=
QUERIES ?= queries.json
PROVIDERS ?= openalex,crossref,s2,arxiv
OUTDIR ?= outputs
STREAM_DIR ?= 
ANALYSIS_OUT ?= analysis
SCOPE ?= any
TOPK ?= 1
TOPICS ?= plant pathology,pest management,crop disease

PY := python
VENV := .venv
PIP := $(VENV)/bin/pip
PYTHON := $(VENV)/bin/python
PYTEST := $(VENV)/bin/pytest
FLAKE := $(VENV)/bin/flake8

.PHONY: venv install test lint run run-stream run-topics analyze analyze-enrich screen dupes bibtex clean

venv:
	$(PY) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

install: venv

test:
	$(PYTEST)

lint:
	$(FLAKE) .

run:
	$(PYTHON) enhanced_query_script.py --mailto "$(MAILTO)" --s2-api-key "$(S2_KEY)" --queries-file "$(QUERIES)" --outdir "$(OUTDIR)" --providers "$(PROVIDERS)"

run-stream:
	$(PYTHON) enhanced_query_script.py --mailto "$(MAILTO)" --s2-api-key "$(S2_KEY)" --queries-file "$(QUERIES)" --outdir "$(OUTDIR)" --providers "$(PROVIDERS)" --stream-dir "$(STREAM_DIR)"

run-topics:
	$(PYTHON) enhanced_query_script.py --mailto "$(MAILTO)" --s2-api-key "$(S2_KEY)" --queries-file "$(QUERIES)" --outdir "$(OUTDIR)" --providers "$(PROVIDERS)" --topic-names "$(TOPICS)" --topic-scope "$(SCOPE)" --topics-topk $(TOPK)

analyze:
	$(PYTHON) results_analyzer.py --inputs $(OUTDIR) --outdir $(ANALYSIS_OUT) --mailto "$(MAILTO)"

analyze-enrich:
	$(PYTHON) results_analyzer.py --inputs $(OUTDIR) --outdir $(ANALYSIS_OUT) --mailto "$(MAILTO)" --enrich-openalex

screen:
	$(PYTHON) screening_cli.py --input $(OUTDIR)/global_dedup.csv --out screening.csv

dupes:
	$(PYTHON) duplicate_checker.py --input $(OUTDIR)/global_dedup.csv --out potential_duplicates.csv --threshold 0.86

bibtex:
	$(PYTHON) bibtex_export.py --input $(OUTDIR)/global_dedup.csv --out refs.bib

clean:
	rm -rf $(OUTDIR) streams __pycache__ .pytest_cache
