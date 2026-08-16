"""CLI for Phase 3 governed graph generation.

Usage (from workspace root, with PYTHONPATH=src):

  python -m phase3_graphs.cli [--split all|train|validation|test]
                               [--root .]
                               [--out-dir data/graphs]
                               [--limit N]

Generates graph artifacts (.npz arrays + JSON metadata sidecar) and emits a
collection-level graph release manifest. Status is always PENDING_HUMAN_REVIEW.
Real training remains blocked until the manifest is reviewed by a human and a
separate first-training approval is recorded.

Governance: docs/scientific_governance/26_HUMAN_REVIEW_GATES.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np

from phase3_data.errors import Phase3DataError
from phase3_data.hashing import sha256_json
from phase3_data.index import build_dataset_index
from phase3_data.io import write_json
from phase3_data.manifests import validate_governed_inputs
from phase3_data.models import Phase3Paths
from phase3_graphs import constants
from phase3_graphs.builder import GraphResult, build_graph
from phase3_graphs.features import FEATURE_DIM
from phase3_graphs.manifest import (
    build_graph_release_manifest,
    feature_definition_hash,
    policy_hash,
)


def save_graph(result: GraphResult, out_dir: Path) -> dict[str, str]:
    """Serialize graph arrays (.npz) and metadata sidecar (.json). Return paths."""
    npz_path = out_dir / f"{result.structure_id}.npz"
    np.savez_compressed(
        str(npz_path),
        node_features=result.node_features,
        node_labels=result.node_labels,
        loss_mask=result.loss_mask,
        edge_index=result.edge_index,
        edge_type=result.edge_type,
        edge_distance=result.edge_distance,
    )
    meta_path = out_dir / f"{result.structure_id}_meta.json"
    write_json(meta_path, {
        "structure_id": result.structure_id,
        "NO_TRAINING_PERFORMED": True,
        "node_metadata": result.node_metadata,
        "manifest_entry": result.manifest_entry,
    })
    return {"npz": str(npz_path), "meta": str(meta_path)}


def run_graph_generation(
    root: Path,
    requested_split: str,
    out_dir: Path,
    limit: int | None = None,
    quiet: bool = False,
) -> dict[str, Any]:
    """Generate all graphs for the requested split. Returns a summary dict."""
    paths = Phase3Paths(root=root)

    # Validate governed inputs (split hash, label counts, exclusions, PCNA cluster)
    summary = validate_governed_inputs(paths)
    if not summary["frozen_split_hash"].startswith("24dd5e347d880108"):
        raise Phase3DataError(
            f"Split manifest hash mismatch: {summary['frozen_split_hash']}"
        )

    policy_h = policy_hash(root)
    feature_h = feature_definition_hash()

    index = build_dataset_index(paths, requested_split=requested_split, require_cif=True)
    if limit is not None:
        index = index[:limit]

    if not quiet:
        print(
            f"[phase3_graphs] Generating {len(index)} graphs "
            f"(split={requested_split}, cutoff={constants.CA_CUTOFF_ANGSTROM}Å, "
            f"feature_dim={FEATURE_DIM})"
        )

    out_dir.mkdir(parents=True, exist_ok=True)

    graph_entries: list[dict] = []
    failed: list[dict] = []

    for i, entry in enumerate(index):
        try:
            result = build_graph(paths, entry, policy_h, feature_h)
            save_graph(result, out_dir)
            graph_entries.append(result.manifest_entry)
            if not quiet and (i + 1) % 100 == 0:
                print(f"  [{i+1}/{len(index)}] {entry.apo_pdb_id}")
        except (Phase3DataError, Exception) as exc:
            failed.append({"structure_id": entry.apo_pdb_id, "error": str(exc)})
            if not quiet:
                print(f"  FAIL {entry.apo_pdb_id}: {exc}", file=sys.stderr)

    command = " ".join(sys.argv)
    manifest = build_graph_release_manifest(
        graph_entries,
        root,
        command,
        paths.split_manifest_path,
        paths.label_manifest_path,
    )
    manifest["failed_count"] = len(failed)
    manifest["failed_structures"] = failed

    # Write manifest
    manifest_hash = sha256_json(manifest)[:16]
    manifest_path = out_dir / f"graph_release_manifest_{manifest_hash}.json"
    write_json(manifest_path, manifest)

    if not quiet:
        print(f"\n[phase3_graphs] Done.")
        print(f"  Graphs generated : {len(graph_entries)}")
        print(f"  Failed           : {len(failed)}")
        print(f"  Manifest         : {manifest_path}")
        print(f"  Manifest hash    : {manifest_hash}")
        print(f"  Status           : PENDING_HUMAN_REVIEW")
        print(f"  Training         : BLOCKED — human graph release review required")

    return {
        "generated": len(graph_entries),
        "failed": len(failed),
        "manifest_path": str(manifest_path),
        "manifest_hash": manifest_hash,
        "status": "PENDING_HUMAN_REVIEW",
        "NO_TRAINING_PERFORMED": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 3 governed graph generation. "
            "Emits graph artifacts and a release manifest for human review. "
            "Training remains blocked until the manifest receives human sign-off."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Workspace root directory (default: current directory)",
    )
    parser.add_argument(
        "--split",
        choices=["all", "train", "validation", "test"],
        default="all",
        help="Split to generate graphs for (default: all)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=constants.GRAPHS_DIR,
        help=f"Output directory for graph artifacts (default: {constants.GRAPHS_DIR})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit to first N structures (for testing only)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output",
    )
    args = parser.parse_args()

    try:
        run_graph_generation(
            root=args.root,
            requested_split=args.split,
            out_dir=args.out_dir,
            limit=args.limit,
            quiet=args.quiet,
        )
    except Phase3DataError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
