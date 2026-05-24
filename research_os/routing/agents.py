"""Agent selector.

Maps intent + risk + gate requirements to the ordered list of agents that
should run. The Context Agent always runs first; the Contradiction Agent
always runs last for medium+ risk so any conflicts surface before we hand
back to the user.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# Per-intent agent set. Each agent ID matches research_os.schemas.vocab.AGENT_IDS.
_AGENT_MAP: Dict[str, Tuple[str, ...]] = {
    "source_of_truth_query": (
        "context_source_truth",
        "provenance_artifacts",
        "contradiction_hunter",
    ),
    "research_design": (
        "context_source_truth",
        "research_design",
        "literature_web",
        "biological_realism",
    ),
    "data_audit": (
        "context_source_truth",
        "dataset_integrity",
        "preprocessing_auditor",
        "leakage_split",
    ),
    "split_or_leakage": (
        "context_source_truth",
        "leakage_split",
        "dataset_integrity",
        "metrics_statistics",
    ),
    "preprocessing_audit": (
        "context_source_truth",
        "preprocessing_auditor",
        "dataset_integrity",
        "scientific_code_review",
    ),
    "code_build": (
        "context_source_truth",
        "code_builder",
        "scientific_code_review",
        "testing_environment",
        "provenance_artifacts",
    ),
    "code_review": (
        "context_source_truth",
        "scientific_code_review",
        "testing_environment",
    ),
    "training": (
        "context_source_truth",
        "leakage_split",
        "dataset_integrity",
        "preprocessing_auditor",
        "model_training",
        "metrics_statistics",
        "provenance_artifacts",
    ),
    "metric_verification": (
        "context_source_truth",
        "metrics_statistics",
        "leakage_split",
        "provenance_artifacts",
        "contradiction_hunter",
    ),
    "md_or_validation": (
        "context_source_truth",
        "validation_skeptic",
        "biological_realism",
        "metrics_statistics",
        "provenance_artifacts",
    ),
    "claim_or_paper": (
        "context_source_truth",
        "paper_claim",
        "metrics_statistics",
        "validation_skeptic",
        "biological_realism",
        "provenance_artifacts",
        "contradiction_hunter",
        "reviewer_collaboration",
    ),
    "figure_generation": (
        "context_source_truth",
        "visual_evidence",
        "metrics_statistics",
        "paper_claim",
        "provenance_artifacts",
    ),
    "compute_planning": (
        "context_source_truth",
        "compute_planning",
        "validation_skeptic",
    ),
    "submission_readiness": (
        "context_source_truth",
        "provenance_artifacts",
        "leakage_split",
        "preprocessing_auditor",
        "metrics_statistics",
        "biological_realism",
        "validation_skeptic",
        "paper_claim",
        "visual_evidence",
        "reviewer_collaboration",
        "testing_environment",
        "contradiction_hunter",
    ),
    "collaboration_sync": (
        "context_source_truth",
        "reviewer_collaboration",
        "provenance_artifacts",
    ),
    "contradiction_hunt": (
        "context_source_truth",
        "contradiction_hunter",
        "provenance_artifacts",
        "leakage_split",
        "metrics_statistics",
        "paper_claim",
    ),
    "general": (
        "context_source_truth",
    ),
}


def select_agents(intents: List[str], risk_level: str) -> List[str]:
    """Return an ordered, deduplicated list of agents to run.

    Context Agent is always first (source of truth before any other reasoning).
    Contradiction Agent is appended to anything high or critical risk if it
    wasn't already chosen by intent.
    """
    ordered: List[str] = []
    seen: set[str] = set()

    def push(agent_id: str) -> None:
        if agent_id not in seen:
            ordered.append(agent_id)
            seen.add(agent_id)

    push("context_source_truth")
    for intent in intents:
        for agent in _AGENT_MAP.get(intent, ()):
            push(agent)

    if risk_level in ("high", "critical") and "contradiction_hunter" not in seen:
        push("contradiction_hunter")
    if risk_level == "critical" and "reviewer_collaboration" not in seen:
        push("reviewer_collaboration")
    return ordered


__all__ = ["select_agents"]
