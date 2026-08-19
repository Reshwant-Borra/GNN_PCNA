"""Regression tests for the Control-20 forensic-audit reporting patches to analyze_md.py.

Context (see md_validation_4070/CONTROL20_FORENSIC_METHODOLOGY_AUDIT.md, section 18):
in the real Control-20 result, 8GLA/rep02 cleared BOTH dynamic discriminators by a wide margin
(D1 hull-volume lag-1 autocorrelation 0.395 vs an IID-null threshold of 0.173; D2 region-internal
mean |DCCM| 0.538 vs a threshold of 0.138) and its ONLY qualification failure was open-like
fraction 0.130 < the frozen 0.200 floor. The gate's "reason" field nonetheless read:

    "FAIL: control trajectories did not demonstrate trajectory-derived dynamics beyond static
     starting-state separation plus per-frame noise."

That statement is false for a replicate that positively rejected the static-noise null on both
discriminators. These tests pin the corrected behavior: the reason must name which situation
actually occurred, and must never fall back to the blanket "no dynamics" message when at least
one replicate rejected the IID-noise null. They also pin the companion fix to the replicate-level
95% CI, which previously used the large-sample z=1.96 approximation for as few as n=2-3
replicates instead of the correct Student's t critical value.

This file does not touch, and must not need to touch, gate PASS/FAIL outcomes, thresholds, or
per-replicate qualification -- only the human-readable "reason" text and the descriptive
aggregate CI are in scope.
"""
from __future__ import annotations

import importlib.util
import json
import math
import statistics
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "md_validation_4070"
sys.path.insert(0, str(ROOT / "tests"))

import md_synthetic as syn  # noqa: E402


def _load_analyze():
    spec = importlib.util.spec_from_file_location("analyze_md_reason_test", MD / "analyze_md.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["analyze_md_reason_test"] = mod
    spec.loader.exec_module(mod)
    return mod


an = _load_analyze()
REGIONS = {"core_3of3": syn.CORE_RESSEQ, "supported_ge2of3": syn.POCKET_RESSEQ}
IFACE = [0]


def _analyze(tmp_path: Path, kind: str, *, n_reps=3, open_scale=1.0, thresholds=None):
    rows = []
    root = tmp_path / kind
    for i in range(1, n_reps + 1):
        traj, _ = syn.make_trajectory(kind, n_frames=syn.N_FRAMES_5NS, seed=i, open_scale=open_scale)
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


_PERMISSIVE = {"supported_sasa_A2": 0.0, "supported_ca_convex_hull_volume_A3": 0.0}


def _permissive_thresholds():
    return _PERMISSIVE


def _strict_thresholds_from(rows):
    """Thresholds ABOVE the observed max -- guarantees open_like_fraction == 0."""
    s = max(r["regions"]["supported_ge2of3"]["sasa_max_A2"] for r in rows)
    h = max(r["regions"]["supported_ge2of3"]["ca_convex_hull_volume_max_A3"] for r in rows)
    return {"supported_sasa_A2": s * 1.5, "supported_ca_convex_hull_volume_A3": h * 1.5}


def test_fail_reason_names_dynamics_when_only_openness_fails(tmp_path):
    """kind='dynamic' trajectories genuinely move (D1/D2 must clear the IID-null thresholds),
    but thresholds set above their reach force open_like_fraction to 0 -- the rep02 pattern."""
    probe_rows = _analyze(tmp_path / "probe", "dynamic", open_scale=1.0)
    strict = _strict_thresholds_from(probe_rows)
    rows = _analyze(tmp_path / "strict", "dynamic", open_scale=1.0, thresholds=strict)
    gate = an.evaluate_control_interpretability(rows)

    for r in rows:
        assert r["openness"]["open_like_fraction"] == 0.0, "precondition: openness must fail"

    assert gate["status"] == "FAIL"
    assert gate["qualifying_control_replicates"] == 0
    assert gate["replicates_with_detected_dynamics"] == len(rows), (
        "precondition: this must be the 'dynamics detected but openness failed' case, not "
        f"the 'no dynamics at all' case -- per_replicate: {gate['per_replicate']}")
    assert "did not demonstrate trajectory-derived dynamics" not in gate["reason"], (
        f"blanket no-dynamics message must not fire when D1/D2 both cleared their "
        f"thresholds: {gate['reason']!r}")
    assert "demonstrated trajectory-derived" in gate["reason"]
    assert "open-like fraction" in gate["reason"]


def test_fail_reason_keeps_no_dynamics_message_when_truly_static(tmp_path):
    """The original blanket message is still correct, and must still be used, for the case it
    was written for: a static structure plus per-frame noise, which fails D1 too."""
    probe_rows = _analyze(tmp_path / "probe", "static_noise", open_scale=1.0)
    strict = _strict_thresholds_from(probe_rows)
    rows = _analyze(tmp_path / "strict", "static_noise", open_scale=1.0, thresholds=strict)
    gate = an.evaluate_control_interpretability(rows)

    assert gate["status"] == "FAIL"
    assert gate["replicates_with_detected_dynamics"] == 0
    assert gate["reason"] == (
        "FAIL: control trajectories did not demonstrate trajectory-derived dynamics beyond "
        "static starting-state separation plus per-frame noise."
    )


def test_pass_reason_text_unchanged(tmp_path):
    """The PASS message must be byte-identical to the pre-patch wording (no behavior change)."""
    rows = _analyze(tmp_path, "dynamic", open_scale=1.35)
    gate = an.evaluate_control_interpretability(rows)
    assert gate["status"] == "PASS"
    assert gate["reason"] == (
        "PASS: independent control trajectories are complete, artifact-free, open-like, and "
        "their motion is statistically distinguishable from a static structure with "
        "per-frame coordinate noise on both the temporal and collectivity discriminators."
    )


def test_t95_critical_value_matches_standard_table():
    assert an.t95_critical_value(1) == pytest.approx(12.706)
    assert an.t95_critical_value(2) == pytest.approx(4.303)
    assert an.t95_critical_value(29) == pytest.approx(2.045)
    assert an.t95_critical_value(1000) == pytest.approx(1.96)  # large-df limit


def test_aggregate_ci_uses_t_not_z_for_three_replicates():
    rows = [
        {"role": "control", "replicate": "rep01", "completion_status": "PASS",
         "openness": {"open_like_fraction": 0.10}, "convergence": {"overall_status": "OK"}},
        {"role": "control", "replicate": "rep02", "completion_status": "PASS",
         "openness": {"open_like_fraction": 0.20}, "convergence": {"overall_status": "OK"}},
        {"role": "control", "replicate": "rep03", "completion_status": "PASS",
         "openness": {"open_like_fraction": 0.30}, "convergence": {"overall_status": "OK"}},
    ]
    agg = an.aggregate_replicates(rows)["control"]
    vals = [0.10, 0.20, 0.30]
    mean = statistics.mean(vals)
    sd = statistics.stdev(vals)
    expected_half_t = 4.303 * sd / math.sqrt(3)
    expected_half_z = 1.96 * sd / math.sqrt(3)

    ci = agg["approx_95ci_across_replicates"]
    reported_half = ci[1] - mean
    assert reported_half == pytest.approx(expected_half_t, rel=1e-3)
    assert reported_half != pytest.approx(expected_half_z, rel=1e-3)
    assert agg["approx_95ci_method"] == "t95(df=2)=4.303"
