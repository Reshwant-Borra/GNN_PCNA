"""Governed spatial-only GraphSAGE-3L training — Option B retraining.

Trains GraphSAGE-3L with sequential edges removed (spatial edges only,
edge_type == 0). Uses the identical primary-model pipeline, hyperparameters,
and governance gates as the full model, differing only in edge filtering.

Authorization:
  reports/phase3/spatial_only_retrain_authorization_20260529.md
  (decision_id: phase3_spatial_only_retrain_20260529)

Parent gates:
  GATE 2: reports/phase3/first_training_signoff_20260528.md
  GATE 3: reports/phase3/baseline_gate3_authorization_20260529.md

Governance:
  docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md
  docs/scientific_governance/09_EVALUATION_PROTOCOL.md
  docs/scientific_governance/10_BASELINE_REQUIREMENTS.md
  docs/scientific_governance/19_STOP_CONDITIONS.md

Hard constraints (same as primary training):
  - Test set is NEVER loaded.
  - Split manifest hash 24dd5e347d880108 validated at load time.
  - PCNA cluster 1168 excluded from all train/val splits.
  - pos_weight computed from training fold only.
  - loss_mask applied before BCEWithLogitsLoss.
  - No sigmoid on model outputs.
  - No scientific claims.
  - All checkpoints labelled spatial_only_ to prevent confusion with full model.

Usage:
  python -u scripts/train_spatial_only.py
  python -u scripts/train_spatial_only.py --device cuda
  python -u scripts/train_spatial_only.py --folds 0 1 --seeds 0
  python -u scripts/train_spatial_only.py --device cpu  # fallback
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for _p in (str(SRC), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import torch
import torch.nn as nn
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader

from phase3_data.graph_loader import compute_pos_weight, load_split
from phase3_evaluation.metrics import compute_metrics_from_lists
from phase3_model.gnn import GraphSAGE3L
from phase3_training.gates import TrainingGateError, training_gate_status
from baselines.gnn_trainer import filter_edges

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------

GATE2_SIGNOFF = ROOT / "reports/phase3/first_training_signoff_20260528.md"
OPTION_B_AUTH = ROOT / "reports/phase3/spatial_only_retrain_authorization_20260529.md"
GRAPH_DIR     = ROOT / "data/graphs"
SPLIT_MANIFEST = ROOT / "data/registries/split_manifest_frozen.json"
CHECKPOINT_DIR = ROOT / "checkpoints/phase3"
OUT_DIR        = ROOT / "reports/phase3/spatial_only_training_runs"

EDGE_TYPE_SPATIAL: int = 0   # spatial 3D-proximity edges only

FOLDS = [0, 1, 2, 3]
SEEDS = [0, 1, 2]

# Hyperparameters — IDENTICAL to primary model.  Do NOT change without approval.
HIDDEN_DIM   = 128
DROPOUT      = 0.1
LR           = 1e-3
WEIGHT_DECAY = 1e-5
MAX_EPOCHS   = 200
PATIENCE     = 10
BATCH_SIZE   = 4


# ---------------------------------------------------------------------------
# Gate checks
# ---------------------------------------------------------------------------

def _check_option_b_auth() -> None:
    if not OPTION_B_AUTH.is_file():
        raise RuntimeError(
            f"Option B retraining authorization record not found:\n  {OPTION_B_AUTH}\n"
            "Human authorization must be recorded before the spatial-only retrain runs."
        )


# ---------------------------------------------------------------------------
# Per-protein validation helper (mirrors train_phase3.py)
# ---------------------------------------------------------------------------

def _collect_protein_scores(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
) -> list[tuple[list[float], list[int]]]:
    model.eval()
    protein_scores: list[tuple[list[float], list[int]]] = []
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            logits = model(batch)
            for i in range(batch.num_graphs):
                node_mask = batch.batch == i
                lm = batch.loss_mask[node_mask]
                s = logits[node_mask][lm].cpu().tolist()
                y = batch.y[node_mask][lm].cpu().tolist()
                protein_scores.append((s, y))
    return protein_scores


# ---------------------------------------------------------------------------
# Core training function — spatial-only variant
# ---------------------------------------------------------------------------

def train_one_run_spatial_only(
    val_fold: int,
    seed: int,
    device_str: str,
    verbose: bool = True,
) -> dict[str, Any]:
    """Train spatial-only GraphSAGE-3L for one (fold, seed) pair.

    Mirrors train_phase3.py::train_one_run exactly, adding:
      - OPTION_B_AUTH gate check
      - edge filtering: keep edge_type==0 (spatial) only
      - checkpoint prefix: spatial_only_fold{f}_seed{s}_best.pt

    Returns run manifest dict with same schema as primary training.
    """
    # Gate checks — both must pass.
    training_gate_status(real_training=True, human_pipeline_signoff=GATE2_SIGNOFF)
    _check_option_b_auth()

    t_start = time.time()
    torch.manual_seed(seed)

    if verbose:
        print(f"\n{'='*64}")
        print(f"  spatial-only  fold={val_fold}  seed={seed}  device={device_str}")
        print(f"{'='*64}")

    # --- Load data ---
    if verbose:
        print("Loading graphs...", end=" ", flush=True)
    train_data_raw = load_split(GRAPH_DIR, SPLIT_MANIFEST, "train", val_fold=val_fold)
    val_data_raw   = load_split(GRAPH_DIR, SPLIT_MANIFEST, "val",   val_fold=val_fold)
    if verbose:
        print(f"train={len(train_data_raw)}  val={len(val_data_raw)}")

    # --- Filter to spatial edges only ---
    train_data = [filter_edges(d, EDGE_TYPE_SPATIAL) for d in train_data_raw]
    val_data   = [filter_edges(d, EDGE_TYPE_SPATIAL) for d in val_data_raw]

    if verbose:
        sample = train_data[0]
        n_edges_before = train_data_raw[0].edge_index.shape[1]
        n_edges_after  = sample.edge_index.shape[1]
        print(f"  Edge filtering: {n_edges_before} -> {n_edges_after} edges per sample (kept spatial only)")

    # --- pos_weight from training fold only (labels unaffected by edge filtering) ---
    pos_weight = compute_pos_weight(train_data)
    if verbose:
        print(f"  pos_weight (train-only): {pos_weight.item():.4f}")

    # --- DataLoaders ---
    train_loader = DataLoader(train_data, batch_size=BATCH_SIZE, shuffle=True)
    val_loader   = DataLoader(val_data,   batch_size=32,         shuffle=False)

    # --- Model and optimizer ---
    device = torch.device(device_str)
    model = GraphSAGE3L(hidden_dim=HIDDEN_DIM, dropout=DROPOUT).to(device)
    pw = pos_weight.to(device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pw)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)

    best_val_auprc = -1.0
    best_epoch = 0
    best_state: dict[str, Any] = copy.deepcopy(model.state_dict())
    no_improve = 0
    history: list[dict[str, Any]] = []

    # --- Training loop (identical to train_phase3.py) ---
    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()
        total_loss, total_nodes = 0.0, 0
        for batch in train_loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            logits = model(batch)
            mask = batch.loss_mask
            loss = criterion(logits[mask], batch.y[mask].float())
            loss.backward()
            optimizer.step()
            n = int(mask.sum())
            total_loss += loss.item() * n
            total_nodes += n
        train_loss = total_loss / max(total_nodes, 1)

        val_scores = _collect_protein_scores(model, val_loader, device)
        val_metrics = compute_metrics_from_lists(val_scores)
        val_auprc = val_metrics["macro_auprc"]
        val_auroc = val_metrics["macro_auroc"]

        history.append({
            "epoch": epoch,
            "train_loss": round(train_loss, 6),
            "val_macro_auprc": round(val_auprc, 6) if not math.isnan(val_auprc) else None,
            "val_macro_auroc": round(val_auroc, 6) if not math.isnan(val_auroc) else None,
        })

        improved = not math.isnan(val_auprc) and val_auprc > best_val_auprc
        if improved:
            best_val_auprc = val_auprc
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())
            no_improve = 0
        else:
            no_improve += 1

        if verbose and (epoch % 5 == 0 or epoch == 1 or improved):
            flag = " *" if improved else ""
            print(
                f"  ep {epoch:3d}  loss={train_loss:.4f}  "
                f"val_auprc={val_auprc:.4f}  val_auroc={val_auroc:.4f}{flag}",
                flush=True,
            )

        if no_improve >= PATIENCE:
            if verbose:
                print(f"  Early stop at epoch {epoch} (patience={PATIENCE})", flush=True)
            break

    # --- Save checkpoint ---
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    ckpt_name = f"spatial_only_fold{val_fold}_seed{seed}_best.pt"
    ckpt_path = CHECKPOINT_DIR / ckpt_name
    torch.save(
        {
            "model_state_dict": best_state,
            "config": {
                "hidden_dim": HIDDEN_DIM,
                "dropout": DROPOUT,
                "lr": LR,
                "weight_decay": WEIGHT_DECAY,
                "max_epochs": MAX_EPOCHS,
                "patience": PATIENCE,
                "batch_size": BATCH_SIZE,
                "edge_type_filter": EDGE_TYPE_SPATIAL,
                "architecture_variant": "spatial_only",
            },
            "val_fold": val_fold,
            "seed": seed,
            "best_epoch": best_epoch,
            "best_val_macro_auprc": best_val_auprc,
            "governance": {
                "option_b_auth": str(OPTION_B_AUTH),
                "decision_id": "phase3_spatial_only_retrain_20260529",
                "gate2_signoff": str(GATE2_SIGNOFF),
                "split_manifest": str(SPLIT_MANIFEST),
                "edge_type_filter": "EDGE_TYPE_SPATIAL=0",
                "no_test_set_evaluation": True,
                "no_scientific_claims": True,
            },
        },
        ckpt_path,
    )

    elapsed = time.time() - t_start
    if verbose:
        print(f"  Best epoch={best_epoch}  val_macro_auprc={best_val_auprc:.4f}", flush=True)
        print(f"  Checkpoint: {ckpt_path}", flush=True)
        print(f"  Elapsed: {elapsed:.1f}s", flush=True)

    manifest = {
        "artifact_type": "phase3_spatial_only_training_run",
        "architecture_variant": "spatial_only",
        "edge_type_filter": EDGE_TYPE_SPATIAL,
        "val_fold": val_fold,
        "seed": seed,
        "hidden_dim": HIDDEN_DIM,
        "dropout": DROPOUT,
        "lr": LR,
        "weight_decay": WEIGHT_DECAY,
        "batch_size": BATCH_SIZE,
        "max_epochs": MAX_EPOCHS,
        "patience": PATIENCE,
        "device": device_str,
        "n_train": len(train_data_raw),
        "n_val": len(val_data_raw),
        "pos_weight": round(pos_weight.item(), 4),
        "epochs_run": len(history),
        "best_epoch": best_epoch,
        "best_val_macro_auprc": round(best_val_auprc, 6),
        "checkpoint_path": str(ckpt_path),
        "elapsed_seconds": round(elapsed, 1),
        "history": history,
        "governance": {
            "option_b_auth": str(OPTION_B_AUTH),
            "decision_id": "phase3_spatial_only_retrain_20260529",
            "gate2_signoff_record": "reports/phase3/first_training_signoff_20260528.md",
            "split_manifest_hash_prefix": "24dd5e347d880108",
            "no_test_set_evaluation": True,
            "no_scientific_claims": True,
        },
    }
    return manifest


# ---------------------------------------------------------------------------
# Aggregate summary helpers
# ---------------------------------------------------------------------------

def _fold_stats(manifests: list[dict]) -> dict[str, Any]:
    folds: dict[int, list[float]] = {}
    for m in manifests:
        fold = m["val_fold"]
        folds.setdefault(fold, []).append(m["best_val_macro_auprc"])
    fold_means = {f: sum(v) / len(v) for f, v in folds.items()}
    all_auprcs = [m["best_val_macro_auprc"] for m in manifests]
    mean = sum(all_auprcs) / len(all_auprcs)
    sd = math.sqrt(sum((x - mean) ** 2 for x in all_auprcs) / max(len(all_auprcs) - 1, 1))
    return {
        "per_fold_means": fold_means,
        "overall_mean": round(mean, 6),
        "overall_sd": round(sd, 6),
        "overall_min": round(min(all_auprcs), 6),
        "overall_max": round(max(all_auprcs), 6),
        "n_runs": len(all_auprcs),
        "all_auprcs": [round(x, 6) for x in all_auprcs],
    }


def _write_summary(manifests: list[dict], out_dir: Path) -> None:
    stats = _fold_stats(manifests)
    best_run = max(manifests, key=lambda m: m["best_val_macro_auprc"])
    per_fold_per_seed = [
        {
            "fold": m["val_fold"],
            "seed": m["seed"],
            "best_val_macro_auprc": m["best_val_macro_auprc"],
            "best_epoch": m["best_epoch"],
            "epochs_run": m["epochs_run"],
            "elapsed_seconds": m["elapsed_seconds"],
            "device": m["device"],
        }
        for m in sorted(manifests, key=lambda m: (m["val_fold"], m["seed"]))
    ]

    summary = {
        "artifact_type": "phase3_spatial_only_all_runs_summary",
        "architecture_variant": "spatial_only",
        "edge_type_filter": EDGE_TYPE_SPATIAL,
        "decision_id": "phase3_spatial_only_retrain_20260529",
        "folds": FOLDS,
        "seeds": SEEDS,
        "per_fold_per_seed": per_fold_per_seed,
        "per_fold_mean_macro_auprc": {str(k): round(v, 6) for k, v in stats["per_fold_means"].items()},
        "overall_macro_auprc_mean": stats["overall_mean"],
        "overall_macro_auprc_sd": stats["overall_sd"],
        "overall_macro_auprc_min": stats["overall_min"],
        "overall_macro_auprc_max": stats["overall_max"],
        "n_runs": stats["n_runs"],
        "recommended_checkpoint": str(CHECKPOINT_DIR / f"spatial_only_fold{best_run['val_fold']}_seed{best_run['seed']}_best.pt"),
        "recommended_fold": best_run["val_fold"],
        "recommended_seed": best_run["seed"],
        "recommended_val_macro_auprc": best_run["best_val_macro_auprc"],
        "governance": {
            "option_b_auth": str(OPTION_B_AUTH),
            "decision_id": "phase3_spatial_only_retrain_20260529",
            "split_manifest_hash_prefix": "24dd5e347d880108",
            "no_test_set_evaluation": True,
            "no_scientific_claims": True,
        },
    }
    summary_path = out_dir / "all_runs_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"\n[summary] Written to {summary_path}", flush=True)
    print(
        f"  overall  macro_auprc = {stats['overall_mean']:.4f} ± {stats['overall_sd']:.4f}"
        f"  (range [{stats['overall_min']:.4f}, {stats['overall_max']:.4f}])",
        flush=True,
    )
    print(f"  best run: fold={best_run['val_fold']} seed={best_run['seed']}  auprc={best_run['best_val_macro_auprc']:.4f}", flush=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _auto_device() -> str:
    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        print(f"[device] CUDA available — {name}. Using cuda.", flush=True)
        return "cuda"
    print("[device] CUDA not available. Using cpu.", flush=True)
    return "cpu"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--folds", nargs="+", type=int, default=FOLDS)
    p.add_argument("--seeds", nargs="+", type=int, default=SEEDS)
    p.add_argument(
        "--device", type=str, default=None,
        help="Training device: 'cuda', 'cpu', or 'auto' (default: auto-detect).",
    )
    p.add_argument(
        "--force", action="store_true",
        help="Re-run even if manifest already exists (overwrites).",
    )
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    device_str = args.device if args.device and args.device != "auto" else _auto_device()
    folds: list[int] = args.folds
    seeds: list[int] = args.seeds

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\nSpatial-only retrain — authorization: {OPTION_B_AUTH.name}", flush=True)
    print(f"  edge_type_filter = SPATIAL (0)  |  device = {device_str}", flush=True)
    print(f"  folds = {folds}  seeds = {seeds}  total runs = {len(folds) * len(seeds)}", flush=True)

    # Confirm auth file exists before attempting any run
    if not OPTION_B_AUTH.is_file():
        print(f"ERROR: Option B authorization record missing: {OPTION_B_AUTH}", file=sys.stderr)
        return 2
    if not GATE2_SIGNOFF.is_file():
        print(f"ERROR: GATE 2 signoff record missing: {GATE2_SIGNOFF}", file=sys.stderr)
        return 2

    t_total = time.time()
    completed, skipped = 0, 0
    manifests: list[dict] = []

    for fold in folds:
        for seed in seeds:
            out_path = OUT_DIR / f"fold{fold}_seed{seed}_manifest.json"

            if out_path.exists() and not args.force:
                print(f"[skip] fold={fold} seed={seed} — manifest exists", flush=True)
                with open(out_path) as f:
                    manifests.append(json.load(f))
                skipped += 1
                continue

            try:
                m = train_one_run_spatial_only(
                    val_fold=fold,
                    seed=seed,
                    device_str=device_str,
                    verbose=True,
                )
            except TrainingGateError as exc:
                print(f"GATE ERROR: {exc}", file=sys.stderr)
                return 2

            out_path.write_text(json.dumps(m, indent=2))
            print(
                f"[saved] fold={fold} seed={seed}  "
                f"val_macro_auprc={m['best_val_macro_auprc']:.4f}  ({m['elapsed_seconds']:.0f}s)",
                flush=True,
            )
            manifests.append(m)
            completed += 1

    elapsed_min = (time.time() - t_total) / 60
    print(
        f"\nDone. completed={completed} skipped={skipped} "
        f"total_elapsed={elapsed_min:.1f}min",
        flush=True,
    )

    # Write summary whenever we have manifests (new or resumed)
    if manifests:
        _write_summary(manifests, OUT_DIR)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
