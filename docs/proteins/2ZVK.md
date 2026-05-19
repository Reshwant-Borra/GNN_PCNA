# 2ZVK — TRANSFERASECRYSTAL STRUCTURE OF PCNA IN COMPLEX WITH DNA POLYMERASE ETA FRAGMENT

> Generated: 2026-05-16  |  Category: Other PCNA structure  

## Quick Stats

| Field | Value |
|-------|-------|
| PDB ID | [2ZVK](https://www.rcsb.org/structure/2ZVK) |
| Residues | 777 across 6 chains |
| Ligands detected | none (apo) |
| AUROC | N/A (apo — no ligand for labeling) |
| Top pocket mean score | 0.5491 (56 residues) |
| AOH1996 GT overlap | ###########.........  13/24 |
| Top pocket concavity | 0.446 (convex) |

## AOH1996 Pocket Assessment

Moderate overlap: **13/24 AOH1996 GT residues** recovered. Partial pocket opening may be present — this structure could bind AOH1996 in a conformation-dependent manner.

## Full Analysis Report

```
======================================================================
PDB: 2ZVK
Title: TRANSFERASECRYSTAL STRUCTURE OF PCNA IN COMPLEX WITH DNA POLYMERASE ETA FRAGMENT
Chains: A, B, C, U, V, W  |  Residues: 777
Ligands detected: none (apo)
Residues above threshold (0.4): 178/777 (22.9%)

Predicted cryptic pockets: 6

  Pocket #1  (PRIMARY)
  ------------------------------------------------------------
  Residues: 56  |  Mean score: 0.549  |  Max score: 0.703
  Center (A): (56.7, -10.1, 13.1)
  Structural region: Domain 2 core beta sheet
     23 residues in: Domain 2 core beta sheet
     17 residues in: C-terminal loop — AOH1996 cryptic pocket region
      6 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      4 residues in: N-terminal beta sheet (domain 1)
      3 residues in: Front-face loop (PIP-box groove)
      3 residues in: Core beta sheet
  AOH1996 pocket overlap: 13/24 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.45 (convex — surface protrusion, interpret cautiously)
  Top residues: C236(VAL)=0.703, C228(SER)=0.692, C235(LEU)=0.685, C227(LEU)=0.679, C226(THR)=0.676, C234(PRO)=0.666, C237(VAL)=0.665, C229(MET)=0.664

  How this pocket was identified:
    The model assigned a high prioritization score to 56 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 30.5 A^2 (70% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 56 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the domain 2 core beta sheet. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #2  (secondary)
  ------------------------------------------------------------
  Residues: 46  |  Mean score: 0.576  |  Max score: 0.686
  Center (A): (66.4, 33.4, 41.0)
  Structural region: C-terminal loop — AOH1996 cryptic pocket region
     15 residues in: C-terminal loop — AOH1996 cryptic pocket region
     13 residues in: Domain 2 core beta sheet
      6 residues in: N-terminal beta sheet (domain 1)
      5 residues in: Core beta sheet
      4 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      3 residues in: Front-face loop (PIP-box groove)
  AOH1996 pocket overlap: 11/24 GT residues
  --> PARTIAL overlap: pocket partially covers the AOH1996 site
  Geometric concavity: 0.50 (concave — geometrically pocket-like)
  Top residues: B239(TYR)=0.686, B238(GLU)=0.675, B228(SER)=0.663, B227(LEU)=0.657, B226(THR)=0.657, B39(SER)=0.652, B237(VAL)=0.650, B40(MET)=0.635

  How this pocket was identified:
    The model assigned a high prioritization score to 46 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 27.1 A^2 (70% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 46 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the c-terminal loop — aoh1996 cryptic pocket region. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #3  (secondary)
  ------------------------------------------------------------
  Residues: 32  |  Mean score: 0.639  |  Max score: 0.762
  Center (A): (42.5, -17.5, 67.8)
  Structural region: Domain 2 core beta sheet
     17 residues in: Domain 2 core beta sheet
     10 residues in: C-terminal loop — AOH1996 cryptic pocket region
      3 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      2 residues in: Front-face loop (PIP-box groove)
  AOH1996 pocket overlap: 8/24 GT residues
  --> PARTIAL overlap: pocket partially covers the AOH1996 site
  Geometric concavity: 0.44 (convex — surface protrusion, interpret cautiously)
  Top residues: A134(SER)=0.762, A135(CYS)=0.756, A163(ALA)=0.751, A235(LEU)=0.751, A234(PRO)=0.746, A232(ASP)=0.745, A136(VAL)=0.744, A236(VAL)=0.740

  How this pocket was identified:
    The model assigned a high prioritization score to 32 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 39.5 A^2 (56% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 32 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the domain 2 core beta sheet. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #4  (secondary)
  ------------------------------------------------------------
  Residues: 24  |  Mean score: 0.530  |  Max score: 0.615
  Center (A): (60.0, 25.8, 18.6)
  Structural region: Core beta sheet
     16 residues in: Core beta sheet
      6 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      2 residues in: N-terminal beta sheet (domain 1)
  AOH1996 pocket overlap: 3/24 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.38 (convex — surface protrusion, interpret cautiously)
  Top residues: B69(GLY)=0.615, B102(VAL)=0.607, B68(MET)=0.607, B120(ASP)=0.595, B100(ALA)=0.590, B99(LEU)=0.589, B118(LEU)=0.588, B98(THR)=0.583

  How this pocket was identified:
    The model assigned a high prioritization score to 24 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 46.0 A^2 (46% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 24 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

  Pocket #5  (secondary)
  ------------------------------------------------------------
  Residues: 14  |  Mean score: 0.520  |  Max score: 0.565
  Center (A): (40.2, -22.7, 37.0)
  Structural region: Core beta sheet
     12 residues in: Core beta sheet
      1 residues in: Domain 2 core beta sheet
      1 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.29 (convex — surface protrusion, interpret cautiously)
  Top residues: C69(GLY)=0.565, C116(MET)=0.557, C118(LEU)=0.557, C99(LEU)=0.556, C68(MET)=0.555, C117(LYS)=0.555, C98(THR)=0.555, C100(ALA)=0.554

  How this pocket was identified:
    The model assigned a high prioritization score to 14 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 30.0 A^2 (64% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 14 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

  Pocket #6  (secondary)
  ------------------------------------------------------------
  Residues: 3  |  Mean score: 0.637  |  Max score: 0.752
  Center (A): (41.7, 10.3, 69.1)
  Structural region: N-terminal beta sheet (domain 1)
  AOH1996 pocket overlap: 3/24 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 1.00 (concave — geometrically pocket-like)
  Top residues: A26(ALA)=0.752, A27(CYS)=0.741, A25(GLU)=0.417

  How this pocket was identified:
    The model assigned a high prioritization score to 3 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 32.9 A^2 (67% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 3 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

Score distribution:
  Min=0.020  Max=0.762  Mean=0.209  Std=0.220
  22.9% of residues exceed threshold 0.4 (focused signal — clusters are reliable)
```

## Data Files

> **Gitignored** — regenerate locally with `python scripts/per_structure_analysis.py`
> PDB inputs: `python agents/pcna_crawler.py --download` | Graphs: `python scripts/build_graphs.py`

| File | Description | Tracked in git? |
|------|-------------|----------------|
| `results/per_structure/2ZVK/scores.csv` | Per-residue pocket scores | No |
| `results/per_structure/2ZVK/clusters.csv` | DBSCAN cluster assignments | No |
| `results/per_structure/2ZVK/report.txt` | Full text analysis report | No |
| `results/per_structure/2ZVK/summary.json` | Machine-readable summary | No |
| `results/per_structure/summary_table.csv` | All-59 rollup | Yes |
| `checkpoints/pcna/best_pcna.ckpt` | Trained model weights | Yes |
| `data/raw/2ZVK.pdb` | Raw PDB structure | No |
| `data/graphs/2ZVK.pt` | PyG graph tensor | No |

---
*GNN-PCNA v2 | Dual-branch GATv2Conv | Checkpoint tracked at `checkpoints/pcna/best_pcna.ckpt`*