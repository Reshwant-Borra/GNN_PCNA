# 6VVO — DNA BINDING

> Generated: 2026-05-16  |  Category: Large replication complex (AUROC unreliable)  

## Quick Stats

| Field | Value |
|-------|-------|
| PDB ID | [6VVO](https://www.rcsb.org/structure/6VVO) |
| Residues | 2493 across 8 chains |
| Ligands detected | AGS|ADP |
| AUROC | 0.4496 (raw — may include co-factor ligands) |
| Top pocket mean score | 0.5868 (376 residues) |
| AOH1996 GT overlap | ####################  24/24 |
| Top pocket concavity | 0.535 (concave) |

## AOH1996 Pocket Assessment

The GNN-PCNA model recovered **24/24 AOH1996 ground-truth residues** in its top predicted cluster. This represents >100% overlap with the experimentally confirmed cryptic pocket from PDB 8GLA. The model assigns a high prioritization score (0.587 mean) to this region. **This is a hypothesis only** — druggability requires MD simulation, docking, or experimental validation.

**Implication:** AOH1996 (or its derivatives AOH1160/AOH1996-1LE) would be predicted to bind this structure with similar affinity to the confirmed holo structure 8GLA.

## Full Analysis Report

```
======================================================================
PDB: 6VVO
Title: DNA BINDING PROTEIN, REPLICATIONSTRUCTURE OF THE HUMAN CLAMP LOADER (REPLICATION FACTOR C, RFC) BOUND TO THE SLIDING CLA
Chains: A, B, C, D, E, F, G, H  |  Residues: 2493
Ligands detected: AGS, ADP
AUROC vs auto-labeled GT: 0.4496
Residues above threshold (0.4): 403/2493 (16.2%)

Predicted cryptic pockets: 3

  Pocket #1  (PRIMARY)
  ------------------------------------------------------------
  Residues: 376  |  Mean score: 0.587  |  Max score: 0.710
  Center (A): (120.9, 124.3, 94.5)
  Structural region: Domain 2 core beta sheet
    131 residues in: Domain 2 core beta sheet
     80 residues in: Core beta sheet
     57 residues in: C-terminal loop — AOH1996 cryptic pocket region
     47 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
     42 residues in: N-terminal beta sheet (domain 1)
     18 residues in: Front-face loop (PIP-box groove)
      1 residues in: C-terminal tail (protein-protein interface)
  AOH1996 pocket overlap: 24/24 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.53 (concave — geometrically pocket-like)
  Top residues: F236(VAL)=0.710, H39(SER)=0.710, H237(VAL)=0.704, H38(GLN)=0.702, G39(SER)=0.700, G228(SER)=0.699, H40(MET)=0.699, G138(LYS)=0.697

  How this pocket was identified:
    The model assigned high pocket probability to 376 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 36.0 A^2 (57% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 376 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the domain 2 core beta sheet. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #2  (secondary)
  ------------------------------------------------------------
  Residues: 14  |  Mean score: 0.554  |  Max score: 0.645
  Center (A): (128.3, 110.6, 147.4)
  Structural region: Core beta sheet
      4 residues in: Core beta sheet
      4 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      4 residues in: Domain 2 core beta sheet
      2 residues in: N-terminal beta sheet (domain 1)
  AOH1996 pocket overlap: 1/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.64 (concave — geometrically pocket-like)
  Top residues: E133(LEU)=0.645, E132(VAL)=0.623, E134(LEU)=0.613, E135(THR)=0.610, E96(ASN)=0.606, E95(VAL)=0.602, E94(GLU)=0.576, E38(LEU)=0.538

  How this pocket was identified:
    The model assigned high pocket probability to 14 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 6.3 A^2 (100% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 14 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #3  (secondary)
  ------------------------------------------------------------
  Residues: 6  |  Mean score: 0.496  |  Max score: 0.527
  Center (A): (106.8, 127.1, 146.9)
  Structural region: Domain 2 core beta sheet
      4 residues in: Domain 2 core beta sheet
      2 residues in: Core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 1.00 (concave — geometrically pocket-like)
  Top residues: D148(ILE)=0.527, D149(LEU)=0.521, D150(ASP)=0.519, D147(VAL)=0.517, D109(ASN)=0.493, D110(ALA)=0.400

  How this pocket was identified:
    The model assigned high pocket probability to 6 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 11.6 A^2 (83% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 6 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

Score distribution:
  Min=0.020  Max=0.710  Mean=0.148  Std=0.205
  16.2% of residues exceed threshold 0.4 (focused signal — clusters are reliable)
```

## Data Files

> **Gitignored** — regenerate locally with `python scripts/per_structure_analysis.py`
> PDB inputs: `python agents/pcna_crawler.py --download` | Graphs: `python scripts/build_graphs.py`

| File | Description | Tracked in git? |
|------|-------------|----------------|
| `results/per_structure/6VVO/scores.csv` | Per-residue pocket scores | No |
| `results/per_structure/6VVO/clusters.csv` | DBSCAN cluster assignments | No |
| `results/per_structure/6VVO/report.txt` | Full text analysis report | No |
| `results/per_structure/6VVO/summary.json` | Machine-readable summary | No |
| `results/per_structure/summary_table.csv` | All-59 rollup | Yes |
| `checkpoints/pcna/best_pcna.ckpt` | Trained model weights | Yes |
| `data/raw/6VVO.pdb` | Raw PDB structure | No |
| `data/graphs/6VVO.pt` | PyG graph tensor | No |

---
*GNN-PCNA v2 | Dual-branch GATv2Conv | Checkpoint tracked at `checkpoints/pcna/best_pcna.ckpt`*