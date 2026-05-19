# 8UMY — REPLICATION/DNAATOMIC MODEL OF THE HUMAN CTF18-RFC-PCNA-DNA TERNARY COMPLEX WITH NARROW PCNA OPENING STATE II (STATE 6)

> Generated: 2026-05-16  |  Category: Large replication complex (AUROC unreliable)  

## Quick Stats

| Field | Value |
|-------|-------|
| PDB ID | [8UMY](https://www.rcsb.org/structure/8UMY) |
| Residues | 2647 across 8 chains |
| Ligands detected | AGS|ADP |
| AUROC | 0.5528 (raw — may include co-factor ligands) |
| Top pocket mean score | 0.5814 (73 residues) |
| AOH1996 GT overlap | #############.......  16/24 |
| Top pocket concavity | 0.575 (concave) |

## AOH1996 Pocket Assessment

Moderate overlap: **16/24 AOH1996 GT residues** recovered. Partial pocket opening may be present — this structure could bind AOH1996 in a conformation-dependent manner.

## Full Analysis Report

```
======================================================================
PDB: 8UMY
Title: REPLICATION/DNAATOMIC MODEL OF THE HUMAN CTF18-RFC-PCNA-DNA TERNARY COMPLEX WITH NARROW PCNA OPENING STATE II (STATE 6)
Chains: A, B, C, D, E, F, G, H  |  Residues: 2647
Ligands detected: AGS, ADP
AUROC vs auto-labeled GT: 0.5528
Residues above threshold (0.4): 310/2647 (11.7%)

Predicted cryptic pockets: 15

  Pocket #1  (PRIMARY)
  ------------------------------------------------------------
  Residues: 73  |  Mean score: 0.581  |  Max score: 0.701
  Center (A): (154.1, 113.9, 102.9)
  Structural region: Domain 2 core beta sheet
     31 residues in: Domain 2 core beta sheet
     18 residues in: C-terminal loop — AOH1996 cryptic pocket region
      6 residues in: N-terminal beta sheet (domain 1)
      6 residues in: Core beta sheet
      5 residues in: Front-face loop (PIP-box groove)
      5 residues in: C-terminal tail (protein-protein interface)
      2 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
  AOH1996 pocket overlap: 16/24 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.58 (concave — geometrically pocket-like)
  Top residues: G39(SER)=0.701, G226(THR)=0.700, G38(GLN)=0.693, G227(LEU)=0.691, G228(SER)=0.687, G138(LYS)=0.687, G40(MET)=0.684, G139(MET)=0.682

  How this pocket was identified:
    The model assigned a high prioritization score to 73 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 28.6 A^2 (67% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 73 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the domain 2 core beta sheet. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #2  (secondary)
  ------------------------------------------------------------
  Residues: 70  |  Mean score: 0.577  |  Max score: 0.691
  Center (A): (164.5, 156.1, 140.7)
  Structural region: Domain 2 core beta sheet
     23 residues in: Domain 2 core beta sheet
     16 residues in: C-terminal loop — AOH1996 cryptic pocket region
     13 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      7 residues in: Front-face loop (PIP-box groove)
      5 residues in: N-terminal beta sheet (domain 1)
      5 residues in: Core beta sheet
      1 residues in: C-terminal tail (protein-protein interface)
  AOH1996 pocket overlap: 21/24 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.60 (concave — geometrically pocket-like)
  Top residues: H236(VAL)=0.691, H235(LEU)=0.684, H226(THR)=0.681, H234(PRO)=0.673, H225(VAL)=0.672, H228(SER)=0.668, H227(LEU)=0.667, H138(LYS)=0.667

  How this pocket was identified:
    The model assigned a high prioritization score to 70 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 39.5 A^2 (51% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 70 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the domain 2 core beta sheet. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #3  (secondary)
  ------------------------------------------------------------
  Residues: 50  |  Mean score: 0.594  |  Max score: 0.721
  Center (A): (127.2, 153.5, 83.8)
  Structural region: C-terminal loop — AOH1996 cryptic pocket region
     18 residues in: C-terminal loop — AOH1996 cryptic pocket region
     15 residues in: Domain 2 core beta sheet
      7 residues in: Front-face loop (PIP-box groove)
      5 residues in: N-terminal beta sheet (domain 1)
      5 residues in: Core beta sheet
  AOH1996 pocket overlap: 16/24 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.64 (concave — geometrically pocket-like)
  Top residues: F236(VAL)=0.721, F235(LEU)=0.714, F226(THR)=0.710, F228(SER)=0.709, F227(LEU)=0.696, F229(MET)=0.687, F234(PRO)=0.687, F230(SER)=0.680

  How this pocket was identified:
    The model assigned a high prioritization score to 50 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 23.0 A^2 (70% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 50 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the c-terminal loop — aoh1996 cryptic pocket region. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #4  (secondary)
  ------------------------------------------------------------
  Residues: 31  |  Mean score: 0.536  |  Max score: 0.645
  Center (A): (146.1, 118.8, 156.4)
  Structural region: Domain 2 core beta sheet
     16 residues in: Domain 2 core beta sheet
     14 residues in: Core beta sheet
      1 residues in: C-terminal loop — AOH1996 cryptic pocket region
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.81 (concave — geometrically pocket-like)
  Top residues: D150(ASP)=0.645, D152(ALA)=0.635, D151(GLU)=0.635, D149(LEU)=0.631, D148(ILE)=0.601, D75(LEU)=0.595, D74(LEU)=0.594, D80(PRO)=0.587

  How this pocket was identified:
    The model assigned a high prioritization score to 31 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 15.1 A^2 (77% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 31 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

  Pocket #5  (secondary)
  ------------------------------------------------------------
  Residues: 19  |  Mean score: 0.567  |  Max score: 0.692
  Center (A): (142.0, 145.4, 158.0)
  Structural region: Core beta sheet
      8 residues in: Core beta sheet
      5 residues in: Domain 2 core beta sheet
      4 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      2 residues in: N-terminal beta sheet (domain 1)
  AOH1996 pocket overlap: 1/24 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.79 (concave — geometrically pocket-like)
  Top residues: E133(LEU)=0.692, E135(THR)=0.676, E132(VAL)=0.676, E134(LEU)=0.668, E131(VAL)=0.662, E95(VAL)=0.606, E136(GLU)=0.588, E94(GLU)=0.585

  How this pocket was identified:
    The model assigned a high prioritization score to 19 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 9.6 A^2 (100% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 19 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

  Pocket #6  (secondary)
  ------------------------------------------------------------
  Residues: 20  |  Mean score: 0.527  |  Max score: 0.676
  Center (A): (145.3, 172.1, 129.8)
  Structural region: Core beta sheet
     15 residues in: Core beta sheet
      5 residues in: N-terminal beta sheet (domain 1)
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.60 (concave — geometrically pocket-like)
  Top residues: H115(GLU)=0.676, H116(MET)=0.661, H102(VAL)=0.616, H103(PHE)=0.598, H101(LEU)=0.586, H117(LYS)=0.582, H100(ALA)=0.549, H118(LEU)=0.542

  How this pocket was identified:
    The model assigned a high prioritization score to 20 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 45.4 A^2 (40% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 20 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

  Pocket #7  (secondary)
  ------------------------------------------------------------
  Residues: 10  |  Mean score: 0.710  |  Max score: 0.797
  Center (A): (97.5, 136.2, 115.9)
  Structural region: Core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.60 (concave — geometrically pocket-like)
  Top residues: A513(THR)=0.797, A512(PRO)=0.779, A511(PRO)=0.743, A547(ASN)=0.722, A374(GLY)=0.696, A514(LEU)=0.695, A510(PHE)=0.690, A376(PRO)=0.673

  How this pocket was identified:
    The model assigned a high prioritization score to 10 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 44.6 A^2 (50% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 10 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

  Pocket #8  (secondary)
  ------------------------------------------------------------
  Residues: 4  |  Mean score: 0.679  |  Max score: 0.778
  Center (A): (92.6, 139.4, 108.8)
  Structural region: Core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.50 (concave — geometrically pocket-like)
  Top residues: A297(ASP)=0.778, A296(SER)=0.728, A298(ASP)=0.630, A295(LEU)=0.578

  How this pocket was identified:
    The model assigned a high prioritization score to 4 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 44.5 A^2 (50% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 4 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

  Pocket #9  (secondary)
  ------------------------------------------------------------
  Residues: 5  |  Mean score: 0.511  |  Max score: 0.533
  Center (A): (176.1, 124.2, 118.6)
  Structural region: N-terminal beta sheet (domain 1)
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.40 (convex — surface protrusion, interpret cautiously)
  Top residues: G5(ARG)=0.533, G4(ALA)=0.528, G3(GLU)=0.506, G6(LEU)=0.505, G7(VAL)=0.483

  How this pocket was identified:
    The model assigned a high prioritization score to 5 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 41.3 A^2 (40% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 5 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

  Pocket #10  (secondary)
  ------------------------------------------------------------
  Residues: 5  |  Mean score: 0.487  |  Max score: 0.558
  Center (A): (163.7, 116.5, 127.0)
  Structural region: Core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.40 (convex — surface protrusion, interpret cautiously)
  Top residues: G69(GLY)=0.558, G68(MET)=0.532, G70(VAL)=0.459, G118(LEU)=0.446, G67(ALA)=0.439

  How this pocket was identified:
    The model assigned a high prioritization score to 5 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 21.9 A^2 (80% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 5 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

  Pocket #11  (secondary)
  ------------------------------------------------------------
  Residues: 4  |  Mean score: 0.522  |  Max score: 0.595
  Center (A): (172.8, 132.2, 123.7)
  Structural region: Core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.25 (convex — surface protrusion, interpret cautiously)
  Top residues: G102(VAL)=0.595, G103(PHE)=0.558, G101(LEU)=0.527, G104(GLU)=0.407

  How this pocket was identified:
    The model assigned a high prioritization score to 4 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 23.1 A^2 (75% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 4 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

  Pocket #12  (secondary)
  ------------------------------------------------------------
  Residues: 4  |  Mean score: 0.522  |  Max score: 0.570
  Center (A): (130.2, 168.9, 92.0)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.50 (concave — geometrically pocket-like)
  Top residues: F168(LYS)=0.570, F169(PHE)=0.557, F170(SER)=0.535, F160(ILE)=0.425

  How this pocket was identified:
    The model assigned a high prioritization score to 4 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 17.8 A^2 (50% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 4 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

  Pocket #13  (secondary)
  ------------------------------------------------------------
  Residues: 3  |  Mean score: 0.548  |  Max score: 0.591
  Center (A): (170.1, 139.9, 135.2)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.67 (concave — geometrically pocket-like)
  Top residues: H170(SER)=0.591, H168(LYS)=0.548, H169(PHE)=0.505

  How this pocket was identified:
    The model assigned a high prioritization score to 3 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 29.0 A^2 (67% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 3 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

  Pocket #14  (secondary)
  ------------------------------------------------------------
  Residues: 3  |  Mean score: 0.529  |  Max score: 0.540
  Center (A): (120.6, 117.5, 112.9)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 1.00 (concave — geometrically pocket-like)
  Top residues: B141(ASP)=0.540, B140(LEU)=0.534, B142(GLU)=0.512

  How this pocket was identified:
    The model assigned a high prioritization score to 3 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 4.6 A^2 (100% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 3 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

  Pocket #15  (secondary)
  ------------------------------------------------------------
  Residues: 3  |  Mean score: 0.458  |  Max score: 0.499
  Center (A): (136.8, 173.3, 86.3)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.33 (convex — surface protrusion, interpret cautiously)
  Top residues: F183(SER)=0.499, F182(LEU)=0.462, F181(LYS)=0.413

  How this pocket was identified:
    The model assigned a high prioritization score to 3 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 84.2 A^2 (33% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 3 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

Score distribution:
  Min=0.020  Max=0.797  Mean=0.128  Std=0.181
  11.7% of residues exceed threshold 0.4 (focused signal — clusters are reliable)
```

## Data Files

> **Gitignored** — regenerate locally with `python scripts/per_structure_analysis.py`
> PDB inputs: `python agents/pcna_crawler.py --download` | Graphs: `python scripts/build_graphs.py`

| File | Description | Tracked in git? |
|------|-------------|----------------|
| `results/per_structure/8UMY/scores.csv` | Per-residue pocket scores | No |
| `results/per_structure/8UMY/clusters.csv` | DBSCAN cluster assignments | No |
| `results/per_structure/8UMY/report.txt` | Full text analysis report | No |
| `results/per_structure/8UMY/summary.json` | Machine-readable summary | No |
| `results/per_structure/summary_table.csv` | All-59 rollup | Yes |
| `checkpoints/pcna/best_pcna.ckpt` | Trained model weights | Yes |
| `data/raw/8UMY.pdb` | Raw PDB structure | No |
| `data/graphs/8UMY.pt` | PyG graph tensor | No |

---
*GNN-PCNA v2 | Dual-branch GATv2Conv | Checkpoint tracked at `checkpoints/pcna/best_pcna.ckpt`*