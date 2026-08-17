"""Large runs must not bypass the production gate by being shaped or labelled differently.

Reproduced 2026-08-16 against b4d9d7c: is_production_scale() protected essentially one shape
of run (3 x 100 ns). All of these ran with NO authorization at all --

    1 x 500 ns   2 x 100 ns   2 x 1000 ns   6 x 99 ns
    --md-stage diagnostic --replicates 1 --ns 500
    --md-stage smoke      --replicates 2 --ns 1000

-- because classify_md_stage() returned the DECLARED stage without ever checking that the
request fits inside it.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "md_validation_4070"


def _load():
    spec = importlib.util.spec_from_file_location("run_md_under_test", MD / "run_md.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_md_under_test"] = mod
    spec.loader.exec_module(mod)
    return mod


rm = _load()


def A(**kw):
    a = types.SimpleNamespace(run="control", replicates=3, ns=100.0, equil_ns=2.0,
                              md_stage=None, production_authorization=None,
                              platform="CUDA", require_platform=True, pocket="p", outdir="o")
    for k, v in kw.items():
        setattr(a, k, v)
    return a


# --------------------------------------------------------------------------------------
# Adversarial: every one of these previously bypassed the gate
# --------------------------------------------------------------------------------------
ADVERSARIAL = [
    pytest.param(A(replicates=1, ns=500.0), 500.0, id="1x500ns"),
    pytest.param(A(replicates=2, ns=100.0), 200.0, id="2x100ns"),
    pytest.param(A(replicates=2, ns=1000.0), 2000.0, id="2x1000ns"),
    pytest.param(A(replicates=6, ns=99.0), 594.0, id="6x99ns"),
    pytest.param(A(replicates=1, ns=500.0, md_stage="diagnostic"), 500.0, id="mislabelled-diagnostic"),
    pytest.param(A(replicates=2, ns=1000.0, md_stage="smoke"), 2000.0, id="mislabelled-smoke"),
    pytest.param(A(replicates=1, ns=200.0, md_stage="benchmark"), 200.0, id="mislabelled-benchmark"),
    pytest.param(A(replicates=8, ns=50.0, md_stage="control_validation"), 400.0, id="mislabelled-control"),
    pytest.param(A(replicates=3, ns=100.0), 300.0, id="canonical-3x100ns"),
    pytest.param(A(replicates=4, ns=100.0), 400.0, id="4x100ns"),
    pytest.param(A(replicates=1, ns=100.0), 100.0, id="1x100ns"),
    pytest.param(A(replicates=3, ns=50.0), 150.0, id="3x50ns"),
]


@pytest.mark.parametrize("args,budget", ADVERSARIAL)
def test_large_runs_require_authorization(args, budget):
    assert rm.total_integration_ns(args) == pytest.approx(budget)
    assert rm.is_production_scale(args) is True, (
        f"{args.replicates} x {args.ns} ns = {budget} ns must require production "
        f"authorization; stage classified as {rm.classify_md_stage(args)}")
    assert rm.production_scale_reasons(args), "a blocked run must state why"


# --------------------------------------------------------------------------------------
# Legitimate: the declared stages must still run without authorization
# --------------------------------------------------------------------------------------
LEGITIMATE = [
    pytest.param(A(replicates=1, ns=0.1, md_stage="smoke"), "smoke", id="smoke-0.1ns"),
    pytest.param(A(replicates=1, ns=0.25, md_stage="smoke"), "smoke", id="smoke-ceiling"),
    pytest.param(A(replicates=1, ns=0.02, equil_ns=0.0, md_stage="benchmark"), "benchmark", id="benchmark"),
    pytest.param(A(replicates=1, ns=1.0, equil_ns=0.0, md_stage="benchmark"), "benchmark", id="benchmark-ceiling"),
    pytest.param(A(replicates=3, ns=5.0, md_stage="control_validation"), "control_validation", id="control5"),
    pytest.param(A(replicates=1, ns=2.0, md_stage="diagnostic"), "diagnostic", id="diagnostic"),
    pytest.param(A(replicates=2, ns=2.0, md_stage="diagnostic"), "diagnostic", id="diagnostic-ceiling"),
]


@pytest.mark.parametrize("args,stage", LEGITIMATE)
def test_legitimate_stages_need_no_authorization(args, stage):
    assert rm.classify_md_stage(args) == stage
    assert rm.is_production_scale(args) is False, rm.production_scale_reasons(args)


@pytest.mark.parametrize("stage,over", [
    ("smoke", A(replicates=1, ns=0.26, md_stage="smoke")),
    ("smoke", A(replicates=2, ns=0.1, md_stage="smoke")),
    ("benchmark", A(replicates=1, ns=1.01, equil_ns=0.0, md_stage="benchmark")),
    ("control_validation", A(replicates=4, ns=5.0, md_stage="control_validation")),
    ("control_validation", A(replicates=3, ns=5.5, md_stage="control_validation")),
    ("diagnostic", A(replicates=3, ns=2.0, md_stage="diagnostic")),
    ("diagnostic", A(replicates=1, ns=2.5, md_stage="diagnostic")),
])
def test_one_step_over_a_stage_ceiling_requires_authorization(stage, over):
    """The envelope boundary is enforced exactly, not approximately."""
    assert rm.is_production_scale(over) is True
    fits, breaches = rm.fits_stage(over, stage)
    assert fits is False and breaches


def test_stage_envelopes_are_declared_explicitly():
    for stage, limits in rm.STAGE_LIMITS.items():
        assert set(limits) == {"max_replicates", "max_ns_per_replicate", "max_total_ns"}
        assert limits["max_total_ns"] <= rm.PRODUCTION_LIMITS["max_total_ns"]


def test_unauthorized_production_scale_exits_before_any_simulation():
    """The refusal must happen at argument parsing, before structure prep or GPU work."""
    proc = subprocess.run(
        [sys.executable, str(MD / "run_md.py"), "--run", "control",
         "--replicates", "2", "--ns", "1000", "--md-stage", "smoke",
         "--outdir", "/tmp/pcna_should_never_be_created"],
        capture_output=True, text=True, cwd=str(ROOT), timeout=180)
    assert proc.returncode != 0
    combined = proc.stdout + proc.stderr
    assert "[production-gate] FATAL" in combined
    assert "requires canonical production authorization" in combined
    assert not Path("/tmp/pcna_should_never_be_created").exists(), (
        "no output directory may be created for a refused run")


def test_authorization_is_bound_to_the_exact_requested_shape(tmp_path):
    """An authorization for 3 x 100 ns must not license a different run."""
    import json
    auth = tmp_path / "auth.json"
    auth.write_text(json.dumps({
        "kind": "PCNA_MD_PRODUCTION_AUTHORIZATION",
        "authorized_by": "md_validation_4070/md_workflow.py production-gate",
        "expires_utc": "2099-01-01T00:00:00+00:00",
        "pocket": "p", "allowed_runs": ["control", "apo"],
        "replicates": 3, "ns": 100.0, "outdir": str(tmp_path),
        "required_platform": "CUDA", "require_platform": True,
        "gate_evidence": {"gate6_human_approval": True, "protocol_ok": True,
                          "cuda_available": True, "readiness_gate_invoked": True},
        "frozen_analysis_protocol_sha256": "wrong",
        "git": {"commit": "x", "status_short": ""},
    }), encoding="utf-8")
    args = A(replicates=1, ns=500.0, outdir=str(tmp_path),
             production_authorization=str(auth))
    with pytest.raises(SystemExit) as exc:
        rm.validate_production_authorization(args)
    assert "rejected" in str(exc.value)
