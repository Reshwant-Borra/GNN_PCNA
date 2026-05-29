"""MD validation workflow."""
from __future__ import annotations

from pathlib import Path

from research_os.workflows.runner import WorkflowOutcome, run_workflow


def run_md_validation(
    repo_root: Path | str = ".",
    md_report_dir: str | Path | None = None,
) -> WorkflowOutcome:
    prompt = "Audit MD validation evidence and classify it explicitly."
    if md_report_dir:
        prompt += f" MD report directory: {md_report_dir}"
    return run_workflow(
        "md_validation",
        repo_root=repo_root,
        prompt=prompt,
        intents=[
            "source_of_truth_query",
            "md_or_validation",
            "metric_verification",
            "contradiction_hunt",
        ],
        risk_level="high",
        title="ResearchOS — MD Validation Audit",
        extra_markdown=(
            "Stable RMSD validates simulation stability — not cryptic pocket opening. "
            "Every MD claim must be explicitly classified as supports / partially supports / "
            "inconclusive / weakens / contradicts."
        ),
    )


__all__ = ["run_md_validation"]
