# Paper Notes

## PCNA — Key Biology

- **Full name**: Proliferating Cell Nuclear Antigen
- **Function**: Homotrimeric ring that acts as a sliding clamp for DNA polymerase δ/ε during replication; scaffold for DNA repair factors
- **Structure**: 3 identical subunits (~29 kDa each), total ~87 kDa ring
- **Cancer relevance**: Overexpressed in many cancers; essential for tumor cell proliferation
- **AOH1996**: First-in-class small molecule inhibitor; discovered ~2023 (City of Hope); PDB **8GLA** shows it bound in an interdomain connecting loop (IDCL) region
- **Cryptic pocket nature**: AOH1996 site is not visible as a pocket in apo structures (1W60) — only opens upon binding or under dynamics

---

## GNN Pocket Detection Methods

### PocketMiner (Durrant Lab, 2023)
- Architecture: GNN trained on CryptoSite dataset (~93 apo/holo pairs)
- Graph: residue-level, edges by Cα distance
- Labels: residues near cryptic pocket in holo structure
- Key result: predicts cryptic pockets with AUROC ~0.85 on held-out proteins
- Limitation: trained on general proteins; may need fine-tuning for PCNA
- **Relevance**: primary baseline to beat; likely recovers 8GLA pocket with fine-tuning

### DeepAllo (2022)
- Targets **allosteric** communication pathways, not just geometric pockets
- Uses attention-based GNN to identify residues that transmit conformational signals
- Relevant for PCNA because: PCNA has known allosteric coupling between subunit interfaces
- Could identify pockets at inter-subunit interfaces that AOH1996-like molecules could exploit

### CryptoSite (Cimermancic et al., 2016)
- Foundational dataset for cryptic pocket detection
- 93 protein pairs with known cryptic pockets
- Features: normal mode analysis, covariance, solvent accessibility
- Classical ML (SVM), not GNN — serves as baseline and training data source

### fpocket (Le Guilloux et al., 2009)
- Geometric: Voronoi tessellation + alpha sphere clustering
- Fast, no ML — identifies all geometric cavities
- On apo PCNA: likely misses AOH1996 pocket (cavity too shallow)
- Use as sanity check and negative control

---

## MD Validation Techniques

### RMSF (Root Mean Square Fluctuation)
- Per-residue measure of atomic positional fluctuation over MD trajectory
- High RMSF in predicted pocket residues = evidence of flexibility = cryptic pocket signature
- Calculation: `RMSF = sqrt(mean((r_i - <r>)^2))` over trajectory frames
- MDAnalysis: `rmsf = MDAnalysis.analysis.rms.RMSF(atomgroup).run()`
- Interpretation: RMSF > 1.5–2.0 Å for pocket residues vs ~0.5–1.0 Å background

### DCCM (Dynamic Cross-Correlation Matrix)
- NxN matrix: `C_ij = <Δr_i · Δr_j> / sqrt(<Δr_i²><Δr_j²>)`
- Values: +1 = fully correlated (move together), -1 = anti-correlated
- Cryptic pocket signature: pocket residues show high internal correlation AND anti-correlation with the regions that "open" to expose the pocket
- MDAnalysis: compute via displacement covariance, or use Bio3D (R) for visualization
- **DCCM blocks** corresponding to pocket clusters suggest allosteric communication

### Pocket Volume Tracking
- Track pocket volume over MD frames using fpocket or MDpocket (fpocket-based)
- Cryptic pocket: volume near zero in crystal frame, opens to >100–300 ų transiently
- Tool: `mdpocket --trajectory_file traj.xtc --trajectory_format xtc -f topology.pdb`

### Principal Component Analysis (PCA) of MD
- Project trajectory onto top PCs (collective motions)
- Overlay pocket open/closed states on PC1 vs PC2 → separates conformational states
- If open pocket state is accessible along PC1, enhanced sampling along PC1 could accelerate pocket opening

### Enhanced Sampling (if needed)
- If 100 ns MD doesn't show pocket opening: use **metadynamics** or **replica exchange MD**
- Collective variable for metadynamics: pocket volume or distance between key gate residues
- PLUMED + GROMACS: standard toolchain for this
