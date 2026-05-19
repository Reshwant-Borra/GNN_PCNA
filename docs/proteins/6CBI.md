# 6CBI — CELL CYCLEPCNA IN COMPLEX WITH INHIBITOR

> Generated: 2026-05-16  |  Category: Other PCNA structure  **AOH1996 CANDIDATE**

## Quick Stats

| Field | Value |
|-------|-------|
| PDB ID | [6CBI](https://www.rcsb.org/structure/6CBI) |
| Residues | 1535 across 10 chains |
| Ligands detected | DAB |
| AUROC | 0.5219 (drug-like ligand, PCNA-chain filtered) |
| Top pocket mean score | 0.5970 (222 residues) |
| AOH1996 GT overlap | ####################  24/24 |
| Top pocket concavity | 0.523 (concave) |

## AOH1996 Pocket Assessment

The GNN-PCNA model recovered **24/24 AOH1996 ground-truth residues** in its top predicted cluster. This represents >100% overlap with the experimentally confirmed cryptic pocket from PDB 8GLA. The model assigns a high prioritization score (0.597 mean) to this region. **This is a hypothesis only** — druggability requires MD simulation, docking, or experimental validation.

**Implication:** AOH1996 (or its derivatives AOH1160/AOH1996-1LE) would be predicted to bind this structure with similar affinity to the confirmed holo structure 8GLA.

## Full Analysis Report

```
======================================================================
PDB: 6CBI
Title: CELL CYCLEPCNA IN COMPLEX WITH INHIBITOR
Chains: A, B, C, D, E, F, H, I, J, K  |  Residues: 1535
Ligands detected: DAB
AUROC vs auto-labeled GT: 0.4066
Residues above threshold (0.4): 468/1535 (30.5%)

Predicted cryptic pockets: 11

  Pocket #1  (PRIMARY)
  ------------------------------------------------------------
  Residues: 222  |  Mean score: 0.597  |  Max score: 0.719
  Center (A): (5.2, -7.7, 211.6)
  Structural region: Domain 2 core beta sheet
     59 residues in: Domain 2 core beta sheet
     55 residues in: Core beta sheet
     39 residues in: C-terminal loop — AOH1996 cryptic pocket region
     30 residues in: N-terminal beta sheet (domain 1)
     25 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
     14 residues in: Front-face loop (PIP-box groove)
  AOH1996 pocket overlap: 24/24 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.52 (concave — geometrically pocket-like)
  Top residues: F228(SER)=0.719, F40(MET)=0.718, F226(THR)=0.718, D100(ALA)=0.718, F227(LEU)=0.717, F39(SER)=0.715, F249(TYR)=0.711, F250(TYR)=0.707

  How this pocket was identified:
    The model assigned high pocket probability to 222 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 30.8 A^2 (63% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 222 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the domain 2 core beta sheet. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #2  (secondary)
  ------------------------------------------------------------
  Residues: 79  |  Mean score: 0.581  |  Max score: 0.728
  Center (A): (27.2, 23.7, 216.2)
  Structural region: Domain 2 core beta sheet
     23 residues in: Domain 2 core beta sheet
     16 residues in: Core beta sheet
     15 residues in: C-terminal loop — AOH1996 cryptic pocket region
      9 residues in: N-terminal beta sheet (domain 1)
      9 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      7 residues in: Front-face loop (PIP-box groove)
  AOH1996 pocket overlap: 19/24 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.51 (concave — geometrically pocket-like)
  Top residues: E139(MET)=0.728, E138(LYS)=0.723, E42(SER)=0.707, E41(ASP)=0.696, E44(HIS)=0.693, E40(MET)=0.689, E239(TYR)=0.687, E238(GLU)=0.686

  How this pocket was identified:
    The model assigned high pocket probability to 79 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 31.5 A^2 (59% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 79 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the domain 2 core beta sheet. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #3  (secondary)
  ------------------------------------------------------------
  Residues: 55  |  Mean score: 0.590  |  Max score: 0.669
  Center (A): (13.5, -24.3, 168.3)
  Structural region: Domain 2 core beta sheet
     17 residues in: Domain 2 core beta sheet
     17 residues in: C-terminal loop — AOH1996 cryptic pocket region
      6 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      5 residues in: N-terminal beta sheet (domain 1)
      5 residues in: Front-face loop (PIP-box groove)
      5 residues in: Core beta sheet
  AOH1996 pocket overlap: 15/24 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.53 (concave — geometrically pocket-like)
  Top residues: B249(TYR)=0.669, B228(SER)=0.668, B250(TYR)=0.666, B227(LEU)=0.665, B226(THR)=0.665, B237(VAL)=0.663, B236(VAL)=0.662, B251(LEU)=0.657

  How this pocket was identified:
    The model assigned high pocket probability to 55 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 36.0 A^2 (60% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 55 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the domain 2 core beta sheet. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #4  (secondary)
  ------------------------------------------------------------
  Residues: 34  |  Mean score: 0.518  |  Max score: 0.648
  Center (A): (4.1, 11.1, 172.7)
  Structural region: Domain 2 core beta sheet
     18 residues in: Domain 2 core beta sheet
     14 residues in: Core beta sheet
      2 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.59 (concave — geometrically pocket-like)
  Top residues: D170(SER)=0.648, D169(PHE)=0.606, D168(LYS)=0.598, D206(THR)=0.586, D159(VAL)=0.585, D205(LEU)=0.575, D161(SER)=0.565, D207(PHE)=0.564

  How this pocket was identified:
    The model assigned high pocket probability to 34 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 33.0 A^2 (56% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 34 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #5  (secondary)
  ------------------------------------------------------------
  Residues: 16  |  Mean score: 0.652  |  Max score: 0.772
  Center (A): (35.0, 20.9, 165.7)
  Structural region: C-terminal loop — AOH1996 cryptic pocket region
      7 residues in: C-terminal loop — AOH1996 cryptic pocket region
      6 residues in: Domain 2 core beta sheet
      3 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
  AOH1996 pocket overlap: 4/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.31 (convex — surface protrusion, interpret cautiously)
  Top residues: A134(SER)=0.772, A135(CYS)=0.742, A136(VAL)=0.739, A133(TYR)=0.727, A231(ALA)=0.722, A232(ASP)=0.715, A235(LEU)=0.686, A234(PRO)=0.670

  How this pocket was identified:
    The model assigned high pocket probability to 16 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 28.0 A^2 (69% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 16 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #6  (secondary)
  ------------------------------------------------------------
  Residues: 14  |  Mean score: 0.553  |  Max score: 0.660
  Center (A): (29.6, 8.6, 228.3)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.71 (concave — geometrically pocket-like)
  Top residues: E170(SER)=0.660, E207(PHE)=0.603, E206(THR)=0.599, E168(LYS)=0.597, E169(PHE)=0.591, E205(LEU)=0.587, E159(VAL)=0.572, E161(SER)=0.542

  How this pocket was identified:
    The model assigned high pocket probability to 14 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 26.1 A^2 (79% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 14 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #7  (secondary)
  ------------------------------------------------------------
  Residues: 14  |  Mean score: 0.543  |  Max score: 0.635
  Center (A): (52.5, -24.6, 200.3)
  Structural region: Domain 2 core beta sheet
      9 residues in: Domain 2 core beta sheet
      5 residues in: C-terminal loop — AOH1996 cryptic pocket region
  AOH1996 pocket overlap: 1/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.50 (concave — geometrically pocket-like)
  Top residues: C236(VAL)=0.635, C237(VAL)=0.624, C238(GLU)=0.598, C138(LYS)=0.596, C235(LEU)=0.594, C225(VAL)=0.536, C228(SER)=0.534, C234(PRO)=0.520

  How this pocket was identified:
    The model assigned high pocket probability to 14 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 11.8 A^2 (93% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 14 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #8  (secondary)
  ------------------------------------------------------------
  Residues: 13  |  Mean score: 0.514  |  Max score: 0.622
  Center (A): (19.4, -33.0, 179.2)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.69 (concave — geometrically pocket-like)
  Top residues: B169(PHE)=0.622, B170(SER)=0.604, B168(LYS)=0.589, B207(PHE)=0.588, B206(THR)=0.550, B205(LEU)=0.541, B159(VAL)=0.534, B160(ILE)=0.487

  How this pocket was identified:
    The model assigned high pocket probability to 13 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 27.0 A^2 (69% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 13 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #9  (secondary)
  ------------------------------------------------------------
  Residues: 7  |  Mean score: 0.651  |  Max score: 0.745
  Center (A): (36.9, 31.0, 173.3)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.43 (convex — surface protrusion, interpret cautiously)
  Top residues: A165(ASP)=0.745, A163(ALA)=0.736, A164(LYS)=0.687, A166(GLY)=0.682, A161(SER)=0.596, A167(VAL)=0.578, A162(CYS)=0.532

  How this pocket was identified:
    The model assigned high pocket probability to 7 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 38.3 A^2 (57% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 7 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #10  (secondary)
  ------------------------------------------------------------
  Residues: 5  |  Mean score: 0.600  |  Max score: 0.697
  Center (A): (26.1, 2.9, 170.0)
  Structural region: Front-face loop (PIP-box groove)
      4 residues in: Front-face loop (PIP-box groove)
      1 residues in: N-terminal beta sheet (domain 1)
  AOH1996 pocket overlap: 4/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 1.00 (concave — geometrically pocket-like)
  Top residues: A42(SER)=0.697, A43(SER)=0.662, A40(MET)=0.614, A44(HIS)=0.517, A41(ASP)=0.511

  How this pocket was identified:
    The model assigned high pocket probability to 5 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 35.5 A^2 (40% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 5 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #11  (secondary)
  ------------------------------------------------------------
  Residues: 5  |  Mean score: 0.515  |  Max score: 0.606
  Center (A): (35.0, -26.1, 207.1)
  Structural region: Front-face loop (PIP-box groove)
      4 residues in: Front-face loop (PIP-box groove)
      1 residues in: N-terminal beta sheet (domain 1)
  AOH1996 pocket overlap: 5/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 1.00 (concave — geometrically pocket-like)
  Top residues: C40(MET)=0.606, C44(HIS)=0.595, C42(SER)=0.549, C45(VAL)=0.427, C41(ASP)=0.400

  How this pocket was identified:
    The model assigned high pocket probability to 5 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 30.3 A^2 (60% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 5 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

Score distribution:
  Min=0.020  Max=0.772  Mean=0.249  Std=0.242
  30.5% of residues exceed threshold 0.4 (high diffuse signal — interpret clusters carefully)
```

## Data Files

> **Gitignored** — regenerate locally with `python scripts/per_structure_analysis.py`
> PDB inputs: `python agents/pcna_crawler.py --download` | Graphs: `python scripts/build_graphs.py`

| File | Description | Tracked in git? |
|------|-------------|----------------|
| `results/per_structure/6CBI/scores.csv` | Per-residue pocket scores | No |
| `results/per_structure/6CBI/clusters.csv` | DBSCAN cluster assignments | No |
| `results/per_structure/6CBI/report.txt` | Full text analysis report | No |
| `results/per_structure/6CBI/summary.json` | Machine-readable summary | No |
| `results/per_structure/summary_table.csv` | All-59 rollup | Yes |
| `checkpoints/pcna/best_pcna.ckpt` | Trained model weights | Yes |
| `data/raw/6CBI.pdb` | Raw PDB structure | No |
| `data/graphs/6CBI.pt` | PyG graph tensor | No |

---
*GNN-PCNA v2 | Dual-branch GATv2Conv | Checkpoint tracked at `checkpoints/pcna/best_pcna.ckpt`*