from __future__ import annotations

import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def _control_row(rep: int, rmsf: float, open_fraction: float,
                 hull_acf: float | None = 0.85, dccm_abs: float | None = 0.45,
                 with_dynamics: bool = True) -> dict:
    """A control replicate summary.

    ``hull_acf`` / ``dccm_abs`` are the trajectory_dynamic_control_gate_v2 discriminators
    D1 and D2. At N=100 production frames their IID-noise null thresholds are 0.300 and
    0.239 respectively, so the defaults here sit clearly above the null and the
    static-noise defaults used below sit clearly below it.
    """
    row = {
        "role": "control",
        "pdb": "8GLA",
        "replicate": f"rep{rep:02d}",
        "n_frames": 100,
        "dt_ns": 0.05,
        "pbc_artifact_suspected": False,
        "duplicate_log_times": False,
        "frame_count_status": "ok",
        "completion_status": "PASS",
        "pocket_rmsf_mean_nm": rmsf,
        "openness": {
            "available": True,
            "open_like_fraction": open_fraction,
        },
    }
    if with_dynamics:
        row["dynamics"] = {
            "primary_region": "supported_ge2of3",
            "n_production_frames": 100,
            "hull_volume_lag1_autocorrelation": hull_acf,
            "region_internal_mean_abs_dccm": dccm_abs,
        }
    return row


def test_md_launcher_exposes_canonical_commands():
    launcher = REPO / "md.sh"
    assert launcher.exists()
    text = launcher.read_text(encoding="utf-8")
    for command in ("smoke", "control5", "benchmark", "production", "analyze", "status", "attach"):
        assert f"{command})" in text or f"./md.sh {command}" in text


def test_production_gate_fails_closed_without_gate6():
    proc = subprocess.run(
        ["bash", "md.sh", "production"],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=60,
    )
    combined = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "PRODUCTION BLOCKED: Gate-6 human approval required." in combined


def _analyze_md():
    import sys

    sys.path.insert(0, str(REPO / "md_validation_4070"))
    import analyze_md

    return analyze_md


def test_static_starting_difference_with_tiny_noise_fails_control_gate():
    analyze_md = _analyze_md()
    rows = [_control_row(i, rmsf=0.001, open_fraction=0.95) for i in range(1, 4)]
    verdict = analyze_md.evaluate_control_interpretability(rows)
    assert verdict["status"] == "FAIL"
    assert verdict["uses_frame_zero_or_static_apo_control_difference"] is False
    assert any("below dynamic floor" in issue for issue in verdict["issues"])


def test_static_noise_clearing_the_rmsf_floor_still_fails_on_the_dynamics():
    """The v1 hole: RMSF above the floor and fully open, but no temporal/collective structure.

    0.10 A per-axis jitter gives RMSF 0.0174 nm, above the 0.015 nm floor, and a static 8GLA
    reads open_like_fraction = 1.0 from frame zero. v1 passed this. v2 must not.
    """
    analyze_md = _analyze_md()
    rows = [_control_row(i, rmsf=0.0174, open_fraction=1.0,
                         hull_acf=0.02, dccm_abs=0.08) for i in range(1, 4)]
    verdict = analyze_md.evaluate_control_interpretability(rows)
    assert verdict["status"] == "FAIL"
    joined = " ".join(verdict["issues"])
    assert "D1" in joined and "D2" in joined


def test_missing_dynamics_block_fails_closed():
    """A summary produced by a pre-v2 analyzer must not satisfy the v2 gate."""
    analyze_md = _analyze_md()
    rows = [_control_row(i, rmsf=0.035, open_fraction=0.55, with_dynamics=False)
            for i in range(1, 4)]
    verdict = analyze_md.evaluate_control_interpretability(rows)
    assert verdict["status"] == "FAIL"
    assert any("unavailable" in issue for issue in verdict["issues"])


def test_valid_dynamic_control_behavior_can_pass():
    analyze_md = _analyze_md()
    rows = [_control_row(i, rmsf=0.035, open_fraction=0.55) for i in range(1, 4)]
    verdict = analyze_md.evaluate_control_interpretability(rows)
    assert verdict["status"] == "PASS", verdict["issues"]
    assert verdict["name"] == "trajectory_dynamic_control_gate_v2"
    assert verdict["rejects_static_structure_plus_per_frame_noise"] is True
