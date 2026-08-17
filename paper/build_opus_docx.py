"""Assemble the Opus-authored paper into a .docx with the 8 figures embedded.

The prose below is written to the same grounded facts and integrity rules as the
generation prompt: real numbers only, no test-set results, honest negative MD
triage, no banned overclaim phrases. We feed it through the existing
paper_engine docx assembler so figures are embedded with numbered captions.
"""
from __future__ import annotations

import json
from pathlib import Path

from paper_engine import config
from paper_engine.manuscript import assemble_docx
from paper_engine.manuscript.bibliography import (
    apply_remap, finalize_citations, load_references)
from paper_engine.manuscript.section_writer import SectionResult

TITLE = ("Leakage-Controlled Graph Neural Networks for Residue-Level "
         "Cryptic-Pocket Prediction in PCNA")
SUBTITLE = "An honestly-evaluated computational pipeline"
DRAFT_NOTICE = (
    "Draft. Every figure and statistic is computed from the project's real validation "
    "data and the real 25 ns exploratory MD; the held-out test set was not evaluated. "
    "For human review and revision before submission."
)

# section_id -> (heading, [figure_ids], prose). Prose uses [n] citations keyed to
# load_references() ordering; finalize_citations renumbers to only-cited refs.
SECTIONS = [
    ("abstract", "Abstract", [],
"""PCNA (proliferating cell nuclear antigen) sits at the center of DNA replication and repair, which is exactly what makes it both an attractive cancer target and a frustrating one: the surfaces that matter are smooth protein-protein interfaces with few obvious small-molecule handles. Cryptic pockets — transient cavities that are not visible in a static structure — could open a way in, but they are hard to find, and many published predictors look stronger than they are because homologous proteins leak between training and test sets [15]. We built a graph neural network that flags candidate cryptic-pocket-associated residues in PCNA at the residue level, and we went out of our way to evaluate it honestly. On a frozen split that blocks homology at 30% sequence identity and holds PCNA out entirely, our GraphSAGE-3L model reached a validation macro-AUPRC of 0.1876 +/- 0.0113, above graph-convolution and attention baselines and well above a random scorer (0.086) on the same split; the 214-structure test set was never touched. We then ran a 25 ns exploratory molecular-dynamics triage on apo PCNA. The candidate residues stayed rigid and showed no pocket opening — a clean negative result at this timescale. We report all of it as-is: a reproducible, leakage-controlled pipeline whose honest evaluation is the contribution."""),

    ("introduction", "1. Introduction", [],
"""PCNA is a homotrimeric ring that clamps around DNA and slides along it, acting as the mobile loading dock for the enzymes that copy and repair the genome. Because almost every replication and repair protein has to dock onto the same clamp, PCNA is a hub, and hubs are tempting drug targets in cancer, where replication is the disease. The problem is that PCNA does its job through a shallow protein-protein interface — the PIP-box groove on the front face and the interdomain connecting loop (IDCL) — rather than a deep catalytic pocket. There is simply not much for a small molecule to grab onto, which is why PCNA has long been filed under "undruggable."

Cryptic pockets are the reason that label may be too pessimistic. These are cavities that stay closed in a crystal structure but open transiently as the protein breathes, and once opened they can bind drug-like molecules. They have been found and exploited in targets that were also thought to be flat or featureless [17, 14], and the precedent of compounds that engage PCNA-adjacent surfaces suggests the same could be true here. The catch is that you cannot see a cryptic pocket by looking; you have to predict where one is likely to form and then test it.

Predicting cryptic-pocket residues from a single structure is hard, and the field has a measurement problem on top of the modeling problem. Most residue-level benchmarks are built from large structure databases in which near-duplicate and homologous proteins end up on both sides of the train/test divide. A model can then score well by memorizing families rather than learning physics, and the headline number — often an inflated AUROC under heavy class imbalance — flatters it [6]. We wanted to know what an honestly-evaluated model actually does.

This paper makes a deliberately modest, careful claim. We trained a graph neural network on a homology-blocked split of labelled structures, reserved a PCNA-containing test set we have not looked at, reported macro-AUPRC against the prevalence floor rather than AUROC, and then ran an exploratory simulation to see whether the residues we flagged behave like a cryptic site. The throughline of the work is a single question: can a leakage-clean GNN highlight candidate cryptic-pocket residues in PCNA and be evaluated honestly enough that the result survives scrutiny?"""),

    ("background", "2. Background and Related Work", [],
"""Cryptic-pocket detection has grown into its own subfield. Geometry- and energy-based methods such as fpocket and P2Rank score static surfaces, while CryptoSite and the PocketMiner graph neural network learn to predict where a pocket is likely to open from a single conformation [15]. The other major line of attack is simulation: mixed-solvent and enhanced-sampling molecular dynamics deliberately perturb the protein to coax cryptic sites open. CrypticScout maps cryptic sites with mixed-solvent simulations [3], SWISH biases water-protein interactions to widen transient pockets [18], and AlphaFold-SFA combines structure prediction with slow-feature analysis and metadynamics to sample opening events efficiently [2, 14]. These simulation methods are powerful but expensive, and they are usually run on a handful of targets at a time.

The modeling tools we build on come from two recent threads. Graph neural networks treat a protein as a graph of residues connected by spatial and sequential edges, which lets a model reason about local structural neighborhoods directly; this framing has been applied to binding-site and allosteric-network prediction with encouraging results [6, 11]. In parallel, protein language models such as ESM2 produce per-residue embeddings that capture evolutionary and structural context, and feeding those embeddings into downstream predictors has improved residue-level tasks from binding-site identification to functional-site classification [1, 12]. Combining a graph view of structure with language-model features is a natural fit for residue-level cryptic-pocket prediction.

What ties our methodological choices together is the leakage problem. When homologous chains appear in both training and evaluation, reported performance reflects memorization as much as generalization, and the issue is sharpened by class imbalance: cryptic-pocket residues are rare, so AUROC can sit near 0.7 while the model is barely beating the prevalence baseline. The honest responses are well known but unevenly applied — block homology in the split, hold out the target family, and report area under the precision-recall curve against the positive rate rather than AUROC [6, 10]. We adopt all three, and treat them not as caveats but as the design.""" ),

    ("methods", "3. Methods", ["dataset_split", "metric_choice"],
"""Dataset and labels. We worked from 1,101 labelled protein structures under a positive-unlabeled labelling scheme, in which residues known to participate in a cryptic or pocket-associated site are positive and the remainder are treated as unlabeled background. This yields 16,335 positive residues; a further 3,704 residues are masked and excluded from the loss where labels are ambiguous. Positive residues make up roughly 4.5% of the evaluated set — an imbalance that drives several downstream choices.

Split. The split is frozen and recorded by a manifest hash (24dd5e34) so that every run sees exactly the same partition. Crucially, it is homology-blocked at 30% sequence identity, so no chain in one fold is a close homolog of a chain in another, and the PCNA cluster is held out in its entirety. A 214-structure test set was set aside at the start and has never been evaluated; all numbers in this paper are validation numbers. Figure 1 summarizes the composition and the label balance.

Features. Each residue is a node carrying 25 hand-built structural features together with per-residue embeddings from the ESM2 protein language model, which supply evolutionary and contextual information that hand-built descriptors miss [1]. Edges encode both spatial proximity and sequential adjacency, so the network can reason about a residue's physical neighborhood and its position along the chain.

Architecture and training. The primary model is a three-layer GraphSAGE network (hidden dimension 128, dropout 0.1) trained with Adam at a learning rate of 0.001. Because positives are rare, the loss is weighted by a positive weight of approximately 21. We trained 12 models in total — four cross-validation folds times three random seeds — with early stopping on validation macro-AUPRC (patience 10), which lets us report variability across both data partition and initialization rather than a single lucky run.

Evaluation. We report macro-AUPRC, the per-protein average area under the precision-recall curve, as the primary metric. The reason is visible in Figure 2: at about 4.6% prevalence, a random scorer already reaches an AUROC near 0.50 while its AUPRC sits near 0.05, so AUROC rewards a model for very little. AUPRC measured against the prevalence floor is the honest yardstick for a rare-residue task, and we use it throughout. We also benchmarked several baselines — a random scorer, a degree/exposure heuristic, a one-layer GCN, a two-layer GAT, and two edge-ablated variants of our own model — all trained and evaluated on the identical split.

Molecular-dynamics setup. To probe whether the flagged residues behave like a cryptic site, we ran an exploratory all-atom simulation of the human PCNA homotrimer (PDB 1AXC, taken apo by removing the bound p21 peptide) in OpenMM 8.2 with the AMBER14 force field and TIP3P water, a system of roughly 287,000 atoms. One replicate reached the full 25 ns (250 frames at 0.1 ns spacing); a second was cut short at the compute-budget wall and is treated as incomplete. We discarded the first 5 ns as equilibration. An initial automated analysis was physically impossible (backbone RMSD around 2.5 nm) because periodic-boundary images had not been rejoined; we re-ran it with explicit molecule imaging before superposition, aligned on a stable structural core that excludes the residue windows we measure (to avoid circularity), and computed RMSF about the mean position. We summarized flexibility per residue window and used solvent-accessible surface area and pocket mouth-distance time series as proxies for opening."""),

    ("results", "4. Results", ["baseline_comparison", "per_fold_performance",
                               "ablation_edges", "training_curves"],
"""Across the 12 validation runs, the GraphSAGE-3L model reached a macro-AUPRC of 0.1876 +/- 0.0113. On the same frozen split, the graph baselines fell below it — GAT-2L at 0.1739 +/- 0.0090 and GCN-1L at 0.1601 +/- 0.0089 — and the structure-free references sat near the prevalence floor, with the degree/exposure heuristic at 0.0813 and a random scorer at 0.0861 +/- 0.0011. Figure 3 shows the full comparison. The gap over random is the number we trust most: it is small in absolute terms, as one should expect for residue-level prediction of a rare label, but it is consistent and it is measured under conditions designed not to flatter the model.

Performance was stable across folds rather than carried by one partition. Per-fold means were 0.173, 0.2035, 0.1872, and 0.1865 (Figure 4). Fold 1 is consistently the easiest partition for every model we tried, not just ours, which tells us the variation reflects how hard each held-out set is rather than seed luck; the best single run, on fold 1, reached 0.2042. The learning curves in Figure 6 show each run climbing and then being halted by early stopping near its validation peak, so the reported numbers are not inflated by overfitting.

The ablation in Figure 5 is where we learned the most, and not in the direction we expected. Removing the spatial edges — the ones that encode physical proximity — dropped performance to 0.1556 +/- 0.0114, confirming that the structural neighborhood carries the signal. Removing the sequential edges did the opposite: the no-sequential variant reached 0.1897 +/- 0.0089, a hair above the full model and well within one standard deviation. We therefore cannot claim that sequential edges contribute anything; if anything, the honest reading is that they are not pulling their weight, and a leaner architecture deserves a look. We report this plainly rather than quietly dropping the inconvenient variant.

One number we deliberately do not report is test-set performance. The 214-structure test set, which contains the PCNA family, has not been evaluated and will not be until the model and baselines are frozen and a one-shot evaluation is authorized. Everything above is validation, intended for model selection, and we treat it that way."""),

    ("md", "5. Molecular-Dynamics Triage", ["md_rmsd", "md_rmsf"],
"""Having a model that flags residues is not the same as having a cryptic pocket, so we ran a short simulation to look. The goal here was triage, not proof: a single 25 ns trajectory of apo PCNA cannot sample the slow opening events that define cryptic sites, and we set it up knowing that. What it can do is tell us whether the candidate residues are even mobile, and whether anything obvious happens when the p21 peptide is removed.

The simulation itself was well-behaved. After re-running the analysis with proper periodic-boundary imaging — the first pass had produced a physically impossible RMSD because images were not rejoined — the backbone settled into a flat plateau, with a mean Cα RMSD of 0.255 nm and a maximum of 0.305 nm over the analyzed window (Figure 7). The trimer is stable; potential energy, temperature, and density were all steady. So the fluctuations we measure reflect equilibrium breathing, not drift or blow-up.

The flexibility result is a clean negative, and it is the honest centerpiece of this section. Figure 8 shows per-window Cα RMSF for the three GNN novel candidates (residues 239-243, 28-32, and 206-210) against the known-flexible IDCL/PIP reference window (118-122). Every candidate window is less mobile than the reference, at 0.59 to 0.65 times its RMSF; even the IDCL-adjacent control window sits at 0.67 times. We extended the check with solvent-accessible surface area and pocket mouth-distance proxies across the three monomers, and the picture held: the candidate regions showed only transient SASA excursions of 18-26% that lasted a handful of frames and returned to baseline, the front-face PIP pocket stayed essentially static after p21 removal, and the only sustained widening was in the IDCL itself, which is exactly the loop expected to move.

The plain reading is that, under this short apo setup, the GNN-predicted candidate pockets remained rigid and did not open. We are careful about what that means. This is a valid negative or inconclusive result, not a falsification of the predictions: 25 ns with one usable replicate and no positive control simply cannot sample nanosecond-to-microsecond cryptic-opening events, and a model that flags a residue as cryptic-pocket-associated is making a prediction about rare conformational states that a stable short trajectory is not designed to reach. The simulation tells us the candidates are not trivially flexible, and it tells us what a real test would require; it does not tell us the predictions are wrong, and it certainly does not support any claim of a binding or druggable site."""),

    ("discussion", "6. Discussion", [],
"""It is worth being precise about what the model produces. A high score on a residue is a computational hypothesis: this position is the kind of place where a cryptic pocket has formed in other proteins, given its structural neighborhood and evolutionary context. It is not a validated site, and on PCNA specifically — held out of training entirely — every prediction is an extrapolation that we have chosen not to test yet. Treating these residues as leads to investigate, rather than as discoveries, is the only defensible stance given the evidence in hand.

The negative MD triage sharpens that stance rather than undermining it. There are two ways to read a stable, rigid candidate region over 25 ns. The pessimistic reading is that the predictions are noise. The more careful reading, and the one the literature supports, is that cryptic opening is a slow, rare event that short apo simulations are the wrong tool to observe; the methods built specifically to see these events — mixed-solvent MD, metadynamics, SWISH, AlphaFold-SFA — exist precisely because plain simulation does not surface them on accessible timescales [2, 3, 18]. Our result is therefore consistent with both a true cryptic site that we failed to open and a residue the model got wrong, and we cannot distinguish them here. What we can say is that the candidates are not already-open, trivially mobile loops, which at least rules out the least interesting explanation. Cryptic sites with real therapeutic relevance have been found in other "flat" cancer targets [13, 7, 8], so the hypothesis is worth the cost of a proper test.

Finally, we think the way this work is evaluated is as much the contribution as the model. It would have been easy to report an AUROC near 0.66, run the simulation until something looked like motion, and call it validation. We did the opposite: we blocked homology, held out the family, reported AUPRC against the prevalence floor, kept the test set sealed, and wrote down a negative simulation result in full. The absolute numbers are modest and we say so. But a modest number you can trust is more useful than an impressive number you cannot, and for a target as consequential and as overclaimed as PCNA, that trade is the right one."""),

    ("limitations", "7. Limitations", [],
"""The limitations are specific and we would rather list them than have a reviewer find them. The headline evaluation is validation-only: the 214-structure test set, which contains PCNA, has never been scored, so we make no claim about generalization. The absolute macro-AUPRC is modest, which is honest for residue-level prediction of a rare label but means the model is a triage tool, not a precise localizer. The edge ablation shows the sequential edges contribute nothing we can measure, so the architecture is not yet justified in full and a leaner variant may be equivalent. The external structural baselines — fpocket, P2Rank, and PocketMiner — have not yet been run on this split, so the comparison set is currently limited to our own baselines [15]. On the simulation side, we have one usable 25 ns replicate (a second was incomplete and a third was not run), on a single structure taken apo by removing p21, with no 8GLA holo positive control to confirm the protocol can detect a known pocket. The opening metrics — SASA, mouth distances, radius-of-gyration proxies — are surrogates for true pocket volume rather than direct measurements, since we did not run fpocket or MDpocket on the trajectory, and the three monomers we treat as informal triplicates are not statistically independent. Finally, the first-MD-interpretation human review gate for this project has not yet been recorded. None of these are fatal, but each bounds exactly how far the claims can be pushed, and we have tried not to push past them."""),

    ("conclusion", "8. Conclusion and Future Work", [],
"""We set out to ask whether a leakage-clean graph neural network could flag candidate cryptic-pocket residues in PCNA and survive an honest evaluation, and the answer is a qualified yes. The model beats naive and graph baselines on a homology-blocked split under the right metric, its behavior is stable across folds, and its one genuinely surprising result — that sequential edges add nothing measurable — was reported rather than buried. The accompanying 25 ns simulation did not show the candidates opening, and we have presented that as the clean negative result it is. What we have, concretely, is a reproducible, leakage-controlled, residue-level pipeline with candid evaluation, which is a more trustworthy starting point than a higher number obtained by looser methods.

The path forward is clear and largely about earning the right to stronger claims. The immediate step is a single, human-authorized, one-shot evaluation on the sealed 214-structure test set, after the model and baselines are frozen. In parallel, the external structural baselines should be run on the same split so the comparison is complete. The simulation work needs the most investment: longer trajectories and enhanced-sampling methods built to surface cryptic opening, run alongside an 8GLA holo positive control that proves the protocol can detect a known PCNA pocket before any candidate is judged. Only then would it be appropriate to move from candidate residues to claims about sites. Until that work is done, the honest summary is the one we have given — a careful method, a modest validated signal, and a negative simulation that tells us exactly what to do next."""),
]


def _finalize_grouped(full_text, refs):
    """Group-aware citation finalizer: handles [n] AND [n, m, ...]."""
    import re
    from dataclasses import replace
    order = []
    for m in re.finditer(r"\[([\d,\s]+)\]", full_text):
        for part in m.group(1).split(","):
            try:
                n = int(part.strip())
            except ValueError:
                continue
            if n not in order and any(r.idx == n for r in refs):
                order.append(n)
    remap = {old: i + 1 for i, old in enumerate(order)}
    by = {r.idx: r for r in refs}
    used = [replace(by[o], idx=remap[o]) for o in order]

    def _sub(m):
        nums = [remap[int(p)] for p in re.findall(r"\d+", m.group(1)) if int(p) in remap]
        return "[" + ", ".join(str(n) for n in nums) + "]" if nums else ""

    def rewrite(text):
        return re.sub(r"\[([\d,\s]+)\]", _sub, text)

    return remap, used, rewrite


def main() -> None:
    refs = load_references(limit=18)
    results = []
    for sid, heading, figs, text in SECTIONS:
        results.append(SectionResult(
            section_id=sid, heading=heading, text=text.strip(),
            word_count=len(text.split()), used_llm=True, figures=list(figs)))

    full = "\n".join(s.text for s in results)
    remap, used_refs, rewrite = _finalize_grouped(full, refs)
    for s in results:
        s.text = rewrite(s.text)

    manifest = config.FIGURES_DIR / "figures_manifest.json"
    figure_map = {f["figure_id"]: f
                  for f in json.loads(manifest.read_text(encoding="utf-8"))["figures"]}

    meta = {"title": TITLE, "subtitle": SUBTITLE, "author": "Advay",
            "date": "2026-05-30", "draft_notice": DRAFT_NOTICE}
    out = config.PAPER_DIR / "manuscript_opus.docx"
    assemble_docx.build_docx(meta, results, figure_map, used_refs, out)

    total = sum(s.word_count for s in results)
    print(f"DOCX: {out}")
    print(f"Sections: {len(results)} | words: ~{total} | references cited: {len(used_refs)}")
    print(f"Figures embedded: {[fid for s in results for fid in s.figures]}")


if __name__ == "__main__":
    main()
