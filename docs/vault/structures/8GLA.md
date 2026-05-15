---
type: pdb_structure
pdb_id: 8GLA
title: PCNA Structure 8GLA
resolution_angstrom: 3.77
chains: ["A", "B", "C", "D"]
organism: ""
source: uniprot
relevance: 1.0
relevance_label: high
validated: true
category: core
ca_completeness: 1.0
residue_count: 952
mean_b_factor: 88.1
tags: [pcna, pdb-structure, validated, source-uniprot, uniprot-confirmed, ground-truth]
rcsb_url: https://www.rcsb.org/structure/8GLA
download_url: "https://files.rcsb.org/download/8GLA.pdb"
---

# 8GLA — PCNA Structure 8GLA

> **Role**: `ground-truth-holo`
>
> PCNA + AOH1996 — cryptic pocket OPEN. Primary positive training example. Ground truth for pocket labeling.

## Summary

| Field | Value |
|---|---|
| PDB ID | `8GLA` |
| Resolution | 3.77 Å |
| Chains | A, B, C, D |
| Organism | unknown |
| Ca completeness | 100.0% |
| Residues | 952 |
| Validation | PASSED |
| Relevance | 1.00 (high) |

## ML Usage

- **Positive training example** — AOH1996 cryptic pocket is open
- Ground truth: residues within 6 Å of AOH1996 ligand labeled `1`
- Required for: pocket labeling, validation gate

## Connections

- **RCSB entry**: [PDB 8GLA](https://www.rcsb.org/structure/8GLA)
- **Download**: [8GLA.pdb](https://files.rcsb.org/download/8GLA.pdb)

**Related structures**: [[1W60]] · [[1AXC]] · [[1W61]]

**Pipeline**: [[PIPELINE]] · [[DATASETS]] · [[parse_pdb]] · [[graph_construction]]

**Hub**: [[_HUB_STRUCTURES]] · [[KNOWLEDGE_GRAPH]]
