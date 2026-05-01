# CHATGPT_REVIEW_PROMPTS.md — Reusable ChatGPT Review Prompts

---

## Standard Code Review Prompt

```
Review this Python implementation for the GNN-PCNA cryptic pocket detection project.
Language: Python 3.10+. Stack: PyTorch Geometric, BioPython, MDAnalysis.

Changed file: src/{path/to/file.py}
[paste complete changed file]

Known bugs to check (from KNOWN_BUGS.md):
[paste KNOWN_BUGS.md content]

Review checklist:
1. Off-by-one errors in residue/graph indexing
2. Data leakage — train/val/test split must be at protein level, not residue level
3. Label imbalance — focal loss or weighted BCE applied correctly (expect ~5–15% positive)
4. PyTorch Geometric API correctness:
   - edge_index must be long dtype
   - edge_attr must be float dtype
   - batch attribute handled correctly if batched
5. BioPython API correctness (if applicable)
6. MDAnalysis API correctness (if applicable)
7. PCNA-specific assumptions:
   - 3 chains A, B, C; ~261 residues each; ~800 total
   - Homotrimer symmetry — chains are near-identical
   - 8GLA ground truth: residues within 6 Å of AOH1996
8. Numerical stability — NaN/Inf in loss, gradients, or scores
9. Memory efficiency — avoid building N×N matrices for large N without warning
10. Missing error handling for invalid inputs (empty PDB, missing CA atoms)

For each issue:
Severity: critical | warning | suggestion
Location: function name or line number
Description: what is wrong
Fix: minimal correction (code snippet preferred)

Do NOT suggest architectural changes.
Do NOT rewrite working logic.
Return: numbered list of issues only, ordered by severity.
```

---

## Scientific Logic Review Prompt

```
Review the scientific logic of this experimental setup for GNN-PCNA cryptic pocket prediction.

Hypothesis: {state hypothesis}

Code / setup:
[paste relevant code or config]

Evaluate:
1. Structural biology: is this physically plausible for PCNA?
2. ML validity: does the training setup allow testing this hypothesis?
3. Data leakage: could PCNA chain A/B/C correlation cause optimistic results?
4. Statistical power: is there enough positive training data?
5. Evaluation: are AUROC and AUPRC both reported? (AUPRC matters more for imbalanced data)
6. Validation: does the positive control (8GLA pocket recovery) gate all novel claims?

Flag the single most critical flaw if one exists.
Return: structured review with one key recommendation.
```

---

## Data Pipeline Review Prompt

```
Review this data processing pipeline for scientific correctness.

Files:
[paste src/data_processing/parse_pdb.py]
[paste src/data_processing/graph_construction.py]

Check:
1. Are crystal contact regions from 1W60 flagged? (lattice packing can mask pockets)
2. Are alternate conformations handled? (use only first conformation)
3. Is water removal correct? (HOH removed, AOH1996 kept in 8GLA)
4. Are labels computed correctly? (6 Å cutoff from any AOH1996 heavy atom)
5. Is SASA computed per residue (not per atom)?
6. Are B-factors normalized per chain (not globally)?
7. Is the Cα–Cα distance cutoff exactly as specified (8.0 Å)?
8. Is sequence separation |i−j| computed correctly (absolute, not signed)?

Return: issues found, ordered by severity.
```

---

## MD Analysis Review Prompt

```
Review this MD analysis implementation for the GNN-PCNA project.

File: src/md/parse_trajectory.py
[paste file content]

Check:
1. RMSF is computed after alignment (superposition) of trajectory frames
2. DCCM matrix is symmetric: C_ij = C_ji (verify)
3. DCCM values are in [-1, 1] (verify normalization)
4. Volume tracking uses per-frame analysis (not just first/last frame)
5. MDAnalysis Universe created correctly with matching topology and trajectory
6. Atom selection uses correct MDAnalysis selection syntax
7. Output arrays match expected shapes (RMSF: (N,), DCCM: (N,N))
8. No trajectory frame skipping issues (step parameter correct)

Return: numbered issue list.
```
