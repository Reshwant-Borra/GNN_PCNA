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
