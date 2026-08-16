#!/usr/bin/env python3
"""Verify or retrieve the frozen 520-dim clean-split graph lineage."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO / "artifacts" / "provenance" / "GRAPH_LINEAGE_520_MANIFEST.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    source = manifest["graphs"].get("source_split_integrity_manifest")
    if source and "per_structure" not in manifest["graphs"]:
        split_integrity = json.loads((REPO / source).read_text(encoding="utf-8"))
        manifest["graphs"]["per_structure"] = split_integrity["per_structure"]
        manifest["graphs"]["graph_manifest_hash"] = split_integrity["graph_manifest_hash"]
        manifest["graphs"]["split_counts"] = split_integrity["split_counts"]
        manifest["graphs"]["structure_count"] = len(split_integrity["per_structure"])
        manifest["graphs"]["degenerate_structures"] = split_integrity.get("degenerate_structures", [])
    return manifest


def retrieve_from_origin(manifest: dict, graph_dir: Path) -> None:
    source = manifest["retrieval"]["git_source"]
    branch = source["branch"]
    paths = source["paths"]
    fetch = subprocess.run(
        ["git", "-C", str(REPO), "fetch", "origin", branch],
        text=True,
        capture_output=True,
    )
    if fetch.returncode != 0:
        repository = source.get("repository")
        if not repository:
            fetch.check_returncode()
        subprocess.run(["git", "-C", str(REPO), "fetch", repository, branch], check=True)
    subprocess.run(
        ["git", "-C", str(REPO), "restore", "--source", f"origin/{branch}", "--", *paths],
        text=True,
        capture_output=True,
        check=False,
    )
    missing_after_origin = [p for p in paths if not (REPO / p).exists()]
    if missing_after_origin:
        subprocess.run(["git", "-C", str(REPO), "restore", "--source", "FETCH_HEAD", "--", *paths],
                       check=True)
    graph_dir.mkdir(parents=True, exist_ok=True)


def validate(manifest: dict, graph_dir: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    rows = manifest["graphs"]["per_structure"]
    found = []
    graph_hash = hashlib.sha256()
    for row in rows:
        pdb_id = row["pdb_id"]
        path = graph_dir / f"{pdb_id}.pt"
        if not path.exists():
            errors.append(f"{pdb_id}: missing {path}")
            continue
        digest = sha256_file(path)
        if digest != row["sha256"]:
            errors.append(f"{pdb_id}: sha256 {digest} != {row['sha256']}")
        graph_hash.update(row["split"].encode("utf-8"))
        graph_hash.update(pdb_id.encode("utf-8"))
        graph_hash.update(digest.encode("ascii"))
        found.append(pdb_id)

    expected_hash = manifest["graphs"]["graph_manifest_hash"]
    observed_hash = graph_hash.hexdigest() if len(found) == len(rows) else None
    if observed_hash and observed_hash != expected_hash:
        errors.append(f"graph manifest hash {observed_hash} != {expected_hash}")
    split_counts = {}
    label_total = 0
    dims = set()
    for row in rows:
        split_counts[row["split"]] = split_counts.get(row["split"], 0) + 1
        label_total += int(row["n_positive"])
        dims.add(int(row["node_dim"]))
    if split_counts != manifest["graphs"]["split_counts"]:
        errors.append(f"split counts {split_counts} != {manifest['graphs']['split_counts']}")
    if dims != {int(manifest["feature_contract"]["node_features_total"])}:
        errors.append(f"node dims {sorted(dims)} do not match feature contract")
    if len(rows) != int(manifest["graphs"]["structure_count"]):
        errors.append("manifest structure count mismatch")
    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "found_graphs": len(found),
        "expected_graphs": len(rows),
        "observed_graph_manifest_hash": observed_hash,
        "expected_graph_manifest_hash": expected_hash,
        "split_counts": split_counts,
        "total_positive_labels": label_total,
        "feature_dims": sorted(dims),
        "homology_split": manifest["homology_split"],
        "composite_chain_bug_status": manifest["label_integrity"]["composite_chain_bug_status"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--graph-dir", type=Path, default=REPO / "data" / "graphs_xl")
    ap.add_argument("--retrieve-from-origin", action="store_true",
                    help="fetch graph tensors from the recorded external git branch before validation")
    ap.add_argument("--allow-missing", action="store_true",
                    help="return 0 while reporting missing local graphs; useful for environment checks")
    args = ap.parse_args()
    manifest = load_manifest(args.manifest)
    if args.retrieve_from_origin:
        retrieve_from_origin(manifest, args.graph_dir)
    result = validate(manifest, args.graph_dir)
    print(json.dumps(result, indent=2))
    if result["ok"] or (args.allow_missing and result["found_graphs"] == 0):
        return 0
    print("Graph lineage validation failed. Retrieval command:", file=sys.stderr)
    print("  python3 scripts/verify_graph_lineage.py --retrieve-from-origin", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
