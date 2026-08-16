"""Residue-label alignment audit scaffolding for Phase 3."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from phase3_data.errors import Phase3DataError
from phase3_data.hashing import sha256_file
from phase3_data.index import build_dataset_index
from phase3_data.labels import background_record, load_structure_label_file, parse_target_chains
from phase3_data.mmcif import parse_mmcif_residues
from phase3_data.models import DatasetIndexEntry, Phase3Paths, ResidueNode
from phase3_data.provenance import process_context


def _target_residues(all_residues: list[ResidueNode], target_chains: tuple[str, ...]) -> tuple[list[ResidueNode], list[str]]:
    target_set = set(target_chains)
    included = [node for node in all_residues if node.chain_id in target_set]
    all_chains = sorted({node.chain_id for node in all_residues})
    excluded = [chain for chain in all_chains if chain not in target_set]
    if not included:
        raise Phase3DataError(f"No residues found for target chains {target_chains}.")
    return included, excluded


def audit_index_entry(paths: Phase3Paths, entry: DatasetIndexEntry) -> dict[str, Any]:
    cif_path = paths.root / entry.cif_path
    label_path = paths.root / entry.label_path
    label_data, explicit_labels = load_structure_label_file(label_path)
    target_chains = parse_target_chains(label_data["chain"])
    residues, excluded_chains = _target_residues(parse_mmcif_residues(cif_path), target_chains)
    residue_keys: dict[str, ResidueNode] = {}
    duplicates: set[str] = set()
    for residue in residues:
        if residue.label_key in residue_keys:
            duplicates.add(residue.label_key)
        residue_keys[residue.label_key] = residue
    if duplicates:
        raise Phase3DataError(
            f"Duplicate residue label keys in {entry.apo_pdb_id}: {sorted(duplicates)[:10]}"
        )
    missing_from_residues = sorted(set(explicit_labels) - set(residue_keys))
    blocking_missing = [
        label_key for label_key in missing_from_residues if explicit_labels[label_key].label != -1
    ]
    if blocking_missing:
        raise Phase3DataError(
            f"Label entries do not align to residues for {entry.apo_pdb_id}: "
            f"{blocking_missing[:10]}"
        )
    masked_without_nodes = [
        label_key for label_key in missing_from_residues if explicit_labels[label_key].label == -1
    ]
    aligned_labels = []
    for residue in residues:
        record = explicit_labels.get(
            residue.label_key,
            background_record(
                residue.label_key,
                residue.chain_id,
                residue.residue_number,
                residue.insertion_code,
            ),
        )
        aligned_labels.append(record)
    positive_count = sum(1 for label in aligned_labels if label.label == 1)
    masked_count = sum(1 for label in aligned_labels if label.label == -1)
    background_count = sum(1 for label in aligned_labels if label.label == 0)
    if positive_count != entry.positive_count or masked_count + len(masked_without_nodes) != entry.masked_count:
        raise Phase3DataError(
            f"Aligned label counts mismatch for {entry.apo_pdb_id}: "
            f"positives {positive_count}/{entry.positive_count}, masked {masked_count}/{entry.masked_count}"
        )
    return {
        "apo_pdb_id": entry.apo_pdb_id,
        "fold": entry.fold,
        "status": "PASS",
        "cif_path": entry.cif_path,
        "cif_hash_sha256": sha256_file(cif_path),
        "label_path": entry.label_path,
        "label_hash_sha256": sha256_file(label_path),
        "included_chains": list(target_chains),
        "excluded_chains": excluded_chains,
        "node_count": len(residues),
        "explicit_label_count": len(explicit_labels),
        "positive_count": positive_count,
        "masked_count": masked_count,
        "masked_label_entries_without_nodes": len(masked_without_nodes),
        "masked_label_keys_without_nodes_sample": masked_without_nodes[:10],
        "background_unlabeled_count": background_count,
        "loss_mask_false_count": masked_count,
        "residues_with_altloc": sum(1 for residue in residues if residue.altloc_ids),
        "residues_without_ca": sum(1 for residue in residues if not residue.has_ca),
        "residue_identity_fields": [
            "chain_id",
            "residue_number",
            "insertion_code",
            "residue_name",
        ],
        "edge_policy": "UNAPPROVED_NOT_GENERATED",
        "feature_policy": "UNAPPROVED_NOT_GENERATED",
    }


def build_residue_audit_manifest(
    paths: Phase3Paths,
    command: str,
    requested_split: str = "all",
    validation_fold: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    index = build_dataset_index(
        paths,
        requested_split=requested_split,
        validation_fold=validation_fold,
        require_cif=True,
    )
    if limit is not None:
        index = index[:limit]
    entries = [audit_index_entry(paths, entry) for entry in index]
    return {
        "artifact_type": "phase3_residue_audit_manifest",
        "status": "PASS",
        **process_context(paths.root, command),
        "requested_split": requested_split,
        "validation_fold": validation_fold,
        "limited_to_first_n": limit,
        "audited_structure_count": len(entries),
        "entries": entries,
        "graph_generation": "NOT_PERFORMED",
        "edge_policy": "UNAPPROVED_NOT_GENERATED",
        "feature_policy": "UNAPPROVED_NOT_GENERATED",
        "training": "NOT_PERFORMED",
        "governance": [
            "docs/scientific_governance/06_LABELING_RULES.md",
            "docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md",
            "docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md",
            "docs/scientific_governance/26_HUMAN_REVIEW_GATES.md",
        ],
        "notes": (
            "Residue-label audit only. Unlisted residues are recorded as background_unlabeled, "
            "not true negatives. Masked label=-1 residues have loss_mask=false."
        ),
    }


def index_manifest(
    paths: Phase3Paths,
    command: str,
    requested_split: str,
    validation_fold: str | None,
) -> dict[str, Any]:
    entries = build_dataset_index(
        paths,
        requested_split=requested_split,
        validation_fold=validation_fold,
        require_cif=True,
    )
    return {
        "artifact_type": "phase3_dataset_index",
        "status": "PASS",
        **process_context(paths.root, command),
        "requested_split": requested_split,
        "validation_fold": validation_fold,
        "entry_count": len(entries),
        "entries": [entry.to_json_dict() for entry in entries],
        "training": "NOT_PERFORMED",
        "governance": [
            "docs/scientific_governance/04_DATASET_CONSTRAINTS.md",
            "docs/scientific_governance/05_SPLIT_PROTOCOL.md",
            "docs/scientific_governance/06_LABELING_RULES.md",
        ],
    }
