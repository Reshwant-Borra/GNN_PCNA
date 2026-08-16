# CryptoBench Candidate Cleaned Registry

## Status

- Registry status: `candidate_not_adopted_not_frozen`.
- This is a planning registry, not a frozen dataset registry.

## Recommendation

- Preferred path: cryptic-only benchmark candidate with exclusions, PCNA isolation, residue-failure remediation, and new homolog-aware split.
- Do not use noncryptic auxiliary records for training until missing structures are resolved.

## Counts

- Total cryptic records: 5493.
- Excluded or review-required records: 158.
- PCNA holdout records: 1.
- Full machine-readable registry: `data/registries/cryptobench_candidate_cleaned_registry.json`.

## Provenance

- Date: 2026-05-27T19:09:22-04:00
- Command: `python scripts/phase2_remediation_packet.py`
- Source paths: `reports/phase2/cryptobench_*`, `data/registries/cryptobench_*`, `data/registries/dataset_inventory.json`, `data/raw_intake/`
- Governance paths: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`
- Confidence: high for local file-derived counts and registry generation; medium for recommended remediation status; low for unresolved homolog safety until clustering is run.
- Evidence status: verified for local artifacts; inferred for planning recommendations; uncertain for final scientific usability.
