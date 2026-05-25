"""GNN ResearchOS — conservative research operating system.

Public API stays small. Most callers should go through `research_os.orchestrator.Orchestrator`
or the CLI in `research_os.__main__`.
"""

from research_os.schemas import (
    AgentOutput,
    ArtifactEntry,
    ClaimEntry,
    ContextPacket,
    ExperimentEntry,
    Finding,
    GateStatus,
    OrchestrationPlan,
    Risk,
)

__version__ = "0.1.0"


def __getattr__(name):
    # Lazy: importing Orchestrator early would pull in every agent and the router.
    if name == "Orchestrator":
        from research_os.orchestrator import Orchestrator as _Orchestrator
        return _Orchestrator
    raise AttributeError(f"module 'research_os' has no attribute {name!r}")


__all__ = [
    "AgentOutput",
    "ArtifactEntry",
    "ClaimEntry",
    "ContextPacket",
    "ExperimentEntry",
    "Finding",
    "GateStatus",
    "OrchestrationPlan",
    "Orchestrator",
    "Risk",
]
