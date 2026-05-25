"""Per-run JSONL transcript writer.

The writer is registered with the global event emitter at the start of a run.
Every ``emit()`` call then writes to both the global NDJSON event log (for the
live dashboard) AND the per-run JSONL transcript (for post-hoc audit).

We deliberately do NOT replace the global emitter — the existing
``data/dashboard_events.ndjson`` is still the source for the live SSE stream.
"""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from research_os.events import emitter as _emitter_module


def _utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc_filename_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


@dataclass
class TranscriptPaths:
    base: Path
    transcript_jsonl: Path
    summary_md: Path
    result_json: Path


class TranscriptWriter:
    """Writes per-run events to ``<reports_root>/runs/<workflow>/<ts>/transcript.jsonl``.

    The writer is thread-safe. Use ``register()`` to hook into the global
    emitter, then ``unregister()`` (or use as a context manager) to detach.
    """

    def __init__(
        self,
        reports_root: "str | Path",
        workflow: str,
        timestamp: Optional[str] = None,
    ):
        self.reports_root = Path(reports_root)
        self.workflow = workflow
        self.timestamp = timestamp or _utc_filename_ts()
        self.base = self.reports_root / "runs" / workflow / self.timestamp
        self.base.mkdir(parents=True, exist_ok=True)
        self.transcript_path = self.base / "transcript.jsonl"
        self.summary_path = self.base / "summary.md"
        self.result_path = self.base / "result.json"
        self._lock = threading.Lock()
        self._events: List[Dict[str, Any]] = []
        self._registered = False

    # ------------------------------------------------------------------
    # Event writing
    # ------------------------------------------------------------------

    def write_event(self, event_type: str, workflow_id: str, data: Dict[str, Any]) -> None:
        """Append one event record. Never raises."""
        record = {
            "ts": _utc_iso(),
            "type": event_type,
            "workflow_id": workflow_id,
            **data,
        }
        with self._lock:
            self._events.append(record)
            try:
                with self.transcript_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(record, default=str) + "\n")
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Global emitter registration
    # ------------------------------------------------------------------

    def register(self) -> None:
        """Subscribe this writer to every ``emit()`` call until ``unregister``."""
        if self._registered:
            return
        _emitter_module._register_transcript(self)  # type: ignore[attr-defined]
        self._registered = True

    def unregister(self) -> None:
        if not self._registered:
            return
        _emitter_module._unregister_transcript(self)  # type: ignore[attr-defined]
        self._registered = False

    def __enter__(self) -> "TranscriptWriter":
        self.register()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.unregister()

    # ------------------------------------------------------------------
    # Final outputs
    # ------------------------------------------------------------------

    def write_summary(self, *, plan_summary: Dict[str, Any], result_summary: Dict[str, Any]) -> None:
        """Write summary.md — a short executive summary for human eyes."""
        lines: List[str] = []
        lines.append(f"# Run summary — {self.workflow} — {self.timestamp}")
        lines.append("")
        lines.append("## Routing")
        lines.append("")
        lines.append(f"- Prompt: > {plan_summary.get('request_summary', '(none)')}")
        lines.append(f"- Decision: `{plan_summary.get('routing_decision', 'unspecified')}`")
        lines.append(f"- Confidence: `{plan_summary.get('routing_confidence', 0.0):.2f}`")
        lines.append(f"- Risk: **{plan_summary.get('risk_level', 'unknown')}**")
        if plan_summary.get("routing_reason"):
            lines.append(f"- Reason: {plan_summary['routing_reason']}")
        lines.append(f"- Selected agents: {', '.join(plan_summary.get('selected_agents', []))}")
        lines.append(f"- Required gates: {', '.join(plan_summary.get('required_gates', [])) or '(none)'}")
        if plan_summary.get("requires_claude_fallback"):
            lines.append("- Requires Claude fallback: **yes**")
        if plan_summary.get("selected_workflow"):
            lines.append(f"- Suggested workflow: `{plan_summary['selected_workflow']}`")
        lines.append("")
        lines.append("## Result")
        lines.append("")
        lines.append(f"- Blocked: **{result_summary.get('blocked', False)}**")
        if result_summary.get("blocked"):
            lines.append(f"- Block reason: {result_summary.get('block_reason', '')}")
        lines.append(f"- Human review required: **{result_summary.get('human_review_required', False)}**")
        for reason in result_summary.get("human_review_reasons", []) or []:
            lines.append(f"  - {reason}")
        gate_status = result_summary.get("gate_status", {}) or {}
        if gate_status:
            lines.append("")
            lines.append("### Gates")
            for gate, status in gate_status.items():
                lines.append(f"- `{gate}` → **{status}**")
        agents_run = result_summary.get("agent_outputs", []) or []
        if agents_run:
            lines.append("")
            lines.append("### Agents")
            for a in agents_run:
                lines.append(
                    f"- `{a.get('agent_id')}` → **{a.get('status')}** "
                    f"(conf {a.get('confidence', 0):.2f}): {a.get('summary', '')[:120]}"
                )
        lines.append("")
        lines.append("## Files")
        lines.append("")
        lines.append(f"- Transcript: `{self.transcript_path.as_posix()}`")
        lines.append(f"- Result JSON: `{self.result_path.as_posix()}`")
        lines.append("")
        try:
            self.summary_path.write_text("\n".join(lines), encoding="utf-8")
        except Exception:
            pass

    def write_result_json(self, result_dict: Dict[str, Any]) -> None:
        try:
            self.result_path.write_text(
                json.dumps(result_dict, indent=2, default=str),
                encoding="utf-8",
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def events_snapshot(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._events)

    @property
    def paths(self) -> TranscriptPaths:
        return TranscriptPaths(
            base=self.base,
            transcript_jsonl=self.transcript_path,
            summary_md=self.summary_path,
            result_json=self.result_path,
        )


# ─── Module-level conveniences ────────────────────────────────────────────


def init_transcript_for_run(
    reports_root: "str | Path",
    workflow: str = "claude_request",
    timestamp: Optional[str] = None,
) -> TranscriptWriter:
    """Create and register a transcript writer for a run.

    Callers should call ``finalize_transcript(writer, plan_dict, result_dict)``
    at the end of the run to write summary.md and result.json + unregister.
    """
    writer = TranscriptWriter(reports_root, workflow, timestamp)
    writer.register()
    return writer


def finalize_transcript(
    writer: TranscriptWriter,
    *,
    plan_dict: Dict[str, Any],
    result_dict: Dict[str, Any],
) -> TranscriptPaths:
    """Write summary.md + result.json and unregister the writer."""
    try:
        writer.write_summary(plan_summary=plan_dict, result_summary=result_dict)
        writer.write_result_json(result_dict)
    finally:
        writer.unregister()
    return writer.paths


__all__ = [
    "TranscriptWriter",
    "TranscriptPaths",
    "init_transcript_for_run",
    "finalize_transcript",
]
