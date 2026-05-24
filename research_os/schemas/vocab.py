"""Closed vocabularies used by registries, agents, and the router.

Every status, severity, intent, gate, artifact type, and claim strength lives
here so validators can reject typos and stale values cannot quietly enter
JSON registries.
"""
from __future__ import annotations

STATUSES = (
    "pass",
    "warning",
    "fail",
    "blocked",
    "inconclusive",
    "not_applicable",
)

SEVERITIES = ("critical", "high", "medium", "low", "info")

RISK_LEVELS = ("low", "medium", "high", "critical")

GATE_STATUSES = (
    "not_started",
    "in_progress",
    "pass",
    "warning",
    "fail",
    "blocked",
    "stale",
)

ARTIFACT_STATUSES = (
    "current",
    "stale",
    "invalid",
    "superseded",
    "draft",
    "archived",
)

ARTIFACT_TYPES = (
    "raw_data",
    "processed_data",
    "split",
    "graph",
    "checkpoint",
    "training_log",
    "prediction",
    "metric",
    "md_trajectory",
    "md_topology",
    "md_analysis",
    "figure",
    "table",
    "report",
    "paper_draft",
    "memory",
    "other",
)

CLAIM_STRENGTHS = (
    "proven_experimentally",
    "strongly_supported_computationally",
    "moderately_supported",
    "suggestive",
    "hypothesis_generating",
    "unsupported",
    "contradicted",
    "deprecated",
)

EXPERIMENT_STATUSES = (
    "planned",
    "approved",
    "running",
    "completed",
    "failed",
    "invalid",
    "superseded",
)

ISSUE_STATUSES = ("open", "investigating", "fixed", "wont_fix", "superseded")

EVIDENCE_CLASSIFICATIONS = (
    "supports_claim",
    "partially_supports_claim",
    "inconclusive",
    "weakens_claim",
    "contradicts_claim",
    "does_not_address_claim",
)

UPDATE_TYPES = (
    "add_fact",
    "revise_fact",
    "deprecate_fact",
    "add_claim",
    "downgrade_claim",
    "upgrade_claim",
    "reject_claim",
    "add_artifact",
    "mark_artifact_stale",
    "mark_artifact_invalid",
    "add_human_decision",
    "add_bug",
    "resolve_bug",
    "add_reviewer_risk",
    "update_validation_status",
)

INTENT_CLASSES = (
    "source_of_truth_query",
    "research_design",
    "data_audit",
    "split_or_leakage",
    "preprocessing_audit",
    "code_build",
    "code_review",
    "training",
    "metric_verification",
    "md_or_validation",
    "claim_or_paper",
    "figure_generation",
    "compute_planning",
    "submission_readiness",
    "collaboration_sync",
    "contradiction_hunt",
    "general",
)

AGENT_IDS = (
    "master_orchestrator",
    "context_source_truth",
    "research_design",
    "biological_realism",
    "literature_web",
    "dataset_integrity",
    "leakage_split",
    "preprocessing_auditor",
    "code_builder",
    "scientific_code_review",
    "testing_environment",
    "model_training",
    "metrics_statistics",
    "compute_planning",
    "validation_skeptic",
    "contradiction_hunter",
    "provenance_artifacts",
    "paper_claim",
    "visual_evidence",
    "reviewer_collaboration",
)

EVIDENCE_TYPES = (
    "memory",
    "registry",
    "source_code",
    "artifact",
    "literature",
    "human_decision",
    "experiment",
    "log",
)


def require_value(name: str, value: str, allowed: tuple[str, ...]) -> None:
    """Raise ValueError if value not in the allowed vocabulary."""
    if value not in allowed:
        allowed_str = ", ".join(allowed)
        raise ValueError(
            f"{name}={value!r} is not one of the allowed values: {allowed_str}"
        )
