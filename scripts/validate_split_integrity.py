"""Validate split, graph, and label integrity before training or evaluation."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import torch


def display_path(path: Path) -> str:
    """Return a readable repo-relative path when possible."""
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    """Return the SHA256 digest for one file."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_split(path: Path) -> dict[str, list[str]]:
    """Load split lists from a manifest."""
    manifest = json.loads(path.read_text(encoding="utf-8"))
    splits = manifest.get("splits")
    if not isinstance(splits, dict):
        raise ValueError(f"{path} does not contain a 'splits' object")
    for name in ("train", "val", "test"):
        if name not in splits:
            raise ValueError(f"{path} is missing split '{name}'")
    return {name: [str(x).upper() for x in splits[name]] for name in ("train", "val", "test")}


def validate(split_path: Path, graph_dir: Path, feature_dim: int,
             min_positive: int = 5) -> dict:
    """Validate one split manifest against a graph directory."""
    splits = load_split(split_path)
    seen: dict[str, str] = {}
    errors: list[str] = []
    warnings: list[str] = []
    per_structure: list[dict] = []
    graph_hash = hashlib.sha256()

    for split, ids in splits.items():
        for pdb_id in ids:
            if pdb_id in seen:
                errors.append(f"{pdb_id} appears in both {seen[pdb_id]} and {split}")
            seen[pdb_id] = split

            path = graph_dir / f"{pdb_id}.pt"
            if not path.exists():
                errors.append(f"{pdb_id}: missing graph {path}")
                continue

            digest = sha256_file(path)
            graph_hash.update(split.encode("utf-8"))
            graph_hash.update(pdb_id.encode("utf-8"))
            graph_hash.update(digest.encode("ascii"))

            try:
                data = torch.load(str(path), weights_only=False)
            except Exception as exc:
                errors.append(f"{pdb_id}: graph load failed: {exc}")
                continue

            n_nodes = int(data.x.shape[0]) if hasattr(data, "x") else 0
            node_dim = int(data.x.shape[1]) if hasattr(data, "x") and data.x.ndim == 2 else None
            if n_nodes <= 0:
                errors.append(f"{pdb_id}: empty residue/node set")
            if node_dim != feature_dim:
                errors.append(f"{pdb_id}: node feature dim {node_dim}, expected {feature_dim}")

            y = getattr(data, "y", None)
            if y is None:
                errors.append(f"{pdb_id}: missing label vector y")
                n_positive = 0
                positive_fraction = 0.0
            else:
                if int(y.numel()) != n_nodes:
                    errors.append(f"{pdb_id}: label length {int(y.numel())}, node count {n_nodes}")
                n_positive = int(y.float().sum().item())
                positive_fraction = float(y.float().mean().item()) if y.numel() else 0.0

            degenerate = n_positive < min_positive
            if degenerate:
                warnings.append(f"{pdb_id}: degenerate_labels ({n_positive} positives)")

            per_structure.append({
                "pdb_id": pdb_id,
                "split": split,
                "graph": str(path),
                "sha256": digest,
                "n_nodes": n_nodes,
                "node_dim": node_dim,
                "n_positive": n_positive,
                "positive_fraction": positive_fraction,
                "degenerate_labels": degenerate,
            })

    return {
        "created_at": datetime.utcnow().isoformat() + "Z",
        "split_file": str(split_path),
        "graph_dir": str(graph_dir),
        "expected_feature_dim": feature_dim,
        "min_positive": min_positive,
        "split_counts": {name: len(ids) for name, ids in splits.items()},
        "graph_manifest_hash": graph_hash.hexdigest(),
        "errors": errors,
        "warnings": warnings,
        "degenerate_structures": [
            r["pdb_id"] for r in per_structure if r["degenerate_labels"]
        ],
        "per_structure": per_structure,
        "ok": not errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate split graph and label integrity")
    parser.add_argument("--split", type=Path, default=REPO / "data" / "splits" / "cryptosite_homology30_split.json")
    parser.add_argument("--graph-dir", type=Path, default=REPO / "data" / "graphs")
    parser.add_argument("--feature-dim", type=int, required=True,
                        help="Expected node feature dimension; use 40 for geometry, 520 for XL")
    parser.add_argument("--min-positive", type=int, default=5)
    parser.add_argument("--out", type=Path, default=REPO / "data" / "results" / "split_integrity.json")
    args = parser.parse_args()

    result = validate(args.split, args.graph_dir, args.feature_dim, args.min_positive)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"Integrity report: {display_path(args.out)}")
    print(f"Graph manifest hash: {result['graph_manifest_hash']}")
    print(f"Degenerate structures: {len(result['degenerate_structures'])}")
    if not result["ok"]:
        for err in result["errors"]:
            print(f"ERROR: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
