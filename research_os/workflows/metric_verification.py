"""Metric verification workflow."""
from __future__ import annotations

from pathlib import Path

from research_os.workflows.runner import WorkflowOutcome, run_workflow


def run_metric_verification(
    repo_root: Path | str = ".",
    metrics_path: str | Path | None = None,
) -> WorkflowOutcome:
    prompt = "Independently verify metrics in the repo."
    if metrics_path:
        prompt += f" Metrics file: {metrics_path}"
    return run_workflow(
        "metric_verification",
        repo_root=repo_root,
        prompt=prompt,
        intents=[
            "source_of_truth_query",
            "metric_verification",
            "split_or_leakage",
            "code_review",
            "contradiction_hunt",
        ],
        risk_level="high",
        title="ResearchOS — Metric Verification",
        extra_markdown=(
            "Headline metrics are only valid when the Leakage gate passes and the Metrics "
            "agent independently reproduces the numbers with appropriate uncertainty."
        ),
    )


__all__ = ["run_metric_verification"]
