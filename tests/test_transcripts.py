"""Tests for per-run transcript writing.

The orchestrator's ``run()`` (and the service layer's ``run_request``) should
write a ``transcript.jsonl`` + ``summary.md`` + ``result.json`` to a
predictable location, and the transcript should contain the routing decision,
agent events, gate updates, and the final workflow_completed event.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List

import pytest

from research_os.events.emitter import emit, init_emitter
from research_os.transcripts.writer import (
    TranscriptWriter,
    init_transcript_for_run,
    finalize_transcript,
)


# ────────────────────────────────────────────────────────────────────────────
# Unit tests for TranscriptWriter itself
# ────────────────────────────────────────────────────────────────────────────

def test_writer_creates_directory_and_paths(tmp_path):
    writer = TranscriptWriter(tmp_path, "test_workflow", "2026-05-25T00-00-00Z")
    assert writer.base.is_dir()
    assert writer.base == tmp_path / "runs" / "test_workflow" / "2026-05-25T00-00-00Z"
    assert writer.transcript_path.parent == writer.base
    assert writer.summary_path.parent == writer.base
    assert writer.result_path.parent == writer.base


def test_write_event_appends_to_jsonl(tmp_path):
    writer = TranscriptWriter(tmp_path, "wf", "ts1")
    writer.write_event("workflow_started", "abc123", {"workflow_name": "test"})
    writer.write_event("agent_started", "abc123", {"agent_id": "context_source_truth"})

    lines = writer.transcript_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    e0 = json.loads(lines[0])
    e1 = json.loads(lines[1])
    assert e0["type"] == "workflow_started"
    assert e0["workflow_id"] == "abc123"
    assert e1["type"] == "agent_started"
    assert e1["agent_id"] == "context_source_truth"


def test_register_forwards_emitter_events(tmp_path):
    init_emitter(tmp_path)
    writer = TranscriptWriter(tmp_path, "wf", "ts2")
    writer.register()
    try:
        emit("routing_started", "wf42", {"prompt": "hello"})
        emit("agent_started", "wf42", {"agent_id": "literature_web"})
    finally:
        writer.unregister()

    events = writer.events_snapshot()
    assert any(e["type"] == "routing_started" for e in events)
    assert any(e["type"] == "agent_started" and e["agent_id"] == "literature_web" for e in events)


def test_unregister_stops_forwarding(tmp_path):
    init_emitter(tmp_path)
    writer = TranscriptWriter(tmp_path, "wf", "ts3")
    writer.register()
    writer.unregister()
    emit("agent_started", "wf42", {"agent_id": "should_not_be_captured"})
    assert all(e.get("agent_id") != "should_not_be_captured" for e in writer.events_snapshot())


def test_context_manager_registers_and_unregisters(tmp_path):
    init_emitter(tmp_path)
    writer = TranscriptWriter(tmp_path, "wf", "ts4")
    with writer:
        emit("agent_started", "wf42", {"agent_id": "inside"})
    emit("agent_started", "wf42", {"agent_id": "outside"})

    captured = [e["agent_id"] for e in writer.events_snapshot() if e["type"] == "agent_started"]
    assert "inside" in captured
    assert "outside" not in captured


def test_write_summary_produces_markdown(tmp_path):
    writer = TranscriptWriter(tmp_path, "wf", "ts5")
    writer.write_summary(
        plan_summary={
            "request_summary": "find papers",
            "routing_decision": "semantic",
            "routing_confidence": 0.85,
            "risk_level": "medium",
            "selected_agents": ["context_source_truth", "literature_web"],
            "required_gates": [],
            "routing_reason": "Literature query",
        },
        result_summary={
            "blocked": False,
            "human_review_required": False,
            "gate_status": {},
            "agent_outputs": [],
        },
    )
    text = writer.summary_path.read_text(encoding="utf-8")
    assert "find papers" in text
    assert "semantic" in text
    assert "literature_web" in text


def test_finalize_writes_summary_and_result_json_and_unregisters(tmp_path):
    init_emitter(tmp_path)
    writer = init_transcript_for_run(tmp_path, "wf", "ts6")
    emit("workflow_started", "wf42", {"workflow_name": "x"})
    finalize_transcript(
        writer,
        plan_dict={"request_summary": "hi", "routing_decision": "semantic"},
        result_dict={"blocked": False},
    )
    assert writer.summary_path.exists()
    assert writer.result_path.exists()
    result = json.loads(writer.result_path.read_text(encoding="utf-8"))
    assert result["blocked"] is False


# ────────────────────────────────────────────────────────────────────────────
# Integration test: run a real Orchestrator and check the transcript file
# ────────────────────────────────────────────────────────────────────────────

def test_orchestrator_run_creates_transcript_with_routing_and_agent_events(tmp_orchestrator: "object"):
    orch = tmp_orchestrator  # fixture from conftest
    # Use a prompt that the keyword router will classify deterministically
    # (semantic is disabled in tests, so this exercises the keyword path).
    result = orch.run("audit the dataset for leakage", workflow_name="claude_request")

    # The transcript should exist somewhere under reports_dir/runs/claude_request/
    runs_root = orch.reports_dir / "runs" / "claude_request"
    assert runs_root.exists(), f"runs root missing: {runs_root}"
    transcript_files = list(runs_root.glob("*/transcript.jsonl"))
    assert transcript_files, f"no transcript.jsonl under {runs_root}"

    # Read the most recent one and verify structure.
    transcript = transcript_files[-1]
    events = [json.loads(line) for line in transcript.read_text(encoding="utf-8").splitlines() if line.strip()]
    types = [e["type"] for e in events]

    # Must include routing events
    assert "routing_started" in types
    assert "routing_completed" in types
    # Must include workflow + agent events
    assert "workflow_started" in types
    assert any(t == "agent_queued" for t in types)
    assert any(t == "agent_started" for t in types)
    assert any(t == "agent_completed" for t in types)
    assert "workflow_completed" in types

    # Routing completed should carry the routing_decision field
    routing = [e for e in events if e["type"] == "routing_completed"][0]
    assert "routing_decision" in routing
    assert "selected_agents" in routing

    # Summary + result files should be present
    summary_md = transcript.parent / "summary.md"
    result_json = transcript.parent / "result.json"
    assert summary_md.exists()
    assert result_json.exists()
    result_data = json.loads(result_json.read_text(encoding="utf-8"))
    assert "plan" in result_data
    assert "agent_outputs" in result_data


def test_run_request_writes_transcript(tmp_path, monkeypatch):
    """The MCP-facing run_request should also write a transcript."""
    from research_os.integrations.claude_code import service

    monkeypatch.setenv("RESEARCH_OS_REPO", str(tmp_path))
    monkeypatch.setenv("RESEARCHOS_DISABLE_SEMANTIC", "1")

    response = service.run_request("audit the dataset for leakage", repo_root=tmp_path)

    assert response["status"] in ("completed", "approval_required")
    # transcript_path should be in the response
    assert "transcript_path" in response
    transcript_path = Path(response["transcript_path"])
    assert transcript_path.exists()
    # The transcript directory should also contain summary.md + result.json
    assert (transcript_path.parent / "summary.md").exists()
    assert (transcript_path.parent / "result.json").exists()
