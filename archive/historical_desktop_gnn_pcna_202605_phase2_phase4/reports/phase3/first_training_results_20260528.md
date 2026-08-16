---
type: training-results
date: 2026-05-28
decision_id: phase3_first_training_run_20260528
status: completed
governance: docs/scientific_governance/09_EVALUATION_PROTOCOL.md
signoff: reports/phase3/first_training_signoff_20260528.md
---

# Phase 3 First Training Results

**Date:** 2026-05-28
**Status:** VALIDATION METRICS ONLY — test set not evaluated
**Governance:** docs/scientific_governance/09_EVALUATION_PROTOCOL.md

## Summary

| Metric | Value |
|--------|-------|
| Runs completed | 12 / 12 (4 folds × 3 seeds) |
| Primary metric | macro-AUPRC (val, per-protein average) |
| **Overall val macro-AUPRC** | **0.1876 ± 0.0113** |
| Range | [0.1719, 0.2042] |

**Interpretation note:** macro-AUPRC is the primary metric because positive label rate
is ~4.6%, making AUROC inflated under extreme class imbalance. These are validation
metrics only. No test-set evaluation has been performed. No scientific claims are made.

## Model Configuration

| Parameter | Value | Note |
|-----------|-------|------|
| Architecture | GraphSAGE-3L | SAGEConv(25→H)+ReLU+Dropout ×2, SAGEConv(H→H)+ReLU, Linear(H→1) |
| hidden_dim | 128 | Approved range: {64, 128} |
| dropout | 0.1 | Applied after layers 1 and 2 |
| lr | 0.001 | Adam optimizer |
| weight_decay | 1e-5 | Adam L2 penalty |
| batch_size | 4 (train) / 32 (val) | Val batch size is compute-only; batch isolation verified |
| max_epochs | 200 | With early stopping |
| patience | 10 | Early stopping on val macro-AUPRC |
| pos_weight | 20.9549 | n_bg_train / n_pos_train (training fold only) |

## Data Split (fold=0 reference)

| Partition | Structures | Note |
|-----------|-----------|------|
| Train | 667 | 3 of 4 folds, PCNA holdout excluded |
| Val | 220 | 1 fold, PCNA holdout excluded |
| Test | not loaded | Untouched until model + baselines frozen |

Split hash: 24dd5e347d880108 (frozen, validated by loader)

## Per-Run Results

| fold | seed | best_epoch | epochs_run | val_macro_auprc | elapsed_s |
|------|------|-----------|-----------|----------------|-----------|
| 0 | 0 |  28 |  38 | 0.1719 | 479 |
| 0 | 1 |  16 |  26 | 0.1747 | 192 |
| 0 | 2 |  19 |  29 | 0.1725 | 306 |
| 1 | 0 |  18 |  28 | 0.2030 | 267 |
| 1 | 1 |  18 |  28 | 0.2033 | 258 |
| 1 | 2 |  17 |  27 | 0.2042 | 242 |
| 2 | 0 |  19 |  29 | 0.1879 | 296 |
| 2 | 1 |  16 |  26 | 0.1859 | 193 |
| 2 | 2 |  16 |  26 | 0.1878 | 218 |
| 3 | 0 |  18 |  28 | 0.1876 | 272 |
| 3 | 1 |  20 |  30 | 0.1848 | 306 |
| 3 | 2 |  16 |  26 | 0.1873 | 272 |

## Per-Fold Summary

| fold | mean_val_macro_auprc |
|------|---------------------|
| 0 | 0.1730 |
| 1 | 0.2035 |
| 2 | 0.1872 |
| 3 | 0.1865 |
| **all** | **0.1876 ± 0.0113** |

## Governance Compliance

- [x] Dry-run guard cleared by human sign-off:
      `reports/phase3/first_training_signoff_20260528.md`
      (decision_id: phase3_first_training_signoff_20260528)
- [x] Split manifest hash validated at load time (24dd5e347d880108)
- [x] PCNA holdout (cluster 1168) excluded from all train and val splits
- [x] pos_weight computed from training fold only
- [x] loss_mask applied before BCEWithLogitsLoss (label=-1 nodes excluded)
- [x] No sigmoid on model outputs (BCEWithLogitsLoss handles it)
- [x] Batch isolation verified (test_batch_isolation.py: 4/4 passed)
- [x] No test-set evaluation performed
- [x] No baselines run yet (separate step)
- [x] No scientific claims made
- [x] Checkpoints saved to checkpoints/phase3/

## Next Steps (not authorized yet)

1. Human reviews these validation results.
2. Authorize and run baselines: random, fpocket, P2Rank, PocketMiner, GCN, GAT, no-edge-type.
3. Freeze model (best fold, best seed) and baselines.
4. Human authorizes test-set evaluation.
5. Run test evaluation once (no second runs).
6. Human PCNA gate before any PCNA inference.

## Provenance

- Signoff decision_id: `phase3_first_training_signoff_20260528`
- Graph release decision_id: `phase3_first_graph_release_20260528`
- Model/training decision_id: `phase3_model_training_plan_20260528`
- Split manifest hash: 24dd5e347d880108
- No test-set evaluation performed.
- No scientific claims made.
- Confidence: high (results match expected range for cold-start residue-level prediction)
- Evidence status: computational, internal validation only
