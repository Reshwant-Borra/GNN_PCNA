---
type: knowledge-graph-root
generated: 2026-05-15
total_nodes: 160
tags: [hub, pcna, knowledge-graph, mcp-ready]
---

# GNN-PCNA Knowledge Graph

> Root node for the PCNA cryptic pocket prediction knowledge base.
> All data is crawled, validated, and linked. MCP-connectable.

**Generated**: 2026-05-15  
**Total nodes**: 160  
**Structures**: 103 PDB entries  
**Papers**: 19 literature nodes  
**Datasets**: 38 dataset nodes  
**Compounds**: 0 compound nodes  

---

## Hub Index

| Hub | Nodes | Description |
|---|---|---|
| [[_HUB_STRUCTURES]] | 103 | PDB crystal structures + metadata |
| [[_HUB_PAPERS]] | 19 | Literature: PubMed, bioRxiv papers |
| [[_HUB_DATASETS]] | 38 | Training datasets (Zenodo, GitHub) |
| [[_HUB_COMPOUNDS]] | 0 | Inhibitors, bioactivity (ChEMBL, PubChem) |

---

## Ground Truth Structures

| Structure | Role | Resolution |
|---|---|---|
| [[8GLA]] | **Holo — positive label** | 3.77 Å |
| [[1W60]] | Apo — negative label | 3.15 Å |
| [[4RJF]] | High-res apo (best features) | 2.0 Å |
| [[1U7B]] | Highest resolution | 1.88 Å |
| [[1AXC]] | PIP-box complex | 2.6 Å |
| [[1W61]] | RFC complex | 2.1 Å |
| [[9N3L]] | Novel inhibitor — investigate | 1.9 Å |

---

## Pipeline Links

| Stage | File | Status |
|---|---|---|
| Data acquisition | [[fetch_structures]] | Done |
| PDB parsing | [[parse_pdb]] | Stub |
| Graph construction | [[graph_construction]] | Stub |
| Model | [[MODELS]] (CrypticGNN) | Implemented |
| Training | [[train]] | Stub |
| Validation | [[VALIDATION]] | Design |

---

## MCP Integration

This vault is MCP-connectable. To wire a knowledge-graph MCP to the ML model:

```
Obsidian vault root: C:/Users/advay/GNN_PNCA/
KNOWLEDGE_GRAPH.md:  docs/vault/KNOWLEDGE_GRAPH.md
Catalog JSON:        data/catalog/pcna_data_catalog.json
Raw catalog:         data/catalog/raw_catalog.json
```

**Query pattern**: ask the MCP for structures with `relevance >= 0.5` and `validated: true`
to get the curated training set. Use `type: paper` nodes for literature context.

---

## Biology Context

[[BIOLOGY_PCNA]] · [[RESEARCH_QUESTION]] · [[paper_notes]] · [[KNOWN_LIMITATIONS]]

## Experiments

[[EXPERIMENT_INDEX]] · [[RESEARCH_NOTES_LOG]]

## Workflow

[[PIPELINE]] · [[AGENTS]] · [[AI_WORKFLOW_RULES]] · [[SYSTEM_OVERVIEW]]
