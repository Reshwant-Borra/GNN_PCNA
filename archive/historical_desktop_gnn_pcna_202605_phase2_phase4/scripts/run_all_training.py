"""Orchestration script: run all Phase 3 CV folds x seeds.

Skips any (fold, seed) pair whose manifest JSON already exists in
reports/phase3/training_runs/.

Usage:
  python -u scripts/run_all_training.py
  python -u scripts/run_all_training.py --folds 0 1 --seeds 0 1 2
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from train_phase3 import train_one_run
from phase3_training.trainer import TrainerConfig

GRAPH_DIR = ROOT / "data/graphs"
SPLIT_MANIFEST = ROOT / "data/registries/split_manifest_frozen.json"
CHECKPOINT_BASE = ROOT / "checkpoints/phase3"
OUT_DIR = ROOT / "reports/phase3/training_runs"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--folds", nargs="+", type=int, default=[0, 1, 2, 3])
    p.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    p.add_argument("--hidden-dim", type=int, default=128)
    args = p.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    config = TrainerConfig(
        hidden_dim=args.hidden_dim,
        dropout=0.1, lr=1e-3, weight_decay=1e-5,
        max_epochs=200, patience=10, batch_size=4,
    )

    t_total = time.time()
    completed, skipped = 0, 0

    for fold in args.folds:
        for seed in args.seeds:
            out_path = OUT_DIR / f"fold{fold}_seed{seed}_manifest.json"
            if out_path.exists():
                print(f"[skip] fold={fold} seed={seed} — manifest already exists", flush=True)
                skipped += 1
                continue

            m = train_one_run(
                val_fold=fold, seed=seed,
                config=TrainerConfig(**{**vars(config), "seed": seed}),
                graph_dir=GRAPH_DIR,
                split_manifest=SPLIT_MANIFEST,
                checkpoint_dir=CHECKPOINT_BASE,
                verbose=True,
            )
            with open(out_path, "w") as f:
                json.dump(m, f, indent=2)
            print(f"[saved] fold={fold} seed={seed}  val_macro_auprc={m['best_val_macro_auprc']:.4f}", flush=True)
            completed += 1

    elapsed = (time.time() - t_total) / 60
    print(f"\nDone. completed={completed} skipped={skipped} total_elapsed={elapsed:.1f}min", flush=True)

    # Write summary if any new runs completed
    if completed > 0:
        manifests = []
        for fold in args.folds:
            for seed in args.seeds:
                p2 = OUT_DIR / f"fold{fold}_seed{seed}_manifest.json"
                if p2.exists():
                    with open(p2) as f:
                        manifests.append(json.load(f))
        with open(OUT_DIR / "all_runs_summary.json", "w") as f:
            json.dump(manifests, f, indent=2)
        print(f"Summary written to {OUT_DIR / 'all_runs_summary.json'}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
