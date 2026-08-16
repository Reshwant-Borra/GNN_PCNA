"""Split-aware Phase 3 dataset index builder."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from phase3_data import constants
from phase3_data.errors import Phase3DataError
from phase3_data.labels import load_structure_label_file
from phase3_data.manifests import (
    load_excluded_records,
    load_label_manifest,
    load_sequence_clusters,
    load_split_manifest,
    split_entries,
)
from phase3_data.models import DatasetIndexEntry, Phase3Paths, SplitEntry


def _entry_in_requested_split(entry: SplitEntry, requested_split: str, validation_fold: str | None) -> bool:
    if requested_split not in constants.VALID_INDEX_SPLITS:
        raise Phase3DataError(f"Invalid requested split: {requested_split}")
    if validation_fold is not None and validation_fold not in constants.TRAIN_FOLDS:
        raise Phase3DataError(f"Invalid validation fold: {validation_fold}")
    if requested_split == "all":
        return True
    if requested_split == "test":
        return entry.final_fold == "test"
    if requested_split == "validation":
        if validation_fold is None:
            raise Phase3DataError(
                "Validation split requires --validation-fold train-0|train-1|train-2|train-3. "
                "The frozen manifest does not define a single default validation fold."
            )
        return entry.final_fold == validation_fold
    if requested_split == "train":
        if entry.final_fold not in constants.TRAIN_FOLDS:
            return False
        return validation_fold is None or entry.final_fold != validation_fold
    raise Phase3DataError(f"Unhandled split: {requested_split}")


def _assert_pcna_not_train_or_validation(entry: SplitEntry, requested_split: str) -> None:
    if requested_split not in {"train", "validation"}:
        return
    if entry.pcna_holdout or entry.cluster_id_30 == constants.EXPECTED_PCNA_CLUSTER_ID_30:
        raise Phase3DataError(
            f"PCNA/PCNA-cluster structure {entry.apo_pdb_id} cannot enter {requested_split}."
        )


def _cif_path_for(paths: Phase3Paths, apo_pdb_id: str) -> Path:
    return paths.cif_dir_path / f"{apo_pdb_id.lower()}.cif"


def build_dataset_index(
    paths: Phase3Paths,
    requested_split: str = "all",
    validation_fold: str | None = None,
    require_cif: bool = True,
) -> list[DatasetIndexEntry]:
    split = load_split_manifest(paths.split_manifest_path)
    label_manifest = load_label_manifest(paths.label_manifest_path)
    excluded = load_excluded_records(paths.excluded_records_path)
    load_sequence_clusters(paths.sequence_clusters_path)

    excluded_ids = {row["apo_pdb_id"].lower() for row in excluded["excluded"]}
    entries = split_entries(split)
    index: list[DatasetIndexEntry] = []
    for apo_pdb_id in sorted(entries):
        entry = entries[apo_pdb_id]
        if entry.excluded or apo_pdb_id in excluded_ids:
            continue
        if not _entry_in_requested_split(entry, requested_split, validation_fold):
            continue
        _assert_pcna_not_train_or_validation(entry, requested_split)
        if entry.label_file is None:
            raise Phase3DataError(f"Non-excluded entry {apo_pdb_id} is missing label_file.")
        label_path = paths.resolve(entry.label_file)
        label_summary = label_manifest["entries"].get(apo_pdb_id)
        if label_summary is None:
            raise Phase3DataError(f"Label manifest is missing {apo_pdb_id}.")
        label_data, label_records = load_structure_label_file(label_path)
        if label_data.get("apo_pdb_id", "").lower() != apo_pdb_id:
            raise Phase3DataError(f"Label file apo_pdb_id mismatch for {apo_pdb_id}.")
        if label_data.get("fold") not in {entry.final_fold, entry.original_fold}:
            raise Phase3DataError(f"Label fold mismatch for {apo_pdb_id}.")
        cif_path = _cif_path_for(paths, apo_pdb_id)
        if require_cif and not cif_path.is_file():
            raise Phase3DataError(
                f"Missing CIF for {apo_pdb_id}: {cif_path}. "
                "Run `python -m phase3_data.cli verify-or-extract-cifs` with PYTHONPATH=src."
            )
        actual_hash_prefix = hashlib.sha256(
            json.dumps(label_data, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
        expected_hash_prefix = label_summary["hash_sha256_prefix"]
        if actual_hash_prefix != expected_hash_prefix:
            raise Phase3DataError(
                f"Label hash prefix mismatch for {apo_pdb_id}: "
                f"expected {expected_hash_prefix}, got {actual_hash_prefix}"
            )
        index.append(
            DatasetIndexEntry(
                apo_pdb_id=apo_pdb_id,
                fold=entry.final_fold,
                requested_split=requested_split,
                cluster_id_30=entry.cluster_id_30,
                uniprot_id=entry.uniprot_id,
                label_path=str(entry.label_file),
                cif_path=str(constants.CRYPTOBENCH_CIF_DIR / f"{apo_pdb_id}.cif"),
                label_hash_sha256_prefix=actual_hash_prefix,
                positive_count=int(label_data["positive_count"]),
                masked_count=int(label_data["masked_count"]),
                explicit_label_count=len(label_records),
            )
        )
    return index
