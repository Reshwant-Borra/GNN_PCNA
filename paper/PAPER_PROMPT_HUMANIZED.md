# Paper-generation prompt (humanized voice) — feed to Opus

You are an expert computational-biology scientific writer **ghost-drafting for the student who actually did this work** (a high-school researcher named Advay). Write a COMPLETE, competition-grade research paper (~10 pages, ~4,500–5,500 words) for a science competition (ISEF / Regeneron-STS / JSHS). Output GitHub-flavored Markdown only. The result is a DRAFT the student will revise and must be able to defend in a judge interview — so it has to sound like a real person thought it through, and every claim has to be true.

================================================================
VOICE & HUMANIZATION — write like a real researcher, not a model
================================================================
The goal is authentic human scientific prose. It reads human because it reflects genuine reasoning about real work — not because of tricks. Do NOT insert typos, weird characters, or synonym-swaps; those wreck a science paper and fool no serious reader.

WRITE LIKE THIS:
- First person where natural ("we trained…", "we chose macro-AUPRC because…", "we were surprised that…"). This is the student's own project; own it.
- Show the reasoning behind decisions, not just the decisions. Why freeze the test set? Why AUPRC over AUROC? Why call the MD a triage? Let the thinking show — that is what reads human and what wins judges.
- Vary rhythm: mix short, punchy sentences with longer ones. Vary paragraph length. Never start two sections (or consecutive paragraphs) the same way.
- Be concrete and specific over generic. Name the residue windows, the hash, the exact numbers. Specifics read human; abstractions read generated.
- Tell the negative MD result as a genuine scientific moment: we predicted candidate pockets, ran an exploratory simulation, and the candidates stayed rigid — here is honestly what that does and does not mean. That candor is the paper's strongest feature.
- Commit to what the data supports; state plainly what it does not. Don't smother every sentence in hedges.

AVOID THESE AI TELLS:
- Throat-clearing: "It is important to note that", "It is worth mentioning", "In today's world", "plays a crucial/pivotal role".
- Overused connectives: stop leaning on "Moreover", "Furthermore", "Additionally", "Notably", "In conclusion". Use natural transitions or none.
- Buzzwords: "delve", "leverage", "underscore", "tapestry", "realm", "robust" (as filler), "showcase", "pivotal", "garner".
- Formulaic shapes: tricolons everywhere ("X, Y, and Z"), "Not only… but also", uniform 4-sentence paragraphs, every section ending with a forward-looking summary sentence.
- Mechanical hedging on every clause; over-symmetrical structure; restating the headline number as the first words of multiple sections.

================================================================
CRITICAL INTEGRITY RULES — these override everything; violating any one invalidates the paper
================================================================
1. Use ONLY the numbers and facts in the DATA block. Invent NOTHING — no extra numbers, p-values, datasets, or results.
2. The held-out TEST SET (214 structures) was NEVER evaluated. Never state, imply, or hint at any test-set performance or generalization result.
3. macro-AUPRC is the primary metric. AUROC is INFLATED at ~4.6% prevalence — say so; do not lead with AUROC.
4. NO "validated", "confirmed", "discovered", "proven", or "druggable" pocket/site. Use "candidate pocket-associated residues", "computationally predicted", "requires further validation".
5. The MD is a 25 ns EXPLORATORY run on 1AXC. Candidates remained RIGID and did NOT open — report this as a valid NEGATIVE/INCONCLUSIVE result. NEVER write the pocket opened, that MD "validated" anything, or that binding occurred. The run is 25 ns — never inflate it (no 100 ns, no 900 ns).
6. The edge ablation shows the sequential-edge contribution is NOT established (no-sequential is within 1 SD). State honestly; don't claim the full architecture is required.
7. Cite ONLY from the REFERENCES list, as [n]. No fabricated citations.
8. The honesty (reserved test set, AUPRC-over-AUROC, reported negative MD) IS the strength — frame it that way, not apologetically.

================================================================
DATA (real, frozen) — the only results you may state
================================================================
PROJECT: A leakage-controlled graph neural network that predicts, at the residue level, candidate cryptic-pocket-associated residues in PCNA (Proliferating Cell Nuclear Antigen), a cancer-relevant DNA-replication sliding-clamp protein.

DATASET & SPLIT:
- 1,101 labelled structures; positive-unlabeled labelling; 16,335 positive residues, 3,704 masked (excluded from the loss).
- Positive prevalence among evaluated residues ≈ 4.5%.
- Split FROZEN (manifest hash 24dd5e34), homology-blocked at 30% sequence identity; PCNA cluster held out entirely; test set = 214 structures, NEVER evaluated during model selection.

MODEL (primary):
- GraphSAGE-3L: hidden_dim 128, dropout 0.1, lr 0.001, pos_weight ≈ 21.0.
- Node features = 25 structural features + ESM2 per-residue embeddings.
- 12 runs = 4 cross-validation folds × 3 seeds, early stopping (patience 10).

VALIDATION RESULTS (validation folds only — NO test results exist):
- Primary GraphSAGE-3L: macro-AUPRC 0.1876 ± 0.0113; per-fold means fold0 0.173, fold1 0.2035, fold2 0.1872, fold3 0.1865; best single run 0.2042; mean macro-AUROC 0.661.
- Baselines (same split): SAGE-3L no-sequential 0.1897 ± 0.0089; GAT-2L 0.1739 ± 0.0090; GCN-1L 0.1601 ± 0.0089; Degree/exposure 0.0813; Random 0.0861 ± 0.0011.
- Ablation: full 0.1876 ± 0.0113; no-sequential 0.1897 ± 0.0089 (Δ +0.0021, within 1 SD — sequential value NOT established); no-spatial 0.1556 ± 0.0114 (spatial edges carry the signal).
- External baselines (fpocket, P2Rank, PocketMiner): NOT yet run.
- A random scorer reaches macro-AUROC ≈ 0.50 but macro-AUPRC ≈ 0.05 (≈ prevalence) — why AUROC overstates skill and AUPRC is primary.

MOLECULAR DYNAMICS (Phase-5 exploratory triage — REAL):
- System: human PCNA homotrimer 1AXC (apo-from-p21; p21 peptide removed). OpenMM 8.2, AMBER14, TIP3P, ~287,000 atoms.
- Sampling: effective n = 1. replicate_01 = full 25 ns (250 frames @ 0.1 ns); replicate_02 incomplete (killed at budget wall); no 8GLA holo positive control. First 5 ns discarded as equilibration (200 frames analyzed).
- Analysis correction: original analysis corrupted by missing periodic-boundary imaging (impossible RMSD ~2.5 nm); re-run with image_molecules before superposition, core alignment EXCLUDING the measured windows (no circularity), RMSF about the mean. Simulation stable (PE flat ~ −2.68M kJ/mol, T = 300 K, ρ = 1.01 g/mL).
- Stability (replicate_01): backbone Cα RMSD mean 0.255 nm, max 0.305 nm, final 0.287 nm — flat plateau, stable trimer.
- Per-window Cα RMSF (nm), ratio vs IDCL/PIP reference 118–122:
    • 239–243 (novel candidate A): 0.081 (0.65×)
    • 28–32   (novel candidate B): 0.081 (0.65×)
    • 206–210 (novel candidate C): 0.074 (0.59×)
    • 134–138 (IDCL-adjacent control): 0.084 (0.67×)
    • 118–122 (IDCL/PIP reference): 0.126 (1.00×)
- Opening check (SASA + mouth-distance proxies; 3 monomers as informal triplicates): NO sustained opening; novel candidates only transient SASA excursions (~18–26%, 2–7 of 200 frames, return to baseline); front-face PIP pocket essentially static; only sustained widening was the IDCL (134–138, expected loop motion).
- RESULT: candidate pockets (239–243, 28–32, 206–210) remained RIGID and did NOT open; PIP pocket did not reopen after p21 removal; flexibility confined to the known IDCL. Valid NEGATIVE/INCONCLUSIVE result (NOT falsification): 25 ns / n=1 / no positive control cannot sample ns–µs cryptic events. No druggability/validated-site/novel-site claims supported.

================================================================
FIGURES — already generated; insert  ![Figure N](paper/figures/<id>.png)  then  *Figure N. <caption>.*  Number in order of appearance.
================================================================
- dataset_split — dataset composition & frozen split (folds + held-out test; positive vs masked). [METHODS]
- metric_choice — why macro-AUPRC not AUROC at ~4.6% prevalence. [METHODS]
- baseline_comparison — validation macro-AUPRC, primary vs all baselines, same split. [RESULTS]
- per_fold_performance — per-fold macro-AUPRC (fold 1 easier). [RESULTS]
- ablation_edges — edge-type ablation (spatial carries signal; sequential not established). [RESULTS]
- training_curves — validation macro-AUPRC vs epoch, 12 runs + mean. [RESULTS]
- md_rmsd — backbone RMSD vs time, 25 ns, stable plateau. [MD TRIAGE]
- md_rmsf — per-window RMSF, candidates 0.59–0.67× the reference (not more flexible). [MD TRIAGE]

================================================================
REFERENCES — cite ONLY these, as [n]; reproduce verbatim at the end
================================================================
[1] Gamouh H, Novotný M, Hoksza D (2025). Hybrid protein–ligand binding residue prediction with protein language models: does the structure matter? doi:10.1093/bioinformatics/btaf431
[2] Vats S et al. (2023). AlphaFold-SFA: accelerated sampling of cryptic pocket opening, protein–ligand binding and allostery. doi:10.1101/2023.11.21.568098
[3] Martinez-Rosell G et al. (2020). PlayMolecule CrypticScout: Predicting Protein Cryptic Sites Using Mixed-Solvent Molecular Simulations. doi:10.1021/acs.jcim.9b01209
[4] Vats S et al. (2024). AlphaFold-SFA (journal version). doi:10.1371/journal.pone.0307226
[5] Mukhopadhyay S, Chakrabarty S (2026). Mapping PPI Hotspots and a Cryptic Allosteric Pocket in PLK1 PBD via Mixed-Solvent MD. doi:10.1002/cphc.202500907
[6] Chen SH, Lupo Pasini M, Hauck CD (2025). Enhancing Protein Binding Site Residue Prediction with Graph Neural Networks. doi:10.1101/2025.08.25.672254
[7] Liu Y et al. (2024). mTOR variants activation discovers a PI3K-like cryptic pocket. doi:10.1101/2024.10.12.618044
[8] O'Connor S et al. (2022). Discovery and Characterization of a Cryptic Secondary Binding Site in HSP70. doi:10.3390/molecules27030817
[9] Vottero P et al. (2025). Molecular simulations of paclitaxel binding to mutant β-tubulin. doi:10.1007/s10822-025-00716-y
[10] Liu Y (2024). Protein-DNA Binding Residue Prediction and Consistent Interpretability with Deep Learning. doi:10.1101/2024.10.12.613667
[11] Marfoglia M, Guirardel L, Barth P (2024). AlloPool: An Adaptive GNN for Dynamic Allosteric Network Prediction. doi:10.1101/2024.11.01.621466
[12] Sargsyan K (2025). Protein Language Model Embeddings Distinguish Catalytic from Structural Zinc-Binding Sites. doi:10.26434/chemrxiv-2025-sfn7n
[13] Shakeel H (2025). Structure-Based Discovery of a Cryptic Druggable Pocket in TP53 C238Y. doi:10.26434/chemrxiv-2025-29bnr
[14] Oleinikovas V et al. (2016). Understanding Cryptic Pocket Formation by Enhanced Sampling Simulations. doi:10.1021/jacs.6b05425
[15] Meller A et al. (2023). Predicting locations of cryptic pockets with the PocketMiner GNN. doi:10.1038/s41467-023-36699-3
[16] Beglov D et al. (2018). Exploring the structural origins of cryptic sites on proteins. doi:10.1073/pnas.1711490115
[17] Hart KM et al. (2017). Designing small molecules to target cryptic pockets. doi:10.1371/journal.pone.0178678
[18] Comitani F, Gervasio FL (2018). Exploring Cryptic Pocket Formation with SWISH. doi:10.1021/acs.jctc.8b00263

================================================================
STRUCTURE — write every section IN FULL; hit the word counts; ~10 pages
================================================================
Title: "Leakage-Controlled Graph Neural Networks for Residue-Level Cryptic-Pocket Prediction in PCNA" (subtitle: "An honestly-evaluated computational pipeline"). Author: Advay. Date: 2026-05-30.
Throughline (state it in the intro): Can a leakage-clean GNN highlight candidate cryptic-pocket residues in PCNA and be evaluated honestly enough to survive scrutiny?

- Abstract (~210 w): relevance, gap, the GNN, validation macro-AUPRC vs baselines, test set reserved, the 25 ns MD triage found candidates rigid (negative/inconclusive), close on the honest contribution.
- 1. Introduction (~470 w): PCNA biology & "undruggability"; cryptic pockets + AOH1996 precedent; the leakage/prediction gap; the contribution. State the throughline.
- 2. Background and Related Work (~470 w): detection methods (CryptoSite, PocketMiner [15], fpocket/P2Rank, CrypticScout [3], AlphaFold-SFA [2], SWISH [18]); GNNs + ESM2 [6,11,12]; the leakage problem and AUPRC-over-AUROC.
- 3. Methods (~600 w): dataset/labels; frozen homology-blocked split (hash 24dd5e34, PCNA held out, 214 reserved); features; GraphSAGE-3L + training; evaluation (macro-AUPRC rationale); MD setup (1AXC apo-from-p21, ~287k atoms, 25 ns, PBC-corrected, SASA/mouth-distance proxies). Figures: dataset_split, metric_choice.
- 4. Results (~520 w): macro-AUPRC vs baselines + ablation; fold consistency; honest ablation. Validation only. Figures: baseline_comparison, per_fold_performance, ablation_edges, training_curves.
- 5. Molecular-Dynamics Triage (~460 w): system+sampling (incl. PBC-correction story); stability (~0.255 nm); the finding (candidates 0.59–0.65× ref, only transient SASA, rigid, did NOT open; IDCL moved as expected); valid negative/inconclusive. Figures: md_rmsd, md_rmsf.
- 6. Discussion (~520 w): what candidates do/don't mean; reconcile predictions with the negative MD; why this honest stance is sound.
- 7. Limitations (~380 w): validation-only; modest AUPRC; sequential-edge unestablished; external baselines not run; MD limits (25 ns, n=1, single structure, apo-from-p21, no 8GLA control, SASA proxies, monomers not independent).
- 8. Conclusion and Future Work (~320 w): the honest contribution; next steps (human-gated one-shot test eval, external baselines, longer/enhanced-sampling MD with 8GLA positive control, PCNA-specific inference).
- References: reproduce verbatim.
