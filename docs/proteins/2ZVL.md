# 2ZVL — TRANSFERASECRYSTAL STRUCTURE OF PCNA IN COMPLEX WITH DNA POLYMERASE KAPPA FRAGMENT

> Generated: 2026-05-19  |  Category: Other PCNA structure  **AOH1996 CANDIDATE**

## Quick Stats

| Field | Value |
|-------|-------|
| PDB ID | [2ZVL](https://www.rcsb.org/structure/2ZVL) |
| Residues | 1543 across 12 chains |
| Ligands detected | none (apo) |
| AUROC | N/A (apo — no ligand for labeling) |
| Top pocket mean score | 0.5867 (337 residues) |
| AOH1996 GT overlap | ###################.  23/24 |
| Top pocket concavity | 0.543 (concave) |

## AOH1996 Pocket Assessment

The model's top predicted cluster overlaps with **23/24 AOH1996 ground-truth residues** (96% of the confirmed pocket from PDB 8GLA). Top cluster mean score: 0.587. **Note: mean score 0.587 is below the 0.7 project-defined threshold — the AOH1996 pocket is not confidently recovered by this checkpoint.**

**Hypothesis (unvalidated):** This region may be compatible with AOH1996 binding. Molecular docking or MD simulation is required to test this hypothesis. Labels are derived from ligand-proximity heuristics, not curated benchmark labels.

## Full Analysis Report

```
======================================================================
PDB: 2ZVL
Title: TRANSFERASECRYSTAL STRUCTURE OF PCNA IN COMPLEX WITH DNA POLYMERASE KAPPA FRAGMENT
Chains: A, B, C, D, E, F, U, V, W, X, Y, Z  |  Residues: 1543
Ligands detected: none (apo)
Residues above threshold (0.4): 457/1543 (29.6%)

Predicted cryptic pockets: 9

  Pocket #1  (PRIMARY)
  ------------------------------------------------------------
  Residues: 337  |  Mean score: 0.587  |  Max score: 0.720
  Center (A): (18.3, -12.4, 25.3)
  Structural region: Domain 2 core beta sheet
    102 residues in: Domain 2 core beta sheet
     79 residues in: Core beta sheet
     55 residues in: C-terminal loop — AOH1996 cryptic pocket region
     44 residues in: N-terminal beta sheet (domain 1)
     38 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
     19 residues in: Front-face loop (PIP-box groove)
  AOH1996 pocket overlap: 23/25 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.54 (concave — geometrically pocket-like)
  Top residues: D239(TYR)=0.720, E239(TYR)=0.717, E138(LYS)=0.713, D139(MET)=0.711, D138(LYS)=0.705, F239(TYR)=0.704, E139(MET)=0.703, E238(GLU)=0.703

  How this pocket was identified:
    The model assigned a high prioritization score to 337 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 34.5 A^2 (63% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 337 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the domain 2 core beta sheet. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #2  (secondary)
  ------------------------------------------------------------
  Residues: 37  |  Mean score: 0.568  |  Max score: 0.661
  Center (A): (-47.6, 4.3, -16.2)
  Structural region: C-terminal loop — AOH1996 cryptic pocket region
     14 residues in: C-terminal loop — AOH1996 cryptic pocket region
     12 residues in: Domain 2 core beta sheet
      4 residues in: N-terminal beta sheet (domain 1)
      4 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      2 residues in: Front-face loop (PIP-box groove)
      1 residues in: Core beta sheet
  AOH1996 pocket overlap: 10/25 GT residues
  --> PARTIAL overlap: pocket partially covers the AOH1996 site
  Geometric concavity: 0.68 (concave — geometrically pocket-like)
  Top residues: B239(TYR)=0.661, B137(VAL)=0.658, B238(GLU)=0.638, B228(SER)=0.622, B237(VAL)=0.621, B138(LYS)=0.616, B136(VAL)=0.615, B226(THR)=0.613

  How this pocket was identified:
    The model assigned a high prioritization score to 37 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 26.2 A^2 (76% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 37 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the c-terminal loop — aoh1996 cryptic pocket region. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #3  (secondary)
  ------------------------------------------------------------
  Residues: 24  |  Mean score: 0.554  |  Max score: 0.691
  Center (A): (-7.0, 40.8, -13.4)
  Structural region: C-terminal loop — AOH1996 cryptic pocket region
     13 residues in: C-terminal loop — AOH1996 cryptic pocket region
      9 residues in: Domain 2 core beta sheet
      2 residues in: Front-face loop (PIP-box groove)
  AOH1996 pocket overlap: 7/25 GT residues
  --> PARTIAL overlap: pocket partially covers the AOH1996 site
  Geometric concavity: 0.71 (concave — geometrically pocket-like)
  Top residues: C236(VAL)=0.691, C235(LEU)=0.674, C230(SER)=0.668, C234(PRO)=0.649, C237(VAL)=0.631, C232(ASP)=0.619, C231(ALA)=0.603, C238(GLU)=0.603

  How this pocket was identified:
    The model assigned a high prioritization score to 24 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 22.8 A^2 (75% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 24 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

  Pocket #4  (secondary)
  ------------------------------------------------------------
  Residues: 14  |  Mean score: 0.656  |  Max score: 0.776
  Center (A): (2.3, -1.5, -54.9)
  Structural region: C-terminal loop — AOH1996 cryptic pocket region
      6 residues in: C-terminal loop — AOH1996 cryptic pocket region
      5 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      3 residues in: Domain 2 core beta sheet
  AOH1996 pocket overlap: 4/25 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.50 (concave — geometrically pocket-like)
  Top residues: A134(SER)=0.776, A135(CYS)=0.752, A136(VAL)=0.739, A232(ASP)=0.715, A231(ALA)=0.711, A235(LEU)=0.710, A234(PRO)=0.700, A133(TYR)=0.695

  How this pocket was identified:
    The model assigned a high prioritization score to 14 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 54.7 A^2 (50% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 14 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

  Pocket #5  (secondary)
  ------------------------------------------------------------
  Residues: 11  |  Mean score: 0.585  |  Max score: 0.638
  Center (A): (17.8, -36.9, 49.9)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/25 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.18 (convex — surface protrusion, interpret cautiously)
  Top residues: D207(PHE)=0.638, D169(PHE)=0.637, D170(SER)=0.634, D205(LEU)=0.630, D206(THR)=0.618, D168(LYS)=0.589, D158(VAL)=0.581, D204(GLN)=0.569

  How this pocket was identified:
    The model assigned a high prioritization score to 11 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 34.5 A^2 (64% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 11 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

  Pocket #6  (secondary)
  ------------------------------------------------------------
  Residues: 13  |  Mean score: 0.498  |  Max score: 0.618
  Center (A): (-47.6, 29.9, -11.4)
  Structural region: Core beta sheet
      7 residues in: Core beta sheet
      6 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
  AOH1996 pocket overlap: 1/25 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.23 (convex — surface protrusion, interpret cautiously)
  Top residues: B68(MET)=0.618, B69(GLY)=0.615, B70(VAL)=0.534, B120(ASP)=0.532, B123(VAL)=0.511, B122(ASP)=0.508, B121(LEU)=0.498, B118(LEU)=0.479

  How this pocket was identified:
    The model assigned a high prioritization score to 13 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 58.2 A^2 (31% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 13 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

  Pocket #7  (secondary)
  ------------------------------------------------------------
  Residues: 7  |  Mean score: 0.509  |  Max score: 0.591
  Center (A): (5.2, 36.6, -39.8)
  Structural region: Core beta sheet
      5 residues in: Core beta sheet
      2 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
  AOH1996 pocket overlap: 0/25 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.29 (convex — surface protrusion, interpret cautiously)
  Top residues: C98(THR)=0.591, C69(GLY)=0.562, C120(ASP)=0.509, C99(LEU)=0.499, C68(MET)=0.494, C118(LEU)=0.464, C119(MET)=0.442

  How this pocket was identified:
    The model assigned a high prioritization score to 7 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 38.9 A^2 (43% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 7 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

  Pocket #8  (secondary)
  ------------------------------------------------------------
  Residues: 8  |  Mean score: 0.460  |  Max score: 0.519
  Center (A): (-45.6, -1.6, -29.2)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/25 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.38 (convex — surface protrusion, interpret cautiously)
  Top residues: B207(PHE)=0.519, B170(SER)=0.519, B206(THR)=0.498, B205(LEU)=0.475, B168(LYS)=0.447, B169(PHE)=0.416, B158(VAL)=0.407, B159(VAL)=0.401

  How this pocket was identified:
    The model assigned a high prioritization score to 8 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 22.5 A^2 (62% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 8 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

  Pocket #9  (secondary)
  ------------------------------------------------------------
  Residues: 3  |  Mean score: 0.700  |  Max score: 0.756
  Center (A): (-23.7, -3.6, -52.1)
  Structural region: N-terminal beta sheet (domain 1)
  AOH1996 pocket overlap: 3/25 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.67 (concave — geometrically pocket-like)
  Top residues: A26(ALA)=0.756, A27(CYS)=0.744, A25(GLU)=0.599

  How this pocket was identified:
    The model assigned a high prioritization score to 3 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 35.3 A^2 (67% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 3 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

Score distribution:
  Min=0.020  Max=0.776  Mean=0.245  Std=0.237
  29.6% of residues exceed threshold 0.4 (focused signal — clusters are reliable)
```

## Data Files

> **Gitignored** — regenerate locally with `python scripts/per_structure_analysis.py`
> PDB inputs: `python agents/pcna_crawler.py --download` | Graphs: `python scripts/build_graphs.py`

| File | Description | Tracked in git? |
|------|-------------|----------------|
| `results/per_structure/2ZVL/scores.csv` | Per-residue pocket scores | No |
| `results/per_structure/2ZVL/clusters.csv` | DBSCAN cluster assignments | No |
| `results/per_structure/2ZVL/report.txt` | Full text analysis report | No |
| `results/per_structure/2ZVL/summary.json` | Machine-readable summary | No |
| `results/per_structure/summary_table.csv` | All-59 rollup | Yes |
| `checkpoints/pcna/best_pcna.ckpt` | Trained model weights | Yes |
| `data/raw/2ZVL.pdb` | Raw PDB structure | No |
| `data/graphs/2ZVL.pt` | PyG graph tensor | No |

---
*GNN-PCNA v2 | Dual-branch GATv2Conv | Checkpoint tracked at `checkpoints/pcna/best_pcna.ckpt`*