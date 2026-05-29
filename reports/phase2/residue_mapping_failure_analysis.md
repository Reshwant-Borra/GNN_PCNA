# Residue Mapping Failure Analysis

## Summary

- Selection tokens checked against present CIF atom-site residue IDs: 409944.
- Mapping failures: 721.
- Selection tokens skipped because referenced CIFs are missing: 180488.

## Failure Reasons

| Reason | Count |
| --- | --- |
| matches_label_seq_id_not_auth_seq_id | 420 |
| residue_token_absent_from_atom_site | 297 |
| residue_token_exists_on_other_chain | 4 |

## Interpretation

- Failures include auth/label numbering mismatches, residues absent from resolved atom-site records, and missing auxiliary CIF references.
- These failures block graph generation until a residue-node and masking policy is approved.
- Full machine-readable failure table: `data/registries/residue_mapping_failures.json`.

## Provenance

- Date: 2026-05-27T19:09:22-04:00
- Command: `python scripts/phase2_remediation_packet.py`
- Source paths: `reports/phase2/cryptobench_*`, `data/registries/cryptobench_*`, `data/registries/dataset_inventory.json`, `data/raw_intake/`
- Governance paths: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`
- Confidence: high for local file-derived counts and registry generation; medium for recommended remediation status; low for unresolved homolog safety until clustering is run.
- Evidence status: verified for local artifacts; inferred for planning recommendations; uncertain for final scientific usability.
