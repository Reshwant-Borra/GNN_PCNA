"""Claim and Paper audit workflow."""
from __future__ import annotations

from pathlib import Path

from research_os.workflows.runner import WorkflowOutcome, run_workflow


def run_claim_audit(
    repo_root: Path | str = ".",
    paper_path: str | Path | None = None,
) -> WorkflowOutcome:
    prompt = "Audit current paper / claim wording for overclaiming."
    if paper_path:
        prompt += f" Target paper file: {paper_path}"
    return run_workflow(
        "claim_audit",
        repo_root=repo_root,
        prompt=prompt,
        intents=[
            "source_of_truth_query",
            "claim_or_paper",
            "metric_verification",
            "md_or_validation",
            "contradiction_hunt",
        ],
        risk_level="high",
        title="ResearchOS — Claim Audit",
        extra_markdown=(
            "Disallowed wording (unless registry approves): 'validated cryptic pocket', "
            "'confirmed novel residues', 'MD proves opening', 'discovered binding site', "
            "'generalizes broadly', 'experimentally validated', 'causal mechanism', 'proved'."
        ),
    )


__all__ = ["run_claim_audit"]
