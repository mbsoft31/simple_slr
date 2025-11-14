Deduplication
=============

Script: `deduplicate_providers.py`

Purpose
-------

Merge records across providers (OpenAlex, Crossref, arXiv, S2) into unique clusters representing the same work, with conservative defaults to minimize false merges.

Matching Strategy
-----------------

1. DOI equality (normalized `https://doi.org/` and `doi:` prefixes removed).
2. arXiv ID equality (from explicit fields, externalIds, and URLs).
3. Exact normalized title + year equality.
4. Fuzzy match within blocks:
   - Block on `(year, sha1(title_fingerprint)[:12])`.
   - Use token-set ratio (RapidFuzz if available, else difflib) with threshold `--min-fuzzy` (default 97).
   - Require `|year_a - year_b| <= --max-year-gap` (default 1).
   - If both have first author family names, require equality.

CLI Usage
---------

- Strict:
  - `python deduplicate_providers.py --input outputs --outdir outputs/dedup_strict`
- Loose thresholds:
  - `python deduplicate_providers.py --input outputs --outdir outputs/dedup_loose --loose`
- Custom thresholds:
  - `--min-fuzzy 95 --max-year-gap 2`

Outputs
-------

- `deduped.jsonl` — One object per cluster (representative + members + identifier sets).
- `clusters.csv` — Summary rows per cluster (size, rep year/title, rep doi/arxiv, counts).
- `members.csv` — All members with cluster_id, source, provider_id, ids, year, title, url.
- Extras:
  - `representatives.jsonl/.csv` — Representative-only view for screening and citation export.
  - `cluster_sources.csv` — Long format per cluster × source counts.
  - `doi_to_cluster.csv`, `arxiv_to_cluster.csv` — Identifier maps.

Safeguards
----------

- Ignores previous dedup outputs and aggregated `all_results.*` to avoid self-ingestion and double-counting.
- Preserves provenance (`source`, `provider_id`, `doi`, `arxiv_id`, `url`).
