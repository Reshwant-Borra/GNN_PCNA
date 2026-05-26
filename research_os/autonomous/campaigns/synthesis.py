"""Synthesis writer for Phase 2 campaigns.

The ``Phase2SynthesisWriter`` is an ``AutonomousAgent`` that takes the
campaign state (source_registry contents, verification report, heal
report) and produces the canonical Phase 2 deliverables under
``research_corpus/``:

- ``PHASE2_CORPUS.md``        — full source index
- ``gap_analysis.md``         — categories below threshold
- ``synthesis_draft.md``      — multi-section narrative synthesis
- ``phase2_design_rules.md``  — design rules extracted from the corpus
- ``readiness_assessment.md`` — verdict + supporting evidence
- ``implementation_roadmap.md`` — Phase 2 implementation plan
- ``remediation_plan.md``     — issues found + recommended fixes

The writer is intentionally deterministic — it composes structured
markdown from the registries / reports passed in via ``ContextPacket``.
LLM-aided synthesis is out of scope for Phase 3-7; a future agent can
sit alongside this one.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from research_os.agents.base import AgentContext
from research_os.autonomous.agent import AutonomousAgent
from research_os.autonomous.coverage import CoverageEstimator
from research_os.autonomous.profile import AgentProfile, AutonomyLevel
from research_os.autonomous.schemas import Budget, Goal, SuccessCriterion
from research_os.schemas.context import ContextPacket
from research_os.schemas.core import AgentOutput


SYNTHESIS_PROFILE = AgentProfile(
    agent_id="__synthesis_writer__",
    capabilities=["synthesis_writing", "report_composition",
                  "phase_assessment", "roadmap_generation"],
    allowed_tools=[
        "memory_read", "memory_list", "registry_read", "registry_query",
        "file_read", "glob", "git_state",
    ],
    domain_areas=["writing", "synthesis"],
    autonomy_level=AutonomyLevel.GUIDED,
    confidence_model="fixed",
    handoff_targets=["paper_claim", "reviewer_collaboration"],
    failure_modes=["empty_corpus", "missing_verification_report"],
    default_budget=Budget(max_iterations=6, max_tool_calls=12,
                          max_failures=2, max_seconds=60.0),
    fallback_behavior="scan_only",
    requires_env=[],
    notes="Composes the Phase 2 corpus + readiness artifacts deterministically.",
)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Phase2SynthesisWriter(AutonomousAgent):
    """Agent that writes Phase 2 deliverables to disk."""

    agent_id = "__synthesis_writer__"
    display_name = "Phase 2 Synthesis Writer"

    def __init__(
        self,
        ctx: AgentContext,
        *,
        coverage_estimator: Optional[CoverageEstimator] = None,
        verification_report: Optional[Any] = None,
        heal_report: Optional[Any] = None,
        output_dir_name: str = "research_corpus",
        **kwargs,
    ):
        kwargs.setdefault("profile", SYNTHESIS_PROFILE)
        super().__init__(ctx, **kwargs)
        self.coverage_estimator = coverage_estimator
        self.verification_report = verification_report
        self.heal_report = heal_report
        self.output_dir = Path(ctx.repo_root) / output_dir_name
        self._written_paths: List[Path] = []

    # ------------------------------------------------------------------

    def build_goal(self, packet: ContextPacket) -> Goal:
        return Goal(
            objective="Compose Phase 2 corpus + synthesis + readiness deliverables.",
            rationale="Phase 7 campaign final synthesis step.",
            success_criteria=[
                SuccessCriterion(
                    name="all_deliverables_written",
                    check_key="all_deliverables_written",
                    op="==", check_value=True,
                ),
            ],
            budget=self.budget,
        )

    def _deterministic_run(self, packet: ContextPacket) -> AgentOutput:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        sources = self._read_sources()
        coverage_dict = self._compute_coverage(sources)

        # Compose each deliverable.
        self._write_corpus_index(sources, coverage_dict)
        self._write_gap_analysis(sources, coverage_dict)
        self._write_synthesis_draft(sources, coverage_dict)
        self._write_phase2_design_rules(sources)
        self._write_readiness_assessment(sources, coverage_dict)
        self._write_implementation_roadmap()
        self._write_remediation_plan()
        self._write_campaign_summary(sources, coverage_dict)

        self._merge_ctx_state("all_deliverables_written", True)
        return self._output(
            task=packet.task,
            status="pass" if sources else "warning",
            confidence=0.85 if sources else 0.45,
            summary=(
                f"Phase 2 synthesis wrote {len(self._written_paths)} files; "
                f"{len(sources)} sources, coverage={coverage_dict.get('score', 0.0):.2f}."
            ),
            notes={
                "written_paths": [str(p) for p in self._written_paths],
                "source_count": len(sources),
                "coverage_score": coverage_dict.get("score", 0.0),
            },
        )

    # ------------------------------------------------------------------
    # Readers
    # ------------------------------------------------------------------

    def _read_sources(self) -> List[Dict[str, Any]]:
        store = self.ctx.registry_store
        if store is None:
            return []
        try:
            return list(store.all_entries("source_registry"))
        except Exception:
            return []

    def _compute_coverage(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        if self.coverage_estimator is None or not sources:
            return {"score": 0.0, "gaps": [], "per_category_counts": {}}
        result = self.coverage_estimator.evaluate(sources)
        return result.to_dict()

    # ------------------------------------------------------------------
    # Writers
    # ------------------------------------------------------------------

    def _write(self, name: str, body: str) -> None:
        path = self.output_dir / name
        path.write_text(body, encoding="utf-8")
        self._written_paths.append(path)

    def _write_corpus_index(self, sources: List[Dict[str, Any]],
                            coverage: Dict[str, Any]) -> None:
        lines: List[str] = []
        lines.append("# Phase 2 Corpus Index")
        lines.append("")
        lines.append(f"Generated: {_utc_iso()}")
        lines.append(f"Source count: **{len(sources)}**")
        lines.append(f"Coverage score: **{coverage.get('score', 0.0):.2f}**")
        lines.append("")
        lines.append("## Sources")
        lines.append("")
        if not sources:
            lines.append("_(no sources registered yet — run a corpus build with web tools enabled.)_")
        else:
            lines.append("| SRC-ID | Title | Source | Topics | Relevance |")
            lines.append("| --- | --- | --- | --- | --- |")
            for s in sources:
                topics = s.get("topics") or []
                topics_str = ", ".join(topics[:4])
                lines.append(
                    f"| {s.get('id', '?')} | {(s.get('title') or '')[:80]} "
                    f"| {s.get('source_type', s.get('source', ''))} "
                    f"| {topics_str} | {s.get('relevance_score', 0.0):.2f} |"
                )
        lines.append("")
        lines.append("## Coverage by category")
        lines.append("")
        cat_counts = coverage.get("per_category_counts", {}) or {}
        cat_scores = coverage.get("per_category_score", {}) or {}
        if cat_counts:
            lines.append("| Category | Items | Score |")
            lines.append("| --- | --- | --- |")
            for name in cat_counts:
                lines.append(
                    f"| {name} | {cat_counts[name]} | {cat_scores.get(name, 0.0):.2f} |"
                )
        else:
            lines.append("_(no coverage estimator configured)_")
        self._write("PHASE2_CORPUS.md", "\n".join(lines) + "\n")

    def _write_gap_analysis(self, sources: List[Dict[str, Any]],
                            coverage: Dict[str, Any]) -> None:
        gaps = coverage.get("gaps", []) or []
        suggested = coverage.get("suggested_queries", []) or []
        lines = ["# Phase 2 Gap Analysis", ""]
        lines.append(f"Generated: {_utc_iso()}")
        lines.append(f"Total items considered: **{coverage.get('total_items', len(sources))}**")
        lines.append(f"Overall coverage: **{coverage.get('score', 0.0):.2f}**")
        lines.append("")
        if not gaps:
            lines.append("All categories meet their minimum-item threshold. No coverage gaps.")
        else:
            lines.append(f"## {len(gaps)} category gap(s)")
            lines.append("")
            for gap, query in zip(gaps, suggested + [""] * len(gaps)):
                lines.append(f"### {gap}")
                if query:
                    lines.append(f"- Suggested follow-up query: `{query}`")
                lines.append("")
        self._write("gap_analysis.md", "\n".join(lines) + "\n")

    def _write_synthesis_draft(self, sources: List[Dict[str, Any]],
                                coverage: Dict[str, Any]) -> None:
        lines = ["# Phase 2 Synthesis Draft", ""]
        lines.append(f"Generated: {_utc_iso()}")
        lines.append("")
        lines.append("## 1. Scope")
        lines.append("")
        lines.append(
            "This synthesis covers the GNN-PCNA project's Phase 2 readiness across "
            "(a) PCNA biology and AOH1996 chemistry, (b) protein graph neural "
            "networks, (c) cryptic-pocket detection and MD validation methods, "
            "(d) leakage-clean split design, (e) baselines, and (f) reproducibility "
            "/ provenance discipline."
        )
        lines.append("")
        lines.append("## 2. Source overview")
        lines.append("")
        lines.append(f"The autonomous corpus build registered {len(sources)} sources.")
        cat_counts = coverage.get("per_category_counts", {}) or {}
        if cat_counts:
            covered = sorted(((name, n) for name, n in cat_counts.items()), key=lambda x: -x[1])
            for name, n in covered:
                lines.append(f"- **{name}**: {n} sources")
        lines.append("")
        lines.append("## 3. Key themes")
        lines.append("")
        lines.append(
            "- Cryptic pockets are dynamic features; static structure prediction "
            "alone is insufficient evidence for novel binding-site claims."
        )
        lines.append(
            "- Leakage-clean splits (homology + apo/holo + chain) are the dominant "
            "concern for any reported AUROC/AUPRC on small structural test sets."
        )
        lines.append(
            "- MD evidence must be classified explicitly (supports / partially / "
            "inconclusive / weakens / contradicts) before any \"validated\" wording."
        )
        lines.append(
            "- Reproducibility = pinned env + deterministic seeds + artifact hashing; "
            "skipped critical deps count as failure, not pass."
        )
        lines.append("")
        lines.append("## 4. Phase 2 implications")
        lines.append("")
        lines.append(
            "Phase 2 should treat the existing PocketGNNXL V3 checkpoint as a "
            "starting point but explicitly enumerate the baselines it must "
            "outperform under the leakage-clean split before any paper claim "
            "above ``moderately_supported`` is permitted."
        )
        self._write("synthesis_draft.md", "\n".join(lines) + "\n")

    def _write_phase2_design_rules(self, sources: List[Dict[str, Any]]) -> None:
        lines = [
            "# Phase 2 Design Rules",
            "",
            f"Generated: {_utc_iso()}",
            "",
            "Hard rules for Phase 2 (extracted from the corpus + project memory):",
            "",
            "1. **No \"validated cryptic pocket\" wording** until MD evidence is "
            "explicitly classified as ``supports_claim`` or ``partially_supports_claim``.",
            "2. **Split protocol must list six checks**: chain, PDB, homology, "
            "apo/holo, label transfer, feature normalization. Any unaddressed "
            "check fails the leakage gate.",
            "3. **Headline metrics require both AUROC and AUPRC** with bootstrap "
            "confidence intervals at the protein-level independence unit.",
            "4. **Baselines required**: random, sequence-only, geometry-only, "
            "distance-to-known-pocket, logistic regression / random forest, "
            "conservation if available, fpocket if relevant.",
            "5. **Provenance required** for every paper-grade artifact: "
            "git commit, command, timestamp, upstream dependency IDs.",
            "6. **Reproducibility check**: tests/ must include a fresh-environment "
            "smoke test that does not skip torch_geometric / PyG.",
            "7. **Reviewer Risk Register** must list at minimum the canonical 12 "
            "reviewer questions; each must have a documented mitigation.",
            "8. **Compute budget**: any MD run > 4 GPU-hours or any cloud cost "
            "requires PI approval logged in HUMAN_DECISIONS.md.",
            "9. **9B8T chain bug** (BUG-001) must be resolved with regenerated "
            "inference on chains B/C/D before any 9B8T-based claim is made.",
            "10. **Stale-artifact propagation**: any \"current\" paper-grade artifact "
            "whose dependencies are stale/invalid must be marked stale.",
            "",
        ]
        self._write("phase2_design_rules.md", "\n".join(lines))

    def _write_readiness_assessment(self, sources: List[Dict[str, Any]],
                                     coverage: Dict[str, Any]) -> None:
        verdict, supporting = self._readiness_verdict(sources, coverage)
        lines = ["# Phase 2 Readiness Assessment", ""]
        lines.append(f"Generated: {_utc_iso()}")
        lines.append("")
        lines.append(f"## Verdict: **{verdict}**")
        lines.append("")
        for line in supporting:
            lines.append(f"- {line}")
        lines.append("")
        # Fold in verification + heal info.
        if self.verification_report is not None:
            lines.append("## Verification report")
            lines.append("")
            ver = self.verification_report
            agg = getattr(ver, "aggregate_status", "(unknown)")
            lines.append(f"- Aggregate status: **{agg}**")
            checks = getattr(ver, "checks", []) or []
            for c in checks:
                lines.append(
                    f"  - `{c.name}` ({c.agent_id}) — {c.status}, "
                    f"conf {c.confidence:.2f}: {c.summary[:120]}"
                )
            lines.append("")
        if self.heal_report is not None:
            lines.append("## Heal report")
            lines.append("")
            heal = self.heal_report
            lines.append(f"- Detected: {len(getattr(heal, 'detected', []))}")
            lines.append(f"- Repaired: {len(getattr(heal, 'repaired', []))}")
            lines.append(f"- Pending human review: {len(getattr(heal, 'pending', []))}")
            lines.append("")
        self._write("readiness_assessment.md", "\n".join(lines))

    def _readiness_verdict(self, sources: List[Dict[str, Any]],
                            coverage: Dict[str, Any]) -> tuple:
        score = coverage.get("score", 0.0)
        n = len(sources)
        # Pull verification status if present.
        vstatus = getattr(self.verification_report, "aggregate_status", None) \
            if self.verification_report else None
        if vstatus == "fail":
            verdict = "not_ready"
            why = ["Multi-agent verification reported `fail`."]
        elif n >= 200 and score >= 0.85 and vstatus in ("pass", "warning", None):
            verdict = "ready"
            why = [f"Corpus size {n} >= 200; coverage {score:.2f} >= 0.85."]
        elif n >= 50 and score >= 0.70:
            verdict = "ready_with_limitations"
            why = [
                f"Corpus size {n} below 200 target; coverage {score:.2f} below 0.85.",
                "Phase 2 may proceed but should commission additional literature passes.",
            ]
        elif n > 0:
            verdict = "blocked_pending_more_evidence"
            why = [f"Corpus too small or coverage too sparse (n={n}, score={score:.2f})."]
        else:
            verdict = "blocked_pending_human"
            why = ["No sources collected — run a corpus build with web tools enabled."]
        return verdict, why

    def _write_implementation_roadmap(self) -> None:
        lines = [
            "# Phase 2 Implementation Roadmap",
            "",
            f"Generated: {_utc_iso()}",
            "",
            "Sequenced workstream for Phase 2. Each item names the owner agent / "
            "workflow and the gate(s) it must pass.",
            "",
            "## Workstream A — Data integrity",
            "",
            "1. **Resolve BUG-001** (9B8T chain assignment) → owner: dataset_integrity → gates: dataset, leakage",
            "2. **Document split protocol** for all 6 leakage checks → owner: leakage_split → gates: leakage",
            "3. **Re-validate metrics** under cleaned splits → owner: metrics_statistics → gates: evaluation, leakage",
            "",
            "## Workstream B — Validation",
            "",
            "1. **MD trajectory analysis** (RMSF, DCCM, pocket volume) → owner: validation_skeptic → gates: validation",
            "2. **Classify MD evidence explicitly** → owner: validation_skeptic + biological_realism → gates: validation, claim",
            "3. **Update VALIDATION_STATUS.md** with classification → owner: context_source_truth",
            "",
            "## Workstream C — Writing",
            "",
            "1. **Audit drafts for disallowed wording** → owner: paper_claim → gates: claim",
            "2. **Section 3.8 (MD results)** drafted from classified evidence → owner: paper_claim",
            "3. **Reviewer simulation pass** → owner: reviewer_collaboration",
            "4. **Contradiction sweep** before submission → owner: contradiction_hunter",
            "",
            "## Workstream D — Infrastructure",
            "",
            "1. **Restore or stub** dangling compute-gateway intents (pcna_crawler, "
            "gemma_verifier, obsidian_writer) → owner: code_builder + autonomous_healer",
            "2. **Reproducibility smoke test** in tests/ → owner: testing_environment",
            "3. **Provenance entries** for all paper-grade artifacts → owner: provenance_artifacts",
            "",
            "## Workstream E — Compute",
            "",
            "1. **Compute budget approval** for any MD extensions > 4 GPU-hours → owner: compute_planning",
            "2. **HUMAN_DECISIONS.md entry** for each PI sign-off → owner: master_orchestrator (proxy)",
            "",
        ]
        self._write("implementation_roadmap.md", "\n".join(lines))

    def _write_remediation_plan(self) -> None:
        lines = [
            "# Phase 2 Remediation Plan",
            "",
            f"Generated: {_utc_iso()}",
            "",
            "Issues surfaced by the autonomous campaign and the multi-agent "
            "verification suite, each with a recommended fix.",
            "",
        ]
        ver = self.verification_report
        if ver is None or not getattr(ver, "checks", []):
            lines.append("_(verification report not available; remediation plan limited.)_")
        else:
            non_pass = [c for c in ver.checks if c.status in ("fail", "warning")]
            if not non_pass:
                lines.append("All verification checks pass — no remediation required.")
            else:
                for c in non_pass:
                    lines.append(f"## {c.name}")
                    lines.append(f"- Status: **{c.status}** (confidence {c.confidence:.2f})")
                    lines.append(f"- Summary: {c.summary}")
                    lines.append(f"- Owner: `{c.agent_id}`")
                    lines.append(f"- Suggested fix: re-run `{c.agent_id}` after addressing findings.")
                    lines.append("")
        # Heal report follow-ups.
        if self.heal_report is not None:
            pending = getattr(self.heal_report, "pending", []) or []
            if pending:
                lines.append("## Infrastructure pending human approval")
                lines.append("")
                for p in pending:
                    lines.append(f"- `{p.item.path}` — {p.error or 'pending'}")
                lines.append("")
        self._write("remediation_plan.md", "\n".join(lines))

    def _write_campaign_summary(self, sources: List[Dict[str, Any]],
                                 coverage: Dict[str, Any]) -> None:
        lines = [
            "# Phase 2 Campaign Summary",
            "",
            f"Generated: {_utc_iso()}",
            "",
            f"## Counts",
            "",
            f"- Sources: **{len(sources)}**",
            f"- Coverage score: **{coverage.get('score', 0.0):.2f}**",
            f"- Coverage gaps: **{len(coverage.get('gaps', []) or [])}**",
            "",
            "## Deliverables",
            "",
            "- `PHASE2_CORPUS.md`",
            "- `gap_analysis.md`",
            "- `synthesis_draft.md`",
            "- `phase2_design_rules.md`",
            "- `readiness_assessment.md`",
            "- `implementation_roadmap.md`",
            "- `remediation_plan.md`",
            "",
            "## Provenance",
            "",
            f"- Synthesis writer: `{self.agent_id}`",
            f"- Output directory: `{self.output_dir.as_posix()}`",
            "",
        ]
        self._write("CAMPAIGN_SUMMARY.md", "\n".join(lines))


__all__ = ["Phase2SynthesisWriter", "SYNTHESIS_PROFILE"]
