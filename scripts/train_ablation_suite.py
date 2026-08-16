"""Run the required clean-split GNN ablation suite.

Conditions:
- small_geometry: PocketGNN.small on 40-dim hand-crafted graphs
- xl_geometry: PocketGNNXL architecture on 40-dim hand-crafted graphs
- xl_esm_zero: PocketGNNXL on 520-dim graphs with ESM2 columns zeroed
- xl_esm_full: PocketGNNXL on 520-dim graphs with full ESM2 features
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

CONDITIONS = {
    "small_geometry": {
        "model_size": "small",
        "graph_dir": "data/graphs",
        "node_dim": "40",
        "feature_dim": "40",
        "zero_esm": False,
    },
    "xl_geometry": {
        "model_size": "xl",
        "graph_dir": "data/graphs",
        "node_dim": "40",
        "feature_dim": "40",
        "zero_esm": False,
    },
    "xl_esm_zero": {
        "model_size": "xl",
        "graph_dir": "data/graphs_xl",
        "node_dim": "520",
        "feature_dim": "520",
        "zero_esm": True,
    },
    "xl_esm_full": {
        "model_size": "xl",
        "graph_dir": "data/graphs_xl",
        "node_dim": "520",
        "feature_dim": "520",
        "zero_esm": False,
    },
}


def run(cmd: list[str], dry_run: bool) -> None:
    """Print and optionally execute a command."""
    print(" ".join(cmd))
    if not dry_run:
        subprocess.run(cmd, cwd=REPO, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train all clean-split ablation conditions")
    parser.add_argument("--split", default="data/splits/cryptosite_homology30_split.json")
    parser.add_argument("--audit", default="data/results/homology30_audit.json")
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44])
    parser.add_argument("--conditions", nargs="+", default=list(CONDITIONS),
                        choices=list(CONDITIONS))
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-env-check", action="store_true")
    args = parser.parse_args()

    py = sys.executable

    if not args.skip_env_check:
        run([py, "scripts/check_env.py"], args.dry_run)

    validated: set[tuple[str, str]] = set()
    for condition in args.conditions:
        cfg = CONDITIONS[condition]
        key = (cfg["graph_dir"], cfg["feature_dim"])
        if key not in validated:
            out = f"data/results/split_integrity_{cfg['feature_dim']}.json"
            run([
                py, "scripts/validate_split_integrity.py",
                "--split", args.split,
                "--graph-dir", cfg["graph_dir"],
                "--feature-dim", cfg["feature_dim"],
                "--out", out,
            ], args.dry_run)
            validated.add(key)

        for seed in args.seeds:
            ckpt_dir = f"checkpoints/clean_split/{condition}/seed_{seed}"
            cmd = [
                py, "-m", "src.training.train",
                "--train_manifest", args.split,
                "--graph_dir", cfg["graph_dir"],
                "--checkpoint_dir", ckpt_dir,
                "--model_size", cfg["model_size"],
                "--node_dim", cfg["node_dim"],
                "--condition", condition,
                "--homology_audit", args.audit,
                "--require_clean_audit",
                "--seed", str(seed),
                "--epochs", str(args.epochs),
                "--batch_size", str(args.batch_size),
                "--lr", str(args.lr),
                "--weight_decay", str(args.weight_decay),
                "--patience", str(args.patience),
            ]
            if cfg["zero_esm"]:
                cmd.append("--zero_esm")
            run(cmd, args.dry_run)

    print("Ablation suite complete.")


if __name__ == "__main__":
    main()
