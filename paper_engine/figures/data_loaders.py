"""Load real Phase-3 experimental results from the repo's run manifests.

Every value returned here is read from a real file on disk. Nothing is
hardcoded or fabricated. If a required manifest is missing the loader raises
``FileNotFoundError`` rather than inventing numbers. The test set is frozen and
not evaluated, so only validation metrics are exposed.

Manifest layout (under ``reports/phase3/``):
  training_runs/all_runs_summary.json   -> primary GraphSAGE-3L, 12 runs + history
  baseline_runs/<model>_manifest.json   -> aggregate per baseline
  baseline_runs/<model>_fold*_seed*_manifest.json -> per-run baselines
"""
from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from paper_engine import config


# --------------------------------------------------------------------------- #
# Dataclasses
# --------------------------------------------------------------------------- #
@dataclass
class TrainingRun:
    fold: int
    seed: int
    best_val_macro_auprc: float
    best_epoch: int
    macro_auroc_at_best: Optional[float]
    n_train: int
    n_val: int
    pos_weight: float
    history: List[dict] = field(default_factory=list)


@dataclass
class PrimaryResults:
    runs: List[TrainingRun]
    mean: float
    sd: float
    per_fold_mean: Dict[int, float]
    best_run: TrainingRun
    pos_weight_mean: float
    macro_auroc_mean: Optional[float]
    source: str = ""


@dataclass
class ModelResult:
    key: str
    display: str
    mean: float
    sd: Optional[float]
    kind: str  # primary | gnn_baseline | naive | ablation | external
    available: bool = True
    per_fold: Optional[Dict[int, float]] = None
    macro_auroc: Optional[float] = None
    n_runs: Optional[int] = None
    source: str = ""


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _load_json(path: Path) -> dict | list:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _phase3_dir() -> Path:
    return config.phase3_reports_dir()


def _baseline_runs_dir() -> Path:
    return _phase3_dir() / "baseline_runs"


def _training_runs_dir() -> Path:
    return _phase3_dir() / "training_runs"


def _auroc_at_best(history: List[dict], best_epoch: int) -> Optional[float]:
    for entry in history:
        if entry.get("epoch") == best_epoch:
            return entry.get("val_macro_auroc")
    return None


# --------------------------------------------------------------------------- #
# Primary model
# --------------------------------------------------------------------------- #
def load_primary_training() -> PrimaryResults:
    """Load the GraphSAGE-3L primary model results from all 12 runs."""
    summary_path = _training_runs_dir() / "all_runs_summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"Primary training summary not found: {summary_path}")
    raw = _load_json(summary_path)
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"Unexpected all_runs_summary shape in {summary_path}")

    runs: List[TrainingRun] = []
    for r in raw:
        history = r.get("history", []) or []
        best_epoch = int(r.get("best_epoch", -1))
        runs.append(
            TrainingRun(
                fold=int(r["val_fold"]),
                seed=int(r["seed"]),
                best_val_macro_auprc=float(r["best_val_macro_auprc"]),
                best_epoch=best_epoch,
                macro_auroc_at_best=_auroc_at_best(history, best_epoch),
                n_train=int(r.get("n_train", 0)),
                n_val=int(r.get("n_val", 0)),
                pos_weight=float(r.get("pos_weight", 0.0)),
                history=history,
            )
        )

    values = [run.best_val_macro_auprc for run in runs]
    mean = statistics.mean(values)
    sd = statistics.stdev(values) if len(values) > 1 else 0.0

    per_fold: Dict[int, List[float]] = {}
    for run in runs:
        per_fold.setdefault(run.fold, []).append(run.best_val_macro_auprc)
    per_fold_mean = {fold: statistics.mean(v) for fold, v in sorted(per_fold.items())}

    best_run = max(runs, key=lambda run: run.best_val_macro_auprc)
    pos_weights = [run.pos_weight for run in runs if run.pos_weight]
    aurocs = [run.macro_auroc_at_best for run in runs if run.macro_auroc_at_best is not None]

    return PrimaryResults(
        runs=runs,
        mean=mean,
        sd=sd,
        per_fold_mean=per_fold_mean,
        best_run=best_run,
        pos_weight_mean=statistics.mean(pos_weights) if pos_weights else 0.0,
        macro_auroc_mean=statistics.mean(aurocs) if aurocs else None,
        source=str(summary_path),
    )


# --------------------------------------------------------------------------- #
# Baselines
# --------------------------------------------------------------------------- #
def _gnn_baseline_auroc(model_key: str) -> Optional[float]:
    """Average final_metrics.macro_auroc over a GNN baseline's per-run manifests."""
    runs_dir = _baseline_runs_dir()
    aurocs: List[float] = []
    for path in sorted(runs_dir.glob(f"{model_key}_fold*_seed*_manifest.json")):
        data = _load_json(path)
        fm = data.get("final_metrics", {}) if isinstance(data, dict) else {}
        if "macro_auroc" in fm:
            aurocs.append(float(fm["macro_auroc"]))
    return statistics.mean(aurocs) if aurocs else None


def load_gnn_baseline(model_key: str, display: str, kind: str = "gnn_baseline") -> ModelResult:
    """Load an aggregate GNN-baseline manifest (gcn_1l, gat_2l, sage ablations)."""
    agg_path = _baseline_runs_dir() / f"{model_key}_manifest.json"
    data = _load_json(agg_path)
    per_fold_raw = data.get("per_fold_mean_macro_auprc", {}) or {}
    per_fold = {int(k): float(v) for k, v in per_fold_raw.items()}
    return ModelResult(
        key=model_key,
        display=display,
        mean=float(data["overall_macro_auprc_mean"]),
        sd=float(data.get("overall_macro_auprc_sd")) if data.get("overall_macro_auprc_sd") is not None else None,
        kind=kind,
        per_fold=per_fold or None,
        macro_auroc=_gnn_baseline_auroc(model_key),
        n_runs=len(data.get("per_fold_per_seed", []) or []) or None,
        source=str(agg_path),
    )


def load_random_baseline() -> ModelResult:
    path = _baseline_runs_dir() / "random_manifest.json"
    agg = _load_json(path).get("aggregate", {})
    return ModelResult(
        key="random",
        display="Random",
        mean=float(agg["macro_auprc_mean"]),
        sd=float(agg.get("macro_auprc_sd")) if agg.get("macro_auprc_sd") is not None else None,
        kind="naive",
        macro_auroc=float(agg["macro_auroc_mean"]) if "macro_auroc_mean" in agg else None,
        source=str(path),
    )


def load_degree_baseline() -> ModelResult:
    path = _baseline_runs_dir() / "degree_manifest.json"
    metrics = _load_json(path).get("metrics", {})
    return ModelResult(
        key="degree",
        display="Degree / exposure",
        mean=float(metrics["macro_auprc"]),
        sd=None,  # deterministic, single value
        kind="naive",
        macro_auroc=float(metrics["macro_auroc"]) if "macro_auroc" in metrics else None,
        source=str(path),
    )


def _external_stub(model_key: str, display: str) -> ModelResult:
    """External baselines not run on this machine (fpocket/P2Rank/PocketMiner)."""
    return ModelResult(
        key=model_key,
        display=display,
        mean=float("nan"),
        sd=None,
        kind="external",
        available=False,
        source=str(_baseline_runs_dir() / f"{model_key}_manifest.json"),
    )


def load_all_models(include_unavailable: bool = False) -> List[ModelResult]:
    """Assemble every model as a comparable ModelResult, primary first.

    The order is chosen for the comparison figure: primary on top, GNN baselines,
    then naive references at the bottom.
    """
    primary = load_primary_training()
    primary_model = ModelResult(
        key="graphsage_3l",
        display="GraphSAGE-3L (primary)",
        mean=primary.mean,
        sd=primary.sd,
        kind="primary",
        per_fold=primary.per_fold_mean,
        macro_auroc=primary.macro_auroc_mean,
        n_runs=len(primary.runs),
        source=primary.source,
    )
    models = [
        primary_model,
        load_gnn_baseline("sage_no_sequential", "SAGE-3L (no sequential edges)", kind="ablation"),
        load_gnn_baseline("gat_2l", "GAT-2L"),
        load_gnn_baseline("gcn_1l", "GCN-1L"),
        load_gnn_baseline("sage_no_spatial", "SAGE-3L (no spatial edges)", kind="ablation"),
        load_degree_baseline(),
        load_random_baseline(),
    ]
    if include_unavailable:
        models += [
            _external_stub("fpocket", "fpocket (external)"),
            _external_stub("p2rank", "P2Rank (external)"),
            _external_stub("pocketminer", "PocketMiner (external)"),
        ]
    return models


# --------------------------------------------------------------------------- #
# Dataset / label / split statistics
# --------------------------------------------------------------------------- #
def load_model_config() -> dict:
    """Hyperparameters of the primary model, read from the first run manifest."""
    summary_path = _training_runs_dir() / "all_runs_summary.json"
    raw = _load_json(summary_path)
    if isinstance(raw, list) and raw:
        r0 = raw[0]
        keys = ["hidden_dim", "dropout", "lr", "weight_decay", "batch_size",
                "max_epochs", "patience", "pos_weight", "n_train", "n_val"]
        cfg = {k: r0.get(k) for k in keys}
        cfg["architecture"] = "GraphSAGE-3L"
        cfg["source"] = str(summary_path)
        return cfg
    return {}


def load_label_stats() -> dict:
    path = config.require_data_file(*config.LABEL_MANIFEST)
    d = _load_json(path)
    positives = int(d["total_positives"])
    masked = int(d["total_masked"])
    structures = int(d["structures_labeled"])
    # Positive prevalence among evaluated (unmasked) residues is best recovered
    # from the training pos_weight (n_bg/n_pos); fall back to None if unavailable.
    prevalence = None
    try:
        primary = load_primary_training()
        if primary.pos_weight_mean:
            prevalence = 1.0 / (1.0 + primary.pos_weight_mean)
    except Exception:
        prevalence = None
    return {
        "structures_labeled": structures,
        "structures_excluded": int(d.get("structures_excluded", 0)),
        "total_positives": positives,
        "total_masked": masked,
        "label_policy": d.get("label_policy", ""),
        "positive_prevalence": prevalence,  # ~0.046, derived from pos_weight
        "status": d.get("status", ""),
        "source": str(path),
    }


def load_split_stats() -> dict:
    path = config.require_data_file(*config.SPLIT_MANIFEST)
    d = _load_json(path)
    fold_dist_raw = d.get("fold_distribution", {}) or {}
    fold_distribution = {str(k): int(v) for k, v in fold_dist_raw.items()}
    return {
        "total_structures": int(d.get("total_structures", 0)),
        "excluded_structures": int(d.get("excluded_structures", 0)),
        "fold_distribution": fold_distribution,
        "pcna_holdout_count": int(d.get("pcna_holdout_count", 0)),
        "identity_threshold": d.get("identity_threshold"),
        "manifest_hash": str(d.get("manifest_hash_sha256", ""))[:16],
        "status": d.get("status", ""),
        "source": str(path),
    }


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    p = load_primary_training()
    print(f"Primary GraphSAGE-3L: {p.mean:.4f} +/- {p.sd:.4f} (n={len(p.runs)})")
    print(f"  per-fold: {p.per_fold_mean}")
    print(f"  best run: fold{p.best_run.fold} seed{p.best_run.seed} = {p.best_run.best_val_macro_auprc:.4f}")
    print(f"  macro-AUROC (mean@best): {p.macro_auroc_mean}")
    print("Models:")
    for m in load_all_models(include_unavailable=True):
        sd = f"+/-{m.sd:.4f}" if m.sd is not None else "       "
        avail = "" if m.available else "  [not run]"
        print(f"  {m.display:32s} {m.mean if m.available else float('nan'):.4f} {sd}  auroc={m.macro_auroc}{avail}")
    print("Labels:", load_label_stats())
    print("Split:", load_split_stats())
