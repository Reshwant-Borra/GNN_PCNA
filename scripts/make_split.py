"""
Split graph .pt files into train / val / test sets.

Splits at the PROTEIN level (not residue level) to prevent data leakage.
PCNA structures (1W60, 8GLA, 1AXC) are excluded from the split
and stay in data/pcna/ for inference and positive-control validation.
1W61 is NOT PCNA — it is proline racemase (Trypanosoma cruzi) and is excluded entirely.

Only graphs that have pocket labels (data.y is not None) are included
in the split — apo structures without labels are excluded.

Default split: 80% train / 10% val / 10% test (deterministic seed).

Output:
    data/cryptosite/train/*.pt
    data/cryptosite/val/*.pt
    data/cryptosite/test/*.pt
    data/splits/cryptosite_split.json  — manifest for reproducibility

Usage:
    python scripts/make_split.py
    python scripts/make_split.py --seed 99 --val-frac 0.15 --test-frac 0.15
    python scripts/make_split.py --graph-dir data/graphs --dry-run
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

import torch

GRAPH_DIR  = REPO_ROOT / "data" / "graphs"
SPLITS_DIR = REPO_ROOT / "data" / "splits"
TRAIN_DIR  = REPO_ROOT / "data" / "cryptosite" / "train"
VAL_DIR    = REPO_ROOT / "data" / "cryptosite" / "val"
TEST_DIR   = REPO_ROOT / "data" / "cryptosite" / "test"

_PCNA_IDS = {"1W60", "8GLA", "1AXC"}  # 1W61 removed — it is proline racemase, not PCNA


def _has_labels(pt_path: Path) -> bool:
    """Return True if the graph has pocket labels (data.y present and has positives)."""
    try:
        data = torch.load(str(pt_path), weights_only=False)
        return hasattr(data, 'y') and data.y is not None
    except Exception:
        return False


def make_split(
    graph_dir: Path = GRAPH_DIR,
    val_frac: float = 0.10,
    test_frac: float = 0.10,
    seed: int = 42,
    dry_run: bool = False,
    force: bool = False,
    split_root: Path | None = None,
    copy_files: bool = False,
) -> dict:
    """
    Split graph files and write a manifest to data/splits/cryptosite_split.json.
    Files are NOT copied by default — training loads directly from data/graphs/.
    Pass copy_files=True to also copy .pt files into train/val/test directories.
    Returns the split manifest dict.
    """
    all_pt = sorted(graph_dir.glob("*.pt"))

    # Exclude PCNA core structures
    candidates = [p for p in all_pt
                  if p.stem.upper() not in _PCNA_IDS]

    # Keep only labeled graphs
    labeled = [p for p in candidates if _has_labels(p)]
    unlabeled_count = len(candidates) - len(labeled)

    print(f"Found {len(all_pt)} total graphs")
    print(f"  PCNA core excluded : {len(all_pt) - len(candidates)}")
    print(f"  No labels (apo)    : {unlabeled_count}")
    print(f"  Labeled for split  : {len(labeled)}")

    if not labeled:
        print("\nNo labeled graphs found. Run scripts/build_graphs.py first.")
        return {}

    rng = random.Random(seed)
    shuffled = list(labeled)
    rng.shuffle(shuffled)

    n       = len(shuffled)
    n_val   = max(1, int(n * val_frac))
    n_test  = max(1, int(n * test_frac))
    n_train = n - n_val - n_test

    splits = {
        "train": shuffled[:n_train],
        "val":   shuffled[n_train:n_train + n_val],
        "test":  shuffled[n_train + n_val:],
    }

    dest_dirs = {
        "train": TRAIN_DIR if split_root is None else split_root / "train",
        "val":   VAL_DIR   if split_root is None else split_root / "val",
        "test":  TEST_DIR  if split_root is None else split_root / "test",
    }

    print(f"\nSplit (seed={seed}): train={n_train}  val={n_val}  test={n_test}")

    manifest: dict = {
        "seed": seed,
        "val_frac":  val_frac,
        "test_frac": test_frac,
        "splits": {},
    }

    for split_name, paths in splits.items():
        dest = dest_dirs[split_name]
        manifest["splits"][split_name] = [p.stem for p in paths]

        if dry_run:
            print(f"\n  [{split_name}] (dry-run, {len(paths)} files)")
            continue

        if copy_files:
            dest.mkdir(parents=True, exist_ok=True)
            if force:
                for f in dest.glob("*.pt"):
                    f.unlink()
            for p in paths:
                dest_file = dest / p.name
                if not dest_file.exists() or force:
                    shutil.copy2(str(p), str(dest_file))
            try:
                dest_label = dest.relative_to(REPO_ROOT)
            except ValueError:
                dest_label = dest
            print(f"  [{split_name}] {len(paths)} files -> {dest_label}")
        else:
            print(f"  [{split_name}] {len(paths)} files (manifest only — loading from {graph_dir.relative_to(REPO_ROOT)})")

    if not dry_run:
        SPLITS_DIR.mkdir(parents=True, exist_ok=True)
        manifest_path = SPLITS_DIR / "cryptosite_split.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))
        print(f"\nManifest -> {manifest_path.relative_to(REPO_ROOT)}")
        print("\nReady to train (using manifest — no duplicate .pt files):")
        print(f"  python -m src.training.train \\")
        print(f"    --train_manifest data/splits/cryptosite_split.json \\")
        print(f"    --graph_dir      data/graphs \\")
        print(f"    --checkpoint_dir checkpoints/ \\")
        print(f"    --epochs 100 --batch_size 16 --lr 1e-3 --patience 10")

    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Split PyG graph files into train/val/test at protein level")
    parser.add_argument("--graph-dir",  type=Path,  default=GRAPH_DIR)
    parser.add_argument("--split-root", type=Path,  default=None,
                        help="Custom root for train/val/test dirs (default: data/cryptosite/)")
    parser.add_argument("--val-frac",   type=float, default=0.10)
    parser.add_argument("--test-frac",  type=float, default=0.10)
    parser.add_argument("--seed",       type=int,   default=42)
    parser.add_argument("--dry-run",    action="store_true")
    parser.add_argument("--force",      action="store_true",
                        help="Overwrite existing split files")
    parser.add_argument("--copy-files", action="store_true",
                        help="Copy .pt files into train/val/test dirs (legacy; creates duplicates)")
    args = parser.parse_args()

    make_split(
        graph_dir=args.graph_dir,
        val_frac=args.val_frac,
        test_frac=args.test_frac,
        seed=args.seed,
        dry_run=args.dry_run,
        force=args.force,
        split_root=args.split_root,
        copy_files=args.copy_files,
    )


if __name__ == "__main__":
    main()
