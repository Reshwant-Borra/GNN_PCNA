"""Routing layer: classify, score, plan.

The router is deterministic and rule-based. It takes a free-form user request
and produces an `OrchestrationPlan` that names intents, risk, required gates,
selected agents, and any human-approval requirements.
"""

from research_os.routing.intent import classify_intent
from research_os.routing.risk import classify_risk
from research_os.routing.agents import select_agents
from research_os.routing.gates import determine_required_gates
from research_os.routing.human import requires_human_review
from research_os.routing.context_builder import build_context_packet
from research_os.routing.router import Router

__all__ = [
    "Router",
    "build_context_packet",
    "classify_intent",
    "classify_risk",
    "determine_required_gates",
    "requires_human_review",
    "select_agents",
]
