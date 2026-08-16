---
type: human-decision-record
date: 2026-05-28
decision_id: phase3_first_training_signoff_20260528
gate: first_training_run
governance: docs/scientific_governance/26_HUMAN_REVIEW_GATES.md
status: approved
reviewer_role: human_project_owner
---

# Phase 3 First-Training Sign-Off — GATE 2

## Decision

**Decision: `approved`**

The human project owner approves the first real training run of the Phase 3
GraphSAGE-3L model on the governed CryptoBench split.

## Evidence Reviewed

All of the following conditions are verified before this sign-off:

| Condition | Status |
|---|---|
| GATE 1 — first graph release approved | CLEARED — `reports/phase3/first_graph_release_approval_20260528.md` |
| Model/training plan approved | CLEARED — `reports/phase3/model_training_decision_20260528.md` |
| GraphSAGE-3L implementation complete | VERIFIED — `src/phase3_model/gnn.py`, no sigmoid, hidden_dim in {64,128} |
| Graph loader enforces frozen split hash | VERIFIED — `src/phase3_data/graph_loader.py`, hash prefix 24dd5e347d880108 |
| PCNA holdout (cluster 1168) excluded from train/val | VERIFIED — enforced in `_get_pdb_ids_for_split()` |
| pos_weight computed from training fold only | VERIFIED — `compute_pos_weight()` uses only loss_mask=True train nodes |
| Batch-isolation test passed | VERIFIED — 4/4 tests pass at atol=1e-5, both orderings |
| Full test suite passing | VERIFIED — 93/93 tests pass |
| No sigmoid on model output | VERIFIED — `gnn.py` returns raw logits; BCEWithLogitsLoss handles sigmoid |
| Early stopping on val macro-AUPRC | VERIFIED — patience=10 in `trainer.py` |
| Loss mask applied before criterion | VERIFIED — `logits[mask]` and `batch.y[mask].float()` before BCEWithLogitsLoss |
| Test set untouched | CONFIRMED — no test-split loading in training script |

## What This Approval Authorizes

- Removal of the unconditional `raise TrainingGateError` at the bottom of
  `src/phase3_training/gates.py`, conditioned on this file existing as a valid record.
- 4-fold cross-validation training on the frozen CryptoBench split (hash: 24dd5e347d880108).
- Minimum 3 random seeds per fold (seeds 0, 1, 2).
- Checkpoints saved to `checkpoints/phase3/`.
- Validation metrics (macro-AUPRC) logged per epoch and per fold-seed.

## What This Approval Does NOT Authorize

- Test-set evaluation (requires separate gate after model and baselines are frozen).
- PCNA inference interpretation.
- Scientific claims or benchmark comparisons.
- Baseline runs (separate step).
- Any modification to split, labels, or graph tensors.

## Provenance

- decision_id: `phase3_first_training_signoff_20260528`
- gate: GATE 2
- parent_decisions:
  - `phase3_first_graph_release_20260528`
  - `phase3_model_training_plan_20260528`
- governance: `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`
- confidence: high
- evidence_status: verified for all referenced artifacts
