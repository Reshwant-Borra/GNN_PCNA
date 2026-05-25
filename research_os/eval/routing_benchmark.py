"""Hand-curated routing benchmark for ResearchOS.

Each ``BenchmarkCase`` is one representative prompt with the expected routing
behavior. The router is graded against this dataset by
``research_os.eval.routing_eval.evaluate``.

Field semantics (intentionally tight):

- ``expected_agents``    — MUST all be in the selected_agents output.
                           ``context_source_truth`` is implicitly required for
                           every case and need not be listed here, but listing
                           it is fine.
- ``optional_agents``    — ALLOWED but not required. Selecting them does not
                           penalize the case.
- ``forbidden_agents``   — MUST NOT appear in selected_agents. Use sparingly:
                           only when including the agent would be clearly wrong
                           (e.g. ``code_builder`` for a literature query).
- ``expected_risk``      — Tuple of acceptable risk_level values.
- ``expected_human_review`` — True / False / None (None = either is acceptable).
- ``expected_claude_fallback`` — True / False / None.
- ``is_compound``        — True if the prompt mixes multiple intents.
- ``is_destructive``     — True if the prompt would mutate or release state
                           in a way that requires PI signoff.

When you add a case, prefer realistic prompts an actual user would send. The
goal is to evaluate the router, not to optimize for any single example.

Coverage as of 2026-05-25: 20 categories, ~70 cases. ``collaboration_sync`` is
intentionally out of scope this phase.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple


_RISK_ANY = ("low", "medium", "high", "critical")
_RISK_LOW_MED = ("low", "medium")
_RISK_MED = ("medium",)
_RISK_MED_HIGH = ("medium", "high")
_RISK_HIGH = ("high",)
_RISK_HIGH_CRIT = ("high", "critical")
_RISK_CRIT = ("critical",)


@dataclass(frozen=True)
class BenchmarkCase:
    id: str
    category: str
    prompt: str
    expected_agents: Tuple[str, ...] = ()
    optional_agents: Tuple[str, ...] = ()
    forbidden_agents: Tuple[str, ...] = ()
    expected_risk: Tuple[str, ...] = _RISK_ANY
    expected_human_review: Optional[bool] = None
    expected_claude_fallback: Optional[bool] = None
    is_compound: bool = False
    is_destructive: bool = False
    notes: str = ""


# Common forbids for non-overlapping domains.
_FORBID_FOR_LITERATURE = ("model_training", "code_builder", "validation_skeptic")
_FORBID_FOR_STATUS = ("code_builder", "model_training", "paper_claim")
_FORBID_FOR_FIGURE = ("validation_skeptic", "leakage_split")
_FORBID_FOR_CODE = ("paper_claim", "visual_evidence")


CASES: Tuple[BenchmarkCase, ...] = (

    # ── literature ──────────────────────────────────────────────────────
    BenchmarkCase(
        id="lit-001",
        category="literature",
        prompt="Research how Graph Neural Networks work and find PubMed articles on this topic",
        expected_agents=("context_source_truth", "literature_web", "document_knowledge_ingestion"),
        optional_agents=("provenance_artifacts",),
        forbidden_agents=_FORBID_FOR_LITERATURE,
        expected_risk=_RISK_LOW_MED,
    ),
    BenchmarkCase(
        id="lit-002",
        category="literature",
        prompt="What's the recent literature on cryptic pockets?",
        expected_agents=("context_source_truth", "literature_web"),
        optional_agents=("document_knowledge_ingestion", "biological_realism"),
        forbidden_agents=_FORBID_FOR_LITERATURE,
    ),
    BenchmarkCase(
        id="lit-003",
        category="literature",
        prompt="Survey GNN architectures used in biology",
        expected_agents=("context_source_truth", "literature_web"),
        optional_agents=("document_knowledge_ingestion",),
        forbidden_agents=("model_training", "code_builder"),
    ),
    BenchmarkCase(
        id="lit-004",
        category="literature",
        prompt="Pull citations for our preprocessing approach",
        expected_agents=("context_source_truth", "literature_web"),
        optional_agents=("document_knowledge_ingestion", "preprocessing_auditor"),
    ),
    BenchmarkCase(
        id="lit-005",
        category="literature",
        prompt="Find a recent benchmark paper for protein-ligand binding site prediction",
        expected_agents=("context_source_truth", "literature_web"),
        optional_agents=("document_knowledge_ingestion", "metrics_statistics"),
        forbidden_agents=("model_training",),
    ),

    # ── document ingestion ──────────────────────────────────────────────
    BenchmarkCase(
        id="ing-001",
        category="document_ingestion",
        prompt="Ingest this PDF: arxiv_2403_12345.pdf",
        expected_agents=("context_source_truth", "document_knowledge_ingestion"),
        optional_agents=("literature_web", "provenance_artifacts"),
        forbidden_agents=("model_training",),
    ),
    BenchmarkCase(
        id="ing-002",
        category="document_ingestion",
        prompt="Add the new lab notebook transcripts to the source registry",
        expected_agents=("context_source_truth", "document_knowledge_ingestion"),
        optional_agents=("provenance_artifacts",),
    ),
    BenchmarkCase(
        id="ing-003",
        category="document_ingestion",
        prompt="Index the AOH1996 paper",
        expected_agents=("context_source_truth", "document_knowledge_ingestion"),
        optional_agents=("literature_web",),
    ),

    # ── data leakage ────────────────────────────────────────────────────
    BenchmarkCase(
        id="leak-001",
        category="data_leakage",
        prompt="Check the train/test split for homology leakage",
        expected_agents=("context_source_truth", "leakage_split"),
        optional_agents=("dataset_integrity", "preprocessing_auditor"),
        forbidden_agents=("paper_claim", "visual_evidence"),
        expected_risk=_RISK_HIGH_CRIT,
    ),
    BenchmarkCase(
        id="leak-002",
        category="data_leakage",
        prompt="Did we apo/holo leak the binding-site features?",
        expected_agents=("context_source_truth", "leakage_split"),
        optional_agents=("preprocessing_auditor", "dataset_integrity"),
        expected_risk=_RISK_HIGH_CRIT,
    ),
    BenchmarkCase(
        id="leak-003",
        category="data_leakage",
        prompt="Audit cross-validation for chain-level leakage",
        expected_agents=("context_source_truth", "leakage_split"),
        optional_agents=("dataset_integrity", "metrics_statistics"),
        expected_risk=_RISK_HIGH_CRIT,
    ),
    BenchmarkCase(
        id="leak-004",
        category="data_leakage",
        prompt="Is there any train-test overlap in our PCNA dataset?",
        expected_agents=("context_source_truth", "leakage_split", "dataset_integrity"),
        expected_risk=_RISK_HIGH_CRIT,
    ),

    # ── dataset audit ───────────────────────────────────────────────────
    BenchmarkCase(
        id="data-001",
        category="dataset_audit",
        prompt="Audit our PDB dataset",
        expected_agents=("context_source_truth", "dataset_integrity"),
        optional_agents=("preprocessing_auditor", "leakage_split"),
        forbidden_agents=("paper_claim", "visual_evidence"),
    ),
    BenchmarkCase(
        id="data-002",
        category="dataset_audit",
        prompt="What's the label definition for our positives?",
        expected_agents=("context_source_truth", "dataset_integrity"),
    ),
    BenchmarkCase(
        id="data-003",
        category="dataset_audit",
        prompt="Review the negative sampling strategy in the dataset",
        expected_agents=("context_source_truth", "dataset_integrity"),
        optional_agents=("leakage_split",),
    ),

    # ── preprocessing audit ─────────────────────────────────────────────
    BenchmarkCase(
        id="pre-001",
        category="preprocessing_audit",
        prompt="Audit the graph construction pipeline",
        expected_agents=("context_source_truth", "preprocessing_auditor"),
        optional_agents=("scientific_code_review", "dataset_integrity"),
    ),
    BenchmarkCase(
        id="pre-002",
        category="preprocessing_audit",
        prompt="Are we normalizing residue features correctly?",
        expected_agents=("context_source_truth", "preprocessing_auditor"),
        optional_agents=("scientific_code_review", "dataset_integrity"),
    ),
    BenchmarkCase(
        id="pre-003",
        category="preprocessing_audit",
        prompt="Check residue-to-PDB chain mapping in preprocessing",
        expected_agents=("context_source_truth", "preprocessing_auditor"),
        optional_agents=("dataset_integrity",),
    ),

    # ── code review ─────────────────────────────────────────────────────
    BenchmarkCase(
        id="code-001",
        category="code_review",
        prompt="Review the evaluation script for correctness",
        expected_agents=("context_source_truth", "scientific_code_review"),
        optional_agents=("testing_environment",),
        forbidden_agents=_FORBID_FOR_CODE,
    ),
    BenchmarkCase(
        id="code-002",
        category="code_review",
        prompt="Audit the training-loop code",
        expected_agents=("context_source_truth", "scientific_code_review"),
        optional_agents=("testing_environment", "model_training"),
    ),
    BenchmarkCase(
        id="code-003",
        category="code_review",
        prompt="Check the loss function implementation",
        expected_agents=("context_source_truth", "scientific_code_review"),
        forbidden_agents=_FORBID_FOR_CODE,
    ),

    # ── testing / environment ───────────────────────────────────────────
    BenchmarkCase(
        id="test-001",
        category="testing_environment",
        prompt="Is the most recent run reproducible?",
        expected_agents=("context_source_truth", "testing_environment"),
        optional_agents=("provenance_artifacts",),
    ),
    BenchmarkCase(
        id="test-002",
        category="testing_environment",
        prompt="Check the conda environment lock for missing pins",
        expected_agents=("context_source_truth", "testing_environment"),
    ),
    BenchmarkCase(
        id="test-003",
        category="testing_environment",
        prompt="Did all the pytest tests pass after the last refactor?",
        expected_agents=("context_source_truth", "testing_environment"),
        optional_agents=("scientific_code_review",),
    ),

    # ── model training ──────────────────────────────────────────────────
    BenchmarkCase(
        id="train-001",
        category="model_training",
        prompt="Train the model for 50 epochs with early stopping",
        expected_agents=("context_source_truth", "model_training", "leakage_split"),
        optional_agents=("dataset_integrity", "preprocessing_auditor", "metrics_statistics", "provenance_artifacts"),
        expected_risk=_RISK_HIGH_CRIT,
    ),
    BenchmarkCase(
        id="train-002",
        category="model_training",
        prompt="Fine-tune from the latest checkpoint",
        expected_agents=("context_source_truth", "model_training"),
        optional_agents=("provenance_artifacts", "leakage_split"),
        expected_risk=_RISK_MED_HIGH,
    ),
    BenchmarkCase(
        id="train-003",
        category="model_training",
        prompt="Show me the training history for the v3 checkpoint",
        expected_agents=("context_source_truth",),
        optional_agents=("model_training", "provenance_artifacts"),
        expected_risk=_RISK_LOW_MED,
    ),

    # ── metric verification ─────────────────────────────────────────────
    BenchmarkCase(
        id="metric-001",
        category="metric_verification",
        prompt="Verify the headline AUROC",
        expected_agents=("context_source_truth", "metrics_statistics", "leakage_split"),
        optional_agents=("contradiction_hunter", "provenance_artifacts"),
        expected_risk=_RISK_HIGH_CRIT,
    ),
    BenchmarkCase(
        id="metric-002",
        category="metric_verification",
        prompt="Compute AUPRC with bootstrap confidence intervals",
        expected_agents=("context_source_truth", "metrics_statistics"),
        optional_agents=("leakage_split", "contradiction_hunter"),
    ),
    BenchmarkCase(
        id="metric-003",
        category="metric_verification",
        prompt="Do the precision and recall numbers hold up under the new split?",
        expected_agents=("context_source_truth", "metrics_statistics"),
        optional_agents=("leakage_split", "contradiction_hunter"),
    ),

    # ── statistical analysis ────────────────────────────────────────────
    BenchmarkCase(
        id="stat-001",
        category="statistical_analysis",
        prompt="Run bootstrap CIs on the headline metrics",
        expected_agents=("context_source_truth", "metrics_statistics"),
    ),
    BenchmarkCase(
        id="stat-002",
        category="statistical_analysis",
        prompt="Statistical comparison between our model and the baselines",
        expected_agents=("context_source_truth", "metrics_statistics"),
        optional_agents=("model_training", "contradiction_hunter"),
    ),

    # ── compute planning ────────────────────────────────────────────────
    BenchmarkCase(
        id="comp-001",
        category="compute_planning",
        prompt="Plan a 100ns MD run on the GPU cluster",
        expected_agents=("context_source_truth", "compute_planning"),
        optional_agents=("validation_skeptic",),
        expected_risk=_RISK_HIGH_CRIT,
        expected_human_review=True,
    ),
    BenchmarkCase(
        id="comp-002",
        category="compute_planning",
        prompt="How much GPU time will retraining take?",
        expected_agents=("context_source_truth", "compute_planning"),
        expected_risk=_RISK_MED_HIGH,
    ),
    BenchmarkCase(
        id="comp-003",
        category="compute_planning",
        prompt="Budget cloud compute for 5 MD trajectories at 200ns each",
        expected_agents=("context_source_truth", "compute_planning"),
        optional_agents=("validation_skeptic",),
        expected_risk=_RISK_HIGH_CRIT,
        expected_human_review=True,
    ),

    # ── MD validation ───────────────────────────────────────────────────
    BenchmarkCase(
        id="md-001",
        category="md_validation",
        prompt="Did MD validate the cryptic pocket?",
        expected_agents=("context_source_truth", "validation_skeptic", "biological_realism", "paper_claim", "contradiction_hunter"),
        optional_agents=("metrics_statistics", "provenance_artifacts"),
        forbidden_agents=("code_builder",),
        expected_risk=_RISK_CRIT,
        expected_human_review=True,
        expected_claude_fallback=True,
    ),
    BenchmarkCase(
        id="md-002",
        category="md_validation",
        prompt="Interpret the RMSF trajectories from last week's run",
        expected_agents=("context_source_truth", "validation_skeptic", "biological_realism"),
        optional_agents=("metrics_statistics", "provenance_artifacts"),
        expected_risk=_RISK_HIGH_CRIT,
    ),
    BenchmarkCase(
        id="md-003",
        category="md_validation",
        prompt="Does the MD support pocket opening under the tested conditions?",
        expected_agents=("context_source_truth", "validation_skeptic", "biological_realism"),
        optional_agents=("paper_claim", "contradiction_hunter", "metrics_statistics"),
        expected_risk=_RISK_HIGH_CRIT,
    ),
    BenchmarkCase(
        id="md-004",
        category="md_validation",
        prompt="Run DCCM analysis on the trajectories",
        expected_agents=("context_source_truth", "validation_skeptic"),
        optional_agents=("biological_realism", "metrics_statistics"),
    ),

    # ── biological realism ──────────────────────────────────────────────
    BenchmarkCase(
        id="bio-001",
        category="biological_realism",
        prompt="Is this predicted pocket region biologically plausible?",
        expected_agents=("context_source_truth", "biological_realism"),
        optional_agents=("validation_skeptic",),
    ),
    BenchmarkCase(
        id="bio-002",
        category="biological_realism",
        prompt="Are the predicted residues near known AOH1996 contacts?",
        expected_agents=("context_source_truth", "biological_realism"),
        optional_agents=("validation_skeptic",),
    ),

    # ── contradiction detection ─────────────────────────────────────────
    BenchmarkCase(
        id="con-001",
        category="contradiction_detection",
        prompt="Find contradictions in our claims",
        expected_agents=("context_source_truth", "contradiction_hunter"),
        optional_agents=("paper_claim", "metrics_statistics", "leakage_split"),
    ),
    BenchmarkCase(
        id="con-002",
        category="contradiction_detection",
        prompt="Look for hidden conflicts between the metrics and the MD evidence",
        expected_agents=("context_source_truth", "contradiction_hunter"),
        optional_agents=("metrics_statistics", "validation_skeptic"),
    ),
    BenchmarkCase(
        id="con-003",
        category="contradiction_detection",
        prompt="Sanity check the whole project before submission",
        expected_agents=("context_source_truth", "contradiction_hunter"),
        optional_agents=("paper_claim", "validation_skeptic", "biological_realism", "leakage_split", "metrics_statistics", "provenance_artifacts", "visual_evidence"),
        is_compound=True,
    ),

    # ── artifact provenance ─────────────────────────────────────────────
    BenchmarkCase(
        id="prov-001",
        category="artifact_provenance",
        prompt="Is checkpoint v3 stale?",
        expected_agents=("context_source_truth", "provenance_artifacts"),
    ),
    BenchmarkCase(
        id="prov-002",
        category="artifact_provenance",
        prompt="Verify the artifact provenance chain for figure 2",
        expected_agents=("context_source_truth", "provenance_artifacts"),
        optional_agents=("visual_evidence",),
    ),
    BenchmarkCase(
        id="prov-003",
        category="artifact_provenance",
        prompt="Which artifacts need to be regenerated after the leakage fix?",
        expected_agents=("context_source_truth", "provenance_artifacts"),
        optional_agents=("leakage_split",),
        expected_risk=_RISK_HIGH_CRIT,
    ),

    # ── claim audit ─────────────────────────────────────────────────────
    BenchmarkCase(
        id="claim-001",
        category="claim_audit",
        prompt="Can we say MD validated the cryptic pocket?",
        expected_agents=("context_source_truth", "paper_claim", "validation_skeptic", "biological_realism", "contradiction_hunter"),
        optional_agents=("metrics_statistics", "provenance_artifacts"),
        expected_risk=_RISK_CRIT,
        expected_human_review=True,
        expected_claude_fallback=True,
    ),
    BenchmarkCase(
        id="claim-002",
        category="claim_audit",
        prompt="Audit current claims in CURRENT_CLAIMS.md",
        expected_agents=("context_source_truth", "paper_claim", "contradiction_hunter"),
        optional_agents=("metrics_statistics", "biological_realism", "validation_skeptic"),
        expected_risk=_RISK_HIGH_CRIT,
    ),
    BenchmarkCase(
        id="claim-003",
        category="claim_audit",
        prompt="Is this claim safe to publish?",
        expected_agents=("context_source_truth", "paper_claim", "contradiction_hunter"),
        optional_agents=("biological_realism", "validation_skeptic"),
        expected_risk=_RISK_HIGH_CRIT,
        expected_human_review=True,
        expected_claude_fallback=True,
    ),

    # ── paper writing ───────────────────────────────────────────────────
    BenchmarkCase(
        id="paper-001",
        category="paper_writing",
        prompt="Write the results section of the manuscript",
        expected_agents=("context_source_truth", "paper_claim"),
        optional_agents=("metrics_statistics", "visual_evidence", "contradiction_hunter"),
        expected_risk=_RISK_HIGH_CRIT,
    ),
    BenchmarkCase(
        id="paper-002",
        category="paper_writing",
        prompt="Draft the abstract for the PCNA paper",
        expected_agents=("context_source_truth", "paper_claim"),
        optional_agents=("biological_realism", "validation_skeptic", "contradiction_hunter"),
        expected_risk=_RISK_HIGH_CRIT,
    ),
    BenchmarkCase(
        id="paper-003",
        category="paper_writing",
        prompt="Audit the manuscript for disallowed wording",
        expected_agents=("context_source_truth", "paper_claim"),
        optional_agents=("biological_realism", "contradiction_hunter"),
    ),

    # ── figure generation ───────────────────────────────────────────────
    BenchmarkCase(
        id="fig-001",
        category="figure_generation",
        prompt="Generate Figure 3 with bootstrap confidence intervals",
        expected_agents=("context_source_truth", "visual_evidence"),
        optional_agents=("metrics_statistics", "paper_claim", "provenance_artifacts"),
        forbidden_agents=_FORBID_FOR_FIGURE,
    ),
    BenchmarkCase(
        id="fig-002",
        category="figure_generation",
        prompt="Audit the figures for misleading axes or cropped data",
        expected_agents=("context_source_truth", "visual_evidence"),
        optional_agents=("paper_claim",),
    ),
    BenchmarkCase(
        id="fig-003",
        category="figure_generation",
        prompt="Regenerate the heatmap for the per-residue scores",
        expected_agents=("context_source_truth", "visual_evidence"),
        optional_agents=("metrics_statistics", "provenance_artifacts"),
    ),

    # ── reviewer simulation ─────────────────────────────────────────────
    BenchmarkCase(
        id="rev-001",
        category="reviewer_simulation",
        prompt="What questions will reviewers ask about leakage?",
        expected_agents=("context_source_truth", "reviewer_collaboration"),
        optional_agents=("leakage_split", "paper_claim"),
    ),
    BenchmarkCase(
        id="rev-002",
        category="reviewer_simulation",
        prompt="Simulate reviewer concerns about the MD evidence",
        expected_agents=("context_source_truth", "reviewer_collaboration"),
        optional_agents=("validation_skeptic", "biological_realism"),
    ),

    # ── dashboard / status / debug ──────────────────────────────────────
    BenchmarkCase(
        id="stat-001b",
        category="dashboard_status_debug",
        prompt="What's the latest checkpoint?",
        expected_agents=("context_source_truth",),
        optional_agents=("model_training", "provenance_artifacts"),
        forbidden_agents=_FORBID_FOR_STATUS,
        expected_risk=_RISK_LOW_MED,
    ),
    BenchmarkCase(
        id="stat-002b",
        category="dashboard_status_debug",
        prompt="Show me the current project status",
        expected_agents=("context_source_truth",),
        optional_agents=("provenance_artifacts",),
        forbidden_agents=("code_builder", "model_training"),
        expected_risk=_RISK_LOW_MED,
    ),
    BenchmarkCase(
        id="stat-003b",
        category="dashboard_status_debug",
        prompt="Why did the last training run fail?",
        expected_agents=("context_source_truth", "provenance_artifacts"),
        optional_agents=("contradiction_hunter", "testing_environment", "scientific_code_review"),
    ),
    BenchmarkCase(
        id="stat-004b",
        category="dashboard_status_debug",
        prompt="What blockers are open right now?",
        expected_agents=("context_source_truth",),
        optional_agents=("contradiction_hunter", "provenance_artifacts"),
        expected_risk=_RISK_LOW_MED,
    ),

    # ── ambiguous compound ──────────────────────────────────────────────
    BenchmarkCase(
        id="comp-c001",
        category="compound_ambiguous",
        prompt="Train the model and verify the metrics",
        expected_agents=("context_source_truth", "model_training", "metrics_statistics"),
        optional_agents=("leakage_split", "dataset_integrity", "preprocessing_auditor", "provenance_artifacts", "contradiction_hunter"),
        is_compound=True,
        expected_risk=_RISK_HIGH_CRIT,
    ),
    BenchmarkCase(
        id="comp-c002",
        category="compound_ambiguous",
        prompt="Find papers on cryptic pockets and update the related work section",
        expected_agents=("context_source_truth", "literature_web", "paper_claim"),
        optional_agents=("document_knowledge_ingestion", "biological_realism", "contradiction_hunter"),
        is_compound=True,
    ),
    BenchmarkCase(
        id="comp-c003",
        category="compound_ambiguous",
        prompt="Audit the leakage and then check whether the AUROC is real",
        expected_agents=("context_source_truth", "leakage_split", "metrics_statistics"),
        optional_agents=("dataset_integrity", "preprocessing_auditor", "contradiction_hunter"),
        is_compound=True,
        expected_risk=_RISK_HIGH_CRIT,
    ),
    BenchmarkCase(
        id="comp-c004",
        category="compound_ambiguous",
        prompt="Write the discussion section based on the MD results",
        expected_agents=("context_source_truth", "paper_claim", "validation_skeptic"),
        optional_agents=("biological_realism", "contradiction_hunter", "metrics_statistics", "reviewer_collaboration"),
        is_compound=True,
        expected_risk=_RISK_HIGH_CRIT,
    ),
    BenchmarkCase(
        id="comp-c005",
        category="compound_ambiguous",
        prompt="Run the full claim audit before submission",
        expected_agents=("context_source_truth", "paper_claim", "contradiction_hunter"),
        optional_agents=("reviewer_collaboration", "validation_skeptic", "biological_realism", "visual_evidence", "provenance_artifacts", "metrics_statistics"),
        is_compound=True,
        expected_risk=_RISK_CRIT,
        expected_human_review=True,
    ),

    # ── destructive / dangerous ─────────────────────────────────────────
    BenchmarkCase(
        id="dest-001",
        category="destructive_dangerous",
        prompt="Delete the experiment registry and start over",
        expected_agents=("context_source_truth",),
        optional_agents=("provenance_artifacts", "contradiction_hunter", "reviewer_collaboration"),
        expected_risk=_RISK_CRIT,
        expected_human_review=True,
        expected_claude_fallback=True,
        is_destructive=True,
    ),
    BenchmarkCase(
        id="dest-002",
        category="destructive_dangerous",
        prompt="Submit the paper to Nature",
        expected_agents=("context_source_truth", "paper_claim"),
        optional_agents=("contradiction_hunter", "reviewer_collaboration", "visual_evidence", "validation_skeptic", "biological_realism", "provenance_artifacts", "metrics_statistics", "leakage_split", "preprocessing_auditor", "testing_environment"),
        expected_risk=_RISK_CRIT,
        expected_human_review=True,
        expected_claude_fallback=True,
        is_destructive=True,
    ),
    BenchmarkCase(
        id="dest-003",
        category="destructive_dangerous",
        prompt="Force-merge the new split into main",
        expected_agents=("context_source_truth",),
        optional_agents=("leakage_split", "dataset_integrity", "scientific_code_review"),
        expected_risk=_RISK_CRIT,
        expected_human_review=True,
        expected_claude_fallback=True,
        is_destructive=True,
    ),
)


def cases_by_category() -> dict:
    """Return cases grouped by category for per-category reporting."""
    out: dict = {}
    for case in CASES:
        out.setdefault(case.category, []).append(case)
    return out


def categories() -> Tuple[str, ...]:
    return tuple(sorted({c.category for c in CASES}))


__all__ = [
    "BenchmarkCase",
    "CASES",
    "cases_by_category",
    "categories",
]
