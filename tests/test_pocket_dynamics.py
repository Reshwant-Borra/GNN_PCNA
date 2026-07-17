"""Guardrail tests for the MD pocket-dynamics self-validating verdict.

The whole point of this module: an MD analysis that is BROKEN (e.g. whole-trimer
misalignment giving a ~27 Å backbone RMSD) must NEVER be reported as a genuine
'no dynamics' negative. These tests pin that three-way classification so the
failure can't silently return.
"""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))


def _load_classifier():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "run_md_analysis", REPO / "scripts" / "run_md_analysis.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.classify_dynamics


classify_dynamics = _load_classifier()


def test_broken_analysis_is_invalid_not_negative():
    """Whole-trimer misalignment (huge RMSD) → INVALID_ANALYSIS, never a negative."""
    agg = {"backbone_rmsd_mean_A": 27.0, "pbc_sane": False,
           "vol_range_A3": 5.0, "sasa_range_A2": 2.0, "mouth_122-232_range_A": 0.1}
    code, msg = classify_dynamics(agg)
    assert code == "INVALID_ANALYSIS"
    assert "not a negative" in msg.lower()


def test_real_dynamics_detected():
    """The corrected 1AXC numbers → DYNAMICS."""
    agg = {"backbone_rmsd_mean_A": 1.65, "pbc_sane": True,
           "vol_range_A3": 429.0, "sasa_range_A2": 313.0, "mouth_122-232_range_A": 5.44}
    code, _ = classify_dynamics(agg)
    assert code == "DYNAMICS"


def test_verified_sane_negative():
    """Sane alignment but flat metrics → VALID_NEGATIVE (a trustworthy negative)."""
    agg = {"backbone_rmsd_mean_A": 2.0, "pbc_sane": True,
           "vol_range_A3": 20.0, "sasa_range_A2": 10.0, "mouth_122-232_range_A": 0.3}
    code, _ = classify_dynamics(agg)
    assert code == "VALID_NEGATIVE"


def test_nan_rmsd_is_invalid():
    agg = {"backbone_rmsd_mean_A": float("nan"), "pbc_sane": True,
           "vol_range_A3": 400.0, "sasa_range_A2": 300.0, "mouth_122-232_range_A": 5.0}
    code, _ = classify_dynamics(agg)
    assert code == "INVALID_ANALYSIS"


def test_single_strong_signal_counts_as_dynamics():
    """Any one metric well above the floor (here just the mouth) → DYNAMICS."""
    agg = {"backbone_rmsd_mean_A": 2.2, "pbc_sane": True,
           "vol_range_A3": 40.0, "sasa_range_A2": 30.0, "mouth_122-232_range_A": 4.0}
    code, _ = classify_dynamics(agg)
    assert code == "DYNAMICS"


def test_pocket_residue_sets_are_chain_aware():
    """The eval GT set is asymmetric (A,B only); chain C must not be in it."""
    from src.md.parse_trajectory import AOH_GT_BY_CHAIN, MD_POCKET_RESSEQ
    assert set(AOH_GT_BY_CHAIN) == {0, 1}          # no chain C in ground truth
    assert len(MD_POCKET_RESSEQ) == 24             # canonical per-chain MD set


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
