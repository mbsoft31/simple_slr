Screening Export
================

Script: `scripts/prepare_screening_export.py`

Purpose
-------

Generate a screening CSV (generic or tool-specific) from `deduped.jsonl`, including title, abstract, authors, year, journal, DOI, URL, and identifiers, plus empty decision columns for dual independent screening.

Usage
-----

- Generic:
  - `python scripts/prepare_screening_export.py --dedup-jsonl outputs/dedup_final/deduped.jsonl --out outputs/dedup_final/screening_generic.csv --format generic`
- Rayyan:
  - `--format rayyan` (columns adapted for Rayyan)
- ASReview:
  - `--format asreview`

Output Columns (generic)
------------------------

- cluster_id, title, abstract, authors, year, journal, doi, url, source, provider_id, n_dois, n_arxiv, size
- screener1_decision, screener1_reason, screener2_decision, screener2_reason, conflict_resolved_by, final_decision, final_reason

Tips
----

- Use `representatives.csv` alongside this export for quick joins and filtering.
- Keep the screening file under version control; record decision changes transparently.
