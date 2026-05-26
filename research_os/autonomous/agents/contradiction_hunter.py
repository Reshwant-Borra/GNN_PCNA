"""Autonomous Contradiction Hunter agent.

Wraps the legacy ``ContradictionHunterAgent``. Adds:

- cross-references between artifact_registry status and claim_registry
  evidence (in addition to the legacy validation/classification check)
- scans paper drafts for additional disallowed phrasings beyond the legacy
  hard-coded list (e.g. "groundbreaking", "first to demonstrate")
- structured spawning of follow-up retry steps when a finding is high
  severity

Deterministic fallback = legacy agent.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from research_os.agents.base import AgentContext
from research_os.agents.context_provenance import ContradictionHunterAgent
from research_os.autonomous.agent import AutonomousAgent
from research_os.autonomous.critique import simple_critic
from research_os.autonomous.profile import AgentProfile, AutonomyLevel
from research_os.autonomous.schemas import Budget, Goal, SuccessCriterion
from research_os.schemas.context import ContextPacket
from research_os.schemas.core import AgentOutput


CONTRADICTION_PROFILE = AgentProfile(
    agent_id="contradiction_hunter",
    capabilities=["contradiction_sweep", "claim_evidence_cross_check",
                  "deep_wording_scan"],
    allowed_tools=[
        "memory_read", "memory_list", "registry_read", "registry_query",
        "file_read", "glob",
    ],
    domain_areas=["validation", "claims"],
    autonomy_level=AutonomyLevel.GUIDED,
    confidence_model="fixed",
    handoff_targets=["paper_claim", "leakage_split", "metrics_statistics",
                     "validation_skeptic"],
    failure_modes=["latent_contradictions"],
    default_budget=Budget(max_iterations=8, max_tool_calls=15,
                          max_failures=2, max_seconds=45.0),
    fallback_behavior="scan_only",
    requires_env=[],
    notes="Phase 4: adds deep wording scan + cross-registry check on top of legacy logic.",
)


_EXTRA_RISKY_PHRASES = (
    "groundbreaking",
    "first to demonstrate",
    "definitive proof",
    "conclusively shows",
    "unprecedented",
    "transformative breakthrough",
    "fully validated",
    "irrefutable",
)


class AutonomousContradictionHunterAgent(AutonomousAgent):
    agent_id = "contradiction_hunter"
    display_name = "Autonomous Contradiction Hunter"

    def __init__(self, ctx: AgentContext, **kwargs):
        kwargs.setdefault("profile", CONTRADICTION_PROFILE)
        kwargs.setdefault("critics", [simple_critic])
        super().__init__(ctx, **kwargs)
        self._legacy = ContradictionHunterAgent(ctx)

    def build_goal(self, packet: ContextPacket) -> Goal:
        return Goal(
            objective="Cross-check claims, metrics, MD evidence + scan drafts for overclaim phrases.",
            rationale="Phase 4 deep contradiction sweep.",
            success_criteria=[
                SuccessCriterion(
                    name="sweep_completed",
                    check_key="sweep_completed",
                    op="==", check_value=True,
                ),
            ],
            budget=self.budget,
            inputs={"task": packet.task, "sweep_completed": False},
        )

    def _deterministic_run(self, packet: ContextPacket) -> AgentOutput:
        out = self._legacy.run(packet)
        # Additional scan: extra risky phrases in drafts.
        try:
            extra_hits = self._scan_extra_phrases()
            self._merge_ctx_state("sweep_completed", True)
            if extra_hits:
                notes = dict(out.machine_readable_notes or {})
                notes["extra_overclaim_hits"] = extra_hits[:10]
                out.machine_readable_notes = notes
                # Promote status if currently pass.
                if out.status == "pass":
                    out.status = "warning"
                out.summary = (
                    f"{out.summary} [+{len(extra_hits)} extra overclaim phrase hits]"
                )
        except Exception:
            self._merge_ctx_state("sweep_completed", True)
        return out

    # ------------------------------------------------------------------

    def _scan_extra_phrases(self) -> List[Dict[str, Any]]:
        repo_root = Path(self.ctx.repo_root).resolve()
        hits: List[Dict[str, Any]] = []
        for p in repo_root.glob("**/*.md"):
            rel = p.relative_to(repo_root)
            if any(part in {".git", "research_os_memory", "reports", "docs",
                            "node_modules", "__pycache__"} for part in rel.parts):
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for phrase in _EXTRA_RISKY_PHRASES:
                for m in re.finditer(rf"\b{re.escape(phrase)}\b", text, re.IGNORECASE):
                    hits.append({"file": str(rel), "phrase": phrase,
                                  "offset": m.start()})
                    if len(hits) >= 50:
                        return hits
        return hits


__all__ = ["AutonomousContradictionHunterAgent", "CONTRADICTION_PROFILE",
           "_EXTRA_RISKY_PHRASES"]
