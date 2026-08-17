"""Declarative metadata for each figure: what it shows, which reviewer question
it answers, and an honest caption.

Captions follow project governance: validation-only, test set untouched, no
scientific claims, candidate-region language. ``render.py`` looks up these specs
so captions and provenance live in one place and the artifact registry can cite
the reviewer question each figure answers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class FigureSpec:
    figure_id: str
    title: str
    reviewer_question: str
    claim_support: str
    caption: str
    kind: str = "result"  # result | method | dataset
    data_sources: List[str] = field(default_factory=list)


# The 12 canonical reviewer questions live in ResearchOS
# (research_os/agents/communication.py::_REVIEWER_QUESTIONS). Each figure below
# is tied to the one it answers, so the figure set demonstrably addresses them.
FIGURE_SPECS: Dict[str, FigureSpec] = {
    "baseline_comparison": FigureSpec(
        figure_id="baseline_comparison",
        title="Validation macro-AUPRC across models and baselines",
        reviewer_question="Were baselines compared under the same leakage-clean split?",
        claim_support="The trained GNN separates candidate pocket residues better than "
        "naive and ablated baselines on held-out validation folds.",
        caption=(
            "Validation macro-AUPRC (mean of per-protein AUPRC) for the primary "
            "GraphSAGE-3L model and all baselines, evaluated on the same frozen, "
            "homology-blocked split (hash 24dd5e34). Error bars are ±1 SD over "
            "4 folds × 3 seeds where applicable. Random and degree references "
            "indicate the prevalence floor. Test set was not evaluated; these are "
            "validation, model-selection metrics only. No scientific claims are made."
        ),
        kind="result",
    ),
    "per_fold_performance": FigureSpec(
        figure_id="per_fold_performance",
        title="Per-fold validation macro-AUPRC",
        reviewer_question="How many independent test proteins?",
        claim_support="Performance is consistent across cross-validation folds, with "
        "fold 1 an easier validation partition.",
        caption=(
            "Per-fold validation macro-AUPRC for the primary model and GNN baselines "
            "(mean over 3 seeds). Fold-to-fold variation is modest; fold 1 is a more "
            "favorable partition across all models, indicating partition difficulty "
            "rather than seed luck. Validation only; the test set remains frozen."
        ),
        kind="result",
    ),
    "ablation_edges": FigureSpec(
        figure_id="ablation_edges",
        title="Edge-type ablation",
        reviewer_question="Are claims proportional to evidence?",
        claim_support="Spatial (Euclidean) edges carry most of the signal; sequential "
        "edges contribute little on validation folds.",
        caption=(
            "Ablation of graph edge types on validation macro-AUPRC. Removing spatial "
            "edges degrades performance; removing sequential edges does not, and "
            "marginally exceeds the full model (Δ +0.0021, within 1 SD). This is an "
            "honest ablation signal that the sequential-edge contribution is not "
            "established and warrants further investigation before any architecture "
            "claim. Validation only."
        ),
        kind="result",
    ),
    "training_curves": FigureSpec(
        figure_id="training_curves",
        title="Validation learning curves",
        reviewer_question="Were old checkpoints regenerated after bug fixes?",
        claim_support="Training converges with early stopping; no validation collapse.",
        caption=(
            "Validation macro-AUPRC versus epoch for all 12 primary-model runs "
            "(4 folds × 3 seeds; faint lines) with the across-run mean (bold). "
            "Early stopping (patience 10) halts each run near its validation peak, "
            "limiting overfitting. Curves are read directly from per-run training "
            "history manifests."
        ),
        kind="method",
    ),
    "metric_choice": FigureSpec(
        figure_id="metric_choice",
        title="Why macro-AUPRC, not AUROC, under class imbalance",
        reviewer_question="Where is AUPRC and what is the positive-class baseline?",
        claim_support="Under ~4.6% positive prevalence AUROC is inflated; AUPRC against "
        "the prevalence floor is the honest metric.",
        caption=(
            "Macro-AUPRC versus macro-AUROC for the primary model and naive baselines. "
            "At ~4.6% positive prevalence (dashed AUPRC floor), a random scorer reaches "
            "AUROC ≈ 0.50 but AUPRC ≈ 0.05; AUROC therefore overstates skill. "
            "macro-AUPRC against the prevalence baseline is reported as the primary "
            "metric for this reason. Validation only."
        ),
        kind="method",
    ),
    "dataset_split": FigureSpec(
        figure_id="dataset_split",
        title="Dataset composition and frozen split",
        reviewer_question="Is the test set independent at the protein level (not residue level)?",
        claim_support="The split is frozen, homology-blocked at 30% identity, with PCNA "
        "held out and the test set never loaded.",
        caption=(
            "Left: structure counts across the frozen cross-validation folds and the "
            "held-out test set (homology-blocked at 30% sequence identity; PCNA cluster "
            "held out entirely). Right: residue label composition (positive vs masked) "
            "under the positive-unlabeled policy. Split manifest hash 24dd5e34; the test "
            "set was never loaded during model selection."
        ),
        kind="dataset",
    ),
}


# Molecular-dynamics figures. These render only when the solvated-system
# topology for the trajectory is available; otherwise they are skipped (never
# fabricated). MD is exploratory under project governance — captions must not
# claim MD "validates" anything.
MD_FIGURE_SPECS: Dict[str, FigureSpec] = {
    "md_rmsd": FigureSpec(
        figure_id="md_rmsd",
        title="Backbone RMSD over the trajectory",
        reviewer_question="Did MD actually validate the prediction, or only simulation stability?",
        claim_support="The simulated structure remains stable (bounded Cα RMSD), supporting "
        "that downstream fluctuation analysis reflects equilibrium dynamics, not drift.",
        caption=(
            "Cα RMSD relative to the first frame over the saved trajectory "
            "({n_frames} frames, {length_ns:.2f} ns at {dt_ps:.0f} ps/frame). "
            "Bounded RMSD indicates a stable fold under the tested apo conditions. "
            "This is a stability check only; it does not by itself validate a cryptic "
            "pocket."
        ),
        kind="result",
    ),
    "md_rmsf": FigureSpec(
        figure_id="md_rmsf",
        title="Per-residue Cα RMSF",
        reviewer_question="Are novel residues experimentally supported?",
        claim_support="Predicted candidate residues coincide with elevated backbone "
        "flexibility, a necessary (not sufficient) condition for cryptic-pocket motion.",
        caption=(
            "Per-residue Cα root-mean-square fluctuation over the trajectory "
            "({length_ns:.2f} ns). Higher values mark mobile regions. Elevated "
            "flexibility at candidate residues is consistent with, but does not prove, "
            "cryptic-pocket opening. Apo conditions only."
        ),
        kind="result",
    ),
    "md_dccm": FigureSpec(
        figure_id="md_dccm",
        title="Cα dynamic cross-correlation (DCCM)",
        reviewer_question="Did MD actually validate the prediction, or only simulation stability?",
        claim_support="Correlated-motion structure provides exploratory context for how "
        "candidate-pocket residues move relative to the rest of the protein.",
        caption=(
            "Dynamic cross-correlation matrix of Cα displacements over the trajectory "
            "({length_ns:.2f} ns). Red indicates correlated motion, blue anti-correlated. "
            "Exploratory analysis under apo conditions; no validation claim is made."
        ),
        kind="result",
    ),
}


def all_specs() -> List[FigureSpec]:
    return list(FIGURE_SPECS.values()) + list(MD_FIGURE_SPECS.values())
