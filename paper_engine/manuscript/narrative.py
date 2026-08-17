"""Narrative plan — the order a competition judge experiences the paper.

The plan encodes a single throughline (one question the whole paper advances)
and a sequence of sections, each with: its job in the judge's mind, the figures
it embeds, and the reviewer questions it must answer. Science-competition judging
rewards novelty, rigor, honesty, and clear personal contribution, so the arc is:
significance -> gap -> approach -> rigor/controls -> honest results -> limitations
-> impact.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


THROUGHLINE = (
    "Can a leakage-clean graph neural network highlight candidate cryptic-pocket "
    "residues in PCNA — a validated cancer target — and be evaluated honestly "
    "enough that the result survives scrutiny?"
)


@dataclass
class SectionPlan:
    section_id: str
    heading: str
    purpose: str           # what this section must achieve for the judge
    guidance: str          # concrete drafting instructions
    figures: List[str] = field(default_factory=list)
    reviewer_questions: List[str] = field(default_factory=list)
    target_words: int = 220
    requires_md: bool = False


_BASE_PLAN: List[SectionPlan] = [
    SectionPlan(
        section_id="abstract",
        heading="Abstract",
        purpose="Give the judge the entire arc in one paragraph: problem, approach, "
                "honest result (including the negative MD triage), and significance.",
        guidance="One paragraph (~210 words). State the cancer relevance of PCNA, the "
                 "cryptic-pocket detection gap, the leakage-clean GNN approach, the "
                 "validation macro-AUPRC vs baselines, that the test set is reserved, and "
                 "that an exploratory 25 ns MD triage found the candidate residues remained "
                 "rigid (a valid negative/inconclusive result). End on significance — an "
                 "honest, reproducible pipeline — without overclaiming.",
        target_words=210,
    ),
    SectionPlan(
        section_id="introduction",
        heading="1. Introduction",
        purpose="Make the judge care: PCNA is a high-value, hard-to-drug cancer target; "
                "cryptic pockets are the opportunity; finding them computationally is the gap.",
        guidance="4 paragraphs: (1) PCNA biology — sliding clamp, DNA replication/repair, "
                 "the PIP-box/IDCL interface — and why it is compelling but 'undruggable'; "
                 "(2) cryptic pockets as the opportunity and the AOH1996 precedent; (3) the "
                 "gap — residue-level prediction is hard and homology leakage makes most "
                 "benchmarks optimistic; (4) this work's contribution: a leakage-clean GNN, "
                 "honestly evaluated, plus an exploratory MD triage. State the throughline.",
        reviewer_questions=["Why is AUROC meaningful here?"],
        target_words=470,
    ),
    SectionPlan(
        section_id="background",
        heading="2. Background and Related Work",
        purpose="Situate the work in the literature so the judge sees command of the field.",
        guidance="3 paragraphs: (1) cryptic-pocket detection methods — CryptoSite, "
                 "PocketMiner, fpocket/P2Rank, mixed-solvent and enhanced-sampling MD "
                 "(CrypticScout, AlphaFold-SFA); (2) graph neural networks and protein "
                 "language models (ESM2) for residue-level structural prediction; (3) the "
                 "leakage problem in structure benchmarks and why homology-blocked splits "
                 "and AUPRC-over-AUROC matter. Cite from the provided references only.",
        reviewer_questions=["Why is AUROC meaningful here?"],
        target_words=470,
    ),
    SectionPlan(
        section_id="methods",
        heading="3. Methods",
        purpose="Convince the judge the work is rigorous and reproducible.",
        guidance="Cover, with subsection-style prose: dataset and labels (positive-"
                 "unlabeled, 1101 structures, 16,335 positive / 3,704 masked); the frozen "
                 "homology-blocked split (30% identity, PCNA held out, 214 reserved test "
                 "structures, hash 24dd5e34); node features (25 structural + ESM2 "
                 "embeddings); the GraphSAGE-3L architecture and training (hidden 128, "
                 "dropout 0.1, lr 0.001, pos_weight ~21); the evaluation protocol justifying "
                 "macro-AUPRC over AUROC at ~4.6% prevalence; and the MD setup — 1AXC PCNA "
                 "homotrimer (apo-from-p21), OpenMM/AMBER14/TIP3P ~287k atoms, 25 ns, with "
                 "PBC-corrected RMSD/RMSF and SASA/mouth-distance opening proxies. Concrete "
                 "and precise.",
        figures=["dataset_split", "metric_choice"],
        reviewer_questions=[
            "How did you prevent homology leakage?",
            "Is the test set independent at the protein level (not residue level)?",
            "Where is AUPRC and what is the positive-class baseline?",
        ],
        target_words=600,
    ),
    SectionPlan(
        section_id="results",
        heading="4. Results",
        purpose="Show the honest GNN evidence: beats naive and ablated baselines on "
                "validation, with consistent folds and a candid ablation.",
        guidance="Report validation macro-AUPRC for the primary model vs random, degree, "
                 "GCN, GAT, and the edge ablations, all on the same split. Note fold "
                 "consistency (fold 1 is an easier partition). Present the edge ablation "
                 "honestly: spatial edges carry the signal and the sequential-edge "
                 "contribution is not established (no-sequential is within 1 SD). State "
                 "clearly these are validation, model-selection metrics; the test set is "
                 "unevaluated.",
        figures=["baseline_comparison", "per_fold_performance", "ablation_edges",
                 "training_curves"],
        reviewer_questions=[
            "Were baselines compared under the same leakage-clean split?",
            "How many independent test proteins?",
            "Are claims proportional to evidence?",
        ],
        target_words=520,
    ),
    SectionPlan(
        section_id="md",
        heading="5. Molecular-Dynamics Triage",
        purpose="Report the real 25 ns MD honestly: a careful negative/inconclusive result.",
        guidance="Report the REAL Phase-5 MD exactly as in the FACTS. (1) System + sampling: "
                 "1AXC PCNA homotrimer apo-from-p21, OpenMM/AMBER14/TIP3P ~287k atoms, n=1 "
                 "usable 25 ns replicate, 5 ns equilibration discarded, no 8GLA control, and "
                 "the PBC-imaging correction that fixed a physically-impossible raw analysis. "
                 "(2) Stability: backbone Cα RMSD plateau ~0.255 nm = stable trimer. "
                 "(3) The key finding: the GNN novel candidate windows (239-243, 28-32, "
                 "206-210) have RMSF 0.59-0.65x the reference and, by SASA/mouth-distance "
                 "proxies, showed only transient excursions that return to baseline — they "
                 "remained RIGID and did NOT open; only the known IDCL loop moved as "
                 "expected. (4) Frame as a valid negative/inconclusive result, NOT "
                 "falsification: 25 ns / n=1 / no positive control cannot sample ns-us "
                 "cryptic events. Never write 'validated', 'opened', or 'binding'.",
        figures=["md_rmsd", "md_rmsf"],
        reviewer_questions=["Did MD actually validate the prediction, or only simulation stability?"],
        target_words=460,
        requires_md=True,
    ),
    SectionPlan(
        section_id="discussion",
        heading="6. Discussion",
        purpose="Interpret carefully and pre-empt every reviewer doubt; honesty wins here.",
        guidance="3 paragraphs: (1) what the GNN candidate residues do and do not mean "
                 "(computational hypotheses, not validated sites); (2) reconcile the GNN "
                 "predictions with the negative MD triage — short apo MD cannot sample "
                 "cryptic opening, so rigidity here neither confirms nor refutes the "
                 "predictions; (3) why the leakage-clean, AUPRC-honest, negative-result-"
                 "reporting approach is the scientifically sound stance. Avoid any "
                 "overclaim.",
        reviewer_questions=[
            "Are claims proportional to evidence?",
            "Are novel residues experimentally supported?",
        ],
        target_words=520,
    ),
    SectionPlan(
        section_id="limitations",
        heading="7. Limitations",
        purpose="State every limitation explicitly — judges reward this candor.",
        guidance="One tight paragraph enumerating: validation-only (214-structure test set "
                 "reserved, never evaluated); modest absolute macro-AUPRC for a hard "
                 "residue-level task; unestablished sequential-edge contribution; external "
                 "structural baselines (fpocket/P2Rank/PocketMiner) not yet run; and the MD "
                 "limits — 25 ns usable, n=1 (rep2 incomplete, rep3 absent), single "
                 "structure, apo-from-p21 relaxation, no 8GLA positive control, "
                 "SASA/distance are opening proxies not true pocket volume, and the three "
                 "monomers are not independent. Frame as the explicit scope of the claims.",
        target_words=380,
    ),
    SectionPlan(
        section_id="conclusion",
        heading="8. Conclusion and Future Work",
        purpose="Leave the judge with the contribution and a credible path forward.",
        guidance="2 paragraphs: the honest contribution (a leakage-clean, reproducible "
                 "residue-level pipeline with candid evaluation and an honest negative MD "
                 "triage), and concrete next steps (human-gated one-shot test evaluation, "
                 "external baselines, longer/enhanced-sampling MD with the 8GLA holo "
                 "positive control, and PCNA-specific inference).",
        target_words=320,
    ),
]


def build_plan(md_available: bool) -> List[SectionPlan]:
    """Return the ordered section plan, dropping the MD section if no MD data."""
    return [s for s in _BASE_PLAN if (not s.requires_md) or md_available]


def figures_for_plan(plan: List[SectionPlan]) -> List[str]:
    seen: List[str] = []
    for s in plan:
        for f in s.figures:
            if f not in seen:
                seen.append(f)
    return seen
