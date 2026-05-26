"""Autonomous Paper/Claim agent.

Wraps the legacy ``PaperClaimAgent``. Autonomous mode adds:

- iterative scan of draft markdown files
- structured suggestion of safe-wording replacements (via LLM if enabled)
- handoff to ``contradiction_hunter`` + ``reviewer_collaboration`` when
  disallowed wording is found

Deterministic fallback = legacy ``PaperClaimAgent.run``.
"""
from __future__ import annotations

from typing import Any, Dict, List

from research_os.agents.base import AgentContext
from research_os.agents.communication import PaperClaimAgent
from research_os.autonomous.agent import AutonomousAgent
from research_os.autonomous.critique import simple_critic
from research_os.autonomous.profile import AgentProfile, AutonomyLevel
from research_os.autonomous.schemas import Budget, Goal, SuccessCriterion
from research_os.schemas.context import ContextPacket
from research_os.schemas.core import AgentOutput


PAPER_CLAIM_PROFILE = AgentProfile(
    agent_id="paper_claim",
    capabilities=["paper_wording_check", "safe_wording_propose",
                  "disallowed_phrase_scan"],
    allowed_tools=[
        "memory_read", "memory_list", "registry_read", "registry_query",
        "file_read", "glob", "llm_chat",
    ],
    domain_areas=["claims", "writing"],
    autonomy_level=AutonomyLevel.ASSISTED,
    confidence_model="evidence_weighted",
    handoff_targets=["biological_realism", "validation_skeptic",
                     "contradiction_hunter", "reviewer_collaboration"],
    failure_modes=["disallowed_wording", "claim_upgrade_attempted"],
    default_budget=Budget(max_iterations=8, max_tool_calls=15,
                          max_failures=2, max_seconds=45.0),
    fallback_behavior="scan_only",
    requires_env=[],
    notes="Phase 4: assisted autonomy — LLM helps propose safe wording only when enabled.",
)


class AutonomousPaperClaimAgent(AutonomousAgent):
    agent_id = "paper_claim"
    display_name = "Autonomous Paper and Claim"

    def __init__(self, ctx: AgentContext, **kwargs):
        kwargs.setdefault("profile", PAPER_CLAIM_PROFILE)
        kwargs.setdefault("critics", [simple_critic])
        super().__init__(ctx, **kwargs)
        self._legacy = PaperClaimAgent(ctx)

    def build_goal(self, packet: ContextPacket) -> Goal:
        return Goal(
            objective="Audit drafts + claim_registry for disallowed wording and propose safe replacements.",
            rationale="Phase 4 paper-claim audit with optional LLM suggestion.",
            success_criteria=[
                SuccessCriterion(
                    name="scan_completed",
                    check_key="scan_completed",
                    op="==", check_value=True,
                ),
            ],
            budget=self.budget,
            inputs={"task": packet.task, "scan_completed": False},
        )

    def _deterministic_run(self, packet: ContextPacket) -> AgentOutput:
        out = self._legacy.run(packet)
        self._merge_ctx_state("scan_completed", True)
        # Append handoff hints for findings.
        if out.findings:
            out.next_recommended_agents = list(out.next_recommended_agents) + [
                "contradiction_hunter", "reviewer_collaboration",
            ]
        return out


__all__ = ["AutonomousPaperClaimAgent", "PAPER_CLAIM_PROFILE"]
