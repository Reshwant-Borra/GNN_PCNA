"""Tests for checkpoint loading and metadata."""
import sys
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
torch = pytest.importorskip("torch")
pytest.importorskip("torch_geometric")

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import PocketGNN, PocketGNNXL

REPO = Path(__file__).parent.parent

CKPT_SMALL = REPO / "checkpoints" / "pcna" / "best_pcna.ckpt"
CKPT_V3 = REPO / "checkpoints" / "pcna" / "best_pcna_v3.ckpt"
CKPT_V3F = REPO / "checkpoints" / "pcna" / "best_pcna_v3_fixed.ckpt"


def _require(path: Path) -> None:
    """Checkpoints are NOT retrievable from a clean clone -- see PROVENANCE_GAPS.md §1.

    `checkpoints/` and `*.ckpt` are git-ignored, so best_pcna_v3.ckpt exists only on the
    original developer machine. This is the FULL_RETRAINING_REPRODUCIBILITY gap, and it is
    real: end-to-end retraining cannot be reproduced from this repository. It does NOT
    affect the MD arm, which consumes the frozen handoff, not the pretrain checkpoint.

    Skipping here rather than failing keeps the gap visible and named instead of appearing
    as a generic red test; test_repository_hygiene.py asserts the gap stays documented.
    """
    if not path.exists():
        pytest.skip(
            f"FULL_RETRAINING_REPRODUCIBILITY gap: {path.name} is git-ignored and not "
            "retrievable from a clean clone (see PROVENANCE_GAPS.md §1). The frozen MD "
            "handoff is unaffected; end-to-end retraining is NOT reproducible.")


def _optional(path: Path) -> None:
    if not path.exists():
        pytest.skip(f"historical optional checkpoint not present in canonical tree: {path}")


def test_small_checkpoint_loads():
    _optional(CKPT_SMALL)
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
    _optional(CKPT_V3F)
    model = PocketGNNXL()
    state = torch.load(str(CKPT_V3F), map_location="cpu", weights_only=True)
    model.load_state_dict(state)


def test_checkpoint_keys_are_state_dict():
    """Verify checkpoints are pure state dicts, not wrapped in extra keys."""
    for ckpt in [p for p in [CKPT_SMALL, CKPT_V3, CKPT_V3F] if p.exists()]:
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
