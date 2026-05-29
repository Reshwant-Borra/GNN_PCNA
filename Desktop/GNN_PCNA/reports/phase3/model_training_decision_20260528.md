---
type: human-decision-record
date: 2026-05-28
decision_id: phase3_model_training_plan_20260528
gate: first_training_run
governance: docs/scientific_governance/26_HUMAN_REVIEW_GATES.md
status: approved
reviewer_role: human_project_owner
---

# Phase 3 Model / Training Plan — Human Decision Record

## Decision

**Decision: `approved`**

The human project owner approves the Phase 3 model/training plan as written in
`reports/phase3/model_training_approval_packet_20260528.md`.

This approval authorizes:
- Implementation of the proposed GraphSAGE-3L architecture and training loop.
- Implementation of the data loader, evaluation module, and baseline runners.
- Adding the batch-isolation unit test to `tests/phase3/`.

This approval does **not** authorize:
- Real training (requires GATE 2: separate first-training sign-off after
  batch-isolation test passes and architecture implementation is reviewed).
- Test-set evaluation before model and baselines are frozen.
- PCNA prediction interpretation.
- MD runs or scientific claims.

## Evidence Packet Reviewed

- `reports/phase3/model_training_approval_packet_20260528.md`
- `reports/phase3/first_graph_release_approval_20260528.md` (GATE 1 already cleared)
- `data/graphs/graph_release_manifest_8c22e46f524d5f1d.json`
- `docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md`
- `docs/scientific_governance/09_EVALUATION_PROTOCOL.md`
- `docs/scientific_governance/10_BASELINE_REQUIREMENTS.md`
- `docs/scientific_governance/19_STOP_CONDITIONS.md`
- `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`

## Approved Plan Elements

**Architecture:** GraphSAGE mean aggregation, 3 message-passing layers,
25-dim input → hidden dim H ∈ {64, 128} → scalar logit per residue.
No virtual node in MVP. No final sigmoid during BCEWithLogitsLoss training.

**Loss:** BCEWithLogitsLoss with `pos_weight` computed from training-fold nodes
only (background count / positive count). No val/test label leakage into class
weights.

**Cross-validation:** 4-fold CV on frozen split (`24dd5e347d880108`).
Minimum 3 random seeds; 5 preferred. Early stopping on validation macro-AUPRC.
Hyperparameters tuned on validation only; test evaluated once after freeze.

**Primary metric (pre-specified):** Macro-AUPRC. Secondary: micro-AUPRC,
macro/micro-AUROC, top-k recovery (k=5, 10, 20), bootstrap 95% CI,
calibration, per-protein table, seed mean ± SD.

**Baselines required before claims:** random, solvent-exposure, fpocket,
P2Rank, PocketMiner (run on our split), basic GCN (1-layer), GAT (2-layer),
no-edge-type ablation.

**Shortcut safeguards:** chain-ID and residue-number excluded from features
(hash-locked). Required post-training ablations: no-sequential-edges,
no-spatial-edges, residue-identity shuffled, graph-size correlation,
per-protein metric inspection.

**Stopping conditions apply:** leakage, graph-label mismatch, shortcut
detection, batch-isolation failure, null-baseline win, broken provenance —
all halt affected work per `docs/scientific_governance/19_STOP_CONDITIONS.md`.

## Limitations Acknowledged

- Batch-isolation unit test must pass before real training begins (GATE 2).
- Architecture ablations (GAT, no-virtual-node, etc.) run after first training.
- No ESM features in MVP; ESM requires separate approval with version/hash policy.
- Positive-label rate is ~4.6%; macro-AUPRC is chosen as primary precisely
  because AUROC is inflated under extreme class imbalance — this must be
  stated in any report.
- All results are internal computational performance only until claim audit.

## Provenance

- decision_id: `phase3_model_training_plan_20260528`
- packet_path: `reports/phase3/model_training_approval_packet_20260528.md`
- graph_release_decision: `phase3_first_graph_release_20260528`
- governance: `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`
- confidence: high
- evidence_status: verified for referenced artifacts
