"""AutonomousController — Phase 5 upgrade.

Goal-driven entry point that:

1. Optionally runs the ``InfrastructureHealer`` to fix dangling files /
   missing scaffolds before any agent runs (controlled by ``heal_first``).
2. Decomposes the top-level ``Goal`` into sub-goals via the
   ``default_decomposer`` (template-based) — or honors a caller-supplied
   ``sub_goals`` list.
3. Dispatches each sub-goal to:
   - a registered ``AutonomousAgent`` factory (the normal case), OR
   - the ``VerificationSuite`` when ``target_agent == "__verification_suite__"``,
     which runs the existing 21 scientific agents through the scientific
     orchestrator and produces a ``VerificationReport``.
4. Aggregates outcomes into a ``CampaignResult``.
5. Emits ``campaign_started`` / ``campaign_completed`` plus all per-step
   events the agents already emit.

The controller still does not collapse the two orchestrators — compute
work is surfaced as ``HandoffRequest`` payloads for the caller to forward
to ``agents/orchestrator.py``.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from research_os.agents.base import AgentContext
from research_os.autonomous import events as ev
from research_os.autonomous.agent import AutonomousAgent
from research_os.autonomous.decomposer import Decomposer, default_decomposer
from research_os.autonomous.healer import HealReport, InfrastructureHealer
from research_os.autonomous.profile import profile_for
from research_os.autonomous.schemas import (
    Budget,
    Goal,
    HandoffRequest,
    Plan,
    Step,
    StepStatus,
)
from research_os.autonomous.verification import VerificationReport, VerificationSuite
from research_os.schemas.context import ContextPacket
from research_os.schemas.core import AgentOutput


AgentFactory = Callable[[AgentContext], AutonomousAgent]


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class SubGoalOutcome:
    sub_goal: Goal
    agent_id: str
    output: Optional[AgentOutput] = None
    verification_report: Optional[VerificationReport] = None
    error: str = ""
    skipped: bool = False

    @property
    def succeeded(self) -> bool:
        if self.skipped or self.error:
            return False
        if self.verification_report is not None:
            return self.verification_report.aggregate_status in ("pass", "warning")
        if self.output is None:
            return False
        return self.output.status in ("pass", "warning")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sub_goal_id": self.sub_goal.goal_id,
            "agent_id": self.agent_id,
            "status": (
                self.output.status if self.output is not None
                else (self.verification_report.aggregate_status
                      if self.verification_report is not None else "missing")
            ),
            "error": self.error,
            "skipped": self.skipped,
            "output_summary": (self.output.summary if self.output is not None else ""),
            "verification": (self.verification_report.to_dict()
                             if self.verification_report is not None else None),
        }


@dataclass
class CampaignResult:
    campaign_id: str
    top_goal: Goal
    sub_outcomes: List[SubGoalOutcome] = field(default_factory=list)
    handoffs: List[HandoffRequest] = field(default_factory=list)
    aggregate_status: str = "pass"
    summary: str = ""
    heal_report: Optional[HealReport] = None
    verification_reports: List[VerificationReport] = field(default_factory=list)
    spawned_followups: List[Step] = field(default_factory=list)

    @property
    def succeeded_count(self) -> int:
        return sum(1 for o in self.sub_outcomes if o.succeeded)

    @property
    def failed_count(self) -> int:
        return sum(1 for o in self.sub_outcomes if not o.succeeded and not o.skipped)

    @property
    def skipped_count(self) -> int:
        return sum(1 for o in self.sub_outcomes if o.skipped)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "top_goal": self.top_goal.to_dict(),
            "sub_outcomes": [o.to_dict() for o in self.sub_outcomes],
            "handoffs": [h.to_dict() for h in self.handoffs],
            "aggregate_status": self.aggregate_status,
            "summary": self.summary,
            "heal_report": self.heal_report.to_dict() if self.heal_report else None,
            "verification_report_count": len(self.verification_reports),
            "spawned_followup_count": len(self.spawned_followups),
            "counts": {
                "succeeded": self.succeeded_count,
                "failed": self.failed_count,
                "skipped": self.skipped_count,
            },
        }


# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------

class AutonomousController:
    def __init__(
        self,
        ctx: AgentContext,
        *,
        agent_factories: Optional[Dict[str, AgentFactory]] = None,
        default_agent_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        decomposer: Optional[Decomposer] = None,
        verification_suite: Optional[VerificationSuite] = None,
        healer: Optional[InfrastructureHealer] = None,
        cross_critics: Optional[List[Any]] = None,
    ):
        self.ctx = ctx
        self.agent_factories = dict(agent_factories or {})
        self.default_agent_id = default_agent_id
        self.workflow_id = workflow_id or f"campaign-{uuid.uuid4().hex[:8]}"
        self.decomposer = decomposer or default_decomposer()
        self.verification_suite = verification_suite or VerificationSuite(
            ctx, workflow_id=self.workflow_id,
        )
        self.healer = healer or InfrastructureHealer(ctx.repo_root)
        self.cross_critics = list(cross_critics or [])

    # ------------------------------------------------------------------

    def register_agent(self, agent_id: str, factory: AgentFactory) -> None:
        self.agent_factories[agent_id] = factory

    def register_agents(self, factories: Dict[str, AgentFactory]) -> None:
        for k, v in factories.items():
            self.agent_factories[k] = v

    # ------------------------------------------------------------------

    def pursue_goal(
        self,
        goal: Goal,
        *,
        sub_goals: Optional[List[Goal]] = None,
        packet: Optional[ContextPacket] = None,
        heal_first: bool = False,
        heal_dry_run: bool = True,
        run_verification: bool = True,
    ) -> CampaignResult:
        """Run a campaign for the top-level ``goal``.

        - If ``sub_goals`` is None, the decomposer breaks the goal into
          sub-goals.
        - If ``heal_first`` is True, the healer runs first; ``heal_dry_run``
          controls whether it actually scaffolds missing modules.
        - If ``run_verification`` is True and the decomposition did not
          already include a ``__verification_suite__`` sub-goal, the
          controller appends one at the end.
        """
        campaign_id = f"camp-{uuid.uuid4().hex[:8]}"

        result = CampaignResult(campaign_id=campaign_id, top_goal=goal)

        # 1. Optional infrastructure heal.
        if heal_first:
            result.heal_report = self.healer.heal_all(dry_run=heal_dry_run)

        # 2. Decompose.
        if sub_goals is not None:
            decomposition = list(sub_goals)
        else:
            decomposition = self.decomposer.decompose(goal)

        # 3. Optionally append verification sub-goal.
        if run_verification and not any(
            sg.inputs.get("target_agent") == "__verification_suite__"
            for sg in decomposition
        ):
            decomposition.append(Goal(
                objective="Final multi-agent verification.",
                rationale="Controller-appended verification pass.",
                budget=goal.budget,
                inputs={"target_agent": "__verification_suite__"},
                parent_goal_id=goal.goal_id,
            ))

        ev.campaign_started(self.workflow_id, campaign_id=campaign_id,
                            goal_id=goal.goal_id,
                            sub_goal_count=len(decomposition))

        # 4. Dispatch each sub-goal.
        for sg in decomposition:
            agent_id = sg.inputs.get("target_agent") or self.default_agent_id
            outcome = self._dispatch(sg, agent_id, packet)
            result.sub_outcomes.append(outcome)
            # Collect verification reports + spawned follow-ups.
            if outcome.verification_report is not None:
                result.verification_reports.append(outcome.verification_report)
                result.spawned_followups.extend(outcome.verification_report.spawned_followups)
            if outcome.output is not None:
                # The autonomous agent's last_run_result (if any) may carry handoff
                # records; surface them.
                for c in outcome.output.next_recommended_agents or []:
                    result.handoffs.append(HandoffRequest(
                        from_agent=outcome.agent_id, to_agent=c,
                        reason=outcome.output.summary[:120],
                    ))

        # 5. Aggregate.
        if result.failed_count > 0:
            result.aggregate_status = "fail"
        elif result.succeeded_count == 0:
            result.aggregate_status = "fail"
        elif result.skipped_count > 0 or any(
            o.output is not None and o.output.status == "warning"
            for o in result.sub_outcomes
        ):
            result.aggregate_status = "warning"
        else:
            result.aggregate_status = "pass"
        result.summary = (
            f"campaign {campaign_id}: {result.succeeded_count} ok, "
            f"{result.failed_count} failed, {result.skipped_count} skipped, "
            f"{len(result.handoffs)} handoffs queued, "
            f"{len(result.verification_reports)} verifications, "
            f"{len(result.spawned_followups)} follow-ups spawned."
        )
        ev.campaign_completed(
            self.workflow_id, campaign_id=campaign_id, goal_id=goal.goal_id,
            status=result.aggregate_status,
            completed_sub_goals=result.succeeded_count,
            failed_sub_goals=result.failed_count,
        )
        return result

    # ------------------------------------------------------------------

    def _dispatch(self, sub_goal: Goal, agent_id: Optional[str],
                  packet: Optional[ContextPacket]) -> SubGoalOutcome:
        if not agent_id:
            return SubGoalOutcome(
                sub_goal=sub_goal, agent_id="(unspecified)",
                error="no agent_id provided", skipped=True,
            )
        # Special agent: verification suite.
        if agent_id == "__verification_suite__":
            try:
                report = self.verification_suite.run(prompt=sub_goal.objective)
                return SubGoalOutcome(
                    sub_goal=sub_goal, agent_id=agent_id,
                    verification_report=report,
                )
            except Exception as e:
                return SubGoalOutcome(
                    sub_goal=sub_goal, agent_id=agent_id,
                    error=f"verification suite crashed: {type(e).__name__}: {e}",
                )
        # Special agent: synthesis writer. If a campaign has registered one
        # under this id, dispatch normally; otherwise return a structured
        # placeholder so the campaign still completes.
        if agent_id == "__synthesis_writer__" and agent_id not in self.agent_factories:
            return self._run_synthesis_placeholder(sub_goal)
        # Normal autonomous agent.
        factory = self.agent_factories.get(agent_id)
        if factory is None:
            return SubGoalOutcome(
                sub_goal=sub_goal, agent_id=agent_id,
                error=f"no agent factory registered for {agent_id}",
                skipped=True,
            )
        try:
            agent = factory(self.ctx)
        except Exception as e:
            return SubGoalOutcome(sub_goal=sub_goal, agent_id=agent_id,
                                  error=f"factory failed: {e}")
        pkt = packet or ContextPacket(task=sub_goal.objective)
        try:
            output = agent.run(pkt)
            return SubGoalOutcome(sub_goal=sub_goal, agent_id=agent_id, output=output)
        except Exception as e:
            return SubGoalOutcome(sub_goal=sub_goal, agent_id=agent_id,
                                  error=f"agent crashed: {type(e).__name__}: {e}")

    def _run_synthesis_placeholder(self, sub_goal: Goal) -> SubGoalOutcome:
        """Phase-7 campaigns register a real synthesis writer; until then,
        this placeholder produces a structured 'deferred' outcome rather
        than crashing the campaign."""
        return SubGoalOutcome(
            sub_goal=sub_goal,
            agent_id="__synthesis_writer__",
            error="synthesis writer not registered; deferred to Phase 7 campaign",
            skipped=True,
        )


__all__ = ["AutonomousController", "CampaignResult", "SubGoalOutcome",
           "AgentFactory"]
