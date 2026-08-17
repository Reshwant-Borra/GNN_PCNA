"""Self-review: run the existing ResearchOS audit over the generated draft.

Rather than inventing a new reviewer, this reuses the project's own claim/paper
audit workflow (PaperClaimAgent disallowed-wording scan, plus the gate machinery)
on the generated ``manuscript.md``. It returns a structured summary the CLI can
print and that records whether the draft is clear of banned wording and what
still requires human sign-off (which ResearchOS never auto-approves).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from paper_engine import config


@dataclass
class SelfReviewResult:
    paper_path: str
    blocked: bool
    human_review_required: bool
    gate_status: Dict[str, str] = field(default_factory=dict)
    findings: List[str] = field(default_factory=list)
    human_review_reasons: List[str] = field(default_factory=list)
    report_path: str = ""

    def ok(self) -> bool:
        """Clear of high/critical findings (human sign-off may still be required)."""
        return not self.blocked


def review(paper_md_path: Path | None = None) -> SelfReviewResult:
    """Run the claim/paper audit over the generated manuscript."""
    from research_os.workflows import run_claim_audit

    paper_md_path = Path(paper_md_path) if paper_md_path else (config.PAPER_DIR / "manuscript.md")
    outcome = run_claim_audit(repo_root=str(config.REPO_ROOT), paper_path=str(paper_md_path))
    result = outcome.result

    findings: List[str] = []
    for out in getattr(result, "agent_outputs", []) or []:
        for f in getattr(out, "findings", []) or []:
            sev = getattr(f, "severity", "")
            title = getattr(f, "title", "")
            if sev in ("high", "critical"):
                findings.append(f"[{sev}] {title}")

    return SelfReviewResult(
        paper_path=str(paper_md_path),
        blocked=bool(getattr(result, "blocked", False)),
        human_review_required=bool(getattr(result, "human_review_required", False)),
        gate_status=dict(getattr(result, "gate_status", {}) or {}),
        findings=findings,
        human_review_reasons=list(getattr(result, "human_review_reasons", []) or []),
        report_path=str(getattr(outcome.report, "markdown", "")),
    )
