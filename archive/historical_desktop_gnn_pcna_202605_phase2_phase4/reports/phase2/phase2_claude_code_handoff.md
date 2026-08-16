# Phase 2 Claude Code Handoff

## Current Status

- Everything remains `raw_unverified`, `not_adopted`, and `not_ready_for_training`.
- Do not train, generate graphs, run MD, freeze labels, freeze splits, or make scientific claims.

## Track A Outputs

- `reports/phase2/cryptobench_adoption_decision.md`
- `reports/phase2/pcna_isolation_policy.md`
- `reports/phase2/cryptobench_leakage_remediation.md`
- `reports/phase2/label_supervision_risks.md`
- `reports/phase2/proposed_label_policy.md`
- `reports/phase2/residue_mapping_failure_analysis.md`
- `reports/phase2/proposed_phase2_split_strategy.md`
- `reports/phase2/cryptobench_candidate_cleaned_registry.md`
- `data/registries/potential_homolog_risks.json`
- `data/registries/residue_mapping_failures.json`
- `data/registries/cryptobench_candidate_cleaned_registry.json`

## Track B Outputs

- `reports/phase2/auxiliary_dataset_audit.md`
- `reports/phase2/benchmark_role_classification.md`
- `reports/phase2/auxiliary_acquisition_status_summary.md`
- `reports/phase2/dataset_footprint_summary.md`
- `data/registries/auxiliary_dataset_role_summary.json`
- `data/registries/dataset_inventory.json`

## Highest-Priority Next Work

1. Human review: decide CryptoBench cryptic-only adoption with exclusions versus benchmark-only/defer.
2. Choose sequence clustering tool/threshold and run clustering before split freeze.
3. Resolve or mask residue mapping failures.
4. Approve a partial-label/positive-unlabeled supervision policy.
5. Draft a split manifest only after PCNA isolation and grouping rules are accepted.

## Provenance

- Date: 2026-05-27T19:09:22-04:00
- Command: `python scripts/phase2_remediation_packet.py`
- Source paths: `reports/phase2/cryptobench_*`, `data/registries/cryptobench_*`, `data/registries/dataset_inventory.json`, `data/raw_intake/`
- Governance paths: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`
- Confidence: high for local file-derived counts and registry generation; medium for recommended remediation status; low for unresolved homolog safety until clustering is run.
- Evidence status: verified for local artifacts; inferred for planning recommendations; uncertain for final scientific usability.
