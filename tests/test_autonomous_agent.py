"""End-to-end tests for AutonomousAgent + ReferenceAutonomousAgent.

Covers:
- Deterministic fallback when autonomy is disabled at the profile level
- Kill-switch env var (RESEARCHOS_AUTONOMY_OFF)
- requires_env on profile gates the loop
- Full autonomous loop with critique + replan + budget exhaustion
- Plan/step trace appears in machine_readable_notes
- Per-agent memory records goal_started + goal_completed
- Event emission goes through the global emitter (capture via subscriber)
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

import pytest

from research_os.agents.base import AgentContext
from research_os.autonomous.agent import AutonomousAgent
from research_os.autonomous.memory import AgentMemory
from research_os.autonomous.profile import AutonomyLevel
from research_os.autonomous.reference_agent import (
    REFERENCE_PROFILE,
    ReferenceAutonomousAgent,
)
from research_os.autonomous.schemas import Budget, Goal, Step, StepStatus, SuccessCriterion
from research_os.events import emitter as _emitter
from research_os.memory.store import MemoryStore, ensure_memory_initialized
from research_os.registries.store import RegistryStore, ensure_registries_initialized
from research_os.schemas.context import ContextPacket


# ---------------------------------------------------------------------------
# Event capture helper
# ---------------------------------------------------------------------------

class _Collector:
    def __init__(self) -> None:
        self.events: List[Dict[str, Any]] = []

    def write_event(self, event_type: str, workflow_id: str, data: Dict[str, Any]) -> None:
        self.events.append({"type": event_type, "workflow_id": workflow_id, **data})


@pytest.fixture
def event_collector():
    coll = _Collector()
    _emitter._register_transcript(coll)
    try:
        yield coll
    finally:
        _emitter._unregister_transcript(coll)


# ---------------------------------------------------------------------------
# Context fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def wired_ctx(tmp_path: Path) -> AgentContext:
    mem = MemoryStore(tmp_path / "mem")
    ensure_memory_initialized(mem)
    reg = RegistryStore(tmp_path / "reg")
    ensure_registries_initialized(reg)
    return AgentContext(repo_root=tmp_path, memory_store=mem, registry_store=reg)


# ---------------------------------------------------------------------------
# Deterministic-fallback path
# ---------------------------------------------------------------------------

def test_deterministic_profile_skips_autonomous_loop(wired_ctx):
    profile = REFERENCE_PROFILE.with_overrides(autonomy_level=AutonomyLevel.DETERMINISTIC)
    agent = ReferenceAutonomousAgent(wired_ctx, profile=profile)
    out = agent.run(ContextPacket(task="test"))
    # Deterministic scan produced a pass; no autonomous trace.
    assert out.status == "pass"
    assert "autonomous" not in (out.machine_readable_notes or {})


def test_kill_switch_disables_autonomy(wired_ctx, monkeypatch):
    monkeypatch.setenv("RESEARCHOS_AUTONOMY_OFF", "1")
    agent = ReferenceAutonomousAgent(wired_ctx)
    out = agent.run(ContextPacket(task="test"))
    assert "autonomous" not in (out.machine_readable_notes or {})
    assert out.status == "pass"


def test_requires_env_gates_autonomy(wired_ctx, monkeypatch):
    profile = REFERENCE_PROFILE.with_overrides(requires_env=["NEVER_SET_THIS_VAR"])
    monkeypatch.delenv("NEVER_SET_THIS_VAR", raising=False)
    agent = ReferenceAutonomousAgent(wired_ctx, profile=profile)
    out = agent.run(ContextPacket(task="test"))
    assert "autonomous" not in (out.machine_readable_notes or {})


# ---------------------------------------------------------------------------
# Full autonomous loop
# ---------------------------------------------------------------------------

def test_autonomous_loop_runs_end_to_end(wired_ctx, event_collector, monkeypatch):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    agent = ReferenceAutonomousAgent(wired_ctx)
    out = agent.run(ContextPacket(task="confirm framework"))
    # Should report pass (canonical files exist after ensure_memory_initialized).
    assert out.status == "pass"
    notes = out.machine_readable_notes
    assert "autonomous" in notes
    trace = notes["autonomous"]
    assert trace["iterations"] >= 1
    assert trace["criteria_met"] is True
    # Plan + step trace present
    assert trace["plan"]["step_count"] if isinstance(trace["plan"], dict) and "step_count" in trace["plan"] else len(trace["plan"]["steps"]) >= 1
    # Events captured by the transcript subscriber
    types_emitted = {e["type"] for e in event_collector.events}
    assert "goal_started" in types_emitted
    assert "plan_created" in types_emitted
    assert "step_started" in types_emitted
    assert "step_completed" in types_emitted
    assert "goal_completed" in types_emitted


def test_autonomous_loop_writes_to_agent_memory(wired_ctx, monkeypatch):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    agent = ReferenceAutonomousAgent(wired_ctx)
    agent.run(ContextPacket(task="x"))
    mem = AgentMemory.for_agent("reference_autonomous", repo_root=wired_ctx.repo_root)
    types = [r["type"] for r in mem.all_records()]
    assert "goal_started" in types
    assert "plan_created" in types
    assert "goal_completed" in types
    # At least one step record (the deterministic scan).
    assert any(t.startswith("step_") for t in types)


def test_autonomous_loop_emits_tool_call_events(wired_ctx, event_collector, monkeypatch):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    agent = ReferenceAutonomousAgent(wired_ctx)
    agent.run(ContextPacket(task="x"))
    tool_called = [e for e in event_collector.events if e["type"] == "tool_called"]
    tool_result = [e for e in event_collector.events if e["type"] == "tool_result"]
    # Reference agent's plan includes memory_list + memory_read tool calls.
    assert len(tool_called) >= 1
    assert len(tool_result) == len(tool_called)
    # Tool name visible in event payload
    assert any(e.get("tool_name") == "memory_list" for e in tool_called)


# ---------------------------------------------------------------------------
# Budget enforcement
# ---------------------------------------------------------------------------

def test_max_iterations_budget_stops_loop(wired_ctx, event_collector, monkeypatch):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    # Constrain to 1 iteration — must trip max_iterations almost immediately.
    profile = REFERENCE_PROFILE.with_overrides(
        default_budget=Budget(max_iterations=1, max_tool_calls=999,
                              max_failures=999, max_seconds=None),
    )
    agent = ReferenceAutonomousAgent(wired_ctx, profile=profile)
    out = agent.run(ContextPacket(task="x"))
    trace = out.machine_readable_notes["autonomous"]
    assert trace["budget_exhausted"] == "max_iterations"
    assert any(e["type"] == "budget_exhausted" for e in event_collector.events)


# ---------------------------------------------------------------------------
# Failure handling + fallback
# ---------------------------------------------------------------------------

class _BrokenLoopAgent(ReferenceAutonomousAgent):
    """Forces the autonomous loop to crash so we can verify the
    deterministic fallback kicks in."""

    def _autonomous_loop(self, packet: ContextPacket):  # type: ignore[override]
        raise RuntimeError("simulated autonomous crash")


def test_loop_crash_falls_back_to_deterministic(wired_ctx, event_collector, monkeypatch):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    agent = _BrokenLoopAgent(wired_ctx)
    out = agent.run(ContextPacket(task="x"))
    # Even though the loop crashed, fallback ran and produced a valid output.
    assert out.status == "pass"
    assert any(e["type"] == "fallback_triggered" for e in event_collector.events)


class _DoubleBrokenAgent(_BrokenLoopAgent):
    """Loop + fallback both crash — verifies the error output is well-formed."""

    def _deterministic_run(self, packet: ContextPacket):  # type: ignore[override]
        raise RuntimeError("fallback also broken")


def test_both_loop_and_fallback_crash_returns_clean_fail(wired_ctx, monkeypatch):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    agent = _DoubleBrokenAgent(wired_ctx)
    out = agent.run(ContextPacket(task="x"))
    assert out.status == "fail"
    assert out.human_review_required is True
    assert "both failed" in out.summary
    out.validate()  # must still be a schema-valid AgentOutput


# ---------------------------------------------------------------------------
# Subclass safety — must implement _deterministic_run
# ---------------------------------------------------------------------------

class _NoFallback(AutonomousAgent):
    agent_id = "no_fallback_test"
    display_name = "No Fallback"


def test_subclass_without_deterministic_run_raises_loudly(wired_ctx):
    agent = _NoFallback(wired_ctx)
    # Profile default is DETERMINISTIC autonomy, so .run() goes straight to
    # _deterministic_run — which raises NotImplementedError.
    with pytest.raises(NotImplementedError):
        agent.run(ContextPacket(task="x"))
