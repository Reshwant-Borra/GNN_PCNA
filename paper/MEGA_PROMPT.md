You are an expert computational-biology scientific writer. Write a COMPLETE, competition-grade research paper (target ~10 pages, ~4,500–5,500 words) for a high-school science competition (ISEF/Regeneron-STS/JSHS style). The work is real; write it with the rigor and restraint of a strong preprint. Output GitHub-flavored Markdown only.

================================================================
CRITICAL INTEGRITY RULES — these override everything; violating any one invalidates the paper
================================================================
1. Use ONLY the numbers and facts in the DATA block below. Invent NOTHING — no extra numbers, p-values, datasets, or results.
2. The held-out TEST SET (214 structures) was NEVER evaluated. Never state, imply, or hint at any test-set performance or generalization result.
3. Report macro-AUPRC as the primary metric. AUROC is INFLATED under ~4.6% positive prevalence — say so; do not lead with AUROC.
4. NO claim of a "validated", "confirmed", "discovered", "proven", or "druggable" pocket or binding site. Use candidate-region language: "candidate pocket-associated residues", "computationally predicted", "requires further validation".
5. The molecular dynamics is a 25 ns EXPLORATORY run on 1AXC. The candidate residues remained RIGID and did NOT open — report this as a valid NEGATIVE/INCONCLUSIVE result. NEVER write that the pocket opened, that MD "validated" anything, or that binding occurred. NEVER inflate the timescale (it is 25 ns — not 100 ns, not 900 ns).
6. The edge-type ablation shows the sequential-edge contribution is NOT established (the no-sequential variant is within 1 SD of the full model). State this honestly; do not claim the full architecture is required.
7. Cite ONLY from the REFERENCES list, as [n]. Do not fabricate citations.
8. The honesty (reserved test set, AUPRC-over-AUROC, reported negative MD result) is the paper's strength — frame it that way, not apologetically.

================================================================
DATA (real, frozen) — the only results you may state
================================================================
PROJECT: A leakage-controlled graph neural network that predicts, at the residue level, candidate cryptic-pocket-associated residues in PCNA (Proliferating Cell Nuclear Antigen), a cancer-relevant DNA-replication sliding-clamp protein.

DATASET & SPLIT:
- 1,101 labelled protein structures; positive-unlabeled labelling; 16,335 positive residues, 3,704 masked (excluded from the loss).
- Positive prevalence among evaluated residues ≈ 4.5%.
- Split is FROZEN (manifest hash 24dd5e34), homology-blocked at 30% sequence identity; the PCNA cluster is held out entirely; the test set = 214 structures and was NEVER evaluated during model selection.

MODEL (primary):
- GraphSAGE-3L: hidden_dim 128, dropout 0.1, lr 0.001, pos_weight ≈ 21.0.
- Node features = 25 structural features + ESM2 per-residue protein-language-model embeddings.
- Trained over 12 runs = 4 cross-validation folds × 3 seeds, early stopping (patience 10).

VALIDATION RESULTS (validation folds only — NO test results exist):
- Primary GraphSAGE-3L: macro-AUPRC 0.1876 ± 0.0113 (12 runs); per-fold means fold0 0.173, fold1 0.2035, fold2 0.1872, fold3 0.1865; best single run 0.2042; mean macro-AUROC 0.661.
- Baselines, SAME split, validation macro-AUPRC:
    • SAGE-3L (no sequential edges): 0.1897 ± 0.0089
    • GAT-2L: 0.1739 ± 0.0090
    • GCN-1L: 0.1601 ± 0.0089
    • Degree / exposure: 0.0813
    • Random: 0.0861 ± 0.0011
- Edge-type ablation (validation macro-AUPRC):
    • Full GraphSAGE-3L: 0.1876 ± 0.0113
    • No sequential edges: 0.1897 ± 0.0089  (Δ +0.0021 vs full — within 1 SD; sequential-edge value NOT established)
    • No spatial edges: 0.1556 ± 0.0114  (spatial edges carry the signal)
- External structural baselines (fpocket, P2Rank, PocketMiner): NOT yet run.
- Note: a random scorer reaches macro-AUROC ≈ 0.50 but macro-AUPRC ≈ 0.05 (≈ prevalence), so AUROC overstates skill — this is why macro-AUPRC is primary.

MOLECULAR DYNAMICS (Phase-5 exploratory triage — REAL):
- System: human PCNA homotrimer 1AXC (apo-from-p21; the p21 peptide was removed). OpenMM 8.2, AMBER14, TIP3P, ~287,000 atoms.
- Sampling: effective n = 1. replicate_01 = full 25 ns (250 frames @ 0.1 ns); replicate_02 incomplete (killed at budget wall); no 8GLA holo positive control. First 5 ns discarded as equilibration (200 frames analyzed).
- Analysis correction (methods detail worth telling): the original analysis was corrupted by missing periodic-boundary imaging (physically impossible RMSD ~2.5 nm, RMSF 1–3 nm); it was re-run with image_molecules before superposition, core alignment EXCLUDING the measured windows (no circularity), and RMSF about the mean position. The simulation itself was stable (potential energy flat ~ −2.68M kJ/mol, T = 300 K, ρ = 1.01 g/mL).
- Stability (replicate_01): backbone Cα RMSD mean 0.255 nm, max 0.305 nm, final 0.287 nm — flat plateau, stable trimer.
- Per-window Cα RMSF (nm) and ratio vs the IDCL/PIP reference window 118–122:
    • 239–243 (novel candidate A): 0.081  (0.65×)
    • 28–32   (novel candidate B): 0.081  (0.65×)
    • 206–210 (novel candidate C): 0.074  (0.59×)
    • 134–138 (IDCL-adjacent control): 0.084 (0.67×)
    • 118–122 (IDCL/PIP positive-control reference): 0.126 (1.00×)
- Pocket-opening check (SASA + mouth-distance proxies; 3 monomers as informal triplicates): NO sustained opening in any monomer. Novel candidates showed only transient SASA excursions (~18–26%, lasting 2–7 of 200 frames, returning to baseline). Front-face PIP pocket essentially static (5–8% amplitude). Only sustained widening was the known-flexible IDCL (134–138, ~55% transient, +6–13% drift) — expected loop motion.
- RESULT: the GNN-predicted novel candidate pockets (239–243, 28–32, 206–210) remained RIGID and did NOT open; the front-face PIP pocket did not reopen after p21 removal; observed flexibility was confined to the known IDCL. A valid NEGATIVE/INCONCLUSIVE result (NOT falsification): 25 ns / n=1 / no positive control cannot sample ns–µs cryptic-opening events. No druggability, validated-site, or novel-site claims are supported.

================================================================
FIGURES — already generated; insert the placeholder where indicated, number them in order of appearance, and write a one–two sentence caption matching the description (do not contradict it)
================================================================
Insert each as a Markdown image placeholder, e.g.  ![Figure N](paper/figures/<id>.png)  followed by *Figure N. <caption>.*
- dataset_split — Dataset composition & frozen split: structure counts across folds + held-out test set (30% identity, PCNA held out); residue label composition (positive vs masked). Hash 24dd5e34; test set never loaded.  [METHODS]
- metric_choice — Why macro-AUPRC not AUROC: at ~4.6% prevalence a random scorer hits AUROC ≈ 0.50 but AUPRC ≈ 0.05; AUROC overstates skill.  [METHODS]
- baseline_comparison — Validation macro-AUPRC for the primary model and all baselines on the same frozen split; ±1 SD; random/degree mark the prevalence floor; test set not evaluated.  [RESULTS]
- per_fold_performance — Per-fold validation macro-AUPRC; fold 1 is a more favorable partition across all models.  [RESULTS]
- ablation_edges — Edge-type ablation: removing spatial edges degrades performance; removing sequential edges does not (Δ +0.0021, within 1 SD) — sequential-edge contribution not established.  [RESULTS]
- training_curves — Validation macro-AUPRC vs epoch for all 12 runs + across-run mean; early stopping limits overfitting.  [RESULTS]
- md_rmsd — Backbone RMSD vs time, apo 1AXC, 25 ns (one complete replicate; a second incomplete at 4 ns, dashed); first 5 ns shaded equilibration; plateau ~0.25 nm = stable.  [MD TRIAGE]
- md_rmsf — Per-window Cα RMSF: candidate windows (239–243, 28–32, 206–210) and IDCL-adjacent control (134–138) are all 0.59–0.67× the IDCL/PIP reference (118–122) — candidates are NOT more flexible; no evidence of opening.  [MD TRIAGE]

================================================================
REFERENCES — cite ONLY these, as [n]; reproduce this list verbatim at the end
================================================================
[1] Gamouh H, Novotný M, Hoksza D (2025). Hybrid protein–ligand binding residue prediction with protein language models: does the structure matter? doi:10.1093/bioinformatics/btaf431
[2] Vats S et al. (2023). AlphaFold-SFA: accelerated sampling of cryptic pocket opening, protein–ligand binding and allostery by AlphaFold, slow feature analysis and metadynamics. doi:10.1101/2023.11.21.568098
[3] Martinez-Rosell G et al. (2020). PlayMolecule CrypticScout: Predicting Protein Cryptic Sites Using Mixed-Solvent Molecular Simulations. doi:10.1021/acs.jcim.9b01209
[4] Vats S et al. (2024). AlphaFold-SFA (journal version). doi:10.1371/journal.pone.0307226
[5] Mukhopadhyay S, Chakrabarty S (2026). Mapping Protein–Protein Interaction Hotspots and Unveiling a Cryptic Allosteric Pocket in PLK1 PBD via Mixed-Solvent MD. doi:10.1002/cphc.202500907
[6] Chen SH, Lupo Pasini M, Hauck CD (2025). Enhancing Protein Binding Site Residue Prediction with Graph Neural Networks. doi:10.1101/2025.08.25.672254
[7] Liu Y et al. (2024). mTOR variants activation discovers a PI3K-like cryptic pocket. doi:10.1101/2024.10.12.618044
[8] O'Connor S et al. (2022). Discovery and Characterization of a Cryptic Secondary Binding Site in HSP70. doi:10.3390/molecules27030817
[9] Vottero P et al. (2025). Molecular simulations of paclitaxel binding to mutant β-tubulin. doi:10.1007/s10822-025-00716-y
[10] Liu Y (2024). Exploring Protein-DNA Binding Residue Prediction and Consistent Interpretability with Deep Learning. doi:10.1101/2024.10.12.613667
[11] Marfoglia M, Guirardel L, Barth P (2024). AlloPool: An Adaptive GNN for Dynamic Allosteric Network Prediction. doi:10.1101/2024.11.01.621466
[12] Sargsyan K (2025). Protein Language Model Embeddings Distinguish Catalytic from Structural Zinc-Binding Sites. doi:10.26434/chemrxiv-2025-sfn7n
[13] Shakeel H (2025). Structure-Based Discovery of a Cryptic Druggable Pocket in TP53 C238Y. doi:10.26434/chemrxiv-2025-29bnr
[14] Oleinikovas V et al. (2016). Understanding Cryptic Pocket Formation in Protein Targets by Enhanced Sampling Simulations. doi:10.1021/jacs.6b05425
[15] Meller A et al. (2023). Predicting locations of cryptic pockets from single protein structures using the PocketMiner GNN. doi:10.1038/s41467-023-36699-3
[16] Beglov D et al. (2018). Exploring the structural origins of cryptic sites on proteins. doi:10.1073/pnas.1711490115
[17] Hart KM et al. (2017). Designing small molecules to target cryptic pockets yields positive and negative allosteric modulators. doi:10.1371/journal.pone.0178678
[18] Comitani F, Gervasio FL (2018). Exploring Cryptic Pocket Formation in Targets of Pharmaceutical Interest with SWISH. doi:10.1021/acs.jctc.8b00263

================================================================
STRUCTURE — write every section IN FULL; aim for the word counts; ~10 pages total
================================================================
Title: "Leakage-Controlled Graph Neural Networks for Residue-Level Cryptic-Pocket Prediction in PCNA"  (subtitle: "An honestly-evaluated computational pipeline"). Author: Advay. Date: 2026-05-30.
Throughline (state it in the intro): Can a leakage-clean GNN highlight candidate cryptic-pocket residues in PCNA and be evaluated honestly enough to survive scrutiny?

Abstract (~210 w): cancer relevance of PCNA; the cryptic-pocket detection gap; the leakage-clean GNN; validation macro-AUPRC vs baselines; test set reserved; the 25 ns MD triage found candidates remained rigid (negative/inconclusive); close on the honest, reproducible contribution. No overclaim.

1. Introduction (~470 w, 4 paragraphs): (a) PCNA biology — homotrimeric sliding clamp, DNA replication/repair, the PIP-box/IDCL interface — compelling but "undruggable"; (b) cryptic pockets as the opportunity (and the AOH1996 precedent); (c) the gap — residue-level prediction is hard, homology leakage inflates benchmarks; (d) contribution: a leakage-clean GNN, honestly evaluated, plus an exploratory MD triage. State the throughline.

2. Background and Related Work (~470 w, 3 paragraphs): (a) cryptic-pocket detection — CryptoSite, PocketMiner [15], fpocket/P2Rank, mixed-solvent & enhanced-sampling MD (CrypticScout [3], AlphaFold-SFA [2], SWISH [18]); (b) GNNs and protein language models (ESM2) for residue-level prediction [6,11,12]; (c) the leakage problem and why homology-blocked splits and AUPRC-over-AUROC matter.

3. Methods (~600 w, with subsection-style prose): dataset & labels (positive-unlabeled, 1,101 structures, 16,335 positive / 3,704 masked); the frozen homology-blocked split (30% identity, PCNA held out, 214 reserved test structures, hash 24dd5e34); node features (25 structural + ESM2); GraphSAGE-3L architecture & training (128 / 0.1 / 0.001 / pos_weight ~21; 4 folds × 3 seeds; early stopping); evaluation protocol justifying macro-AUPRC over AUROC at ~4.6% prevalence; MD setup (1AXC apo-from-p21 homotrimer, OpenMM/AMBER14/TIP3P ~287k atoms, 25 ns, 5 ns equilibration discarded, PBC-corrected RMSD/RMSF, SASA & mouth-distance opening proxies). Place figures dataset_split and metric_choice here.

4. Results (~520 w): validation macro-AUPRC for the primary model vs random, degree, GCN, GAT, and edge ablations on the same split; fold consistency (fold 1 easier); honest edge ablation (spatial carries signal; sequential not established). State these are validation, model-selection metrics; test set unevaluated. Place baseline_comparison, per_fold_performance, ablation_edges, training_curves here.

5. Molecular-Dynamics Triage (~460 w): system + sampling (incl. the PBC-correction story); stability (RMSD plateau ~0.255 nm); the key finding (candidate windows RMSF 0.59–0.65× reference; SASA/mouth-distance show only transient excursions returning to baseline → candidates RIGID, did NOT open; only the IDCL moved as expected); frame as a valid negative/inconclusive result (25 ns / n=1 / no positive control cannot sample ns–µs events). Never write "validated"/"opened"/"binding". Place md_rmsd and md_rmsf here.

6. Discussion (~520 w, 3 paragraphs): (a) what the GNN candidates do/do not mean (computational hypotheses, not validated sites); (b) reconcile the predictions with the negative MD — short apo MD cannot sample cryptic opening, so rigidity here neither confirms nor refutes; (c) why the leakage-clean, AUPRC-honest, negative-result-reporting stance is scientifically sound.

7. Limitations (~380 w, one tight paragraph): validation-only (214-structure test reserved); modest absolute macro-AUPRC for a hard task; unestablished sequential-edge contribution; external baselines not run; MD limits — 25 ns usable, n=1 (rep2 incomplete, rep3 absent), single structure, apo-from-p21 relaxation, no 8GLA positive control, SASA/distance are proxies not true pocket volume, 3 monomers not independent.

8. Conclusion and Future Work (~320 w, 2 paragraphs): the honest contribution; concrete next steps (human-gated one-shot test evaluation, external baselines, longer/enhanced-sampling MD with the 8GLA holo positive control, PCNA-specific inference).

References: reproduce the list above verbatim.

================================================================
STYLE
================================================================
Precise, restrained academic English; define terms on first use; vary section openings (never start two sections the same way); integrate citations naturally; never use the banned overclaim words. The strongest move you can make is calm honesty about what was and was not shown.
