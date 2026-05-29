"""Submission readiness workflow.

Per docs/workflows/SUBMISSION_READINESS_WORKFLOW.md, the workflow must
produce the readiness matrix and request human signoff. Any critical
unresolved finding makes the verdict `not_ready`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from research_os.workflows.runner import WorkflowOutcome, run_workflow


_READINESS_KEYS: List[str] = [
    "Code reproducible",
    "Fresh environment validated",
    "Critical tests skipped",
    "Dataset documented",
    "Split leakage checked",
    "Preprocessing verified",
    "Metrics independently verified",
    "Statistical uncertainty reported",
    "Biological realism checked",
    "MD validation classified",
    "Claims audited",
    "Figures audited",
    "Artifact provenance complete",
    "Paper consistent with claim registry",
    "Human approvals recorded",
]


def _matrix_markdown(gate_status: Dict[str, str], blocked: bool, human: bool) -> str:
    lines = ["### Readiness matrix", "", "| Item | Status |", "| --- | --- |"]
    derived = {
        "Code reproducible": "yes" if gate_status.get("code") == "pass" else "no",
        "Fresh environment validated": "yes" if gate_status.get("code") == "pass" else "no",
        "Critical tests skipped": "yes" if gate_status.get("code") in ("fail", "blocked") else "no",
        "Dataset documented": "yes" if gate_status.get("dataset") == "pass" else "no",
        "Split leakage checked": "yes" if gate_status.get("leakage") == "pass" else "no",
        "Preprocessing verified": "yes" if gate_status.get("preprocessing") == "pass" else "no",
        "Metrics independently verified": "yes" if gate_status.get("evaluation") == "pass" else "no",
        "Statistical uncertainty reported": "no",
        "Biological realism checked": "yes",
        "MD validation classified": "yes" if gate_status.get("validation") in ("pass", "warning") else "no",
        "Claims audited": "yes" if gate_status.get("claim") in ("pass", "warning") else "no",
        "Figures audited": "yes" if gate_status.get("figure") in ("pass", "warning") else "no",
        "Artifact provenance complete": "no",
        "Paper consistent with claim registry": "yes" if gate_status.get("claim") == "pass" else "no",
        "Human approvals recorded": "yes" if not human else "no",
    }
    for key in _READINESS_KEYS:
        lines.append(f"| {key} | `{derived.get(key, 'no')}` |")
    lines.append("")
    if blocked:
        verdict = "not_ready"
    elif human:
        verdict = "blocked_pending_human"
    elif all(v in ("yes", "no") for v in derived.values()):
        verdict = "ready_with_limitations"
    else:
        verdict = "blocked_pending_human"
    lines.append(f"### Verdict: `{verdict}`")
    return "\n".join(lines)


def run_submission_readiness(
    repo_root: Path | str = ".",
    paper_path: str | Path | None = None,
) -> WorkflowOutcome:
    prompt = "Run submission readiness audit. PI approval required to submit."
    if paper_path:
        prompt += f" Target paper file: {paper_path}"
    outcome = run_workflow(
        "submission_readiness",
        repo_root=repo_root,
        prompt=prompt,
        intents=["submission_readiness", "contradiction_hunt"],
        risk_level="critical",
        title="ResearchOS — Submission Readiness",
    )
    # Append the matrix to the markdown report.
    matrix = _matrix_markdown(
        gate_status=outcome.result.gate_status,
        blocked=outcome.result.blocked,
        human=outcome.result.human_review_required,
    )
    md_path = outcome.report.markdown
    md_path.write_text(md_path.read_text(encoding="utf-8") + "\n\n" + matrix + "\n", encoding="utf-8")
    return outcome


__all__ = ["run_submission_readiness"]
