# PCNA Contamination Screen

## Status

- Final audit status: `EXACT_PCNA_CONTAMINATION_DETECTED_HOMOLOG_RISK_UNRESOLVED`
- PCNA isolation is not frozen.

## Exact Screens Run

- Exact dataset UniProt screen for human PCNA `P12004`: 1 record hits.
- Required CIF text screen terms: `p12004`, `pcna`, `proliferating cell nuclear antigen`, `pol30`, `sliding clamp`, `dna sliding clamp`, `beta clamp`, `dna polymerase iii beta`.
- Required CIFs with PCNA/sliding-clamp term hits: 4.

## Hits

- Dataset record: apo `5e0v` fold `test`, holo `3vkx`, UniProt `P12004`, ligand `T3` `301`.
- CIF text hit `2xur`: sliding clamp
- CIF text hit `3bep`: sliding clamp
- CIF text hit `3vkx`: p12004, pcna, proliferating cell nuclear antigen
- CIF text hit `5e0v`: p12004, pcna, proliferating cell nuclear antigen, sliding clamp

## Interpretation Limits

- This is a local exact-text and exact-UniProt screen, not a homolog search.
- Absence of `P12004` and PCNA text hits does not exclude PCNA-like clamps or distant structural homologs.
- A governed sequence-cluster and structural-similarity screen is still required before any split freeze or PCNA final-claim holdout statement.

## Provenance

- Date: 2026-05-27T18:29:47-04:00
- Command: `python scripts/cryptobench_deep_audit.py`
- Source paths: `data/raw_intake/cryptobench/metadata_files/`, `data/raw_intake/cryptobench/labels_or_splits/`, `data/raw_intake/cryptobench/files/672a0171eae0bff252ba9ea3_cif-files.zip`
- Governance paths: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `14_CLAIM_POLICY.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`
- Confidence: high for local schema/count/hash/readability checks; medium for label-semantic interpretation from local README; low for homolog exclusion because no sequence clustering was run.
- Evidence status: verified for local files and machine checks; inferred for biological meaning; uncertain for final scientific usability.
