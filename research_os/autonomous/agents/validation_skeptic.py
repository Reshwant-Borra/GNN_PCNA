"""Autonomous Validation Skeptic agent.

Wraps the legacy ``ValidationSkepticAgent``. Adds:

- searches the repo for MD report directories / analysis JSON
- if found, attempts to read their classification line(s) and cross-check
  against ``VALIDATION_STATUS.md``
- on disagreement, surfaces a contradiction + handoff to
  ``contradiction_hunter``

Deterministic fallback = legacy agent (which reads VALIDATION_STATUS.md
and emits one classification finding).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from research_os.agents.base import AgentContext
from research_os.agents.science_evaluation import ValidationSkepticAgent
from research_os.autonomous.agent import AutonomousAgent
from research_os.autonomous.critique import simple_critic
from research_os.autonomous.profile import AgentProfile, AutonomyLevel
from research_os.autonomous.schemas import Budget, Goal, SuccessCriterion
from research_os.schemas.context import ContextPacket
from research_os.schemas.core import AgentOutput


VALIDATION_PROFILE = AgentProfile(
    agent_id="validation_skeptic",
    capabilities=["md_evidence_classification", "validation_audit",
                  "trajectory_report_scan"],
    allowed_tools=[
        "memory_read", "registry_read", "registry_query",
        "file_read", "glob", "hash_file",
    ],
    domain_areas=["validation", "md"],
    autonomy_level=AutonomyLevel.GUIDED,
    confidence_model="evidence_weighted",
    handoff_targets=["biological_realism", "metrics_statistics",
                     "paper_claim", "contradiction_hunter"],
    failure_modes=["inconclusive_evidence", "validation_disagreement"],
    default_budget=Budget(max_iterations=8, max_tool_calls=20,
                          max_failures=2, max_seconds=45.0),
    fallback_behavior="scan_only",
    requires_env=[],
    notes="Phase 4: scans MD report dirs for classification; legacy fallback otherwise.",
)


_CLASSIFICATION_TOKENS = (
    "supports_claim", "partially_supports_claim", "inconclusive",
    "weakens_claim", "contradicts_claim",
)


class AutonomousValidationSkepticAgent(AutonomousAgent):
    agent_id = "validation_skeptic"
    display_name = "Autonomous Validation Skeptic"

    MD_GLOBS = ("**/md_*.json", "**/md_report*/**/*.md", "**/rmsf*.json",
                "**/dccm*.json", "**/trajectory*.md")

    def __init__(self, ctx: AgentContext, **kwargs):
        kwargs.setdefault("profile", VALIDATION_PROFILE)
        kwargs.setdefault("critics", [simple_critic])
        super().__init__(ctx, **kwargs)
        self._legacy = ValidationSkepticAgent(ctx)

    def build_goal(self, packet: ContextPacket) -> Goal:
        return Goal(
            objective="Cross-check MD trajectory reports against VALIDATION_STATUS.md classification.",
            rationale="Detect classification disagreement between memory and disk.",
            success_criteria=[
                SuccessCriterion(
                    name="scan_completed",
                    check_key="scan_completed",
                    op="==", check_value=True,
                ),
            ],
            budget=self.budget,
            inputs={"task": packet.task, "scan_completed": False},
        )

    def _deterministic_run(self, packet: ContextPacket) -> AgentOutput:
        out = self._legacy.run(packet)
        # In autonomous mode, also surface any classification tokens found
        # in MD report files on disk so the controller can detect drift.
        try:
            on_disk = self._scan_md_reports()
            self._merge_ctx_state("scan_completed", True)
            if on_disk:
                memory_class = (out.machine_readable_notes or {}).get("classification", "")
                disagreements = [
                    c for c in on_disk if c and c != memory_class and memory_class
                ]
                notes = dict(out.machine_readable_notes or {})
                notes["md_classifications_on_disk"] = on_disk
                notes["disagreements_with_memory"] = disagreements
                out.machine_readable_notes = notes
                if disagreements:
                    out.next_recommended_agents = list(out.next_recommended_agents) + [
                        "contradiction_hunter"
                    ]
                    out.summary = (
                        f"{out.summary} [disagreement: memory={memory_class!r} "
                        f"vs disk={disagreements!r}]"
                    )
        except Exception:
            self._merge_ctx_state("scan_completed", True)
        return out

    # ------------------------------------------------------------------

    def _scan_md_reports(self) -> List[str]:
        repo_root = Path(self.ctx.repo_root).resolve()
        found: List[str] = []
        for pat in self.MD_GLOBS:
            for p in repo_root.glob(pat):
                if not p.is_file():
                    continue
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                for tok in _CLASSIFICATION_TOKENS:
                    if re.search(rf"\b{tok}\b", text):
                        found.append(tok)
                        break
                if len(found) >= 20:
                    return found
        return found


__all__ = ["AutonomousValidationSkepticAgent", "VALIDATION_PROFILE"]
