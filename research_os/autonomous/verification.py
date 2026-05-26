"""Multi-agent verification suite for autonomous campaigns.

Runs the existing 21 scientific agents through the **scientific
orchestrator** (not a new orchestrator) as the final cross-check after
autonomous work. Maps directly to the 10-check verification the user
asked for in the Phase 7 spec:

    1. dataset integrity        → dataset_integrity
    2. leakage / split protocol → leakage_split
    3. code architecture        → scientific_code_review
    4. biological realism       → biological_realism
    5. PCNA-specific claim      → paper_claim (+ biological_realism)
    6. MD validation realism    → validation_skeptic
    7. metrics / statistics     → metrics_statistics
    8. reproducibility / prov.  → testing_environment + provenance_artifacts
    9. contradiction / overclaim→ contradiction_hunter
   10. source quality           → literature_web

The suite is gate-respectful: it relies on the scientific orchestrator's
existing no-self-approval + producer/reviewer logic, so verification can
never silently upgrade a gate.

Output is a ``VerificationReport`` with per-check status, findings, and
suggested follow-up steps that the controller feeds back to the planner.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from research_os.agents import AGENT_REGISTRY, AgentContext, BaseAgent
from research_os.autonomous import events as ev
from research_os.autonomous.schemas import Step
from research_os.orchestrator import Orchestrator
from research_os.routing.agents import select_agents
from research_os.routing.context_builder import build_context_packet
from research_os.routing.gates import determine_required_gates
from research_os.schemas.context import OrchestrationPlan
from research_os.schemas.core import AgentOutput


VERIFICATION_AGENTS_ORDER: List[str] = [
    "context_source_truth",
    "dataset_integrity",
    "leakage_split",
    "preprocessing_auditor",
    "scientific_code_review",
    "biological_realism",
    "validation_skeptic",
    "metrics_statistics",
    "testing_environment",
    "provenance_artifacts",
    "literature_web",
    "paper_claim",
    "reviewer_collaboration",
    "contradiction_hunter",
]


CHECK_NAME_BY_AGENT: Dict[str, str] = {
    "dataset_integrity": "dataset_integrity_check",
    "leakage_split": "leakage_split_check",
    "scientific_code_review": "code_architecture_check",
    "biological_realism": "biological_realism_check",
    "paper_claim": "pcna_claim_check",
    "validation_skeptic": "md_validation_check",
    "metrics_statistics": "metrics_statistics_check",
    "testing_environment": "reproducibility_check",
    "provenance_artifacts": "provenance_check",
    "contradiction_hunter": "contradiction_overclaim_check",
    "literature_web": "source_quality_check",
}


@dataclass
class CheckResult:
    name: str
    agent_id: str
    status: str
    confidence: float
    summary: str
    finding_count: int = 0
    blocks_pipeline: bool = False

    @classmethod
    def from_output(cls, name: str, agent_id: str, out: AgentOutput) -> "CheckResult":
        return cls(
            name=name,
            agent_id=agent_id,
            status=out.status,
            confidence=float(out.confidence),
            summary=out.summary[:280],
            finding_count=len(out.findings),
            blocks_pipeline=out.blocks_pipeline(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "agent_id": self.agent_id,
            "status": self.status,
            "confidence": self.confidence,
            "summary": self.summary,
            "finding_count": self.finding_count,
            "blocks_pipeline": self.blocks_pipeline,
        }


@dataclass
class VerificationReport:
    verification_id: str
    aggregate_status: str
    checks: List[CheckResult] = field(default_factory=list)
    gate_status: Dict[str, str] = field(default_factory=dict)
    blocked: bool = False
    block_reason: str = ""
    spawned_followups: List[Step] = field(default_factory=list)
    plan_dict: Dict[str, Any] = field(default_factory=dict)
    result_dict: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verification_id": self.verification_id,
            "aggregate_status": self.aggregate_status,
            "checks": [c.to_dict() for c in self.checks],
            "gate_status": dict(self.gate_status),
            "blocked": self.blocked,
            "block_reason": self.block_reason,
            "spawned_followup_count": len(self.spawned_followups),
        }


class VerificationSuite:
    """Run the 14-agent verification sequence using the scientific
    orchestrator.

    The suite produces both a per-agent breakdown and a set of
    ``spawned_followups`` (autonomous ``Step``s) that the controller can
    feed back into its planner for the "critic → planner" loop at the
    campaign level.
    """

    def __init__(
        self,
        ctx: AgentContext,
        *,
        orchestrator: Optional[Orchestrator] = None,
        agents_order: Optional[List[str]] = None,
        workflow_id: Optional[str] = None,
    ):
        self.ctx = ctx
        # Build orchestrator pointing at the same memory/registries the ctx
        # uses. We don't bootstrap — assume caller has initialized memory.
        if orchestrator is not None:
            self.orchestrator = orchestrator
        else:
            self.orchestrator = Orchestrator(
                repo_root=ctx.repo_root,
                memory_dir=Path(ctx.repo_root) / "research_os_memory",
                registries_dir=Path(ctx.repo_root) / "research_os_registries",
                reports_dir=Path(ctx.repo_root) / "reports" / "research_os",
            )
        self.agents_order = list(agents_order or VERIFICATION_AGENTS_ORDER)
        self.workflow_id = workflow_id or f"verify-{uuid.uuid4().hex[:8]}"

    # ------------------------------------------------------------------

    def run(self, *, prompt: str = "Multi-agent autonomous verification.",
            intents: Optional[List[str]] = None) -> VerificationReport:
        intents_list = list(intents or [
            "source_of_truth_query", "data_audit", "split_or_leakage",
            "preprocessing_audit", "code_review", "metric_verification",
            "md_or_validation", "claim_or_paper", "contradiction_hunt",
        ])
        # Build a plan whose selected_agents = our verification sequence
        # (subject to AGENT_REGISTRY availability).
        agents = [a for a in self.agents_order if a in AGENT_REGISTRY]
        gates = determine_required_gates(intents_list)
        packet = build_context_packet(
            task=prompt,
            intents=intents_list,
            risk_level="high",
            memory_store=self.orchestrator.memory_store,
            registry_store=self.orchestrator.registry_store,
        )
        plan = OrchestrationPlan(
            request_summary=prompt,
            intents=intents_list,
            risk_level="high",
            selected_agents=agents,
            required_gates=gates,
            context_packet=packet,
        )
        plan.validate()

        result = self.orchestrator.execute_plan(
            plan, workflow_id=self.workflow_id,
            workflow_name="autonomous_verification",
        )

        checks: List[CheckResult] = []
        spawned: List[Step] = []
        for out in result.agent_outputs:
            label = CHECK_NAME_BY_AGENT.get(out.agent_id, f"{out.agent_id}_check")
            check = CheckResult.from_output(label, out.agent_id, out)
            checks.append(check)
            # Each FAIL/WARNING with findings spawns a follow-up step.
            if out.status in ("fail", "warning") and out.findings:
                spawned.append(Step(
                    kind="handoff",
                    description=f"Follow up on {label}: {out.summary[:160]}",
                    target_agent=out.agent_id,
                    rationale="VerificationSuite spawned follow-up for non-pass check",
                ))

        agg = self._aggregate_status(checks, result.blocked)
        report = VerificationReport(
            verification_id=self.workflow_id,
            aggregate_status=agg,
            checks=checks,
            gate_status=dict(result.gate_status),
            blocked=result.blocked,
            block_reason=result.block_reason,
            spawned_followups=spawned,
            plan_dict=plan.to_dict(),
            result_dict=result.to_dict(),
        )
        return report

    # ------------------------------------------------------------------

    @staticmethod
    def _aggregate_status(checks: List[CheckResult], blocked: bool) -> str:
        if blocked or any(c.blocks_pipeline for c in checks):
            return "fail"
        if any(c.status == "fail" for c in checks):
            return "fail"
        if any(c.status == "warning" for c in checks):
            return "warning"
        if not checks:
            return "warning"
        return "pass"


__all__ = ["CHECK_NAME_BY_AGENT", "CheckResult", "VerificationReport",
           "VERIFICATION_AGENTS_ORDER", "VerificationSuite"]
