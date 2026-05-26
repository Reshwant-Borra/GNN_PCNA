"""Autonomous variants of existing ResearchOS scientific agents.

This subpackage holds Phase 4 migrations. Each agent here subclasses
``AutonomousAgent`` and provides:

- a ``_deterministic_run`` method preserving the legacy behavior, and
- an ``AgentProfile`` with elevated autonomy_level + a curated tool
  allow-list.

The registry below is **additive**: the existing
``research_os.agents.AGENT_REGISTRY`` is unchanged. Callers (the
``AutonomousController``, future MCP ``pursue_goal`` tool) opt into the
autonomous variants by name; everything else continues to dispatch
through the legacy registry.

If an autonomous variant is enabled but the upgrade fails or autonomy is
disabled, the agent falls back to the deterministic scan — which is the
exact same logic the legacy agent uses. There is no behavior loss.
"""
from typing import Callable, Dict

from research_os.agents.base import AgentContext
from research_os.autonomous.agent import AutonomousAgent
from research_os.autonomous.agents.code_builder import AutonomousCodeBuilderAgent
from research_os.autonomous.agents.contradiction_hunter import (
    AutonomousContradictionHunterAgent,
)
from research_os.autonomous.agents.document_ingestion import (
    AutonomousDocumentIngestionAgent,
)
from research_os.autonomous.agents.literature_web import AutonomousLiteratureWebAgent
from research_os.autonomous.agents.paper_claim import AutonomousPaperClaimAgent
from research_os.autonomous.agents.validation_skeptic import (
    AutonomousValidationSkepticAgent,
)


AUTONOMOUS_AGENTS: Dict[str, Callable[[AgentContext], AutonomousAgent]] = {
    "literature_web": AutonomousLiteratureWebAgent,
    "document_knowledge_ingestion": AutonomousDocumentIngestionAgent,
    "code_builder": AutonomousCodeBuilderAgent,
    "paper_claim": AutonomousPaperClaimAgent,
    "validation_skeptic": AutonomousValidationSkepticAgent,
    "contradiction_hunter": AutonomousContradictionHunterAgent,
}


__all__ = [
    "AUTONOMOUS_AGENTS",
    "AutonomousCodeBuilderAgent",
    "AutonomousContradictionHunterAgent",
    "AutonomousDocumentIngestionAgent",
    "AutonomousLiteratureWebAgent",
    "AutonomousPaperClaimAgent",
    "AutonomousValidationSkepticAgent",
]
