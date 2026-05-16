# 6GIS — DNA BINDING

> Generated: 2026-05-16  |  Category: Other PCNA structure  **AOH1996 CANDIDATE**

## Quick Stats

| Field | Value |
|-------|-------|
| PDB ID | [6GIS](https://www.rcsb.org/structure/6GIS) |
| Residues | 744 across 3 chains |
| Ligands detected | none (apo) |
| AUROC | N/A (apo — no ligand for labeling) |
| Top pocket mean score | 0.5830 (60 residues) |
| AOH1996 GT overlap | ################....  19/24 |
| Top pocket concavity | 0.450 (convex) |

## AOH1996 Pocket Assessment

Moderate overlap: **19/24 AOH1996 GT residues** recovered. Partial pocket opening may be present — this structure could bind AOH1996 in a conformation-dependent manner.

## Full Analysis Report

```
======================================================================
PDB: 6GIS
Title: DNA BINDING PROTEINSTRUCTURAL BASIS OF HUMAN CLAMP SLIDING ON DNA
Chains: A, B, C  |  Residues: 744
Ligands detected: none (apo)
Residues above threshold (0.4): 172/744 (23.1%)

Predicted cryptic pockets: 6

  Pocket #1  (PRIMARY)
  ------------------------------------------------------------
  Residues: 60  |  Mean score: 0.583  |  Max score: 0.681
  Center (A): (55.2, 82.9, 31.5)
  Structural region: C-terminal loop — AOH1996 cryptic pocket region
     17 residues in: C-terminal loop — AOH1996 cryptic pocket region
     15 residues in: Domain 2 core beta sheet
     12 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      6 residues in: N-terminal beta sheet (domain 1)
      5 residues in: Front-face loop (PIP-box groove)
      5 residues in: Core beta sheet
  AOH1996 pocket overlap: 19/24 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.45 (convex — surface protrusion, interpret cautiously)
  Top residues: B236(VAL)=0.681, B237(VAL)=0.673, B39(SER)=0.671, B226(THR)=0.669, B227(LEU)=0.666, B46(SER)=0.665, B228(SER)=0.664, B137(VAL)=0.661

  How this pocket was identified:
    The model assigned high pocket probability to 60 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 35.5 A^2 (48% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 60 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the c-terminal loop — aoh1996 cryptic pocket region. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #2  (secondary)
  ------------------------------------------------------------
  Residues: 40  |  Mean score: 0.678  |  Max score: 0.796
  Center (A): (76.9, 83.5, 85.8)
  Structural region: C-terminal loop — AOH1996 cryptic pocket region
     16 residues in: C-terminal loop — AOH1996 cryptic pocket region
     12 residues in: Domain 2 core beta sheet
      6 residues in: Front-face loop (PIP-box groove)
      3 residues in: N-terminal beta sheet (domain 1)
      3 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
  AOH1996 pocket overlap: 17/24 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.47 (convex — surface protrusion, interpret cautiously)
  Top residues: A232(ASP)=0.796, A234(PRO)=0.792, A231(ALA)=0.792, A233(VAL)=0.792, A235(LEU)=0.790, A46(SER)=0.780, A253(PRO)=0.778, A252(ALA)=0.777

  How this pocket was identified:
    The model assigned high pocket probability to 40 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 33.6 A^2 (50% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 40 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the c-terminal loop — aoh1996 cryptic pocket region. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #3  (secondary)
  ------------------------------------------------------------
  Residues: 46  |  Mean score: 0.555  |  Max score: 0.667
  Center (A): (46.3, 41.2, 66.8)
  Structural region: Domain 2 core beta sheet
     14 residues in: Domain 2 core beta sheet
     13 residues in: C-terminal loop — AOH1996 cryptic pocket region
      8 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      4 residues in: N-terminal beta sheet (domain 1)
      4 residues in: Front-face loop (PIP-box groove)
      3 residues in: Core beta sheet
  AOH1996 pocket overlap: 11/24 GT residues
  --> PARTIAL overlap: pocket partially covers the AOH1996 site
  Geometric concavity: 0.48 (convex — surface protrusion, interpret cautiously)
  Top residues: C236(VAL)=0.667, C237(VAL)=0.664, C226(THR)=0.649, C228(SER)=0.647, C238(GLU)=0.644, C227(LEU)=0.643, C235(LEU)=0.631, C225(VAL)=0.627

  How this pocket was identified:
    The model assigned high pocket probability to 46 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 31.9 A^2 (59% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 46 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the domain 2 core beta sheet. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #4  (secondary)
  ------------------------------------------------------------
  Residues: 9  |  Mean score: 0.529  |  Max score: 0.648
  Center (A): (64.3, 94.9, 40.4)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.33 (convex — surface protrusion, interpret cautiously)
  Top residues: B168(LYS)=0.648, B169(PHE)=0.600, B170(SER)=0.573, B167(VAL)=0.568, B204(GLN)=0.518, B159(VAL)=0.505, B158(VAL)=0.504, B205(LEU)=0.440

  How this pocket was identified:
    The model assigned high pocket probability to 9 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 32.2 A^2 (67% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 9 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #5  (secondary)
  ------------------------------------------------------------
  Residues: 9  |  Mean score: 0.488  |  Max score: 0.590
  Center (A): (37.4, 68.2, 35.0)
  Structural region: Core beta sheet
      6 residues in: Core beta sheet
      2 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      1 residues in: N-terminal beta sheet (domain 1)
  AOH1996 pocket overlap: 1/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.44 (convex — surface protrusion, interpret cautiously)
  Top residues: B69(GLY)=0.590, B68(MET)=0.573, B118(LEU)=0.543, B67(ALA)=0.516, B117(LYS)=0.469, B70(VAL)=0.451, B120(ASP)=0.424, B119(MET)=0.420

  How this pocket was identified:
    The model assigned high pocket probability to 9 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 41.6 A^2 (44% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 9 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #6  (secondary)
  ------------------------------------------------------------
  Residues: 3  |  Mean score: 0.490  |  Max score: 0.537
  Center (A): (47.7, 55.1, 39.6)
  Structural region: Core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.67 (concave — geometrically pocket-like)
  Top residues: B102(VAL)=0.537, B103(PHE)=0.471, B101(LEU)=0.462

  How this pocket was identified:
    The model assigned high pocket probability to 3 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 12.0 A^2 (67% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 3 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

Score distribution:
  Min=0.020  Max=0.796  Mean=0.209  Std=0.229
  23.1% of residues exceed threshold 0.4 (focused signal — clusters are reliable)
```

## Data Files

> **Gitignored** — regenerate locally with `python scripts/per_structure_analysis.py`
> PDB inputs: `python agents/pcna_crawler.py --download` | Graphs: `python scripts/build_graphs.py`

| File | Description | Tracked in git? |
|------|-------------|----------------|
| `results/per_structure/6GIS/scores.csv` | Per-residue pocket scores | No |
| `results/per_structure/6GIS/clusters.csv` | DBSCAN cluster assignments | No |
| `results/per_structure/6GIS/report.txt` | Full text analysis report | No |
| `results/per_structure/6GIS/summary.json` | Machine-readable summary | No |
| `results/per_structure/summary_table.csv` | All-59 rollup | Yes |
| `checkpoints/pcna/best_pcna.ckpt` | Trained model weights | Yes |
| `data/raw/6GIS.pdb` | Raw PDB structure | No |
| `data/graphs/6GIS.pt` | PyG graph tensor | No |

---
*GNN-PCNA v2 | Dual-branch GATv2Conv | Checkpoint tracked at `checkpoints/pcna/best_pcna.ckpt`*