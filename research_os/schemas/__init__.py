"""Dataclasses and validation for ResearchOS structured outputs.

Every agent, registry entry, and orchestration plan in ResearchOS is a typed
dataclass with explicit allowed-value vocabularies. Wire data crosses module
boundaries only through these schemas.
"""

from research_os.schemas.core import (
    AgentOutput,
    EvidenceRef,
    Finding,
    GateUpdate,
    MemoryUpdate,
    Risk,
)
from research_os.schemas.context import ContextPacket, OrchestrationPlan
from research_os.schemas.gates import GateStatus, GateName
from research_os.schemas.registries import (
    ArtifactEntry,
    ClaimEntry,
    DecisionEntry,
    EnvironmentEntry,
    ExperimentEntry,
    IssueEntry,
    SourceEntry,
)
from research_os.schemas.vocab import (
    AGENT_IDS,
    ARTIFACT_STATUSES,
    ARTIFACT_TYPES,
    CLAIM_STRENGTHS,
    EVIDENCE_CLASSIFICATIONS,
    EXPERIMENT_STATUSES,
    GATE_STATUSES,
    INTENT_CLASSES,
    ISSUE_STATUSES,
    RISK_LEVELS,
    SEVERITIES,
    STATUSES,
    UPDATE_TYPES,
)

__all__ = [
    "AgentOutput",
    "ArtifactEntry",
    "ClaimEntry",
    "ContextPacket",
    "DecisionEntry",
    "EnvironmentEntry",
    "EvidenceRef",
    "ExperimentEntry",
    "Finding",
    "GateName",
    "GateStatus",
    "GateUpdate",
    "IssueEntry",
    "MemoryUpdate",
    "OrchestrationPlan",
    "Risk",
    "SourceEntry",
    "AGENT_IDS",
    "ARTIFACT_STATUSES",
    "ARTIFACT_TYPES",
    "CLAIM_STRENGTHS",
    "EVIDENCE_CLASSIFICATIONS",
    "EXPERIMENT_STATUSES",
    "GATE_STATUSES",
    "INTENT_CLASSES",
    "ISSUE_STATUSES",
    "RISK_LEVELS",
    "SEVERITIES",
    "STATUSES",
    "UPDATE_TYPES",
]
