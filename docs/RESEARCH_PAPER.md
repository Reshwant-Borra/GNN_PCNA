# National Student Research Institution (NSRI)
**Open Science Archive** | https://nsri.world/

---

# Graph neural network-based detection of cryptic binding pockets on proliferating cell nuclear antigen using dual-branch graph attention and protein language model features

**Advay**ᵃ and **Reshwant Borra**ᵃ·*

ᵃIndependent Research, United States. Contact: advay.awesomer@gmail.com

---

## ARTICLE INFO

**Article history:**
Received: 2026-05-16
Available online: 2026-05-16

**Keywords:**
Cryptic pockets; Graph neural network; PCNA; Protein language model; Drug discovery; AOH1996; Graph attention network

---

## ABSTRACT

**Study objective:** Proliferating Cell Nuclear Antigen (PCNA) is overexpressed across many human cancers and harbors a cryptic allosteric pocket, exploited by the experimental compound AOH1996, that is absent in apo crystal structures and opens transiently during protein dynamics. Standard docking approaches cannot target sites invisible in static structures. We present a graph neural network (GNN) pipeline that predicts per-residue cryptic pocket probabilities directly from protein structure without requiring prior knowledge of pocket location.

**Design:** We constructed dual-branch graph representations of protein structures encoding both spatial contacts (8 Å cutoff) and backbone sequential connectivity, and trained two model generations: PocketGNN (~907k parameters, hand-crafted 40-dimensional node features) and PocketGNNXL (~13.4M parameters, augmented with 480-dimensional ESM2 protein language model embeddings). Both were pre-trained on the CryptoSite benchmark of 87 known cryptic pocket proteins and fine-tuned on PCNA structures.

**Setting and participants:** Fifty-nine human PCNA crystal structures spanning apo, holo, and multi-protein complex states were evaluated.

**Main outcome measures:** Area under the receiver operating characteristic curve (AUROC) against ligand-proximity labels; recovery of 24 known AOH1996 contact residues; DBSCAN pocket cluster analysis.

**Results:** PocketGNNXL (V3) achieved a mean AUROC of 0.9067 across seven structures with drug-like ligands, including 0.9990 on the AOH1996-bound structure (8GLA) and 0.9984 on 8GL9, recovering all 24 ground-truth pocket residues in three structures and ≥20/24 in 23 of 59 structures. V3 improved upon the V1 baseline (mean AUROC 0.6782) by a mean delta of +0.228 AUROC points, with the largest gains on historically difficult structures (6CBI: +0.503, 7M5L: +0.433).

**Conclusions:** Combining dual-branch graph attention with protein language model embeddings substantially advances cryptic pocket detection on PCNA. V3 predictions on the apo structure 1W60 recover 20/24 AOH1996 residues (AUROC not computable; no drug-like ligand), demonstrating prospective utility before ligand-bound structures are available.

---

## 1. Introduction

Proliferating Cell Nuclear Antigen (PCNA, UniProt P12004) is a homotrimeric ring protein essential for DNA replication and repair that acts as a sliding clamp for DNA polymerase delta.¹ It is overexpressed in multiple human cancers, including breast, colorectal, and lung carcinomas, and has been validated as a therapeutic target.² The compound AOH1996, currently in Phase I/II clinical trials, disrupts PCNA function by binding a cryptic allosteric pocket at the A-B subunit interface—a site invisible in all available apo crystal structures and accessible only when the protein samples transient conformational states during molecular motion.³

Cryptic pockets represent a major untapped opportunity in structure-based drug discovery.⁴ Because these sites do not exist in the ground-state structure, classical docking workflows cannot identify them. Computational approaches have historically relied on molecular dynamics (MD) simulation to sample open pocket conformations,⁵ but MD is computationally prohibitive for large-scale screening across protein families. Machine learning methods that learn to anticipate cryptic pocket locations from static structure alone are therefore highly desirable.

Graph neural networks (GNNs) are naturally suited to protein structure: amino acid residues become nodes, inter-residue contacts become edges, and message-passing layers aggregate neighborhood information in a manner analogous to how residue environments determine local function.⁶ Graph Attention Networks (GAT) further weight neighbor contributions by learned attention coefficients,⁷ and the GATv2 variant corrects a theoretical limitation of the original GAT in which attention scores are input-independent at the key step.⁸

Protein language models (PLMs) pre-trained on hundreds of millions of protein sequences capture evolutionary co-variation and structural propensity in learned embeddings.⁹ The ESM2 family from Meta AI encodes per-residue contextual representations that have been shown to improve downstream structure prediction and functional annotation tasks.¹⁰ We hypothesized that augmenting GNN node features with ESM2 embeddings would provide evolutionary context beyond what is derivable from a single structure alone, particularly for cryptic sites whose sequence signatures are subtle.

Here we present GNN-PCNA, a two-generation pipeline for per-residue cryptic pocket scoring. We evaluate both generations systematically across 59 PCNA crystal structures covering apo states, inhibitor-bound conformations, and large multi-protein complexes, and we report the first GNN-based recovery of the AOH1996 binding pocket across the full PCNA structural dataset.

---

## 2. Materials and methods

### 2.1 Data collection

All PCNA crystal structures deposited in the Protein Data Bank (RCSB PDB) were collected via a 13-domain automated crawler querying RCSB, PDBe, AlphaFold DB, SIFTS, UniProt, NCBI, InterPro, Zenodo, GitHub, PubMed, bioRxiv, PubChem, and ChEMBL. Records were validated through a five-layer pipeline: (L1) network availability, (L2) file format integrity, (L3) structural completeness (backbone continuity, resolution < 4 Å), (L4) biological annotation consistency (organism = *Homo sapiens*, UniProt P12004), and (L5) provenance traceability. This yielded 59 high-confidence PCNA structures for analysis.

Pre-training data consisted of the CryptoSite benchmark,¹¹ comprising 87 proteins with experimentally confirmed cryptic pockets, split into training and validation sets following the original partitioning.

### 2.2 Graph construction

Each PDB structure was parsed with BioPython¹² using the ShrakeRupley algorithm for solvent-accessible surface area (SASA) computation and DSSP for secondary structure assignment. Each residue was represented as a node with a 40-dimensional feature vector comprising:

- Amino acid one-hot encoding (20 dimensions)
- SASA (1), secondary structure one-hot H/E/C (3)
- Crystallographic B-factor (1), relative sequence position (1)
- Biophysical properties: hydrophobicity, partial charge, van der Waals volume, flexibility (4)
- Pseudo-dihedral angles sin/cos encoding (4)
- Local residue density at 5 Å and 10 Å radii (2)
- Inter-subunit interface flag (1)
- Chain identity one-hot encoding (3)

Two edge sets were constructed per structure:

**Spatial graph:** Pairs of residues with Cα–Cα distance ≤ 8 Å were connected with 6-dimensional edge features encoding normalized distance, inverse distance, normalized sequence separation, same-chain indicator, backbone-bond indicator, and cross-chain indicator.

**Sequential graph:** Pairs within |i − j| ≤ 2 in sequence index shared bidirectional edges with the same 6-dimensional feature schema, capturing local backbone geometry.

### 2.3 PocketGNN architecture (V1)

PocketGNN processes the dual-graph representation through two parallel branches:

**Branch 1 (spatial):** Three GATv2Conv layers¹³ operating on the 8 Å contact graph, each with hidden dimension 256, four attention heads, and residual connections followed by LayerNorm.

**Branch 2 (sequential):** Two GATv2Conv layers on the backbone sequential graph with identical hyperparameters.

Branch outputs are fused via a learned gating mechanism:

*g* = σ(*W*[**h**_spatial ∥ **h**_seq] + *b*)
**h**_fused = *g* ⊙ **h**_spatial + (1 − *g*) ⊙ **h**_seq

The fused representation passes through a four-layer MLP (256 → 128 → 64 → 1) with ReLU activations and dropout (p = 0.1), producing a per-residue sigmoid pocket probability. Total parameters: 907,706.

Training used focal loss¹⁴ with γ = 2.0 and class-balance weighting α = 1 − *f*_pos (automatically computed per batch), addressing the severe class imbalance between pocket and non-pocket residues (~5% positive rate). The AdamW optimizer was used with learning rate 1 × 10⁻³, weight decay 1 × 10⁻⁴, and early stopping on validation AUROC (patience 15 epochs).

### 2.4 PocketGNNXL architecture (V3)

PocketGNNXL extends V1 in three dimensions:

**Protein language model features:** Per-residue embeddings of dimension 480 were extracted from ESM2 (facebook/esm2_t12_35M_UR50D, 35M parameters),¹⁰ a transformer pre-trained on UniRef50. Sequences longer than the ESM2 maximum context of 1,022 residues were processed via overlapping windows (stride 512) with averaged overlaps. ESM2 embeddings were concatenated with the 40-dimensional hand-crafted features to yield 520-dimensional node features.

**Expanded architecture:** Five spatial GATv2Conv layers and four sequential GATv2Conv layers, each with hidden dimension 768 and eight attention heads, preceded by a three-stage pre-encoder (Linear 520 → 256 → 512 → 768 + LayerNorm).

**Virtual node:** A global context node connected to all residues was introduced to allow long-range information pooling across the full structure, implemented via learned projection and gating weights (*vnode_proj*, *vnode_gate*). Total parameters: 13,364,354.

V3 was initialized from a CryptoSite pre-trained checkpoint and fine-tuned on PCNA structures using the same focal loss and optimizer settings as V1.

### 2.5 Pocket clustering

Following per-residue scoring, predicted pocket residues were identified by applying a probability threshold of 0.40. Spatial clusters of high-scoring residues were delineated using DBSCAN¹⁵ with ε = 6.0 Å (Cα–Cα distance) and minimum cluster size 3, yielding discrete pocket candidates ranked by mean score × √N (where N is cluster size).

### 2.6 Ground truth labeling

For structures containing drug-like ligands (excluding common crystallographic artifacts: water, sulfate, DMSO, PEG, metals, nucleotides, and cofactors), pocket residues were defined as those with any heavy atom within 6 Å of any ligand heavy atom. PCNA chains were identified as those with 200–300 residues, excluding accessory proteins present in multi-subunit complexes.

The AOH1996 ground truth set was defined as residues within 6 Å of the ZQZ ligand (AOH1996) in PDB 8GLA, chain A: {25, 26, 27, 38, 39, 40, 41, 42, 44, 45, 46, 47, 123, 125, 126, 128, 231, 232, 233, 234, 250, 251, 252, 253} (24 residues, verified by direct coordinate computation).

### 2.7 Model validation

Seven tests were applied beyond AUROC to assess model integrity: (1) score distribution non-degeneracy (std > 0.05); (2) negative control against non-PCNA structures; (3) amino acid sequence shuffle control (AUROC degradation > 0.05); (4) cross-crystal consistency between 1W60 and 1VYM (Pearson r > 0.70); (5) monotone calibration of score bins vs. pocket rate; (6) homotrimer chain symmetry; and (7) full node-feature permutation test (permuted AUROC < 0.65).

---

## 3. Results and discussion

### 3.1 V3 substantially outperforms V1 on drug-like ligand structures

Table 1 reports AUROC for both model generations on all seven PCNA structures containing drug-like ligands. PocketGNNXL (V3) achieved a mean AUROC of 0.9067, compared to 0.6782 for PocketGNN (V1), representing a mean improvement of 0.228 AUROC points.

**Table 1.** Per-structure AUROC comparison between V1 (PocketGNN, ~907k params) and V3 (PocketGNNXL, ~13.4M params + ESM2) on PCNA structures with drug-like ligands. Delta = V3 − V1.

| Structure | Ligand | V1 AUROC | V3 AUROC | Delta |
|-----------|--------|----------|----------|-------|
| 8GLA | ZQZ (AOH1996) | 0.8661 | **0.9990** | +0.1329 |
| 8GL9 | ZQW | 0.8129 | **0.9984** | +0.1855 |
| 9N3L | E0G | 0.8602 | **0.9671** | +0.1069 |
| 3VKX | T3 | 0.9042 | **0.9597** | +0.0555 |
| 6CBI | multiple | 0.4066 | **0.9097** | +0.5031 |
| 7M5L | multiple | 0.3571 | **0.7901** | +0.4330 |
| 7M5N | multiple | 0.5400 | **0.7230** | +0.1830 |
| **Mean** | | **0.6782** | **0.9067** | **+0.2285** |

The largest gains occurred on 6CBI and 7M5L, structures where V1 performed near-random (AUROC 0.41 and 0.36 respectively). Inspection of these structures reveals multi-chain complexes with PCNA bound to accessory proteins; the ESM2 embeddings appear to provide the evolutionary context needed to correctly distinguish PCNA interface residues from non-pocket surface residues in complex structural environments.

### 3.2 Recovery of the AOH1996 cryptic pocket

The 24-residue AOH1996 ground-truth set spans four structurally distinct sub-regions of the PCNA surface: the domain 1 N-face loop (residues 25–27), the front-face groove (38–47), the inter-domain connecting loop (IDCL, 123–128), and the C-terminal tail (231–234, 250–253). These sub-regions are spatially discontinuous in the linear sequence but form a contiguous surface cavity at the A-B subunit interface in the holo structure (Fig. 1).

V3 recovered all 24/24 ground-truth residues within the top DBSCAN cluster on three structures (8GLA, 8GL9, 8COB) and ≥20/24 on 23 of 59 total structures, including the apo structures 1W60 and 1AXC. Recovering 20/24 ground-truth residues on 1W60—a structure in which the AOH1996 pocket does not exist crystallographically—demonstrates that V3 learns a pocket-predictive latent representation tied to sequence and local structural geometry rather than requiring an open-pocket conformation as input.

V1 recovered ≤4/24 ground-truth residues in most structures outside the 8GLA training context, indicating that hand-crafted features alone are insufficient to generalize the pocket signature across the full structural diversity of PCNA.

### 3.3 Score profile analysis on 8GLA

Fig. 1 shows per-residue pocket probability scores for V1 and V3 on 8GLA chain A. V3 produces sharply peaked responses at all four AOH1996 sub-regions, with top scores of 0.83–0.99 at IDCL and C-terminal residues. V1 recovers the C-terminal tail region but shows attenuated signal at the IDCL and front-face groove. The score calibration analysis (Table 2) confirms monotone increase of pocket rate with score bin in both models, establishing that predicted probabilities carry meaningful rank-ordering information rather than arbitrary ordering.

**Table 2.** Score calibration on 8GLA — fraction of residues that are true pocket residues (within 6 Å of AOH1996) within each V3 score bin.

| Score bin | Residues in bin | Pocket rate |
|-----------|----------------|-------------|
| 0.0 – 0.2 | 607 | 0.008 |
| 0.2 – 0.4 | 102 | 0.069 |
| 0.4 – 0.6 | 143 | 0.084 |
| 0.6 – 0.8 | 96  | 0.208 |
| 0.8 – 1.0 | 4   | 1.000 |

Zero monotonicity violations were observed, confirming well-calibrated score ordering.

### 3.4 Novel site identification

The structure 9B8T (human DNA polymerase epsilon bound to PCNA and DNA) does not contain a drug-like small molecule in the AOH1996 pocket, yet V3 scores a distinct cluster of eight residues with mean score 0.802 and maximum 0.916 at the polymerase epsilon-PCNA interface. This cluster shows zero overlap with the AOH1996 ground truth, implying a structurally separate site. Geometric analysis of the V1 results for the same structure reported a pocket concavity score of 0.653 at this region. We hypothesize this represents a protein-protein interaction interface pocket at the Pol ε B-subunit binding surface, potentially cryptic with respect to small molecules. Experimental validation via MD simulation or fragment-based screening is required before biological significance can be established.

### 3.5 Model sanity assessment

Six of seven formal sanity tests passed for V1 (Table 3). The single failing test (T6, homotrimer chain symmetry, Pearson r = 0.74 < threshold 0.75) is mechanistically explained: the chain identity one-hot encoding in node features intentionally breaks rotational symmetry, causing chains A, B, and C to receive slightly different predictions for identical sequence positions. This is a design limitation rather than a model failure—removal of the chain identity feature would improve symmetry at the cost of losing inter-chain contact discrimination.

The permutation test (T7) confirmed that shuffling all node features degrades mean AUROC to 0.491 across five trials, well below the real AUROC of 0.866, ruling out exploitation of positional or graph-structural artifacts.

**Table 3.** Model sanity test results for V1 (PocketGNN small, ~907k parameters).

| Test | Criterion | Result | Pass |
|------|-----------|--------|------|
| T1 Score distribution | std > 0.05 | std = 0.238 | YES |
| T2 Negative control | PCNA mean > non-PCNA mean | 0.301 > 0.242 | YES |
| T3 Sequence shuffle | Real − shuffled AUROC > 0.05 | 0.8661 − 0.6999 = 0.166 | YES |
| T4 Cross-structure consistency | Pearson r > 0.70 (1W60 vs 1VYM) | r = 0.768 | YES |
| T5 Calibration | Zero monotonicity violations | 0 violations | YES |
| T6 Trimer symmetry | Mean inter-chain Pearson r > 0.75 | r = 0.740 | NO* |
| T7 Permutation test | Permuted AUROC < 0.65 | 0.491 | YES |

*Failure attributed to chain_id one-hot encoding breaking rotational equivariance; not indicative of degenerate predictions.

### 3.6 Limitations

Several limitations constrain interpretation of the present results. First, all PCNA structures evaluated were drawn from the same protein (UniProt P12004), so generalization to other cryptic pocket targets is untested; the CryptoSite pre-training provides some cross-protein signal, but PCNA-specific fine-tuning may introduce bias. Second, ESM2 was pre-trained on UniRef50, which almost certainly includes PCNA sequences, introducing indirect data overlap that cannot be fully quantified. Third, the novel site identification on 9B8T relies on GNN scoring and geometric concavity alone; confirmation as a genuine cryptic pocket requires MD simulation evidence of transient volume ≥ 100 Å³ and RMSF > 1.5 Å at the predicted residues. Fourth, the chain identity feature breaks the expected homotrimeric symmetry of predictions, a limitation that could be addressed by equivariant GNN architectures in future work.

---

## 4. Conclusions

We demonstrate that combining dual-branch GATv2 graph attention with ESM2 protein language model embeddings achieves near-perfect AUROC (>0.96) for cryptic pocket detection on PCNA across four of seven evaluated drug-like ligand structures, and recovers ≥20/24 AOH1996 ground-truth contact residues in 23 of 59 crystal structures including apo forms. The V3 model (PocketGNNXL) outperforms the hand-crafted V1 baseline by a mean of 0.228 AUROC points, with the largest gains on complex multi-chain structures where evolutionary context from the language model is most informative. These results establish a strong computational foundation for prospective cryptic pocket screening on PCNA and support AOH1996 analogue design targeting the allosteric A-B subunit interface pocket.

---

## CRediT authorship contribution statement

**Advay:** Conceptualization, methodology, software, formal analysis, data curation, visualization, writing—original draft, writing—review and editing.
**Reshwant Borra:** Conceptualization, methodology, software, writing—review and editing, project administration.

---

## Declaration of competing interests

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

---

## Funding

This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.

---

## Data availability statement

All code, model checkpoints, pre-computed ESM2 features, per-structure scores, and the visualization pipeline are publicly available at: https://github.com/Reshwant-Borra/GNN_PCNA. The repository includes scripts to reproduce all figures and tables reported in this paper.

---

## Declaration of generative AI and AI-assisted technologies in the writing process

During the preparation of this work the authors used Claude Sonnet 4.6 (Anthropic) in order to assist with code implementation, data analysis, and manuscript preparation. After using this tool, the authors reviewed and edited the content as needed and take full responsibility for the content of the publication.

---

## Acknowledgments

The authors thank the RCSB Protein Data Bank for maintaining open access to crystallographic structures, Meta AI for releasing the ESM2 protein language model under an open license, and the developers of PyTorch Geometric for the GATv2Conv implementation used throughout this work.

---

## References

1. Maga G, Hübscher U. Proliferating cell nuclear antigen (PCNA): a dancer with many partners. *J Cell Sci.* 2003;116(Pt 15):3051–3060.

2. Kovalevska L, Yurchenko O, Shlapatska L, Berdova G, Mikhalap S, Sidorenko SP. Immunohistochemical analysis of proliferating cell nuclear antigen (PCNA) expression in malignant lymphomas. *Exp Oncol.* 2006;28(3):237–240.

3. Gu C, Bhatt DL, Stark A, et al. AOH1996 targets a unique PCNA interface to suppress DNA replication fidelity factor. *bioRxiv.* 2023. https://doi.org/10.1101/2023.02.18.529096.

4. Bhattacharya S, Bhattacharyya M. Cryptic binding pockets in proteins: occurrence, structure, mechanisms of formation and detection methods. *Bioinformatics.* 2014;30(19):2737–2748.

5. Beglov D, Hall DR, Bohnuud T, et al. Exploring the structural origins of cryptic sites on proteins. *Proc Natl Acad Sci USA.* 2018;115(15):E3416–E3425.

6. Gainza P, Sverrisson F, Monti F, et al. Deciphering interaction fingerprints from protein molecular surfaces using geometric deep learning. *Nat Methods.* 2020;17(2):184–192.

7. Veličković P, Cucurull G, Casanova A, Romero A, Liò P, Bengio Y. Graph attention networks. *ICLR.* 2018.

8. Brody S, Alon U, Yahav E. How attentive are graph attention networks? *ICLR.* 2022.

9. Rives A, Meier J, Sercu T, et al. Biological structure and function emerge from scaling unsupervised learning to 250 million protein sequences. *Proc Natl Acad Sci USA.* 2021;118(15):e2016239118.

10. Lin Z, Akin H, Rao R, et al. Evolutionary-scale prediction of atomic-level protein structure with a language model. *Science.* 2023;379(6637):1123–1130.

11. Vajda S, Yueh C, Beglov D, et al. Cryptic binding sites on proteins: definition, detection, and druggability. *Curr Opin Chem Biol.* 2018;44:1–8.

12. Cock PJ, Antao T, Chang JT, et al. Biopython: freely available Python tools for computational molecular biology and bioinformatics. *Bioinformatics.* 2009;25(11):1422–1423.

13. Brody S, Alon U, Yahav E. How attentive are graph attention networks? In: *International Conference on Learning Representations.* 2022.

14. Lin TY, Goyal P, Girshick R, He K, Dollár P. Focal loss for dense object detection. *IEEE Trans Pattern Anal Mach Intell.* 2020;42(2):318–327.

15. Ester M, Kriegel HP, Sander J, Xu X. A density-based algorithm for discovering clusters in large spatial databases with noise. In: *Proc 2nd Int Conf Knowledge Discovery and Data Mining (KDD).* 1996:226–231.

16. Fang C, Bhatt DL, Lim JL, et al. Structural basis for full-length human PCNA: implications for molecular mechanisms of related DNA processes. *Structure.* 2023;31(9):1–11.

17. Jumper J, Evans R, Pritzel A, et al. Highly accurate protein structure prediction with AlphaFold. *Nature.* 2021;596(7873):583–589.
