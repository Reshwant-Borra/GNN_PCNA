# PCNA Isolation Policy

## Recommendation

Use full PCNA isolation for Phase 2 model development. PCNA and PCNA-like sliding-clamp records must not appear in training, validation, threshold selection, feature-scaler fitting, architecture selection, or split tuning.

## Policy

| Option | Decision | Reason |
| --- | --- | --- |
| Full exclusion from model development | Required | CryptoBench contains exact PCNA contamination and Phase 2 intends PCNA-facing interpretation later. |
| External blind target | Allowed later | Only after model, split, labels, baselines, and report protocol are frozen. |
| Held-out family | Required if homologs/sliding clamps are found | Sequence/structure relatives can leak PCNA-like features. |
| Positive-control only | Allowed with label | PCNA records may be sanity checks, not independent validation. |
| Inference-only target | Allowed later | No tuning or claims from inference-only PCNA targets without downstream gates. |

## Current PCNA Findings

- Exact PCNA record: apo `5e0v` fold `test`, holo `3vkx`, UniProt `P12004`, ligand `T3` `301`.
- CIF text hit `2xur`: sliding clamp.
- CIF text hit `3bep`: sliding clamp.
- CIF text hit `3vkx`: p12004, pcna, proliferating cell nuclear antigen.
- CIF text hit `5e0v`: p12004, pcna, proliferating cell nuclear antigen, sliding clamp.

## Required Before Split Freeze

- Exclude or hold out exact PCNA apo/holo records.
- Screen all CryptoBench structures for PCNA-like sliding clamps using sequence clustering and structural similarity review.
- Record PCNA holdout/positive-control status in the split manifest.
- Human review must approve the PCNA isolation decision.

## Provenance

- Date: 2026-05-27T19:09:22-04:00
- Command: `python scripts/phase2_remediation_packet.py`
- Source paths: `reports/phase2/cryptobench_*`, `data/registries/cryptobench_*`, `data/registries/dataset_inventory.json`, `data/raw_intake/`
- Governance paths: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`
- Confidence: high for local file-derived counts and registry generation; medium for recommended remediation status; low for unresolved homolog safety until clustering is run.
- Evidence status: verified for local artifacts; inferred for planning recommendations; uncertain for final scientific usability.
