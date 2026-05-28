# CryptoBench Adoption Decision

## Decision

- Current decision: `not_adopted`.
- Recommended path: `cryptic_only_benchmark_candidate_with_exclusions_and_split_redesign`.
- Do not adopt the full CryptoBench bundle as-is.

## Option Matrix

| Option | Decision | Reason |
| --- | --- | --- |
| Adopted with exclusions | Possible later | Requires PCNA isolation, repeated-holo grouping/exclusion, residue mapping remediation, homolog clustering, and human review. |
| Cryptic-only adoption | Preferred candidate path | `dataset.json` has complete CIF coverage; noncryptic auxiliary records have missing structures and unresolved semantics. |
| Benchmark-only | Acceptable interim status | Can remain an audited benchmark candidate while remediation is completed. |
| Deferred/rejected | Not required yet | Current blockers are serious but appear remediable for cryptic-only use if human review approves. |

## Required Exclusions Or Holds Before Any Adoption

- Exact PCNA record: apo `5e0v`, holo `3vkx`, UniProt `P12004`.
- PCNA-like/sliding-clamp hits pending sequence and structural review: `2xur`, `3bep`, `3vkx`, `5e0v`.
- Repeated-holo cross-fold systems until grouped or excluded.
- Records with unresolved residue mapping failures until corrected or masked.
- Noncryptic auxiliary records unless missing structures are acquired/subsetted and audited.

## Adoption Preconditions

- Human dataset adoption review.
- PCNA isolation policy approval.
- Sequence/homolog clustering and split redesign.
- Label policy approval for partial/proxy supervision.
- Residue mapping remediation or explicit masking policy.

## Provenance

- Date: 2026-05-27T19:09:22-04:00
- Command: `python scripts/phase2_remediation_packet.py`
- Source paths: `reports/phase2/cryptobench_*`, `data/registries/cryptobench_*`, `data/registries/dataset_inventory.json`, `data/raw_intake/`
- Governance paths: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`
- Confidence: high for local file-derived counts and registry generation; medium for recommended remediation status; low for unresolved homolog safety until clustering is run.
- Evidence status: verified for local artifacts; inferred for planning recommendations; uncertain for final scientific usability.
