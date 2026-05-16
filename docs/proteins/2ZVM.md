# 2ZVM — TRANSFERASECRYSTAL STRUCTURE OF PCNA IN COMPLEX WITH DNA POLYMERASE IOTA FRAGMENT

> Generated: 2026-05-16  |  Category: Other PCNA structure  

## Quick Stats

| Field | Value |
|-------|-------|
| PDB ID | [2ZVM](https://www.rcsb.org/structure/2ZVM) |
| Residues | 776 across 6 chains |
| Ligands detected | none (apo) |
| AUROC | N/A (apo — no ligand for labeling) |
| Top pocket mean score | 0.5634 (48 residues) |
| AOH1996 GT overlap | ############........  15/24 |
| Top pocket concavity | 0.562 (concave) |

## AOH1996 Pocket Assessment

Moderate overlap: **15/24 AOH1996 GT residues** recovered. Partial pocket opening may be present — this structure could bind AOH1996 in a conformation-dependent manner.

## Full Analysis Report

```
======================================================================
PDB: 2ZVM
Title: TRANSFERASECRYSTAL STRUCTURE OF PCNA IN COMPLEX WITH DNA POLYMERASE IOTA FRAGMENT
Chains: A, B, C, U, V, W  |  Residues: 776
Ligands detected: none (apo)
Residues above threshold (0.4): 163/776 (21.0%)

Predicted cryptic pockets: 8

  Pocket #1  (PRIMARY)
  ------------------------------------------------------------
  Residues: 48  |  Mean score: 0.563  |  Max score: 0.662
  Center (A): (1.6, -14.6, 19.3)
  Structural region: C-terminal loop — AOH1996 cryptic pocket region
     15 residues in: C-terminal loop — AOH1996 cryptic pocket region
     13 residues in: Domain 2 core beta sheet
      7 residues in: Front-face loop (PIP-box groove)
      5 residues in: N-terminal beta sheet (domain 1)
      4 residues in: Core beta sheet
      4 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
  AOH1996 pocket overlap: 15/24 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.56 (concave — geometrically pocket-like)
  Top residues: B228(SER)=0.662, B227(LEU)=0.659, B137(VAL)=0.658, B226(THR)=0.655, B237(VAL)=0.653, B238(GLU)=0.650, B239(TYR)=0.640, B236(VAL)=0.638

  How this pocket was identified:
    The model assigned high pocket probability to 48 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 27.4 A^2 (69% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 48 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the c-terminal loop — aoh1996 cryptic pocket region. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #2  (secondary)
  ------------------------------------------------------------
  Residues: 34  |  Mean score: 0.528  |  Max score: 0.637
  Center (A): (54.7, -8.0, 11.1)
  Structural region: C-terminal loop — AOH1996 cryptic pocket region
     13 residues in: C-terminal loop — AOH1996 cryptic pocket region
      9 residues in: Domain 2 core beta sheet
      5 residues in: Front-face loop (PIP-box groove)
      4 residues in: N-terminal beta sheet (domain 1)
      3 residues in: Core beta sheet
  AOH1996 pocket overlap: 11/24 GT residues
  --> PARTIAL overlap: pocket partially covers the AOH1996 site
  Geometric concavity: 0.62 (concave — geometrically pocket-like)
  Top residues: C226(THR)=0.637, C228(SER)=0.636, C227(LEU)=0.631, C236(VAL)=0.625, C237(VAL)=0.621, C40(MET)=0.609, C225(VAL)=0.608, C238(GLU)=0.606

  How this pocket was identified:
    The model assigned high pocket probability to 34 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 17.1 A^2 (79% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 34 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the c-terminal loop — aoh1996 cryptic pocket region. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #3  (secondary)
  ------------------------------------------------------------
  Residues: 23  |  Mean score: 0.548  |  Max score: 0.635
  Center (A): (21.3, -27.6, 8.5)
  Structural region: Core beta sheet
     17 residues in: Core beta sheet
      5 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      1 residues in: N-terminal beta sheet (domain 1)
  AOH1996 pocket overlap: 2/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.30 (convex — surface protrusion, interpret cautiously)
  Top residues: B68(MET)=0.635, B69(GLY)=0.622, B99(LEU)=0.600, B120(ASP)=0.597, B102(VAL)=0.597, B98(THR)=0.591, B118(LEU)=0.590, B119(MET)=0.586

  How this pocket was identified:
    The model assigned high pocket probability to 23 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 43.9 A^2 (52% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 23 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #4  (secondary)
  ------------------------------------------------------------
  Residues: 16  |  Mean score: 0.648  |  Max score: 0.754
  Center (A): (37.3, 24.5, 50.3)
  Structural region: C-terminal loop — AOH1996 cryptic pocket region
      8 residues in: C-terminal loop — AOH1996 cryptic pocket region
      5 residues in: Domain 2 core beta sheet
      3 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
  AOH1996 pocket overlap: 4/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.38 (convex — surface protrusion, interpret cautiously)
  Top residues: A134(SER)=0.754, A135(CYS)=0.737, A136(VAL)=0.733, A232(ASP)=0.720, A235(LEU)=0.715, A231(ALA)=0.708, A234(PRO)=0.700, A233(VAL)=0.692

  How this pocket was identified:
    The model assigned high pocket probability to 16 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 30.9 A^2 (69% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 16 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #5  (secondary)
  ------------------------------------------------------------
  Residues: 18  |  Mean score: 0.525  |  Max score: 0.600
  Center (A): (60.6, 5.7, 32.1)
  Structural region: Core beta sheet
     15 residues in: Core beta sheet
      3 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.22 (convex — surface protrusion, interpret cautiously)
  Top residues: C99(LEU)=0.600, C98(THR)=0.599, C100(ALA)=0.583, C69(GLY)=0.578, C118(LEU)=0.559, C117(LYS)=0.549, C68(MET)=0.548, C97(ASP)=0.537

  How this pocket was identified:
    The model assigned high pocket probability to 18 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 35.3 A^2 (61% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 18 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #6  (secondary)
  ------------------------------------------------------------
  Residues: 11  |  Mean score: 0.544  |  Max score: 0.635
  Center (A): (-0.9, -6.8, 31.9)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.45 (convex — surface protrusion, interpret cautiously)
  Top residues: B168(LYS)=0.635, B170(SER)=0.610, B169(PHE)=0.592, B205(LEU)=0.589, B207(PHE)=0.581, B206(THR)=0.580, B204(GLN)=0.526, B167(VAL)=0.525

  How this pocket was identified:
    The model assigned high pocket probability to 11 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 28.4 A^2 (64% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 11 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #7  (secondary)
  ------------------------------------------------------------
  Residues: 7  |  Mean score: 0.569  |  Max score: 0.673
  Center (A): (46.7, 28.2, 43.1)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.14 (convex — surface protrusion, interpret cautiously)
  Top residues: A163(ALA)=0.673, A165(ASP)=0.643, A164(LYS)=0.618, A162(CYS)=0.588, A161(SER)=0.555, A203(VAL)=0.491, A166(GLY)=0.413

  How this pocket was identified:
    The model assigned high pocket probability to 7 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 46.8 A^2 (57% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 7 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #8  (secondary)
  ------------------------------------------------------------
  Residues: 4  |  Mean score: 0.499  |  Max score: 0.600
  Center (A): (41.4, -16.5, 1.4)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.50 (concave — geometrically pocket-like)
  Top residues: C168(LYS)=0.600, C170(SER)=0.506, C167(VAL)=0.452, C169(PHE)=0.438

  How this pocket was identified:
    The model assigned high pocket probability to 4 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 21.6 A^2 (75% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 4 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

Score distribution:
  Min=0.020  Max=0.754  Mean=0.193  Std=0.208
  21.0% of residues exceed threshold 0.4 (focused signal — clusters are reliable)
```

## Data Files

| File | Description |
|------|-------------|
| `results/per_structure/2ZVM/scores.csv` | Per-residue pocket scores |
| `results/per_structure/2ZVM/clusters.csv` | DBSCAN cluster assignments |
| `results/per_structure/2ZVM/report.txt` | Full text analysis report |
| `results/per_structure/2ZVM/summary.json` | Machine-readable summary |

---
*GNN-PCNA v2 | Dual-branch GATv2Conv | Checkpoint: `checkpoints/pcna/best_pcna.ckpt`*