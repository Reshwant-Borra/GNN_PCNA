"""
ResearchOS Orchestrator — permission-aware task dispatcher.

Central routing layer between external frontends (e.g. agents/telegram_gateway.py)
and the GNN-PCNA pipeline. Frontends submit named *intents*; the Orchestrator
maps each intent to a subprocess command against existing pipeline scripts,
runs it in a worker thread, streams progress events to subscribed listeners,
and writes artifacts under data/artifacts/<task_id>/.

Risky / long-running intents are queued and require owner approval before
they run (anything that re-trains, re-splits, overwrites checkpoints, deletes
files, force-pushes, or runs expensive compute).

This module DOES NOT call Claude Code. It only invokes the project's own
Python pipeline entrypoints via subprocess.

Usage:
    # Programmatic
    from agents.orchestrator import Orchestrator, Role
    orch = Orchestrator()
    task = orch.submit(user="advay", role=Role.OWNER, intent="status")

    # CLI (local debugging)
    python agents/orchestrator.py list-intents
    python agents/orchestrator.py run --user advay --role owner --intent status
    python agents/orchestrator.py run --user advay --role owner --intent eval
    python agents/orchestrator.py pending
    python agents/orchestrator.py approve --task-id <id> --user advay
"""
from __future__ import annotations

import argparse
import enum
import json
import queue
import shlex
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

REPO_ROOT     = Path(__file__).parent.parent
ARTIFACT_ROOT = REPO_ROOT / "data" / "artifacts"


class Role(str, enum.Enum):
    OWNER        = "owner"
    COLLABORATOR = "collaborator"
    VIEWER       = "viewer"


class TaskState(str, enum.Enum):
    QUEUED            = "queued"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED          = "approved"
    RUNNING           = "running"
    SUCCEEDED         = "succeeded"
    FAILED            = "failed"
    DENIED            = "denied"
    CANCELLED         = "cancelled"


@dataclass
class Intent:
    name:           str
    description:    str
    min_role:       Role
    risky:          bool
    long_running:   bool
    # builder receives the orchestrator + task and returns argv for subprocess
    build_cmd:      Callable[["Orchestrator", "Task"], list[str]]


@dataclass
class Task:
    task_id:       str
    user:          str
    role:          Role
    intent:        str
    args:          dict[str, Any]
    state:         TaskState                = TaskState.QUEUED
    created_at:    str                      = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at:    str | None               = None
    finished_at:   str | None               = None
    exit_code:     int | None               = None
    artifact_dir:  str | None               = None
    artifacts:     list[str]                = field(default_factory=list)
    log_path:      str | None               = None
    note:          str                      = ""
    approver:      str | None               = None

    def to_public(self) -> dict[str, Any]:
        d = asdict(self)
        d["role"]  = self.role.value
        d["state"] = self.state.value
        return d


# ── Intent registry ──────────────────────────────────────────────────────────

def _py() -> str:
    return sys.executable


def _cmd_status(o: "Orchestrator", t: Task) -> list[str]:
    # Internal status — no subprocess; orchestrator handles it directly
    return []


def _cmd_crawl(o: "Orchestrator", t: Task) -> list[str]:
    cmd = [_py(), "agents/pcna_crawler.py", "--workers", str(t.args.get("workers", 6))]
    sources = t.args.get("sources")
    if sources:
        cmd += ["--sources", *sources]
    return cmd


def _cmd_verify(o: "Orchestrator", t: Task) -> list[str]:
    return [_py(), "agents/gemma_verifier.py"]


def _cmd_vault(o: "Orchestrator", t: Task) -> list[str]:
    return [_py(), "agents/obsidian_writer.py"]


def _cmd_fetch(o: "Orchestrator", t: Task) -> list[str]:
    catalog = REPO_ROOT / "data" / "catalog" / "pcna_data_catalog.json"
    cmd     = [_py(), "-m", "src.data_processing.fetch_structures", "--strip"]
    if catalog.exists():
        cmd += ["--catalog", str(catalog), "--limit", str(t.args.get("limit", 100))]
    else:
        cmd += ["--cryptosite"]
    return cmd


def _cmd_graphs(o: "Orchestrator", t: Task) -> list[str]:
    return [_py(), "scripts/build_graphs.py", "--cutoff", str(t.args.get("cutoff", 8.0))]


def _cmd_split(o: "Orchestrator", t: Task) -> list[str]:
    return [_py(), "scripts/make_split.py"]


def _cmd_train(o: "Orchestrator", t: Task) -> list[str]:
    train_dir = REPO_ROOT / "data" / "cryptosite" / "train"
    val_dir   = REPO_ROOT / "data" / "cryptosite" / "val"
    ckpt_dir  = REPO_ROOT / "checkpoints"
    ckpt_dir.mkdir(exist_ok=True)
    return [_py(), "-m", "src.training.train",
            "--train_dir", str(train_dir),
            "--val_dir",   str(val_dir),
            "--checkpoint_dir", str(ckpt_dir),
            "--model_size", t.args.get("model_size", "small"),
            "--epochs",     str(t.args.get("epochs", 100)),
            "--batch_size", str(t.args.get("batch_size", 16)),
            "--lr",         str(t.args.get("lr", 1e-3)),
            "--patience",   str(t.args.get("patience", 10))]


def _cmd_eval(o: "Orchestrator", t: Task) -> list[str]:
    return [_py(), "-m", "src.evaluation.score_pockets",
            "--checkpoint", t.args.get("checkpoint", "checkpoints/best.pt")]


def _cmd_inference(o: "Orchestrator", t: Task) -> list[str]:
    cmd = [_py(), "scripts/bulk_inference.py"]
    if "checkpoint" in t.args:
        cmd += ["--checkpoint", t.args["checkpoint"]]
    return cmd


def _cmd_verify_claims(o: "Orchestrator", t: Task) -> list[str]:
    return [_py(), "scripts/verify_all_claims.py"]


def _cmd_pipeline(o: "Orchestrator", t: Task) -> list[str]:
    cmd = [_py(), "scripts/run_pipeline.py"]
    if t.args.get("from_stage"):
        cmd += ["--from", t.args["from_stage"]]
    if t.args.get("only"):
        cmd += ["--only", *t.args["only"]]
    if t.args.get("skip"):
        cmd += ["--skip", *t.args["skip"]]
    return cmd


def _cmd_docker_build(o: "Orchestrator", t: Task) -> list[str]:
    out = Path(t.artifact_dir) if t.artifact_dir else ARTIFACT_ROOT / t.task_id
    cmd = [_py(), "agents/docker_packager.py", "docker", "--out", str(out)]
    if t.args.get("cuda"):
        cmd += ["--cuda"]
    if t.args.get("build"):
        cmd += ["--build"]
    return cmd


def _cmd_bundle(o: "Orchestrator", t: Task) -> list[str]:
    out = Path(t.artifact_dir) if t.artifact_dir else ARTIFACT_ROOT / t.task_id
    return [_py(), "agents/docker_packager.py", "bundle", "--out", str(out)]


def _cmd_shell(o: "Orchestrator", t: Task) -> list[str]:
    cmd = t.args.get("cmd", "")
    if not cmd:
        raise ValueError("shell intent requires a cmd arg")
    return ["bash", "-c", cmd]


def _cmd_ingest(o: "Orchestrator", t: Task) -> list[str]:
    cmd = [_py(), "agents/ingest.py", "ingest"]
    for p in t.args.get("paths", []):
        cmd += ["--path", str(p)]
    if t.args.get("dir"):
        cmd += ["--dir", str(t.args["dir"])]
    if t.args.get("transcript"):
        cmd += ["--transcript", str(t.args["transcript"])]
    if t.args.get("source_type"):
        cmd += ["--source-type", t.args["source_type"]]
    return cmd


INTENTS: dict[str, Intent] = {
    "status": Intent(
        name="status", description="Show orchestrator + repo status",
        min_role=Role.VIEWER, risky=False, long_running=False,
        build_cmd=_cmd_status,
    ),
    "crawl": Intent(
        name="crawl", description="Run multi-source crawler",
        min_role=Role.COLLABORATOR, risky=False, long_running=True,
        build_cmd=_cmd_crawl,
    ),
    "verify": Intent(
        name="verify", description="Gemma L6 credibility scoring",
        min_role=Role.COLLABORATOR, risky=False, long_running=True,
        build_cmd=_cmd_verify,
    ),
    "vault": Intent(
        name="vault", description="Write verified records to Obsidian vault",
        min_role=Role.COLLABORATOR, risky=False, long_running=False,
        build_cmd=_cmd_vault,
    ),
    "fetch": Intent(
        name="fetch", description="Download PDB structures",
        min_role=Role.COLLABORATOR, risky=False, long_running=True,
        build_cmd=_cmd_fetch,
    ),
    "graphs": Intent(
        name="graphs", description="Build PyG graph .pt files",
        min_role=Role.COLLABORATOR, risky=False, long_running=True,
        build_cmd=_cmd_graphs,
    ),
    "split": Intent(
        name="split", description="Re-generate train/val/test split (invalidates claims)",
        min_role=Role.COLLABORATOR, risky=True, long_running=False,
        build_cmd=_cmd_split,
    ),
    "train": Intent(
        name="train", description="Train CrypticGNN (overwrites checkpoints, invalidates claims)",
        min_role=Role.COLLABORATOR, risky=True, long_running=True,
        build_cmd=_cmd_train,
    ),
    "eval": Intent(
        name="eval", description="Score pockets with current checkpoint",
        min_role=Role.COLLABORATOR, risky=False, long_running=False,
        build_cmd=_cmd_eval,
    ),
    "inference": Intent(
        name="inference", description="Bulk inference over PCNA structures",
        min_role=Role.COLLABORATOR, risky=False, long_running=True,
        build_cmd=_cmd_inference,
    ),
    "verify_claims": Intent(
        name="verify_claims", description="Re-validate held-out AUROC and scientific claims",
        min_role=Role.COLLABORATOR, risky=False, long_running=True,
        build_cmd=_cmd_verify_claims,
    ),
    "pipeline": Intent(
        name="pipeline", description="Run full end-to-end pipeline (risky: re-splits + re-trains)",
        min_role=Role.COLLABORATOR, risky=True, long_running=True,
        build_cmd=_cmd_pipeline,
    ),
    "docker_build": Intent(
        name="docker_build", description="Generate reproducible Dockerfile (optional image build)",
        min_role=Role.COLLABORATOR, risky=False, long_running=True,
        build_cmd=_cmd_docker_build,
    ),
    "bundle": Intent(
        name="bundle", description="Produce a stripped repo .zip bundle",
        min_role=Role.COLLABORATOR, risky=False, long_running=True,
        build_cmd=_cmd_bundle,
    ),
    "shell": Intent(
        name="shell", description="Run any arbitrary bash command or script on the compute machine (cmd arg required)",
        min_role=Role.OWNER, risky=True, long_running=True,
        build_cmd=_cmd_shell,
    ),
    "ingest": Intent(
        name="ingest", description="Ingest documents into source registry + Obsidian vault (Agent 21)",
        min_role=Role.COLLABORATOR, risky=False, long_running=False,
        build_cmd=_cmd_ingest,
    ),
}


_ROLE_RANK = {Role.VIEWER: 0, Role.COLLABORATOR: 1, Role.OWNER: 2}


def _role_meets(actor: Role, required: Role) -> bool:
    return _ROLE_RANK[actor] >= _ROLE_RANK[required]


# ── Event bus ────────────────────────────────────────────────────────────────

@dataclass
class Event:
    task_id: str
    kind:    str       # "submitted" | "queued" | "approval_required" | "approved"
                       # | "denied" | "started" | "log" | "finished" | "cancelled"
    payload: dict[str, Any] = field(default_factory=dict)
    ts:      str            = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ── Orchestrator ─────────────────────────────────────────────────────────────

class Orchestrator:
    def __init__(self, artifact_root: Path = ARTIFACT_ROOT) -> None:
        self.artifact_root           = Path(artifact_root)
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        self.tasks:    dict[str, Task]                              = {}
        self._procs:   dict[str, subprocess.Popen]                  = {}
        self._lock                                                  = threading.Lock()
        self._listeners: list[queue.Queue[Event]]                    = []
        self._listeners_lock                                        = threading.Lock()

    # -- listeners ----------------------------------------------------------

    def subscribe(self) -> queue.Queue:
        q: queue.Queue[Event] = queue.Queue()
        with self._listeners_lock:
            self._listeners.append(q)
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        with self._listeners_lock:
            if q in self._listeners:
                self._listeners.remove(q)

    def _emit(self, ev: Event) -> None:
        with self._listeners_lock:
            for q in list(self._listeners):
                try:
                    q.put_nowait(ev)
                except Exception:
                    pass

    # -- intents ------------------------------------------------------------

    @staticmethod
    def list_intents() -> dict[str, Intent]:
        return dict(INTENTS)

    # -- submission + approval ---------------------------------------------

    def submit(
        self,
        user:         str,
        role:         Role,
        intent:       str,
        args:         dict[str, Any] | None = None,
        auto_approve: bool                   = False,
    ) -> Task:
        if intent not in INTENTS:
            raise ValueError(f"unknown intent: {intent}")
        spec = INTENTS[intent]
        if not _role_meets(role, spec.min_role):
            raise PermissionError(
                f"role '{role.value}' cannot run intent '{intent}' "
                f"(requires >= {spec.min_role.value})"
            )

        task_id      = uuid.uuid4().hex[:12]
        artifact_dir = self.artifact_root / task_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        log_path     = artifact_dir / "run.log"

        task = Task(
            task_id=task_id, user=user, role=role,
            intent=intent, args=args or {},
            artifact_dir=str(artifact_dir),
            log_path=str(log_path),
        )

        with self._lock:
            self.tasks[task_id] = task

        self._emit(Event(task_id, "submitted",
                         {"user": user, "role": role.value, "intent": intent,
                          "risky": spec.risky, "long_running": spec.long_running,
                          "auto_approve": auto_approve}))

        # Risky or long-running tasks queue for owner approval — even owners.
        # The whole point of the gateway is "confirm before the remote machine
        # burns GPU hours." Per-user opt-out via auto_approve=True (config).
        needs_approval = (spec.risky or spec.long_running) and not auto_approve
        if needs_approval:
            task.state = TaskState.AWAITING_APPROVAL
            self._emit(Event(task_id, "approval_required",
                             {"intent": intent, "user": user,
                              "reason": "risky" if spec.risky else "long_running"}))
            return task

        self._start(task)
        return task

    def approve(self, task_id: str, approver_user: str, approver_role: Role) -> Task:
        if approver_role != Role.OWNER:
            raise PermissionError("only owner may approve tasks")
        task = self._require_task(task_id)
        if task.state != TaskState.AWAITING_APPROVAL:
            raise RuntimeError(f"task {task_id} not awaiting approval (state={task.state.value})")
        task.state    = TaskState.APPROVED
        task.approver = approver_user
        self._emit(Event(task_id, "approved", {"approver": approver_user}))
        self._start(task)
        return task

    def deny(self, task_id: str, approver_user: str, approver_role: Role, reason: str = "") -> Task:
        if approver_role != Role.OWNER:
            raise PermissionError("only owner may deny tasks")
        task = self._require_task(task_id)
        if task.state != TaskState.AWAITING_APPROVAL:
            raise RuntimeError(f"task {task_id} not awaiting approval")
        task.state       = TaskState.DENIED
        task.approver    = approver_user
        task.finished_at = datetime.now(timezone.utc).isoformat()
        task.note        = reason
        self._emit(Event(task_id, "denied", {"approver": approver_user, "reason": reason}))
        return task

    def cancel(self, task_id: str, user: str, role: Role) -> Task:
        task = self._require_task(task_id)
        if role != Role.OWNER and user != task.user:
            raise PermissionError("only owner or task submitter may cancel")
        if task.state in (TaskState.SUCCEEDED, TaskState.FAILED,
                          TaskState.DENIED, TaskState.CANCELLED):
            return task
        proc = self._procs.get(task_id)
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass
        task.state       = TaskState.CANCELLED
        task.finished_at = datetime.now(timezone.utc).isoformat()
        self._emit(Event(task_id, "cancelled", {"by": user}))
        return task

    # -- queries ------------------------------------------------------------

    def get(self, task_id: str) -> Task:
        return self._require_task(task_id)

    def pending(self) -> list[Task]:
        with self._lock:
            return [t for t in self.tasks.values() if t.state == TaskState.AWAITING_APPROVAL]

    def recent(self, limit: int = 10) -> list[Task]:
        with self._lock:
            ts = sorted(self.tasks.values(), key=lambda t: t.created_at, reverse=True)
        return ts[:limit]

    def status_snapshot(self) -> dict[str, Any]:
        with self._lock:
            by_state: dict[str, int] = {}
            for t in self.tasks.values():
                by_state[t.state.value] = by_state.get(t.state.value, 0) + 1
            return {
                "total_tasks":   len(self.tasks),
                "by_state":      by_state,
                "pending_count": sum(1 for t in self.tasks.values() if t.state == TaskState.AWAITING_APPROVAL),
                "running_count": sum(1 for t in self.tasks.values() if t.state == TaskState.RUNNING),
                "artifact_root": str(self.artifact_root),
            }

    # -- execution ----------------------------------------------------------

    def _require_task(self, task_id: str) -> Task:
        with self._lock:
            t = self.tasks.get(task_id)
        if not t:
            raise KeyError(f"unknown task: {task_id}")
        return t

    def _start(self, task: Task) -> None:
        spec = INTENTS[task.intent]
        # Special-case the in-process "status" intent
        if task.intent == "status":
            task.state       = TaskState.RUNNING
            task.started_at  = datetime.now(timezone.utc).isoformat()
            self._emit(Event(task.task_id, "started", {"intent": "status"}))
            snap = self.status_snapshot()
            (Path(task.artifact_dir) / "status.json").write_text(
                json.dumps(snap, indent=2), encoding="utf-8")
            task.artifacts.append("status.json")
            task.state       = TaskState.SUCCEEDED
            task.exit_code   = 0
            task.finished_at = datetime.now(timezone.utc).isoformat()
            self._emit(Event(task.task_id, "finished",
                             {"exit_code": 0, "artifacts": task.artifacts}))
            return

        argv = spec.build_cmd(self, task)
        if not argv:
            task.state       = TaskState.FAILED
            task.note        = "empty command"
            task.finished_at = datetime.now(timezone.utc).isoformat()
            self._emit(Event(task.task_id, "finished", {"exit_code": -1, "error": "empty command"}))
            return

        thread = threading.Thread(target=self._run_subprocess, args=(task, argv), daemon=True)
        thread.start()

    def _run_subprocess(self, task: Task, argv: list[str]) -> None:
        task.state      = TaskState.RUNNING
        task.started_at = datetime.now(timezone.utc).isoformat()
        self._emit(Event(task.task_id, "started",
                         {"cmd": " ".join(shlex.quote(a) for a in argv)}))

        log_path = Path(task.log_path) if task.log_path else None
        try:
            proc = subprocess.Popen(
                argv, cwd=str(REPO_ROOT),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1,
            )
        except Exception as exc:
            task.state       = TaskState.FAILED
            task.exit_code   = -1
            task.note        = f"spawn failed: {exc}"
            task.finished_at = datetime.now(timezone.utc).isoformat()
            self._emit(Event(task.task_id, "finished",
                             {"exit_code": -1, "error": str(exc)}))
            return

        self._procs[task.task_id] = proc
        log_fh = open(log_path, "w", encoding="utf-8") if log_path else None
        try:
            assert proc.stdout is not None
            for line in proc.stdout:
                line = line.rstrip("\n")
                if log_fh:
                    log_fh.write(line + "\n")
                    log_fh.flush()
                self._emit(Event(task.task_id, "log", {"line": line}))
            proc.wait()
        finally:
            if log_fh:
                log_fh.close()
            self._procs.pop(task.task_id, None)

        task.exit_code   = proc.returncode
        task.finished_at = datetime.now(timezone.utc).isoformat()

        # Collect artifacts: any file in artifact_dir other than run.log
        if task.artifact_dir:
            for p in Path(task.artifact_dir).iterdir():
                if p.is_file() and p.name != "run.log":
                    rel = p.name
                    if rel not in task.artifacts:
                        task.artifacts.append(rel)

        if task.state == TaskState.CANCELLED:
            pass
        elif proc.returncode == 0:
            task.state = TaskState.SUCCEEDED
        else:
            task.state = TaskState.FAILED

        self._emit(Event(task.task_id, "finished",
                         {"exit_code":   proc.returncode,
                          "state":       task.state.value,
                          "artifacts":   task.artifacts,
                          "artifact_dir": task.artifact_dir,
                          "log_path":    task.log_path}))


# ── CLI ──────────────────────────────────────────────────────────────────────

def _print_task(t: Task) -> None:
    print(json.dumps(t.to_public(), indent=2))


def _cli_list_intents() -> None:
    rows = []
    for name, spec in INTENTS.items():
        rows.append(f"  {name:<15} role>={spec.min_role.value:<12} "
                    f"risky={'Y' if spec.risky else 'n'} "
                    f"long={'Y' if spec.long_running else 'n'}  {spec.description}")
    print("Available intents:")
    print("\n".join(rows))


def _wait_for_finish(orch: Orchestrator, task_id: str, timeout_s: float = 600.0) -> None:
    q = orch.subscribe()
    try:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            try:
                ev = q.get(timeout=2.0)
            except queue.Empty:
                continue
            if ev.task_id != task_id:
                continue
            if ev.kind == "log":
                print(f"  | {ev.payload.get('line','')}")
            else:
                print(f"  [{ev.kind}] {ev.payload}")
            if ev.kind in ("finished", "denied", "cancelled"):
                return
    finally:
        orch.unsubscribe(q)


def main() -> None:
    p = argparse.ArgumentParser(description="ResearchOS Orchestrator CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list-intents", help="Show all registered intents")

    pr = sub.add_parser("run", help="Submit + run an intent")
    pr.add_argument("--user",   required=True)
    pr.add_argument("--role",   required=True, choices=[r.value for r in Role])
    pr.add_argument("--intent", required=True, choices=list(INTENTS.keys()))
    pr.add_argument("--args",   default="{}", help="JSON dict of intent args")
    pr.add_argument("--wait",   action="store_true", help="Block + stream logs until finish")

    pa = sub.add_parser("approve", help="Owner-approve a pending task")
    pa.add_argument("--task-id", required=True)
    pa.add_argument("--user",    required=True)

    pd = sub.add_parser("deny", help="Owner-deny a pending task")
    pd.add_argument("--task-id", required=True)
    pd.add_argument("--user",    required=True)
    pd.add_argument("--reason",  default="")

    pc = sub.add_parser("cancel", help="Cancel a running task")
    pc.add_argument("--task-id", required=True)
    pc.add_argument("--user",    required=True)
    pc.add_argument("--role",    required=True, choices=[r.value for r in Role])

    sub.add_parser("pending", help="List tasks awaiting approval")
    sub.add_parser("status",  help="Show orchestrator status snapshot")

    pg = sub.add_parser("get", help="Show one task by id")
    pg.add_argument("--task-id", required=True)

    args = p.parse_args()
    orch = Orchestrator()

    if args.cmd == "list-intents":
        _cli_list_intents(); return

    if args.cmd == "run":
        try:
            extra = json.loads(args.args or "{}")
        except json.JSONDecodeError as exc:
            print(f"[orchestrator] bad --args JSON: {exc}"); sys.exit(2)
        try:
            t = orch.submit(args.user, Role(args.role), args.intent, extra)
        except (ValueError, PermissionError) as exc:
            print(f"[orchestrator] {exc}"); sys.exit(2)
        _print_task(t)
        if args.wait:
            terminal = {TaskState.SUCCEEDED, TaskState.FAILED,
                        TaskState.DENIED, TaskState.CANCELLED}
            if orch.get(t.task_id).state not in terminal:
                _wait_for_finish(orch, t.task_id)
            _print_task(orch.get(t.task_id))
        return

    if args.cmd == "approve":
        t = orch.approve(args.task_id, args.user, Role.OWNER)
        _print_task(t); return

    if args.cmd == "deny":
        t = orch.deny(args.task_id, args.user, Role.OWNER, args.reason)
        _print_task(t); return

    if args.cmd == "cancel":
        t = orch.cancel(args.task_id, args.user, Role(args.role))
        _print_task(t); return

    if args.cmd == "pending":
        for t in orch.pending():
            _print_task(t)
        return

    if args.cmd == "status":
        print(json.dumps(orch.status_snapshot(), indent=2)); return

    if args.cmd == "get":
        _print_task(orch.get(args.task_id)); return


if __name__ == "__main__":
    main()
