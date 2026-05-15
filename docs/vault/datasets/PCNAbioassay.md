---
type: dataset
uid: "PCNA:bioassay"
title: PCNA bioactivity data (PubChem)
source: pubchem
url: "https://pubchem.ncbi.nlm.nih.gov/protein/P12004/bioactivities"
download_url: ""
relevance: 0.0
relevance_label: minimal
validated: false
tags: [pcna, dataset, source-pubchem]
---

# PCNA bioactivity data (PubChem)

## Description

All bioassay records for human PCNA from PubChem

## Source

| Field | Value |
|---|---|
| Source | pubchem |
| URL | [PCNA:bioassay](https://pubchem.ncbi.nlm.nih.gov/protein/P12004/bioactivities) |

## Metadata

- **uniprot**: P12004

## Usage in Pipeline

_Annotate: how does this dataset fit into the GNN-PCNA pipeline?_

- [ ] Pre-training (CryptoSite-style)
- [ ] Fine-tuning
- [ ] Evaluation / benchmark
- [ ] Negative controls

## Connections

**Hub**: [[_HUB_DATASETS]] · [[KNOWLEDGE_GRAPH]]

**Pipeline**: [[PIPELINE]] · [[DATASETS]] · [[fetch_structures]]
