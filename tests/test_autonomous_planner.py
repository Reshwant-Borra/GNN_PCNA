"""Tests for the autonomous planners (deterministic + LLM-backed)."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from research_os.agents.base import AgentContext
from research_os.autonomous.planner import DeterministicPlanner, LLMPlanner
from research_os.autonomous.profile import AgentProfile, AutonomyLevel, profile_for
from research_os.autonomous.schemas import (
    CritiqueResult,
    Goal,
    Plan,
    Step,
    StepResult,
    StepStatus,
    SuccessCriterion,
)
from research_os.schemas.context import ContextPacket
from research_os.tools.llm import register_llm, set_llm_backend
from research_os.tools.builtin import register_builtin
from research_os.tools.registry import ToolRegistry


@pytest.fixture
def ctx_packet() -> ContextPacket:
    return ContextPacket(task="do the thing", intents=["general"], risk_level="low")


@pytest.fixture
def wired_tools(tmp_path: Path) -> ToolRegistry:
    ctx = AgentContext(repo_root=tmp_path)
    reg = ToolRegistry()
    register_builtin(reg, ctx, agent_id="planner_test")
    register_llm(reg)
    return reg


@pytest.fixture
def profile() -> AgentProfile:
    p = profile_for("context_source_truth")
    return p.with_overrides(autonomy_level=AutonomyLevel.GUIDED)


# ---------------------------------------------------------------------------
# DeterministicPlanner
# ---------------------------------------------------------------------------

def test_deterministic_planner_produces_orient_then_critique(ctx_packet, wired_tools, profile):
    planner = DeterministicPlanner()
    goal = Goal(objective="test")
    plan = planner.plan(goal, ctx_packet, profile=profile, tools=wired_tools)
    kinds = [s.kind for s in plan.steps]
    # Should at least: memory_list (tool) → memory_read (tool) → deterministic → critique
    assert kinds[0] == "tool_call"
    assert "deterministic" in kinds
    assert kinds[-1] == "critique"


def test_deterministic_planner_skips_orient_when_no_memory_tools(ctx_packet):
    profile = AgentProfile(
        agent_id="bare", allowed_tools=[],
        autonomy_level=AutonomyLevel.GUIDED,
    )
    planner = DeterministicPlanner()
    plan = planner.plan(Goal(objective="x"), ctx_packet, profile=profile, tools=ToolRegistry())
    # No tool_call steps because profile has none allowed; one deterministic + one critique.
    assert all(s.kind != "tool_call" for s in plan.steps)
    assert any(s.kind == "deterministic" for s in plan.steps)


def test_deterministic_planner_replan_adds_critic_spawned_steps(ctx_packet, wired_tools, profile):
    planner = DeterministicPlanner()
    plan = planner.plan(Goal(objective="x"), ctx_packet, profile=profile, tools=wired_tools)
    original_len = len(plan.steps)
    critique = CritiqueResult(
        critic_name="test_critic",
        severity="medium",
        summary="needs more work",
        spawned_steps=[
            Step(kind="tool_call", tool_name="memory_read",
                 tool_input={"name": "PROJECT_CANONICAL_STATUS.md"},
                 description="Re-read source of truth"),
        ],
        requires_replan=True,
    )
    revised = planner.replan(plan, [], [critique],
                              goal=Goal(objective="x"), packet=ctx_packet,
                              profile=profile, tools=wired_tools)
    assert len(revised.steps) == original_len + 1
    assert revised.revision == 1


def test_replan_drops_disallowed_tools(ctx_packet, wired_tools, profile):
    planner = DeterministicPlanner()
    plan = planner.plan(Goal(objective="x"), ctx_packet, profile=profile, tools=wired_tools)
    original_len = len(plan.steps)
    critique = CritiqueResult(
        critic_name="t",
        spawned_steps=[
            Step(kind="tool_call", tool_name="web_search",  # not in profile.allowed_tools
                 description="Disallowed!"),
        ],
        requires_replan=True,
    )
    revised = planner.replan(plan, [], [critique],
                              goal=Goal(objective="x"), packet=ctx_packet,
                              profile=profile, tools=wired_tools)
    assert len(revised.steps) == original_len  # disallowed step dropped


# ---------------------------------------------------------------------------
# LLMPlanner
# ---------------------------------------------------------------------------

def test_llm_planner_falls_back_when_disabled(monkeypatch, ctx_packet, wired_tools, profile):
    monkeypatch.delenv("RESEARCHOS_ENABLE_LLM_AGENTS", raising=False)
    planner = LLMPlanner()
    plan = planner.plan(Goal(objective="x"), ctx_packet, profile=profile, tools=wired_tools)
    # Falls back to DeterministicPlanner — should produce its shape.
    assert any(s.kind == "deterministic" for s in plan.steps)


def test_llm_planner_uses_backend_when_enabled(monkeypatch, ctx_packet, wired_tools, profile):
    monkeypatch.setenv("RESEARCHOS_ENABLE_LLM_AGENTS", "1")

    def fake(system: str, user: str, timeout_s: float) -> str:
        return (
            '{"steps":['
            '{"kind":"tool_call","description":"orient","tool_name":"memory_list",'
            ' "tool_input":{},"rationale":"first"},'
            '{"kind":"critique","description":"check","tool_name":null,'
            ' "tool_input":{},"rationale":"last"}'
            ']}'
        )

    set_llm_backend(fake)
    try:
        planner = LLMPlanner()
        plan = planner.plan(Goal(objective="x"), ctx_packet,
                            profile=profile, tools=wired_tools)
        descs = [s.description for s in plan.steps]
        assert "orient" in descs
        assert "check" in descs
        # Created_by reflects which planner won
        assert plan.created_by == "llm_planner"
    finally:
        set_llm_backend(None)


def test_llm_planner_falls_back_on_malformed_json(monkeypatch, ctx_packet, wired_tools, profile):
    monkeypatch.setenv("RESEARCHOS_ENABLE_LLM_AGENTS", "1")

    def garbage(system: str, user: str, timeout_s: float) -> str:
        return "not json at all"

    set_llm_backend(garbage)
    try:
        planner = LLMPlanner()
        plan = planner.plan(Goal(objective="x"), ctx_packet,
                            profile=profile, tools=wired_tools)
        # Fell back — should match the deterministic shape.
        assert plan.created_by == "deterministic_planner"
    finally:
        set_llm_backend(None)


def test_llm_planner_drops_disallowed_tool_steps(monkeypatch, ctx_packet, wired_tools):
    monkeypatch.setenv("RESEARCHOS_ENABLE_LLM_AGENTS", "1")
    # Profile only allows memory_list.
    profile = AgentProfile(
        agent_id="bare2", allowed_tools=["memory_list", "llm_chat"],
        autonomy_level=AutonomyLevel.ASSISTED,
    )

    def returns_disallowed(system: str, user: str, timeout_s: float) -> str:
        return ('{"steps":['
                '{"kind":"tool_call","description":"sneaky","tool_name":"web_search",'
                ' "tool_input":{"query":"x"},"rationale":"shouldnt run"},'
                '{"kind":"deterministic","description":"ok","tool_name":null,'
                ' "tool_input":{},"rationale":"ok"}'
                ']}')

    set_llm_backend(returns_disallowed)
    try:
        planner = LLMPlanner()
        plan = planner.plan(Goal(objective="x"), ctx_packet,
                            profile=profile, tools=wired_tools)
        descs = [s.description for s in plan.steps]
        assert "sneaky" not in descs
        assert "ok" in descs
    finally:
        set_llm_backend(None)
