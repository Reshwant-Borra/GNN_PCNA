"""Evaluate clean-split checkpoints with validation-selected thresholds."""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import numpy as np
import torch
from sklearn.metrics import (
    average_precision_score,
    matthews_corrcoef,
    precision_recall_curve,
    roc_auc_score,
)

from src.models import PocketGNN, PocketGNNXL

CONDITIONS = {
    "small_geometry": {"model_size": "small", "graph_dir": "data/graphs", "node_dim": 40, "zero_esm": False},
    "xl_geometry": {"model_size": "xl", "graph_dir": "data/graphs", "node_dim": 40, "zero_esm": False},
    "xl_esm_zero": {"model_size": "xl", "graph_dir": "data/graphs_xl", "node_dim": 520, "zero_esm": True},
    "xl_esm_full": {"model_size": "xl", "graph_dir": "data/graphs_xl", "node_dim": 520, "zero_esm": False},
}


def display_path(path: Path) -> str:
    """Return a readable repo-relative path when possible."""
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPO))
    except ValueError:
        return str(path)


def finite(value: float | None) -> float | None:
    """Return JSON-safe finite floats."""
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return float(value)


def load_model(model_size: str, node_dim: int, ckpt: Path):
    """Instantiate and load a checkpoint, checking node feature dimension."""
    if not ckpt.exists():
        raise FileNotFoundError(f"Missing checkpoint: {ckpt}")
    model = PocketGNN.small() if model_size == "small" else PocketGNNXL(node_in_dim=node_dim)
    state = torch.load(str(ckpt), map_location="cpu", weights_only=True)
    ckpt_node_dim = state["node_encoder.0.weight"].shape[1]
    if int(ckpt_node_dim) != int(node_dim):
        raise ValueError(
            f"{ckpt} expects node_dim={ckpt_node_dim}, but evaluation graph mode is {node_dim}"
        )
    model.load_state_dict(state)
    model.eval()
    return model


def maybe_zero_esm(x: torch.Tensor, zero_esm: bool) -> torch.Tensor:
    """Zero ESM2 columns for xl_esm_zero evaluation."""
    if not zero_esm or x.shape[1] <= 40:
        return x
    x = x.clone()
    x[:, 40:] = 0.0
    return x


@torch.no_grad()
def predict(model, data, zero_esm: bool) -> np.ndarray:
    """Run per-residue inference for one graph."""
    x = maybe_zero_esm(data.x, zero_esm)
    scores = model(
        x, data.edge_index, data.edge_attr,
        data.edge_index_seq, data.edge_attr_seq,
        getattr(data, "chain_id", None),
    )
    return scores.cpu().numpy()


def select_mcc_threshold(y_true: np.ndarray, scores: np.ndarray) -> tuple[float, float]:
    """Select one MCC threshold from validation residues only."""
    if len(np.unique(y_true)) < 2:
        return 0.5, float("nan")
    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    candidates = np.unique(np.concatenate([thresholds, np.array([0.5])]))
    best_thr, best_mcc = 0.5, -2.0
    for thr in candidates:
        pred = (scores >= thr).astype(int)
        mcc = matthews_corrcoef(y_true, pred)
        if mcc > best_mcc:
            best_thr, best_mcc = float(thr), float(mcc)
    return best_thr, best_mcc


def metric_dict(y_true: np.ndarray, scores: np.ndarray, threshold: float) -> dict:
    """Compute residue-level metrics for one structure."""
    n = int(len(y_true))
    n_pos = int(y_true.sum())
    pos_frac = float(n_pos / n) if n else 0.0
    out = {
        "n_residues": n,
        "n_positive": n_pos,
        "positive_fraction": pos_frac,
        "degenerate_labels": n_pos < 5,
    }
    if n == 0 or len(np.unique(y_true)) < 2:
        out.update({
            "auroc": None, "auprc": None, "mcc": None,
            "precision_at_k": None, "recall_at_k": None,
            "enrichment_factor": None,
        })
        return out

    pred = (scores >= threshold).astype(int)
    k = max(n_pos, 1)
    top = np.argsort(scores)[-k:]
    hits = int(y_true[top].sum())
    precision_at_k = hits / k
    recall_at_k = hits / n_pos if n_pos else 0.0
    enrichment = precision_at_k / pos_frac if pos_frac > 0 else None

    out.update({
        "auroc": finite(roc_auc_score(y_true, scores)),
        "auprc": finite(average_precision_score(y_true, scores)),
        "auprc_baseline": pos_frac,
        "mcc": finite(matthews_corrcoef(y_true, pred)),
        "threshold": threshold,
        "precision_at_k": finite(precision_at_k),
        "recall_at_k": finite(recall_at_k),
        "enrichment_factor": finite(enrichment),
    })
    return out


def aggregate(rows: list[dict]) -> dict:
    """Aggregate per-structure metrics as means over structures."""
    metrics = [
        "auroc", "auprc", "mcc", "precision_at_k", "recall_at_k",
        "enrichment_factor", "positive_fraction",
    ]
    out = {"n_structures": len(rows)}
    for metric in metrics:
        vals = [r[metric] for r in rows if r.get(metric) is not None]
        out[f"mean_{metric}"] = finite(float(np.mean(vals))) if vals else None
    return out


def bootstrap_ci(rows: list[dict], n_boot: int, seed: int) -> dict:
    """Bootstrap confidence intervals by resampling structures."""
    if not rows:
        return {}
    rng = np.random.default_rng(seed)
    metrics = ["auroc", "auprc", "mcc", "precision_at_k", "recall_at_k", "enrichment_factor"]
    cis: dict[str, dict] = {}
    for metric in metrics:
        vals = np.array([r[metric] for r in rows if r.get(metric) is not None], dtype=float)
        if len(vals) == 0:
            cis[metric] = {"low": None, "high": None}
            continue
        boot = []
        for _ in range(n_boot):
            sample = rng.choice(vals, size=len(vals), replace=True)
            boot.append(float(np.mean(sample)))
        low, high = np.percentile(boot, [2.5, 97.5])
        cis[metric] = {"low": finite(low), "high": finite(high)}
    return cis


def evaluate_run(condition: str, seed: int, split: dict, cfg: dict,
                 ckpt_root: Path, n_boot: int) -> dict:
    """Evaluate one condition/seed checkpoint on val and test splits."""
    ckpt_dir = ckpt_root / condition / f"seed_{seed}"
    ckpt = ckpt_dir / "best.ckpt"
    meta_path = ckpt_dir / "best_meta.json"
    model = load_model(cfg["model_size"], cfg["node_dim"], ckpt)
    graph_dir = REPO / cfg["graph_dir"]

    by_split: dict[str, list[dict]] = {"val": [], "test": []}
    val_scores, val_labels = [], []

    for split_name in ("val", "test"):
        for pdb_id in split["splits"][split_name]:
            pt = graph_dir / f"{pdb_id}.pt"
            data = torch.load(str(pt), weights_only=False)
            if int(data.x.shape[1]) != int(cfg["node_dim"]):
                raise ValueError(f"{pt} has node_dim={data.x.shape[1]}, expected {cfg['node_dim']}")
            y = data.y.cpu().numpy().astype(int)
            scores = predict(model, data, cfg["zero_esm"])
            if split_name == "val" and int(y.sum()) >= 5 and len(np.unique(y)) == 2:
                val_scores.append(scores)
                val_labels.append(y)
            by_split[split_name].append({
                "pdb_id": pdb_id,
                "split": split_name,
                "scores": scores,
                "labels": y,
            })

    if not val_scores:
        raise RuntimeError(f"{condition} seed {seed}: no non-degenerate validation structures")

    threshold, val_mcc = select_mcc_threshold(
        np.concatenate(val_labels), np.concatenate(val_scores)
    )

    per_split = {}
    for split_name, raw_rows in by_split.items():
        rows = []
        for row in raw_rows:
            metrics = metric_dict(row["labels"], row["scores"], threshold)
            metrics.update({"pdb_id": row["pdb_id"], "split": split_name})
            rows.append(metrics)

        full_rows = rows
        clean_rows = [r for r in rows if not r["degenerate_labels"] and r.get("auprc") is not None]
        degenerate_rows = [r for r in rows if r["degenerate_labels"]]
        per_split[split_name] = {
            "full": aggregate(full_rows),
            "clean": aggregate(clean_rows),
            "degenerate_excluded": aggregate(clean_rows),
            "bootstrap_ci": bootstrap_ci(clean_rows, n_boot, seed),
            "degenerate_structures": [r["pdb_id"] for r in degenerate_rows],
            "per_structure": rows,
        }

    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    return {
        "condition": condition,
        "seed": seed,
        "checkpoint": str(ckpt),
        "checkpoint_meta": str(meta_path) if meta_path.exists() else None,
        "model_size": cfg["model_size"],
        "node_dim": cfg["node_dim"],
        "zero_esm": cfg["zero_esm"],
        "validation_selected_threshold": threshold,
        "validation_mcc_at_selected_threshold": finite(val_mcc),
        "meta": meta,
        "splits": per_split,
    }


def summarize(results: dict, out_path: Path) -> None:
    """Write a compact Markdown summary of clean test metrics."""
    lines = [
        "# Clean Split Evaluation Summary",
        "",
        "AUPRC is primary. AUROC is secondary. Thresholds are selected on validation only.",
        "",
        "| Condition | Seeds | Test AUPRC mean | 95% CI | Test AUROC mean | Degenerate test structures |",
        "|---|---:|---:|---|---:|---:|",
    ]
    for condition, runs in results["runs_by_condition"].items():
        auprcs = []
        aurocs = []
        degenerate = set()
        ci_parts = []
        for run in runs:
            test = run["splits"]["test"]
            clean = test["clean"]
            if clean["mean_auprc"] is not None:
                auprcs.append(clean["mean_auprc"])
            if clean["mean_auroc"] is not None:
                aurocs.append(clean["mean_auroc"])
            degenerate.update(test["degenerate_structures"])
            ci = test["bootstrap_ci"].get("auprc", {})
            if ci:
                ci_parts.append((ci.get("low"), ci.get("high")))
        mean_auprc = np.mean(auprcs) if auprcs else float("nan")
        mean_auroc = np.mean(aurocs) if aurocs else float("nan")
        if ci_parts:
            lows = [x[0] for x in ci_parts if x[0] is not None]
            highs = [x[1] for x in ci_parts if x[1] is not None]
            ci_text = f"{np.mean(lows):.4f}-{np.mean(highs):.4f}" if lows and highs else "n/a"
        else:
            ci_text = "n/a"
        lines.append(
            f"| {condition} | {len(runs)} | {mean_auprc:.4f} | {ci_text} | "
            f"{mean_auroc:.4f} | {len(degenerate)} |"
        )
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate clean split checkpoints")
    parser.add_argument("--split", type=Path, default=REPO / "data" / "splits" / "cryptosite_homology30_split.json")
    parser.add_argument("--checkpoint-root", type=Path, default=REPO / "checkpoints" / "clean_split")
    parser.add_argument("--conditions", nargs="+", default=list(CONDITIONS), choices=list(CONDITIONS))
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44])
    parser.add_argument("--out", type=Path, default=REPO / "data" / "results" / "clean_split_evaluation.json")
    parser.add_argument("--summary", type=Path, default=REPO / "data" / "results" / "clean_split_summary.md")
    parser.add_argument("--bootstrap", type=int, default=1000)
    args = parser.parse_args()

    split = json.loads(args.split.read_text(encoding="utf-8"))
    results = {
        "created_at": datetime.utcnow().isoformat() + "Z",
        "split_file": str(args.split),
        "primary_metric": "AUPRC",
        "threshold_rule": "Select MCC threshold on validation residues only, then freeze for test.",
        "bootstrap_unit": "structure",
        "runs_by_condition": {},
    }
    for condition in args.conditions:
        cfg = CONDITIONS[condition]
        runs = []
        for seed in args.seeds:
            runs.append(evaluate_run(condition, seed, split, cfg, args.checkpoint_root, args.bootstrap))
        results["runs_by_condition"][condition] = runs

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    summarize(results, args.summary)
    print(f"Evaluation written: {display_path(args.out)}")
    print(f"Summary written: {display_path(args.summary)}")


if __name__ == "__main__":
    main()
