"""Tests for checkpoint loading and metadata."""
import sys
from pathlib import Path

import numpy as np
import torch
import torch_geometric  # noqa: F401

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import PocketGNN, PocketGNNXL

REPO = Path(__file__).parent.parent

CKPT_SMALL = REPO / "checkpoints" / "pcna" / "best_pcna.ckpt"
CKPT_V3 = REPO / "checkpoints" / "pcna" / "best_pcna_v3.ckpt"
CKPT_V3F = REPO / "checkpoints" / "pcna" / "best_pcna_v3_fixed.ckpt"


def _require(path: Path) -> None:
    assert path.exists(), f"Required checkpoint is missing: {path}"


def test_small_checkpoint_loads():
    _require(CKPT_SMALL)
    model = PocketGNN.small()
    state = torch.load(str(CKPT_SMALL), map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    n = sum(p.numel() for p in model.parameters())
    assert 800_000 < n < 1_100_000, f"Unexpected param count: {n}"


def test_v3_checkpoint_loads():
    _require(CKPT_V3)
    model = PocketGNNXL()
    state = torch.load(str(CKPT_V3), map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    n = sum(p.numel() for p in model.parameters())
    assert 13_000_000 < n < 14_000_000, f"Unexpected param count: {n}"


def test_v3_fixed_checkpoint_loads():
    _require(CKPT_V3F)
    model = PocketGNNXL()
    state = torch.load(str(CKPT_V3F), map_location="cpu", weights_only=True)
    model.load_state_dict(state)


def test_checkpoint_keys_are_state_dict():
    """Verify checkpoints are pure state dicts, not wrapped in extra keys."""
    for ckpt in [CKPT_SMALL, CKPT_V3, CKPT_V3F]:
        _require(ckpt)
        state = torch.load(str(ckpt), map_location="cpu", weights_only=True)
        assert isinstance(state, dict), f"{ckpt.name} is not a dict"
        first_key = next(iter(state))
        assert "." in first_key or "_" in first_key, (
            f"{ckpt.name} looks wrapped; found key: {first_key!r}"
        )


def test_chain_mapping_consistency():
    """Chain IDs in graph should be contiguous integers starting from 0."""
    from src.data_processing.parse_pdb import Residue
    from src.data_processing.graph_construction import build_graph_v2

    residues = [
        Residue("A", i, "ALA", np.array([i * 3.8, 0, 0], np.float32), 20.0, "C", 50.0)
        for i in range(1, 11)
    ] + [
        Residue("B", i, "ALA", np.array([i * 3.8, 20, 0], np.float32), 20.0, "C", 50.0)
        for i in range(1, 11)
    ]
    data = build_graph_v2(residues)
    unique_ids = set(data.chain_id.tolist())
    assert unique_ids == {0, 1}, f"Expected {{0, 1}}, got {unique_ids}"
