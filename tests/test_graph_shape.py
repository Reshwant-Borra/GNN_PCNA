"""Tests for graph construction shapes and feature dimensions."""
import numpy as np
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import torch
    from src.data_processing.parse_pdb import Residue
    from src.data_processing.graph_construction import build_graph_v2
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

pytestmark = pytest.mark.skipif(not HAS_TORCH, reason="torch / torch_geometric not installed")

NODE_DIM = 40
EDGE_DIM = 6


def _dummy_residue(chain: str, resid: int, ca: list) -> Residue:
    return Residue(
        chain=chain, resid=resid, resname="ALA",
        ca_coord=np.array(ca, dtype=np.float32),
        b_factor=20.0, secondary_structure="C", sasa=50.0,
    )


def _make_chain(n: int, chain: str = "A", spacing: float = 3.8) -> list:
    return [_dummy_residue(chain, i + 1, [i * spacing, 0.0, 0.0]) for i in range(n)]


def test_node_feature_dim():
    residues = _make_chain(10)
    data = build_graph_v2(residues)
    assert data.x.shape[1] == NODE_DIM, f"Expected {NODE_DIM}-dim nodes, got {data.x.shape[1]}"


def test_edge_feature_dim():
    residues = _make_chain(10)
    data = build_graph_v2(residues)
    assert data.edge_attr.shape[1] == EDGE_DIM
    if hasattr(data, "edge_attr_seq"):
        assert data.edge_attr_seq.shape[1] == EDGE_DIM


def test_node_count_matches_residues():
    n = 15
    residues = _make_chain(n)
    data = build_graph_v2(residues)
    assert data.x.shape[0] == n


def test_edge_index_valid():
    residues = _make_chain(10)
    data = build_graph_v2(residues)
    assert data.edge_index.shape[0] == 2
    assert data.edge_index.min() >= 0
    assert data.edge_index.max() < 10


def test_chain_id_assigned():
    residues = _make_chain(5, "A") + _make_chain(5, "B", spacing=4.0)
    # Offset B chain so it's spatially separate
    for r in residues[5:]:
        r.ca_coord = r.ca_coord + np.array([100.0, 0.0, 0.0])
    data = build_graph_v2(residues)
    assert hasattr(data, "chain_id")
    assert len(data.chain_id) == 10


def test_scores_in_range():
    import torch
    from src.models import PocketGNN
    residues = _make_chain(20)
    data = build_graph_v2(residues)
    model = PocketGNN.small().eval()
    with torch.no_grad():
        scores = model(
            data.x, data.edge_index, data.edge_attr,
            data.edge_index_seq, data.edge_attr_seq,
            data.chain_id,
        )
    assert scores.shape == (20,)
    assert float(scores.min()) >= 0.0
    assert float(scores.max()) <= 1.0
