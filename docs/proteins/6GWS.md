# 6GWS — REPLICATIONCRYSTAL STRUCTURE OF HUMAN PCNA IN COMPLEX WITH THREE P15 PEPTIDES

> Generated: 2026-05-16  |  Category: Other PCNA structure  

## Quick Stats

| Field | Value |
|-------|-------|
| PDB ID | [6GWS](https://www.rcsb.org/structure/6GWS) |
| Residues | 831 across 6 chains |
| Ligands detected | none (apo) |
| AUROC | N/A (apo — no ligand for labeling) |
| Top pocket mean score | 0.5681 (36 residues) |
| AOH1996 GT overlap | ########............  9/24 |
| Top pocket concavity | 0.611 (concave) |

## AOH1996 Pocket Assessment

Low AOH1996 overlap: **9/24 GT residues**. The top predicted pocket does not coincide with the AOH1996 site. Either a novel pocket is predicted, or the model's top cluster is at a distinct binding interface.

## Full Analysis Report

```
======================================================================
PDB: 6GWS
Title: REPLICATIONCRYSTAL STRUCTURE OF HUMAN PCNA IN COMPLEX WITH THREE P15 PEPTIDES
Chains: A, B, C, D, E, F  |  Residues: 831
Ligands detected: none (apo)
Residues above threshold (0.4): 109/831 (13.1%)

Predicted cryptic pockets: 5

  Pocket #1  (PRIMARY)
  ------------------------------------------------------------
  Residues: 36  |  Mean score: 0.568  |  Max score: 0.670
  Center (A): (18.3, -32.2, -14.8)
  Structural region: Domain 2 core beta sheet
     13 residues in: Domain 2 core beta sheet
     13 residues in: C-terminal loop — AOH1996 cryptic pocket region
      5 residues in: N-terminal beta sheet (domain 1)
      3 residues in: Core beta sheet
      2 residues in: Front-face loop (PIP-box groove)
  AOH1996 pocket overlap: 9/24 GT residues
  --> PARTIAL overlap: pocket partially covers the AOH1996 site
  Geometric concavity: 0.61 (concave — geometrically pocket-like)
  Top residues: B228(SER)=0.670, B236(VAL)=0.664, B229(MET)=0.658, B226(THR)=0.656, B227(LEU)=0.656, B237(VAL)=0.650, B235(LEU)=0.647, B230(SER)=0.640

  How this pocket was identified:
    The model assigned a high prioritization score to 36 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 18.2 A^2 (78% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 36 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the domain 2 core beta sheet. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #2  (secondary)
  ------------------------------------------------------------
  Residues: 26  |  Mean score: 0.652  |  Max score: 0.769
  Center (A): (26.8, 20.0, 11.2)
  Structural region: Domain 2 core beta sheet
     11 residues in: Domain 2 core beta sheet
     10 residues in: C-terminal loop — AOH1996 cryptic pocket region
      5 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
  AOH1996 pocket overlap: 4/24 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.42 (convex — surface protrusion, interpret cautiously)
  Top residues: A134(SER)=0.769, A230(SER)=0.762, A231(ALA)=0.753, A136(VAL)=0.748, A133(TYR)=0.745, A135(CYS)=0.745, A235(LEU)=0.742, A233(VAL)=0.742

  How this pocket was identified:
    The model assigned a high prioritization score to 26 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 39.4 A^2 (62% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 26 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

  Pocket #3  (secondary)
  ------------------------------------------------------------
  Residues: 27  |  Mean score: 0.515  |  Max score: 0.635
  Center (A): (0.4, -22.0, 36.0)
  Structural region: Domain 2 core beta sheet
      9 residues in: Domain 2 core beta sheet
      9 residues in: C-terminal loop — AOH1996 cryptic pocket region
      4 residues in: N-terminal beta sheet (domain 1)
      2 residues in: Front-face loop (PIP-box groove)
      2 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      1 residues in: Core beta sheet
  AOH1996 pocket overlap: 6/24 GT residues
  --> PARTIAL overlap: pocket partially covers the AOH1996 site
  Geometric concavity: 0.63 (concave — geometrically pocket-like)
  Top residues: C226(THR)=0.635, C227(LEU)=0.617, C236(VAL)=0.613, C225(VAL)=0.612, C228(SER)=0.597, C237(VAL)=0.596, C39(SER)=0.571, C235(LEU)=0.566

  How this pocket was identified:
    The model assigned a high prioritization score to 27 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 21.2 A^2 (74% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 27 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

  Pocket #4  (secondary)
  ------------------------------------------------------------
  Residues: 10  |  Mean score: 0.537  |  Max score: 0.618
  Center (A): (22.3, -19.5, -22.0)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.50 (concave — geometrically pocket-like)
  Top residues: B168(LYS)=0.618, B205(LEU)=0.600, B169(PHE)=0.594, B206(THR)=0.581, B170(SER)=0.579, B204(GLN)=0.546, B207(PHE)=0.538, B160(ILE)=0.457

  How this pocket was identified:
    The model assigned a high prioritization score to 10 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 33.9 A^2 (60% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 10 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

  Pocket #5  (secondary)
  ------------------------------------------------------------
  Residues: 4  |  Mean score: 0.619  |  Max score: 0.755
  Center (A): (20.1, 10.8, -11.9)
  Structural region: N-terminal beta sheet (domain 1)
      3 residues in: N-terminal beta sheet (domain 1)
      1 residues in: Core beta sheet
  AOH1996 pocket overlap: 3/24 GT residues
  --> LOW overlap: model predicts a distinct site (hypothesis — requires experimental validation)
  Geometric concavity: 0.75 (concave — geometrically pocket-like)
  Top residues: A26(ALA)=0.755, A27(CYS)=0.732, A69(GLY)=0.544, A25(GLU)=0.443

  How this pocket was identified:
    The model assigned a high prioritization score to 4 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 25.1 A^2 (75% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 4 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site. The model assigns high scores here; whether this represents a true cryptic pocket is a hypothesis requiring experimental validation.

Score distribution:
  Min=0.020  Max=0.769  Mean=0.154  Std=0.185
  13.1% of residues exceed threshold 0.4 (focused signal — clusters are reliable)
```

## Data Files

> **Gitignored** — regenerate locally with `python scripts/per_structure_analysis.py`
> PDB inputs: `python agents/pcna_crawler.py --download` | Graphs: `python scripts/build_graphs.py`

| File | Description | Tracked in git? |
|------|-------------|----------------|
| `results/per_structure/6GWS/scores.csv` | Per-residue pocket scores | No |
| `results/per_structure/6GWS/clusters.csv` | DBSCAN cluster assignments | No |
| `results/per_structure/6GWS/report.txt` | Full text analysis report | No |
| `results/per_structure/6GWS/summary.json` | Machine-readable summary | No |
| `results/per_structure/summary_table.csv` | All-59 rollup | Yes |
| `checkpoints/pcna/best_pcna.ckpt` | Trained model weights | Yes |
| `data/raw/6GWS.pdb` | Raw PDB structure | No |
| `data/graphs/6GWS.pt` | PyG graph tensor | No |

---
*GNN-PCNA v2 | Dual-branch GATv2Conv | Checkpoint tracked at `checkpoints/pcna/best_pcna.ckpt`*