"""The positive-control gate must not be satisfiable by a static structure plus noise.

FROZEN_MD_ANALYSIS_PROTOCOL.json states, as a negative_diagnostic:

    "starting structures differ plus tiny random coordinate noise must fail because static
     separation alone is not dynamic validation"

trajectory_dynamic_control_gate_v1 violated that. Reproduced against b4d9d7c on 2026-08-16:
8GLA's frozen static reference already exceeds BOTH midpoint openness thresholds
(SASA 839.109 >= 808.568 A^2; CA hull 610.253 >= 560.687 A^3), so a motionless 8GLA run scores
open_like_fraction = 1.0 from frame zero, and IID jitter of 0.10 A/axis gives RMSF 0.0174 nm,
clearing the 0.015 nm floor. Three such "trajectories" passed the gate with zero issues.

These tests drive the REAL analyzer over REAL DCD files and assert the repaired behaviour.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "md_validation_4070"
sys.path.insert(0, str(ROOT / "tests"))

import md_synthetic as syn  # noqa: E402


def _load_analyze():
    spec = importlib.util.spec_from_file_location("analyze_md_under_test", MD / "analyze_md.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["analyze_md_under_test"] = mod
    spec.loader.exec_module(mod)
    return mod


an = _load_analyze()

REGIONS = {"core_3of3": syn.CORE_RESSEQ, "supported_ge2of3": syn.POCKET_RESSEQ}
IFACE = [0]


def _analyze(tmp_path: Path, kind: str, *, n_reps=3, open_scale=1.0, thresholds=None,
             n_frames=syn.N_FRAMES_5NS):
    """Build n_reps synthetic control replicates and run the production analysis path."""
    rows = []
    root = tmp_path / kind
    for i in range(1, n_reps + 1):
        traj, _ = syn.make_trajectory(kind, n_frames=n_frames, seed=i, open_scale=open_scale)
        rep = syn.write_replicate(root, "8GLA", f"rep{i:02d}", traj)
        done = json.loads((rep / "DONE.json").read_text())
        r = an.analyze_replicate(
            rep / "production.dcd", root / "8GLA" / "system_solvated.pdb",
            syn.POCKET_RESSEQ, IFACE, regions=REGIONS,
            thresholds=thresholds if thresholds is not None else _permissive_thresholds(),
            done_payload=done,
        )
        r.update({"role": "control", "pdb": "8GLA", "replicate": f"rep{i:02d}",
                  "completion_status": "PASS"})
        rows.append(r)
    return rows


_THRESHOLD_CACHE: dict = {}


def _permissive_thresholds():
    """Thresholds the STATIC structure already satisfies -- exactly 8GLA's real situation.

    Calibrated once from a static frame so the openness criterion alone cannot fail the
    static-noise case. This is the point of the test: openness must not be the only
    discriminator.
    """
    if "v" in _THRESHOLD_CACHE:
        return _THRESHOLD_CACHE["v"]
    _THRESHOLD_CACHE["v"] = {"supported_sasa_A2": 0.0,
                             "supported_ca_convex_hull_volume_A3": 0.0}
    return _THRESHOLD_CACHE["v"]


def _strict_thresholds_from(rows):
    """Thresholds ABOVE the observed values -- the closed (1W60-like) starting state."""
    s = max(r["regions"]["supported_ge2of3"]["sasa_max_A2"] for r in rows)
    h = max(r["regions"]["supported_ge2of3"]["ca_convex_hull_volume_max_A3"] for r in rows)
    return {"supported_sasa_A2": s * 1.5, "supported_ca_convex_hull_volume_A3": h * 1.5}


# --------------------------------------------------------------------------------------
# The three required cases
# --------------------------------------------------------------------------------------
def test_static_8gla_plus_noise_fails_gate_v2(tmp_path):
    """Static 8GLA-like structure + realistic 0.10 A jitter -> FAIL."""
    rows = _analyze(tmp_path, "static_noise", open_scale=1.35)
    gate = an.evaluate_control_interpretability(rows)

    # Precondition: this really is the pathological case -- it starts open and stays open,
    # and it clears the v1 RMSF floor. Otherwise the test would pass for the wrong reason.
    for r in rows:
        assert r["openness"]["available"] is True
        assert r["openness"]["open_like_fraction"] == 1.0, "static case must read fully open"
        assert r["pocket_rmsf_mean_nm"] >= an.CONTROL_MIN_RMSF_NM, (
            "static jitter must clear the v1 RMSF floor, else v1 was not actually broken")

    assert gate["name"] == "trajectory_dynamic_control_gate_v2"
    assert gate["status"] == "FAIL", (
        "static structure + per-frame noise passed the positive-control gate: "
        f"{json.dumps(gate['per_replicate'], indent=2)}")
    assert gate["interpretable"] is False
    joined = " ".join(gate["issues"])
    assert "D1" in joined and "D2" in joined, (
        f"both dynamic discriminators must reject IID noise; issues were: {gate['issues']}")


def test_genuinely_dynamic_trajectory_passes_gate_v2(tmp_path):
    """A genuinely dynamic opening/closing trajectory -> PASS when its criteria are met."""
    rows = _analyze(tmp_path, "dynamic", open_scale=1.35)
    gate = an.evaluate_control_interpretability(rows)
    assert gate["status"] == "PASS", (
        "a genuinely dynamic, open-like, artifact-free control must pass; issues: "
        f"{gate['issues']}")
    assert gate["interpretable"] is True
    assert gate["qualifying_control_replicates"] == 3


def test_static_1w60_plus_noise_fails_gate_v2(tmp_path):
    """Static apo-like (closed) structure + the same noise -> FAIL, and for both reasons."""
    rows = _analyze(tmp_path, "static_noise", open_scale=1.0)
    strict = _strict_thresholds_from(rows)
    rows = _analyze(tmp_path / "closed", "static_noise", open_scale=1.0, thresholds=strict)
    gate = an.evaluate_control_interpretability(rows)
    assert gate["status"] == "FAIL"
    joined = " ".join(gate["issues"])
    assert "open-like fraction" in joined, "a closed starting state must fail openness"
    assert "D1" in joined, "a static structure must also fail the temporal discriminator"


# --------------------------------------------------------------------------------------
# Regression witnesses: the specific v1 defect, and the discriminator mathematics
# --------------------------------------------------------------------------------------
def test_v1_criteria_alone_would_have_accepted_static_noise(tmp_path):
    """Document the exact defect: the v1 criteria are satisfied by the static-noise case."""
    rows = _analyze(tmp_path, "static_noise", open_scale=1.35)
    v1_qualifying = sum(
        1 for r in rows
        if r["pocket_rmsf_mean_nm"] >= an.CONTROL_MIN_RMSF_NM
        and r["openness"]["open_like_fraction"] >= an.CONTROL_MIN_OPEN_LIKE_FRACTION
    )
    assert v1_qualifying == 3, (
        "the v1 criteria (RMSF floor + open-like fraction) must still be shown to accept "
        "static noise -- that is the defect v2 exists to fix")
    assert an.evaluate_control_interpretability(rows)["status"] == "FAIL"


def test_dynamic_discriminators_separate_noise_from_motion(tmp_path):
    """D1/D2 must sit below the IID null for noise and above it for real motion."""
    noise = _analyze(tmp_path / "n", "static_noise", open_scale=1.35)
    motion = _analyze(tmp_path / "m", "dynamic", open_scale=1.35)
    n_frames = noise[0]["dynamics"]["n_production_frames"]
    r1_thr = an.autocorrelation_null_threshold(n_frames)
    dccm_thr = an.dccm_null_threshold(n_frames)

    for r in noise:
        assert r["dynamics"]["hull_volume_lag1_autocorrelation"] < r1_thr
        assert r["dynamics"]["region_internal_mean_abs_dccm"] < dccm_thr
    for r in motion:
        assert r["dynamics"]["hull_volume_lag1_autocorrelation"] >= r1_thr
        assert r["dynamics"]["region_internal_mean_abs_dccm"] >= dccm_thr


def test_static_noise_surrogate_is_reported(tmp_path):
    """The matched static+noise null must be reported next to the real statistics."""
    rows = _analyze(tmp_path, "dynamic", open_scale=1.35)
    sur = rows[0]["dynamics"]["static_noise_surrogate"]
    assert sur is not None and "error" not in sur
    assert sur["hull_volume_lag1_autocorrelation"] is not None
    assert sur["hull_volume_lag1_autocorrelation"] < \
        rows[0]["dynamics"]["hull_volume_lag1_autocorrelation"]


def test_lag1_autocorrelation_reference_cases():
    assert an.lag1_autocorrelation([1.0, 1.0, 1.0]) is None          # constant -> undefined
    assert an.lag1_autocorrelation([1.0]) is None                    # too short
    ramp = an.lag1_autocorrelation(np.arange(200.0))
    assert ramp > 0.95
    iid = an.lag1_autocorrelation(np.random.default_rng(3).normal(size=5000))
    assert abs(iid) < 0.1
    alternating = an.lag1_autocorrelation([1.0, -1.0] * 100)
    assert alternating < -0.9


def test_null_thresholds_scale_with_sampling():
    """Thresholds are derived from N, so they cannot be relaxed by choosing a run length."""
    assert an.autocorrelation_null_threshold(100) == pytest.approx(0.3)
    assert an.autocorrelation_null_threshold(10_000) == pytest.approx(0.03)
    assert an.dccm_null_threshold(100) == pytest.approx(3.0 * (2 / np.pi) ** 0.5 / 10.0)
    assert an.autocorrelation_null_threshold(0) is None
    assert an.dccm_null_threshold(2) is None


def test_gate_requires_three_replicates(tmp_path):
    rows = _analyze(tmp_path, "dynamic", n_reps=2, open_scale=1.35)
    gate = an.evaluate_control_interpretability(rows)
    assert gate["status"] == "FAIL"
    assert any("control replicates 2 < 3" in i for i in gate["issues"])
