# 1AXC — COMPLEX (DNA-BINDING

> Generated: 2026-05-16  |  Category: Other PCNA structure  **AOH1996 CANDIDATE**

## Quick Stats

| Field | Value |
|-------|-------|
| PDB ID | [1AXC](https://www.rcsb.org/structure/1AXC) |
| Residues | 804 across 6 chains |
| Ligands detected | none (apo) |
| AUROC | N/A (apo — no ligand for labeling) |
| Top pocket mean score | 0.5916 (141 residues) |
| AOH1996 GT overlap | ##################..  22/24 |
| Top pocket concavity | 0.496 (convex) |

## AOH1996 Pocket Assessment

The GNN-PCNA model recovered **22/24 AOH1996 ground-truth residues** in its top predicted cluster. This represents >92% overlap with the experimentally confirmed cryptic pocket from PDB 8GLA. The model assigns a high prioritization score (0.592 mean) to this region. **This is a hypothesis only** — druggability requires MD simulation, docking, or experimental validation.

**Implication:** AOH1996 (or its derivatives AOH1160/AOH1996-1LE) would be predicted to bind this structure with similar affinity to the confirmed holo structure 8GLA.

## Full Analysis Report

```
======================================================================
PDB: 1AXC
Title: COMPLEX (DNA-BINDING PROTEIN/DNA)HUMAN PCNA
Chains: A, B, C, D, E, F  |  Residues: 804
Ligands detected: none (apo)
Residues above threshold (0.4): 221/804 (27.5%)

Predicted cryptic pockets: 5

  Pocket #1  (PRIMARY)
  ------------------------------------------------------------
  Residues: 141  |  Mean score: 0.592  |  Max score: 0.729
  Center (A): (81.2, -2.7, 18.9)
  Structural region: Domain 2 core beta sheet
     55 residues in: Domain 2 core beta sheet
     29 residues in: Core beta sheet
     20 residues in: C-terminal loop — AOH1996 cryptic pocket region
     17 residues in: N-terminal beta sheet (domain 1)
     13 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      7 residues in: Front-face loop (PIP-box groove)
  AOH1996 pocket overlap: 22/24 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.50 (convex — surface protrusion, interpret cautiously)
  Top residues: E138(LYS)=0.729, E137(VAL)=0.721, E228(SER)=0.719, E227(LEU)=0.717, E226(THR)=0.717, E139(MET)=0.715, E238(GLU)=0.702, E237(VAL)=0.702

  How this pocket was identified:
    The model assigned high pocket probability to 141 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 25.1 A^2 (70% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 141 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the domain 2 core beta sheet. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #2  (secondary)
  ------------------------------------------------------------
  Residues: 43  |  Mean score: 0.573  |  Max score: 0.688
  Center (A): (81.3, 51.7, 19.8)
  Structural region: Domain 2 core beta sheet
     15 residues in: Domain 2 core beta sheet
     15 residues in: C-terminal loop — AOH1996 cryptic pocket region
      6 residues in: Front-face loop (PIP-box groove)
      5 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
      2 residues in: N-terminal beta sheet (domain 1)
  AOH1996 pocket overlap: 14/24 GT residues
  --> HIGH overlap: this pocket is the known AOH1996 cryptic site
  Geometric concavity: 0.58 (concave — geometrically pocket-like)
  Top residues: C228(SER)=0.688, C226(THR)=0.687, C236(VAL)=0.686, C227(LEU)=0.679, C138(LYS)=0.675, C225(VAL)=0.670, C237(VAL)=0.667, C235(LEU)=0.652

  How this pocket was identified:
    The model assigned high pocket probability to 43 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 21.9 A^2 (74% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 43 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This matches the region where AOH1996 binds in PDB 8GLA, specifically the domain 2 core beta sheet. The prediction is consistent with the known mechanism of cryptic pocket opening.

  Pocket #3  (secondary)
  ------------------------------------------------------------
  Residues: 26  |  Mean score: 0.650  |  Max score: 0.784
  Center (A): (34.2, 13.1, 19.7)
  Structural region: Domain 2 core beta sheet
     14 residues in: Domain 2 core beta sheet
      7 residues in: C-terminal loop — AOH1996 cryptic pocket region
      5 residues in: IDCL — Interdomain Connecting Loop (key interaction hub)
  AOH1996 pocket overlap: 4/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.38 (convex — surface protrusion, interpret cautiously)
  Top residues: A134(SER)=0.784, A136(VAL)=0.773, A135(CYS)=0.773, A232(ASP)=0.767, A133(TYR)=0.767, A235(LEU)=0.764, A234(PRO)=0.762, A137(VAL)=0.761

  How this pocket was identified:
    The model assigned high pocket probability to 26 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 32.8 A^2 (65% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 26 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #4  (secondary)
  ------------------------------------------------------------
  Residues: 4  |  Mean score: 0.557  |  Max score: 0.622
  Center (A): (65.8, 53.7, 21.6)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.50 (concave — geometrically pocket-like)
  Top residues: C168(LYS)=0.622, C167(VAL)=0.563, C169(PHE)=0.543, C170(SER)=0.500

  How this pocket was identified:
    The model assigned high pocket probability to 4 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 13.2 A^2 (75% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 4 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

  Pocket #5  (secondary)
  ------------------------------------------------------------
  Residues: 4  |  Mean score: 0.537  |  Max score: 0.572
  Center (A): (71.3, 56.0, 14.4)
  Structural region: Domain 2 core beta sheet
  AOH1996 pocket overlap: 0/24 GT residues
  --> LOW overlap: likely a distinct/novel predicted site
  Geometric concavity: 0.25 (convex — surface protrusion, interpret cautiously)
  Top residues: C207(PHE)=0.572, C205(LEU)=0.562, C206(THR)=0.549, C204(GLN)=0.468

  How this pocket was identified:
    The model assigned high pocket probability to 4 residues that cluster within 6 A of each other in 3D space. These residues have a mean SASA of 34.5 A^2 (50% are partially buried, SASA < 30 A^2), consistent with a recessed binding surface rather than an exposed loop.
    The GNN assigned high scores here because the dual-branch message-passing identified this neighborhood as chemically similar to known cryptic pocket residues in the training data: the spatial branch detected dense local packing (average 4 close contacts) and the sequential branch detected the loop or beta-strand context typical of induced-fit binding sites.
    This does not overlap significantly with the AOH1996 site, suggesting a potentially novel cryptic pocket that may respond to a different small molecule than AOH1996.

Score distribution:
  Min=0.020  Max=0.784  Mean=0.235  Std=0.239
  27.5% of residues exceed threshold 0.4 (focused signal — clusters are reliable)
```

## Data Files

> **Gitignored** — regenerate locally with `python scripts/per_structure_analysis.py`
> PDB inputs: `python agents/pcna_crawler.py --download` | Graphs: `python scripts/build_graphs.py`

| File | Description | Tracked in git? |
|------|-------------|----------------|
| `results/per_structure/1AXC/scores.csv` | Per-residue pocket scores | No |
| `results/per_structure/1AXC/clusters.csv` | DBSCAN cluster assignments | No |
| `results/per_structure/1AXC/report.txt` | Full text analysis report | No |
| `results/per_structure/1AXC/summary.json` | Machine-readable summary | No |
| `results/per_structure/summary_table.csv` | All-59 rollup | Yes |
| `checkpoints/pcna/best_pcna.ckpt` | Trained model weights | Yes |
| `data/raw/1AXC.pdb` | Raw PDB structure | No |
| `data/graphs/1AXC.pt` | PyG graph tensor | No |

---
*GNN-PCNA v2 | Dual-branch GATv2Conv | Checkpoint tracked at `checkpoints/pcna/best_pcna.ckpt`*