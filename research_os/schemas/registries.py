"""Registry entry dataclasses: artifact, claim, experiment, issue, source, environment, decision.

Each entry has a stable ID, created/updated timestamps, a status from a closed
vocabulary, and links to other registries by ID. Atomic writes happen through
research_os.registries.store.RegistryStore.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List

from research_os.schemas.vocab import (
    ARTIFACT_STATUSES,
    ARTIFACT_TYPES,
    CLAIM_STRENGTHS,
    EVIDENCE_CLASSIFICATIONS,
    EXPERIMENT_STATUSES,
    ISSUE_STATUSES,
    require_value,
)


@dataclass
class ArtifactEntry:
    artifact_id: str
    path: str
    artifact_type: str  # ARTIFACT_TYPES
    status: str = "draft"  # ARTIFACT_STATUSES
    created_at: str = ""
    updated_at: str = ""
    created_by_agent: str = ""
    git_commit: str = ""
    git_dirty: bool = False
    dataset_hash: str = ""
    checkpoint_hash: str = ""
    environment_hash: str = ""
    machine: str = ""
    command: str = ""
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    status_reason: str = ""
    associated_claims: List[str] = field(default_factory=list)
    associated_experiments: List[str] = field(default_factory=list)
    associated_figures: List[str] = field(default_factory=list)
    associated_tables: List[str] = field(default_factory=list)
    associated_reports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    downstream_artifacts: List[str] = field(default_factory=list)
    notes: str = ""

    def validate(self) -> None:
        require_value("ArtifactEntry.artifact_type", self.artifact_type, ARTIFACT_TYPES)
        require_value("ArtifactEntry.status", self.status, ARTIFACT_STATUSES)


@dataclass
class ClaimEntry:
    claim_id: str
    claim_text: str
    claim_strength: str = "hypothesis_generating"  # CLAIM_STRENGTHS
    status: str = "hypothesis_generating"  # mirrors strength for legacy callers
    created_at: str = ""
    updated_at: str = ""
    created_by: str = ""
    plain_language_summary: str = ""
    evidence_for: List[str] = field(default_factory=list)
    evidence_against: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    required_evidence_to_strengthen: List[str] = field(default_factory=list)
    allowed_wording: List[str] = field(default_factory=list)
    disallowed_wording: List[str] = field(default_factory=list)
    required_citations: List[str] = field(default_factory=list)
    associated_artifacts: List[str] = field(default_factory=list)
    associated_experiments: List[str] = field(default_factory=list)
    associated_figures: List[str] = field(default_factory=list)
    associated_paper_sections: List[str] = field(default_factory=list)
    gate_status: Dict[str, str] = field(default_factory=dict)
    human_approval: Dict[str, Any] = field(default_factory=lambda: {
        "required": False,
        "decision_id": "",
        "approval_status": "not_required",
    })
    notes: str = ""

    def validate(self) -> None:
        require_value(
            "ClaimEntry.claim_strength", self.claim_strength, CLAIM_STRENGTHS
        )
        require_value("ClaimEntry.status", self.status, CLAIM_STRENGTHS)


@dataclass
class ExperimentEntry:
    experiment_id: str
    title: str
    purpose: str
    hypothesis_tested: str
    null_hypothesis: str = ""
    expected_outcome: str = ""
    status: str = "planned"  # EXPERIMENT_STATUSES
    created_at: str = ""
    updated_at: str = ""
    created_by_agent: str = ""
    input_artifacts: List[str] = field(default_factory=list)
    output_artifacts: List[str] = field(default_factory=list)
    script_or_workflow: str = ""
    command: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    environment_id: str = ""
    git_commit: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    actual_outcome: str = ""
    interpretation: str = ""
    failure_modes: List[str] = field(default_factory=list)
    evidence_classification: str = "inconclusive"  # EVIDENCE_CLASSIFICATIONS
    associated_claims: List[str] = field(default_factory=list)
    gate_results: Dict[str, str] = field(default_factory=dict)
    human_approval: Dict[str, Any] = field(default_factory=lambda: {
        "required": False,
        "decision_id": "",
        "status": "not_required",
    })
    notes: str = ""

    def validate(self) -> None:
        require_value("ExperimentEntry.status", self.status, EXPERIMENT_STATUSES)
        require_value(
            "ExperimentEntry.evidence_classification",
            self.evidence_classification,
            EVIDENCE_CLASSIFICATIONS,
        )


@dataclass
class IssueEntry:
    issue_id: str
    title: str
    description: str
    status: str = "open"  # ISSUE_STATUSES
    severity: str = "medium"
    created_at: str = ""
    updated_at: str = ""
    created_by: str = ""
    affected_artifacts: List[str] = field(default_factory=list)
    affected_claims: List[str] = field(default_factory=list)
    resolution: str = ""
    notes: str = ""

    def validate(self) -> None:
        require_value("IssueEntry.status", self.status, ISSUE_STATUSES)


@dataclass
class SourceEntry:
    source_id: str
    source: str
    topic: str = ""
    created_at: str = ""
    updated_at: str = ""
    key_methods: List[str] = field(default_factory=list)
    required_controls: List[str] = field(default_factory=list)
    metrics_used: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    relevance_to_project: str = ""
    claims_supported: List[str] = field(default_factory=list)
    claims_not_supported: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class EnvironmentEntry:
    environment_id: str
    description: str = ""
    created_at: str = ""
    updated_at: str = ""
    python_version: str = ""
    os: str = ""
    machine: str = ""
    package_hash: str = ""
    cuda_version: str = ""
    notes: str = ""


@dataclass
class DecisionEntry:
    decision_id: str
    date: str
    decision_maker: str
    request: str
    options: List[str] = field(default_factory=list)
    decision: str = ""
    rationale: str = ""
    evidence: List[str] = field(default_factory=list)
    affected_claims: List[str] = field(default_factory=list)
    affected_artifacts: List[str] = field(default_factory=list)
    follow_up: List[str] = field(default_factory=list)
    notes: str = ""


__all__ = [
    "ArtifactEntry",
    "ClaimEntry",
    "DecisionEntry",
    "EnvironmentEntry",
    "ExperimentEntry",
    "IssueEntry",
    "SourceEntry",
]


def entry_to_dict(entry: Any) -> Dict[str, Any]:
    """Convert any registry dataclass to a JSON-safe dict."""
    return asdict(entry)
