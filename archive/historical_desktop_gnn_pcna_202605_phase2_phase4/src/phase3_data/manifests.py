"""Governed readers and validators for frozen Phase 2 artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from phase3_data import constants
from phase3_data.errors import Phase3DataError
from phase3_data.hashing import sha256_file
from phase3_data.io import read_json, reject_original_folds_path
from phase3_data.models import Phase3Paths, SplitEntry


def load_split_manifest(path: Path) -> dict[str, Any]:
    reject_original_folds_path(path)
    data = read_json(path)
    if data.get("status") != "FROZEN":
        raise Phase3DataError(f"Split manifest must be FROZEN: {path}")
    manifest_hash = data.get("manifest_hash_sha256")
    if manifest_hash != constants.EXPECTED_SPLIT_HASH_SHA256:
        raise Phase3DataError(
            "Frozen split manifest hash mismatch: "
            f"expected {constants.EXPECTED_SPLIT_HASH_SHA256}, got {manifest_hash}"
        )
    if data.get("excluded_structures") != constants.EXPECTED_EXCLUDED_STRUCTURES:
        raise Phase3DataError("Frozen split manifest excluded count mismatch.")
    entries = data.get("entries")
    if not isinstance(entries, dict):
        raise Phase3DataError("Frozen split manifest is missing entries.")
    non_excluded = [row for row in entries.values() if not row.get("excluded")]
    if len(non_excluded) != constants.EXPECTED_LABEL_STRUCTURES:
        raise Phase3DataError(
            f"Expected {constants.EXPECTED_LABEL_STRUCTURES} non-excluded split entries, "
            f"found {len(non_excluded)}."
        )
    return data


def reject_forbidden_supervised_source(path: Path) -> None:
    normalized = str(path).replace("\\", "/").lower()
    forbidden_markers = (
        "friend_crawl",
        "friend_sample",
        "gnn_pnca",
        "project-version-1",
        "pcna-xl-esm-full-final-framing",
    )
    if any(marker in normalized for marker in forbidden_markers):
        raise Phase3DataError(
            f"Forbidden Phase 3 supervised source path: {path}. "
            "Use frozen CryptoBench Phase 2 artifacts only."
        )


def split_entries(split_manifest: dict[str, Any]) -> dict[str, SplitEntry]:
    rows: dict[str, SplitEntry] = {}
    for apo_pdb_id, row in split_manifest["entries"].items():
        label_file = row.get("label_file")
        rows[apo_pdb_id.lower()] = SplitEntry(
            apo_pdb_id=row["apo_pdb_id"].lower(),
            original_fold=row["original_fold"],
            final_fold=row["final_fold"],
            cluster_id_30=row.get("cluster_id_30"),
            uniprot_id=row.get("uniprot_id"),
            pcna_holdout=bool(row.get("pcna_holdout")),
            excluded=bool(row.get("excluded")),
            exclusion_reason=row.get("exclusion_reason"),
            label_file=Path(label_file) if label_file else None,
        )
    return rows


def load_label_manifest(path: Path) -> dict[str, Any]:
    data = read_json(path)
    if data.get("status") != "FROZEN":
        raise Phase3DataError(f"Label manifest must be FROZEN: {path}")
    expected = {
        "structures_labeled": constants.EXPECTED_LABEL_STRUCTURES,
        "structures_excluded": constants.EXPECTED_EXCLUDED_STRUCTURES,
        "total_positives": constants.EXPECTED_TOTAL_POSITIVES,
        "total_masked": constants.EXPECTED_TOTAL_MASKED,
    }
    for key, value in expected.items():
        if data.get(key) != value:
            raise Phase3DataError(
                f"Label manifest {key} mismatch: expected {value}, got {data.get(key)}"
            )
    expected_split_ref = str(constants.FROZEN_SPLIT_MANIFEST).replace("\\", "/")
    actual_split_ref = str(data.get("split_manifest_ref")).replace("\\", "/")
    if actual_split_ref != expected_split_ref:
        raise Phase3DataError("Label manifest does not reference the frozen split manifest.")
    if data.get("label_policy") != "positive_unlabeled":
        raise Phase3DataError("Label manifest must declare positive_unlabeled policy.")
    return data


def load_excluded_records(path: Path) -> dict[str, Any]:
    data = read_json(path)
    if data.get("total_excluded") != constants.EXPECTED_EXCLUDED_STRUCTURES:
        raise Phase3DataError("Excluded-record manifest count mismatch.")
    excluded = data.get("excluded")
    if not isinstance(excluded, list):
        raise Phase3DataError("Excluded-record manifest is missing excluded list.")
    ids = {row.get("apo_pdb_id", "").lower() for row in excluded}
    if len(ids) != constants.EXPECTED_EXCLUDED_STRUCTURES:
        raise Phase3DataError("Excluded-record manifest contains duplicate or missing IDs.")
    return data


def load_sequence_clusters(path: Path) -> dict[str, Any]:
    data = read_json(path)
    if data.get("pcna_cluster_id_30") != constants.EXPECTED_PCNA_CLUSTER_ID_30:
        raise Phase3DataError("PCNA cluster ID mismatch in sequence cluster assignments.")
    return data


def validate_governed_inputs(paths: Phase3Paths) -> dict[str, Any]:
    split = load_split_manifest(paths.split_manifest_path)
    labels = load_label_manifest(paths.label_manifest_path)
    excluded = load_excluded_records(paths.excluded_records_path)
    clusters = load_sequence_clusters(paths.sequence_clusters_path)
    return {
        "status": "PASS",
        "split_manifest": str(paths.split_manifest_path),
        "split_manifest_hash_sha256": sha256_file(paths.split_manifest_path),
        "frozen_split_hash": split["manifest_hash_sha256"],
        "label_manifest": str(paths.label_manifest_path),
        "label_manifest_hash_sha256": sha256_file(paths.label_manifest_path),
        "excluded_records": str(paths.excluded_records_path),
        "excluded_ids": sorted(row["apo_pdb_id"].lower() for row in excluded["excluded"]),
        "sequence_clusters": str(paths.sequence_clusters_path),
        "pcna_cluster_id_30": clusters["pcna_cluster_id_30"],
        "structures_labeled": labels["structures_labeled"],
        "total_positives": labels["total_positives"],
        "total_masked": labels["total_masked"],
        "governance": list(constants.GOVERNANCE_PATHS),
    }
