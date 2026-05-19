# System Overview

## Goal
Identify **cryptic binding pockets** on PCNA (Proliferating Cell Nuclear Antigen) using a GNN-based detection pipeline. ANM flexibility analysis completed (apo/holo comparison: fold-change delta +0.247). Full MD trajectory not yet generated.

## Why PCNA
- Homotrimeric sliding clamp, essential for DNA replication and repair
- Overexpressed in cancer; current drug AOH1996 targets a known site (PDB: 8GLA)
- Cryptic pockets — transiently accessible only under protein dynamics — may reveal new druggable sites
- Trimer symmetry allows 3× data augmentation per structure

## Biological Constraint
- Ground truth pocket: AOH1996 binding site on PDB **8GLA**
- Apo structure for baseline: PDB **1W60** (no visible pocket at that site)
- Any model must **recover 8GLA pocket** as a positive signal before being trusted on novel predictions

## System Pipeline (High Level)
```
PDB Structure(s)
  → Graph Construction (residues as nodes, edges by distance/contact)
  → GNN Encoder (learns pocket-relevant node/edge embeddings)
  → Pocket Scoring Head (per-residue cryptic prioritization score)
  → ANM Flexibility Analysis (DONE — apo fold-change 0.857, holo 1.104, delta +0.247)
  → MD Validation (FUTURE — full trajectory not yet generated)
  → Ranked Output (novel cryptic sites + confidence)
```

## Stack
- Language: Python 3.10+
- GNN: PyTorch Geometric (PyG)
- MD parsing: MDAnalysis
- Structure handling: BioPython / ProDy
- Visualization: py3Dmol (3D), matplotlib / seaborn (plots)

---

## Related

[[INDEX]] · [[RESEARCH_QUESTION]] · [[BIOLOGY_PCNA]] · [[PIPELINE]] · [[MODELS]] · [[DATASETS]] · [[VALIDATION]]
