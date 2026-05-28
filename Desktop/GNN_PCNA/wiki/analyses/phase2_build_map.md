---
type: analysis
status: active
created: 2026-05-27
updated: 2026-05-28
tags: [phase2, build-map, governance]
aliases: [Phase2 Build Map]
confidence: high
evidence_status: verified
---

# Phase2 Build Map

## Governed Build Order

1. Source and scope freeze.
2. Assumption and uncertainty registry.
3. Source registry from `crawls/`.
4. Benchmark limitations review.
5. Dataset and lifecycle registries.
6. Split protocol and human split freeze.
7. Label protocol and human label freeze.
8. Biological data sanity review.
9. Graph generation manifest and graph audit.
10. Red-team audit and null-baseline plan.
11. Readiness gate: stop at governed data.
12. Later only after gates: baselines, training, PCNA prediction, interpretability, MD, claims, publication readiness.

## Implementation Constraint

Do not start with model code. Build governed data and verification artifacts first.

## Current Foundation Artifacts

Checklist items 1-7 now have draft artifacts:

- `reports/phase2/source_of_truth_audit.md`
- `reports/phase2/project_scope_audit.md`
- `data/registries/assumption_registry.json`
- `reports/phase2/scientific_uncertainty_register.md`
- `data/registries/source_registry.json`
- `reports/phase2/benchmark_limitations.md`
- `docs/scientific_governance/DATASET_REGISTRY.md`
- `data/registries/data_lifecycle_registry.json`
- `reports/phase2/split_freeze_plan.md`
- `reports/phase2/label_freeze_plan.md`
- `reports/phase2/human_review_log.md`
- `reports/phase2/biological_data_sanity_review.md`
- `reports/phase2/readiness_gate.md`

Current status as of 2026-05-28: Phase 2 split and label freeze are complete, but first
real training remains blocked until the Phase 3 data pipeline is implemented, audited, and
human-reviewed.

## Phase 3 / Phase 4 Dataset Roles

Phase 3 supervised training and evaluation must use the frozen CryptoBench v2 benchmark:

- `data/registries/split_manifest_frozen.json`
- `data/labels/labels_{apo_pdb_id}.json`
- `data/raw_intake/cryptobench/cif-files/`
- `data/registries/excluded_records.json`

The Friend/40GB crawl must not be used as Phase 3 supervised benchmark training data. The
committed crawl metadata describes a PCNA-focused experimental subset, not a governed,
labeled, clustered, leakage-audited benchmark. Its proper roles are:

1. Phase 4 external inference/discovery after the Phase 3 model is frozen.
2. Future pretraining or dataset expansion only after separate governance, deduplication,
   clustering, benchmark-contamination checks, lifecycle status changes, labeling or
   self-supervision policy, and human approval.

This protects the Phase 3 benchmark from PCNA leakage and avoids turning heuristic crawl
outputs into training truth.

## Provenance

- Source path: `docs/scientific_governance/37_PHASE2_IMPLEMENTATION_PLAN.md`, `reports/phase2/foundation_milestone_status.md`, `.memory/PROJECT_STATE.md`, `COLLABORATION.md`, `reports/phase2/handoff_20260528.md`
- Confidence level: high
- Date last updated: 2026-05-28
