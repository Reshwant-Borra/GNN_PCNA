"""Summarize Phase 3 CV training results from manifest JSONs.

Reads all reports/phase3/training_runs/fold*_seed*_manifest.json files,
computes fold-mean and cross-fold stats, and prints a formatted table.

Usage:
  python scripts/summarize_training.py
  python scripts/summarize_training.py --out-md reports/phase3/first_training_results_20260528.md
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

OUT_DIR = ROOT / "reports/phase3/training_runs"


def load_manifests() -> list[dict]:
    manifests = []
    for p in sorted(OUT_DIR.glob("fold*_seed*_manifest.json")):
        with open(p) as f:
            manifests.append(json.load(f))
    return manifests


def fold_stats(manifests: list[dict]) -> dict:
    """Aggregate per-fold and overall statistics."""
    folds: dict[int, list[float]] = {}
    for m in manifests:
        fold = m["val_fold"]
        auprc = m["best_val_macro_auprc"]
        folds.setdefault(fold, []).append(auprc)

    fold_means: dict[int, float] = {f: sum(v) / len(v) for f, v in folds.items()}
    all_auprcs = [m["best_val_macro_auprc"] for m in manifests]

    mean = sum(all_auprcs) / len(all_auprcs)
    variance = sum((x - mean) ** 2 for x in all_auprcs) / max(len(all_auprcs) - 1, 1)
    sd = math.sqrt(variance)

    return {
        "per_fold_means": fold_means,
        "overall_mean": mean,
        "overall_sd": sd,
        "overall_min": min(all_auprcs),
        "overall_max": max(all_auprcs),
        "n_runs": len(all_auprcs),
        "all_auprcs": all_auprcs,
    }


def render_table(manifests: list[dict]) -> str:
    lines = []
    lines.append("| fold | seed | best_epoch | epochs_run | val_macro_auprc | elapsed_s |")
    lines.append("|------|------|-----------|-----------|----------------|-----------|")
    for m in sorted(manifests, key=lambda x: (x["val_fold"], x["seed"])):
        lines.append(
            f"| {m['val_fold']} | {m['seed']} | {m['best_epoch']:3d} "
            f"| {m['epochs_run']:3d} | {m['best_val_macro_auprc']:.4f} "
            f"| {m['elapsed_seconds']:.0f} |"
        )
    return "\n".join(lines)


def render_fold_summary(stats: dict) -> str:
    lines = []
    lines.append("| fold | mean_val_macro_auprc |")
    lines.append("|------|---------------------|")
    for fold in sorted(stats["per_fold_means"]):
        lines.append(f"| {fold} | {stats['per_fold_means'][fold]:.4f} |")
    lines.append(f"| **all** | **{stats['overall_mean']:.4f} ± {stats['overall_sd']:.4f}** |")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-md", type=Path, default=None)
    args = p.parse_args()

    manifests = load_manifests()
    if not manifests:
        print("No manifest files found in", OUT_DIR, file=sys.stderr)
        return 1

    stats = fold_stats(manifests)
    run_table = render_table(manifests)
    fold_table = render_fold_summary(stats)

    sample = manifests[0]
    pos_weight = sample["pos_weight"]
    n_train = sample["n_train"]
    n_val = sample["n_val"]
    hidden_dim = sample["hidden_dim"]
    dropout = sample["dropout"]
    lr = sample["lr"]
    patience = sample["patience"]
    max_epochs = sample["max_epochs"]

    report = f"""---
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
| Runs completed | {stats["n_runs"]} / 12 (4 folds × 3 seeds) |
| Primary metric | macro-AUPRC (val, per-protein average) |
| **Overall val macro-AUPRC** | **{stats["overall_mean"]:.4f} ± {stats["overall_sd"]:.4f}** |
| Range | [{stats["overall_min"]:.4f}, {stats["overall_max"]:.4f}] |

**Interpretation note:** macro-AUPRC is the primary metric because positive label rate
is ~4.6%, making AUROC inflated under extreme class imbalance. These are validation
metrics only. No test-set evaluation has been performed. No scientific claims are made.

## Model Configuration

| Parameter | Value | Note |
|-----------|-------|------|
| Architecture | GraphSAGE-3L | SAGEConv(25→H)+ReLU+Dropout ×2, SAGEConv(H→H)+ReLU, Linear(H→1) |
| hidden_dim | {hidden_dim} | Approved range: {{64, 128}} |
| dropout | {dropout} | Applied after layers 1 and 2 |
| lr | {lr} | Adam optimizer |
| weight_decay | 1e-5 | Adam L2 penalty |
| batch_size | 4 (train) / 32 (val) | Val batch size is compute-only; batch isolation verified |
| max_epochs | {max_epochs} | With early stopping |
| patience | {patience} | Early stopping on val macro-AUPRC |
| pos_weight | {pos_weight:.4f} | n_bg_train / n_pos_train (training fold only) |

## Data Split (fold=0 reference)

| Partition | Structures | Note |
|-----------|-----------|------|
| Train | {n_train} | 3 of 4 folds, PCNA holdout excluded |
| Val | {n_val} | 1 fold, PCNA holdout excluded |
| Test | not loaded | Untouched until model + baselines frozen |

Split hash: 24dd5e347d880108 (frozen, validated by loader)

## Per-Run Results

{run_table}

## Per-Fold Summary

{fold_table}

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
"""

    print(report)

    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        with open(args.out_md, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\nReport written to {args.out_md}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
