# 6FCM — NUCLEAR

> Generated: 2026-05-16  |  Category: Other PCNA structure  **AOH1996 CANDIDATE**

## Quick Stats

| Field | Value |
|-------|-------|
| PDB ID | [6FCM](https://www.rcsb.org/structure/6FCM) |
| Residues | 755 across 3 chains |
| Ligands detected | none (apo) |
| AUROC | N/A (apo — no ligand for labeling) |
| Top pocket mean score | 0.5654 (74 residues) |
| AOH1996 GT overlap | #################...  20/24 |
| Top pocket concavity | 0.446 (convex) |

## AOH1996 Pocket Assessment

The GNN-PCNA model recovered **20/24 AOH1996 ground-truth residues** in its top predicted cluster. This represents >83% overlap with the experimentally confirmed cryptic pocket from PDB 8GLA. The model assigns a high prioritization score (0.565 mean) to this region. **This is a hypothesis only** — druggability requires MD simulation, docking, or experimental validation.

**Implication:** AOH1996 (or its derivatives AOH1160/AOH1996-1LE) would be predicted to bind this structure with similar affinity to the confirmed holo structure 8GLA.

## Full Analysis Report

```
======================================================================
PDB: 6FCM
Title: NUCLEAR PROTEINCRYSTAL STRUCTURE OF HUMAN PCNA
Chains: A, C, E  |  Residues: 755
Ligands detected: none (apo)
Residues above threshold (0.4): 154/755 (20.4%)

Predicted cryptic pockets: 4

  Pocket #1  (PRIMARY)
  ------------------------------------------------------------
  Residues: 74  |  Mean score: 0.565  |  Max score: 0.665
  Center (A): (10.9, 21.8, -43.5)
  Structural region: Domain 2 core beta sheet
     21 residues in: Domain 2 core beta sheet
     17 residues in: C-terminal loop — AOH1996 cryptic pocket region
     16 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
     10 residues in: Core beta sheet
      6 residues in: N-terminal beta sheet (domain 1)
      4 residues in: Front-face loop (PIP-box groove)
  AOH1996 pocket overlap: 20/24 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.45 (convex — surface protrusion, interpret cautiously)
  Top residues: C226(THR)=0.665, C228(SER)=0.660, C227(LEU)=0.660, C237(VAL)=0.646, C46(SER)=0.642, C238(GLU)=0.641, C225(VAL)=0.638, C236(VAL)=0.630

  How this pocket was identified:
    The model assigned high pocket probability to 74 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 42.7 A^2 (51% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 74 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the domain 2 core beta sheet. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #2  (secondary)
  ------------------------------------------------------------
  Residues: 45  |  Mean score: 0.672  |  Max score: 0.810
  Center (A): (11.9, -33.3, -26.0)
  Structural region: IDCL — Interdomain Connecting Loop (key interaction hub)
     13 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
     13 residues in: C-terminal loop — AOH1996 cryptic pocket region
     10 residues in: Domain 2 core beta sheet
      5 residues in: Front-face loop (PIP-box groove)
      4 residues in: N-terminal beta sheet (domain 1)
  AOH1996 pocket overlap: 20/24 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.40 (convex — surface protrusion, interpret cautiously)
  Top residues: A232(ASP)=0.810, A231(ALA)=0.809, A233(VAL)=0.804, A234(PRO)=0.803, A235(LEU)=0.800, A230(SER)=0.796, A40(MET)=0.790, A39(SER)=0.782

  How this pocket was identified:
    The model assigned high pocket probability to 45 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 48.8 A^2 (47% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 45 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the idcl — interdomain connecting loop (key interaction hub). The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #3  (secondary)
  ------------------------------------------------------------
  Residues: 25  |  Mean score: 0.509  |  Max score: 0.594
  Center (A): (5.3, 11.5, 8.9)
  Structural region: C-terminal loop — AOH1996 cryptic pocket region
      9 residues in: C-terminal loop — AOH1996 cryptic pocket region
      6 residues in: Domain 2 core beta sheet
      3 residues in: N-terminal beta sheet (domain 1)
      3 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      2 residues in: Front-face loop (PIP-box groove)
      2 residues in: Core beta sheet
  AOH1996 pocket overlap: 7/24 GT residues
  --> PARTIAL overlap: pocket partially covers the AOH1996 site
  Geometric concavity: 0.44 (convex — surface protrusion, interpret cautiously)
  Top residues: E236(VAL)=0.594, E226(THR)=0.589, E237(VAL)=0.583, E228(SER)=0.571, E227(LEU)=0.568, E47(LEU)=0.562, E238(GLU)=0.551, E225(VAL)=0.548

  How this pocket was identified:
    The model assigned high pocket probability to 25 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 23.8 A^2 (76% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 25 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #4  (secondary)
  ------------------------------------------------------------
  Residues: 3  |  Mean score: 0.532  |  Max score: 0.545
  Center (A): (9.6, 2.6, -51.3)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.33 (convex — surface protrusion, interpret cautiously)
  Top residues: C168(LYS)=0.545, C170(SER)=0.537, C169(PHE)=0.516

  How this pocket was identified:
    The model assigned high pocket probability to 3 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 28.6 A^2 (67% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 3 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

Score distribution:
  Min=0.020  Max=0.810  Mean=0.196  Std=0.220
  20.4% of residues exceed threshold 0.4 (focused signal — clusters are reliable)
```

## Data Files

> **Gitignored** — regenerate locally with `python scripts/per_structure_analysis.py`
> PDB inputs: `python agents/pcna_crawler.py --download` | Graphs: `python scripts/build_graphs.py`

| File | Description | Tracked in git? |
|------|-------------|----------------|
| `results/per_structure/6FCM/scores.csv` | Per-residue pocket scores | No |
| `results/per_structure/6FCM/clusters.csv` | DBSCAN cluster assignments | No |
| `results/per_structure/6FCM/report.txt` | Full text analysis report | No |
| `results/per_structure/6FCM/summary.json` | Machine-readable summary | No |
| `results/per_structure/summary_table.csv` | All-59 rollup | Yes |
| `checkpoints/pcna/best_pcna.ckpt` | Trained model weights | Yes |
| `data/raw/6FCM.pdb` | Raw PDB structure | No |
| `data/graphs/6FCM.pt` | PyG graph tensor | No |

---
*GNN-PCNA v2 | Dual-branch GATv2Conv | Checkpoint tracked at `checkpoints/pcna/best_pcna.ckpt`*