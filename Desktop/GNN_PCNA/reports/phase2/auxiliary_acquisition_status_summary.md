# Auxiliary Acquisition Status Summary

| Source | Downloaded files | Linked assets | Bytes | License | Schema | Lifecycle |
| --- | --- | --- | --- | --- | --- | --- |
| alphafold | 1 | 0 | 2226 | LICENSE_UNRESOLVED | SCHEMA_PARTIAL | quarantined |
| asd | 0 | 1 | 0 | LICENSE_UNRESOLVED | SCHEMA_UNKNOWN | candidate |
| baseline_tools | 2 | 0 | 11821 | LICENSE_UNRESOLVED | SCHEMA_PARTIAL | quarantined |
| biogrid | 0 | 1 | 0 | LICENSE_UNRESOLVED | SCHEMA_UNKNOWN | candidate |
| biolip | 0 | 2 | 0 | LICENSE_UNRESOLVED | SCHEMA_UNKNOWN | candidate |
| cryptobench | 44 | 1 | 1282249609 | LICENSE_KNOWN | SCHEMA_PARTIAL | quarantined |
| pcna_structures | 4 | 0 | 1285208 | LICENSE_KNOWN | SCHEMA_PARTIAL | quarantined |
| pocketminer | 1 | 1 | 14656 | LICENSE_UNRESOLVED | SCHEMA_PARTIAL | quarantined |
| scpdb | 0 | 1 | 0 | LICENSE_UNRESOLVED | SCHEMA_UNKNOWN | candidate |
| string | 0 | 1 | 0 | LICENSE_UNRESOLVED | SCHEMA_UNKNOWN | candidate |
| pdbbind | 0 | 0 | 0 | not_acquired_this_phase | not_acquired_this_phase | excluded_from_primary_benchmark |

## Provenance

- Date: 2026-05-27T19:09:22-04:00
- Command: `python scripts/phase2_remediation_packet.py`
- Source paths: `reports/phase2/cryptobench_*`, `data/registries/cryptobench_*`, `data/registries/dataset_inventory.json`, `data/raw_intake/`
- Governance paths: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`
- Confidence: high for local file-derived counts and registry generation; medium for recommended remediation status; low for unresolved homolog safety until clustering is run.
- Evidence status: verified for local artifacts; inferred for planning recommendations; uncertain for final scientific usability.
