"""The prospectively amended Control-20 continuation must be the ONLY thing it authorizes.

Background. The initial 8GLA control validation ran as 3 x 5 ns and the trajectory-derived
control gate returned FAIL with 2/3 qualifying replicates. A prospective amendment --
recorded before any extended data existed -- authorizes continuing those same three
replicates to 20 ns of TOTAL production each. `--md-stage control_validation` is capped at
3 x 5 ns / 15 ns, so the continuation needs its own stage.

This file pins the shape of that stage: exact 3 x 20 ns 8GLA control, continuation-only,
evidence-bound, and incapable of reaching apo, production, 100 ns, or a fresh start.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "md_validation_4070"


def _load():
    spec = importlib.util.spec_from_file_location("run_md_control_extension", MD / "run_md.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_md_control_extension"] = mod
    spec.loader.exec_module(mod)
    return mod


rm = _load()
STAGE = rm.CONTROL_EXTENSION_STAGE
CONTRACT = rm.CONTROL_EXTENSION_CONTRACT


def A(**kw):
    """A control_extension request; defaults are the exact authorized shape."""
    a = types.SimpleNamespace(
        run="control", replicates=3, ns=20.0, equil_ns=2.0, md_stage=STAGE,
        production_authorization=None, platform="CUDA", require_platform=True,
        pocket="final_consensus_1w60_20260815", outdir="o", hmr=True,
        report_ps=50.0, checkpoint_ps=10.0, _pdb_id="8GLA",
    )
    for k, v in kw.items():
        setattr(a, k, v)
    if not hasattr(a, "_md_stage"):
        a._md_stage = rm.classify_md_stage(a)      # main() resolves this before any gate runs
    return a


# --------------------------------------------------------------------------------------
# On-disk state builders
# --------------------------------------------------------------------------------------
def _done_5ns(rep: int, **over) -> dict:
    payload = {
        "replicate": rep, "pdb": "8GLA", "role": "control", "ns": 5.0,
        "md_stage": "control_validation",
        "production_ns": 4.999999999999, "production_steps": 1_250_000,
        "target_production_steps": 1_250_000, "equilibration_steps": 500_000,
        "equil_ns": 2.0, "report_ps": 50.0, "checkpoint_ps": 10.0,
        "seed": 20260000 + rep, "steps": 1_750_000, "timestep_fs": 4.0,
        "sanity_gate": "passed (energy finite, coordinates finite, backbone RMSD ok)",
    }
    payload.update(over)
    return payload


def _summary_gate5_fail(**over) -> dict:
    gate = {
        "name": "trajectory_dynamic_control_gate_v2",
        "status": "FAIL",
        "qualifying_control_replicates": 2,
        "minimum_control_replicates": 3,
    }
    gate.update(over)
    return {"control_interpretability_gate": gate, "per_replicate": []}


def build_control5_state(base: Path, *, reps=(1, 2, 3), checkpoints=True, dcds=True,
                         done_over: dict | None = None, summary_over: dict | None = None,
                         summary=True) -> Path:
    """A completed 3 x 5 ns 8GLA control run with a recorded FAIL / 2-of-3 gate result."""
    root = base / "8GLA"
    for rep in reps:
        rep_dir = root / f"rep{rep:02d}"
        rep_dir.mkdir(parents=True, exist_ok=True)
        (rep_dir / "DONE.json").write_text(
            json.dumps(_done_5ns(rep, **(done_over or {}))), encoding="utf-8")
        if checkpoints:
            (rep_dir / "state.chk").write_bytes(b"checkpoint-bytes")
        if dcds:
            (rep_dir / "production.dcd").write_bytes(b"dcd-bytes")
    if summary:
        (base / "analysis").mkdir(parents=True, exist_ok=True)
        (base / "analysis" / "summary.json").write_text(
            json.dumps(_summary_gate5_fail(**(summary_over or {}))), encoding="utf-8")
    return base


@pytest.fixture
def amendment_present(monkeypatch, tmp_path):
    """Point the stage at a stand-in amendment so tests do not depend on the real file."""
    path = tmp_path / CONTRACT["amendment_relative_path"]
    path.write_text("# Prospective Control-20 amendment (test stand-in)\n", encoding="utf-8")
    monkeypatch.setattr(rm, "CONTROL_EXTENSION_AMENDMENT", path)
    return path


# --------------------------------------------------------------------------------------
# 1. The authorized run: allowed only when every prerequisite is satisfied
# --------------------------------------------------------------------------------------
def test_exact_3x20ns_control_extension_is_allowed_with_all_prerequisites(
        tmp_path, amendment_present):
    out = build_control5_state(tmp_path / "outputs_control5")
    args = A(outdir=str(out))
    assert rm.classify_md_stage(args) == STAGE
    assert rm.is_production_scale(args) is False, rm.production_scale_reasons(args)
    ok, failures, evidence = rm.control_extension_prerequisites(args)
    assert ok, failures
    assert evidence["amendment"]["sha256"]
    assert evidence["prior_control_gate"]["status"] == "FAIL"
    assert evidence["prior_control_gate"]["qualifying_control_replicates"] == 2
    for rep in ("rep01", "rep02", "rep03"):
        rec = evidence["prior_control5"]["replicates"][rep]
        assert rec["checkpoint_exists"] and rec["production_dcd_exists"]
        assert rec["prior_production_ns"] == pytest.approx(5.0, abs=0.05)
        assert rec["prior_seed"] == rec["expected_seed"]


def test_the_contract_is_control_8gla_three_replicates_twenty_ns():
    assert CONTRACT["role"] == "control"
    assert CONTRACT["pdb"] == "8GLA"
    assert CONTRACT["replicates"] == 3
    assert CONTRACT["target_production_ns_per_replicate"] == 20.0
    assert CONTRACT["total_integration_ns"] == 60.0
    assert CONTRACT["continuation_only"] is True
    assert CONTRACT["authorizes_production"] is False
    assert CONTRACT["authorizes_apo"] is False


# --------------------------------------------------------------------------------------
# 2. Shape: exact, not bounded
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize("args,why", [
    pytest.param(A(run="apo", _pdb_id="1W60"), "apo", id="20ns-apo-rejected"),
    pytest.param(A(run="apo", _pdb_id="1W60", replicates=3, ns=20.0), "apo", id="3x20ns-apo-rejected"),
    pytest.param(A(replicates=1), "replicates", id="1-replicate-rejected"),
    pytest.param(A(replicates=2), "replicates", id="2-replicates-rejected"),
    pytest.param(A(replicates=4), "replicates", id="4-replicates-rejected"),
    pytest.param(A(ns=20.5), "ns per replicate", id="20.5ns-rejected"),
    pytest.param(A(ns=25.0), "ns per replicate", id="25ns-rejected"),
    pytest.param(A(ns=100.0), "ns per replicate", id="100ns-rejected"),
    pytest.param(A(ns=15.0), "ns per replicate", id="15ns-rejected-exact-target"),
    pytest.param(A(ns=5.0), "ns per replicate", id="5ns-rejected-exact-target"),
    pytest.param(A(_pdb_id="1W60"), "structure", id="wrong-structure-rejected"),
])
def test_only_the_exact_shape_is_in_the_envelope(args, why):
    breaches = rm.control_extension_shape_violations(args)
    assert breaches, f"{args.run} {args.replicates} x {args.ns} ns must not be in the envelope"
    assert any(why in b for b in breaches), breaches
    assert rm.is_production_scale(args) is True, (
        "a request outside the exact contract must fall back to requiring canonical "
        "production authorization")


def test_three_by_one_hundred_ns_cannot_be_launched_through_control_extension():
    args = A(ns=100.0)
    assert rm.total_integration_ns(args) == pytest.approx(300.0)
    fits, breaches = rm.fits_stage(args, STAGE)
    assert fits is False and breaches
    assert rm.is_production_scale(args) is True
    assert rm.production_scale_reasons(args)


def test_shape_violations_are_rejected_before_prerequisites_can_help(tmp_path, amendment_present):
    """Complete, valid 5 ns evidence must not license a differently shaped run."""
    out = build_control5_state(tmp_path / "outputs_control5")
    ok, failures, _ = rm.control_extension_prerequisites(A(outdir=str(out), replicates=2))
    assert ok is False
    assert any("replicates" in f for f in failures)


# --------------------------------------------------------------------------------------
# 3. Evidence: amendment, prior 5 ns state, prior gate result
# --------------------------------------------------------------------------------------
def test_missing_amendment_is_rejected(tmp_path, monkeypatch):
    out = build_control5_state(tmp_path / "outputs_control5")
    monkeypatch.setattr(rm, "CONTROL_EXTENSION_AMENDMENT", tmp_path / "does_not_exist.md")
    ok, failures, _ = rm.control_extension_prerequisites(A(outdir=str(out)))
    assert ok is False
    assert any("prospective amendment" in f for f in failures)


def test_empty_amendment_is_rejected(tmp_path, monkeypatch):
    out = build_control5_state(tmp_path / "outputs_control5")
    empty = tmp_path / CONTRACT["amendment_relative_path"]
    empty.write_text("", encoding="utf-8")
    monkeypatch.setattr(rm, "CONTROL_EXTENSION_AMENDMENT", empty)
    ok, failures, _ = rm.control_extension_prerequisites(A(outdir=str(out)))
    assert ok is False
    assert any("prospective amendment" in f for f in failures)


def test_amendment_path_that_is_a_directory_is_rejected(tmp_path, monkeypatch):
    """A directory accidentally created at the amendment path must not count as 'exists'."""
    out = build_control5_state(tmp_path / "outputs_control5")
    as_dir = tmp_path / CONTRACT["amendment_relative_path"]
    as_dir.mkdir()
    monkeypatch.setattr(rm, "CONTROL_EXTENSION_AMENDMENT", as_dir)
    ok, failures, _ = rm.control_extension_prerequisites(A(outdir=str(out)))
    assert ok is False
    assert any("prospective amendment" in f for f in failures)


def test_missing_prior_checkpoints_are_rejected(tmp_path, amendment_present):
    out = build_control5_state(tmp_path / "outputs_control5", checkpoints=False)
    ok, failures, _ = rm.control_extension_prerequisites(A(outdir=str(out)))
    assert ok is False
    assert sum("no state.chk" in f for f in failures) == 3


def test_missing_prior_trajectories_are_rejected(tmp_path, amendment_present):
    out = build_control5_state(tmp_path / "outputs_control5", dcds=False)
    ok, failures, _ = rm.control_extension_prerequisites(A(outdir=str(out)))
    assert ok is False
    assert sum("production.dcd" in f for f in failures) == 3


def test_fresh_start_control_extension_is_rejected(tmp_path, amendment_present):
    """Nothing on disk at all: the stage must refuse to start three new replicates."""
    out = tmp_path / "outputs_control5"
    out.mkdir()
    ok, failures, _ = rm.control_extension_prerequisites(A(outdir=str(out)))
    assert ok is False
    assert sum("no state.chk" in f for f in failures) == 3
    assert sum("no DONE.json" in f for f in failures) == 3
    assert any("summary.json" in f for f in failures)


def test_a_partial_prior_run_is_rejected(tmp_path, amendment_present):
    """Two complete replicates are not three."""
    out = build_control5_state(tmp_path / "outputs_control5", reps=(1, 2))
    ok, failures, _ = rm.control_extension_prerequisites(A(outdir=str(out)))
    assert ok is False
    assert any("rep03" in f for f in failures)


def test_prior_run_shorter_than_five_ns_is_rejected(tmp_path, amendment_present):
    out = build_control5_state(tmp_path / "outputs_control5",
                               done_over={"production_ns": 0.1})
    ok, failures, _ = rm.control_extension_prerequisites(A(outdir=str(out)))
    assert ok is False
    assert sum("no DONE.json" in f for f in failures) == 3


def test_changed_seeds_are_rejected(tmp_path, amendment_present):
    out = build_control5_state(tmp_path / "outputs_control5", done_over={"seed": 12345})
    ok, failures, _ = rm.control_extension_prerequisites(A(outdir=str(out)))
    assert ok is False
    assert any("same seeds" in f for f in failures)


@pytest.mark.parametrize("field,value", [
    ("equil_ns", 5.0),
    ("timestep_fs", 2.0),
    ("report_ps", 25.0),
    ("checkpoint_ps", 20.0),
])
def test_changed_integration_settings_are_rejected(tmp_path, amendment_present, field, value):
    out = build_control5_state(tmp_path / "outputs_control5", done_over={field: value})
    ok, failures, _ = rm.control_extension_prerequisites(A(outdir=str(out)))
    assert ok is False
    assert any(f"prior {field}" in f for f in failures)


def test_prior_stage_must_be_the_recorded_control_validation(tmp_path, amendment_present):
    out = build_control5_state(tmp_path / "outputs_control5",
                               done_over={"md_stage": "diagnostic"})
    ok, failures, _ = rm.control_extension_prerequisites(A(outdir=str(out)))
    assert ok is False
    assert any("prior md_stage" in f for f in failures)


@pytest.mark.parametrize("gate_over,needle", [
    ({"status": "PASS"}, "status"),
    ({"qualifying_control_replicates": 3}, "qualifying control replicates"),
    ({"qualifying_control_replicates": 1}, "qualifying control replicates"),
    ({"minimum_control_replicates": 2}, "3/3 aggregation rule"),
])
def test_the_prior_gate_result_must_be_the_recorded_fail_2_of_3(
        tmp_path, amendment_present, gate_over, needle):
    out = build_control5_state(tmp_path / "outputs_control5", summary_over=gate_over)
    ok, failures, _ = rm.control_extension_prerequisites(A(outdir=str(out)))
    assert ok is False
    assert any(needle in f for f in failures), failures


def test_missing_prior_analysis_summary_is_rejected(tmp_path, amendment_present):
    out = build_control5_state(tmp_path / "outputs_control5", summary=False)
    ok, failures, _ = rm.control_extension_prerequisites(A(outdir=str(out)))
    assert ok is False
    assert any("summary.json is missing" in f for f in failures)


def test_preflight_record_accumulates_and_keeps_the_original_5ns_state(
        tmp_path, amendment_present):
    """The record of what was continued from must survive a relaunch."""
    out = build_control5_state(tmp_path / "outputs_control5")
    record = out / "CONTROL_EXTENSION_PREFLIGHT.json"
    args = A(outdir=str(out))

    first = rm.validate_control_extension(args, write_to=record)
    assert first is not None
    on_disk = json.loads(record.read_text(encoding="utf-8"))
    assert on_disk["previous_checks"] == []
    original = on_disk["prior_control5"]["replicates"]["rep01"]["done_json_sha256"]

    rm.validate_control_extension(A(outdir=str(out)), write_to=record)
    on_disk = json.loads(record.read_text(encoding="utf-8"))
    assert len(on_disk["previous_checks"]) == 1
    assert (on_disk["previous_checks"][0]["prior_control5"]["replicates"]["rep01"]
            ["done_json_sha256"]) == original


def test_provenance_names_the_amendment_and_what_it_continued_from(tmp_path, amendment_present):
    out = build_control5_state(tmp_path / "outputs_control5")
    args = A(outdir=str(out))
    rm.validate_control_extension(args, write_to=None)
    prov = rm._control_extension_provenance(args, rep=2)
    assert prov["kind"] == "PROSPECTIVE_PROTOCOL_AMENDMENT"
    assert prov["recorded_before_any_extended_data"] is True
    assert prov["amendment_sha256"]
    assert prov["target_production_ns_total"] == 20.0
    assert prov["continued_from"]["prior_seed"] == 20260002
    assert prov["prior_control_gate"]["status"] == "FAIL"
    assert prov["authorizes_production"] is False
    assert prov["authorizes_gate6"] is False


def test_provenance_is_absent_off_stage():
    assert rm._control_extension_provenance(A(md_stage="control_validation"), rep=1) is None


# --------------------------------------------------------------------------------------
# 4. The immutable 5 ns backup must never be the continuation target
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize("name", [
    "outputs_control5_immutable", "control5_backup", "archive_control5", "frozen_control5",
])
def test_the_immutable_backup_is_never_continued_in_place(tmp_path, amendment_present, name):
    out = build_control5_state(tmp_path / name)
    ok, failures, _ = rm.control_extension_prerequisites(A(outdir=str(out)))
    assert ok is False
    assert any("immutable 5 ns archive" in f for f in failures)


@pytest.mark.parametrize("name", [
    "Outputs_Control5_BACKUP", "CONTROL5_IMMUTABLE", "Archive_Control5", "FROZEN_control5",
])
def test_the_immutable_backup_guard_is_case_insensitive(tmp_path, amendment_present, name):
    """A mixed-case path must not slip past the lowercased marker match."""
    out = build_control5_state(tmp_path / name)
    ok, failures, _ = rm.control_extension_prerequisites(A(outdir=str(out)))
    assert ok is False
    assert any("immutable 5 ns archive" in f for f in failures)


# --------------------------------------------------------------------------------------
# 4b. Repeated / chained adaptive extension must be structurally impossible
# --------------------------------------------------------------------------------------
def test_a_completed_control20_run_cannot_be_chained_into_another_extension(
        tmp_path, amendment_present):
    """The requirement is 'no repeated adaptive extensions'.

    Simulate what the on-disk state looks like AFTER a genuine control20 run has already
    completed: DONE.json now records production_ns ~= 20.0 and md_stage = 'control_extension'
    (see done_payload in run_replicate). Nothing about the shape contract changes (ns must
    still be exactly 20.0), so this can only matter if someone tries to use that finished
    20 ns state as the "prior" baseline for a further extension. It must not validate as
    prior evidence: the duration-matching search in _control_extension_prior_5ns looks for
    ~5.0 ns records specifically, so a 20 ns DONE.json is invisible to it regardless of any
    md_stage label.
    """
    out = build_control5_state(
        tmp_path / "outputs_control5",
        done_over={"production_ns": 19.999999, "ns": 20.0, "md_stage": "control_extension",
                  "steps": 5_500_000, "production_steps": 5_000_000},
    )
    ok, failures, evidence = rm.control_extension_prerequisites(A(outdir=str(out)))
    assert ok is False
    assert sum("no DONE.json (live or archived) recording a completed 5.0 ns" in f
               for f in failures) == 3
    for rep in ("rep01", "rep02", "rep03"):
        assert evidence["prior_control5"]["replicates"][rep]["done_json"] is None


def test_relabelling_a_20ns_done_as_control_validation_still_fails_on_duration(
        tmp_path, amendment_present):
    """Even disguising the stage label alone is not enough: the ~5 ns duration is checked."""
    out = build_control5_state(
        tmp_path / "outputs_control5",
        done_over={"production_ns": 19.999999, "ns": 20.0, "md_stage": "control_validation"},
    )
    ok, failures, _ = rm.control_extension_prerequisites(A(outdir=str(out)))
    assert ok is False
    assert sum("no DONE.json (live or archived) recording a completed 5.0 ns" in f
               for f in failures) == 3


# --------------------------------------------------------------------------------------
# 5. --ns 20 stays TOTAL production time, so each 5 ns replicate adds only 15 ns
# --------------------------------------------------------------------------------------
def test_ns_is_total_production_so_the_continuation_adds_fifteen_ns():
    dt_ns = 4.0 / 1_000_000.0                      # 4 fs HMR timestep, unchanged
    steps_per_ns = int(round(1.0 / dt_ns))
    equil_steps = int(round(2.0 * steps_per_ns))
    prod_steps_20 = int(round(20.0 * steps_per_ns))
    already_done = equil_steps + int(round(5.0 * steps_per_ns))   # state at the 5 ns checkpoint

    total_steps = equil_steps + prod_steps_20
    remaining = total_steps - already_done

    assert rm.production_step_to_ns(already_done, equil_steps, dt_ns) == pytest.approx(5.0)
    assert rm.production_step_to_ns(total_steps, equil_steps, dt_ns) == pytest.approx(20.0)
    assert remaining * dt_ns == pytest.approx(15.0), (
        "--ns 20 must mean 20 ns TOTAL production, not 20 ns more")


def test_a_completed_20ns_replicate_is_not_rerun():
    """validate_done compares against the 20 ns target, so a finished replicate is complete."""
    args = A()
    done = _done_5ns(1, production_ns=19.999999, steps=5_500_000, ns=20.0)
    assert float(done["production_ns"]) + 1e-9 >= float(args.ns) - 1e-3


# --------------------------------------------------------------------------------------
# 6. Nothing else weakened: existing envelopes and the production gate are untouched
# --------------------------------------------------------------------------------------
def test_control_validation_is_still_capped_at_three_by_five_ns():
    limits = rm.STAGE_LIMITS["control_validation"]
    assert limits == {"max_replicates": 3, "max_ns_per_replicate": 5.0, "max_total_ns": 15.0}
    over = types.SimpleNamespace(run="control", replicates=3, ns=20.0, equil_ns=2.0,
                                 md_stage="control_validation", production_authorization=None,
                                 platform="CUDA", require_platform=True, pocket="p", outdir="o")
    assert rm.fits_stage(over, "control_validation")[0] is False
    assert rm.is_production_scale(over) is True
    assert rm.classify_md_stage(
        types.SimpleNamespace(run="control", replicates=3, ns=5.0, equil_ns=2.0,
                              md_stage=None, production_authorization=None, platform="CUDA",
                              require_platform=True, pocket="p", outdir="o")
    ) == "control_validation"


def test_control_extension_is_never_inferred_only_declared():
    undeclared = A(md_stage=None)
    assert rm.classify_md_stage(undeclared) == "production"
    assert rm.is_production_scale(undeclared) is True


def test_production_still_requires_gate6_authorization():
    prod = A(md_stage=None, ns=100.0)
    assert rm.is_production_scale(prod) is True
    with pytest.raises(SystemExit) as exc:
        rm.validate_production_authorization(prod)
    assert "requires canonical production authorization" in str(exc.value)


def test_control_extension_stage_does_not_raise_the_production_ceiling():
    assert rm.PRODUCTION_LIMITS == {"max_replicates": 3, "max_ns_per_replicate": 100.0,
                                    "max_total_ns": 300.0}
    assert rm.STAGE_LIMITS[STAGE]["max_total_ns"] < rm.PRODUCTION_LIMITS["max_total_ns"]


def test_every_other_stage_envelope_is_unchanged():
    assert rm.STAGE_LIMITS["smoke"] == {"max_replicates": 1, "max_ns_per_replicate": 0.25,
                                        "max_total_ns": 0.25}
    assert rm.STAGE_LIMITS["benchmark"] == {"max_replicates": 1, "max_ns_per_replicate": 1.0,
                                            "max_total_ns": 1.0}
    assert rm.STAGE_LIMITS["diagnostic"] == {"max_replicates": 2, "max_ns_per_replicate": 2.0,
                                             "max_total_ns": 4.0}


# --------------------------------------------------------------------------------------
# 7. End-to-end refusals, before any structure preparation or GPU work
# --------------------------------------------------------------------------------------
def _run_md(*argv, cwd=ROOT):
    return subprocess.run([sys.executable, str(MD / "run_md.py"), *argv],
                          capture_output=True, text=True, cwd=str(cwd), timeout=180)


def test_cli_apo_under_control_extension_is_refused(tmp_path):
    proc = _run_md("--run", "apo", "--replicates", "3", "--ns", "20",
                   "--md-stage", "control_extension", "--outdir", str(tmp_path / "never"))
    combined = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "[production-gate] FATAL" in combined
    assert not (tmp_path / "never").exists()


def test_cli_100ns_under_control_extension_is_refused(tmp_path):
    proc = _run_md("--run", "control", "--replicates", "3", "--ns", "100",
                   "--md-stage", "control_extension", "--outdir", str(tmp_path / "never"))
    combined = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "[production-gate] FATAL" in combined
    assert not (tmp_path / "never").exists()


@pytest.mark.parametrize("replicates", ["1", "2"])
def test_cli_wrong_replicate_count_is_refused(tmp_path, replicates):
    proc = _run_md("--run", "control", "--replicates", replicates, "--ns", "20",
                   "--md-stage", "control_extension", "--outdir", str(tmp_path / "never"))
    assert proc.returncode != 0
    assert "[production-gate] FATAL" in (proc.stdout + proc.stderr)


def test_cli_exact_shape_without_evidence_is_refused(tmp_path):
    """The shape is right, so the production gate passes; the evidence check must not."""
    out = tmp_path / "outputs_control5"
    out.mkdir()
    proc = _run_md("--run", "control", "--replicates", "3", "--ns", "20",
                   "--md-stage", "control_extension", "--outdir", str(out),
                   "--control-extension-preflight-only")
    combined = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "[control-extension] FATAL" in combined
    assert "no state.chk" in combined
    assert not (out / "8GLA").exists(), "a refused run must not prepare any structure"


def test_cli_preflight_only_requires_the_stage(tmp_path):
    proc = _run_md("--run", "control", "--replicates", "3", "--ns", "5",
                   "--md-stage", "control_validation", "--outdir", str(tmp_path / "never"),
                   "--control-extension-preflight-only")
    assert proc.returncode != 0
    assert "--control-extension-preflight-only requires" in (proc.stdout + proc.stderr)


# --------------------------------------------------------------------------------------
# 8. The launcher
# --------------------------------------------------------------------------------------
def test_launcher_exposes_control20_with_the_exact_command():
    text = (ROOT / "md.sh").read_text(encoding="utf-8")
    assert "control20)" in text
    assert "--md-stage control_extension" in text
    assert "--replicates 3" in text and "--ns 20" in text
    assert "outputs_control5" in text
    assert "--platform CUDA --require-platform" in text
    assert "analyze_md.py" in text and "control-report" in text
    assert "CONTROL20_PROSPECTIVE_AMENDMENT_20260817.md" in text


def test_launcher_control20_never_touches_gate6_or_production():
    text = (ROOT / "md.sh").read_text(encoding="utf-8")
    body = text.split("run_control20() {", 1)[1].split("\nrun_benchmark()", 1)[0]
    assert "production-gate" not in body
    assert "--authorize-run" not in body
    assert "--md-stage production" not in body
    assert "gate6" not in body.lower().replace("gate 6 is not approved", "")


def test_launcher_control20_preflights_before_launching(tmp_path):
    text = (ROOT / "md.sh").read_text(encoding="utf-8")
    body = text.split("run_control20() {", 1)[1].split("\nrun_benchmark()", 1)[0]
    assert body.index("--control-extension-preflight-only") < body.index("launch_tmux")


def _usable_bash() -> str | None:
    for candidate in ("bash", r"C:\Program Files\Git\bin\bash.exe"):
        try:
            probe = subprocess.run([candidate, "-c", "echo ok"], capture_output=True,
                                   text=True, timeout=60)
        except (OSError, subprocess.SubprocessError):
            continue
        if probe.returncode == 0 and "ok" in probe.stdout:
            return candidate
    return None


def test_launcher_control20_blocks_without_the_amendment():
    """The real amendment file gates the real launcher."""
    bash = _usable_bash()
    if bash is None:
        pytest.skip("no usable POSIX bash on this host")
    amendment = MD / CONTRACT["amendment_relative_path"]
    if amendment.is_file() and amendment.stat().st_size > 0:
        pytest.skip("the amendment exists; this test pins the refusal when it does not")
    proc = subprocess.run([bash, "md.sh", "control20"], cwd=ROOT, capture_output=True,
                          text=True, timeout=120)
    assert proc.returncode != 0
    assert "CONTROL-20 BLOCKED" in (proc.stdout + proc.stderr)
