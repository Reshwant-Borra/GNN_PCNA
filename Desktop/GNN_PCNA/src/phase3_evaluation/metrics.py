"""Pre-specified evaluation metrics for Phase 3.

Primary metric: macro-AUPRC.
Secondary metrics (all pre-specified before training):
  micro-AUPRC, macro-AUROC, micro-AUROC,
  top-k residue recovery (k=5, 10, 20), precision@k,
  bootstrap 95% CI (N=1000), per-protein table, seed mean ± SD.

No metric may be added or changed after test-set evaluation begins.

Governance: docs/scientific_governance/09_EVALUATION_PROTOCOL.md
Approval:   reports/phase3/model_training_decision_20260528.md
            (decision_id: phase3_model_training_plan_20260528)
"""

from __future__ import annotations

import math
import warnings
from typing import Any

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

_TOP_K_VALUES: tuple[int, ...] = (5, 10, 20)
_BOOTSTRAP_N: int = 1000
_BOOTSTRAP_SEED: int = 42
_CI_ALPHA: float = 0.95


# ---------------------------------------------------------------------------
# Per-protein helpers
# ---------------------------------------------------------------------------

def _protein_auprc(scores: list[float], labels: list[int]) -> float | None:
    """AUPRC for one protein. Returns None if only one class present."""
    y = np.asarray(labels, dtype=np.int32)
    if y.sum() == 0 or (y == 0).all():
        return None
    s = np.asarray(scores, dtype=np.float64)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return float(average_precision_score(y, s))


def _protein_auroc(scores: list[float], labels: list[int]) -> float | None:
    """AUROC for one protein. Returns None if only one class present."""
    y = np.asarray(labels, dtype=np.int32)
    if y.sum() == 0 or (y == 0).all():
        return None
    s = np.asarray(scores, dtype=np.float64)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return float(roc_auc_score(y, s))


def _top_k_stats(scores: list[float], labels: list[int], k: int) -> dict[str, float]:
    """Recovery and precision at k for one protein.

    top_k_recovery@k = (# positives in top-k) / (# total positives)
    precision@k      = (# positives in top-k) / k
    """
    y = np.asarray(labels, dtype=np.int32)
    s = np.asarray(scores, dtype=np.float64)
    n_pos = int(y.sum())
    actual_k = min(k, len(s))
    top_k_idx = np.argsort(s)[::-1][:actual_k]
    hits = int(y[top_k_idx].sum())
    recovery = hits / n_pos if n_pos > 0 else float("nan")
    precision = hits / actual_k if actual_k > 0 else float("nan")
    return {"recovery": recovery, "precision": precision, "n_pos": n_pos, "k_used": actual_k}


# ---------------------------------------------------------------------------
# Aggregate metric computation
# ---------------------------------------------------------------------------

ProteinScores = list[tuple[list[float], list[int]]]


def compute_metrics_from_lists(
    protein_scores: ProteinScores,
) -> dict[str, Any]:
    """Compute all pre-specified metrics from per-protein (scores, labels) pairs.

    Args:
        protein_scores: List of (scores, labels) tuples. Scores are raw logits
            or calibrated probabilities; labels are 0/1 integers (loss_mask=True
            nodes only — no -1 labels should be passed here).

    Returns:
        Dictionary containing macro/micro variants and per-protein table.
        macro-AUPRC is the primary metric (key: "macro_auprc").
    """
    per_protein: list[dict[str, Any]] = []
    all_scores: list[float] = []
    all_labels: list[int] = []

    for i, (scores, labels) in enumerate(protein_scores):
        row: dict[str, Any] = {"protein_idx": i, "n_nodes": len(labels)}
        row["auprc"] = _protein_auprc(scores, labels)
        row["auroc"] = _protein_auroc(scores, labels)
        for k in _TOP_K_VALUES:
            stats = _top_k_stats(scores, labels, k)
            row[f"top_{k}_recovery"] = stats["recovery"]
            row[f"precision_at_{k}"] = stats["precision"]
        per_protein.append(row)
        all_scores.extend(scores)
        all_labels.extend(labels)

    # Macro: mean over proteins, ignoring None (undefined per-protein metrics)
    valid_auprcs = [r["auprc"] for r in per_protein if r["auprc"] is not None]
    valid_aurocs = [r["auroc"] for r in per_protein if r["auroc"] is not None]

    macro_auprc = float(np.mean(valid_auprcs)) if valid_auprcs else float("nan")
    macro_auroc = float(np.mean(valid_aurocs)) if valid_aurocs else float("nan")

    for k in _TOP_K_VALUES:
        key = f"top_{k}_recovery"
        pkey = f"precision_at_{k}"

    # Micro: pool all nodes
    y_all = np.asarray(all_labels, dtype=np.int32)
    s_all = np.asarray(all_scores, dtype=np.float64)
    micro_auprc: float
    micro_auroc: float
    if y_all.sum() > 0 and (y_all == 0).any():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            micro_auprc = float(average_precision_score(y_all, s_all))
            micro_auroc = float(roc_auc_score(y_all, s_all))
    else:
        micro_auprc = float("nan")
        micro_auroc = float("nan")

    # Macro top-k (mean over proteins)
    macro_top_k: dict[str, float] = {}
    for k in _TOP_K_VALUES:
        recoveries = [
            r[f"top_{k}_recovery"] for r in per_protein
            if not math.isnan(r[f"top_{k}_recovery"])
        ]
        precisions = [
            r[f"precision_at_{k}"] for r in per_protein
            if not math.isnan(r[f"precision_at_{k}"])
        ]
        macro_top_k[f"macro_top_{k}_recovery"] = float(np.mean(recoveries)) if recoveries else float("nan")
        macro_top_k[f"macro_precision_at_{k}"] = float(np.mean(precisions)) if precisions else float("nan")

    result: dict[str, Any] = {
        "macro_auprc": macro_auprc,       # PRIMARY METRIC
        "micro_auprc": micro_auprc,
        "macro_auroc": macro_auroc,
        "micro_auroc": micro_auroc,
        "n_proteins": len(per_protein),
        "n_proteins_with_valid_auprc": len(valid_auprcs),
        **macro_top_k,
        "per_protein": per_protein,
    }
    return result


# ---------------------------------------------------------------------------
# Bootstrap confidence intervals
# ---------------------------------------------------------------------------

def bootstrap_ci(
    protein_scores: ProteinScores,
    n_bootstrap: int = _BOOTSTRAP_N,
    seed: int = _BOOTSTRAP_SEED,
    alpha: float = _CI_ALPHA,
) -> dict[str, tuple[float, float]]:
    """Bootstrap 95% CI over proteins for macro-AUPRC and macro-AUROC.

    Resamples proteins (not residues) with replacement N times.
    Returns dict mapping metric_name -> (lower, upper).

    Governance: docs/scientific_governance/09_EVALUATION_PROTOCOL.md
      "Bootstrap confidence intervals over proteins."
    """
    rng = np.random.default_rng(seed)
    n = len(protein_scores)

    boot_auprc: list[float] = []
    boot_auroc: list[float] = []

    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        sample = [protein_scores[i] for i in idx]
        m = compute_metrics_from_lists(sample)
        if not math.isnan(m["macro_auprc"]):
            boot_auprc.append(m["macro_auprc"])
        if not math.isnan(m["macro_auroc"]):
            boot_auroc.append(m["macro_auroc"])

    lo = (1.0 - alpha) / 2.0
    hi = 1.0 - lo

    def _ci(vals: list[float]) -> tuple[float, float]:
        if not vals:
            return (float("nan"), float("nan"))
        arr = np.asarray(vals)
        return (float(np.quantile(arr, lo)), float(np.quantile(arr, hi)))

    return {
        "macro_auprc_ci": _ci(boot_auprc),
        "macro_auroc_ci": _ci(boot_auroc),
        "n_bootstrap": n_bootstrap,
        "alpha": alpha,
    }


# ---------------------------------------------------------------------------
# Multi-seed aggregation
# ---------------------------------------------------------------------------

def aggregate_seeds(seed_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute mean ± SD over multiple training seed results.

    Args:
        seed_results: List of metric dicts from compute_metrics_from_lists,
            one per seed run.

    Returns:
        Dict with {metric}_mean and {metric}_sd for scalar metrics.

    Governance: docs/scientific_governance/09_EVALUATION_PROTOCOL.md
      "Minimum 3 seeds; 5 preferred. Show seed variance."
    """
    if len(seed_results) < 1:
        raise ValueError("At least one seed result required.")

    scalar_keys = [k for k, v in seed_results[0].items() if isinstance(v, (int, float))]
    out: dict[str, Any] = {"n_seeds": len(seed_results)}
    for k in scalar_keys:
        vals = [r[k] for r in seed_results if not math.isnan(r.get(k, float("nan")))]
        out[f"{k}_mean"] = float(np.mean(vals)) if vals else float("nan")
        out[f"{k}_sd"] = float(np.std(vals, ddof=1)) if len(vals) > 1 else float("nan")
    return out
