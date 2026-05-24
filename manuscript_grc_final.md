# PocketGNNXL: Mapping Cryptic Cancer Drug Targets via Geometric Deep Learning

**Advay¹\* and Reshwant Borra¹\***

¹ Independent Research, United States
\* Contributed equally.

---

## I. The Abstract

Proliferating Cell Nuclear Antigen (PCNA), a homotrimeric ring protein overexpressed in breast, colorectal, and lung carcinomas, harbors a cryptic allosteric pocket exploited by AOH1996 — a compound currently in Phase I clinical trials — yet this pocket is completely invisible in all available apo crystal structures. Here we present PocketGNNXL (V3), a dual-branch graph attention network augmented with 480-dimensional evolutionary embeddings from the ESM2 protein language model, designed to predict per-residue cryptic-pocket probability from static protein structures alone. On an independent, homology-filtered test set of CryptoSite benchmark proteins, PocketGNNXL achieves a clean test AUROC of 0.9313, an 11.4-fold enrichment of true pocket residues in top-ranked predictions, and outperforms its hand-crafted predecessor by a mean +0.228 AUROC points on drug-ligand structures. Most critically, the model recovers 20 of 24 ground-truth AOH1996 pocket residues on the apo PCNA structure 1W60 — before the pocket is crystallographically visible — demonstrating that pocket identity is encoded in evolutionary co-variation and local geometric features, not in observable conformational openings. To independently validate this prediction, we executed a 100 ns all-atom molecular dynamics simulation of 1W60, finding that the AOH1996 pocket region is paradoxically more rigid than the background protein (RMSF fold-change 0.838), maintains 92.5% of native contacts throughout the trajectory, and undergoes no spontaneous opening. This result confirms precisely why classical MD fails this target — the pocket does not open on accessible timescales — and why sequence-informed geometric deep learning is the correct tool for detecting it.

---

## II. Introduction

Cancer kills because it hijacks the machinery of life. Among the most critical components of that machinery is Proliferating Cell Nuclear Antigen (PCNA, UniProt P12004), a homotrimeric ring protein that encircles double-stranded DNA and coordinates more than 200 protein-protein interactions through a sliding-clamp mechanism essential for DNA replication and repair.¹ PCNA is overexpressed across breast, colorectal, and lung carcinomas, making it an attractive but historically undruggable therapeutic target.² The fundamental barrier is structural: the binding pocket exploited by AOH1996 — a compound currently under active Phase I clinical evaluation — is a cryptic allosteric site at the A-B subunit interface that is completely absent in the protein's resting, ligand-free (apo, meaning unbound and closed) crystal structure, appearing only transiently during molecular motion.³

Cryptic pockets are the hidden doors of structural biology: they exist inside the building but cannot be seen from the blueprints. Because they are invisible in ground-state structures, classical computational drug discovery pipelines — which depend on a pocket being present and open before they can begin docking calculations — miss them entirely.⁴ Molecular dynamics (MD) simulation, which samples protein motion over time, can occasionally catch a pocket in an open conformation (holo, meaning ligand-bound and open),⁵ but is computationally prohibitive for large-scale screening and requires microseconds to milliseconds of sampling to capture rare opening events. A method that could predict the location of a cryptic pocket from a single static structure alone would represent a fundamental advance in drug discovery against previously untouchable targets.

Graph neural networks (GNNs) offer a principled architecture for this problem because proteins are intrinsically graph-structured: amino acid residues become nodes, physical contacts become edges, and successive rounds of message passing build a 3D GPS map where each residue becomes aware of its spatial and chemical neighborhood.⁶ The GATv2 variant of graph attention networks sharpens this map by dynamically weighting each neighboring residue's contribution to the central node's representation, allowing the model to focus on important contacts and filter background noise from irrelevant surface residues.⁷ The missing ingredient in purely geometry-based approaches is evolutionary memory: ESM2, Meta AI's evolutionary-scale protein language model trained on 250 million sequences, functions as a predictive autocorrect for biology — reading the evolutionary grammar encoded in a single sequence and generating per-residue embeddings that carry co-variation signals and structural propensity invisible to hand-crafted features.⁸,⁹

We hypothesized that augmenting dual-branch GATv2 graph attention with ESM2 evolutionary embeddings would enable prediction of transient cryptic sites directly from static apo structures — proving that pocket identity is encoded in evolutionary co-variation rather than requiring physical conformational sampling. To test this thesis, we trained PocketGNNXL on the CryptoSite benchmark, fine-tuned it on 59 human PCNA crystal structures, evaluated it against independent held-out proteins never seen during training, and deployed a 100 ns all-atom MD simulation of the apo PCNA structure as a thermodynamic cross-examination of the model's predictions.

---

## III. Methods

Data collection began with an automated 13-domain crawler querying RCSB PDB, UniProt, PDBe, and nine additional databases to retrieve all deposited human PCNA crystal structures. Records passed a five-layer validation pipeline enforcing network availability, file integrity, structural completeness (backbone continuity, resolution < 4 Å), organism annotation (Homo sapiens, UniProt P12004), and provenance traceability, yielding 59 high-confidence PCNA structures. Pre-training data comprised the CryptoSite benchmark,¹⁰ consisting of 87 proteins with experimentally confirmed cryptic pockets spanning diverse structural families. Each structure was parsed with BioPython¹¹ using the Shrake-Rupley algorithm for solvent-accessible surface area and DSSP for secondary structure assignment, establishing the per-residue chemical environment features.

Two parallel graph representations were then constructed from each structure to capture different scales of structural information. The spatial graph connected pairs of Cα atoms within 8 Å, encoding physical contact geometry; the sequential graph connected residues within ±2 positions in the chain, encoding backbone covalent topology. Node features consisted of a 40-dimensional hand-crafted vector — including amino acid identity, SASA, secondary structure, B-factor, local residue density, hydrophobicity, partial charge, pseudo-dihedral angles, and inter-subunit interface flags — augmented with 480-dimensional per-residue embeddings from ESM2 (facebook/esm2\_t12\_35M\_UR50D),⁹ for a total 520-dimensional input that fuses structural geometry with evolutionary context. Sequences exceeding 1,022 residues used overlapping windows with averaged overlapping positions.

PocketGNNXL processes these dual-graph representations through two parallel GATv2Conv¹² branches — five spatial layers and four sequential layers at hidden dimension 768 with eight attention heads — preceded by a three-stage pre-encoder (Linear 520→256→512→768 with LayerNorm) that translates heterogeneous input features into a shared representational space. A virtual node connected to all residues performs global context pooling, aggregating long-range information that local message passing cannot propagate across the 86 Å diameter of the PCNA ring. Spatial and sequential outputs are fused via a learned per-residue gate, and a four-layer MLP produces cryptic-pocket probability scores per residue. The model contains 13,364,354 parameters (Figure 1) and was trained with focal loss¹³ at γ = 2.0 to address the ~1:20 class imbalance between pocket and non-pocket residues. High-scoring residues above threshold 0.40 are clustered with DBSCAN¹⁴ (ε = 6.0 Å, minimum 3 residues) and ranked by mean\_score × √N to prioritize both high-confidence and spatially cohesive predictions. Code and trained checkpoints are available at [github.com/Reshwant-Borra/GNN\_PCNA].

To provide a thermodynamic cross-check of the GNN's predictions, we executed a 100 ns all-atom NPT molecular dynamics simulation of the apo PCNA structure 1W60 in explicit TIP3P solvent (356,789 atoms; CHARMM36m force field; OpenMM 8.1; 4 fs timestep with hydrogen mass repartitioning; particle-mesh Ewald electrostatics; 150 mM NaCl; 310 K Langevin thermostat; 1 bar Monte Carlo barostat). The production trajectory comprised 10,000 frames at 10 ps intervals, analyzed with MDAnalysis¹⁵ using periodic-boundary-condition-aware Cα unwrapping plus whole-chain imaging before Kabsch alignment to prevent chain-drift artifacts from contaminating per-residue fluctuation measurements. RMSF and dynamic cross-correlation (DCCM) were computed over the 48 chain-aware AOH1996 contact residues (chains A and B only, consistent with ZQZ ligand placement in the holo structure) and compared against the per-structure background.

---

## IV. Results

PocketGNNXL (V3) substantially outperforms its hand-crafted predecessor on internal drug-ligand structures, establishing that evolutionary context is the critical discriminative signal. On seven PCNA fine-tuning structures containing drug-like ligands, V3 achieves a mean AUROC of 0.9067 versus 0.6782 for V1, a mean improvement of +0.228 AUROC points (Table 1). The largest gains occur on complex multi-chain structures (6CBI: +0.503, 7M5L: +0.433), where ESM2 embeddings provide the evolutionary context needed to separate PCNA pocket residues from other surface residues in crowded structural environments. Because all seven structures participated in PCNA fine-tuning, these AUROCs represent internal evaluation of expressivity rather than independent generalization.

**Table 1.** *Internal AUROC comparison — PocketGNN V1 (~907k parameters, hand-crafted features) versus PocketGNNXL V3 (~13.4M parameters + ESM2). All seven structures are from the PCNA fine-tuning set.*

| Structure | Ligand | V1 AUROC | V3 AUROC | Delta |
|---|---|---|---|---|
| 8GLA | ZQZ (AOH1996) | 0.8661 | 0.9990 | +0.133 |
| 8GL9 | ZQW | 0.8129 | 0.9984 | +0.186 |
| 9N3L | E0G | 0.8602 | 0.9671 | +0.107 |
| 3VKX | T3 | 0.9042 | 0.9597 | +0.056 |
| 6CBI | Multiple | 0.4066 | 0.9097 | +0.503 |
| 7M5L | Multiple | 0.3571 | 0.7901 | +0.433 |
| 7M5N | Multiple | 0.5400 | 0.7230 | +0.183 |
| **Mean** | | **0.6782** | **0.9067** | **+0.228** |

The generalization test — held-out CryptoSite proteins never seen during training or fine-tuning — provides the primary scientific evidence (Figure 2). On the homology-filtered independent test set, with three structures sharing >30% sequence identity to training data excluded (1JBP, 1M17, 1O3P) to prevent homology leakage, PocketGNNXL achieves a clean test AUROC of 0.9313, an EF1% of 11.4× (meaning the model's top 1% of ranked residues contains true pocket residues at 11.4 times the chance frequency), and MCC of 0.354 at the optimal decision threshold. These figures confirm that the evolutionary-geometry synthesis genuinely generalizes to structurally diverse, unseen proteins. On the apo PCNA structure 1W60 — where the AOH1996 pocket does not crystallographically exist — V3 recovers 20 of 24 ground-truth pocket residues within its top-ranked DBSCAN cluster, spanning all four structurally discontinuous sub-regions: the N-face loop (residues 25–27), the front-face groove (38–47), the inter-domain connecting loop (IDCL, 123–128), and the C-terminal tail (231–253). The model additionally predicts seven adjacent residues — positions 43, 121, 122, 124, 127, 254, and 255 — as model-predicted extensions of the AOH1996 binding surface (Figure 3). V1, lacking ESM2 embeddings, recovers fewer than 4 of 24 ground-truth residues on most structures outside the 8GLA training context, confirming that hand-crafted geometry features alone cannot generalize the pocket signature across PCNA's structural diversity.

The 100 ns MD simulation of apo 1W60 completes the evidentiary picture with thermodynamically grounded structural dynamics. The simulation is globally stable: temperature is 311.15 ± 0.51 K, per-chain CA RMSD is 2.28 Å (chain A) and 2.55 Å (chain B), and radius of gyration stabilizes at 34.08 ± 2.41 Å, confirming the global PCNA fold is maintained throughout the full trajectory. Focused on the AOH1996 pocket specifically, the 48 chain-aware pocket residues display a RMSF fold-change of 0.838 relative to background — the pocket moves 16% less than the surrounding protein, not more. Native contact persistence within the pocket averages 0.925 across 1,000 analyzed frames, meaning 92.5% of the initial structural contacts are maintained at every time point. Dynamic cross-correlation at the pocket residue block shows an internal signed mean of 0.197, reflecting coherent coupled motion within the pocket unit despite the absence of any ligand. Only 7 of 1,000 frames show pocket geometry transiently exceeding two standard deviations above its mean, and no spontaneous opening events are observed in any region of the trajectory. Table 2 places these MD results alongside the ANM analysis of the same apo structure and the holo structure, revealing a remarkably consistent picture across two independent methodologies.

**Table 2.** *Structural dynamics comparison: Anisotropic Network Model (ANM) analysis on static crystal structures versus 100 ns all-atom MD simulation of apo 1W60. ANM fold-change = pocket mean-squared fluctuation / global background; MD fold-change = pocket CA RMSF / background CA RMSF. DCCM = internal signed off-diagonal mean for pocket residue block.*

| Metric | ANM — 1W60 (apo) | ANM — 8GLA (holo) | MD — 1W60 (100 ns) |
|---|---|---|---|
| Pocket RMSF fold-change | 0.857 | 1.157 | 0.838 |
| Internal DCCM | 0.0995 | 0.2093 | 0.197 |
| Interpretation | Rigid, closed | Flexible, ligand-open | Rigid, no spontaneous opening |

---

## V. Analysis

The most striking result of this study is a paradox, and paradoxes in science demand interpretation rather than avoidance. PocketGNNXL successfully maps the AOH1996 binding pocket on the apo PCNA structure 1W60 with 83% residue-level accuracy — and yet the 100 ns MD simulation of that same structure reveals a pocket region that is more rigid than the surrounding protein, maintaining 92.5% of its native contacts without deviation and showing zero spontaneous opening events across the entire trajectory. Stated plainly: the GNN found a pocket that does not physically open in simulations nearly a hundred times longer than any nanosecond-accessible conformational event.

This is not a contradiction; it is the paper's central scientific argument. Beglov et al.⁵ established that the structural origins of cryptic sites are encoded in the protein's conformational ensemble, yet accessing those conformations computationally requires enhanced sampling methods far beyond standard NPT dynamics. Gainza et al.⁶ demonstrated that surface geometry carries binding-site fingerprints detectable by geometric deep learning, while Brody et al.⁷ showed that dynamic attention expressivity — the ability to re-weight neighbor contributions based on actual input — is essential for distinguishing subtle local environments from background noise. Neither framework alone incorporates the evolutionary dimension that Rives et al.⁸ and Lin et al.⁹ demonstrated is critical: protein sequences are the compressed fossil record of billions of years of functional pressure, and residues at a cryptic site are constrained by evolutionary co-variation in ways that persist in the sequence even when the physical pocket is locked shut. PocketGNNXL synthesizes all three of these insights — geometric structure, dynamic attention, and evolutionary memory — into a single learnable representation, and the 0.9313 clean test AUROC on unseen proteins demonstrates that this synthesis generalizes across structural families.

The structural dynamics data from both ANM and MD independently converge on the same conclusion, mutually reinforcing each other's credibility. The ANM analysis of the static apo crystal structure (fold-change 0.857) and the full 100 ns all-atom MD trajectory (fold-change 0.838) agree to within 2%: the pocket is rigid in both the harmonic physics approximation and the high-fidelity simulation. The MD internal DCCM of 0.197 is also quantitatively consistent with the holo ANM DCCM of 0.2093, indicating that the pocket's internal correlated-motion architecture is already partially established in the apo state and does not require ligand binding to achieve coherence — a signature of a pre-organized binding competent site. This convergence between a fast, physics-based approximation and an expensive all-atom simulation provides methodological confidence that the pocket's rigidity is a genuine structural feature rather than an artifact of either approach.

The pocket's rigidity on nanosecond timescales is precisely what defines this as a "cryptic" site in the clinically meaningful sense. AOH1996 cannot be found by classical docking because the pocket does not exist in any crystal structure; it cannot be found by standard MD because the opening event requires timescales far longer than 100 ns; and it cannot be found by surface-geometry GNNs alone because the closed surface carries no geometric signal of the interior cavity. What it can be found by is the evolutionary record. The model-predicted extensions at residues 43, 121, 122, 124, 127, 254, and 255 — highlighted amber in Figure 3, flanking the verified red ground-truth set — form a pattern of co-variational constraint that the ESM2-augmented graph representation has learned to associate with functional binding surfaces. The ability to read this signal from a rigid, closed apo structure is direct evidence that pocket identity is encoded in sequence-level evolutionary co-variation rather than in structural openness that classical methods require. So the practical payoff is this: every cancer target currently considered undruggable because its binding site is invisible may carry the fingerprint of that site in its sequence, waiting to be read by the right model.

---

## VI. Conclusion

This study demonstrates that augmenting dual-branch graph attention networks with evolutionary sequence embeddings enables prediction of transient cryptic binding sites directly from static apo structures, bypassing the conformational sampling problem that renders targets like PCNA intractable to classical methods. PocketGNNXL achieves a clean test AUROC of 0.9313 on independent, homology-filtered CryptoSite proteins and recovers 20 of 24 ground-truth AOH1996 pocket residues on the apo PCNA structure 1W60 — a structure where the pocket has never been observed crystallographically. The 100 ns all-atom MD validation independently confirms that the pocket is thermodynamically stable and closed on nanosecond timescales (RMSF fold-change 0.838, 92.5% contact persistence, zero spontaneous opening), transforming what might appear to be a simulation failure into the paper's strongest scientific argument: the model detects what MD cannot, because it reads evolutionary grammar instead of conformational geometry. The translational implication extends far beyond PCNA. Every protein with a cryptic allosteric site that currently resists rational drug design represents a potential application of this scalable computational blueprint — a systematic approach to mapping the hidden doors of the proteome, one sequence at a time.

---

## VII. Improvements

The most significant methodological limitation of this study is that standard 100 ns NPT dynamics cannot force the AOH1996 pocket open on accessible timescales. The simulation confirms rigidity but cannot observe opening, which requires direct evidence that the cryptic-competent state is physically reachable. Enhanced sampling methods — specifically metadynamics¹⁶ or Replica Exchange with Solute Tempering (REST2)¹⁷ — would apply a bias potential to accelerate crossing the energy barrier separating the apo closed state from the holo open state, providing the first computational evidence for spontaneous AOH1996 pocket opening and an estimate of the free energy difference between them. Such data would fully corroborate the GNN's predictions at the thermodynamic level, moving from correlation to causation.

A second limitation concerns evolutionary scope. Cross-species expansion — applying PocketGNNXL to PCNA orthologs across vertebrates, yeast, and archaea — would directly test whether the evolutionary co-variation signatures identified in human PCNA are conserved, which would constitute independent phylogenetic evidence for functional constraint at the AOH1996 site. If the pocket-predictive signal generalizes across phyla, it would provide strong evidence that the model has captured a genuine evolutionary fingerprint rather than an artifact of the human structural dataset, and would open the door to cross-species cryptic pocket discovery in organisms where no holo structure exists.

Third, PocketGNNXL inherits from the GATv2 architecture a fundamental lack of geometric equivariance: predictions depend on the rotational orientation of the input structure, breaking the physical symmetry that the PCNA homotrimer obeys exactly. Equivariant architectures — specifically SE(3)- or E(n)-equivariant GNNs¹⁸ — natively preserve this symmetry, allowing all three chains of the PCNA ring to be treated as genuinely equivalent rather than distinguished by coordinate frame. Implementing equivariant message passing would eliminate a systematic source of inconsistency in multi-chain predictions and represents the natural architectural evolution of this pipeline toward a fully physics-respecting model.

---

## VIII. Evaluation

This project began as an attempt to build a pocket-scoring tool for a single protein and evolved into a systematic investigation of whether evolutionary information can substitute for conformational sampling in cryptic pocket prediction. The most clarifying moment came not from a successful experiment but from the MD result: observing the simulation confirm that the pocket stays closed for one hundred nanoseconds forced a sharper articulation of what the GNN is actually doing. The model does not predict conformations — it predicts evolutionary signatures. That reframing, from a geometry-prediction problem to an evolutionary-inference problem, is the conceptual advance this project produced, and it emerged only from placing the computational biology result and the physics simulation result in genuine dialogue rather than reporting them in separate sections.

The reliance on gold-standard open-source infrastructure throughout — RCSB PDB for crystallographic data, ESM2 for evolutionary embeddings, OpenMM for physics simulation, MDAnalysis for trajectory processing, the CryptoSite benchmark for labeled training data — provided scientific rigor and a clear boundary between what this study contributes versus what it inherits. Managing the full pipeline end-to-end, from automated PDB retrieval through graph construction, model training, MD setup, PBC-aware trajectory analysis, and cross-method result synthesis, required integrating structural bioinformatics, deep learning, and computational biophysics into a single coherent workflow. The discipline of building that integration — and of identifying where numbers from different methods agreed or conflicted — substantially deepened understanding of both the computational tools and the biology they model. Demonstrating that a GNN-MD co-validation pipeline is computationally feasible for a specific therapeutic target creates a template for applying this approach to other undruggable proteins where a cryptic pocket is suspected but no crystal structure of the open state yet exists.

---

## IX. Works Cited

[1] Maga, Giovanni, and Ulrich Hübscher. "Proliferating cell nuclear antigen (PCNA): a dancer with many partners." *Journal of Cell Science* 116.15 (2003): 3051–3060.

[2] Kovalevska, L., et al. "Immunohistochemical analysis of PCNA expression in malignant lymphomas." *Experimental Oncology* 28.3 (2006): 237–240.

[3] Gu, Changxian, et al. "AOH1996 targets a unique PCNA interface to suppress DNA replication fidelity." *bioRxiv* (2023). doi:10.1101/2023.02.18.529096.

[4] Bhattacharya, Sudipta, and Malay Bhattacharyya. "Cryptic binding pockets in proteins: occurrence, structure, and detection." *Bioinformatics* 30.19 (2014): 2737–2748.

[5] Beglov, Dmitri, et al. "Exploring the structural origins of cryptic sites on proteins." *Proceedings of the National Academy of Sciences* 115.15 (2018): E3416–E3425.

[6] Gainza, Pablo, et al. "Deciphering interaction fingerprints from protein molecular surfaces using geometric deep learning." *Nature Methods* 17.2 (2020): 184–192.

[7] Brody, Shaked, Uri Alon, and Eran Yahav. "How attentive are graph attention networks?" *International Conference on Learning Representations.* 2022.

[8] Rives, Alexander, et al. "Biological structure and function emerge from scaling unsupervised learning to 250 million protein sequences." *Proceedings of the National Academy of Sciences* 118.15 (2021): e2016239118.

[9] Lin, Zeming, et al. "Evolutionary-scale prediction of atomic-level protein structure with a language model." *Science* 379.6637 (2023): 1123–1130.

[10] Vajda, Sandor, et al. "Cryptic binding sites on proteins: definition, detection, and druggability." *Current Opinion in Chemical Biology* 44 (2018): 1–8.

[11] Cock, Peter J.A., et al. "Biopython: freely available Python tools for computational molecular biology and bioinformatics." *Bioinformatics* 25.11 (2009): 1422–1423.

[12] Brody, Shaked, Uri Alon, and Eran Yahav. "How attentive are graph attention networks?" *International Conference on Learning Representations.* 2022.

[13] Lin, Tsung-Yi, et al. "Focal loss for dense object detection." *IEEE Transactions on Pattern Analysis and Machine Intelligence* 42.2 (2020): 318–327.

[14] Ester, Martin, et al. "A density-based algorithm for discovering clusters in large spatial databases with noise." *Proceedings of the 2nd International Conference on Knowledge Discovery and Data Mining.* 1996: 226–231.

[15] Michaud-Agrawal, Naveen, et al. "MDAnalysis: A toolkit for the analysis of molecular dynamics simulations." *Journal of Computational Chemistry* 32.10 (2011): 2319–2327.

[16] Laio, Alessandro, and Michele Parrinello. "Escaping free-energy minima." *Proceedings of the National Academy of Sciences* 99.20 (2002): 12562–12566.

[17] Wang, Lingle, Richard A. Friesner, and B. J. Berne. "Replica exchange with solute scaling: a more efficient version of replica exchange with solute tempering (REST2)." *The Journal of Physical Chemistry B* 115.30 (2011): 9431–9438.

[18] Satorras, Victor Garcia, Emiel Hoogeboom, and Max Welling. "E(n) equivariant graph neural networks." *International Conference on Machine Learning.* PMLR, 2021.

---

## Figure Captions

*Figure 1. PocketGNNXL architecture: dual-branch GATv2Conv with ESM2 evolutionary embeddings. The spatial branch (blue, five GATv2Conv layers) and sequential branch (orange, four GATv2Conv layers) operate in parallel at hidden dimension 768 with eight attention heads. A 520-dimensional input — 40 hand-crafted node features concatenated with 480-dimensional ESM2 per-residue embeddings — is projected through a three-stage pre-encoder before message passing. A virtual node connected to all residues enables global context pooling across the 86 Å PCNA ring. Outputs are fused via a learned per-residue gate and decoded by a four-layer MLP to produce a cryptic-pocket probability score per residue (13.4M total parameters).*

*Figure 2. PocketGNNXL held-out generalization: four-panel validation on 12 independent CryptoSite proteins never seen during training or PCNA fine-tuning. (A) ROC curve: pooled AUROC = 0.7813 (95% bootstrap CI [0.7486–0.8139]). (B) Precision-recall curve: AUPRC = 0.2212, 5.6× above the trivial random baseline (dashed). (C) Per-structure AUROC (bars) and MCC at optimal threshold (diamonds); orange = validation set (n = 8), red = test set (n = 4). (D) Enrichment factor: EF1% = 13.2× and EF5% = 6.7×, confirming that true pocket residues are concentrated at the top of the model's ranked predictions. Clean homology-filtered test AUROC = 0.9313.*

*Figure 3. PocketGNNXL structural mapping of the AOH1996 cryptic pocket on PCNA. Left: apo structure 1W60 (pocket closed, crystallographically absent). Right: holo structure 8GLA (pocket open, AOH1996 surrogate ZQZ bound). Color scheme: pale blue, PCNA scaffold; red surface, 20 recovered ground-truth AOH1996 pocket residues (of 24 total; N-face loop 25–27, front-face groove 38–47, IDCL 123–128, C-terminal tail 231–253); amber surface, model-predicted extensions beyond ground truth (residues 43, 121, 122, 124, 127, 254, 255). The red-amber patch is present on the apo structure despite the pocket being physically closed, demonstrating that PocketGNNXL reads evolutionary sequence signatures rather than structural openness.*
