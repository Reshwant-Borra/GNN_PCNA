"""Tests for AgentMemory — append-only per-agent JSONL state."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from research_os.autonomous.memory import AgentMemory


def test_record_and_recent_round_trip(tmp_path: Path):
    mem = AgentMemory.for_agent("test_agent", repo_root=tmp_path)
    mem.record("goal_started", {"goal_id": "g-1", "objective": "do thing"})
    mem.record("step_completed", {"goal_id": "g-1", "step_id": "s-1", "status": "succeeded"})

    recent = mem.recent(limit=10)
    assert len(recent) == 2
    assert recent[0]["type"] == "goal_started"
    assert recent[0]["goal_id"] == "g-1"
    assert recent[1]["type"] == "step_completed"


def test_records_persist_to_disk(tmp_path: Path):
    mem = AgentMemory.for_agent("agent_x", repo_root=tmp_path)
    mem.record("plan_created", {"goal_id": "g-1", "plan_id": "p-1", "step_count": 3})
    expected = tmp_path / "research_os_memory" / "agent_state" / "agent_x.jsonl"
    assert expected.exists()
    lines = expected.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["type"] == "plan_created"
    assert parsed["plan_id"] == "p-1"


def test_load_existing_records_on_init(tmp_path: Path):
    mem = AgentMemory.for_agent("agent_y", repo_root=tmp_path)
    mem.record("goal_started", {"goal_id": "g-1"})
    mem.record("goal_completed", {"goal_id": "g-1", "status": "pass"})

    # New instance should see the prior records.
    mem2 = AgentMemory.for_agent("agent_y", repo_root=tmp_path)
    rec = mem2.all_records()
    assert len(rec) == 2
    assert rec[-1]["status"] == "pass"


def test_for_goal_filters(tmp_path: Path):
    mem = AgentMemory.for_agent("agent_z", repo_root=tmp_path)
    mem.record("goal_started", {"goal_id": "g-1"})
    mem.record("step_completed", {"goal_id": "g-1", "step_id": "s-1"})
    mem.record("goal_started", {"goal_id": "g-2"})
    mem.record("step_completed", {"goal_id": "g-2", "step_id": "s-2"})

    g1 = mem.for_goal("g-1")
    g2 = mem.for_goal("g-2")
    assert len(g1) == 2
    assert len(g2) == 2
    assert all(r.get("goal_id") == "g-1" for r in g1)
    assert all(r.get("goal_id") == "g-2" for r in g2)


def test_recent_goals_newest_first(tmp_path: Path):
    mem = AgentMemory.for_agent("agent_q", repo_root=tmp_path)
    mem.record("goal_started", {"goal_id": "first", "objective": "a"})
    mem.record("step_completed", {})
    mem.record("goal_started", {"goal_id": "second", "objective": "b"})

    goals = mem.recent_goals(limit=5)
    assert len(goals) == 2
    assert goals[0]["goal_id"] == "second"
    assert goals[1]["goal_id"] == "first"


def test_failure_pattern_counts_signatures(tmp_path: Path):
    mem = AgentMemory.for_agent("agent_f", repo_root=tmp_path)
    mem.record("step_failed", {"reason": "timeout"})
    mem.record("step_failed", {"reason": "timeout"})
    mem.record("step_failed", {"reason": "404 not found"})
    mem.record("fallback_triggered", {"reason": "timeout"})

    pat = mem.failure_pattern(last_n=10)
    assert pat["failure_count"] == 4
    assert pat["signatures"].get("timeout") == 3
    assert pat["signatures"].get("404 not found") == 1
    assert pat["agent_id"] == "agent_f"


def test_corrupt_jsonl_line_is_skipped(tmp_path: Path):
    path = tmp_path / "research_os_memory" / "agent_state" / "broken.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"ts": "2026-01-01T00:00:00Z", "type": "goal_started", "goal_id": "g-1"}) + "\n"
        + "this is not json\n"
        + json.dumps({"ts": "2026-01-01T00:00:01Z", "type": "step_completed", "step_id": "s-1"}) + "\n",
        encoding="utf-8",
    )
    mem = AgentMemory("broken", path)
    rec = mem.all_records()
    assert len(rec) == 2  # corrupt line skipped, not raised


def test_record_failure_is_silent(tmp_path: Path, monkeypatch):
    """Writing to a path that can't be opened must not raise."""
    mem = AgentMemory.for_agent("agent_silent", repo_root=tmp_path)
    # Sabotage the path so the open() fails — but record() should still
    # update the in-memory mirror without raising.
    mem.path = Path("/this/path/does/not/exist/and/will/not/be/created/foo.jsonl")
    mem.record("step_completed", {"step_id": "s-1"})
    # in-memory mirror updated
    assert any(r["type"] == "step_completed" for r in mem.all_records())
