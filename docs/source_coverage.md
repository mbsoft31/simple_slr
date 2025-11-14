Source Coverage (Wide)
======================

Script: `scripts/source_coverage_wide.py`

Purpose
-------

Convert the long-format `cluster_sources.csv` (cluster_id, source, count) into a wide table with one row per cluster and columns per source (e.g., `arxiv_count`, `crossref_count`, `openalex_count`, `s2_count`).

Usage
-----

- `python scripts/source_coverage_wide.py --long outputs/dedup_final/cluster_sources.csv --out outputs/dedup_final/cluster_sources_wide.csv`

Notes
-----

- Use the wide table to quickly assess the source mix per cluster and identify clusters supported by multiple providers.
