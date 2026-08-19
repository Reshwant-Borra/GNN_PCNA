#!/usr/bin/env python3
"""Small workflow helpers for the tmux-first PCNA MD launcher."""
from __future__ import annotations

import argparse
import secrets
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
EXPECTED_ANALYSIS_PROTOCOL_SHA256 = "c6ddd0fd4f2c9c05c1cf651358a7f59957c9cf077a5dea4c8331f4d4261f2df6"
EXPECTED_CONTROL_GATE_NAME = "trajectory_dynamic_control_gate_v2"
AUTHORIZATION_TTL_SECONDS = 6 * 60 * 60


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


# --------------------------------------------------------------------------------------
# Duration comparison.
#
# run_md.py accumulates production time as (total_steps - equil_steps) * dt_ns with
# dt_ns = 4.0/1e6. A COMPLETE 0.1 ns smoke therefore writes production_ns =
# 0.09999999999999999, and the old literal test `production_ns >= 0.1` evaluated False --
# a perfectly valid smoke could never pass its own gate. Integer step accounting is exact,
# so prefer it and fall back to a float comparison with a tolerance far below any duration
# difference that could matter scientifically (1e-6 ns = 1 fs).
# --------------------------------------------------------------------------------------
NS_TOLERANCE = 1e-6


def meets_ns_target(done: dict, target_ns: float, tolerance_ns: float = NS_TOLERANCE) -> bool:
    """Whether a DONE.json records at least ``target_ns`` of production time.

    Exact when the run recorded integer step counts; tolerant float compare otherwise.
    A genuinely truncated run still fails: the shortfall is orders of magnitude larger
    than the tolerance.
    """
    if not isinstance(done, dict):
        return False
    steps = done.get("production_steps")
    target_steps = done.get("target_production_steps")
    if isinstance(steps, int) and isinstance(target_steps, int) and target_steps > 0:
        timestep_fs = float(done.get("timestep_fs", 4.0) or 4.0)
        want = int(round(float(target_ns) / (timestep_fs / 1_000_000.0)))
        return steps >= want
    try:
        return float(done.get("production_ns", 0.0)) >= float(target_ns) - float(tolerance_ns)
    except (TypeError, ValueError):
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
    smoke_pass = bool(smoke
                      and meets_ns_target(smoke, 0.1)
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


# --------------------------------------------------------------------------------------
# Gate 6: structured, machine-readable human decision.
#
# The previous implementation substring-scanned research_os_memory/HUMAN_DECISIONS.md:
#     has_gate = "gate 6" in text or "gate-6" in text
#     negative = any(x in text for x in ("not approved", "not granted", "required_before_md"))
#     return "approved" in text and not negative
# Reproduced 2026-08-16, that authorizes production for BOTH of these documents:
#     "Gate 6: NOT YET APPROVED"        -> the negative list has "not approved", the text has
#                                          "not YET approved", so the negative never matches
#     "Gate 5 approved; Gate 6 pending" -> "gate 6" appears, "approved" appears, and the two
#                                          are never associated with each other
# Prose cannot carry an authorization. Gate 6 is now a signed-in-intent JSON artifact that a
# human must write deliberately, and it is bound to the exact commit, control-5 report and
# analysis protocol it was granted against.
# --------------------------------------------------------------------------------------
GATE6_DECISION_PATH = HERE / "GATE6_DECISION.json"
GATE6_KIND = "PCNA_MD_GATE6_DECISION"
GATE6_SCHEMA_VERSION = 1
GATE6_REQUIRED_FIELDS = (
    "schema_version", "kind", "approved", "approved_by", "approved_utc",
    "commit", "control5_report_sha256", "analysis_protocol_sha256", "notes",
)


def _sha256_or_none(path: Path) -> str | None:
    return sha256_file(path) if path.exists() else None


def gate6_decision(decision_path: Path | None = None, strict_bindings: bool = True) -> dict:
    """Evaluate the Gate-6 decision artifact. Fail closed on every abnormal condition.

    Returns {"approved": bool, "reasons": [...], "decision": <payload or None>}.
    ``strict_bindings=False`` skips commit/report/protocol binding checks; it exists so
    ``status`` can display "a decision exists but is bound to another commit" instead of
    silently printing PENDING.
    """
    path = Path(decision_path) if decision_path else GATE6_DECISION_PATH
    reasons: list[str] = []
    if not path.exists():
        return {"approved": False, "decision": None,
                "reasons": [f"no Gate-6 decision artifact at {path}"]}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"approved": False, "decision": None,
                "reasons": [f"Gate-6 decision is not valid JSON: {exc}"]}
    if not isinstance(payload, dict):
        return {"approved": False, "decision": None,
                "reasons": ["Gate-6 decision is not a JSON object"]}

    missing = [f for f in GATE6_REQUIRED_FIELDS if f not in payload]
    if missing:
        reasons.append(f"Gate-6 decision is missing required fields: {', '.join(missing)}")
    if payload.get("kind") != GATE6_KIND:
        reasons.append(f"Gate-6 decision kind is {payload.get('kind')!r}, expected {GATE6_KIND!r}")
    if payload.get("schema_version") != GATE6_SCHEMA_VERSION:
        reasons.append(
            f"Gate-6 schema_version {payload.get('schema_version')!r} != {GATE6_SCHEMA_VERSION}")
    if payload.get("approved") is not True:
        reasons.append(f"Gate-6 approved is {payload.get('approved')!r}, not boolean true")
    approver = str(payload.get("approved_by") or "").strip()
    if not approver:
        reasons.append("Gate-6 approved_by is empty; a human reviewer must be named")
    approved_utc = str(payload.get("approved_utc") or "").strip()
    if not approved_utc:
        reasons.append("Gate-6 approved_utc is empty")
    else:
        try:
            datetime.fromisoformat(approved_utc.replace("Z", "+00:00"))
        except Exception:
            reasons.append(f"Gate-6 approved_utc {approved_utc!r} is not an ISO-8601 timestamp")
    expires = str(payload.get("expires_utc") or "").strip()
    if expires:
        try:
            if datetime.now(timezone.utc) > datetime.fromisoformat(expires.replace("Z", "+00:00")):
                reasons.append(f"Gate-6 decision expired at {expires}")
        except Exception:
            reasons.append(f"Gate-6 expires_utc {expires!r} is not an ISO-8601 timestamp")

    if strict_bindings:
        head = run_text(["git", "-C", str(ROOT), "rev-parse", "HEAD"])
        if head and payload.get("commit") != head:
            reasons.append(
                f"Gate-6 decision was granted against commit {payload.get('commit')!r}, "
                f"but HEAD is {head!r}")
        want_protocol = _sha256_or_none(HERE / "FROZEN_MD_ANALYSIS_PROTOCOL.json")
        if payload.get("analysis_protocol_sha256") != want_protocol:
            reasons.append(
                "Gate-6 decision analysis_protocol_sha256 does not match the current "
                "FROZEN_MD_ANALYSIS_PROTOCOL.json")
        want_report = _sha256_or_none(HERE / "CONTROL_INTERPRETABILITY_REPORT.md")
        if want_report is None:
            reasons.append(
                "Gate-6 requires a control-5 interpretability report, but "
                "CONTROL_INTERPRETABILITY_REPORT.md does not exist")
        elif payload.get("control5_report_sha256") != want_report:
            reasons.append(
                "Gate-6 decision control5_report_sha256 does not match the current "
                "CONTROL_INTERPRETABILITY_REPORT.md")

    return {"approved": not reasons, "decision": payload, "reasons": reasons}


def gate6_approved() -> bool:
    """Boolean Gate-6 authorization. True only for a valid, correctly bound approval."""
    return bool(gate6_decision()["approved"])


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


def write_production_authorization(args) -> Path:
    """Write a short-lived authorization consumed by run_md.py.

    This is defense in depth, not the primary gate. The primary gate remains the
    fail-closed production_gate() checks below. The token records the current
    gate evidence and the exact production command contract that run_md.py must
    match before it will run production-scale trajectories.
    """
    outdir = Path(args.outdir)
    git = {
        "commit": run_text(["git", "-C", str(ROOT), "rev-parse", "HEAD"]),
        "branch": run_text(["git", "-C", str(ROOT), "rev-parse", "--abbrev-ref", "HEAD"]),
        "status_short": run_text(["git", "-C", str(ROOT), "status", "--short"]),
    }
    now = datetime.now(timezone.utc)
    payload = {
        "schema_version": 1,
        "kind": "PCNA_MD_PRODUCTION_AUTHORIZATION",
        "authorized_by": "md_validation_4070/md_workflow.py production-gate",
        "created_utc": now.isoformat(),
        "expires_utc": datetime.fromtimestamp(
            now.timestamp() + AUTHORIZATION_TTL_SECONDS, timezone.utc
        ).isoformat(),
        "nonce": secrets.token_hex(32),
        "pocket": args.pocket,
        "allowed_runs": ["control", "apo"],
        "replicates": int(args.replicates),
        "ns": float(args.ns),
        "required_platform": "CUDA",
        "require_platform": True,
        "outdir": str(outdir.resolve()),
        "git": git,
        "frozen_analysis_protocol_sha256": sha256_file(HERE / "FROZEN_MD_ANALYSIS_PROTOCOL.json"),
        "md_workflow_sha256": sha256_file(HERE / "md_workflow.py"),
        "run_md_sha256": sha256_file(HERE / "run_md.py"),
        "gate_evidence": {
            "gate6_human_approval": gate6_approved(),
            "protocol_ok": protocol_ok()[0],
            "cuda_available": cuda_available()[0],
            "readiness_gate_invoked": True,
        },
    }
    path = outdir / ".production_authorization.json"
    write_json(path, payload)
    return path


def production_gate(args) -> int:
    decision = gate6_decision()
    if not decision["approved"]:
        print("PRODUCTION BLOCKED: Gate-6 human approval required.")
        for reason in decision["reasons"]:
            print(f"  - {reason}")
        print(f"\nA human reviewer must create {GATE6_DECISION_PATH} deliberately.")
        print("This tool will never create it. See GATE6_DECISION.template.json and")
        print("md_validation_4070/CLOUD_MD_RUNBOOK.md section J.")
        return 1
    # control-5 must actually have passed, not merely have a report file on disk
    ok, issues = control5_pass(Path(args.outdir))
    if not ok:
        print("PRODUCTION BLOCKED: control-5 interpretability gate has not passed.")
        for issue in issues:
            print(f"  - {issue}")
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
    if proc.returncode != 0:
        return proc.returncode
    if getattr(args, "authorize_run", False):
        path = write_production_authorization(args)
        print(f"PRODUCTION AUTHORIZED FOR CANONICAL WORKFLOW: {path}")
    return 0


def complete_reps(outdir: Path, pdb: str, n_reps: int, min_ns: float) -> tuple[bool, list[str]]:
    missing = []
    for rep in range(1, n_reps + 1):
        done = load_json(outdir / pdb / f"rep{rep:02d}" / "DONE.json", {})
        if not done:
            missing.append(f"{pdb}/rep{rep:02d}: missing DONE.json")
            continue
        if not meets_ns_target(done, min_ns):
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
        if control_gate.get("rejects_static_structure_plus_per_frame_noise") is not True:
            issues.append(
                "control gate does not declare rejection of the static-structure-plus-noise "
                "null; a pre-v2 analyzer produced this summary")
        if control_gate.get("name") != EXPECTED_CONTROL_GATE_NAME:
            issues.append(
                f"control gate is {control_gate.get('name')!r}, expected "
                f"{EXPECTED_CONTROL_GATE_NAME!r}")
        if summary.get("diagnostic_only"):
            issues.append("analysis summary is DIAGNOSTIC_ONLY and cannot satisfy a scientific gate")
    return ok and not issues, issues


def write_control_report(args) -> int:
    outdir = Path(args.outdir)
    ok, issues = control5_pass(outdir)
    report = HERE / "CONTROL_INTERPRETABILITY_REPORT.md"
    verdict = "PASS" if ok else "FAIL"

    # Stage identity: which outdir (and therefore which MD stage -- control5, control20, ...)
    # produced this verdict. The report path is fixed, so without this a later stage silently
    # overwrites an earlier stage's DISTINCT verdict with nothing in the file recording that a
    # different run produced it. Archive the outgoing report first whenever the outdir or the
    # verdict is about to change, mirroring the manual backup convention already used for the
    # Control-5 FAIL result (CONTROL_INTERPRETABILITY_REPORT_5ns_FAIL_2of3_20260817_163213.md).
    try:
        stage_outdir = str(outdir.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        stage_outdir = str(outdir)
    if report.exists():
        prev_text = report.read_text(encoding="utf-8")
        prev_outdir = prev_verdict = None
        for line in prev_text.splitlines():
            if line.startswith("Source outdir:"):
                prev_outdir = line.split(":", 1)[1].strip()
            elif line.startswith("CONTROL INTERPRETABLE:"):
                prev_verdict = line.split(":", 1)[1].strip()
        if prev_outdir is not None and (prev_outdir != stage_outdir or prev_verdict != verdict):
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            # Use only the outdir's basename (sanitized) in the filename -- prev_outdir may be
            # an arbitrary absolute path (e.g. a custom --outdir outside ROOT) and Windows caps
            # total path length, so the full path belongs in the file's "Source outdir:" line,
            # not in the filename.
            base = "".join(c if (c.isalnum() or c in "-_.") else "_"
                           for c in Path(prev_outdir).name)[:60] or "outdir"
            archive = HERE / f"CONTROL_INTERPRETABILITY_REPORT_ARCHIVED_{base}_{prev_verdict}_{ts}.md"
            archive.write_text(prev_text, encoding="utf-8")
            print(f"Archived prior report ({prev_outdir}: {prev_verdict}) -> {archive}")

    lines = [
        "# Control-First Interpretability Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Source outdir: {stage_outdir}",
        "",
        "CONTROL INTERPRETABLE: " + verdict,
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


# --------------------------------------------------------------------------------------
# Compact cloud-result bundle.
#
# Production trajectories are tens of GB and STAY on the cloud instance. Everything
# scientifically necessary is derived there by analyze_md.py; this packages only the derived
# results plus a manifest of the large source files' SHA-256, so the compact bundle remains
# verifiably tied to trajectories that were never transferred.
# --------------------------------------------------------------------------------------
BUNDLE_EXCLUDE_SUFFIXES = (".dcd", ".chk", ".npy", ".xtc", ".trr", ".h5", ".dat")
BUNDLE_EXCLUDE_NAMES = ("system_solvated.pdb", "prepared_protein.pdb",
                        "assembly_protein_raw.pdb", "state.chk", "state.prev.chk")
LARGE_SOURCE_PATTERNS = ("production.dcd", "equilibration.dcd", "system_solvated.pdb",
                         "state.chk", "prepared_protein.pdb")


def _bundle_candidates(outdir: Path) -> list[Path]:
    """Compact derived results and small per-replicate provenance. No trajectories."""
    files: list[Path] = []
    adir = outdir / "analysis"
    if adir.is_dir():
        files += [p for p in sorted(adir.rglob("*")) if p.is_file()]
    for rep_dir in sorted(outdir.glob("*/rep*")):
        if not rep_dir.is_dir():
            continue
        for name in ("DONE.json", "FAILED.json", "STATUS.json", "PROVENANCE.json",
                     "MINIMIZATION.json", "EQUILIBRATION.json", "RESUME_AUDIT.json",
                     "checkpoint_meta.json", "production.log", "equilibration.log"):
            p = rep_dir / name
            if p.is_file():
                files.append(p)
    for pdb_dir in sorted(outdir.glob("*")):
        for name in ("pocket_definition.json", "storage_preflight.json"):
            p = pdb_dir / name
            if p.is_file():
                files.append(p)
        p = pdb_dir / "prep" / "prep_audit.json"
        if p.is_file():
            files.append(p)
    return [p for p in files
            if p.suffix.lower() not in BUNDLE_EXCLUDE_SUFFIXES
            and p.name not in BUNDLE_EXCLUDE_NAMES]


def _large_source_manifest(outdir: Path) -> list[dict]:
    """SHA-256 + size of every large cloud-resident file the results were derived from."""
    entries = []
    for pattern in LARGE_SOURCE_PATTERNS:
        for p in sorted(outdir.rglob(pattern)):
            if not p.is_file():
                continue
            entries.append({
                "path": str(p.relative_to(outdir)),
                "absolute_path_on_cloud_instance": str(p.resolve()),
                "bytes": p.stat().st_size,
                "sha256": sha256_file(p),
                "included_in_bundle": False,
            })
    return entries


def make_bundle(args) -> int:
    import tarfile

    outdir = Path(args.outdir)
    if not outdir.is_dir():
        print(f"BUNDLE FAILED: no output directory at {outdir}")
        return 1
    summary = load_json(outdir / "analysis" / "summary.json")
    if not summary and not args.allow_missing_summary:
        print("BUNDLE FAILED: outputs/analysis/summary.json is missing. Run './md.sh analyze' "
              "first, or pass --allow-missing-summary to bundle whatever exists.")
        return 1

    files = _bundle_candidates(outdir)
    if not files:
        print(f"BUNDLE FAILED: nothing to package under {outdir}")
        return 1
    sources = _large_source_manifest(outdir)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = Path(args.bundle_out) if args.bundle_out else (HERE / f"pcna_md_results_{stamp}.tar.gz")
    manifest = {
        "kind": "PCNA_MD_COMPACT_RESULT_BUNDLE",
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "outdir": str(outdir.resolve()),
        "git": {
            "commit": run_text(["git", "-C", str(ROOT), "rev-parse", "HEAD"]),
            "branch": run_text(["git", "-C", str(ROOT), "rev-parse", "--abbrev-ref", "HEAD"]),
            "dirty": bool(run_text(["git", "-C", str(ROOT), "status", "--short"])),
        },
        "analysis_protocol_sha256": sha256_file(HERE / "FROZEN_MD_ANALYSIS_PROTOCOL.json"),
        "analysis_code_sha256": sha256_file(HERE / "analyze_md.py"),
        "run_md_sha256": sha256_file(HERE / "run_md.py"),
        "md_workflow_sha256": sha256_file(HERE / "md_workflow.py"),
        "diagnostic_only": bool((summary or {}).get("diagnostic_only")),
        "control_interpretability_gate": (summary or {}).get("control_interpretability_gate", {}).get("status"),
        "excluded_by_policy": {
            "suffixes": list(BUNDLE_EXCLUDE_SUFFIXES),
            "names": list(BUNDLE_EXCLUDE_NAMES),
            "reason": "raw trajectories, checkpoints and solvated topologies remain on the "
                      "cloud instance; they are referenced by SHA-256 below instead",
        },
        "large_cloud_resident_sources": sources,
        "large_cloud_resident_total_bytes": sum(e["bytes"] for e in sources),
        "included_files": [
            {"path": str(p.relative_to(outdir)), "bytes": p.stat().st_size,
             "sha256": sha256_file(p)}
            for p in files
        ],
    }
    manifest_path = outdir / "analysis" / "BUNDLE_MANIFEST.json"
    write_json(manifest_path, manifest)

    dest.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(dest, "w:gz") as tar:
        for p in files + [manifest_path]:
            tar.add(p, arcname=str(Path("pcna_md_results") / p.relative_to(outdir)))

    size = dest.stat().st_size
    print(f"Bundle: {dest}")
    print(f"  files            : {len(files) + 1}")
    print(f"  bundle size      : {size / (1024 ** 2):.2f} MiB")
    print(f"  excluded raw data: {manifest['large_cloud_resident_total_bytes'] / (1024 ** 3):.2f} GiB "
          f"across {len(sources)} file(s), referenced by SHA-256 in BUNDLE_MANIFEST.json")
    if manifest["diagnostic_only"]:
        print("  WARNING: the analysis summary is DIAGNOSTIC_ONLY / "
              "NOT_FOR_SCIENTIFIC_INTERPRETATION")
    for entry in manifest["included_files"]:
        if entry["path"].endswith(".dcd"):
            print("BUNDLE FAILED: a trajectory leaked into the bundle")
            return 1
    return 0


# --------------------------------------------------------------------------------------
# Storage and memory planning for every stage.
#
# The storage preflight in run_md.py only ran for the stage actually being launched, so a
# user could reach production and only then discover the disk was too small. This computes
# the whole ladder up front, and adds the ANALYSIS-side memory figure that the streaming
# analyzer needs -- the failure the audit was most worried about is dying after a successful
# expensive simulation because the analysis loaded every water for every frame.
# --------------------------------------------------------------------------------------
# Human PCNA is 261 aa; the biological assembly is a homotrimer (783 aa). With hydrogens
# that is ~12.7k protein atoms; TIP3P at 1.0 nm padding around the ~9.0 x 9.0 x 4.5 nm ring
# adds ~26k waters. Override with --atoms once smoke has written the real count.
DEFAULT_SOLVATED_ATOMS = 100_000
DEFAULT_PROTEIN_ATOMS = 12_700

STAGE_PLAN = [
    # name,               replicates, ns/rep, report_ps, equil_ns
    ("smoke",                    1,     0.1,     50.0,     2.0),
    ("benchmark",                1,    0.02,     50.0,     0.0),
    ("control5 (3 x 5 ns)",      3,     5.0,     50.0,     2.0),
    ("production control",       3,   100.0,     50.0,     2.0),
    ("production apo",           3,   100.0,     50.0,     2.0),
]


def stage_estimates(solvated_atoms: int, protein_atoms: int, safety: float) -> list[dict]:
    rows = []
    total_bytes = 0
    for name, reps, ns, report_ps, equil_ns in STAGE_PLAN:
        dt_ps = 0.004                      # 4 fs with HMR
        frames = int(round(ns * 1000.0 / report_ps))
        dcd = 4096 + 12 * solvated_atoms * frames
        log = max(4096, frames * 512)
        chk = max(32 << 20, solvated_atoms * 128)
        raw = (dcd + log + chk) * reps
        total_bytes += raw
        coord = protein_atoms * 3 * 4 * max(frames, 1)
        rows.append({
            "stage": name,
            "replicates": reps,
            "ns_per_replicate": ns,
            "frames_per_replicate": frames,
            "dcd_bytes_per_replicate": dcd,
            "stage_bytes": raw,
            "stage_gib": raw / (1024 ** 3),
            "required_free_gib": raw * safety / (1024 ** 3),
            "analysis_peak_ram_gib": coord * 4 / (1024 ** 3),
            "analysis_peak_ram_if_solvent_loaded_gib":
                solvated_atoms * 3 * 4 * max(frames, 1) * 4 / (1024 ** 3),
        })
    rows.append({
        "stage": "TOTAL (all stages resident)",
        "replicates": sum(r for _, r, *_ in STAGE_PLAN),
        "ns_per_replicate": None, "frames_per_replicate": None,
        "dcd_bytes_per_replicate": None,
        "stage_bytes": total_bytes,
        "stage_gib": total_bytes / (1024 ** 3),
        "required_free_gib": total_bytes * safety / (1024 ** 3),
        "analysis_peak_ram_gib": max(r["analysis_peak_ram_gib"] for r in rows),
        "analysis_peak_ram_if_solvent_loaded_gib":
            max(r["analysis_peak_ram_if_solvent_loaded_gib"] for r in rows),
    })
    return rows


def print_estimates(args) -> int:
    rows = stage_estimates(args.atoms, args.protein_atoms, args.storage_safety_factor)
    print(f"Assumed solvated system : {args.atoms:,} atoms "
          f"(override with --atoms once smoke reports the real count)")
    print(f"Assumed protein subset  : {args.protein_atoms:,} atoms "
          "(what the analyzer actually loads)")
    print(f"Storage safety factor   : {args.storage_safety_factor}")
    print()
    print(f"{'stage':<30}{'reps':>5}{'frames':>8}{'DCD/rep':>12}{'stage':>10}"
          f"{'need free':>11}{'analysis RAM':>14}{'if solvent':>12}")
    for r in rows:
        dcd = (f"{r['dcd_bytes_per_replicate'] / (1024 ** 3):.2f} GiB"
               if r["dcd_bytes_per_replicate"] else "-")
        frames = r["frames_per_replicate"] if r["frames_per_replicate"] is not None else "-"
        print(f"{r['stage']:<30}{r['replicates']:>5}{str(frames):>8}{dcd:>12}"
              f"{r['stage_gib']:>9.2f}G{r['required_free_gib']:>10.2f}G"
              f"{r['analysis_peak_ram_gib']:>13.2f}G"
              f"{r['analysis_peak_ram_if_solvent_loaded_gib']:>11.2f}G")
    usage = shutil.disk_usage(Path(args.outdir) if Path(args.outdir).exists() else ROOT)
    total = rows[-1]
    print()
    print(f"Free space at {args.outdir}: {usage.free / (1024 ** 3):.1f} GiB")
    verdict = usage.free >= total["required_free_gib"] * (1024 ** 3)
    print(f"Sufficient for the full ladder with safety factor: {verdict}")
    print()
    print("Notes:")
    print("  * 'analysis RAM' is the streaming analyzer's peak: it loads the PROTEIN atom")
    print("    subset only (md.load(..., atom_indices=protein)), four working copies assumed.")
    print("  * 'if solvent' is what the pre-2026-08-16 analyzer would have needed by loading")
    print("    the whole solvated box; that is the column that used to kill the analysis")
    print("    after an expensive simulation had already succeeded.")
    print("  * Raw trajectories are NEVER deleted automatically by any command here.")
    return 0 if verdict else 1


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
    ap.add_argument("command", choices=["status", "production-gate", "control-report",
                                        "benchmark-report", "bundle", "gate6-status",
                                        "estimates"])
    ap.add_argument("--outdir", default=str(DEFAULT_OUTDIR))
    ap.add_argument("--bundle-out", default=None,
                    help="destination .tar.gz for the compact result bundle")
    ap.add_argument("--allow-missing-summary", action="store_true",
                    help="package whatever derived results exist even without summary.json")
    ap.add_argument("--atoms", type=int, default=DEFAULT_SOLVATED_ATOMS,
                    help="solvated system atom count for storage/memory estimates")
    ap.add_argument("--protein-atoms", type=int, default=DEFAULT_PROTEIN_ATOMS,
                    help="protein-only atom count the analyzer loads")
    ap.add_argument("--storage-safety-factor", type=float, default=1.5)
    ap.add_argument("--authorize-run", action="store_true",
                    help="after all production gates pass, write run_md.py authorization evidence")
    ap.add_argument("--pocket", default="final_consensus_1w60_20260815")
    ap.add_argument("--replicates", type=int, default=3)
    ap.add_argument("--ns", type=float, default=100.0)
    args = ap.parse_args()
    if args.command == "status":
        return print_status(args)
    if args.command == "production-gate":
        return production_gate(args)
    if args.command == "control-report":
        return write_control_report(args)
    if args.command == "benchmark-report":
        return benchmark_report(args)
    if args.command == "bundle":
        return make_bundle(args)
    if args.command == "estimates":
        return print_estimates(args)
    if args.command == "gate6-status":
        decision = gate6_decision()
        print(f"Gate-6 decision artifact : {GATE6_DECISION_PATH}")
        print(f"Gate-6 approved          : {decision['approved']}")
        if decision["reasons"]:
            print("Blocking reasons:")
            for reason in decision["reasons"]:
                print(f"  - {reason}")
        return 0 if decision["approved"] else 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
