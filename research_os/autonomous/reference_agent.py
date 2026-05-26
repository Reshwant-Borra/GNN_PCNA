"""Reference autonomous agent for the framework tests + demo.

``ReferenceAutonomousAgent`` exercises every framework feature in one place:

- subclasses ``AutonomousAgent`` with a custom ``AgentProfile``
- defines a deterministic fallback that always produces a valid AgentOutput
- attaches the built-in ``simple_critic`` so the critique→replan loop fires
- builds a goal with a measurable success criterion
- uses only the always-on built-in tools (no LLM, no web)

This is the agent the Phase 3 tests use to verify end-to-end behavior
without depending on any of the 21 production agents being migrated.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from research_os.agents.base import AgentContext
from research_os.autonomous.agent import AutonomousAgent
from research_os.autonomous.critique import simple_critic
from research_os.autonomous.profile import AgentProfile, AutonomyLevel
from research_os.autonomous.schemas import Budget, Goal, SuccessCriterion
from research_os.schemas.context import ContextPacket
from research_os.schemas.core import AgentOutput


_BUILT_IN_TOOLS = [
    "memory_read", "memory_list", "registry_read", "registry_query",
    "file_read", "glob", "git_state", "env_snapshot", "hash_file",
]


REFERENCE_PROFILE = AgentProfile(
    agent_id="reference_autonomous",
    capabilities=["self_test", "memory_walk", "registry_walk"],
    allowed_tools=list(_BUILT_IN_TOOLS),
    domain_areas=["framework_demo"],
    autonomy_level=AutonomyLevel.GUIDED,
    confidence_model="fixed",
    handoff_targets=[],
    failure_modes=["memory_missing", "registry_missing"],
    default_budget=Budget(max_iterations=6, max_tool_calls=8, max_failures=2,
                          max_seconds=15.0),
    fallback_behavior="scan_only",
    requires_env=[],
    notes="Reference agent used by the Phase 3 framework tests.",
)


class ReferenceAutonomousAgent(AutonomousAgent):
    """A self-test agent. Goal: confirm the memory store is initialized and
    at least one canonical file exists. Verifies the framework end-to-end.
    """

    agent_id = "reference_autonomous"
    display_name = "Reference Autonomous (framework demo)"

    def __init__(self, ctx: AgentContext, **kwargs):
        kwargs.setdefault("profile", REFERENCE_PROFILE)
        kwargs.setdefault("critics", [simple_critic])
        super().__init__(ctx, **kwargs)

    # ------------------------------------------------------------------

    def build_goal(self, packet: ContextPacket) -> Goal:
        return Goal(
            objective=packet.task or "Confirm canonical memory is initialized.",
            rationale="Framework self-test: prove the planning loop runs end-to-end.",
            success_criteria=[
                SuccessCriterion(
                    name="any_canonical_file_present",
                    check_key="any_canonical_present",
                    op="==",
                    check_value=True,
                    description="At least one canonical memory file exists.",
                ),
            ],
            budget=self.budget,
            inputs={"task": packet.task},
        )

    def _deterministic_run(self, packet: ContextPacket) -> AgentOutput:
        """Minimal deterministic scan that always passes safely."""
        mem = self.ctx.memory_store
        any_present = False
        if mem is not None:
            from research_os.memory.store import CANONICAL_FILES
            any_present = any(mem.exists(name) for name in CANONICAL_FILES)
        # Surface into ctx_state so the autonomous loop's success criterion
        # can read it. _merge_ctx_state is a no-op if called outside a run.
        self._merge_ctx_state("any_canonical_present", any_present)
        return self._output(
            task=packet.task,
            status="pass" if any_present else "warning",
            confidence=0.9 if any_present else 0.4,
            summary=(
                "reference deterministic scan: "
                f"any_canonical_present={any_present}"
            ),
        )


__all__ = ["REFERENCE_PROFILE", "ReferenceAutonomousAgent"]
