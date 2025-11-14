Extraction Template & Codebook
==============================

Template: `templates/extraction_template.csv`

Purpose
-------

Provide a structured sheet for data extraction after screening. Fill one row per included cluster.

Key Columns
-----------

- Identifiers: cluster_id, title, year, venue, doi, arxiv_id, url
- Decisions: include, reason_exclude
- Study focus: population, crop_species, pathogen_type, imaging_modality, platform, setting_lab_field
- Method: task, method_architecture, domain_adaptation, augmentation, transfer learning notes (if applicable)
- Evaluation: datasets_used, train_test_protocol, metrics_reported, main_metric, main_value, ci_or_se, external_validation, robustness_tests
- Reproducibility: code_available, data_available, reproducibility_notes
- Bias/quality: risk_of_bias_notes
- People: screener1, screener2, extractor1, extractor2

Workflow Tips
-------------

- Pre-fill bibliographic fields from `representatives.csv` by joining on `cluster_id`.
- Pilot the codebook on a small subset and refine definitions before full extraction.
- Extract in duplicate for a subset to calibrate and measure agreement.
