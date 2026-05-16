# 9EOA — DNA BINDING

> Generated: 2026-05-16  |  Category: Other PCNA structure  

## Quick Stats

| Field | Value |
|-------|-------|
| PDB ID | [9EOA](https://www.rcsb.org/structure/9EOA) |
| Residues | 1337 across 4 chains |
| Ligands detected | none (apo) |
| AUROC | N/A (apo — no ligand for labeling) |
| Top pocket mean score | 0.5858 (60 residues) |
| AOH1996 GT overlap | #############.......  16/24 |
| Top pocket concavity | 0.600 (concave) |

## AOH1996 Pocket Assessment

Moderate overlap: **16/24 AOH1996 GT residues** recovered. Partial pocket opening may be present — this structure could bind AOH1996 in a conformation-dependent manner.

## Full Analysis Report

```
======================================================================
PDB: 9EOA
Title: DNA BINDING PROTEINCRYO_EM STRUCTURE OF HUMAN FAN1 IN COMPLEX WITH 5' FLAP DNA SUBSTRATE AND PCNA
Chains: A, F, G, H  |  Residues: 1337
Ligands detected: none (apo)
Residues above threshold (0.4): 200/1337 (15.0%)

Predicted cryptic pockets: 10

  Pocket #1  (PRIMARY)
  ------------------------------------------------------------
  Residues: 60  |  Mean score: 0.586  |  Max score: 0.723
  Center (A): (142.0, 122.7, 176.8)
  Structural region: C-terminal loop — AOH1996 cryptic pocket region
     19 residues in: C-terminal loop — AOH1996 cryptic pocket region
     14 residues in: Domain 2 core beta sheet
     10 residues in: N-terminal beta sheet (domain 1)
      9 residues in: Core beta sheet
      5 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      3 residues in: Front-face loop (PIP-box groove)
  AOH1996 pocket overlap: 16/24 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.60 (concave — geometrically pocket-like)
  Top residues: H234(PRO)=0.723, H235(LEU)=0.720, H233(VAL)=0.718, H232(ASP)=0.717, H236(VAL)=0.713, H230(SER)=0.706, H231(ALA)=0.703, H229(MET)=0.685

  How this pocket was identified:
    The model assigned high pocket probability to 60 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 33.9 A^2 (55% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 60 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the c-terminal loop — aoh1996 cryptic pocket region. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #2  (secondary)
  ------------------------------------------------------------
  Residues: 56  |  Mean score: 0.565  |  Max score: 0.676
  Center (A): (139.6, 174.7, 189.2)
  Structural region: Domain 2 core beta sheet
     14 residues in: Domain 2 core beta sheet
     14 residues in: C-terminal loop — AOH1996 cryptic pocket region
     10 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      9 residues in: Core beta sheet
      6 residues in: N-terminal beta sheet (domain 1)
      3 residues in: Front-face loop (PIP-box groove)
  AOH1996 pocket overlap: 13/24 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.59 (concave — geometrically pocket-like)
  Top residues: F228(SER)=0.676, F236(VAL)=0.673, F237(VAL)=0.667, F235(LEU)=0.666, F229(MET)=0.665, F227(LEU)=0.659, F226(THR)=0.652, F230(SER)=0.652

  How this pocket was identified:
    The model assigned high pocket probability to 56 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 33.9 A^2 (64% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 56 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the domain 2 core beta sheet. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #3  (secondary)
  ------------------------------------------------------------
  Residues: 25  |  Mean score: 0.639  |  Max score: 0.733
  Center (A): (167.1, 144.1, 114.0)
  Structural region: Core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.60 (concave — geometrically pocket-like)
  Top residues: A960(ASP)=0.733, A1002(GLU)=0.724, A1004(CYS)=0.723, A1003(VAL)=0.723, A959(PRO)=0.717, A961(LEU)=0.715, A974(VAL)=0.691, A975(GLU)=0.686

  How this pocket was identified:
    The model assigned high pocket probability to 25 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 23.6 A^2 (76% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 25 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #4  (secondary)
  ------------------------------------------------------------
  Residues: 22  |  Mean score: 0.539  |  Max score: 0.663
  Center (A): (183.5, 150.7, 200.0)
  Structural region: C-terminal loop — AOH1996 cryptic pocket region
      9 residues in: C-terminal loop — AOH1996 cryptic pocket region
      8 residues in: Domain 2 core beta sheet
      3 residues in: N-terminal beta sheet (domain 1)
      1 residues in: Front-face loop (PIP-box groove)
      1 residues in: Core beta sheet
  AOH1996 pocket overlap: 7/24 GT residues
  --> PARTIAL overlap: pocket partially covers the AOH1996 site
  Geometric concavity: 0.59 (concave — geometrically pocket-like)
  Top residues: G236(VAL)=0.663, G226(THR)=0.627, G225(VAL)=0.622, G228(SER)=0.614, G227(LEU)=0.610, G237(VAL)=0.606, G235(LEU)=0.601, G230(SER)=0.592

  How this pocket was identified:
    The model assigned high pocket probability to 22 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 23.0 A^2 (64% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 22 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #5  (secondary)
  ------------------------------------------------------------
  Residues: 10  |  Mean score: 0.574  |  Max score: 0.642
  Center (A): (127.3, 145.9, 173.7)
  Structural region: Core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.70 (concave — geometrically pocket-like)
  Top residues: H99(LEU)=0.642, H100(ALA)=0.622, H98(THR)=0.614, H101(LEU)=0.590, H117(LYS)=0.579, H115(GLU)=0.569, H102(VAL)=0.565, H97(ASP)=0.563

  How this pocket was identified:
    The model assigned high pocket probability to 10 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 46.7 A^2 (40% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 10 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #6  (secondary)
  ------------------------------------------------------------
  Residues: 9  |  Mean score: 0.539  |  Max score: 0.614
  Center (A): (128.6, 164.4, 179.1)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.78 (concave — geometrically pocket-like)
  Top residues: F170(SER)=0.614, F168(LYS)=0.588, F169(PHE)=0.583, F205(LEU)=0.552, F206(THR)=0.543, F207(PHE)=0.519, F159(VAL)=0.499, F204(GLN)=0.485

  How this pocket was identified:
    The model assigned high pocket probability to 9 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 34.9 A^2 (56% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 9 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #7  (secondary)
  ------------------------------------------------------------
  Residues: 3  |  Mean score: 0.602  |  Max score: 0.660
  Center (A): (164.6, 168.9, 118.2)
  Structural region: Core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 1.00 (concave — geometrically pocket-like)
  Top residues: A865(ALA)=0.660, A866(PHE)=0.607, A915(SER)=0.539

  How this pocket was identified:
    The model assigned high pocket probability to 3 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 40.5 A^2 (33% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 3 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #8  (secondary)
  ------------------------------------------------------------
  Residues: 5  |  Mean score: 0.450  |  Max score: 0.534
  Center (A): (160.1, 117.3, 178.1)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.80 (concave — geometrically pocket-like)
  Top residues: H205(LEU)=0.534, H170(SER)=0.481, H204(GLN)=0.418, H159(VAL)=0.416, H158(VAL)=0.401

  How this pocket was identified:
    The model assigned high pocket probability to 5 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 52.1 A^2 (40% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 5 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #9  (secondary)
  ------------------------------------------------------------
  Residues: 3  |  Mean score: 0.517  |  Max score: 0.604
  Center (A): (177.3, 123.2, 187.4)
  Structural region: Core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.67 (concave — geometrically pocket-like)
  Top residues: G98(THR)=0.604, G99(LEU)=0.523, G100(ALA)=0.423

  How this pocket was identified:
    The model assigned high pocket probability to 3 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 28.9 A^2 (67% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 3 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #10  (secondary)
  ------------------------------------------------------------
  Residues: 3  |  Mean score: 0.507  |  Max score: 0.511
  Center (A): (122.4, 157.9, 203.0)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.00 (convex — surface protrusion, interpret cautiously)
  Top residues: F186(SER)=0.511, F188(VAL)=0.511, F187(ASN)=0.500

  How this pocket was identified:
    The model assigned high pocket probability to 3 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 88.9 A^2 (0% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 3 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

Score distribution:
  Min=0.020  Max=0.733  Mean=0.156  Std=0.197
  15.0% of residues exceed threshold 0.4 (focused signal — clusters are reliable)
```

## Data Files

| File | Description |
|------|-------------|
| `results/per_structure/9EOA/scores.csv` | Per-residue pocket scores |
| `results/per_structure/9EOA/clusters.csv` | DBSCAN cluster assignments |
| `results/per_structure/9EOA/report.txt` | Full text analysis report |
| `results/per_structure/9EOA/summary.json` | Machine-readable summary |

---
*GNN-PCNA v2 | Dual-branch GATv2Conv | Checkpoint: `checkpoints/pcna/best_pcna.ckpt`*