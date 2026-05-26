"""Planners for the autonomous-agent loop.

A planner takes a ``Goal`` + ``ContextPacket`` and returns a ``Plan`` of
``Step``s. It can also ``replan(...)`` mid-run when critics surface
spawned steps or required revisions.

Two built-ins:

- ``DeterministicPlanner`` (always available): builds a minimal plan that
  introspects memory + registries, runs the agent's main deterministic
  check, then critiques. No LLM, no web.
- ``LLMPlanner`` (opt-in via ``RESEARCHOS_ENABLE_LLM_AGENTS=1``):
  prompts the local Ollama model for a structured JSON plan. Falls back to
  ``DeterministicPlanner`` on any failure.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Protocol

from research_os.autonomous.profile import AgentProfile
from research_os.autonomous.schemas import (
    CritiqueResult,
    Goal,
    Plan,
    Step,
    StepResult,
)
from research_os.schemas.context import ContextPacket
from research_os.tools.llm import llm_enabled
from research_os.tools.registry import ToolRegistry, ToolResult


class Planner(Protocol):
    name: str

    def plan(
        self,
        goal: Goal,
        packet: ContextPacket,
        *,
        profile: AgentProfile,
        tools: ToolRegistry,
    ) -> Plan: ...

    def replan(
        self,
        plan: Plan,
        results: List[StepResult],
        critiques: List[CritiqueResult],
        *,
        goal: Goal,
        packet: ContextPacket,
        profile: AgentProfile,
        tools: ToolRegistry,
    ) -> Plan: ...


# ---------------------------------------------------------------------------
# DeterministicPlanner
# ---------------------------------------------------------------------------

class DeterministicPlanner:
    """Template-based planner. Builds the same shape of plan regardless of
    the agent — readable, predictable, no external calls.

    Default plan:
      1. memory_list                          (always — cheap orientation)
      2. memory_read PROJECT_CANONICAL_STATUS (if available)
      3. agent's main deterministic check     (the agent's own scan)
      4. critique                             (run attached critics)
    """
    name = "deterministic_planner"

    def __init__(
        self,
        *,
        include_memory_orient: bool = True,
        include_critique: bool = True,
        extra_steps: Optional[List[Step]] = None,
    ):
        self.include_memory_orient = include_memory_orient
        self.include_critique = include_critique
        self.extra_steps = list(extra_steps or [])

    def plan(
        self,
        goal: Goal,
        packet: ContextPacket,
        *,
        profile: AgentProfile,
        tools: ToolRegistry,
    ) -> Plan:
        steps: List[Step] = []
        if self.include_memory_orient and profile.can_call("memory_list"):
            steps.append(Step(
                kind="tool_call",
                description="Orient: list canonical memory files.",
                tool_name="memory_list",
                tool_input={},
                rationale="Default deterministic orientation step.",
            ))
            if profile.can_call("memory_read"):
                steps.append(Step(
                    kind="tool_call",
                    description="Read PROJECT_CANONICAL_STATUS.md",
                    tool_name="memory_read",
                    tool_input={"name": "PROJECT_CANONICAL_STATUS.md"},
                    rationale="Source-of-truth read before any other action.",
                ))
        # Agent's own deterministic check.
        steps.append(Step(
            kind="deterministic",
            description=f"Run {profile.agent_id} legacy scan.",
            tool_name=None,
            tool_input={},
            rationale="Always-on baseline; produces an AgentOutput.",
        ))
        # Extra subclass-provided steps before the critique.
        for s in self.extra_steps:
            steps.append(s)
        # Critique step.
        if self.include_critique:
            steps.append(Step(
                kind="critique",
                description="Run attached critics on plan results.",
                rationale="Closes the critique→planner feedback loop.",
            ))
        return Plan(
            goal_id=goal.goal_id,
            steps=steps,
            rationale=f"DeterministicPlanner produced {len(steps)} steps.",
            created_by=self.name,
        )

    def replan(
        self,
        plan: Plan,
        results: List[StepResult],
        critiques: List[CritiqueResult],
        *,
        goal: Goal,
        packet: ContextPacket,
        profile: AgentProfile,
        tools: ToolRegistry,
    ) -> Plan:
        """Append every critic-spawned step (deduped by description) to the plan."""
        existing_descs = {s.description for s in plan.steps}
        appended = 0
        for crit in critiques:
            for s in crit.spawned_steps:
                # Don't add duplicate descriptions if we've already queued them.
                if s.description in existing_descs:
                    continue
                # Honor allow-list: drop tool-call steps the profile can't run.
                if s.kind == "tool_call" and s.tool_name and not profile.can_call(s.tool_name):
                    continue
                plan.append(s)
                existing_descs.add(s.description)
                appended += 1
        plan.revision += 1
        plan.rationale = (
            f"{plan.rationale} [revision {plan.revision}: added {appended} critic-spawned steps]"
        )
        return plan


# ---------------------------------------------------------------------------
# LLMPlanner
# ---------------------------------------------------------------------------

_LLM_PLAN_SYSTEM = """\
You produce a small JSON plan for an autonomous research agent.

Output STRICT JSON only:
{"steps":[
  {"kind":"tool_call|deterministic|critique|evaluate_coverage",
   "description":"<short>",
   "tool_name":"<name or null>",
   "tool_input":{...},
   "rationale":"<one sentence>"},
  ...
]}

Rules:
- Use ONLY tools listed under "available_tools".
- Keep the plan small (<= 6 steps).
- The last step should usually be kind="critique".
- Don't invent tools or arguments. If you're unsure, skip the step.
"""

_LLM_PLAN_USER_TMPL = """\
goal_objective: {objective}
goal_rationale: {rationale}

available_tools:
{tools_block}

agent_profile:
- agent_id: {agent_id}
- capabilities: {capabilities}
- domain_areas: {domains}

prior_context:
{prior_context}

Produce the JSON plan now.
"""


class LLMPlanner:
    """Wraps the deterministic planner. If LLM is enabled and the call
    succeeds, the LLM-produced plan is used. Otherwise we fall back to
    ``DeterministicPlanner``.
    """
    name = "llm_planner"

    def __init__(self, *, fallback: Optional[Planner] = None):
        self.fallback = fallback or DeterministicPlanner()

    def plan(
        self,
        goal: Goal,
        packet: ContextPacket,
        *,
        profile: AgentProfile,
        tools: ToolRegistry,
    ) -> Plan:
        if not llm_enabled() or "llm_chat" not in tools:
            return self.fallback.plan(goal, packet, profile=profile, tools=tools)

        # Build the prompt context.
        allowed = [t for t in profile.allowed_tools if t in tools]
        tools_block = "\n".join(
            f"- {n}: {tools.get(n).description}"  # type: ignore[union-attr]
            for n in allowed if tools.get(n) is not None
        ) or "(none)"
        user = _LLM_PLAN_USER_TMPL.format(
            objective=goal.objective[:280],
            rationale=goal.rationale[:280],
            tools_block=tools_block,
            agent_id=profile.agent_id,
            capabilities=", ".join(profile.capabilities) or "(none)",
            domains=", ".join(profile.domain_areas) or "(none)",
            prior_context=(packet.task or "")[:500],
        )
        result: ToolResult = tools.call("llm_chat", {
            "system": _LLM_PLAN_SYSTEM, "user": user, "expect_json": True,
        })
        if not result.ok or not isinstance(result.output, dict):
            return self.fallback.plan(goal, packet, profile=profile, tools=tools)
        payload = result.output.get("json")
        if not isinstance(payload, dict):
            return self.fallback.plan(goal, packet, profile=profile, tools=tools)
        steps_raw = payload.get("steps")
        if not isinstance(steps_raw, list) or not steps_raw:
            return self.fallback.plan(goal, packet, profile=profile, tools=tools)

        steps: List[Step] = []
        for s in steps_raw[:8]:
            if not isinstance(s, dict):
                continue
            kind = s.get("kind", "tool_call")
            tool_name = s.get("tool_name") or None
            if kind == "tool_call" and tool_name and not profile.can_call(tool_name):
                continue  # drop disallowed tools
            steps.append(Step(
                kind=kind if kind in ("tool_call", "deterministic", "critique",
                                       "evaluate_coverage", "sub_goal", "handoff",
                                       "noop") else "tool_call",
                description=str(s.get("description", ""))[:280],
                tool_name=tool_name,
                tool_input=dict(s.get("tool_input") or {}),
                rationale=str(s.get("rationale", ""))[:280],
            ))
        if not steps:
            return self.fallback.plan(goal, packet, profile=profile, tools=tools)
        return Plan(
            goal_id=goal.goal_id,
            steps=steps,
            rationale=f"LLMPlanner produced {len(steps)} steps.",
            created_by=self.name,
        )

    def replan(self, *args, **kwargs) -> Plan:
        return self.fallback.replan(*args, **kwargs)


__all__ = ["DeterministicPlanner", "LLMPlanner", "Planner"]
