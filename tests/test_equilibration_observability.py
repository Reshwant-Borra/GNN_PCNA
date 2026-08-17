"""Equilibration must be observable and must be evaluated against the frozen criteria.

Reproduced 2026-08-16 against b4d9d7c: run_replicate() did

    if equil_steps > 0:
        sim.step(equil_steps)          # <-- 2 ns integrated here
    ...
    sim.reporters.append(DCDReporter(...))          # <-- reporters attached AFTER
    sim.reporters.append(StateDataReporter(...))

so not one of the quantities named in EQUILIBRATION_ACCEPTANCE_CRITERIA.json (temperature,
density, potential energy, box volume) was ever recorded during equilibration, and a failure
in those 2 ns escaped as a bare traceback with no FAILED.json or STATUS.json.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "md_validation_4070"


def _load():
    spec = importlib.util.spec_from_file_location("run_md_equil", MD / "run_md.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_md_equil"] = mod
    spec.loader.exec_module(mod)
    return mod


rm = _load()
CRITERIA = json.loads((MD / "EQUILIBRATION_ACCEPTANCE_CRITERIA.json").read_text())

HEADER = ('#"Progress (%)"\t"Step"\t"Time (ps)"\t"Potential Energy (kJ/mole)"\t'
          '"Kinetic Energy (kJ/mole)"\t"Total Energy (kJ/mole)"\t"Temperature (K)"\t'
          '"Box Volume (nm^3)"\t"Density (g/mL)"\t"Speed (ns/day)"\t"Time Remaining"')


def _log(tmp_path, n=50, temp=310.0, density=1.01, pe=-1.5e6, volume=900.0,
         pe_drift=0.0, temp_drift=0.0, volume_jump_at=None):
    rows = [HEADER]
    for i in range(n):
        t = temp + temp_drift * i
        p = pe + pe_drift * i
        v = volume
        if volume_jump_at is not None and i >= volume_jump_at:
            v = volume * 0.4                       # box collapse
        rows.append(f"{100.0*i/n:.1f}\t{i*100}\t{i*0.4:.4f}\t{p:.1f}\t1.0e5\t{p+1e5:.1f}"
                    f"\t{t:.2f}\t{v:.2f}\t{density:.4f}\t50.0\t--")
    path = tmp_path / "equilibration.log"
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


# --------------------------------------------------------------------------------------
# What is now recorded, and how acceptance is computed
# --------------------------------------------------------------------------------------
def test_healthy_equilibration_is_accepted(tmp_path):
    rep = rm.evaluate_equilibration(_log(tmp_path), CRITERIA, 0.12, 2.0)
    assert rep["accepted"] is True, rep["failures"]
    assert rep["log_status"] == "ok"
    assert rep["samples"] == 50


def test_every_documented_criterion_is_actually_evaluated(tmp_path):
    """Each acceptance criterion must map to a check that ran, or say why it cannot."""
    rep = rm.evaluate_equilibration(_log(tmp_path), CRITERIA, 0.12, 2.0)
    for name in ("temperature_mean_in_range", "temperature_no_runaway", "temperature_finite",
                 "density_final_in_range", "potential_energy_finite",
                 "potential_energy_no_runaway", "box_volume_finite_positive",
                 "box_volume_no_discontinuity", "backbone_rmsd_within_limits"):
        assert name in rep["checks"], f"{name} was never evaluated"
        assert rep["checks"][name]["evaluated"] is True
        assert rep["checks"][name]["detail"]


def test_pressure_is_declared_not_evaluable_rather_than_passing(tmp_path):
    """OpenMM exposes no instantaneous pressure; that must be stated, not silently passed."""
    rep = rm.evaluate_equilibration(_log(tmp_path), CRITERIA, 0.12, 2.0)
    check = rep["checks"]["pressure_mean_in_range"]
    assert check["evaluated"] is False
    assert check["pass"] is None
    assert "not evaluable" in check["detail"].lower() or "no instantaneous" in check["detail"]


@pytest.mark.parametrize("kwargs,expected", [
    ({"temp": 250.0}, "temperature_mean_in_range"),
    ({"temp_drift": 1.5}, "temperature_no_runaway"),
    ({"density": 0.5}, "density_final_in_range"),
    ({"pe_drift": 5e5}, "potential_energy_no_runaway"),
    ({"volume_jump_at": 30}, "box_volume_no_discontinuity"),
])
def test_each_failure_mode_is_caught(tmp_path, kwargs, expected):
    rep = rm.evaluate_equilibration(_log(tmp_path, **kwargs), CRITERIA, 0.12, 2.0)
    assert rep["accepted"] is False
    assert rep["checks"][expected]["pass"] is False
    assert any(expected in f for f in rep["failures"])


def test_backbone_rmsd_fail_threshold(tmp_path):
    ok = rm.evaluate_equilibration(_log(tmp_path), CRITERIA, 0.45, 2.0)
    assert ok["accepted"] is True and not ok["warnings"]
    warn = rm.evaluate_equilibration(_log(tmp_path), CRITERIA, 0.75, 2.0)
    assert warn["accepted"] is True and warn["warnings"]
    fail = rm.evaluate_equilibration(_log(tmp_path), CRITERIA, 1.5, 2.0)
    assert fail["accepted"] is False


@pytest.mark.parametrize("status,setup", [
    ("missing", lambda p: None),
    ("empty", lambda p: p.write_text("", encoding="utf-8")),
])
def test_absent_log_fails_closed(tmp_path, status, setup):
    """No log means the criteria CANNOT be evaluated, which is a failure, not a pass."""
    log = tmp_path / "equilibration.log"
    setup(log)
    rep = rm.evaluate_equilibration(log, CRITERIA, 0.1, 2.0)
    assert rep["accepted"] is False
    assert rep["log_status"] == status
    assert rep["checks"]["equilibration_log_readable"]["pass"] is False


def test_nonfinite_energy_is_caught(tmp_path):
    log = _log(tmp_path)
    lines = log.read_text().splitlines()
    parts = lines[10].split("\t")
    parts[3] = "nan"
    lines[10] = "\t".join(parts)
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")
    rep = rm.evaluate_equilibration(log, CRITERIA, 0.1, 2.0)
    assert rep["accepted"] is False
    assert rep["checks"]["potential_energy_finite"]["pass"] is False


# --------------------------------------------------------------------------------------
# Structural guarantees about the launcher
# --------------------------------------------------------------------------------------
def _run_replicate_source() -> str:
    """Only the executable body of run_replicate, so rationale comments cannot match."""
    src = (MD / "run_md.py").read_text(encoding="utf-8")
    body = src[src.index("def run_replicate("):src.index("\ndef main()")]
    return "\n".join(ln for ln in body.splitlines()
                     if not ln.lstrip().startswith("#"))


def test_reporters_are_attached_before_equilibration_stepping():
    """The ordering defect itself: reporters must precede sim.step(equil_steps)."""
    body = _run_replicate_source()
    attach = body.index("str(equil_log), equil_report_every")
    step = body.index("sim.step(equil_steps)")
    assert attach < step, "equilibration reporters must be attached BEFORE stepping"
    # and the production reporters must still come after equilibration finishes
    assert body.index("DCDReporter(str(dcd)") > step


def test_equilibration_frames_go_to_a_separate_file():
    """Equilibration frames must never be written into production.dcd."""
    src = (MD / "run_md.py").read_text(encoding="utf-8")
    assert "DCDReporter(str(equil_dcd)" in src
    assert 'equil_dcd = run_dir / "equilibration.dcd"' in src
    # the production DCD reporter must still be the only writer of production.dcd
    assert len(re.findall(r"DCDReporter\(str\(dcd\)", src)) == 1


def test_equilibration_failure_writes_failed_and_status():
    """A crash during equilibration must produce artifacts, not a bare traceback."""
    src = _run_replicate_source()
    block = src[src.index("sim.step(equil_steps)"):]
    block = block[:block.index('save_checkpoint_atomic(sim, chk, chk_meta, dt_ns, equil_steps, "post_equilibration")')]
    assert "write_json(failed_flag" in block
    assert 'update_status("FAILED"' in block
    assert '"phase": "equilibration"' in block
    assert "except BaseException" in block


def test_equilibration_report_is_written_and_gates_the_run():
    src = (MD / "run_md.py").read_text(encoding="utf-8")
    assert "write_json(equil_json, equil_report)" in src
    assert 'if not equil_report["accepted"]:' in src


# --------------------------------------------------------------------------------------
# Live OpenMM: the reporter configuration must emit the columns the evaluator needs
# --------------------------------------------------------------------------------------
def test_openmm_statedatareporter_emits_every_required_column(tmp_path):
    """Guard the column-name contract between run_md.py's reporter and parse_state_log."""
    mm = pytest.importorskip("openmm")
    from openmm import app, unit
    import numpy as np

    n = 200
    system = mm.System()
    box = 3.0
    system.setDefaultPeriodicBoxVectors(*(mm.Vec3(box, 0, 0), mm.Vec3(0, box, 0),
                                          mm.Vec3(0, 0, box)))
    nb = mm.NonbondedForce()
    nb.setNonbondedMethod(mm.NonbondedForce.CutoffPeriodic)
    nb.setCutoffDistance(1.0 * unit.nanometer)
    top = app.Topology()
    chain = top.addChain()
    for _ in range(n):
        system.addParticle(39.948 * unit.amu)
        nb.addParticle(0.0, 0.34 * unit.nanometer, 0.996 * unit.kilojoule_per_mole)
        res = top.addResidue("AR", chain)
        top.addAtom("AR", app.Element.getBySymbol("Ar"), res)
    system.addForce(nb)
    system.addForce(mm.MonteCarloBarostat(1.0 * unit.bar, 310.0 * unit.kelvin, 25))
    top.setUnitCellDimensions(mm.Vec3(box, box, box) * unit.nanometer)

    integrator = mm.LangevinMiddleIntegrator(310.0 * unit.kelvin, 1.0 / unit.picosecond,
                                             0.002 * unit.picoseconds)
    integrator.setRandomNumberSeed(42)
    sim = app.Simulation(top, system, integrator,
                         mm.Platform.getPlatformByName("CPU"))
    rng = np.random.default_rng(0)
    sim.context.setPositions(rng.uniform(0, box, size=(n, 3)) * unit.nanometer)
    sim.minimizeEnergy(maxIterations=200)
    sim.context.setVelocitiesToTemperature(310.0 * unit.kelvin, 42)

    log = tmp_path / "equilibration.log"
    # EXACTLY the reporter configuration run_md.py uses for equilibration
    sim.reporters.append(app.StateDataReporter(
        str(log), 25, step=True, time=True, potentialEnergy=True, kineticEnergy=True,
        totalEnergy=True, temperature=True, volume=True, density=True,
        progress=True, remainingTime=True, speed=True, totalSteps=500,
        separator="\t", append=False))
    sim.step(500)
    sim.reporters.clear()

    cols, status = rm.parse_state_log(log)
    assert status == "ok"
    assert rm._col(cols, "temperature") is not None
    assert rm._col(cols, "density") is not None
    assert rm._col(cols, "potential", "energy") is not None
    assert (rm._col(cols, "box", "volume") or rm._col(cols, "volume")) is not None

    rep = rm.evaluate_equilibration(log, CRITERIA, 0.1, 0.001)
    assert rep["log_status"] == "ok"
    for name in ("temperature_mean_in_range", "density_final_in_range",
                 "potential_energy_finite", "box_volume_finite_positive"):
        assert rep["checks"][name]["evaluated"] is True, (
            f"{name} must be computable from a real OpenMM equilibration log")
