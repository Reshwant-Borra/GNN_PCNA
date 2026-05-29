---
type: spatial-only-retrain-authorization
date: 2026-05-29
authorized_by: Reshwant
decision_id: phase3_spatial_only_retrain_20260529
parent_gate: GATE_4_OPTION_B
status: AUTHORIZED
---

# Option B Retraining Authorization — Spatial-Only GraphSAGE-3L

## Decision

Reshwant has selected **Option B** from the GATE 4 draft
(`reports/phase3/model_freeze_gate4_DRAFT_20260529.md`).

The current GATE 4 draft is **REJECTED** pending this retraining.

## Rationale (as stated by Reshwant, 2026-05-29)

> The sequential-edge ablation indicates that the spatial-only GraphSAGE model
> performs slightly better on validation while using a simpler architecture.
> Before freezing a checkpoint for one-shot test evaluation, I want the cleaner
> architecture evaluated and frozen.

## What Is Authorized

- Retrain GraphSAGE-3L (spatial-only, edge_type_filter=0) on the **same
  frozen dataset, splits, labels, and hyperparameters** as the primary model.
- Architecture: SAGEConv-3L, hidden_dim=128, dropout=0.1 — no changes.
- Hyperparameters: lr=1e-3, weight_decay=1e-5, max_epochs=200, patience=10,
  batch_size=4 — same as primary training.
- Seeds: 0, 1, 2. Folds: 0, 1, 2, 3. 12 total runs.
- CUDA allowed (RTX 4070); device must be logged in run manifests.
- Edge type: **spatial edges only** (edge_type == 0).
  Sequential edges (edge_type == 1) are excluded before DataLoader construction.
- Checkpoints: `checkpoints/phase3/spatial_only_fold{f}_seed{s}_best.pt`
- Manifests: `reports/phase3/spatial_only_training_runs/`

## What Is NOT Authorized

- Test-set evaluation (GATE 5 remains blocked until GATE 4 is re-approved).
- Changing split manifest, labels, or graph structure.
- Changing hidden_dim, dropout, optimizer, or loss function.
- Changing max_epochs or patience.
- PCNA inference (GATE 6 remains blocked).
- Making scientific claims.

## Parent Gates

- GATE 2 (first training signoff): `reports/phase3/first_training_signoff_20260528.md`
  — authorizes GraphSAGE-3L training; this retrain falls within that authorization.
- GATE 3 (baselines): `reports/phase3/baseline_gate3_authorization_20260529.md`
  — authorizes `sage_no_sequential` ablation; this retrain elevates that ablation
  to freeze-candidate quality using the primary training pipeline.

## Next Steps After Retraining

1. Agent compares spatial-only vs full model on validation.
2. Agent regenerates the GATE 4 draft.
3. Reshwant reviews and approves GATE 4 (model freeze).
4. Separate GATE 5 authorization required before test evaluation.
