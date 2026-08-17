"""The 0.1 ns smoke gate must pass a complete smoke and fail a truncated one.

run_md.py accumulates production time as (total_steps - equil_steps) * dt_ns with
dt_ns = 4.0/1e6. Reproduced 2026-08-16: a COMPLETE 0.1 ns smoke writes
production_ns = 0.09999999999999999, while md_workflow.stage_status tested
`float(production_ns) >= 0.1`, which is False. A perfectly valid smoke could never satisfy
its own gate, so the workflow would sit at PENDING forever.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "md_validation_4070"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


wf = _load("md_workflow_ns", MD / "md_workflow.py")

TIMESTEP_FS = 4.0
DT_NS = TIMESTEP_FS / 1_000_000.0
STEPS_PER_NS = int(round(1.0 / DT_NS))


def _done_for(target_ns: float, *, achieved_ns: float | None = None, integer_steps=True,
              equil_ns=2.0):
    """Build a DONE.json payload exactly as run_md.py computes it."""
    achieved_ns = target_ns if achieved_ns is None else achieved_ns
    equil_steps = int(round(equil_ns * STEPS_PER_NS))
    target_steps = int(round(target_ns * STEPS_PER_NS))
    prod_steps = int(round(achieved_ns * STEPS_PER_NS))
    payload = {
        "production_ns": max(0.0, (equil_steps + prod_steps - equil_steps) * DT_NS),
        "timestep_fs": TIMESTEP_FS,
        "sanity_gate": "passed: finite energy+coords",
    }
    if integer_steps:
        payload["production_steps"] = prod_steps
        payload["target_production_steps"] = target_steps
    return payload


def test_exact_float_pathology_still_exists_in_the_raw_value():
    """The underlying float is genuinely 0.09999999999999999; we fixed the COMPARISON."""
    done = _done_for(0.1)
    assert done["production_ns"] == 0.09999999999999999
    assert (done["production_ns"] >= 0.1) is False, "the naive literal comparison still fails"


def test_complete_smoke_passes():
    assert wf.meets_ns_target(_done_for(0.1), 0.1) is True
    assert wf.meets_ns_target(_done_for(0.1, integer_steps=False), 0.1) is True


@pytest.mark.parametrize("target", [0.1, 0.2, 5.0, 100.0, 0.02])
def test_complete_run_passes_at_every_documented_duration(target):
    assert wf.meets_ns_target(_done_for(target), target) is True
    assert wf.meets_ns_target(_done_for(target, integer_steps=False), target) is True


@pytest.mark.parametrize("achieved", [0.0, 0.05, 0.09, 0.0999])
def test_truncated_smoke_still_fails(achieved):
    assert wf.meets_ns_target(_done_for(0.1, achieved_ns=achieved), 0.1) is False
    assert wf.meets_ns_target(
        _done_for(0.1, achieved_ns=achieved, integer_steps=False), 0.1) is False


def test_one_step_short_fails():
    """The boundary: exactly one integration step short must not pass."""
    done = _done_for(0.1)
    done["production_steps"] -= 1
    done["production_ns"] = done["production_steps"] * DT_NS
    assert wf.meets_ns_target(done, 0.1) is False


def test_tolerance_is_far_below_any_meaningful_shortfall():
    """1e-6 ns = 1 fs. A truncation that matters is many orders of magnitude larger."""
    assert wf.NS_TOLERANCE == pytest.approx(1e-6)
    one_step_ns = DT_NS                      # 4e-6 ns
    assert one_step_ns > wf.NS_TOLERANCE, "one step must exceed the tolerance"


def test_control5_duration_gate_uses_the_same_rule(tmp_path):
    outdir = tmp_path / "outputs"
    for rep in (1, 2, 3):
        d = outdir / "8GLA" / f"rep{rep:02d}"
        d.mkdir(parents=True)
        (d / "DONE.json").write_text(json.dumps(_done_for(5.0)), encoding="utf-8")
    ok, issues = wf.complete_reps(outdir, "8GLA", 3, 5.0)
    assert ok is True, issues


def test_control5_duration_gate_rejects_short_replicate(tmp_path):
    outdir = tmp_path / "outputs"
    for rep in (1, 2, 3):
        d = outdir / "8GLA" / f"rep{rep:02d}"
        d.mkdir(parents=True)
        payload = _done_for(5.0, achieved_ns=5.0 if rep != 2 else 4.5)
        (d / "DONE.json").write_text(json.dumps(payload), encoding="utf-8")
    ok, issues = wf.complete_reps(outdir, "8GLA", 3, 5.0)
    assert ok is False
    assert any("rep02" in i for i in issues)


def test_stage_status_smoke_gate_passes_for_complete_smoke(tmp_path):
    outdir = tmp_path / "outputs"
    rep = outdir / "8GLA" / "rep01"
    rep.mkdir(parents=True)
    (rep / "DONE.json").write_text(json.dumps(_done_for(0.1)), encoding="utf-8")
    assert wf.stage_status(outdir)["gates"]["smoke_0p1ns"] is True


def test_stage_status_smoke_gate_fails_for_truncated_smoke(tmp_path):
    outdir = tmp_path / "outputs"
    rep = outdir / "8GLA" / "rep01"
    rep.mkdir(parents=True)
    (rep / "DONE.json").write_text(json.dumps(_done_for(0.1, achieved_ns=0.05)),
                                   encoding="utf-8")
    assert wf.stage_status(outdir)["gates"]["smoke_0p1ns"] is False
