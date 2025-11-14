PRISMA Counts
=============

Script: `scripts/prisma_counts.py`

Purpose
-------

Compute PRISMA-style counts from raw provider runs and deduplicated outputs:

- Records identified (total and by provider)
- Deduplication members and clusters
- Duplicates removed
- Records after deduplication

Usage
-----

- `python scripts/prisma_counts.py --raw-dir outputs --dedup-dir outputs/dedup_final`

Outputs (written to `--out-dir` or `--dedup-dir`)
-------------------------------------------------

- `prisma_counts.json` — JSON summary including placeholders for screening stages.
- `prisma_summary.csv` — Key metrics as a two-column CSV.
- `prisma_by_source.csv` — Per-provider counts before deduplication.

Notes
-----

- `records_identified` are computed using `all_results.*` in each provider run directory to avoid double-counting per-query CSV/JSONL pairs.
- Update the JSON screening placeholders as you progress through title/abstract and full-text screening.
