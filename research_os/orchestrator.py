"""Orchestrator: the live, gate-enforcing runtime that turns a router plan
into actual agent invocations.

The Orchestrator is the *only* component that:

- runs agents in order,
- applies (or blocks) memory updates,
- reads gate updates and decides whether to block the rest of the pipeline,
- escalates to a human approval prompt,
- and bundles the final WorkflowResult.

No agent may approve its own work — the orchestrator never trusts a producer
agent's own status when a reviewer agent says "fail".
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from research_os.agents import AGENT_REGISTRY, AgentContext, BaseAgent
from research_os.memory.store import (
    CANONICAL_FILES,
    MemoryStore,
    MemoryUpdateProposal,
    apply_memory_update,
    ensure_memory_initialized,
)
from research_os.registries.store import RegistryStore, ensure_registries_initialized
from research_os.routing.router import Router
from research_os.schemas.context import ContextPacket, OrchestrationPlan
from research_os.schemas.core import AgentOutput, GateUpdate
from research_os.schemas.gates import GateName, GateStatus
from research_os.tools.git import capture_git_state


# Producer / reviewer pairs from docs/03_AGENT_INTERACTION_MODEL.md.
# An agent in the "producer" column cannot self-approve work that the named
# reviewers should sign off on.
_PRODUCER_REVIEWERS: Dict[str, List[str]] = {
    "code_builder": ["scientific_code_review", "testing_environment"],
    "model_training": ["metrics_statistics", "leakage_split", "provenance_artifacts"],
    "metrics_statistics": ["contradiction_hunter", "provenance_artifacts"],
    "validation_skeptic": ["biological_realism", "paper_claim"],
    "paper_claim": ["reviewer_collaboration", "contradiction_hunter"],
    "visual_evidence": ["paper_claim", "metrics_statistics"],
}


@dataclass
class WorkflowResult:
    plan: OrchestrationPlan
    agent_outputs: List[AgentOutput] = field(default_factory=list)
    gate_status: Dict[str, str] = field(default_factory=dict)
    blocked: bool = False
    block_reason: str = ""
    human_review_required: bool = False
    human_review_reasons: List[str] = field(default_factory=list)
    applied_memory_updates: List[Dict[str, Any]] = field(default_factory=list)
    pending_memory_updates: List[Dict[str, Any]] = field(default_factory=list)
    git: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan": self.plan.to_dict(),
            "agent_outputs": [a.to_dict() for a in self.agent_outputs],
            "gate_status": dict(self.gate_status),
            "blocked": self.blocked,
            "block_reason": self.block_reason,
            "human_review_required": self.human_review_required,
            "human_review_reasons": list(self.human_review_reasons),
            "applied_memory_updates": list(self.applied_memory_updates),
            "pending_memory_updates": list(self.pending_memory_updates),
            "git": dict(self.git),
        }


class Orchestrator:
    """Wraps Router + agent execution + gate enforcement.

    The Orchestrator NEVER writes to disk on behalf of an agent without going
    through the memory/registry stores' validation paths. Memory updates that
    require human approval are held in ``pending_memory_updates``; agents
    must surface them to the operator.
    """

    def __init__(
        self,
        *,
        repo_root: Path | str = ".",
        memory_dir: Path | str = "research_os_memory",
        registries_dir: Path | str = "research_os_registries",
        reports_dir: Path | str = "reports/research_os",
    ):
        self.repo_root = Path(repo_root)
        self.memory_dir = Path(memory_dir)
        self.registries_dir = Path(registries_dir)
        self.reports_dir = Path(reports_dir)
        self.memory_store = MemoryStore(self.memory_dir)
        self.registry_store = RegistryStore(self.registries_dir)
        self.router = Router(memory_store=self.memory_store, registry_store=self.registry_store)
        self.agent_context = AgentContext(
            repo_root=self.repo_root,
            memory_store=self.memory_store,
            registry_store=self.registry_store,
            reports_root=self.reports_dir,
        )

    def bootstrap(self) -> None:
        ensure_memory_initialized(self.memory_store)
        ensure_registries_initialized(self.registry_store)

    def route(self, message: str) -> OrchestrationPlan:
        return self.router.route(message)

    def execute_plan(self, plan: OrchestrationPlan) -> WorkflowResult:
        """Run the agents in the plan, enforce gates, and return a WorkflowResult."""
        agent_outputs: List[AgentOutput] = []
        applied_updates: List[Dict[str, Any]] = []
        pending_updates: List[Dict[str, Any]] = []
        gate_status: Dict[str, str] = {g: "not_started" for g in plan.required_gates}
        human_reasons: List[str] = []
        blocked = plan.blocked
        block_reason = plan.block_reason
        if plan.human_review_required:
            human_reasons.append(plan.human_review_reason)

        for agent_id in plan.selected_agents:
            cls = AGENT_REGISTRY.get(agent_id)
            if cls is None:
                continue
            agent: BaseAgent = cls(self.agent_context)
            packet = ContextPacket(
                task=plan.context_packet.task,
                intents=list(plan.context_packet.intents),
                risk_level=plan.context_packet.risk_level,
                memory_files=list(plan.context_packet.memory_files),
                registry_entries=dict(plan.context_packet.registry_entries),
                repo_files=list(plan.context_packet.repo_files),
                artifacts=list(plan.context_packet.artifacts),
                known_risks=list(plan.context_packet.known_risks),
                allowed_actions=list(plan.context_packet.allowed_actions),
                forbidden_actions=list(plan.context_packet.forbidden_actions),
                prior_agent_outputs=[a.to_dict() for a in agent_outputs],
            )
            try:
                out = agent.run(packet)
            except Exception as e:  # pragma: no cover — defensive
                out = AgentOutput(
                    agent=cls.__name__,
                    agent_id=agent_id,
                    task=packet.task,
                    status="fail",
                    confidence=0.0,
                    summary=f"agent crashed: {e}",
                    human_review_required=True,
                    human_review_reason=f"crash in {agent_id}: {e}",
                )
                out.validate()

            agent_outputs.append(out)
            if out.human_review_required:
                human_reasons.append(f"{agent_id}: {out.human_review_reason}")
            # Apply / hold memory updates.
            for update in out.updates_to_memory:
                payload = {"agent": agent_id, **update.__dict__}
                if update.requires_human_approval:
                    pending_updates.append(payload)
                    continue
                try:
                    proposal = MemoryUpdateProposal(
                        target_file=update.target_file,
                        update_type=update.update_type,
                        summary=update.summary,
                        proposed_by=agent_id,
                        append_section=update.summary if update.target_file in CANONICAL_FILES else None,
                        evidence=list(update.evidence),
                        affected_claim_ids=list(update.affected_claim_ids),
                        affected_artifact_ids=list(update.affected_artifact_ids),
                        requires_human_approval=False,
                    )
                    apply_memory_update(self.memory_store, proposal, applied_by=agent_id)
                    applied_updates.append(payload)
                except Exception as e:
                    pending_updates.append({**payload, "error": str(e)})

            # Roll up gate updates. Reviewer agents are allowed to override
            # producer agents' gate decisions (no self-approval).
            for gu in out.gate_updates:
                if gu.gate not in gate_status:
                    gate_status[gu.gate] = gu.new_status
                else:
                    # If the agent IS the producer of this gate's domain, it can only
                    # warn or fail — it cannot upgrade a gate to pass when a reviewer
                    # has not yet weighed in.
                    if self._agent_is_self_approving(agent_id, gu.gate, agent_outputs[:-1]):
                        if gu.new_status == "pass":
                            gate_status[gu.gate] = "warning"
                        else:
                            gate_status[gu.gate] = gu.new_status
                    else:
                        gate_status[gu.gate] = self._merge_gate_status(
                            gate_status[gu.gate], gu.new_status
                        )

            if out.blocks_pipeline():
                blocked = True
                block_reason = f"{agent_id} flagged a blocker: {out.summary}"

        # Hard rule: any gate left at fail or blocked or stale ⇒ pipeline blocked.
        for gate, status in gate_status.items():
            if status in ("fail", "blocked", "stale"):
                blocked = True
                if not block_reason:
                    block_reason = f"gate {gate} status={status} blocks pipeline."

        result = WorkflowResult(
            plan=plan,
            agent_outputs=agent_outputs,
            gate_status=gate_status,
            blocked=blocked,
            block_reason=block_reason,
            human_review_required=bool(human_reasons) or plan.human_review_required,
            human_review_reasons=human_reasons,
            applied_memory_updates=applied_updates,
            pending_memory_updates=pending_updates,
            git=capture_git_state(self.repo_root).to_dict(),
        )
        return result

    def run(self, message: str) -> WorkflowResult:
        plan = self.route(message)
        return self.execute_plan(plan)

    # ----- helpers -----

    _GATE_OWNERS: Dict[str, str] = {
        GateName.CODE: "code_builder",
        GateName.EVALUATION: "model_training",
        GateName.VALIDATION: "validation_skeptic",
        GateName.CLAIM: "paper_claim",
        GateName.FIGURE: "visual_evidence",
    }

    def _agent_is_self_approving(
        self,
        agent_id: str,
        gate: str,
        prior_outputs: List[AgentOutput],
    ) -> bool:
        owner = self._GATE_OWNERS.get(gate)
        if owner != agent_id:
            return False
        # Owner agent. Check that at least one required reviewer ran before this.
        reviewers = _PRODUCER_REVIEWERS.get(agent_id, [])
        if not reviewers:
            return False
        seen_reviewer = {p.agent_id for p in prior_outputs}
        return not seen_reviewer.intersection(reviewers)

    @staticmethod
    def _merge_gate_status(current: str, incoming: str) -> str:
        """Take the worst of the two statuses (pass weakest, blocked strongest)."""
        order = ["pass", "warning", "stale", "blocked", "fail", "not_started", "in_progress"]
        severity = {s: i for i, s in enumerate(order)}
        return current if severity.get(current, 0) >= severity.get(incoming, 0) else incoming


__all__ = ["Orchestrator", "WorkflowResult"]
