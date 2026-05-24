"""Core agent-output dataclasses: Finding, Risk, GateUpdate, MemoryUpdate, AgentOutput.

Every agent in ResearchOS returns an AgentOutput. AgentOutput is the contract
between agents, the orchestrator, the registries, and the report writers.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from research_os.schemas.vocab import (
    EVIDENCE_TYPES,
    SEVERITIES,
    STATUSES,
    UPDATE_TYPES,
    require_value,
)


@dataclass
class EvidenceRef:
    type: str  # one of EVIDENCE_TYPES
    id: str = ""
    path: str = ""
    description: str = ""

    def validate(self) -> None:
        require_value("EvidenceRef.type", self.type, EVIDENCE_TYPES)


@dataclass
class Finding:
    finding_id: str
    severity: str  # one of SEVERITIES
    title: str
    description: str = ""
    evidence: List[EvidenceRef] = field(default_factory=list)
    affected_claims: List[str] = field(default_factory=list)
    affected_artifacts: List[str] = field(default_factory=list)
    required_action: str = ""
    blocks_pipeline: bool = False

    def validate(self) -> None:
        require_value("Finding.severity", self.severity, SEVERITIES)
        for ev in self.evidence:
            ev.validate()


@dataclass
class Risk:
    risk_id: str
    severity: str  # one of SEVERITIES
    title: str
    description: str = ""
    likelihood: str = "unknown"
    mitigation: str = ""

    def validate(self) -> None:
        require_value("Risk.severity", self.severity, SEVERITIES)


@dataclass
class GateUpdate:
    gate: str  # GateName value
    new_status: str  # GateStatus value
    reason: str = ""
    evidence: List[EvidenceRef] = field(default_factory=list)


@dataclass
class MemoryUpdate:
    target_file: str
    update_type: str  # one of UPDATE_TYPES
    summary: str
    evidence: List[str] = field(default_factory=list)
    affected_claim_ids: List[str] = field(default_factory=list)
    affected_artifact_ids: List[str] = field(default_factory=list)
    requires_human_approval: bool = False
    reason_human_approval_required: str = ""

    def validate(self) -> None:
        require_value("MemoryUpdate.update_type", self.update_type, UPDATE_TYPES)
        if self.requires_human_approval and not self.reason_human_approval_required:
            raise ValueError(
                "MemoryUpdate.requires_human_approval is True but "
                "reason_human_approval_required is empty"
            )


@dataclass
class AgentOutput:
    agent: str
    agent_id: str
    task: str
    status: str  # one of STATUSES
    confidence: float
    summary: str
    evidence_used: List[EvidenceRef] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    risks: List[Risk] = field(default_factory=list)
    required_actions: List[str] = field(default_factory=list)
    gate_updates: List[GateUpdate] = field(default_factory=list)
    artifacts_created: List[str] = field(default_factory=list)
    artifacts_updated: List[str] = field(default_factory=list)
    artifacts_to_mark_stale: List[str] = field(default_factory=list)
    claims_supported: List[str] = field(default_factory=list)
    claims_weakened: List[str] = field(default_factory=list)
    claims_contradicted: List[str] = field(default_factory=list)
    human_review_required: bool = False
    human_review_reason: str = ""
    updates_to_memory: List[MemoryUpdate] = field(default_factory=list)
    next_recommended_agents: List[str] = field(default_factory=list)
    machine_readable_notes: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        require_value("AgentOutput.status", self.status, STATUSES)
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"AgentOutput.confidence={self.confidence} must be in [0, 1]"
            )
        if self.human_review_required and not self.human_review_reason:
            raise ValueError(
                "AgentOutput.human_review_required is True but human_review_reason is empty"
            )
        for f in self.findings:
            f.validate()
        for r in self.risks:
            r.validate()
        for u in self.updates_to_memory:
            u.validate()
        for ev in self.evidence_used:
            ev.validate()

    def blocks_pipeline(self) -> bool:
        """True if any finding sets blocks_pipeline=True or status is fail/blocked."""
        if self.status in ("fail", "blocked"):
            return True
        return any(f.blocks_pipeline for f in self.findings)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


__all__ = [
    "AgentOutput",
    "EvidenceRef",
    "Finding",
    "GateUpdate",
    "MemoryUpdate",
    "Risk",
]
