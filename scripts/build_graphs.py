"""
Build PyG graph .pt files from processed PDB structures.

For each PDB in data/processed/:
  1. parse_pdb → list[Residue]
  2. get_ligand_coords → ligand atoms (if present)
  3. label_pocket_residues → binary labels (N,)
  4. build_graph → PyG Data
  5. save to data/graphs/{PDB_ID}.pt

Special handling:
  - 8GLA: AOH1996 ligand (resname AOH) → pocket labels
  - 1W60: apo structure, no ligand → labels = all zeros (inference target)
  - CryptoSite proteins: auto-detect first drug-like ligand → pocket labels
  - Structures with no ligand: labels = all zeros (still useful as negatives)

Usage:
    python scripts/build_graphs.py
    python scripts/build_graphs.py --pdb-dir data/processed --out-dir data/graphs
    python scripts/build_graphs.py --ids 1W60 8GLA        # specific structures
    python scripts/build_graphs.py --cutoff 8.0           # edge distance cutoff
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.data_processing.parse_pdb import parse_pdb, get_ligand_coords, label_pocket_residues
from src.data_processing.graph_construction import build_graph_v2, save_graph

PDB_DIR   = REPO_ROOT / "data" / "processed"
RAW_DIR   = REPO_ROOT / "data" / "raw"
GRAPH_DIR = REPO_ROOT / "data" / "graphs"
PCNA_DIR  = REPO_ROOT / "data" / "pcna"

# Ground-truth PCNA structures — explicit ligand resname
_PCNA_LIGANDS = {
    "8GLA": "ZQZ",   # AOH1996 derivative (CCD code ZQZ)
}

# Structures to route to data/pcna/ instead of data/graphs/
_PCNA_IDS = {"1W60", "8GLA", "1AXC"}  # 1W61 removed — proline racemase, not PCNA


def build_one(pdb_path: Path, out_dir: Path, cutoff: float = 8.0) -> bool:
    """
    Build and save one graph. Returns True on success.
    """
    pdb_id   = pdb_path.stem.replace("_clean", "").upper()
    out_path = out_dir / f"{pdb_id}.pt"

    if out_path.exists():
        print(f"  -- {pdb_id:<8} already exists, skipping")
        return True

    try:
        residues = parse_pdb(pdb_path)
    except Exception as e:
        print(f"  ERR {pdb_id:<8} parse_pdb failed: {e}")
        return False

    if not residues:
        print(f"  ERR {pdb_id:<8} no residues parsed")
        return False

    # Extract ligand coords for labeling — prefer raw PDB (has HETATM)
    labels = None
    ligand_resname = _PCNA_LIGANDS.get(pdb_id)
    raw_path = RAW_DIR / pdb_path.name.replace("_clean", "")
    lig_source = raw_path if raw_path.exists() else pdb_path

    lig_coords = get_ligand_coords(lig_source, resname=ligand_resname)
    if lig_coords is not None:
        labels = label_pocket_residues(residues, lig_coords, cutoff_angstrom=6.0)
        pos_frac = labels.mean()
        lig_info = f"ligand: {pos_frac:.1%} positive"
    else:
        import numpy as np
        labels = None   # no labels for apo / unlabeled structures
        lig_info = "no ligand (apo)"

    try:
        data = build_graph_v2(residues, labels=labels, distance_cutoff=cutoff)
    except Exception as e:
        print(f"  ERR {pdb_id:<8} build_graph failed: {e}")
        return False

    out_dir.mkdir(parents=True, exist_ok=True)
    save_graph(data, str(out_path))

    n_nodes = data.x.shape[0]
    n_edges = data.edge_index.shape[1]
    print(f"  OK  {pdb_id:<8} N={n_nodes:>4}  E={n_edges:>5}  {lig_info}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build PyG graph files from processed PDB structures")
    parser.add_argument("--pdb-dir", type=Path, default=PDB_DIR)
    parser.add_argument("--out-dir", type=Path, default=GRAPH_DIR)
    parser.add_argument("--ids",     nargs="+", metavar="PDB_ID",
                        help="Only process specific PDB IDs")
    parser.add_argument("--cutoff",  type=float, default=8.0,
                        help="Cα–Cα edge distance cutoff in Å (default 8.0)")
    parser.add_argument("--force",   action="store_true",
                        help="Overwrite existing .pt files")
    args = parser.parse_args()

    pdb_files = sorted(args.pdb_dir.glob("*.pdb"))
    if not pdb_files:
        print(f"No PDB files found in {args.pdb_dir}")
        print("Run: python -m src.data_processing.fetch_structures --cryptosite --strip")
        return

    # Filter to requested IDs if given
    if args.ids:
        id_set = {i.upper() for i in args.ids}
        pdb_files = [p for p in pdb_files
                     if p.stem.replace("_clean", "").upper() in id_set]

    if args.force:
        for p in pdb_files:
            pdb_id = p.stem.replace("_clean", "").upper()
            out = args.out_dir / f"{pdb_id}.pt"
            if out.exists():
                out.unlink()
        for pdb_id in _PCNA_IDS:
            p = PCNA_DIR / f"{pdb_id}.pt"
            if p.exists():
                p.unlink()

    ok = failed = 0
    print(f"Building graphs for {len(pdb_files)} structures "
          f"(cutoff={args.cutoff}A) ...\n")

    for pdb_path in pdb_files:
        pdb_id = pdb_path.stem.replace("_clean", "").upper()
        out_dir = PCNA_DIR if pdb_id in _PCNA_IDS else args.out_dir
        success = build_one(pdb_path, out_dir, cutoff=args.cutoff)
        if success:
            ok += 1
        else:
            failed += 1

    print(f"\nDone. OK={ok}  Failed={failed}")
    print(f"Graphs -> {args.out_dir}")
    print(f"PCNA   -> {PCNA_DIR}")
    print("\nNext: python scripts/make_split.py")


if __name__ == "__main__":
    main()
