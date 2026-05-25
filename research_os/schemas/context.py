"""Context packet (input to an agent) and orchestration plan (output of router)."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from research_os.schemas.vocab import INTENT_CLASSES, RISK_LEVELS, require_value


# Allowed values for OrchestrationPlan.routing_decision.
ROUTING_DECISIONS = (
    "semantic",        # Ollama produced a result and it was accepted as-is
    "keyword_only",    # Ollama unavailable or returned None
    "merged",          # Semantic + keyword results were unioned
    "low_confidence",  # Semantic confidence below threshold; merged with keyword
    "claude_fallback", # AnthropicAPIFallback overrode the decision
    "error",           # Routing failed; minimal safe plan returned
    "unspecified",     # Default before routing runs
)


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
    workflow runners to decide what to do next.

    The semantic-routing upgrade added a set of OPTIONAL fields (all with
    defaults) so existing callers and tests continue to work unchanged:

    - ``routing_decision`` — which routing path produced this plan
    - ``routing_confidence`` — 0-1 confidence from the semantic router
    - ``routing_reason`` — human-readable summary
    - ``ollama_response_raw`` — raw structured JSON from Ollama (for transcripts)
    - ``requires_claude_fallback`` — flag that surfaces via MCP for Claude Code
    - ``selected_workflow`` — name of a workflow recipe the router suggests
    """

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

    # --- semantic-routing additions (all optional / safe defaults) ---
    routing_decision: str = "unspecified"
    routing_confidence: float = 0.0
    routing_reason: str = ""
    ollama_response_raw: Optional[Dict[str, Any]] = None
    requires_claude_fallback: bool = False
    selected_workflow: Optional[str] = None

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
        if self.routing_decision not in ROUTING_DECISIONS:
            raise ValueError(
                f"OrchestrationPlan.routing_decision={self.routing_decision!r} "
                f"not in {ROUTING_DECISIONS}"
            )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


__all__ = ["ContextPacket", "OrchestrationPlan", "ROUTING_DECISIONS"]
