"""Master Research Orchestrator Agent (the role-agent, distinct from the
Orchestrator class that runs the system).

This agent's job inside a workflow is to summarize the routing decision, the
selected gates, the reviewer-style risks, and the recommended next step.
It does not approve any of its own routing — the actual Orchestrator class
enforces gate blocking.
"""
from __future__ import annotations

from research_os.agents.base import BaseAgent, GateName
from research_os.schemas.context import ContextPacket
from research_os.schemas.core import AgentOutput


class MasterResearchOrchestratorAgent(BaseAgent):
    agent_id = "master_orchestrator"
    display_name = "Master Research Orchestrator"

    def run(self, packet: ContextPacket) -> AgentOutput:
        intents = packet.intents or ["general"]
        bullet_intents = ", ".join(intents)
        gates_reminder = (
            "Block paper writing until claim, evaluation, and validation gates pass."
            if "claim_or_paper" in intents
            else "Enforce gates per intent map."
        )
        evidence = []
        if "PROJECT_CANONICAL_STATUS.md" in {n.rsplit("\\", 1)[-1].rsplit("/", 1)[-1] for n in packet.memory_files}:
            evidence.append(self._evidence_memory("PROJECT_CANONICAL_STATUS.md", "source of truth"))

        findings = []
        if "claim_or_paper" in intents and "validation_skeptic" not in (packet.prior_agent_outputs or []):
            findings.append(
                self._new_finding(
                    severity="info",
                    title="Validation agent must run before any claim wording is finalized",
                    description=(
                        "claim_or_paper intent detected. The orchestrator must include the "
                        "Validation, Biological Realism, Metrics, Contradiction, and Provenance "
                        "agents and not let the Paper agent self-approve."
                    ),
                )
            )

        return self._output(
            task=packet.task,
            status="pass",
            confidence=0.85,
            summary=(
                f"Routed request with intents [{bullet_intents}] at risk={packet.risk_level}. "
                f"{gates_reminder}"
            ),
            evidence_used=evidence,
            findings=findings,
            required_actions=[
                "Run agents in the order recommended by the router.",
                "Refuse to accept headline metrics without Leakage + Metrics sign-off.",
                "Refuse paper writing until Claim, Evaluation, Validation gates pass.",
            ],
            next_recommended_agents=packet.prior_agent_outputs and [] or ["context_source_truth"],
        )
