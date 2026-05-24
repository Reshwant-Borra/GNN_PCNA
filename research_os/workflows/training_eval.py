"""Training + Evaluation workflow.

Per docs/workflows/TRAINING_EVALUATION_WORKFLOW.md, the workflow must pass
Dataset, Leakage, Preprocessing, Code, Evaluation, and Provenance gates and
must run baselines.
"""
from __future__ import annotations

from pathlib import Path

from research_os.workflows.runner import WorkflowOutcome, run_workflow


def run_training_eval(
    repo_root: Path | str = ".",
    prompt: str = "Plan and review a leakage-clean training + evaluation run.",
) -> WorkflowOutcome:
    return run_workflow(
        "training_eval",
        repo_root=repo_root,
        prompt=prompt,
        intents=[
            "source_of_truth_query",
            "data_audit",
            "split_or_leakage",
            "preprocessing_audit",
            "training",
            "metric_verification",
            "code_review",
            "contradiction_hunt",
        ],
        risk_level="high",
        title="ResearchOS — Training and Evaluation Audit",
        extra_markdown=(
            "Training results are only valid when Dataset, Leakage, Preprocessing, "
            "Code, and Evaluation gates pass *and* the GNN beats the required baselines "
            "(random, sequence-only, geometry-only, distance-to-known-pocket, "
            "logistic regression / random forest, conservation if available, fpocket if relevant)."
        ),
    )


__all__ = ["run_training_eval"]
