"""Phase 3 governed training runner.

Trains GraphSAGE-3L for one (val_fold, seed) pair.
Saves best checkpoint and a run manifest JSON.

Usage:
  python scripts/train_phase3.py --val-fold 0 --seed 0
  python scripts/train_phase3.py --val-fold 0 --seed 0 --hidden-dim 64
  python scripts/train_phase3.py --help

GATE 2 must be cleared (first_training_signoff exists) before this runs.
Test-set evaluation is never performed here.

Governance:
  docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md
  docs/scientific_governance/09_EVALUATION_PROTOCOL.md
  docs/scientific_governance/19_STOP_CONDITIONS.md
Signoff: reports/phase3/first_training_signoff_20260528.md
  (decision_id: phase3_first_training_signoff_20260528)
"""

from __future__ import annotations

import argparse
import copy
import dataclasses
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import torch
import torch.nn as nn
from torch_geometric.loader import DataLoader

from phase3_data.graph_loader import compute_pos_weight, load_split, make_dataloader
from phase3_evaluation.metrics import compute_metrics_from_lists
from phase3_model.gnn import GraphSAGE3L
from phase3_training.gates import TrainingGateError, training_gate_status
from phase3_training.trainer import TrainerConfig

SIGNOFF_RECORD = ROOT / "reports/phase3/first_training_signoff_20260528.md"
GRAPH_DIR = ROOT / "data/graphs"
SPLIT_MANIFEST = ROOT / "data/registries/split_manifest_frozen.json"
CHECKPOINT_BASE = ROOT / "checkpoints/phase3"


def train_one_run(
    val_fold: int,
    seed: int,
    config: TrainerConfig,
    graph_dir: Path,
    split_manifest: Path,
    checkpoint_dir: Path,
    verbose: bool = True,
) -> dict:
    """Train one (fold, seed) pair. Returns run manifest dict."""

    # Gate check — refuses if signoff record is absent.
    gate = training_gate_status(real_training=True, human_pipeline_signoff=SIGNOFF_RECORD)

    t_start = time.time()
    torch.manual_seed(seed)

    if verbose:
        print(f"\n{'='*60}")
        print(f"  fold={val_fold}  seed={seed}  hidden={config.hidden_dim}  lr={config.lr}")
        print(f"{'='*60}")

    # Load data
    if verbose:
        print("Loading graphs...", end=" ", flush=True)
    train_data = load_split(graph_dir, split_manifest, "train", val_fold=val_fold)
    val_data   = load_split(graph_dir, split_manifest, "val",   val_fold=val_fold)
    if verbose:
        print(f"train={len(train_data)}  val={len(val_data)}")

    # pos_weight from training fold only (governance requirement)
    pos_weight = compute_pos_weight(train_data)
    if verbose:
        print(f"pos_weight (train-only): {pos_weight.item():.4f}")

    train_loader = make_dataloader(train_data, batch_size=config.batch_size, shuffle=True)
    # Val batch size is a compute-efficiency choice only — batch isolation is verified,
    # so logits are identical regardless of how many proteins share a batch.
    val_loader   = make_dataloader(val_data, batch_size=32, shuffle=False)

    device = torch.device(config.device)
    model = GraphSAGE3L(hidden_dim=config.hidden_dim, dropout=config.dropout).to(device)
    pw = pos_weight.to(device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pw)
    optimizer = torch.optim.Adam(
        model.parameters(), lr=config.lr, weight_decay=config.weight_decay
    )

    best_val_auprc = -1.0
    best_epoch = 0
    best_state = copy.deepcopy(model.state_dict())
    no_improve = 0
    history = []

    for epoch in range(1, config.max_epochs + 1):
        # Train epoch
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

        # Val evaluation
        model.eval()
        protein_scores = []
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(device)
                logits = model(batch)
                for i in range(batch.num_graphs):
                    node_mask = batch.batch == i
                    lm = batch.loss_mask[node_mask]
                    s = logits[node_mask][lm].cpu().tolist()
                    y = batch.y[node_mask][lm].cpu().tolist()
                    protein_scores.append((s, y))
        val_metrics = compute_metrics_from_lists(protein_scores)
        val_auprc = val_metrics["macro_auprc"]

        history.append({
            "epoch": epoch,
            "train_loss": round(train_loss, 6),
            "val_macro_auprc": round(val_auprc, 6) if not math.isnan(val_auprc) else None,
            "val_macro_auroc": round(val_metrics["macro_auroc"], 6) if not math.isnan(val_metrics["macro_auroc"]) else None,
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
                f"val_macro_auprc={val_auprc:.4f}{flag}"
            )

        if no_improve >= config.patience:
            if verbose:
                print(f"  Early stop at epoch {epoch} (patience={config.patience})")
            break

    # Save best checkpoint
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    ckpt_name = f"fold{val_fold}_seed{seed}_best.pt"
    ckpt_path = checkpoint_dir / ckpt_name
    torch.save(
        {
            "model_state_dict": best_state,
            "config": dataclasses.asdict(config),
            "val_fold": val_fold,
            "seed": seed,
            "best_epoch": best_epoch,
            "best_val_macro_auprc": best_val_auprc,
            "governance": {
                "signoff": str(SIGNOFF_RECORD),
                "decision_id": "phase3_first_training_signoff_20260528",
                "split_manifest": str(split_manifest),
            },
        },
        ckpt_path,
    )

    elapsed = time.time() - t_start
    if verbose:
        print(f"  Best epoch={best_epoch}  val_macro_auprc={best_val_auprc:.4f}")
        print(f"  Checkpoint: {ckpt_path}")
        print(f"  Elapsed: {elapsed:.1f}s")

    manifest = {
        "artifact_type": "phase3_training_run",
        "val_fold": val_fold,
        "seed": seed,
        "hidden_dim": config.hidden_dim,
        "dropout": config.dropout,
        "lr": config.lr,
        "weight_decay": config.weight_decay,
        "batch_size": config.batch_size,
        "max_epochs": config.max_epochs,
        "patience": config.patience,
        "n_train": len(train_data),
        "n_val": len(val_data),
        "pos_weight": round(pos_weight.item(), 4),
        "epochs_run": len(history),
        "best_epoch": best_epoch,
        "best_val_macro_auprc": round(best_val_auprc, 6),
        "checkpoint_path": str(ckpt_path),
        "elapsed_seconds": round(elapsed, 1),
        "history": history,
        "gate_status": gate,
        "governance": {
            "signoff_record": "reports/phase3/first_training_signoff_20260528.md",
            "decision_id": "phase3_first_training_signoff_20260528",
            "split_manifest_hash_prefix": "24dd5e347d880108",
            "no_test_set_evaluation": True,
            "no_scientific_claims": True,
        },
    }

    return manifest


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--val-fold", type=int, required=True, choices=[0, 1, 2, 3])
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--hidden-dim", type=int, default=128, choices=[64, 128])
    p.add_argument("--dropout", type=float, default=0.1)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--weight-decay", type=float, default=1e-5)
    p.add_argument("--max-epochs", type=int, default=200)
    p.add_argument("--patience", type=int, default=10)
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--out-json", type=Path, default=None)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    config = TrainerConfig(
        hidden_dim=args.hidden_dim,
        dropout=args.dropout,
        lr=args.lr,
        weight_decay=args.weight_decay,
        max_epochs=args.max_epochs,
        patience=args.patience,
        batch_size=args.batch_size,
        seed=args.seed,
    )
    try:
        manifest = train_one_run(
            val_fold=args.val_fold,
            seed=args.seed,
            config=config,
            graph_dir=GRAPH_DIR,
            split_manifest=SPLIT_MANIFEST,
            checkpoint_dir=CHECKPOINT_BASE,
        )
    except TrainingGateError as exc:
        print(f"GATE ERROR: {exc}", file=sys.stderr)
        return 2

    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        with open(args.out_json, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"Manifest written to {args.out_json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
