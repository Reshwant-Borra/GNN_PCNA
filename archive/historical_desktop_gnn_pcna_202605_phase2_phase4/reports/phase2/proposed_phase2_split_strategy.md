# Proposed Phase 2 Split Strategy

## Status

- Strategy status: `draft_not_frozen`.
- Split freeze remains blocked.

## Candidate Split Design

1. Start from CryptoBench cryptic `dataset.json` only.
2. Remove or isolate exact PCNA and PCNA-like sliding-clamp records.
3. Build system groups using UniProt, apo/holo pair, ligand variants, repeated holo structures, sequence cluster, and structural review flags.
4. Assign train/validation/test by group, never by residue or graph.
5. Keep PCNA/external targets out of train/validation/test model development if they may support later PCNA interpretation.

## Candidate Split Families

| Candidate | Purpose | Status |
| --- | --- | --- |
| Sequence-cluster split | Controls close homolog leakage | planned; tool/threshold not frozen |
| Homolog-aware split | Groups families beyond exact UniProt | planned; requires clustering |
| Family-isolation split | Stress-tests generalization | optional after clusters exist |
| Apo/holo grouped split | Prevents paired-structure leakage | required |
| PCNA holdout split | Protects PCNA interpretation | required if PCNA remains in any source set |

## Freeze Preconditions

- Sequence clustering completed and registered.
- Repeated holo PDB IDs resolved by grouping/exclusion.
- PCNA isolation approved.
- Label policy approved.
- Human split review recorded.

## Provenance

- Date: 2026-05-27T19:09:22-04:00
- Command: `python scripts/phase2_remediation_packet.py`
- Source paths: `reports/phase2/cryptobench_*`, `data/registries/cryptobench_*`, `data/registries/dataset_inventory.json`, `data/raw_intake/`
- Governance paths: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`
- Confidence: high for local file-derived counts and registry generation; medium for recommended remediation status; low for unresolved homolog safety until clustering is run.
- Evidence status: verified for local artifacts; inferred for planning recommendations; uncertain for final scientific usability.
