"""Graph release manifest generation for Phase 3.

Produces a collection-level manifest that is the artifact submitted for
human review before any real training is authorized.

Status is always PENDING_HUMAN_REVIEW — training remains blocked under
docs/scientific_governance/26_HUMAN_REVIEW_GATES.md.

Governance: docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from phase3_data.hashing import sha256_file, sha256_json
from phase3_data.provenance import process_context
from phase3_graphs import constants
from phase3_graphs.features import FEATURE_DIM, STANDARD_AA, VOCAB_SIZE


def policy_hash(root: Path) -> str:
    """SHA-256 of the human-approved graph policy decision record."""
    path = root / constants.GRAPH_POLICY_APPROVAL_PATH
    if not path.is_file():
        from phase3_data.errors import Phase3DataError
        raise Phase3DataError(
            f"Graph policy approval record is missing: {path}. "
            "Cannot proceed without a signed human decision record."
        )
    return sha256_file(path)


def feature_definition_hash() -> str:
    """Stable SHA-256 fingerprint of the approved feature definition.

    This hash changes if the vocabulary, feature layout, cutoff, or edge
    encoding is modified — triggering a re-generation requirement.
    """
    defn: dict[str, Any] = {
        "standard_aa": STANDARD_AA,
        "vocab_size": VOCAB_SIZE,
        "feature_dim": FEATURE_DIM,
        "feature_layout": [
            "indices_0_to_19_one_hot_standard_20aa_alphabetical",
            "index_20_modified_residue_one_hot",
            "index_21_unknown_residue_one_hot",
            "index_22_binary_is_modified",
            "index_23_binary_missing_ca",
            "index_24_binary_has_altloc",
        ],
        "ca_cutoff_angstrom": constants.CA_CUTOFF_ANGSTROM,
        "edge_type_encoding": {
            str(constants.EDGE_TYPE_SPATIAL): "spatial",
            str(constants.EDGE_TYPE_SEQUENTIAL): "sequential",
        },
        "esm_features": "NOT_INCLUDED",
        "normalization": "NONE",
    }
    return sha256_json(defn)


def build_graph_release_manifest(
    graph_entries: list[dict[str, Any]],
    root: Path,
    command: str,
    split_manifest_path: Path,
    label_manifest_path: Path,
) -> dict[str, Any]:
    """Build the collection-level manifest for human review.

    Every field in this manifest is needed for the first graph release review
    required by docs/scientific_governance/26_HUMAN_REVIEW_GATES.md.
    """
    split_hash = sha256_file(split_manifest_path)
    label_hash = sha256_file(label_manifest_path)
    policy_h = policy_hash(root)
    feature_h = feature_definition_hash()

    total_nodes = sum(e["node_count"] for e in graph_entries)
    total_positives = sum(e["positive_count"] for e in graph_entries)
    total_masked = sum(e["masked_count"] for e in graph_entries)
    total_bg = sum(e["background_count"] for e in graph_entries)
    total_spatial = sum(e["spatial_edge_pairs"] for e in graph_entries)
    total_sequential = sum(e["sequential_edge_pairs"] for e in graph_entries)
    total_no_ca = sum(e["nodes_without_ca"] for e in graph_entries)
    total_altloc = sum(e["nodes_with_altloc"] for e in graph_entries)
    total_masked_without_nodes = sum(e["masked_label_entries_without_nodes"] for e in graph_entries)

    return {
        "artifact_type": "phase3_graph_release_manifest",
        "status": "PENDING_HUMAN_REVIEW",
        "NO_TRAINING_PERFORMED": True,
        **process_context(root, command),
        "graph_policy_decision_id": constants.GRAPH_POLICY_DECISION_ID,
        "graph_policy_approval_path": str(constants.GRAPH_POLICY_APPROVAL_PATH),
        "split_manifest_hash_sha256": split_hash,
        "label_manifest_hash_sha256": label_hash,
        "policy_hash_sha256": policy_h,
        "feature_definition_hash_sha256": feature_h,
        "feature_dim": FEATURE_DIM,
        "ca_cutoff_angstrom": constants.CA_CUTOFF_ANGSTROM,
        "edge_type_encoding": {
            str(constants.EDGE_TYPE_SPATIAL): "spatial",
            str(constants.EDGE_TYPE_SEQUENTIAL): "sequential",
        },
        "esm_features": "NOT_INCLUDED",
        "normalization": "NONE_APPLIED",
        "structure_count": len(graph_entries),
        "total_nodes": total_nodes,
        "total_positives": total_positives,
        "total_masked": total_masked,
        "total_background": total_bg,
        "total_spatial_edge_pairs": total_spatial,
        "total_sequential_edge_pairs": total_sequential,
        "total_nodes_without_ca": total_no_ca,
        "total_nodes_with_altloc": total_altloc,
        "total_masked_labels_without_nodes": total_masked_without_nodes,
        "governance": list(constants.GOVERNANCE_PATHS),
        "graphs": graph_entries,
    }
