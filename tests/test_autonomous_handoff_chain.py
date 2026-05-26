"""Phase 6 — handoff chain tests.

When an autonomous agent emits ``next_recommended_agents``, the controller
should surface those as ``HandoffRequest`` entries on the
``CampaignResult``. Multiple handoffs should compose into a chain.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from research_os.agents.base import AgentContext
from research_os.autonomous.agent import AutonomousAgent
from research_os.autonomous.controller import AutonomousController
from research_os.autonomous.profile import AgentProfile, AutonomyLevel
from research_os.autonomous.reference_agent import ReferenceAutonomousAgent
from research_os.autonomous.schemas import Goal
from research_os.memory.store import MemoryStore, ensure_memory_initialized
from research_os.registries.store import RegistryStore, ensure_registries_initialized
from research_os.schemas.context import ContextPacket


class _HandoffEmittingAgent(AutonomousAgent):
    """Deterministic agent whose output explicitly recommends two follow-ups."""

    agent_id = "handoff_emitter"
    display_name = "Handoff Emitter"

    def __init__(self, ctx: AgentContext, **kwargs):
        kwargs.setdefault("profile", AgentProfile(
            agent_id="handoff_emitter",
            autonomy_level=AutonomyLevel.DETERMINISTIC,
        ))
        super().__init__(ctx, **kwargs)

    def _deterministic_run(self, packet: ContextPacket):
        return self._output(
            task=packet.task, status="warning", confidence=0.7,
            summary="found something; needs follow-up",
            next_recommended_agents=["paper_claim", "contradiction_hunter"],
        )


@pytest.fixture
def wired_ctx(tmp_path: Path) -> AgentContext:
    mem = MemoryStore(tmp_path / "research_os_memory")
    ensure_memory_initialized(mem)
    reg = RegistryStore(tmp_path / "research_os_registries")
    ensure_registries_initialized(reg)
    return AgentContext(repo_root=tmp_path, memory_store=mem, registry_store=reg)


def test_next_recommended_agents_surfaces_as_handoffs(wired_ctx):
    controller = AutonomousController(
        wired_ctx,
        agent_factories={"handoff_emitter": _HandoffEmittingAgent},
        default_agent_id="handoff_emitter",
    )
    result = controller.pursue_goal(
        Goal(objective="run"),
        run_verification=False,
    )
    # Two next_recommended_agents → two handoff entries.
    assert len(result.handoffs) == 2
    targets = {h.to_agent for h in result.handoffs}
    assert "paper_claim" in targets
    assert "contradiction_hunter" in targets


def test_handoff_chain_via_sequential_sub_goals(wired_ctx):
    controller = AutonomousController(
        wired_ctx,
        agent_factories={
            "handoff_emitter": _HandoffEmittingAgent,
            "reference_autonomous": ReferenceAutonomousAgent,
        },
    )
    result = controller.pursue_goal(
        Goal(objective="chain"),
        sub_goals=[
            Goal(objective="step 1: emit handoffs",
                 inputs={"target_agent": "handoff_emitter"}),
            Goal(objective="step 2: reference follow-up",
                 inputs={"target_agent": "reference_autonomous"}),
        ],
        run_verification=False,
    )
    assert result.succeeded_count == 2
    # Step 1's handoffs are still surfaced on the campaign result.
    assert len(result.handoffs) >= 2
