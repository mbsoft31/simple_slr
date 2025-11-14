Quickstart
==========

This quickstart gets you from provider outputs to deduplicated clusters, PRISMA counts, and screening exports.

Prerequisites
-------------

- Python 3.10+ (tested with 3.14)
- Optional: create and activate a virtualenv and install requirements:

  - `python -m venv .venv`
  - `./.venv/Scripts/Activate.ps1` (Windows PowerShell)
  - `pip install -r requirements.txt`

Inputs
------

- `queries/` contains versioned search queries.
- `outputs/` contains provider run folders (e.g., `openalex_run_*`, `crossref_run_*`, `arxiv_run_*`, `s2_run_*`) with per-query `Q##_results.*` and aggregated `all_results.*` files.

Step 1 — Deduplicate
--------------------

- Strict:
  - `python deduplicate_providers.py --input outputs --outdir outputs/dedup_strict`
- Loose (slightly lower fuzzy threshold, larger year gap):
  - `python deduplicate_providers.py --input outputs --outdir outputs/dedup_loose --loose`

Outputs include:

- `deduped.jsonl` (all clusters with representative + members)
- `clusters.csv` (one row per cluster)
- `members.csv` (all source members per cluster)
- Extras: `representatives.csv/.jsonl`, `cluster_sources.csv`, `doi_to_cluster.csv`, `arxiv_to_cluster.csv`

Step 2 — PRISMA Counts
----------------------

- `python scripts/prisma_counts.py --raw-dir outputs --dedup-dir outputs/dedup_strict`
- Writes `prisma_counts.json`, `prisma_summary.csv`, `prisma_by_source.csv` into the dedup directory.

Step 3 — Screening Export
-------------------------

- Generic screening sheet:
  - `python scripts/prepare_screening_export.py --dedup-jsonl outputs/dedup_strict/deduped.jsonl --out outputs/dedup_strict/screening_generic.csv --format generic`
- Rayyan/ASReview formats:
  - `--format rayyan` or `--format asreview`

Step 4 — Source Coverage (wide)
-------------------------------

- `python scripts/source_coverage_wide.py --long outputs/dedup_strict/cluster_sources.csv --out outputs/dedup_strict/cluster_sources_wide.csv`

Step 5 — Extraction Template
----------------------------

- Copy `templates/extraction_template.csv` to your working folder and fill one row per included cluster.

Notes
-----

- The dedup script automatically ignores previous dedup outputs and aggregated `all_results.*` to avoid double-counting/self-ingestion.
- For PRISMA counts, provider totals are read from `all_results.*` in each provider run directory.
