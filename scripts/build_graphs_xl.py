"""
Build XL graph .pt files: hand-crafted features + ESM2 embeddings.

Reads ESM2 .npy files from data/esm_features/ (produced by build_esm_features.py).
Saves XL graphs to:
  data/graphs_xl/{PDB_ID}.pt  — CryptoSite structures
  data/pcna_xl/{PDB_ID}.pt    — PCNA core structures

Usage:
    python scripts/build_graphs_xl.py
    python scripts/build_graphs_xl.py --ids 8GLA 1W60
    python scripts/build_graphs_xl.py --force
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.data_processing.parse_pdb import parse_pdb, get_ligand_coords, label_pocket_residues
from src.data_processing.graph_construction import build_graph_xl, save_graph

PROC_DIR    = REPO_ROOT / "data" / "processed"
RAW_DIR     = REPO_ROOT / "data" / "raw"
ESM_DIR     = REPO_ROOT / "data" / "esm_features"
GRAPH_XL    = REPO_ROOT / "data" / "graphs_xl"
PCNA_XL     = REPO_ROOT / "data" / "pcna_xl"

_PCNA_LIGANDS = {"8GLA": "ZQZ"}
_PCNA_IDS     = {"1W60", "8GLA", "1AXC"}  # 1W61 removed — proline racemase, not PCNA


def build_one(pdb_path: Path, out_dir: Path, cutoff: float = 8.0) -> bool:
    pdb_id   = pdb_path.stem.replace("_clean", "").upper()
    out_path = out_dir / f"{pdb_id}.pt"

    if out_path.exists():
        print(f"  -- {pdb_id:<8} already exists, skipping")
        return True

    try:
        residues = parse_pdb(pdb_path)
    except Exception as e:
        print(f"  ERR {pdb_id:<8} parse_pdb: {e}")
        return False

    if not residues:
        print(f"  ERR {pdb_id:<8} no residues")
        return False

    # Load ESM2 features
    esm_path = ESM_DIR / f"{pdb_id}.npy"
    if esm_path.exists():
        esm_feats = np.load(str(esm_path))
    else:
        print(f"  WARN {pdb_id:<8} no ESM features at {esm_path} — using 40-dim only")
        esm_feats = None

    # Labels
    labels = None
    ligand_resname = _PCNA_LIGANDS.get(pdb_id)
    raw_path   = RAW_DIR / pdb_path.name.replace("_clean", "")
    lig_source = raw_path if raw_path.exists() else pdb_path
    lig_coords = get_ligand_coords(lig_source, resname=ligand_resname)
    if lig_coords is not None:
        labels   = label_pocket_residues(residues, lig_coords, cutoff_angstrom=6.0)
        lig_info = f"ligand: {labels.mean():.1%} positive"
    else:
        lig_info = "no ligand (apo)"

    try:
        data = build_graph_xl(residues, esm_features=esm_feats,
                              labels=labels, distance_cutoff=cutoff)
    except Exception as e:
        print(f"  ERR {pdb_id:<8} build_graph_xl: {e}")
        return False

    out_dir.mkdir(parents=True, exist_ok=True)
    save_graph(data, str(out_path))

    esm_info = f"ESM={esm_feats.shape[1]}d" if esm_feats is not None else "no-ESM"
    print(f"  OK  {pdb_id:<8}  N={data.x.shape[0]:>4}  "
          f"feat={data.x.shape[1]}  {esm_info}  {lig_info}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build XL graphs (hand-crafted + ESM2 features)")
    parser.add_argument("--pdb-dir", type=Path, default=PROC_DIR)
    parser.add_argument("--ids",     nargs="+", metavar="PDB_ID")
    parser.add_argument("--cutoff",  type=float, default=8.0)
    parser.add_argument("--force",   action="store_true")
    args = parser.parse_args()

    pdb_files = sorted(args.pdb_dir.glob("*.pdb"))
    if args.ids:
        id_set    = {i.upper() for i in args.ids}
        pdb_files = [p for p in pdb_files
                     if p.stem.replace("_clean","").upper() in id_set]

    if args.force:
        for p in pdb_files:
            pdb_id = p.stem.replace("_clean","").upper()
            for d in (GRAPH_XL, PCNA_XL):
                f = d / f"{pdb_id}.pt"
                if f.exists():
                    f.unlink()

    print(f"Building XL graphs for {len(pdb_files)} structures ...\n")
    ok = failed = 0
    for pdb_path in pdb_files:
        pdb_id  = pdb_path.stem.replace("_clean","").upper()
        out_dir = PCNA_XL if pdb_id in _PCNA_IDS else GRAPH_XL
        if build_one(pdb_path, out_dir, args.cutoff):
            ok += 1
        else:
            failed += 1

    print(f"\nDone. OK={ok}  Failed={failed}")
    print(f"Graphs  -> {GRAPH_XL}")
    print(f"PCNA XL -> {PCNA_XL}")
    print("\nNext:")
    print("  python scripts/make_split.py --graph-dir data/graphs_xl "
          "--val-frac 0.15 --test-frac 0.10 --force")
    print("  (then retrain with --model_size xl)")


if __name__ == "__main__":
    main()
