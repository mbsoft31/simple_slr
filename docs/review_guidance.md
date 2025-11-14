Documentation for Reviewers, Project Team and Supervisors
=========================================================

1. Review Purpose and Objectives
--------------------------------

This review maps and synthesises research on machine‑learning and computer‑vision methods for detecting plant diseases and pests under field or realistic conditions. It follows best‑practice guidance: PRISMA‑ScR for scoping reviews (20 essential items and two optional items; see pubmed.ncbi.nlm.nih.gov) and PRISMA 2020 for systematic reviews (see equator-network.org). Following these guidelines ensures transparent and comprehensive reporting.

2. Search and Data Sources
--------------------------

Searches were run across OpenAlex, Crossref, arXiv and Semantic Scholar using pre‑defined queries stored in the `queries/` folder. Raw results (CSV and JSONL) for each provider are in the `outputs/` directory. These files form the canonical search log and should not be edited.

3. Deduplication and PRISMA Counts
----------------------------------

Records were deduplicated with `deduplicate_providers.py` to produce unique clusters of studies. Running `scripts/prisma_counts.py` (14 Nov 2025) produced the following counts:

- Records identified (total): 9,635 — unique records from all provider runs (from `all_results.*`).
- Records identified by source: openalex = 2,503; crossref = 6,400; s2 = 615; arxiv = 117.
- Members in deduplication: 19,270 — all records ingested.
- Clusters (unique studies): 6,688 — unique works after deduplication.
- Duplicates removed: 12,582 — members minus clusters.
- Records for screening: 6,688 — number of studies to screen.

The JSON file `prisma_counts.json` contains these numbers and placeholders for subsequent screening stages. Update it as screening progresses.

4. Inclusion and Exclusion Criteria
-----------------------------------

Apply these criteria consistently. Do not modify them without team consensus.

4.1 Inclusion Criteria

- Population: Cultivated crops, horticultural plants or forestry species imaged under field, greenhouse or realistic conditions (e.g., UAV, smartphone). Leaf, stem or fruit studies are acceptable if they relate to field diagnosis.
- Intervention/Index test: ML or deep‑learning methods for disease, pest or stress detection/diagnosis from visual data. Tasks include classification, detection, segmentation or multi‑task models using RGB, multispectral/hyperspectral, thermal or other imaging.
- Outcomes: Studies reporting performance metrics (accuracy, F1, precision, recall, AUC, AP/mAP, etc.). Note external validation, cross‑domain testing or robustness evaluations when present.
- Study types: Primary empirical studies (journal articles, conference papers, preprints). Both peer‑reviewed and grey literature (e.g., arXiv) are included. Must be in English.
- Publication date: No date restrictions unless specified; always record publication year.

4.2 Exclusion Criteria

- Non‑visual or non‑ML methods: Exclude if no ML is used (e.g., rule‑based) or if data are non‑visual (e.g., spectroscopy without imaging).
- Irrelevant tasks: Exclude studies focusing solely on weed detection, yield estimation, biomass measurement or phenotyping unrelated to disease/pest detection.
- Laboratory‑only studies: Exclude if imaging is exclusively in controlled lab conditions with no field or semi‑field component. Mixed lab–field studies are acceptable.
- Simulated or synthetic datasets: Exclude if only synthetic images are used with no real‑world validation.
- Reviews and surveys: Exclude secondary research (reviews, meta‑analyses), though may inform citation chasing.
- Language: Exclude studies not in English unless a translation is available.

5. Screening Process
--------------------

5.1 Title/Abstract Screening

- Each cluster from `representatives.csv` and `screening_generic.csv` must be independently assessed by two reviewers.
- Use columns `screener1_decision`, `screener1_reason`, `screener2_decision`, `screener2_reason` to record include/exclude (1/0) and brief reasons (e.g., “weed detection task”).
- Use standardised reason codes: `non-ml`, `non-visual`, `irrelevant`, `lab-only`, `review`. If unsure, mark “maybe” or leave blank for discussion.
- After both reviewers finish, a conflict resolver reviews conflicts and fills `final_decision` and `final_reason`. Calculate Cohen’s κ to assess inter‑rater agreement.

5.2 Full‑Text Retrieval and Screening

- For studies included at title/abstract stage, obtain full texts via DOI, arXiv or library access; note preprint vs published.
- Apply the same inclusion/exclusion criteria to the full text. Add columns such as `ft_decision` and `ft_reason` if needed.
- Document reasons for exclusion carefully for PRISMA reporting.

6. Data Extraction
------------------

Use `templates/extraction_template.csv` to capture detailed information. Copy the template to your working directory and complete one row per cluster.

- Bibliographic data (title, year, venue, DOI, arXiv ID, URL) can be pre‑filled from `representatives.csv`.
- Study focus: crop species, pathogen type (virus, fungus, insect), imaging modality, platform (handheld, UAV, robot, smartphone), setting (field, lab, mixed).
- Method: task (classification, detection, segmentation), architecture (ResNet/YOLO/Transformer), domain adaptation/augmentation, transfer learning.
- Evaluation: datasets used, train/test split, external validation, metrics and primary values with CIs/SEs; robustness tests and dataset‑shift evaluation.
- Reproducibility: code/data availability; reproducibility notes (random seed, repetitions).
- Risk of bias: narrative notes (sample sizes, class imbalance, leakage risks, lack of external validation).
- Each study should be extracted by two independent extractors; record initials in `extractor1` and `extractor2`.

7. Risk of Bias and Quality Assessment
--------------------------------------

- Choose appropriate tools: QUADAS‑2 for diagnostic accuracy analogues, PROBAST for prediction models; adapt to ML contexts (external validation, domain shift, leakage, class imbalance, robustness tests).
- For reporting quality, apply AI‑specific extensions (TRIPOD‑AI or CONSORT‑AI) where relevant.
- Summarise assessments in a structured table and include narrative explanations.

8. Reporting and Next Steps
---------------------------

- Update PRISMA counts at each screening stage and produce a PRISMA flow diagram.
- Train reviewers: share this document and the screening export; run a calibration exercise.
- Conduct screening, resolve conflicts, and update the screening file. After final inclusion decisions, proceed with full‑text retrieval and data extraction.
- Synthesize evidence: For a scoping review, map studies by task, modality and crop and highlight gaps. For a systematic review, harmonise metrics and consider meta‑analysis if appropriate.
- Prepare the final report per PRISMA‑ScR or PRISMA 2020. Include search strategy, PRISMA flow, characteristics of included studies, risk‑of‑bias assessments and synthesis results. Append extraction form, exclusion reasons and full references.

9. Contacts and Roles
---------------------

- Lead reviewer/Coordinator: [Name] — oversees protocol and timelines.
- Reviewers: [Names] — independent screening and data extraction.
- Conflict resolver/Supervisor: [Name] — resolves screening disagreements and checks extraction consistency.
- Advisory supervisor(s): [Names] — methodological oversight and final approval.

