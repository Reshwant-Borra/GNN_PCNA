# Benchmark Role Classification Table

| Source | Role | Keep recommendation | Supervision meaning | Limitation |
| --- | --- | --- | --- | --- |
| alphafold | targeted PCNA predicted-structure context | yes_context_only_if_needed | none | predicted structure is not pocket truth |
| asd | allosteric context/reference | yes_as_context_not_training_labels | allosteric annotations only after entry-level audit | not PCNA cryptic-pocket supervision by default |
| baseline_tools | fpocket/P2Rank baseline tooling metadata | yes_for_baseline_planning | tool predictions only | installation/output schemas not verified |
| biogrid | targeted PCNA interaction context | yes_context_only | interaction metadata only after API/license review | not structural pocket labels |
| biolip | auxiliary ligand-contact/proxy context | yes_linked_only_until_terms_and_schema_review | ligand contacts if later acquired | not cryptic-pocket truth |
| cryptobench | primary benchmark candidate after remediation | yes_with_exclusions_pending_human_review | proxy cryptic pocket selections | not true negatives; PCNA contamination; split redesign required |
| pcna_structures | targeted PCNA experimental structure source | requires_review | unknown | requires_schema_review |
| pocketminer | baseline/method reference | yes_for_baseline_review | method outputs only; not labels | overlap/leakage with CryptoBench must be audited |
| scpdb | auxiliary binding-pocket/proxy source | maybe_terms_and_bulk_size_unresolved | binding pocket/protein-ligand records if later acquired | not cryptic-pocket truth; licensing/bulk unresolved |
| string | targeted PCNA functional association context | yes_context_only | functional association metadata only | not structural pocket labels |
| pdbbind | background affinity/source lead only | exclude_from_primary_phase2_benchmark | affinity/protein-ligand complexes | not cryptic-pocket benchmark |

## Provenance

- Date: 2026-05-27T19:09:22-04:00
- Command: `python scripts/phase2_remediation_packet.py`
- Source paths: `reports/phase2/cryptobench_*`, `data/registries/cryptobench_*`, `data/registries/dataset_inventory.json`, `data/raw_intake/`
- Governance paths: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`
- Confidence: high for local file-derived counts and registry generation; medium for recommended remediation status; low for unresolved homolog safety until clustering is run.
- Evidence status: verified for local artifacts; inferred for planning recommendations; uncertain for final scientific usability.
