"""Unlabeled graph construction for Phase 4 PCNA inference.

Reuses Phase 3 feature and edge utilities but requires no label files.
Builds spatial-only edges (edge_type==0, 8Å cutoff) matching the frozen
spatial_only checkpoint used for inference.

Governance: docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md
Authorization: reports/phase4/gate6_authorization_20260529.md
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch_geometric.data import Data

from phase3_data.models import ResidueNode
from phase3_graphs.builder import _build_spatial_edges
from phase3_graphs.constants import CA_CUTOFF_ANGSTROM
from phase3_graphs.features import FEATURE_DIM, is_modified_residue, residue_features
from phase3_graphs.mmcif_coords import extract_ca_coordinates
from phase4_inference.cif_utils import temp_cif

ResidueKey = tuple[str, str, str | None]  # (chain_id, residue_number, insertion_code)


def _residue_key(node: ResidueNode) -> ResidueKey:
    return (node.chain_id, node.residue_number, node.insertion_code)


def build_inference_graph(
    cif_path: Path,
    selected_chains: set[str],
    residues: list[ResidueNode],
) -> tuple[Data, list[dict[str, Any]]]:
    """Build a PyG Data object for unlabeled Phase 4 inference.

    Args:
        cif_path:        Original .cif or .cif.gz path (used for CA extraction).
        selected_chains: Chain IDs to include (from chain_selector).
        residues:        Pre-parsed ResidueNode list (from chain_selector, all chains).

    Returns:
        data:          PyG Data with x=(N,25) float32, edge_index=(2,E) int64,
                       edge_attr=(E,) float32 (CA distances in Angstrom).
        node_metadata: List of per-node dicts with chain_id, residue_number,
                       insertion_code, residue_name, entity_id for score mapping.
    """
    target_residues = [r for r in residues if r.chain_id in selected_chains]

    if not target_residues:
        empty = Data(
            x=torch.zeros((0, FEATURE_DIM), dtype=torch.float32),
            edge_index=torch.zeros((2, 0), dtype=torch.int64),
            edge_attr=torch.zeros(0, dtype=torch.float32),
        )
        return empty, []

    node_keys: list[ResidueKey] = [_residue_key(r) for r in target_residues]

    with temp_cif(cif_path) as tmp:
        ca_coords = extract_ca_coordinates(tmp)

    N = len(target_residues)
    x = np.zeros((N, FEATURE_DIM), dtype=np.float32)
    node_metadata: list[dict[str, Any]] = []

    for i, r in enumerate(target_residues):
        is_mod = is_modified_residue(r.residue_name)
        has_altloc = bool(r.altloc_ids)
        x[i] = residue_features(r.residue_name, is_mod, r.has_ca, has_altloc)
        node_metadata.append({
            "node_index": i,
            "chain_id": r.chain_id,
            "residue_number": r.residue_number,
            "insertion_code": r.insertion_code,
            "residue_name": r.residue_name,
            "entity_id": r.entity_id,
            "has_ca": r.has_ca,
        })

    edge_index_np, edge_dist_np = _build_spatial_edges(ca_coords, node_keys, CA_CUTOFF_ANGSTROM)

    data = Data(
        x=torch.from_numpy(x),
        edge_index=torch.from_numpy(edge_index_np),
        edge_attr=torch.from_numpy(edge_dist_np),
    )
    return data, node_metadata
