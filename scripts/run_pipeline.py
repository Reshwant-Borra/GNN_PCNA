"""
End-to-end pipeline runner for GNN-PCNA.

Stages (run in order):
  1. crawl    — multi-domain web scraping (agents/pcna_crawler.py)
  2. verify   — Gemma 3:4b L6 credibility scoring (agents/gemma_verifier.py)
  3. vault    — write Obsidian notes (agents/obsidian_writer.py)
  4. fetch    — download verified PDB structures (src/data_processing/fetch_structures.py)
  5. graphs   — build PyG graph .pt files (scripts/build_graphs.py)
  6. split    — train/val/test split at protein level (scripts/make_split.py)
  7. train    — train CrypticGNN (src/training/train.py)

Usage:
    python scripts/run_pipeline.py                     # full pipeline
    python scripts/run_pipeline.py --from fetch        # resume from a stage
    python scripts/run_pipeline.py --only graphs split # run specific stages
    python scripts/run_pipeline.py --skip crawl verify # skip slow stages
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Core training pipeline — no external services required
STAGES         = ["fetch", "graphs", "split", "train"]
# Optional Obsidian research stages (require Ollama + internet crawler)
OBSIDIAN_STAGES = ["crawl", "verify", "vault"]
ALL_STAGES      = OBSIDIAN_STAGES + STAGES


def run(cmd: list[str], label: str) -> bool:
    """Run a subprocess command. Returns True on success."""
    print(f"\n{'='*60}")
    print(f"  STAGE: {label}")
    print(f"  CMD:   {' '.join(cmd)}")
    print(f"{'='*60}\n")
    result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    if result.returncode != 0:
        print(f"\n[PIPELINE] Stage '{label}' FAILED (exit {result.returncode})")
        return False
    print(f"\n[PIPELINE] Stage '{label}' complete.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="End-to-end GNN-PCNA pipeline runner. "
                    "Default: fetch -> graphs -> split -> train (no Obsidian required). "
                    "Add --with-obsidian to also run crawl/verify/vault stages.")
    parser.add_argument("--from",   dest="from_stage", choices=ALL_STAGES,
                        help="Resume from this stage (inclusive)")
    parser.add_argument("--only",   nargs="+", choices=ALL_STAGES,
                        help="Run only these stages")
    parser.add_argument("--skip",   nargs="+", choices=ALL_STAGES, default=[],
                        help="Skip these stages")
    parser.add_argument("--with-obsidian", action="store_true",
                        help="Include crawl/verify/vault stages (requires Ollama + internet)")

    # Stage-specific options
    parser.add_argument("--sources", nargs="+",
                        help="[crawl] Specific sources to query")
    parser.add_argument("--workers", type=int, default=6,
                        help="[crawl] Parallel workers (default 6)")
    parser.add_argument("--download-limit", type=int, default=100,
                        help="[fetch] Max PDB files to download (default 100)")
    parser.add_argument("--cutoff",  type=float, default=8.0,
                        help="[graphs] Cα–Cα edge cutoff in Å (default 8.0)")
    parser.add_argument("--epochs",  type=int,   default=100)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr",      type=float, default=1e-3)
    parser.add_argument("--patience", type=int,  default=10)
    args = parser.parse_args()

    # Determine which stages to run
    stage_pool = ALL_STAGES if args.with_obsidian else STAGES
    if args.only:
        active = [s for s in args.only if s in ALL_STAGES]
    elif args.from_stage:
        idx    = ALL_STAGES.index(args.from_stage)
        active = [s for s in ALL_STAGES[idx:] if s in stage_pool]
    else:
        active = list(stage_pool)

    active = [s for s in active if s not in args.skip]
    print(f"[PIPELINE] Stages to run: {' -> '.join(active)}")
    if not args.with_obsidian:
        print("[PIPELINE] Obsidian stages skipped (add --with-obsidian to include)")

    py = sys.executable

    for stage in active:
        if stage == "crawl":
            cmd = [py, "agents/pcna_crawler.py",
                   "--workers", str(args.workers)]
            if args.sources:
                cmd += ["--sources"] + args.sources
            if not run(cmd, "crawl"):
                break

        elif stage == "verify":
            cmd = [py, "agents/gemma_verifier.py"]
            if not run(cmd, "verify (Gemma L6)"):
                print("  [warn] Gemma verify failed — continuing without L6 scores")

        elif stage == "vault":
            cmd = [py, "agents/obsidian_writer.py"]
            if not run(cmd, "vault (Obsidian notes)"):
                print("  [warn] obsidian_writer failed — continuing")

        elif stage == "fetch":
            catalog = REPO_ROOT / "data" / "catalog" / "pcna_data_catalog.json"
            if catalog.exists():
                cmd = [py, "-m", "src.data_processing.fetch_structures",
                       "--catalog", str(catalog),
                       "--strip",
                       "--limit", str(args.download_limit)]
            else:
                # No catalog — fetch CryptoSite directly
                cmd = [py, "-m", "src.data_processing.fetch_structures",
                       "--cryptosite", "--strip"]
            if not run(cmd, "fetch PDB structures"):
                break

        elif stage == "graphs":
            cmd = [py, "scripts/build_graphs.py",
                   "--cutoff", str(args.cutoff)]
            if not run(cmd, "build graphs"):
                break

        elif stage == "split":
            cmd = [py, "scripts/make_split.py"]
            if not run(cmd, "make train/val/test split"):
                break

        elif stage == "train":
            train_dir = REPO_ROOT / "data" / "cryptosite" / "train"
            val_dir   = REPO_ROOT / "data" / "cryptosite" / "val"
            ckpt_dir  = REPO_ROOT / "checkpoints"
            ckpt_dir.mkdir(exist_ok=True)

            if not train_dir.exists() or not any(train_dir.glob("*.pt")):
                print("[PIPELINE] No training graphs found. Run 'graphs' and 'split' first.")
                break

            cmd = [py, "-m", "src.training.train",
                   "--train_dir", str(train_dir),
                   "--val_dir",   str(val_dir),
                   "--checkpoint_dir", str(ckpt_dir),
                   "--model_size", "small",
                   "--epochs",    str(args.epochs),
                   "--batch_size", str(args.batch_size),
                   "--lr",        str(args.lr),
                   "--patience",  str(args.patience)]
            if not run(cmd, "train PocketGNN"):
                break

    print("\n[PIPELINE] Done.")


if __name__ == "__main__":
    main()
