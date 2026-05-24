"""Context packet (input to an agent) and orchestration plan (output of router)."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List

from research_os.schemas.vocab import INTENT_CLASSES, RISK_LEVELS, require_value


@dataclass
class ContextPacket:
    """What an agent receives. Agents should not need to read random repo files
    beyond what's listed here; the Context Agent and Orchestrator are responsible
    for picking the right context."""

    task: str
    intents: List[str] = field(default_factory=list)
    risk_level: str = "medium"
    memory_files: List[str] = field(default_factory=list)
    registry_entries: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    repo_files: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    known_risks: List[str] = field(default_factory=list)
    allowed_actions: List[str] = field(default_factory=list)
    forbidden_actions: List[str] = field(default_factory=list)
    expected_output_schema: str = "AgentOutput"
    prior_agent_outputs: List[Dict[str, Any]] = field(default_factory=list)

    def validate(self) -> None:
        require_value("ContextPacket.risk_level", self.risk_level, RISK_LEVELS)
        for intent in self.intents:
            require_value("ContextPacket.intents", intent, INTENT_CLASSES)


@dataclass
class OrchestrationPlan:
    """Result of routing a user request. Used by both the CLI and downstream
    workflow runners to decide what to do next."""

    request_summary: str
    intents: List[str] = field(default_factory=list)
    risk_level: str = "medium"
    selected_agents: List[str] = field(default_factory=list)
    required_gates: List[str] = field(default_factory=list)
    context_packet: ContextPacket = field(
        default_factory=lambda: ContextPacket(task="")
    )
    actions: List[str] = field(default_factory=list)
    blocked: bool = False
    block_reason: str = ""
    human_review_required: bool = False
    human_review_reason: str = ""
    expected_outputs: List[str] = field(default_factory=list)

    def validate(self) -> None:
        require_value("OrchestrationPlan.risk_level", self.risk_level, RISK_LEVELS)
        for intent in self.intents:
            require_value("OrchestrationPlan.intents", intent, INTENT_CLASSES)
        if self.blocked and not self.block_reason:
            raise ValueError("Plan.blocked is True but block_reason is empty")
        if self.human_review_required and not self.human_review_reason:
            raise ValueError(
                "Plan.human_review_required is True but human_review_reason is empty"
            )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


__all__ = ["ContextPacket", "OrchestrationPlan"]
