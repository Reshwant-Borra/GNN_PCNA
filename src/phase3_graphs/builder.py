"""Governed graph construction from approved policy.

Implements the Phase 3 MVP graph for one structure:
  - One node per target-chain residue aligned to an audited label.
  - Spatial edges: undirected CA-CA contact, cutoff 8.0 Angstrom (approved).
  - Sequential edges: undirected, consecutive-integer label_seq_id only,
    same chain, no gap bridging.
  - Node features: 25-dim float32 (22 one-hot residue identity + 3 binary flags).
  - No ESM features, no normalization, no training.

Approval: reports/phase3/graph_policy_human_decision_20260528.md
Governance: docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from phase3_data.errors import Phase3DataError
from phase3_data.hashing import sha256_file, sha256_json
from phase3_data.labels import background_record, load_structure_label_file, parse_target_chains
from phase3_data.mmcif import parse_mmcif_residues
from phase3_data.models import DatasetIndexEntry, Phase3Paths, ResidueNode
from phase3_graphs import constants
from phase3_graphs.features import FEATURE_DIM, is_modified_residue, residue_features
from phase3_graphs.mmcif_coords import CACoords, extract_ca_coordinates


@dataclass
class GraphResult:
    structure_id: str
    node_features: np.ndarray    # (N, FEATURE_DIM) float32
    node_labels: np.ndarray      # (N,) int32  — values in {-1, 0, 1}
    loss_mask: np.ndarray        # (N,) bool   — True = participates in loss
    edge_index: np.ndarray       # (2, E) int64 — directed (both directions stored)
    edge_type: np.ndarray        # (E,) int8   — 0=spatial, 1=sequential
    edge_distance: np.ndarray    # (E,) float32 — Inf for sequential edges
    node_metadata: list[dict]    # per-node provenance (not trainable features)
    manifest_entry: dict[str, Any]  # full per-graph provenance record


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

ResidueKey = tuple[str, str, str | None]  # (chain_id, residue_number, insertion_code)


def _residue_key(node: ResidueNode) -> ResidueKey:
    return (node.chain_id, node.residue_number, node.insertion_code)


def _build_spatial_edges(
    ca_coords: CACoords,
    node_keys: list[ResidueKey],
    cutoff: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Undirected CA-CA spatial edges within cutoff (Angstrom).

    Returns (edge_index shape (2,E), edge_distance shape (E,)).
    Both directions are included for each pair (undirected representation).
    """
    N = len(node_keys)
    coords = np.full((N, 3), np.nan, dtype=np.float64)
    for i, key in enumerate(node_keys):
        if key in ca_coords:
            x, y, z, _ = ca_coords[key]
            coords[i] = [x, y, z]

    has_ca = ~np.isnan(coords[:, 0])
    ca_idx = np.where(has_ca)[0]
    ca_xyz = coords[ca_idx]

    if len(ca_xyz) == 0:
        return np.zeros((2, 0), dtype=np.int64), np.zeros(0, dtype=np.float32)

    # Pairwise distances — O(M^2), acceptable for M ≤ ~1000 residues per structure
    diff = ca_xyz[:, None, :] - ca_xyz[None, :, :]  # (M, M, 3)
    dist_mat = np.sqrt((diff ** 2).sum(axis=-1))     # (M, M)

    # Upper-triangle pairs within cutoff (excluding self)
    rows, cols = np.where((dist_mat <= cutoff) & (np.arange(len(ca_idx))[:, None] < np.arange(len(ca_idx))[None, :]))
    src_ca = ca_idx[rows]
    dst_ca = ca_idx[cols]
    dists = dist_mat[rows, cols].astype(np.float32)

    # Store both directions for undirected representation
    edge_src = np.concatenate([src_ca, dst_ca]).astype(np.int64)
    edge_dst = np.concatenate([dst_ca, src_ca]).astype(np.int64)
    edge_dist = np.concatenate([dists, dists])

    return np.stack([edge_src, edge_dst], axis=0), edge_dist


def _build_sequential_edges(
    nodes: list[ResidueNode],
    node_key_to_idx: dict[ResidueKey, int],
) -> np.ndarray:
    """Undirected sequential edges within each chain.

    Connects adjacent residue pairs only when:
    - Both share the same chain.
    - Both have an integer label_seq_id.
    - label_seq_id values differ by exactly 1 (no gap bridging).

    Returns edge_index shape (2, E); both directions included per pair.
    """
    chain_nodes: dict[str, list[tuple[int, int]]] = defaultdict(list)

    for node in nodes:
        key = _residue_key(node)
        if key not in node_key_to_idx:
            continue
        node_idx = node_key_to_idx[key]
        try:
            seq_id = int(node.label_seq_id) if node.label_seq_id is not None else None
        except (ValueError, TypeError):
            seq_id = None
        if seq_id is None:
            continue  # conservative: skip residues without parseable label_seq_id
        chain_nodes[node.chain_id].append((node_idx, seq_id))

    src_list: list[int] = []
    dst_list: list[int] = []

    for node_list in chain_nodes.values():
        node_list.sort(key=lambda x: x[1])  # sort by label_seq_id
        for j in range(len(node_list) - 1):
            idx_a, seq_a = node_list[j]
            idx_b, seq_b = node_list[j + 1]
            if seq_b - seq_a == 1:  # strictly consecutive, no gap
                src_list.extend([idx_a, idx_b])
                dst_list.extend([idx_b, idx_a])

    if not src_list:
        return np.zeros((2, 0), dtype=np.int64)
    return np.stack(
        [np.array(src_list, dtype=np.int64), np.array(dst_list, dtype=np.int64)],
        axis=0,
    )


def _combine_edges(
    spatial_edge_index: np.ndarray,
    spatial_dists: np.ndarray,
    seq_edge_index: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Concatenate spatial and sequential edge arrays."""
    n_spatial = spatial_edge_index.shape[1]
    n_seq = seq_edge_index.shape[1]

    parts_index = [a for a in [spatial_edge_index, seq_edge_index] if a.shape[1] > 0]
    parts_type = []
    parts_dist = []

    if n_spatial > 0:
        parts_type.append(np.full(n_spatial, constants.EDGE_TYPE_SPATIAL, dtype=np.int8))
        parts_dist.append(spatial_dists)
    if n_seq > 0:
        parts_type.append(np.full(n_seq, constants.EDGE_TYPE_SEQUENTIAL, dtype=np.int8))
        parts_dist.append(np.full(n_seq, np.inf, dtype=np.float32))

    if not parts_index:
        return (
            np.zeros((2, 0), dtype=np.int64),
            np.zeros(0, dtype=np.int8),
            np.zeros(0, dtype=np.float32),
        )

    edge_index = np.concatenate(parts_index, axis=1)
    edge_type = np.concatenate(parts_type)
    edge_distance = np.concatenate(parts_dist)
    return edge_index, edge_type, edge_distance


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_graph(
    paths: Phase3Paths,
    entry: DatasetIndexEntry,
    policy_hash: str,
    feature_hash: str,
) -> GraphResult:
    """Build a governed graph for one structure.

    Raises Phase3DataError on any policy violation:
      - Non-masked positive label that cannot align to a node.
      - Positive count mismatch after alignment.
      - Non-numeric CA coordinates.
      - Duplicate residue keys.
    """
    cif_path = paths.root / entry.cif_path
    label_path = paths.root / entry.label_path

    cif_hash = sha256_file(cif_path)
    label_hash = sha256_file(label_path)

    label_data, explicit_labels = load_structure_label_file(label_path)
    target_chains = parse_target_chains(label_data["chain"])
    target_chain_set = set(target_chains)

    all_residues = parse_mmcif_residues(cif_path)
    target_residues = [r for r in all_residues if r.chain_id in target_chain_set]
    excluded_chains = sorted({r.chain_id for r in all_residues if r.chain_id not in target_chain_set})

    if not target_residues:
        raise Phase3DataError(
            f"No residues found for target chains {target_chains} in {entry.apo_pdb_id}."
        )

    # Residue dedup check — fail closed
    seen: dict[str, ResidueNode] = {}
    dupes: set[str] = set()
    for r in target_residues:
        if r.label_key in seen:
            dupes.add(r.label_key)
        seen[r.label_key] = r
    if dupes:
        raise Phase3DataError(
            f"Duplicate residue label_keys in {entry.apo_pdb_id}: {sorted(dupes)[:10]}"
        )

    # Label alignment
    missing_from_residues = sorted(set(explicit_labels) - set(seen))
    blocking_missing = [k for k in missing_from_residues if explicit_labels[k].label != -1]
    if blocking_missing:
        raise Phase3DataError(
            f"Non-masked positive labels cannot align to any node in {entry.apo_pdb_id}: "
            f"{blocking_missing[:10]}"
        )
    masked_without_nodes = [k for k in missing_from_residues if explicit_labels[k].label == -1]

    aligned_labels = []
    for r in target_residues:
        rec = explicit_labels.get(
            r.label_key,
            background_record(r.label_key, r.chain_id, r.residue_number, r.insertion_code),
        )
        aligned_labels.append(rec)

    # Validate aligned counts against index entry
    pos_count = sum(1 for l in aligned_labels if l.label == 1)
    masked_count = sum(1 for l in aligned_labels if l.label == -1)
    bg_count = sum(1 for l in aligned_labels if l.label == 0)

    if pos_count != entry.positive_count:
        raise Phase3DataError(
            f"Positive count mismatch in {entry.apo_pdb_id}: "
            f"aligned {pos_count}, expected {entry.positive_count}"
        )
    if masked_count + len(masked_without_nodes) != entry.masked_count:
        raise Phase3DataError(
            f"Masked count mismatch in {entry.apo_pdb_id}: "
            f"{masked_count} nodes + {len(masked_without_nodes)} without nodes "
            f"= {masked_count + len(masked_without_nodes)}, expected {entry.masked_count}"
        )

    # CA coordinate extraction (approved altloc policy)
    ca_coords = extract_ca_coordinates(cif_path)

    N = len(target_residues)
    node_keys: list[ResidueKey] = [_residue_key(r) for r in target_residues]
    node_key_to_idx: dict[ResidueKey, int] = {k: i for i, k in enumerate(node_keys)}

    # Build node arrays and metadata
    node_features = np.zeros((N, FEATURE_DIM), dtype=np.float32)
    node_labels_arr = np.zeros(N, dtype=np.int32)
    loss_mask_arr = np.zeros(N, dtype=bool)
    node_metadata: list[dict] = []
    altloc_tiebreaks: list[str] = []

    for i, (r, lrec) in enumerate(zip(target_residues, aligned_labels)):
        is_mod = is_modified_residue(r.residue_name)
        has_altloc = bool(r.altloc_ids)
        node_features[i] = residue_features(r.residue_name, is_mod, r.has_ca, has_altloc)
        node_labels_arr[i] = lrec.label
        loss_mask_arr[i] = lrec.loss_mask

        key = _residue_key(r)
        selected_altloc: str | None = None
        if key in ca_coords:
            selected_altloc = ca_coords[key][3]
            if selected_altloc is not None:
                altloc_tiebreaks.append(f"{r.label_key}:{selected_altloc}")

        node_metadata.append({
            "node_index": i,
            "chain_id": r.chain_id,
            "residue_number": r.residue_number,
            "insertion_code": r.insertion_code,
            "residue_name": r.residue_name,
            "label_key": r.label_key,
            "label_seq_id": r.label_seq_id,
            "entity_id": r.entity_id,
            "has_ca": r.has_ca,
            "has_altloc": has_altloc,
            "is_modified": is_mod,
            "selected_altloc": selected_altloc,
            "label": int(lrec.label),
            "loss_mask": bool(lrec.loss_mask),
            "supervision_role": lrec.supervision_role,
        })

    # Edge construction
    spatial_ei, spatial_dist = _build_spatial_edges(ca_coords, node_keys, constants.CA_CUTOFF_ANGSTROM)
    seq_ei = _build_sequential_edges(target_residues, node_key_to_idx)
    edge_index, edge_type, edge_distance = _combine_edges(spatial_ei, spatial_dist, seq_ei)

    n_spatial = spatial_ei.shape[1]
    n_seq = seq_ei.shape[1]

    # Graph hash — canonical over arrays (covers node features, labels, edges)
    graph_hash = sha256_json({
        "structure_id": entry.apo_pdb_id,
        "node_features": node_features.tolist(),
        "node_labels": node_labels_arr.tolist(),
        "loss_mask": loss_mask_arr.tolist(),
        "edge_index": edge_index.tolist(),
        "edge_type": edge_type.tolist(),
    })

    manifest_entry: dict[str, Any] = {
        "structure_id": entry.apo_pdb_id,
        "fold": entry.fold,
        "requested_split": entry.requested_split,
        "cif_hash_sha256": cif_hash,
        "label_hash_sha256": label_hash,
        "policy_hash_sha256": policy_hash,
        "feature_hash_sha256": feature_hash,
        "graph_hash_sha256": graph_hash,
        "included_chains": list(target_chains),
        "excluded_chains": excluded_chains,
        "node_count": N,
        "positive_count": pos_count,
        "masked_count": masked_count,
        "background_count": bg_count,
        "masked_label_entries_without_nodes": len(masked_without_nodes),
        "masked_label_keys_without_nodes": masked_without_nodes,
        "spatial_edge_pairs": n_spatial // 2,
        "sequential_edge_pairs": n_seq // 2,
        "total_directed_edges": n_spatial + n_seq,
        "nodes_without_ca": sum(1 for r in target_residues if not r.has_ca),
        "nodes_with_altloc": sum(1 for r in target_residues if r.altloc_ids),
        "altloc_tiebreaks_applied": altloc_tiebreaks,
        "ca_cutoff_angstrom": constants.CA_CUTOFF_ANGSTROM,
        "edge_policy": "spatial_CA_8A_undirected_and_sequential_consecutive_label_seq_id",
        "feature_policy": "one_hot_22aa_plus_3_binary_flags_25dim",
        "esm_features": "NOT_INCLUDED",
        "normalization": "NONE_APPLIED",
        "NO_TRAINING_PERFORMED": True,
        "graph_policy_decision_id": constants.GRAPH_POLICY_DECISION_ID,
        "graph_policy_approval_path": str(constants.GRAPH_POLICY_APPROVAL_PATH),
        "governance": list(constants.GOVERNANCE_PATHS),
    }

    return GraphResult(
        structure_id=entry.apo_pdb_id,
        node_features=node_features,
        node_labels=node_labels_arr,
        loss_mask=loss_mask_arr,
        edge_index=edge_index,
        edge_type=edge_type,
        edge_distance=edge_distance,
        node_metadata=node_metadata,
        manifest_entry=manifest_entry,
    )
