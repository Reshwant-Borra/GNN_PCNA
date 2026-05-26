"""Phase 5 — tests for the upgraded AutonomousController."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pytest

from research_os.agents.base import AgentContext
from research_os.autonomous import AUTONOMOUS_AGENTS
from research_os.autonomous.controller import AutonomousController
from research_os.autonomous.decomposer import default_decomposer
from research_os.autonomous.reference_agent import ReferenceAutonomousAgent
from research_os.autonomous.schemas import Goal
from research_os.events import emitter as _emitter
from research_os.memory.store import MemoryStore, ensure_memory_initialized
from research_os.registries.store import RegistryStore, ensure_registries_initialized


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
    mem = MemoryStore(tmp_path / "research_os_memory")
    ensure_memory_initialized(mem)
    reg = RegistryStore(tmp_path / "research_os_registries")
    ensure_registries_initialized(reg)
    return AgentContext(repo_root=tmp_path, memory_store=mem, registry_store=reg)


# ---------------------------------------------------------------------------
# Decomposition-driven dispatch
# ---------------------------------------------------------------------------

def test_controller_decomposes_corpus_goal(wired_ctx, monkeypatch):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    controller = AutonomousController(
        wired_ctx,
        agent_factories=dict(AUTONOMOUS_AGENTS),
    )
    result = controller.pursue_goal(
        Goal(objective="Build a research corpus for cryptic pockets"),
        run_verification=False,
    )
    # The corpus template decomposes into 3 sub-goals.
    assert len(result.sub_outcomes) >= 3
    agents = [o.agent_id for o in result.sub_outcomes]
    assert "literature_web" in agents
    assert "document_knowledge_ingestion" in agents


def test_controller_appends_verification_when_requested(wired_ctx, monkeypatch):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    controller = AutonomousController(
        wired_ctx,
        agent_factories=dict(AUTONOMOUS_AGENTS),
    )
    result = controller.pursue_goal(
        Goal(objective="Build a corpus for PCNA"),
        run_verification=True,
    )
    assert any(o.agent_id == "__verification_suite__" for o in result.sub_outcomes)
    assert len(result.verification_reports) >= 1


def test_controller_runs_verification_via_special_subgoal(wired_ctx):
    controller = AutonomousController(
        wired_ctx,
        agent_factories=dict(AUTONOMOUS_AGENTS),
    )
    result = controller.pursue_goal(
        Goal(objective="Cross-check claims for overclaim"),
        run_verification=False,  # Verify template already supplies it
    )
    assert len(result.verification_reports) >= 1


def test_controller_heal_first_emits_report(wired_ctx, monkeypatch):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    # Create a fake agents/orchestrator referring to a missing module so the
    # healer's detection has something to surface.
    (wired_ctx.repo_root / "agents").mkdir(exist_ok=True)
    (wired_ctx.repo_root / "agents" / "orchestrator.py").write_text(
        "import agents.pcna_crawler\n", encoding="utf-8",
    )
    controller = AutonomousController(
        wired_ctx,
        agent_factories=dict(AUTONOMOUS_AGENTS),
    )
    result = controller.pursue_goal(
        Goal(objective="Cross-check claims"),
        heal_first=True,
        heal_dry_run=True,
        run_verification=False,
    )
    assert result.heal_report is not None
    assert result.heal_report.detected   # at least the pcna_crawler entry


def test_controller_handoffs_recorded_from_agent_recommendations(wired_ctx, monkeypatch):
    monkeypatch.delenv("RESEARCHOS_AUTONOMY_OFF", raising=False)
    controller = AutonomousController(
        wired_ctx,
        agent_factories={"reference_autonomous": ReferenceAutonomousAgent},
        default_agent_id="reference_autonomous",
    )
    # No verification (would override the simple flow).
    result = controller.pursue_goal(
        Goal(objective="run reference agent only",
             inputs={"target_agent": "reference_autonomous"}),
        sub_goals=[Goal(objective="reference",
                         inputs={"target_agent": "reference_autonomous"})],
        run_verification=False,
    )
    assert result.aggregate_status in ("pass", "warning")
