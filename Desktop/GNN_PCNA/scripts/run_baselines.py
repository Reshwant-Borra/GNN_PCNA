"""Master baseline runner for Phase 3.

Runs all required baselines on validation folds only. Never loads test data.
Writes per-baseline manifests to reports/phase3/baseline_runs/.

Required baselines (GATE 3 authorized, 2026-05-29):
  - random:           uniform random scores, 3 seeds
  - degree:           negative spatial degree, no training
  - gcn_1l:          GCN-1L, 4 folds x 3 seeds
  - gat_2l:          GAT-2L, 4 folds x 3 seeds
  - sage_no_spatial:  GraphSAGE-3L with sequential edges only, 4 folds x 3 seeds
  - sage_no_sequential: GraphSAGE-3L with spatial edges only, 4 folds x 3 seeds

External baselines (fpocket, P2Rank, PocketMiner) require tool installation;
stubs are written to baseline_runs/ noting the installation requirement.

Usage:
  python scripts/run_baselines.py                    # all baselines
  python scripts/run_baselines.py --only random degree  # quick non-training baselines
  python scripts/run_baselines.py --folds 0 1 --seeds 0  # reduced sweep

Governance:
  docs/scientific_governance/10_BASELINE_REQUIREMENTS.md
  docs/scientific_governance/09_EVALUATION_PROTOCOL.md
Gate: reports/phase3/baseline_gate3_authorization_20260529.md
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from phase3_data.graph_loader import compute_pos_weight, load_split, make_dataloader
from phase3_model.gnn import GraphSAGE3L
from baselines.random_baseline import run_random_baseline
from baselines.structural_baseline import run_degree_baseline
from baselines.gnn_models import GCN1L, GAT2L
from baselines.gnn_trainer import (
    EDGE_TYPE_SEQUENTIAL,
    EDGE_TYPE_SPATIAL,
    BaselineGateError,
    train_baseline_gnn,
)
from phase3_evaluation.metrics import aggregate_seeds

GRAPH_DIR = ROOT / "data/graphs"
SPLIT_MANIFEST = ROOT / "data/registries/split_manifest_frozen.json"
OUT_DIR = ROOT / "reports/phase3/baseline_runs"
GATE3_RECORD = ROOT / "reports/phase3/baseline_gate3_authorization_20260529.md"
SIGNOFF_RECORD = ROOT / "reports/phase3/first_training_signoff_20260528.md"

FOLDS = [0, 1, 2, 3]
SEEDS = [0, 1, 2]

_GNN_BASELINES = ["gcn_1l", "gat_2l", "sage_no_spatial", "sage_no_sequential"]
_ALL_BASELINES = ["random", "degree"] + _GNN_BASELINES


# ---------------------------------------------------------------------------
# Non-training baselines (fast)
# ---------------------------------------------------------------------------

def run_and_save_random(out_dir: Path) -> None:
    out_path = out_dir / "random_manifest.json"
    if out_path.exists():
        print("[skip] random — manifest exists", flush=True)
        return
    print("\n[running] random baseline ...", flush=True)
    # Use all 4 validation folds, pooled
    all_val: list[Any] = []
    for fold in FOLDS:
        all_val.extend(load_split(GRAPH_DIR, SPLIT_MANIFEST, "val", val_fold=fold))
    result = run_random_baseline(all_val, seeds=(0, 1, 2))
    out_path.write_text(json.dumps(result, indent=2))
    agg = result["aggregate"]
    print(f"  [done] random  macro_auprc_mean={agg.get('macro_auprc_mean', 'N/A'):.4f}", flush=True)


def run_and_save_degree(out_dir: Path) -> None:
    out_path = out_dir / "degree_manifest.json"
    if out_path.exists():
        print("[skip] degree — manifest exists", flush=True)
        return
    print("\n[running] degree baseline ...", flush=True)
    all_val: list[Any] = []
    for fold in FOLDS:
        all_val.extend(load_split(GRAPH_DIR, SPLIT_MANIFEST, "val", val_fold=fold))
    result = run_degree_baseline(all_val)
    out_path.write_text(json.dumps(result, indent=2))
    m = result["metrics"]
    print(f"  [done] degree  macro_auprc={m.get('macro_auprc', 'N/A'):.4f}", flush=True)


# ---------------------------------------------------------------------------
# GNN-based baselines (training required)
# ---------------------------------------------------------------------------

def _run_gnn_baseline(
    name: str,
    model_factory,        # callable(seed) -> nn.Module
    folds: list[int],
    seeds: list[int],
    out_dir: Path,
    edge_type_filter: int | None = None,
    hidden_dim: int = 128,
    max_epochs: int = 100,
    patience: int = 10,
) -> None:
    """Run one GNN baseline across folds and seeds, saving per-run manifests."""
    from phase3_evaluation.metrics import aggregate_seeds

    summary_path = out_dir / f"{name}_manifest.json"
    if summary_path.exists():
        print(f"[skip] {name} — summary manifest exists", flush=True)
        return

    print(f"\n[running] {name} baseline  ({len(folds)} folds x {len(seeds)} seeds) ...", flush=True)
    t_total = time.time()
    all_seed_results: list[dict] = []
    per_fold_per_seed: list[dict] = []

    for fold in folds:
        fold_results = []
        for seed in seeds:
            run_path = out_dir / f"{name}_fold{fold}_seed{seed}_manifest.json"
            if run_path.exists():
                print(f"  [skip] fold={fold} seed={seed}", flush=True)
                with open(run_path) as f:
                    run_m = json.load(f)
            else:
                print(f"  [train] fold={fold} seed={seed} ...", end=" ", flush=True)
                train_data = load_split(GRAPH_DIR, SPLIT_MANIFEST, "train", val_fold=fold)
                val_data = load_split(GRAPH_DIR, SPLIT_MANIFEST, "val", val_fold=fold)
                pos_weight = compute_pos_weight(train_data)

                import torch
                model = model_factory(seed)
                run_m = train_baseline_gnn(
                    model=model,
                    train_data=train_data,
                    val_data=val_data,
                    pos_weight=pos_weight,
                    seed=seed,
                    max_epochs=max_epochs,
                    patience=patience,
                    edge_type_filter=edge_type_filter,
                    verbose=False,
                )
                run_m.update({
                    "baseline_name": name,
                    "val_fold": fold,
                    "n_train": len(train_data),
                    "n_val": len(val_data),
                    "pos_weight": round(float(pos_weight), 4),
                    "split_manifest_hash_prefix": "24dd5e347d880108",
                    "governance": "docs/scientific_governance/10_BASELINE_REQUIREMENTS.md",
                })
                run_path.write_text(json.dumps(run_m, indent=2))
                print(f"val_macro_auprc={run_m['best_val_macro_auprc']:.4f}  ({run_m['elapsed_seconds']:.0f}s)", flush=True)

            all_seed_results.append(run_m["final_metrics"])
            fold_results.append(run_m)
            per_fold_per_seed.append({
                "fold": fold, "seed": seed,
                "best_val_macro_auprc": run_m["best_val_macro_auprc"],
                "best_epoch": run_m["best_epoch"],
                "epochs_run": run_m["epochs_run"],
            })

    aggregate = aggregate_seeds(all_seed_results)

    per_fold_means: dict[int, float] = {}
    for fold in folds:
        fold_auprcs = [
            r["best_val_macro_auprc"] for r in per_fold_per_seed if r["fold"] == fold
        ]
        per_fold_means[fold] = sum(fold_auprcs) / len(fold_auprcs) if fold_auprcs else float("nan")

    summary = {
        "baseline_name": name,
        "folds": folds,
        "seeds": seeds,
        "per_fold_per_seed": per_fold_per_seed,
        "per_fold_mean_macro_auprc": per_fold_means,
        "aggregate": aggregate,
        "overall_macro_auprc_mean": aggregate.get("macro_auprc_mean"),
        "overall_macro_auprc_sd": aggregate.get("macro_auprc_sd"),
        "total_elapsed_seconds": round(time.time() - t_total, 1),
        "split_manifest_hash_prefix": "24dd5e347d880108",
        "governance": [
            "docs/scientific_governance/10_BASELINE_REQUIREMENTS.md",
            "docs/scientific_governance/09_EVALUATION_PROTOCOL.md",
        ],
        "gate": "reports/phase3/baseline_gate3_authorization_20260529.md",
        "no_test_set_evaluation": True,
        "no_scientific_claims": True,
    }
    summary_path.write_text(json.dumps(summary, indent=2))
    print(
        f"  [done] {name}  macro_auprc={aggregate.get('macro_auprc_mean', float('nan')):.4f}"
        f" ± {aggregate.get('macro_auprc_sd', float('nan')):.4f}",
        flush=True,
    )


def run_gcn1l(folds: list[int], seeds: list[int], out_dir: Path) -> None:
    def factory(seed: int):
        return GCN1L(hidden_dim=128)
    _run_gnn_baseline("gcn_1l", factory, folds, seeds, out_dir)


def run_gat2l(folds: list[int], seeds: list[int], out_dir: Path) -> None:
    def factory(seed: int):
        return GAT2L(hidden_dim=128, heads=4)
    _run_gnn_baseline("gat_2l", factory, folds, seeds, out_dir)


def run_sage_no_spatial(folds: list[int], seeds: list[int], out_dir: Path) -> None:
    """GraphSAGE-3L ablation: sequential edges only (spatial edges removed)."""
    def factory(seed: int):
        return GraphSAGE3L(hidden_dim=128, dropout=0.1)
    _run_gnn_baseline(
        "sage_no_spatial", factory, folds, seeds, out_dir,
        edge_type_filter=EDGE_TYPE_SEQUENTIAL,
    )


def run_sage_no_sequential(folds: list[int], seeds: list[int], out_dir: Path) -> None:
    """GraphSAGE-3L ablation: spatial edges only (sequential edges removed)."""
    def factory(seed: int):
        return GraphSAGE3L(hidden_dim=128, dropout=0.1)
    _run_gnn_baseline(
        "sage_no_sequential", factory, folds, seeds, out_dir,
        edge_type_filter=EDGE_TYPE_SPATIAL,
    )


# ---------------------------------------------------------------------------
# External tool stubs
# ---------------------------------------------------------------------------

def write_external_stubs(out_dir: Path) -> None:
    """Write stub manifests for external baselines that require tool installation."""
    stubs = {
        "fpocket": {
            "baseline_name": "fpocket",
            "status": "NOT_RUN",
            "reason": "fpocket requires a separate binary installation (not available on this Windows system).",
            "installation_note": "Download from https://fpocket.sourceforge.net/ or compile from source. Run fpocket on each structure, parse output, align predictions to residues, compute metrics.",
            "script": "scripts/run_fpocket.py (to be created after installation)",
            "governance": "docs/scientific_governance/10_BASELINE_REQUIREMENTS.md",
        },
        "p2rank": {
            "baseline_name": "p2rank",
            "status": "NOT_RUN",
            "reason": "P2Rank requires Java and the P2Rank distribution (not available on this system).",
            "installation_note": "Download from https://github.com/rdk/p2rank/releases. Run prank predict on each structure, align predictions to residues, compute metrics.",
            "script": "scripts/run_p2rank.py (to be created after installation)",
            "governance": "docs/scientific_governance/10_BASELINE_REQUIREMENTS.md",
        },
        "pocketminer": {
            "baseline_name": "pocketminer",
            "status": "NOT_RUN",
            "reason": "PocketMiner requires downloading the model weights and dependencies.",
            "installation_note": "Install from https://github.com/Mickdub/gvp (or the PocketMiner repo). Run inference on each structure, align per-residue scores, compute metrics on frozen split.",
            "script": "scripts/run_pocketminer.py (to be created after installation)",
            "governance": "docs/scientific_governance/10_BASELINE_REQUIREMENTS.md",
        },
    }
    for name, stub in stubs.items():
        path = out_dir / f"{name}_manifest.json"
        if not path.exists():
            path.write_text(json.dumps(stub, indent=2))
            print(f"[stub] {name} — written (tool not installed)", flush=True)
        else:
            print(f"[skip] {name} — manifest exists", flush=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--only", nargs="+", choices=_ALL_BASELINES,
        help="Run only these baselines (default: all).",
    )
    p.add_argument("--folds", nargs="+", type=int, default=FOLDS)
    p.add_argument("--seeds", nargs="+", type=int, default=SEEDS)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    targets: list[str] = args.only if args.only else _ALL_BASELINES

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\nBaseline runner — GATE 3 record: {GATE3_RECORD}", flush=True)
    if not GATE3_RECORD.is_file():
        print("ERROR: GATE 3 authorization record not found. Aborting.", file=sys.stderr)
        return 2

    t0 = time.time()

    if "random" in targets:
        run_and_save_random(OUT_DIR)

    if "degree" in targets:
        run_and_save_degree(OUT_DIR)

    if "gcn_1l" in targets:
        run_gcn1l(args.folds, args.seeds, OUT_DIR)

    if "gat_2l" in targets:
        run_gat2l(args.folds, args.seeds, OUT_DIR)

    if "sage_no_spatial" in targets:
        run_sage_no_spatial(args.folds, args.seeds, OUT_DIR)

    if "sage_no_sequential" in targets:
        run_sage_no_sequential(args.folds, args.seeds, OUT_DIR)

    write_external_stubs(OUT_DIR)

    elapsed = (time.time() - t0) / 60
    print(f"\nAll baselines complete. Total elapsed: {elapsed:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
