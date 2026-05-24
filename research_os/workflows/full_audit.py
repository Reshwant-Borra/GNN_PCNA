"""Full audit workflow: runs every audit-class agent on the current repo.

This is the workflow you run before reviewing the project's health. It does
not train models, run MD, or write paper text. It returns a markdown +
JSON report under reports/research_os/full_audit/<timestamp>/.
"""
from __future__ import annotations

from pathlib import Path

from research_os.workflows.runner import WorkflowOutcome, run_workflow


_FULL_AUDIT_AGENTS = (
    "context_source_truth",
    "provenance_artifacts",
    "dataset_integrity",
    "leakage_split",
    "preprocessing_auditor",
    "scientific_code_review",
    "testing_environment",
    "metrics_statistics",
    "biological_realism",
    "validation_skeptic",
    "paper_claim",
    "visual_evidence",
    "reviewer_collaboration",
    "contradiction_hunter",
    "model_training",
    "research_design",
    "literature_web",
    "compute_planning",
)


def run_full_audit(repo_root: Path | str = ".") -> WorkflowOutcome:
    return run_workflow(
        "full_audit",
        repo_root=repo_root,
        prompt=(
            "Run a complete ResearchOS audit on the current repo: "
            "context, provenance, leakage, preprocessing, metrics, validation, "
            "biology, claims, figures, reviewer risks, and contradictions."
        ),
        intents=[
            "source_of_truth_query",
            "data_audit",
            "split_or_leakage",
            "preprocessing_audit",
            "code_review",
            "metric_verification",
            "md_or_validation",
            "claim_or_paper",
            "figure_generation",
            "contradiction_hunt",
            "submission_readiness",
        ],
        risk_level="high",
        extra_agents=_FULL_AUDIT_AGENTS,
        title="ResearchOS — Full Audit",
        extra_markdown=(
            "This audit is conservative by design. Pass status on any single agent "
            "does not imply the project is publication-ready. Submission readiness is "
            "a separate workflow."
        ),
    )


__all__ = ["run_full_audit"]
