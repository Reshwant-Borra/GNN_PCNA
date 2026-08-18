"""Missing inputs must make metrics UNAVAILABLE, never silently produce a scientific claim.

Reproduced 2026-08-16 against b4d9d7c:
  * convex_hull_volume_A3 swallowed ImportError and returned NaN. Downstream, the openness
    mask (sasa >= t) & (hull >= t) was all-False because NaN >= x is False, so a machine
    without scipy reported openness = {"available": true, "open_like_fraction": 0.0} --
    a missing optional dependency became the scientific claim "the pocket never opened".
  * _parse_log_times returned [] for a missing, unreadable or malformed log, and the caller
    tested `if times and ...`, so duplicate-time and output-interval validation were silently
    SKIPPED rather than failed.
"""
from __future__ import annotations

import builtins
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "md_validation_4070"
sys.path.insert(0, str(ROOT / "tests"))

import md_synthetic as syn  # noqa: E402


def _load():
    spec = importlib.util.spec_from_file_location("analyze_md_failclosed", MD / "analyze_md.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["analyze_md_failclosed"] = mod
    spec.loader.exec_module(mod)
    return mod


an = _load()
REGIONS = {"core_3of3": syn.CORE_RESSEQ, "supported_ge2of3": syn.POCKET_RESSEQ}
PERMISSIVE = {"supported_sasa_A2": 0.0, "supported_ca_convex_hull_volume_A3": 0.0}


@pytest.fixture
def no_scipy(monkeypatch):
    real = builtins.__import__

    def blocked(name, *a, **k):
        if name.startswith("scipy"):
            raise ImportError("No module named 'scipy' (simulated)")
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", blocked)
    return None


# --------------------------------------------------------------------------------------
# L1: missing scipy
# --------------------------------------------------------------------------------------
def test_hull_backend_availability_is_explicit(no_scipy):
    ok, why = an.hull_backend_available()
    assert ok is False
    assert "scipy" in why


def test_convex_hull_raises_instead_of_returning_nan(no_scipy):
    import numpy as np
    with pytest.raises(an.HullDependencyUnavailable):
        an.convex_hull_volume_A3(np.eye(4)[:, :3], np)


def test_degenerate_geometry_is_nan_not_an_error():
    """Genuine geometric degeneracy is a property of the data, not a broken environment."""
    import numpy as np
    assert np.isnan(an.convex_hull_volume_A3(np.zeros((3, 3)), np))          # <4 points
    coplanar = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [1., 1., 0.]])
    assert np.isnan(an.convex_hull_volume_A3(coplanar, np))                  # coplanar


def test_openness_is_unavailable_without_scipy(tmp_path, no_scipy):
    traj, _ = syn.make_trajectory("dynamic", seed=1, open_scale=1.35)
    rep = syn.write_replicate(tmp_path, "8GLA", "rep01", traj)
    done = json.loads((rep / "DONE.json").read_text())
    r = an.analyze_replicate(rep / "production.dcd",
                             tmp_path / "8GLA" / "system_solvated.pdb",
                             syn.POCKET_RESSEQ, [0], regions=REGIONS,
                             thresholds=PERMISSIVE, done_payload=done)
    assert r["openness"]["available"] is False, (
        "a missing convex-hull backend must make openness UNAVAILABLE, not 0.0")
    assert "scipy" in r["openness"]["reason"]
    assert "open_like_fraction" not in r["openness"], (
        "an unavailable metric must not emit a value at all")


def test_gate_fails_closed_when_openness_is_unavailable(tmp_path, no_scipy):
    rows = []
    for i in (1, 2, 3):
        traj, _ = syn.make_trajectory("dynamic", seed=i, open_scale=1.35)
        rep = syn.write_replicate(tmp_path / f"r{i}", "8GLA", f"rep{i:02d}", traj)
        done = json.loads((rep / "DONE.json").read_text())
        r = an.analyze_replicate(rep / "production.dcd",
                                 tmp_path / f"r{i}" / "8GLA" / "system_solvated.pdb",
                                 syn.POCKET_RESSEQ, [0], regions=REGIONS,
                                 thresholds=PERMISSIVE, done_payload=done)
        r.update({"role": "control", "pdb": "8GLA", "replicate": f"rep{i:02d}",
                  "completion_status": "PASS"})
        rows.append(r)
    gate = an.evaluate_control_interpretability(rows)
    assert gate["status"] == "FAIL"
    assert any("openness unavailable" in i for i in gate["issues"])
    assert any("D1" in i for i in gate["issues"]), \
        "the hull-based discriminator must also report unavailable, not pass"


# --------------------------------------------------------------------------------------
# L2: unreadable / missing / malformed production.log
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize("setup,expected", [
    (lambda p: None, "missing"),
    (lambda p: p.write_text("", encoding="utf-8"), "empty"),
    (lambda p: p.write_text("no header here\n1\t2\n", encoding="utf-8"), "no_time_column"),
    (lambda p: p.write_text('#"Step"\t"Time (ps)"\n', encoding="utf-8"), "no_time_rows"),
])
def test_log_parse_status_is_explicit(tmp_path, setup, expected):
    log = tmp_path / "production.log"
    setup(log)
    times, status = an.read_log_times(log)
    assert status == expected
    assert times == []


def test_unreadable_log_fails_validation(tmp_path):
    traj, _ = syn.make_trajectory("dynamic", seed=1)
    rep = syn.write_replicate(tmp_path, "8GLA", "rep01", traj, write_log=False)
    result = an.validate_scientific_replicate(rep, expected_pdb="8GLA", expected_role="control")
    assert result["ok"] is False
    assert any("production.log unusable" in i for i in result["issues"])
    assert result["log_status"] == "missing"


def test_duplicate_log_times_fail_validation(tmp_path):
    traj, _ = syn.make_trajectory("dynamic", seed=1)
    rep = syn.write_replicate(tmp_path, "8GLA", "rep01", traj)
    log = rep / "production.log"
    lines = log.read_text().splitlines()
    lines.append(lines[-1])                      # duplicate the final sample
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = an.validate_scientific_replicate(rep, expected_pdb="8GLA", expected_role="control")
    assert result["ok"] is False
    assert any("duplicate log times" in i for i in result["issues"])


def test_irregular_output_interval_fails_validation(tmp_path):
    traj, _ = syn.make_trajectory("dynamic", seed=1)
    rep = syn.write_replicate(tmp_path, "8GLA", "rep01", traj)
    log = rep / "production.log"
    lines = log.read_text().splitlines()
    parts = lines[5].split("\t")
    parts[2] = "12345.0"                          # break the cadence
    lines[5] = "\t".join(parts)
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = an.validate_scientific_replicate(rep, expected_pdb="8GLA", expected_role="control")
    assert result["ok"] is False
    assert any("output interval inconsistent" in i for i in result["issues"])


# --------------------------------------------------------------------------------------
# Completion enforcement
# --------------------------------------------------------------------------------------
def test_truncated_trajectory_is_rejected(tmp_path):
    traj, _ = syn.make_trajectory("dynamic", seed=1)
    rep = syn.write_replicate(tmp_path, "8GLA", "rep01", traj, truncate_frames=40)
    result = an.validate_scientific_replicate(rep, expected_pdb="8GLA", expected_role="control")
    assert result["ok"] is False
    assert any("truncated" in i for i in result["issues"])


def test_missing_done_is_rejected(tmp_path):
    traj, _ = syn.make_trajectory("dynamic", seed=1)
    rep = syn.write_replicate(tmp_path, "8GLA", "rep01", traj, write_done=False)
    result = an.validate_scientific_replicate(rep, expected_pdb="8GLA", expected_role="control")
    assert result["ok"] is False
    assert any("DONE.json missing" in i for i in result["issues"])


def test_failed_json_is_rejected(tmp_path):
    traj, _ = syn.make_trajectory("dynamic", seed=1)
    rep = syn.write_replicate(tmp_path, "8GLA", "rep01", traj)
    (rep / "FAILED.json").write_text(json.dumps({"reason": "blew up"}), encoding="utf-8")
    result = an.validate_scientific_replicate(rep, expected_pdb="8GLA", expected_role="control")
    assert result["ok"] is False
    assert any("FAILED.json present" in i for i in result["issues"])


def test_role_and_pdb_mismatch_are_rejected(tmp_path):
    traj, _ = syn.make_trajectory("dynamic", seed=1)
    rep = syn.write_replicate(tmp_path, "8GLA", "rep01", traj, role="control")
    result = an.validate_scientific_replicate(rep, expected_pdb="1W60", expected_role="apo")
    assert result["ok"] is False
    assert any("pdb identity mismatch" in i for i in result["issues"])
    assert any("role mismatch" in i for i in result["issues"])


def test_a_fully_valid_replicate_passes(tmp_path):
    traj, _ = syn.make_trajectory("dynamic", seed=1)
    rep = syn.write_replicate(tmp_path, "8GLA", "rep01", traj)
    result = an.validate_scientific_replicate(rep, expected_pdb="8GLA", expected_role="control")
    assert result["ok"] is True, result["issues"]


# --------------------------------------------------------------------------------------
# L3: cadence tolerance (2026-08-18 repair)
#
# OpenMM's StateDataReporter "Time (ps)" column is an accumulated float. Two adjacent
# intervals that are the SAME nominal cadence can land on different floats purely from
# floating-point accumulation -- e.g. a real Control-20 resume produced adjacent intervals
# of 49.99999999881766 ps and 50.00000001018634 ps for a declared 50.0 ps cadence. The old
# check compared diffs to EACH OTHER via round(diff, 9) + len(set(diffs)) > 1, so any such
# pair was rejected as "output interval inconsistent" even though both are the same cadence
# to 9 decimal places. The repaired check compares each diff against the authoritative
# DONE.json report_ps with a tolerance instead.
# --------------------------------------------------------------------------------------
def _write_log_with_times(rep_dir: Path, times: list[float], start_step: int = 12500,
                          step_spacing: int = 12500) -> None:
    lines = ['#"Progress (%)"\t"Step"\t"Time (ps)"\t"Potential Energy (kJ/mole)"'
             '\t"Temperature (K)"\t"Density (g/mL)"']
    for i, t in enumerate(times):
        step = start_step + i * step_spacing
        lines.append(f"{100.0 * (i + 1) / len(times):.1f}\t{step}\t{t:.10f}\t-1.5e6\t310.1\t1.010")
    (rep_dir / "production.log").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_exact_cadence_passes_validation(tmp_path):
    traj, _ = syn.make_trajectory("dynamic", seed=1)
    rep = syn.write_replicate(tmp_path, "8GLA", "rep01", traj)          # report_ps=50.0
    _write_log_with_times(rep, [50.0 * i for i in range(1, 21)])
    result = an.validate_scientific_replicate(rep, expected_pdb="8GLA", expected_role="control")
    assert result["ok"] is True, result["issues"]


def test_tiny_floating_point_cadence_drift_passes_validation(tmp_path):
    """The exact real-world Control-20 boundary values that exposed the bug must pass."""
    traj, _ = syn.make_trajectory("dynamic", seed=1)
    rep = syn.write_replicate(tmp_path, "8GLA", "rep01", traj)          # report_ps=50.0
    times = [0.0, 49.99999999881766, 49.99999999881766 + 50.00000001018634, ]
    _write_log_with_times(rep, times)
    result = an.validate_scientific_replicate(rep, expected_pdb="8GLA", expected_role="control")
    assert result["ok"] is True, result["issues"]
    assert not any("output interval" in i for i in result["issues"])


def test_resumed_style_log_with_400_rows_and_fp_drift_passes_validation(tmp_path):
    """Reproduces the real Control-20 evidence: 400 rows, 12,500-step spacing, 50 ps nominal
    cadence with float64-accumulation-scale drift on every adjacent interval."""
    import numpy as np
    traj, _ = syn.make_trajectory("dynamic", seed=1)
    rep = syn.write_replicate(tmp_path, "8GLA", "rep01", traj)          # report_ps=50.0
    rng = np.random.default_rng(20260817)
    dt_ps_exact = 0.004                        # 4 fs timestep -> ps/step
    base_step = 512500
    n_rows = 400
    step_spacing = 12500
    times = []
    for i in range(n_rows):
        step = base_step + i * step_spacing
        jitter = float(rng.uniform(-1.2e-8, 1.2e-8))
        times.append(step * dt_ps_exact + jitter)
    _write_log_with_times(rep, times, start_step=base_step, step_spacing=step_spacing)
    result = an.validate_scientific_replicate(rep, expected_pdb="8GLA", expected_role="control")
    assert result["ok"] is True, result["issues"]


def test_real_100ps_discontinuity_fails_validation(tmp_path):
    traj, _ = syn.make_trajectory("dynamic", seed=1)
    rep = syn.write_replicate(tmp_path, "8GLA", "rep01", traj)          # report_ps=50.0
    times = [50.0, 100.0, 200.0, 250.0]        # one 100 ps gap
    _write_log_with_times(rep, times)
    result = an.validate_scientific_replicate(rep, expected_pdb="8GLA", expected_role="control")
    assert result["ok"] is False
    assert any("output interval inconsistent" in i for i in result["issues"])


def test_real_25ps_discontinuity_fails_validation(tmp_path):
    traj, _ = syn.make_trajectory("dynamic", seed=1)
    rep = syn.write_replicate(tmp_path, "8GLA", "rep01", traj)          # report_ps=50.0
    times = [50.0, 100.0, 125.0, 175.0]        # one 25 ps gap
    _write_log_with_times(rep, times)
    result = an.validate_scientific_replicate(rep, expected_pdb="8GLA", expected_role="control")
    assert result["ok"] is False
    assert any("output interval inconsistent" in i for i in result["issues"])


def test_non_monotonic_log_times_fail_validation(tmp_path):
    traj, _ = syn.make_trajectory("dynamic", seed=1)
    rep = syn.write_replicate(tmp_path, "8GLA", "rep01", traj)          # report_ps=50.0
    times = [50.0, 100.0, 80.0, 130.0]         # time goes backwards
    _write_log_with_times(rep, times)
    result = an.validate_scientific_replicate(rep, expected_pdb="8GLA", expected_role="control")
    assert result["ok"] is False
    assert any("output interval inconsistent" in i for i in result["issues"])


def test_missing_report_ps_fails_closed(tmp_path):
    traj, _ = syn.make_trajectory("dynamic", seed=1)
    rep = syn.write_replicate(tmp_path, "8GLA", "rep01", traj)
    done_path = rep / "DONE.json"
    done = json.loads(done_path.read_text())
    del done["report_ps"]
    done_path.write_text(json.dumps(done), encoding="utf-8")
    result = an.validate_scientific_replicate(rep, expected_pdb="8GLA", expected_role="control")
    assert result["ok"] is False
    assert any("report_ps is missing or invalid" in i for i in result["issues"])


def test_invalid_report_ps_fails_closed(tmp_path):
    traj, _ = syn.make_trajectory("dynamic", seed=1)
    rep = syn.write_replicate(tmp_path, "8GLA", "rep01", traj)
    done_path = rep / "DONE.json"
    done = json.loads(done_path.read_text())
    done["report_ps"] = 0.0
    done_path.write_text(json.dumps(done), encoding="utf-8")
    result = an.validate_scientific_replicate(rep, expected_pdb="8GLA", expected_role="control")
    assert result["ok"] is False
    assert any("report_ps is missing or invalid" in i for i in result["issues"])
