"""Per-agent memory for the autonomous framework.

Each agent gets its own append-only JSONL file under
``research_os_memory/agent_state/<agent_id>.jsonl``. This is separate from
the 9 canonical human-curated memory files so autonomous-agent activity
never pollutes the project's source-of-truth pages.

Records are plain dicts with at minimum ``ts`` + ``type`` + a payload. The
file is treated as a stream — readers slice the tail or filter by goal_id.
Writes are append-only and best-effort; corruption of the JSONL never blocks
the running agent (the autonomous loop falls back to in-memory state if the
file can't be written).
"""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def _utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class _MemoryRecord:
    """In-memory mirror of one JSONL line. Internal helper."""
    ts: str
    type: str
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"ts": self.ts, "type": self.type, **self.payload}


class AgentMemory:
    """Append-only per-agent state log.

    Typical usage from inside an autonomous agent:

        mem = AgentMemory.for_agent(self.agent_id, repo_root=self.ctx.repo_root)
        mem.record("goal_started", {"goal_id": g.goal_id, "objective": g.objective})
        ...
        mem.record("goal_completed", {"goal_id": g.goal_id, "status": "succeeded"})

    Readers:

        recent = mem.recent(limit=20)
        history = mem.for_goal(goal_id)
        pattern = mem.failure_pattern(last_n=5)
    """

    _AGENT_STATE_SUBDIR = "agent_state"

    def __init__(self, agent_id: str, path: Path):
        self.agent_id = agent_id
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._mirror: List[_MemoryRecord] = []
        # Pre-load existing records so readers work immediately, even before
        # the first write.
        self._mirror = list(self._iter_existing())

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    @classmethod
    def for_agent(
        cls,
        agent_id: str,
        *,
        repo_root: "str | Path" = ".",
        memory_dir: "str | Path | None" = None,
    ) -> "AgentMemory":
        base = Path(memory_dir) if memory_dir is not None else Path(repo_root) / "research_os_memory"
        path = base / cls._AGENT_STATE_SUBDIR / f"{agent_id}.jsonl"
        return cls(agent_id, path)

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def record(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> None:
        """Append one record. Never raises — failures are silent."""
        rec = _MemoryRecord(ts=_utc_iso(), type=event_type, payload=dict(payload or {}))
        with self._lock:
            self._mirror.append(rec)
            try:
                with self.path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(rec.to_dict(), default=str) + "\n")
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def all_records(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [r.to_dict() for r in self._mirror]

    def recent(self, *, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return [r.to_dict() for r in self._mirror[-limit:]]

    def for_goal(self, goal_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                r.to_dict()
                for r in self._mirror
                if r.payload.get("goal_id") == goal_id
            ]

    def recent_goals(self, *, limit: int = 10) -> List[Dict[str, Any]]:
        """Return the most recent N ``goal_started`` records, newest first."""
        with self._lock:
            starts = [r.to_dict() for r in self._mirror if r.type == "goal_started"]
        return list(reversed(starts))[:limit]

    def failure_pattern(self, *, last_n: int = 5) -> Dict[str, Any]:
        """Summarize the last N failures so a planner can adapt strategy.

        Returns a dict with the failure count and the most common error
        signatures — useful for "we've tried this tool 3 times and it
        always fails, try a different tool" decisions.
        """
        with self._lock:
            failures = [r for r in self._mirror if r.type in ("step_failed", "fallback_triggered")]
        recent_failures = failures[-last_n:]
        signatures: Dict[str, int] = {}
        for r in recent_failures:
            sig = str(r.payload.get("reason") or r.payload.get("error") or "unknown")[:120]
            signatures[sig] = signatures.get(sig, 0) + 1
        return {
            "failure_count": len(recent_failures),
            "signatures": signatures,
            "agent_id": self.agent_id,
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _iter_existing(self) -> Iterable[_MemoryRecord]:
        if not self.path.exists():
            return []
        out: List[_MemoryRecord] = []
        try:
            with self.path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    ts = obj.pop("ts", "")
                    typ = obj.pop("type", "unknown")
                    out.append(_MemoryRecord(ts=ts, type=typ, payload=obj))
        except OSError:
            return []
        return out


__all__ = ["AgentMemory"]
