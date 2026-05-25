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

import uuid
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
from research_os.events import emit, init_emitter
from research_os.transcripts import (
    TranscriptWriter,
    init_transcript_for_run,
    finalize_transcript,
)


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
        init_emitter(self.repo_root)

    def bootstrap(self) -> None:
        ensure_memory_initialized(self.memory_store)
        ensure_registries_initialized(self.registry_store)

    def route(self, message: str, *, workflow_id: Optional[str] = None) -> OrchestrationPlan:
        """Route a prompt. If ``workflow_id`` is provided, emit routing events
        so the transcript captures the routing decision.
        """
        if workflow_id:
            emit("routing_started", workflow_id, {"prompt": message[:1000]})
        if workflow_id:
            emit("ollama_router_started", workflow_id, {})
        plan = self.router.route(message)
        if workflow_id:
            emit("ollama_router_completed", workflow_id, {
                "routing_decision": plan.routing_decision,
                "routing_confidence": plan.routing_confidence,
                "ollama_response_raw": plan.ollama_response_raw,
            })
            emit("routing_completed", workflow_id, {
                "routing_decision": plan.routing_decision,
                "routing_confidence": plan.routing_confidence,
                "routing_reason": plan.routing_reason,
                "selected_agents": list(plan.selected_agents),
                "required_gates": list(plan.required_gates),
                "risk_level": plan.risk_level,
                "requires_claude_fallback": plan.requires_claude_fallback,
                "human_review_required": plan.human_review_required,
                "selected_workflow": plan.selected_workflow,
            })
        return plan

    def execute_plan(
        self,
        plan: OrchestrationPlan,
        *,
        workflow_id: Optional[str] = None,
        workflow_name: str = "claude_request",
        transcript: Optional[TranscriptWriter] = None,
    ) -> WorkflowResult:
        """Run the agents in the plan, enforce gates, and return a WorkflowResult.

        ``workflow_id`` and ``transcript`` are optional; when not provided the
        orchestrator creates them so every run gets a transcript on disk.
        """
        agent_outputs: List[AgentOutput] = []
        applied_updates: List[Dict[str, Any]] = []
        pending_updates: List[Dict[str, Any]] = []
        gate_status: Dict[str, str] = {g: "not_started" for g in plan.required_gates}
        human_reasons: List[str] = []
        blocked = plan.blocked
        block_reason = plan.block_reason
        if plan.human_review_required:
            human_reasons.append(plan.human_review_reason)

        wf_id = workflow_id or str(uuid.uuid4())[:8]
        owned_transcript = False
        if transcript is None:
            transcript = init_transcript_for_run(self.reports_dir, workflow_name)
            owned_transcript = True

        emit("workflow_started", wf_id, {
            "workflow_name": plan.request_summary[:120],
            "selected_agents": list(plan.selected_agents),
            "required_gates": list(plan.required_gates),
            "risk_level": plan.context_packet.risk_level,
            "routing_decision": plan.routing_decision,
            "routing_confidence": plan.routing_confidence,
            "requires_claude_fallback": plan.requires_claude_fallback,
        })

        # Surface human approval requests at the workflow level.
        if plan.human_review_required:
            emit("human_approval_requested", wf_id, {
                "scope": "workflow",
                "reason": plan.human_review_reason,
            })

        # Queue all agents up front so the dashboard graph can light them blue.
        for agent_index, agent_id in enumerate(plan.selected_agents):
            emit("agent_queued", wf_id, {
                "agent_id": agent_id,
                "agent_index": agent_index,
                "total_agents": len(plan.selected_agents),
            })

        for agent_id in plan.selected_agents:
            cls = AGENT_REGISTRY.get(agent_id)
            if cls is None:
                continue
            emit("agent_started", wf_id, {
                "agent_id": agent_id,
                "agent_index": len(agent_outputs),
                "total_agents": len(plan.selected_agents),
            })
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
                emit("agent_error", wf_id, {
                    "agent_id": agent_id,
                    "error_message": str(e),
                })

            agent_outputs.append(out)
            emit("agent_completed", wf_id, {
                "agent_id": agent_id,
                "status": out.status,
                "confidence": out.confidence,
                "summary": out.summary,
                "findings_count": len(out.findings),
                "findings": [
                    {
                        "severity": f.severity,
                        "title": f.title,
                        "description": f.description,
                        "required_action": f.required_action,
                        "blocks_pipeline": f.blocks_pipeline,
                    }
                    for f in out.findings[:20]  # cap at 20 for event size
                ],
                "gate_updates": [
                    {"gate": g.gate, "new_status": g.new_status, "reason": g.reason}
                    for g in out.gate_updates
                ],
                "human_review_required": out.human_review_required,
                "human_review_reason": out.human_review_reason if out.human_review_required else "",
                "blocks_pipeline": out.blocks_pipeline(),
            })
            if out.human_review_required:
                human_reasons.append(f"{agent_id}: {out.human_review_reason}")
                emit("human_approval_requested", wf_id, {
                    "scope": "agent",
                    "agent_id": agent_id,
                    "reason": out.human_review_reason,
                })
            # Apply / hold memory updates.
            for update in out.updates_to_memory:
                payload = {"agent": agent_id, **update.__dict__}
                emit("memory_update_proposed", wf_id, {
                    "agent_id": agent_id,
                    "target_file": update.target_file,
                    "update_type": update.update_type,
                    "summary": update.summary[:200],
                    "requires_human_approval": update.requires_human_approval,
                })
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
                    emit("memory_update_applied", wf_id, {
                        "agent_id": agent_id,
                        "target_file": update.target_file,
                        "update_type": update.update_type,
                    })
                except Exception as e:
                    pending_updates.append({**payload, "error": str(e)})

            # Roll up gate updates. Reviewer agents are allowed to override
            # producer agents' gate decisions (no self-approval).
            for gu in out.gate_updates:
                old_gate_status = gate_status.get(gu.gate, "not_started")
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
                emit("gate_updated", wf_id, {
                    "gate": gu.gate,
                    "new_status": gate_status[gu.gate],
                    "old_status": old_gate_status,
                    "updated_by_agent": agent_id,
                    "reason": gu.reason,
                })

            if out.blocks_pipeline():
                blocked = True
                block_reason = f"{agent_id} flagged a blocker: {out.summary}"
                emit("blocker_detected", wf_id, {
                    "agent_id": agent_id,
                    "reason": out.summary,
                })

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
        emit("workflow_completed", wf_id, {
            "blocked": result.blocked,
            "block_reason": result.block_reason,
            "human_review_required": result.human_review_required,
            "gate_status": dict(result.gate_status),
            "applied_updates_count": len(result.applied_memory_updates),
            "pending_updates_count": len(result.pending_memory_updates),
            "workflow_id": wf_id,
            "workflow_name": workflow_name,
        })

        # Finalize transcript: write summary.md + result.json, unregister.
        if owned_transcript:
            try:
                finalize_transcript(
                    transcript,
                    plan_dict=plan.to_dict(),
                    result_dict=result.to_dict(),
                )
            except Exception:
                pass
        return result

    def run(self, message: str, *, workflow_name: str = "claude_request") -> WorkflowResult:
        """End-to-end: create transcript, route, execute, finalize."""
        wf_id = str(uuid.uuid4())[:8]
        transcript = init_transcript_for_run(self.reports_dir, workflow_name)
        plan: Optional[OrchestrationPlan] = None
        result: Optional[WorkflowResult] = None
        try:
            plan = self.route(message, workflow_id=wf_id)
            result = self.execute_plan(
                plan,
                workflow_id=wf_id,
                workflow_name=workflow_name,
                transcript=transcript,
            )
        finally:
            try:
                finalize_transcript(
                    transcript,
                    plan_dict=plan.to_dict() if plan is not None else {},
                    result_dict=result.to_dict() if result is not None else {},
                )
            except Exception:
                pass
        assert result is not None  # execute_plan always returns when plan is set
        return result

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
