Repository Structure
====================

Key files and folders:

- `queries/` — Versioned search queries for providers.
- `outputs/` — Raw provider results per run (per-query CSV/JSONL and aggregated `all_results.*`).
- `deduplicate_providers.py` — Cross-provider deduplication and extras writer.
- `arxiv_provider.py`, `crossref_provider.py`, `results_analyzer.py`, etc. — Provider utilities and helpers.
- `scripts/` — Helper scripts for PRISMA counts, screening export, coverage pivot.
- `templates/` — Extraction template CSV.

Deduplication Outputs (per `--outdir`):

- `deduped.jsonl` — All clusters with representative record + members and provenance.
- `clusters.csv` — One row per cluster (id, size, rep year/title/doi/arxiv, counts).
- `members.csv` — One row per member record (cluster_id, source, ids, year, title, url).
- `representatives.jsonl/.csv` — Representative-only rows, suitable for screening and citation export.
- `cluster_sources.csv` — Cluster × source counts (long format).
- `doi_to_cluster.csv`, `arxiv_to_cluster.csv` — Identifier maps for downstream joins.
