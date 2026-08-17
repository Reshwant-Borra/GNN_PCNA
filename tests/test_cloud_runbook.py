"""Every command in the cloud runbook must correspond to code that exists. No pseudocode."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "md_validation_4070"
RUNBOOK = MD / "CLOUD_MD_RUNBOOK.md"


@pytest.fixture(scope="module")
def text():
    return RUNBOOK.read_text(encoding="utf-8")


def test_runbook_exists(text):
    assert len(text) > 4000


@pytest.mark.parametrize("section", list("ABCDEFGHIJKLMNOPQ"))
def test_every_required_section_is_present(text, section):
    assert re.search(rf"^## {section}\. ", text, re.M), f"section {section} missing"


def test_every_md_sh_subcommand_used_is_dispatched(text):
    used = set(re.findall(r"\./md\.sh ([a-z0-9]+)", text))
    dispatch = (ROOT / "md.sh").read_text(encoding="utf-8")
    case_block = dispatch[dispatch.index('case "${1:-}" in'):]
    for cmd in sorted(used):
        assert re.search(rf"^\s*{re.escape(cmd)}\)", case_block, re.M), (
            f"./md.sh {cmd} is used in the runbook but not dispatched in md.sh")


def test_md_sh_dispatch_matches_its_own_usage_text():
    dispatch = (ROOT / "md.sh").read_text(encoding="utf-8")
    usage = dispatch[dispatch.index("Usage:"):dispatch.index("EOF\n}")]
    documented = set(re.findall(r"\./md\.sh ([a-z0-9]+)", usage))
    case_block = dispatch[dispatch.index('case "${1:-}" in'):]
    dispatched = set(re.findall(r"^\s{2}([a-z0-9]+)\)", case_block, re.M))
    missing = documented - dispatched
    assert not missing, f"documented but not dispatched: {missing}"


def test_every_md_workflow_subcommand_used_is_a_real_choice(text):
    used = set(re.findall(r"md_workflow\.py ([a-z0-9-]+)", text))
    src = (MD / "md_workflow.py").read_text(encoding="utf-8")
    choices = set(re.findall(r'"([a-z0-9-]+)"', src[src.index('ap.add_argument("command"'):
                                                    src.index("ap.add_argument(\"--outdir\"")]))
    for cmd in used:
        assert cmd in choices, f"md_workflow.py {cmd} is not a valid command"


def test_referenced_repository_files_exist(text):
    referenced = set(re.findall(r"md_validation_4070/[A-Za-z0-9_./-]+", text))
    missing = []
    for rel in sorted(referenced):
        if any(part in rel for part in ("outputs", "logs/", "pcna_md_results_",
                                        "benchmark_outputs", "GATE6_DECISION.json",
                                        "CONTROL_INTERPRETABILITY_REPORT.md",
                                        "BENCHMARK_REPORT.json")):
            continue                      # runtime outputs, created by the run itself
        if not (ROOT / rel).exists():
            missing.append(rel)
    assert not missing, f"runbook references files that do not exist: {missing}"


def test_referenced_python_entrypoints_exist(text):
    for rel in set(re.findall(r"python (?:-m )?([A-Za-z0-9_./]+\.py)", text)):
        assert (ROOT / rel).exists(), f"{rel} referenced but absent"


def test_analyzer_flags_used_in_the_runbook_are_real(text):
    proc = subprocess.run([sys.executable, str(MD / "analyze_md.py"), "--help"],
                          capture_output=True, text=True, cwd=str(ROOT), timeout=180)
    assert proc.returncode == 0, proc.stderr
    help_text = proc.stdout
    for flag in ("--pocket", "--outdir", "--allow-incomplete-diagnostic", "--stride"):
        assert flag in help_text, f"{flag} is not a real analyze_md.py option"


def test_run_md_flags_used_by_md_sh_are_real():
    proc = subprocess.run([sys.executable, str(MD / "run_md.py"), "--help"],
                          capture_output=True, text=True, cwd=str(ROOT), timeout=180)
    assert proc.returncode == 0, proc.stderr
    help_text = proc.stdout
    dispatch = (ROOT / "md.sh").read_text(encoding="utf-8")
    for flag in set(re.findall(r"(--[a-z][a-z0-9-]+)", dispatch)):
        if flag in ("--query-gpu", "--format", "--short", "--abbrev-ref", "--bundle-out",
                    "--outdir", "--allow-missing-summary", "--authorize-run", "--pocket",
                    "--replicates", "--ns", "--atoms", "--protein-atoms",
                    "--storage-safety-factor", "--help"):
            continue
        assert flag in help_text, f"md.sh passes {flag} but run_md.py does not accept it"


def test_runbook_never_instructs_downloading_a_trajectory(text):
    lowered = text.lower()
    assert "raw trajectories stay there" in lowered or "stay on" in lowered
    # scp/rsync may appear only for the compact bundle, never for a DCD
    for match in re.findall(r"^.*(?:scp|rsync).*$", text, re.M):
        assert ".dcd" not in match.lower(), f"runbook suggests transferring a trajectory: {match}"


def test_runbook_documents_the_manual_gates(text):
    assert "Never automatic" in text
    for phrase in ("Do not continue automatically",
                   "Nothing in this repository can approve Gate 6",
                   "PERFORMANCE_ONLY"):
        assert phrase in text, f"runbook is missing: {phrase!r}"


def test_runbook_forbids_threshold_tuning(text):
    assert "Do not tune thresholds" in text
    assert "that is a real result" in text.lower() or "is a real result" in text


def test_stage_gate_order_is_stated(text):
    order = ["PRECHECK", "SMOKE", "SMOKE_REVIEW", "CONTROL5", "CONTROL_INTERPRETATION",
             "HUMAN_GATE6", "BENCHMARK", "PRODUCTION", "ANALYSIS", "FINAL_INTERPRETATION"]
    positions = [text.index(stage) for stage in order]
    assert positions == sorted(positions), "the stage ladder is not stated in order"
