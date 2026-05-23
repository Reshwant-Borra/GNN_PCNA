"""Create a homology-clean CryptoSite split with MMseqs2 clustering.

This script clusters chain-level PDB sequences at 30 percent sequence identity,
collapses chain clusters into structure-level connected components, and splits
components so no homologous component can appear in more than one split.
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import torch

AA3 = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
    "MSE": "M", "HSD": "H", "HSE": "H", "HSP": "H", "SEC": "C",
    "PYL": "K",
}

PCNA_IDS = {"1W60", "8GLA", "1AXC"}


class UnionFind:
    """Minimal disjoint-set structure for structure-level components."""

    def __init__(self, items: list[str]) -> None:
        self.parent = {item: item for item in items}

    def find(self, item: str) -> str:
        parent = self.parent[item]
        if parent != item:
            self.parent[item] = self.find(parent)
        return self.parent[item]

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def _has_labels(pt_path: Path) -> bool:
    """Return True when a graph has a non-empty label vector."""
    data = torch.load(str(pt_path), weights_only=False)
    return hasattr(data, "y") and data.y is not None and int(data.y.numel()) > 0


def _labeled_structure_ids(graph_dir: Path) -> list[str]:
    """List labeled non-PCNA structures available as PyG graph files."""
    ids: list[str] = []
    for path in sorted(graph_dir.glob("*.pt")):
        pdb_id = path.stem.upper()
        if pdb_id in PCNA_IDS:
            continue
        if _has_labels(path):
            ids.append(pdb_id)
    return ids


def extract_chain_sequences(pdb_path: Path) -> dict[str, str]:
    """Extract one-letter protein sequences from CA atoms in each PDB chain."""
    chains: dict[str, list[str]] = defaultdict(list)
    seen: set[tuple[str, str, str]] = set()
    for line in pdb_path.read_text(errors="ignore").splitlines():
        if not line.startswith("ATOM") or line[12:16].strip() != "CA":
            continue
        chain = line[21].strip() or "_"
        resid = line[22:27].strip()
        icode = line[26].strip()
        resname = line[17:20].strip()
        key = (chain, resid, icode)
        if key in seen:
            continue
        seen.add(key)
        aa = AA3.get(resname)
        if aa:
            chains[chain].append(aa)
    return {chain: "".join(seq) for chain, seq in chains.items() if seq}


def write_fasta(ids: list[str], raw_dir: Path, out_path: Path) -> dict[str, str]:
    """Write chain-level FASTA records and return header-to-structure mapping."""
    header_to_structure: dict[str, str] = {}
    with out_path.open("w", encoding="utf-8") as fh:
        for pdb_id in ids:
            chains = extract_chain_sequences(raw_dir / f"{pdb_id}.pdb")
            if not chains:
                raise RuntimeError(f"No protein sequence extracted for {pdb_id}")
            for chain, seq in sorted(chains.items()):
                header = f"{pdb_id}__{chain}"
                header_to_structure[header] = pdb_id
                fh.write(f">{header}\n")
                for i in range(0, len(seq), 80):
                    fh.write(seq[i:i + 80] + "\n")
    return header_to_structure


def find_mmseqs(explicit: Path | None = None) -> str:
    """Find MMseqs2 from an explicit path, PATH, or the bundled tools directory."""
    candidates: list[Path] = []
    if explicit:
        candidates.append(explicit)
    bundled = REPO / "tools" / "mmseqs-win64" / "mmseqs" / "mmseqs.bat"
    bundled_exe = REPO / "tools" / "mmseqs-win64" / "mmseqs" / "bin" / "mmseqs.exe"
    candidates.extend([bundled, bundled_exe])
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    found = shutil.which("mmseqs")
    if found:
        return found
    raise RuntimeError(
        "MMseqs2 is required for homology-clean splitting. Install mmseqs, "
        "place the official Windows binary under tools/mmseqs-win64/, or pass --mmseqs."
    )


def run_mmseqs(fasta: Path, work_dir: Path, min_seq_id: float,
               mmseqs_bin: Path | None = None) -> Path:
    """Run MMseqs2 easy-cluster and return the cluster TSV path."""
    mmseqs = find_mmseqs(mmseqs_bin)
    prefix = work_dir / "cryptosite_homology30"
    tmp = work_dir / "tmp"
    cmd = [
        mmseqs,
        "easy-cluster",
        str(fasta),
        str(prefix),
        str(tmp),
        "--min-seq-id",
        str(min_seq_id),
    ]
    subprocess.run(cmd, check=True)
    tsv = work_dir / "cryptosite_homology30_cluster.tsv"
    if not tsv.exists():
        raise FileNotFoundError(f"MMseqs2 did not create expected cluster TSV: {tsv}")
    return tsv


def read_clusters(tsv_path: Path) -> dict[str, list[str]]:
    """Read MMseqs2 representative/member cluster assignments."""
    clusters: dict[str, list[str]] = defaultdict(list)
    for line in tsv_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rep, member = line.split("\t")[:2]
        clusters[rep].append(member)
    return dict(clusters)


def build_components(ids: list[str], clusters: dict[str, list[str]],
                     header_to_structure: dict[str, str]) -> tuple[dict[str, list[str]], dict[str, str]]:
    """Collapse chain-level sequence clusters into structure-level components."""
    uf = UnionFind(ids)
    for members in clusters.values():
        structures = sorted({header_to_structure[m] for m in members if m in header_to_structure})
        if len(structures) < 2:
            continue
        first = structures[0]
        for other in structures[1:]:
            uf.union(first, other)

    grouped: dict[str, list[str]] = defaultdict(list)
    for pdb_id in ids:
        grouped[uf.find(pdb_id)].append(pdb_id)

    components: dict[str, list[str]] = {}
    component_of: dict[str, str] = {}
    for idx, members in enumerate(sorted(grouped.values(), key=lambda xs: (len(xs), xs), reverse=True)):
        cid = f"comp_{idx:04d}"
        components[cid] = sorted(members)
        for pdb_id in members:
            component_of[pdb_id] = cid
    return components, component_of


def split_components(components: dict[str, list[str]], seed: int,
                     val_frac: float, test_frac: float) -> dict[str, list[str]]:
    """Assign whole components to train/val/test splits."""
    rng = random.Random(seed)
    items = list(components.items())
    rng.shuffle(items)

    total = sum(len(v) for _, v in items)
    targets = {
        "test": max(1, round(total * test_frac)),
        "val": max(1, round(total * val_frac)),
    }
    assignments = {"train": [], "val": [], "test": []}

    for cid, members in items:
        if len(assignments["test"]) < targets["test"]:
            split = "test"
        elif len(assignments["val"]) < targets["val"]:
            split = "val"
        else:
            split = "train"
        assignments[split].extend(members)

    return {name: sorted(ids) for name, ids in assignments.items()}


def make_audit(splits: dict[str, list[str]], components: dict[str, list[str]],
               component_of: dict[str, str], clusters: dict[str, list[str]],
               header_to_structure: dict[str, str], threshold: float) -> dict:
    """Build an audit proving there is no component or sequence-cluster overlap."""
    split_of = {pdb_id: split for split, ids in splits.items() for pdb_id in ids}
    component_splits: dict[str, set[str]] = defaultdict(set)
    for pdb_id, cid in component_of.items():
        component_splits[cid].add(split_of[pdb_id])
    component_overlaps = {
        cid: sorted(parts) for cid, parts in component_splits.items() if len(parts) > 1
    }

    cluster_overlaps = {}
    for rep, members in clusters.items():
        struct_splits = {
            split_of[header_to_structure[m]]
            for m in members
            if m in header_to_structure and header_to_structure[m] in split_of
        }
        if len(struct_splits) > 1:
            cluster_overlaps[rep] = sorted(struct_splits)

    leakage_detected = bool(component_overlaps or cluster_overlaps)
    return {
        "created_at": datetime.utcnow().isoformat() + "Z",
        "backend": "mmseqs2 easy-cluster",
        "identity_threshold": threshold,
        "n_structures": sum(len(v) for v in splits.values()),
        "split_counts": {k: len(v) for k, v in splits.items()},
        "n_components": len(components),
        "component_overlaps": component_overlaps,
        "sequence_cluster_overlaps": cluster_overlaps,
        "train_to_val_test_cluster_overlap_count": len(cluster_overlaps),
        "leakage_detected": leakage_detected,
        "verdict": "PASS" if not leakage_detected else "FAIL",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create MMseqs2 homology-clean CryptoSite split")
    parser.add_argument("--graph-dir", type=Path, default=REPO / "data" / "graphs")
    parser.add_argument("--raw-dir", type=Path, default=REPO / "data" / "raw")
    parser.add_argument("--out", type=Path, default=REPO / "data" / "splits" / "cryptosite_homology30_split.json")
    parser.add_argument("--audit", type=Path, default=REPO / "data" / "results" / "homology30_audit.json")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--val-frac", type=float, default=0.10)
    parser.add_argument("--test-frac", type=float, default=0.10)
    parser.add_argument("--min-seq-id", type=float, default=0.30)
    parser.add_argument("--keep-work", type=Path, default=None)
    parser.add_argument("--mmseqs", type=Path, default=None,
                        help="Optional path to mmseqs executable or mmseqs.bat wrapper")
    args = parser.parse_args()

    ids = _labeled_structure_ids(args.graph_dir)
    if not ids:
        raise RuntimeError(f"No labeled graphs found in {args.graph_dir}")

    with tempfile.TemporaryDirectory() as tmp_name:
        work_dir = args.keep_work or Path(tmp_name)
        work_dir.mkdir(parents=True, exist_ok=True)
        fasta = work_dir / "cryptosite_chains.fasta"
        header_to_structure = write_fasta(ids, args.raw_dir, fasta)
        cluster_tsv = run_mmseqs(fasta, work_dir, args.min_seq_id, args.mmseqs)
        clusters = read_clusters(cluster_tsv)
        components, component_of = build_components(ids, clusters, header_to_structure)
        splits = split_components(components, args.seed, args.val_frac, args.test_frac)
        audit = make_audit(
            splits, components, component_of, clusters, header_to_structure, args.min_seq_id
        )

        if audit["leakage_detected"]:
            args.audit.parent.mkdir(parents=True, exist_ok=True)
            args.audit.write_text(json.dumps(audit, indent=2), encoding="utf-8")
            raise RuntimeError(f"Homology leakage detected; audit written to {args.audit}")

        manifest = {
            "seed": args.seed,
            "val_frac": args.val_frac,
            "test_frac": args.test_frac,
            "homology_backend": "mmseqs2 easy-cluster",
            "identity_threshold": args.min_seq_id,
            "graph_dir": str(args.graph_dir),
            "splits": splits,
            "components": components,
            "component_of": component_of,
        }

        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.audit.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        args.audit.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    print(f"Split written: {args.out.relative_to(REPO)}")
    print(f"Audit written: {args.audit.relative_to(REPO)}")
    print(f"Verdict: {audit['verdict']} ({audit['n_components']} components)")


if __name__ == "__main__":
    main()
