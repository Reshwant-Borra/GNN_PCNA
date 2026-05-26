"""GNN-PCNA Phase 2 autonomous research-and-engineering campaign.

End-to-end demonstration of the full ResearchOS autonomous stack:

1. **Self-healing infrastructure** — detect dangling modules / missing
   memory files; scaffold safe placeholders in smoke mode, defer to a
   human in live mode unless ``heal_dry_run=False`` is passed.
2. **Plan campaign** — decompose the top-level goal into corpus +
   ingestion + verification + synthesis sub-goals via the default
   decomposer (template-based; falls back deterministically when no
   LLM is available).
3. **Research 200+ sources** — in ``smoke`` mode, seed the source
   registry with a coverage-balanced stub bank; in ``live`` mode, the
   ``AutonomousLiteratureWebAgent`` queries PubMed + arXiv.
4. **Ingest** — the ``AutonomousDocumentIngestionAgent`` walks the
   repo's ``data/`` and ``research/`` dirs and registers new sources.
5. **Multi-agent scientific verification** — 10 canonical checks run
   through the existing scientific orchestrator (dataset_integrity,
   leakage_split, scientific_code_review, biological_realism,
   paper_claim, validation_skeptic, metrics_statistics,
   testing_environment + provenance_artifacts, contradiction_hunter,
   literature_web).
6. **Critic → planner feedback** — failing checks spawn follow-up
   handoff steps surfaced on the ``CampaignResult``.
7. **Synthesis** — the ``Phase2SynthesisWriter`` composes the canonical
   deliverables into ``research_corpus/``: corpus index, gap analysis,
   synthesis draft, Phase 2 design rules, readiness assessment,
   implementation roadmap, remediation plan, campaign summary.

Both ``smoke`` and ``live`` modes are safe by default — no scientific
model code is modified, no MD is run, no claims are upgraded above
``moderately_supported`` without human approval.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from research_os.agents.base import AgentContext
from research_os.autonomous import AUTONOMOUS_AGENTS
from research_os.autonomous.agents.literature_web import _PCNA_COVERAGE_CATEGORIES
from research_os.autonomous.campaigns.stubs import seed_source_registry, stub_sources
from research_os.autonomous.campaigns.synthesis import Phase2SynthesisWriter
from research_os.autonomous.controller import AutonomousController, CampaignResult
from research_os.autonomous.coverage import CoverageEstimator
from research_os.autonomous.schemas import Budget, Goal


PHASE2_GOAL_OBJECTIVE = (
    "Build a Phase 2 readiness corpus for GNN-PCNA, run multi-agent "
    "scientific verification, and produce structured artifacts for "
    "the implementation roadmap and readiness assessment."
)


@dataclass
class Phase2CampaignReport:
    """User-facing summary of one Phase 2 campaign run."""
    mode: str                                # "smoke" | "live"
    campaign_result: CampaignResult
    seeded_source_count: int = 0
    synthesis_paths: List[str] = field(default_factory=list)
    output_dir: Optional[str] = None

    @property
    def aggregate_status(self) -> str:
        return self.campaign_result.aggregate_status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "aggregate_status": self.aggregate_status,
            "seeded_source_count": self.seeded_source_count,
            "synthesis_paths": list(self.synthesis_paths),
            "output_dir": self.output_dir,
            "campaign": self.campaign_result.to_dict(),
        }


def run_phase2_pcna(
    repo_root: "str | Path" = ".",
    *,
    mode: str = "smoke",
    output_dir_name: str = "research_corpus",
    heal_dry_run: Optional[bool] = None,
    budget: Optional[Budget] = None,
) -> Phase2CampaignReport:
    """Execute the Phase 2 PCNA campaign and produce all deliverables.

    Arguments:
        repo_root: Project directory (must contain ``research_os_memory``
            and ``research_os_registries`` or they will be bootstrapped).
        mode: ``"smoke"`` (default) seeds stub sources + ``heal_dry_run=True``.
            ``"live"`` does no seeding and defaults ``heal_dry_run=False``
            so the healer actually writes placeholder modules.
        output_dir_name: Subdirectory under ``repo_root`` to write
            deliverables. Defaults to ``research_corpus``.
        heal_dry_run: Override the mode-derived default.
        budget: Optional explicit ``Budget`` for the campaign.

    Returns:
        ``Phase2CampaignReport`` with the campaign aggregate status and
        the list of synthesis files written.
    """
    if mode not in ("smoke", "live"):
        raise ValueError(f"mode must be 'smoke' or 'live'; got {mode!r}")

    root = Path(repo_root).resolve()
    if heal_dry_run is None:
        heal_dry_run = (mode == "smoke")

    # Bootstrap stores via the scientific orchestrator so memory + registries
    # exist before the campaign runs.
    from research_os.orchestrator import Orchestrator
    orch = Orchestrator(
        repo_root=root,
        memory_dir=root / "research_os_memory",
        registries_dir=root / "research_os_registries",
        reports_dir=root / "reports" / "research_os",
    )
    orch.bootstrap()

    ctx = AgentContext(
        repo_root=root,
        memory_store=orch.memory_store,
        registry_store=orch.registry_store,
        reports_root=orch.reports_dir,
    )

    seeded = 0
    if mode == "smoke":
        seeded = seed_source_registry(orch.registry_store, stub_sources())

    estimator = CoverageEstimator(_PCNA_COVERAGE_CATEGORIES)

    # Build factories: include all autonomous agents PLUS the synthesis
    # writer (parameterized with the estimator + later set with the
    # verification report once the campaign produces one).
    factories = dict(AUTONOMOUS_AGENTS)

    # Closure variables so the synthesis-writer factory can pick up the
    # verification report after it runs.
    state: Dict[str, Any] = {"verification_report": None, "heal_report": None}

    def _synthesis_factory(c: AgentContext) -> Phase2SynthesisWriter:
        return Phase2SynthesisWriter(
            c,
            coverage_estimator=estimator,
            verification_report=state.get("verification_report"),
            heal_report=state.get("heal_report"),
            output_dir_name=output_dir_name,
        )

    factories["__synthesis_writer__"] = _synthesis_factory

    controller = AutonomousController(
        ctx,
        agent_factories=factories,
        workflow_id="phase2_pcna",
    )

    top_goal = Goal(
        objective=PHASE2_GOAL_OBJECTIVE,
        rationale="Phase 7 end-to-end autonomous campaign demonstration.",
        budget=budget or Budget(max_iterations=40, max_tool_calls=120,
                                  max_failures=10, max_seconds=300.0),
    )

    # Run heal first, capture the report, then dispatch the campaign with
    # heal_first=False (because we've already done it) so the heal_report
    # is the one we captured.
    from research_os.autonomous.healer import InfrastructureHealer
    healer = InfrastructureHealer(root)
    state["heal_report"] = healer.heal_all(dry_run=heal_dry_run)

    # The controller runs decomposition + verification. We want the
    # synthesis writer to receive the verification report, so we run the
    # campaign in two passes when needed: first a verification pass,
    # then a synthesis pass with the verification report wired in.

    # Pass 1: full decomposition (literature → ingest → coverage → verify)
    # without synthesis, so we capture the verification report.
    pass1 = controller.pursue_goal(
        Goal(
            objective="Phase 2 corpus + verification only (synthesis split out).",
            rationale="Pre-synthesis pass — capture verification report.",
            budget=top_goal.budget,
            parent_goal_id=top_goal.goal_id,
        ),
        sub_goals=[
            Goal(objective="Literature sweep + ingest", inputs={"target_agent": "literature_web"},
                 budget=top_goal.budget, parent_goal_id=top_goal.goal_id),
            Goal(objective="Ingest discovered documents", inputs={"target_agent": "document_knowledge_ingestion"},
                 budget=top_goal.budget, parent_goal_id=top_goal.goal_id),
            Goal(objective="Verify", inputs={"target_agent": "__verification_suite__"},
                 budget=top_goal.budget, parent_goal_id=top_goal.goal_id),
        ],
        run_verification=False,  # we already include it explicitly
    )
    if pass1.verification_reports:
        state["verification_report"] = pass1.verification_reports[0]

    # Pass 2: synthesis only, now that verification_report is wired in.
    pass2 = controller.pursue_goal(
        top_goal,
        sub_goals=[
            Goal(objective="Synthesize Phase 2 deliverables.",
                 inputs={"target_agent": "__synthesis_writer__"},
                 budget=top_goal.budget,
                 parent_goal_id=top_goal.goal_id),
        ],
        run_verification=False,
    )

    # Merge results into a single CampaignResult-like object so callers
    # get one report. We treat pass1 as the canonical campaign result and
    # append pass2's sub_outcomes for visibility.
    pass1.sub_outcomes.extend(pass2.sub_outcomes)
    pass1.summary = (
        f"Phase 2 campaign: {len(pass1.sub_outcomes)} sub-goals "
        f"(pass1 {len(pass1.sub_outcomes) - len(pass2.sub_outcomes)} + pass2 {len(pass2.sub_outcomes)}). "
        f"{pass1.summary}"
    )
    # Recompute aggregate after merge.
    if pass1.failed_count > 0:
        pass1.aggregate_status = "fail"
    elif pass1.succeeded_count == 0:
        pass1.aggregate_status = "fail"
    elif pass1.skipped_count > 0:
        pass1.aggregate_status = "warning"
    pass1.heal_report = state["heal_report"]

    # Collect written paths.
    synth_outcome = next(
        (o for o in pass1.sub_outcomes if o.agent_id == "__synthesis_writer__"),
        None,
    )
    written: List[str] = []
    if synth_outcome and synth_outcome.output is not None:
        notes = synth_outcome.output.machine_readable_notes or {}
        written = list(notes.get("written_paths", []))
        # Fall back to glob if notes weren't surfaced.
        if not written:
            out_dir = root / output_dir_name
            if out_dir.exists():
                written = [str(p) for p in sorted(out_dir.glob("*.md"))]

    report = Phase2CampaignReport(
        mode=mode,
        campaign_result=pass1,
        seeded_source_count=seeded,
        synthesis_paths=written,
        output_dir=str((root / output_dir_name).as_posix()),
    )
    return report


__all__ = ["PHASE2_GOAL_OBJECTIVE", "Phase2CampaignReport", "run_phase2_pcna"]
