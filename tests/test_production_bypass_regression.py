from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def _active_lines(path: Path) -> list[str]:
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(stripped)
    return lines


def test_legacy_full_tmux_launcher_has_no_runnable_md_production_commands():
    path = REPO / "md_validation_4070" / "gnn_pocket_search" / "run_all_in_tmux.sh"
    text = "\n".join(_active_lines(path))
    assert "run_md.py" not in text
    assert "--ns 100" not in text
    assert "HISTORICAL_DISABLED" in path.read_text(encoding="utf-8")


def test_active_shell_launchers_do_not_bypass_canonical_authorization():
    launchers = [
        REPO / "md.sh",
        REPO / "md_validation_4070" / "run_in_tmux.sh",
        REPO / "md_validation_4070" / "gnn_pocket_search" / "run_all_in_tmux.sh",
        REPO / "md_validation_4070" / "gnn_pocket_search" / "run_pocket_search.sh",
    ]
    offenders = []
    for path in launchers:
        active = "\n".join(_active_lines(path))
        direct_prod = re.search(r"run_md\.py.*--replicates\s+3.*--ns\s+100", active, re.S)
        if direct_prod and path.name != "md.sh":
            offenders.append(str(path.relative_to(REPO)))
        if direct_prod and path.name == "md.sh":
            assert "--production-authorization" in active
            assert "production-gate" in active
    assert not offenders


def test_direct_production_scale_run_md_fails_before_md_imports(tmp_path):
    proc = subprocess.run(
        [
            sys.executable,
            "md_validation_4070/run_md.py",
            "--run",
            "control",
            "--replicates",
            "3",
            "--ns",
            "100",
            "--outdir",
            str(tmp_path),
            "--md-stage",
            "production",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=30,
    )
    combined = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "requires --production-authorization" in combined


def test_smoke_scale_direct_run_is_not_classified_as_production():
    sys.path.insert(0, str(REPO / "md_validation_4070"))
    import run_md

    args = type("Args", (), {"md_stage": None, "ns": 0.1, "replicates": 1, "equil_ns": 2.0, "run": "control"})()
    assert run_md.classify_md_stage(args) == "smoke"
    assert run_md.is_production_scale(args) is False
