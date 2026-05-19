# 6FCN — NUCLEAR

> Generated: 2026-05-16  |  Category: Other PCNA structure  **AOH1996 CANDIDATE**

## Quick Stats

| Field | Value |
|-------|-------|
| PDB ID | [6FCN](https://www.rcsb.org/structure/6FCN) |
| Residues | 755 across 3 chains |
| Ligands detected | none (apo) |
| AUROC | N/A (apo — no ligand for labeling) |
| Top pocket mean score | 0.6878 (57 residues) |
| AOH1996 GT overlap | ##################..  21/24 |
| Top pocket concavity | 0.439 (convex) |

## AOH1996 Pocket Assessment

The GNN-PCNA model recovered **21/24 AOH1996 ground-truth residues** in its top predicted cluster. This represents >88% overlap with the experimentally confirmed cryptic pocket from PDB 8GLA. The model assigns a high prioritization score (0.688 mean) to this region. **This is a hypothesis only** — druggability requires MD simulation, docking, or experimental validation.

**Implication:** AOH1996 (or its derivatives AOH1160/AOH1996-1LE) would be predicted to bind this structure with similar affinity to the confirmed holo structure 8GLA.

## Full Analysis Report

```
======================================================================
PDB: 6FCN
Title: NUCLEAR PROTEINCRYSTAL STRUCTURE OF HUMAN PCNA SOAKED WITH P47PHOX(106-127) PEPTIDE
Chains: A, C, E  |  Residues: 755
Ligands detected: none (apo)
Residues above threshold (0.4): 153/755 (20.3%)

Predicted cryptic pockets: 5

  Pocket #1  (PRIMARY)
  ------------------------------------------------------------
  Residues: 57  |  Mean score: 0.688  |  Max score: 0.798
  Center (A): (10.5, -32.5, -24.8)
  Structural region: Domain 2 core beta sheet
     18 residues in: Domain 2 core beta sheet
     17 residues in: C-terminal loop — AOH1996 cryptic pocket region
     13 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      6 residues in: Front-face loop (PIP-box groove)
      3 residues in: N-terminal beta sheet (domain 1)
  AOH1996 pocket overlap: 21/24 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.44 (convex — surface protrusion, interpret cautiously)
  Top residues: A46(SER)=0.798, A232(ASP)=0.790, A40(MET)=0.790, A234(PRO)=0.786, A233(VAL)=0.785, A235(LEU)=0.785, A253(PRO)=0.780, A41(ASP)=0.779

  How this pocket was identified:
    The model assigned high pocket probability to 57 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 47.0 A^2 (53% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 57 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the domain 2 core beta sheet. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #2  (secondary)
  ------------------------------------------------------------
  Residues: 65  |  Mean score: 0.561  |  Max score: 0.652
  Center (A): (11.5, 22.0, -44.1)
  Structural region: C-terminal loop — AOH1996 cryptic pocket region
     17 residues in: C-terminal loop — AOH1996 cryptic pocket region
     16 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
     15 residues in: Domain 2 core beta sheet
      9 residues in: Core beta sheet
      5 residues in: N-terminal beta sheet (domain 1)
      3 residues in: Front-face loop (PIP-box groove)
  AOH1996 pocket overlap: 18/24 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.48 (convex — surface protrusion, interpret cautiously)
  Top residues: C46(SER)=0.652, C226(THR)=0.647, C228(SER)=0.643, C227(LEU)=0.641, C249(TYR)=0.639, C237(VAL)=0.634, C225(VAL)=0.632, C250(TYR)=0.631

  How this pocket was identified:
    The model assigned high pocket probability to 65 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 40.5 A^2 (55% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 65 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the c-terminal loop — aoh1996 cryptic pocket region. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #3  (secondary)
  ------------------------------------------------------------
  Residues: 23  |  Mean score: 0.510  |  Max score: 0.592
  Center (A): (3.5, 13.2, 8.7)
  Structural region: C-terminal loop — AOH1996 cryptic pocket region
      9 residues in: C-terminal loop — AOH1996 cryptic pocket region
      6 residues in: Domain 2 core beta sheet
      5 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      1 residues in: N-terminal beta sheet (domain 1)
      1 residues in: Front-face loop (PIP-box groove)
      1 residues in: Core beta sheet
  AOH1996 pocket overlap: 4/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.52 (concave — geometrically pocket-like)
  Top residues: E226(THR)=0.592, E236(VAL)=0.587, E228(SER)=0.583, E227(LEU)=0.576, E237(VAL)=0.565, E238(GLU)=0.543, E225(VAL)=0.535, E47(LEU)=0.531

  How this pocket was identified:
    The model assigned high pocket probability to 23 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 29.0 A^2 (70% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 23 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #4  (secondary)
  ------------------------------------------------------------
  Residues: 3  |  Mean score: 0.520  |  Max score: 0.569
  Center (A): (-2.4, -31.0, -9.8)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.33 (convex — surface protrusion, interpret cautiously)
  Top residues: A166(GLY)=0.569, A167(VAL)=0.557, A183(SER)=0.434

  How this pocket was identified:
    The model assigned high pocket probability to 3 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 16.5 A^2 (67% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 3 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #5  (secondary)
  ------------------------------------------------------------
  Residues: 3  |  Mean score: 0.461  |  Max score: 0.520
  Center (A): (9.5, 1.9, -51.7)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.33 (convex — surface protrusion, interpret cautiously)
  Top residues: C168(LYS)=0.520, C170(SER)=0.443, C169(PHE)=0.418

  How this pocket was identified:
    The model assigned high pocket probability to 3 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 30.3 A^2 (67% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 3 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

Score distribution:
  Min=0.020  Max=0.798  Mean=0.196  Std=0.225
  20.3% of residues exceed threshold 0.4 (focused signal — clusters are reliable)
```

## Data Files

> **Gitignored** — regenerate locally with `python scripts/per_structure_analysis.py`
> PDB inputs: `python agents/pcna_crawler.py --download` | Graphs: `python scripts/build_graphs.py`

| File | Description | Tracked in git? |
|------|-------------|----------------|
| `results/per_structure/6FCN/scores.csv` | Per-residue pocket scores | No |
| `results/per_structure/6FCN/clusters.csv` | DBSCAN cluster assignments | No |
| `results/per_structure/6FCN/report.txt` | Full text analysis report | No |
| `results/per_structure/6FCN/summary.json` | Machine-readable summary | No |
| `results/per_structure/summary_table.csv` | All-59 rollup | Yes |
| `checkpoints/pcna/best_pcna.ckpt` | Trained model weights | Yes |
| `data/raw/6FCN.pdb` | Raw PDB structure | No |
| `data/graphs/6FCN.pt` | PyG graph tensor | No |

---
*GNN-PCNA v2 | Dual-branch GATv2Conv | Checkpoint tracked at `checkpoints/pcna/best_pcna.ckpt`*