"""Top-level Router: glue intent + risk + agents + gates + human + context."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from research_os.memory.store import MemoryStore
from research_os.registries.store import RegistryStore
from research_os.routing.agents import select_agents
from research_os.routing.context_builder import build_context_packet
from research_os.routing.gates import determine_required_gates
from research_os.routing.human import requires_human_review
from research_os.routing.intent import classify_intent
from research_os.routing.risk import classify_risk
from research_os.schemas.context import OrchestrationPlan


class Router:
    def __init__(
        self,
        memory_store: Optional[MemoryStore] = None,
        registry_store: Optional[RegistryStore] = None,
    ):
        self.memory_store = memory_store
        self.registry_store = registry_store

    def route(self, message: str) -> OrchestrationPlan:
        intents = classify_intent(message)
        risk = classify_risk(message, intents)
        agents = select_agents(intents, risk)
        gates = determine_required_gates(intents)
        human_required, human_reason = requires_human_review(message, intents, risk)
        packet = build_context_packet(
            task=message,
            intents=intents,
            risk_level=risk,
            memory_store=self.memory_store,
            registry_store=self.registry_store,
        )
        plan = OrchestrationPlan(
            request_summary=message.strip().splitlines()[0][:280] if message.strip() else "(empty)",
            intents=intents,
            risk_level=risk,
            selected_agents=agents,
            required_gates=gates,
            context_packet=packet,
            actions=self._actions_for(intents, agents, gates, risk),
            blocked=False,
            block_reason="",
            human_review_required=human_required,
            human_review_reason=human_reason,
            expected_outputs=self._expected_outputs_for(intents),
        )
        plan.validate()
        return plan

    def _actions_for(
        self,
        intents: List[str],
        agents: List[str],
        gates: List[str],
        risk: str,
    ) -> List[str]:
        actions: List[str] = []
        actions.append(f"Run agents in order: {', '.join(agents)}")
        if gates:
            actions.append(f"Evaluate gates: {', '.join(gates)}")
        if "claim_or_paper" in intents:
            actions.append("Block paper writing if claim/validation/leakage gates are not pass.")
        if "training" in intents:
            actions.append("Reject metrics if dataset, leakage, preprocessing, or code gates fail.")
        if "md_or_validation" in intents:
            actions.append("Require explicit MD evidence classification before any validation claim.")
        if "submission_readiness" in intents:
            actions.append("Produce readiness matrix and request human signoff.")
        if risk in ("high", "critical"):
            actions.append("Run contradiction hunter at end of pipeline.")
        return actions

    def _expected_outputs_for(self, intents: List[str]) -> List[str]:
        out: List[str] = ["AgentOutput per agent", "OrchestrationPlan JSON"]
        if "training" in intents:
            out.append("Updated experiment_registry + artifact_registry entries")
        if "metric_verification" in intents:
            out.append("Verified metrics JSON with confidence intervals")
        if "md_or_validation" in intents:
            out.append("Validation classification: supports|partially|inconclusive|weakens|contradicts")
        if "claim_or_paper" in intents:
            out.append("Claim audit report with safe-wording replacements")
        if "submission_readiness" in intents:
            out.append("Readiness matrix + human signoff prompt")
        return out


__all__ = ["Router"]
