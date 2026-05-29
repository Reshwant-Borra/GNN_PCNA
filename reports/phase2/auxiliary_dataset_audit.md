# Auxiliary Dataset Audit

## Status

- Auxiliary assets remain `raw_unverified` and `not_adopted`.
- None are accepted cryptic-pocket truth.

## Findings

- BioLiP/Q-BioLiP: useful ligand-contact context only after terms/schema review; not cryptic-pocket truth.
- scPDB: possible binding-pocket proxy source, but terms/bulk/schema unresolved.
- ASD: allosteric context/reference only unless entry-level labels are separately audited.
- PocketMiner: useful baseline/method reference; overlap with CryptoBench must be audited.
- fpocket/P2Rank: baseline tool metadata acquired; installation/output schema still pending.
- BioGRID/STRING: PCNA context only, not structural pocket labels.
- AlphaFold P12004: targeted predicted-structure metadata only, not supervision.
- PDBbind: excluded from primary benchmark role; retain only as background/source lead if needed.

## Provenance

- Date: 2026-05-27T19:09:22-04:00
- Command: `python scripts/phase2_remediation_packet.py`
- Source paths: `reports/phase2/cryptobench_*`, `data/registries/cryptobench_*`, `data/registries/dataset_inventory.json`, `data/raw_intake/`
- Governance paths: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`
- Confidence: high for local file-derived counts and registry generation; medium for recommended remediation status; low for unresolved homolog safety until clustering is run.
- Evidence status: verified for local artifacts; inferred for planning recommendations; uncertain for final scientific usability.
