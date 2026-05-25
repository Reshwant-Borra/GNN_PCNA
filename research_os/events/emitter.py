"""Thread-safe NDJSON event emitter for the ResearchOS dashboard.

Call ``init_emitter(repo_root)`` once at startup (the Orchestrator does this
automatically).  Then call ``emit(event_type, workflow_id, data)`` from any
thread.  If ``init_emitter`` was never called, ``emit`` is a silent no-op so
existing CLI/MCP users are unaffected.

Per-run transcript writers can subscribe via ``_register_transcript`` so each
``emit`` also lands in the run's ``transcript.jsonl`` file. This is how the
``research_os.transcripts.writer.TranscriptWriter`` integrates without
duplicating event-routing logic.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

_lock = threading.Lock()
_events_path: Optional[Path] = None


class _TranscriptLike(Protocol):
    def write_event(self, event_type: str, workflow_id: str, data: Dict[str, Any]) -> None: ...


# Subscribers (per-run transcript writers). Each ``emit`` call also forwards
# to every subscribed writer. Typically there is 1 active writer per run.
_subscribers: List[_TranscriptLike] = []


def init_emitter(repo_root: "str | Path") -> None:
    """Point the emitter at ``<repo_root>/data/dashboard_events.ndjson``.

    Idempotent and thread-safe.  Creates parent directories if needed.
    """
    global _events_path
    p = Path(repo_root) / "data" / "dashboard_events.ndjson"
    p.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        _events_path = p


def emit(event_type: str, workflow_id: str, data: Dict[str, Any]) -> None:
    """Append one NDJSON event record.

    Silent no-op if ``init_emitter`` has not been called.  Never raises —
    dashboard telemetry must not break the main execution path.

    Also forwards the event to every registered transcript subscriber.
    """
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": event_type,
        "workflow_id": workflow_id,
        **data,
    }
    # Fan out to subscribers first — they should see the event even if the
    # global NDJSON file isn't configured (e.g. CLI runs without dashboard).
    with _lock:
        subs = list(_subscribers)
    for sub in subs:
        try:
            sub.write_event(event_type, workflow_id, data)
        except Exception:
            pass
    # Write to the global NDJSON sink.
    if _events_path is None:
        return
    line = json.dumps(record, default=str) + "\n"
    try:
        with _lock:
            with _events_path.open("a", encoding="utf-8") as f:
                f.write(line)
    except Exception:  # pragma: no cover — filesystem errors should never crash the pipeline
        pass


def _register_transcript(writer: _TranscriptLike) -> None:
    """Subscribe a transcript writer to all ``emit`` calls. Idempotent."""
    with _lock:
        if writer not in _subscribers:
            _subscribers.append(writer)


def _unregister_transcript(writer: _TranscriptLike) -> None:
    """Stop forwarding events to a transcript writer."""
    with _lock:
        if writer in _subscribers:
            _subscribers.remove(writer)
