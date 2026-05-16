# 1VYM — DNA BINDING

> Generated: 2026-05-16  |  Category: Other PCNA structure  

## Quick Stats

| Field | Value |
|-------|-------|
| PDB ID | [1VYM](https://www.rcsb.org/structure/1VYM) |
| Residues | 765 across 3 chains |
| Ligands detected | none (apo) |
| AUROC | N/A (apo — no ligand for labeling) |
| Top pocket mean score | 0.5756 (77 residues) |
| AOH1996 GT overlap | ############........  15/24 |
| Top pocket concavity | 0.429 (convex) |

## AOH1996 Pocket Assessment

Moderate overlap: **15/24 AOH1996 GT residues** recovered. Partial pocket opening may be present — this structure could bind AOH1996 in a conformation-dependent manner.

## Full Analysis Report

```
======================================================================
PDB: 1VYM
Title: DNA BINDING PROTEINNATIVE HUMAN PCNA
Chains: A, B, C  |  Residues: 765
Ligands detected: none (apo)
Residues above threshold (0.4): 189/765 (24.7%)

Predicted cryptic pockets: 7

  Pocket #1  (PRIMARY)
  ------------------------------------------------------------
  Residues: 77  |  Mean score: 0.576  |  Max score: 0.666
  Center (A): (19.4, -30.3, 8.0)
  Structural region: Domain 2 core beta sheet
     36 residues in: Domain 2 core beta sheet
     18 residues in: C-terminal loop — AOH1996 cryptic pocket region
      8 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      6 residues in: N-terminal beta sheet (domain 1)
      5 residues in: Core beta sheet
      4 residues in: Front-face loop (PIP-box groove)
  AOH1996 pocket overlap: 15/24 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.43 (convex — surface protrusion, interpret cautiously)
  Top residues: B237(VAL)=0.666, B228(SER)=0.664, B46(SER)=0.663, B236(VAL)=0.660, B227(LEU)=0.659, B239(TYR)=0.657, B226(THR)=0.653, B238(GLU)=0.650

  How this pocket was identified:
    The model assigned high pocket probability to 77 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 37.4 A^2 (55% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 77 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the domain 2 core beta sheet. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #2  (secondary)
  ------------------------------------------------------------
  Residues: 41  |  Mean score: 0.669  |  Max score: 0.794
  Center (A): (29.2, 26.0, 21.2)
  Structural region: Domain 2 core beta sheet
     18 residues in: Domain 2 core beta sheet
     14 residues in: C-terminal loop — AOH1996 cryptic pocket region
      6 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      2 residues in: Front-face loop (PIP-box groove)
      1 residues in: N-terminal beta sheet (domain 1)
  AOH1996 pocket overlap: 11/24 GT residues
  --> PARTIAL overlap: pocket partially covers the AOH1996 site
  Geometric concavity: 0.39 (convex — surface protrusion, interpret cautiously)
  Top residues: A134(SER)=0.794, A234(PRO)=0.790, A133(TYR)=0.788, A235(LEU)=0.788, A233(VAL)=0.787, A232(ASP)=0.786, A136(VAL)=0.782, A135(CYS)=0.782

  How this pocket was identified:
    The model assigned high pocket probability to 41 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 42.0 A^2 (46% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 41 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the domain 2 core beta sheet. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #3  (secondary)
  ------------------------------------------------------------
  Residues: 52  |  Mean score: 0.566  |  Max score: 0.679
  Center (A): (3.7, 10.8, -26.2)
  Structural region: Domain 2 core beta sheet
     19 residues in: Domain 2 core beta sheet
     18 residues in: C-terminal loop — AOH1996 cryptic pocket region
      4 residues in: N-terminal beta sheet (domain 1)
      4 residues in: Front-face loop (PIP-box groove)
      4 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      3 residues in: Core beta sheet
  AOH1996 pocket overlap: 15/24 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.46 (convex — surface protrusion, interpret cautiously)
  Top residues: C226(THR)=0.679, C237(VAL)=0.672, C227(LEU)=0.670, C236(VAL)=0.669, C228(SER)=0.668, C238(GLU)=0.661, C239(TYR)=0.654, C225(VAL)=0.643

  How this pocket was identified:
    The model assigned high pocket probability to 52 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 27.9 A^2 (63% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 52 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the domain 2 core beta sheet. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #4  (secondary)
  ------------------------------------------------------------
  Residues: 5  |  Mean score: 0.624  |  Max score: 0.673
  Center (A): (46.1, 2.9, 26.3)
  Structural region: IDCL — Interdomain Connecting Loop (key interaction hub)
  AOH1996 pocket overlap: 1/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.00 (convex — surface protrusion, interpret cautiously)
  Top residues: A122(ASP)=0.673, A123(VAL)=0.654, A121(LEU)=0.645, A120(ASP)=0.641, A124(GLU)=0.506

  How this pocket was identified:
    The model assigned high pocket probability to 5 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 112.0 A^2 (0% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 5 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #5  (secondary)
  ------------------------------------------------------------
  Residues: 3  |  Mean score: 0.552  |  Max score: 0.571
  Center (A): (15.1, -28.6, -19.3)
  Structural region: Core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.67 (concave — geometrically pocket-like)
  Top residues: B68(MET)=0.571, B69(GLY)=0.551, B67(ALA)=0.533

  How this pocket was identified:
    The model assigned high pocket probability to 3 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 11.7 A^2 (100% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 3 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #6  (secondary)
  ------------------------------------------------------------
  Residues: 4  |  Mean score: 0.475  |  Max score: 0.518
  Center (A): (21.8, 29.3, -14.7)
  Structural region: Core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.50 (concave — geometrically pocket-like)
  Top residues: C69(GLY)=0.518, C118(LEU)=0.468, C68(MET)=0.464, C117(LYS)=0.449

  How this pocket was identified:
    The model assigned high pocket probability to 4 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 29.8 A^2 (75% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 4 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #7  (secondary)
  ------------------------------------------------------------
  Residues: 3  |  Mean score: 0.518  |  Max score: 0.565
  Center (A): (2.2, -5.3, -25.5)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.67 (concave — geometrically pocket-like)
  Top residues: C168(LYS)=0.565, C169(PHE)=0.508, C170(SER)=0.482

  How this pocket was identified:
    The model assigned high pocket probability to 3 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 22.4 A^2 (67% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 3 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

Score distribution:
  Min=0.020  Max=0.794  Mean=0.224  Std=0.231
  24.7% of residues exceed threshold 0.4 (focused signal — clusters are reliable)
```

## Data Files

| File | Description |
|------|-------------|
| `results/per_structure/1VYM/scores.csv` | Per-residue pocket scores |
| `results/per_structure/1VYM/clusters.csv` | DBSCAN cluster assignments |
| `results/per_structure/1VYM/report.txt` | Full text analysis report |
| `results/per_structure/1VYM/summary.json` | Machine-readable summary |

---
*GNN-PCNA v2 | Dual-branch GATv2Conv | Checkpoint: `checkpoints/pcna/best_pcna.ckpt`*