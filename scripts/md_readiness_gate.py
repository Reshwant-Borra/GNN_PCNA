#!/usr/bin/env python3
"""Fail-closed MD readiness gate for GNN-PCNA production MD."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "md_validation_4070"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git_dirty() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), "status", "--short"], text=True).strip()
    except Exception as exc:
        return f"UNKNOWN: {exc}"


def main() -> int:
    failures: list[str] = []
    warnings: list[str] = []

    pocket_path = MD / "pockets" / "final_consensus_1w60_20260815.json"
    if not pocket_path.exists():
        failures.append(f"missing canonical pocket: {pocket_path}")
    else:
        pocket = load(pocket_path)
        for key in ("pocket_name", "pocket_residues_resseq", "core_3of3", "fringe_2of3", "uncertain_fringe_1of3", "apo_pdb", "control_pdb"):
            if key not in pocket:
                failures.append(f"pocket missing required key: {key}")
        if len(pocket.get("core_3of3", [])) != 11:
            failures.append("core_3of3 does not contain 11 residues")
        if len(pocket.get("pocket_residues_resseq", [])) != 16:
            failures.append("supported >=2/3 pocket_residues_resseq does not contain 16 residues")

    for rel in (
        "MD_SCIENTIFIC_QUESTION.md",
        "MD_ASSUMPTION_AND_SOURCE_AUDIT.md",
        "PREVIOUS_MD_FAILURES_AND_PREVENTIONS.md",
        "MD_STRUCTURE_VALIDATION_REPORT.md",
        "PCNA_CHAIN_AND_RESIDUE_MAPPING.md",
        "POSITIVE_CONTROL_SPECIFICATION.md",
        "MD_PARAMETER_AUDIT.md",
        "EQUILIBRATION_ACCEPTANCE_CRITERIA.json",
        "CONTROL_SMOKE_TEST_REPORT.md",
        "MD_ANALYSIS_VALIDATION_REPORT.md",
        "FROZEN_MD_ANALYSIS_PROTOCOL.json",
        "MD_REPLICATE_AND_DURATION_PLAN.md",
        "MD_READINESS_REPORT.md",
        "GATE6_PACKET_FINAL_PRE_MD_READINESS.md",
    ):
        if not (MD / rel).exists():
            failures.append(f"missing required report/artifact: md_validation_4070/{rel}")

    protocol = MD / "FROZEN_MD_ANALYSIS_PROTOCOL.json"
    protocol_hash = MD / "FROZEN_MD_ANALYSIS_PROTOCOL.sha256"
    if protocol.exists() and protocol_hash.exists():
        recorded = protocol_hash.read_text(encoding="utf-8").split()[0]
        actual = sha256(protocol)
        if recorded != actual:
            failures.append(f"frozen analysis hash mismatch: recorded {recorded}, actual {actual}")
    else:
        failures.append("frozen analysis protocol/hash missing")

    structure_json = MD / "MD_STRUCTURE_VALIDATION.json"
    if structure_json.exists():
        structure = load(structure_json)
        for pdb_id in ("1W60", "8GLA"):
            try:
                audit = structure["preflight_min5000"][pdb_id]["prep_audit"]
                done = structure["preflight_min5000"][pdb_id]["done"]
                if len(audit["final_chains"]) != 3:
                    failures.append(f"{pdb_id} preflight did not produce 3 final chains")
                if not str(done.get("sanity_gate", "")).startswith("passed"):
                    failures.append(f"{pdb_id} minimization sanity gate did not pass")
                if done.get("minimization") is None:
                    failures.append(f"{pdb_id} minimization metadata missing")
            except KeyError as exc:
                failures.append(f"{pdb_id} structure validation missing key: {exc}")
    else:
        failures.append("machine-readable structure validation missing")

    status_path = MD / "md_readiness_status.json"
    if status_path.exists():
        status = load(status_path)
        if status.get("md_ready") is True:
            warnings.append("md_readiness_status.json claims md_ready=true; verifying independent gates")
    else:
        failures.append("md_readiness_status.json missing")

    smoke_done = MD / "outputs" / "8GLA" / "rep01" / "DONE.json"
    if not smoke_done.exists():
        failures.append("exact control smoke DONE.json missing in md_validation_4070/outputs/8GLA/rep01")
    else:
        smoke = load(smoke_done)
        if float(smoke.get("production_ns", 0.0)) < 0.1:
            failures.append("control smoke production_ns < 0.1")
        if not str(smoke.get("sanity_gate", "")).startswith("passed"):
            failures.append("control smoke sanity gate did not pass")

    analysis_summary = MD / "outputs" / "analysis" / "summary.json"
    if not analysis_summary.exists():
        failures.append("trajectory analysis summary missing")
    else:
        summary = load(analysis_summary)
        if summary.get("pbc_artifact_suspected_any"):
            failures.append("analysis reports PBC artifact")

    control_report = MD / "CONTROL_INTERPRETABILITY_REPORT.md"
    if not control_report.exists():
        failures.append("control interpretability report missing")
    elif "CONTROL INTERPRETABLE: PASS" not in control_report.read_text(encoding="utf-8"):
        failures.append("control interpretability is not PASS")

    human_decisions = ROOT / "research_os_memory" / "HUMAN_DECISIONS.md"
    approval_text = human_decisions.read_text(encoding="utf-8", errors="replace").lower() if human_decisions.exists() else ""
    if "gate 6" not in approval_text or "approved" not in approval_text:
        failures.append("human Gate-6 approval not recorded")

    dirty = git_dirty()
    if dirty:
        failures.append("git worktree is dirty; production provenance would be ambiguous")

    if warnings:
        print("WARNINGS:")
        for item in warnings:
            print(f"- {item}")
    if failures:
        print("MD READINESS GATE: FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    print("MD READINESS GATE: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
