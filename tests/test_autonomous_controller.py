"""Tests for AutonomousController.pursue_goal scaffold."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pytest

from research_os.agents.base import AgentContext
from research_os.autonomous.agent import AutonomousAgent
from research_os.autonomous.controller import AutonomousController
from research_os.autonomous.profile import AutonomyLevel
from research_os.autonomous.reference_agent import (
    REFERENCE_PROFILE,
    ReferenceAutonomousAgent,
)
from research_os.autonomous.schemas import Goal
from research_os.events import emitter as _emitter
from research_os.memory.store import MemoryStore, ensure_memory_initialized
from research_os.registries.store import RegistryStore, ensure_registries_initialized
from research_os.schemas.context import ContextPacket


class _Collector:
    def __init__(self) -> None:
        self.events: List[Dict[str, Any]] = []

    def write_event(self, event_type, workflow_id, data):
        self.events.append({"type": event_type, "workflow_id": workflow_id, **data})


@pytest.fixture
def event_collector():
    coll = _Collector()
    _emitter._register_transcript(coll)
    try:
        yield coll
    finally:
        _emitter._unregister_transcript(coll)


@pytest.fixture
def wired_ctx(tmp_path: Path) -> AgentContext:
    mem = MemoryStore(tmp_path / "mem")
    ensure_memory_initialized(mem)
    reg = RegistryStore(tmp_path / "reg")
    ensure_registries_initialized(reg)
    return AgentContext(repo_root=tmp_path, memory_store=mem, registry_store=reg)


def test_controller_runs_default_agent(wired_ctx, event_collector, monkeypatch):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    controller = AutonomousController(
        wired_ctx,
        agent_factories={"reference_autonomous": ReferenceAutonomousAgent},
        default_agent_id="reference_autonomous",
    )
    goal = Goal(objective="campaign-smoke", rationale="phase3")
    # Phase 5 enables verification by default; opt out for this minimal smoke test.
    result = controller.pursue_goal(goal, run_verification=False)
    assert result.aggregate_status in ("pass", "warning")
    assert result.succeeded_count >= 1
    # Campaign events emitted
    types = {e["type"] for e in event_collector.events}
    assert "campaign_started" in types
    assert "campaign_completed" in types


def test_controller_skips_when_no_factory(wired_ctx, event_collector, monkeypatch):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    controller = AutonomousController(wired_ctx, default_agent_id="missing_agent")
    result = controller.pursue_goal(Goal(objective="x"), run_verification=False)
    assert result.aggregate_status == "fail"
    assert result.sub_outcomes[0].skipped is True
    assert "no agent factory" in result.sub_outcomes[0].error


def test_controller_records_factory_crash(wired_ctx, monkeypatch):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)

    def broken_factory(ctx: AgentContext):
        raise RuntimeError("simulated factory failure")

    controller = AutonomousController(
        wired_ctx,
        agent_factories={"broken": broken_factory},
        default_agent_id="broken",
    )
    result = controller.pursue_goal(Goal(objective="x"))
    assert result.aggregate_status == "fail"
    assert "factory failed" in result.sub_outcomes[0].error


def test_controller_records_agent_run_crash(wired_ctx, monkeypatch):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)

    class _Crash(AutonomousAgent):
        agent_id = "crasher"
        display_name = "Crasher"

        def run(self, packet):  # type: ignore[override]
            raise RuntimeError("simulated agent crash")

    controller = AutonomousController(
        wired_ctx,
        agent_factories={"crasher": _Crash},
        default_agent_id="crasher",
    )
    result = controller.pursue_goal(Goal(objective="x"))
    assert result.aggregate_status == "fail"
    assert "agent crashed" in result.sub_outcomes[0].error


def test_controller_multiple_sub_goals(wired_ctx, event_collector, monkeypatch):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    controller = AutonomousController(
        wired_ctx,
        agent_factories={"reference_autonomous": ReferenceAutonomousAgent},
        default_agent_id="reference_autonomous",
    )
    sub_goals = [
        Goal(objective="sub1", inputs={"target_agent": "reference_autonomous"}),
        Goal(objective="sub2", inputs={"target_agent": "reference_autonomous"}),
        Goal(objective="sub3-orphan", inputs={"target_agent": "no_such_agent"}),
    ]
    result = controller.pursue_goal(
        Goal(objective="campaign"),
        sub_goals=sub_goals,
        run_verification=False,           # explicit sub_goals — no verify append
    )
    assert len(result.sub_outcomes) == 3
    assert result.succeeded_count == 2
    assert result.failed_count == 0  # orphan is *skipped*, not failed
    # The orphan sub-goal is in sub_outcomes as skipped.
    skipped = [o for o in result.sub_outcomes if o.skipped]
    assert len(skipped) == 1
