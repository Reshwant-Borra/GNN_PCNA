#!/usr/bin/env python3
"""Small workflow helpers for the tmux-first PCNA MD launcher."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DEFAULT_OUTDIR = HERE / "outputs"
EXPECTED_ANALYSIS_PROTOCOL_SHA256 = "587f27cf2e402fe50b264d98d3d60fbbdcc8f9095025b2a89d12c7aebd633e56"


def load_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def run_text(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
    except Exception:
        return ""


def is_pid_alive(pid) -> bool:
    try:
        pid = int(pid)
        if pid <= 0:
            return False
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def rep_status(rep_dir: Path) -> dict:
    done = load_json(rep_dir / "DONE.json")
    failed = load_json(rep_dir / "FAILED.json")
    status = load_json(rep_dir / "STATUS.json", {})
    chk = rep_dir / "state.chk"
    dcd = rep_dir / "production.dcd"
    if done:
        state = "COMPLETE"
    elif failed:
        state = "FAILED"
    elif status.get("status") == "RUNNING" and is_pid_alive(status.get("pid")):
        state = "RUNNING"
    elif chk.exists():
        state = "RESUMABLE"
    elif status.get("status"):
        state = status.get("status")
    else:
        state = "NOT_STARTED"
    return {
        "replicate": rep_dir.name,
        "state": state,
        "production_ns": (done or status).get("production_ns")
        or (done or status).get("current_production_ns"),
        "step": (done or status).get("steps") or (done or status).get("current_step"),
        "dcd_bytes": dcd.stat().st_size if dcd.exists() else 0,
        "updated_utc": status.get("updated_utc") or (done or {}).get("finished_utc"),
        "reason": (failed or {}).get("reason"),
    }


def stage_status(outdir: Path) -> dict:
    runs = {}
    for pdb_dir in sorted(p for p in outdir.glob("*") if p.is_dir() and p.name != "analysis"):
        reps = [rep_status(r) for r in sorted(pdb_dir.glob("rep*")) if r.is_dir()]
        if reps:
            runs[pdb_dir.name] = reps
    smoke = load_json(outdir / "8GLA" / "rep01" / "DONE.json", {})
    smoke_pass = bool(smoke and float(smoke.get("production_ns", 0.0)) >= 0.1
                      and str(smoke.get("sanity_gate", "")).startswith("passed"))
    analysis = load_json(outdir / "analysis" / "summary.json", {})
    analysis_pass = bool(analysis and not analysis.get("pbc_artifact_suspected_any")
                         and not analysis.get("duplicate_frame_count_risk_any"))
    control_pass = control5_pass(outdir)[0]
    gate6 = gate6_approved()
    return {
        "outdir": str(outdir),
        "runs": runs,
        "gates": {
            "smoke_0p1ns": smoke_pass,
            "analysis_validation": analysis_pass,
            "control5_interpretability": control_pass,
            "gate6_human_approval": gate6,
        },
    }


def print_status(args) -> int:
    outdir = Path(args.outdir)
    sessions = run_text(["tmux", "list-sessions", "-F", "#{session_name}"]) if shutil.which("tmux") else ""
    if sessions:
        pcna = [s for s in sessions.splitlines() if s.startswith("pcna_")]
        print("tmux sessions: " + (", ".join(pcna) if pcna else "none"))
    else:
        print("tmux sessions: tmux unavailable or no sessions")
    status = stage_status(outdir)
    print("gates:")
    for key, value in status["gates"].items():
        print(f"  {key}: {'PASS' if value else 'PENDING'}")
    if not status["runs"]:
        print("runs: none")
        return 0
    print("runs:")
    for pdb, reps in status["runs"].items():
        for rep in reps:
            ns = rep.get("production_ns")
            ns_txt = f"{float(ns):.3f} ns" if ns is not None else "n/a"
            reason = f" ({rep['reason']})" if rep.get("reason") else ""
            print(f"  {pdb}/{rep['replicate']}: {rep['state']} step={rep.get('step')} "
                  f"prod={ns_txt} dcd={rep['dcd_bytes']} bytes{reason}")
    return 0


def gate6_approved() -> bool:
    text = (ROOT / "research_os_memory" / "HUMAN_DECISIONS.md").read_text(
        encoding="utf-8", errors="replace"
    ).lower() if (ROOT / "research_os_memory" / "HUMAN_DECISIONS.md").exists() else ""
    has_gate = "gate 6" in text or "gate-6" in text
    if not has_gate:
        return False
    negative = any(x in text for x in ("not approved", "not granted", "required_before_md"))
    return "approved" in text and not negative


def cuda_available() -> tuple[bool, str]:
    try:
        import openmm as mm
        platforms = [mm.Platform.getPlatform(i).getName() for i in range(mm.Platform.getNumPlatforms())]
    except Exception as exc:
        return False, f"OpenMM import/platform check failed: {exc}"
    if "CUDA" not in platforms:
        return False, f"OpenMM CUDA platform unavailable; platforms={platforms}"
    return True, "CUDA platform available"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def protocol_ok() -> tuple[bool, str]:
    protocol = HERE / "FROZEN_MD_ANALYSIS_PROTOCOL.json"
    if not protocol.exists():
        return False, "frozen analysis protocol missing"
    observed = sha256_file(protocol)
    if observed != EXPECTED_ANALYSIS_PROTOCOL_SHA256:
        return False, (
            "frozen analysis protocol hash mismatch: "
            f"{observed} != {EXPECTED_ANALYSIS_PROTOCOL_SHA256}"
        )
    return True, "frozen analysis protocol hash matches"


def production_gate(args) -> int:
    if not gate6_approved():
        print("PRODUCTION BLOCKED: Gate-6 human approval required.")
        return 1
    ok, why = protocol_ok()
    if not ok:
        print(f"PRODUCTION BLOCKED: {why}")
        return 1
    if platform.system() == "Darwin":
        print("PRODUCTION BLOCKED: production MD must run on a Linux NVIDIA GPU, not macOS.")
        return 1
    ok, why = cuda_available()
    if not ok:
        print(f"PRODUCTION BLOCKED: {why}")
        return 1
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "md_readiness_gate.py")],
                          cwd=ROOT, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout.rstrip())
    if proc.stderr:
        print(proc.stderr.rstrip())
    return proc.returncode


def complete_reps(outdir: Path, pdb: str, n_reps: int, min_ns: float) -> tuple[bool, list[str]]:
    missing = []
    for rep in range(1, n_reps + 1):
        done = load_json(outdir / pdb / f"rep{rep:02d}" / "DONE.json", {})
        if not done:
            missing.append(f"{pdb}/rep{rep:02d}: missing DONE.json")
            continue
        if float(done.get("production_ns", 0.0)) + 1e-9 < min_ns:
            missing.append(f"{pdb}/rep{rep:02d}: production_ns {done.get('production_ns')} < {min_ns}")
        if not str(done.get("sanity_gate", "")).startswith("passed"):
            missing.append(f"{pdb}/rep{rep:02d}: sanity gate not passed")
    return not missing, missing


def control5_pass(outdir: Path) -> tuple[bool, list[str]]:
    ok, issues = complete_reps(outdir, "8GLA", 3, 5.0)
    summary = load_json(outdir / "analysis" / "summary.json", {})
    if not summary:
        issues.append("analysis summary missing")
    else:
        if summary.get("pbc_artifact_suspected_any"):
            issues.append("analysis reports PBC artifact")
        if summary.get("duplicate_frame_count_risk_any"):
            issues.append("analysis reports duplicate frame-count risk")
        control_rows = [r for r in summary.get("per_replicate", []) if r.get("role") == "control"]
        if len(control_rows) < 3:
            issues.append(f"analysis has {len(control_rows)} control replicates < 3")
        control_gate = summary.get("control_interpretability_gate", {})
        if control_gate.get("status") != "PASS":
            issues.append(
                "trajectory-derived control gate not PASS: "
                + control_gate.get("reason", "missing control_interpretability_gate")
            )
        if control_gate.get("uses_frame_zero_or_static_apo_control_difference") is not False:
            issues.append("control gate does not explicitly reject static frame-zero separation")
    return ok and not issues, issues


def write_control_report(args) -> int:
    outdir = Path(args.outdir)
    ok, issues = control5_pass(outdir)
    report = HERE / "CONTROL_INTERPRETABILITY_REPORT.md"
    lines = [
        "# Control-First Interpretability Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "CONTROL INTERPRETABLE: " + ("PASS" if ok else "FAIL"),
        "",
    ]
    if issues:
        lines += ["## Issues", ""]
        lines += [f"- {x}" for x in issues]
    else:
        lines += [
            "Three 5 ns 8GLA control replicates completed with valid DONE/status files.",
            "The frozen analyzer read the trajectories without PBC or duplicate-frame-count artifacts.",
        ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {report}")
    return 0 if ok else 1


def benchmark_report(args) -> int:
    done = load_json(Path(args.outdir) / "8GLA" / "rep01" / "DONE.json", {})
    ns_day = done.get("ns_per_day_observed")
    if not ns_day:
        print("Benchmark result unavailable: DONE.json lacks ns_per_day_observed.")
        return 1
    ns_day = float(ns_day)
    hours_100 = 100.0 / ns_day * 24.0
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "ns_per_day": ns_day,
        "estimated_hours_per_100ns_replicate": hours_100,
        "estimated_hours_6_replicates_sequential": hours_100 * 6,
        "estimated_hours_6_replicates_on_3_gpus": hours_100 * 2,
        "estimated_hours_6_replicates_on_6_gpus": hours_100,
        "source_done": str(Path(args.outdir) / "8GLA" / "rep01" / "DONE.json"),
    }
    write_json(HERE / "BENCHMARK_REPORT.json", report)
    print(f"Benchmark: {ns_day:.2f} ns/day")
    print(f"Estimated 100 ns replicate: {hours_100:.1f} h")
    print(f"Estimated 6 replicates sequential: {hours_100 * 6:.1f} h")
    print(f"Estimated 6 replicates on 3 GPUs: {hours_100 * 2:.1f} h")
    print(f"Estimated 6 replicates on 6 GPUs: {hours_100:.1f} h")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["status", "production-gate", "control-report", "benchmark-report"])
    ap.add_argument("--outdir", default=str(DEFAULT_OUTDIR))
    args = ap.parse_args()
    if args.command == "status":
        return print_status(args)
    if args.command == "production-gate":
        return production_gate(args)
    if args.command == "control-report":
        return write_control_report(args)
    if args.command == "benchmark-report":
        return benchmark_report(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
