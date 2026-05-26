"""Autonomous-agent framework for ResearchOS (Phase 3).

This subpackage adds a goal-driven planning layer on top of the existing
single-pass agents. It is **purely additive**: nothing here changes the
behavior of any existing agent or the scientific orchestrator. Agents that
opt in subclass ``AutonomousAgent`` (which itself subclasses ``BaseAgent``),
so they remain drop-in compatible with ``Orchestrator.execute_plan``.

Design principles (per Phase 2 sign-off):

- **Additive, not destructive.** Disable autonomy and the system behaves
  exactly as it did before.
- **Falls back everywhere.** If the planning loop fails, the LLM is
  unavailable, the web is disabled, or any tool errors, the agent reverts to
  its deterministic ``run()`` implementation.
- **Bounded by budgets.** Every autonomous run carries explicit
  ``max_iterations``, ``max_tool_calls``, ``max_failures``, and time/token
  caps. The loop exits cleanly when any cap is hit and emits
  ``budget_exhausted``.
- **Observable.** Every step, tool call, critique, and re-plan emits a
  structured event so transcripts and the dashboard can see the agent's
  reasoning.
- **Profile-driven.** Each agent has an ``AgentProfile`` declaring its
  capabilities, allowed tools, autonomy level, and fallback behavior.

Public exports kept tight on purpose — internals can move without breaking
downstream callers.
"""
from research_os.autonomous.schemas import (
    Budget,
    CritiqueResult,
    CoverageCategory,
    CoverageResult,
    Goal,
    HandoffRequest,
    Plan,
    Step,
    StepResult,
    StepStatus,
    StopCondition,
    SuccessCriterion,
)
from research_os.autonomous.profile import (
    AgentProfile,
    AutonomyLevel,
    DEFAULT_PROFILES,
    profile_for,
)
from research_os.autonomous.memory import AgentMemory
from research_os.autonomous.coverage import CoverageEstimator
from research_os.autonomous.critique import Critic, simple_critic
from research_os.autonomous.planner import DeterministicPlanner, Planner
from research_os.autonomous.agent import AutonomousAgent, AutonomousRunResult
from research_os.autonomous.controller import AutonomousController, CampaignResult
from research_os.autonomous.agents import AUTONOMOUS_AGENTS

__all__ = [
    "AUTONOMOUS_AGENTS",
    "AgentMemory",
    "AgentProfile",
    "AutonomousAgent",
    "AutonomousController",
    "AutonomousRunResult",
    "AutonomyLevel",
    "Budget",
    "CampaignResult",
    "CoverageCategory",
    "CoverageEstimator",
    "CoverageResult",
    "Critic",
    "CritiqueResult",
    "DEFAULT_PROFILES",
    "DeterministicPlanner",
    "Goal",
    "HandoffRequest",
    "Plan",
    "Planner",
    "Step",
    "StepResult",
    "StepStatus",
    "StopCondition",
    "SuccessCriterion",
    "profile_for",
    "simple_critic",
]
