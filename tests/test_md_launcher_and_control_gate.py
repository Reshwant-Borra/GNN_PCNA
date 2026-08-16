from __future__ import annotations

import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def _control_row(rep: int, rmsf: float, open_fraction: float) -> dict:
    return {
        "role": "control",
        "pdb": "8GLA",
        "replicate": f"rep{rep:02d}",
        "n_frames": 100,
        "dt_ns": 0.05,
        "pbc_artifact_suspected": False,
        "duplicate_log_times": False,
        "frame_count_status": "ok",
        "pocket_rmsf_mean_nm": rmsf,
        "openness": {
            "available": True,
            "open_like_fraction": open_fraction,
        },
    }


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


def test_static_starting_difference_with_tiny_noise_fails_control_gate():
    import sys

    sys.path.insert(0, str(REPO / "md_validation_4070"))
    import analyze_md

    rows = [_control_row(i, rmsf=0.001, open_fraction=0.95) for i in range(1, 4)]
    verdict = analyze_md.evaluate_control_interpretability(rows)
    assert verdict["status"] == "FAIL"
    assert verdict["uses_frame_zero_or_static_apo_control_difference"] is False
    assert any("below dynamic floor" in issue for issue in verdict["issues"])


def test_valid_dynamic_control_behavior_can_pass():
    import sys

    sys.path.insert(0, str(REPO / "md_validation_4070"))
    import analyze_md

    rows = [_control_row(i, rmsf=0.035, open_fraction=0.55) for i in range(1, 4)]
    verdict = analyze_md.evaluate_control_interpretability(rows)
    assert verdict["status"] == "PASS"
