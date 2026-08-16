# Dataset Footprint Summary

| Source | Downloaded bytes | Downloaded file count | Linked-only count | Adoption status |
| --- | --- | --- | --- | --- |
| alphafold | 2226 | 1 | 0 | not_adopted |
| asd | 0 | 0 | 1 | not_adopted |
| baseline_tools | 11821 | 2 | 0 | not_adopted |
| biogrid | 0 | 0 | 1 | not_adopted |
| biolip | 0 | 0 | 2 | not_adopted |
| cryptobench | 1282249609 | 44 | 1 | not_adopted |
| pcna_structures | 1285208 | 4 | 0 | not_adopted |
| pocketminer | 14656 | 1 | 1 | not_adopted |
| scpdb | 0 | 0 | 1 | not_adopted |
| string | 0 | 0 | 1 | not_adopted |
| pdbbind | 0 | 0 | 0 | not_adopted |

All files remain quarantined. The 20 GB total budget remains active; no new bulk file over 500 MB was downloaded in this remediation packet.

## Provenance

- Date: 2026-05-27T19:09:22-04:00
- Command: `python scripts/phase2_remediation_packet.py`
- Source paths: `reports/phase2/cryptobench_*`, `data/registries/cryptobench_*`, `data/registries/dataset_inventory.json`, `data/raw_intake/`
- Governance paths: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`
- Confidence: high for local file-derived counts and registry generation; medium for recommended remediation status; low for unresolved homolog safety until clustering is run.
- Evidence status: verified for local artifacts; inferred for planning recommendations; uncertain for final scientific usability.
