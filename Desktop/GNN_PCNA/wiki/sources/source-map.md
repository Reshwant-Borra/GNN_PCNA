---
type: source
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [sources, provenance, map]
aliases: [Source Map]
confidence: high
evidence_status: verified
---

# Source Map

This page explains how Codex should navigate source evidence for GNN-PCNA Phase 2.

## Source Layers

- `docs/scientific_governance/` is higher authority than wiki summaries, crawl summaries, reports, and V1 artifacts.
- `crawls/` contains raw/prior evidence and source leads. It is not automatically verified truth.
- `wiki/sources/crawl-map.md` maps topics to crawl paths so Codex can find evidence without randomly scanning the repo.
- `wiki/` summarizes and routes. It is not a replacement for governance docs or raw source materials.
- V1 and old artifacts are historical reference only.

## Promotion Rule

Sources must be promoted carefully before influencing implementation. A crawl hit or prior generated summary can suggest where to inspect, but Codex must check source metadata, source type, authority, and relevant governance before using it for project decisions.

## Source Classification

Each important source should eventually be classified as one of:

- primary evidence
- benchmark/dataset source
- implementation lead
- biological context
- MD validation context
- leakage warning
- reproducibility guidance
- excluded/noisy

## Registry Template

| Source ID | Topic | Path/URL | Type | Trust Level | Used For | Related Wiki Page | Related Governance Rule | Status |
|---|---|---|---|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | unreviewed |

## Current High-Level Source Locations

| Area | Path | Use | Status |
|---|---|---|---|
| Governance | `docs/scientific_governance/` | Binding project rules | verified |
| Crawl map | `wiki/sources/crawl-map.md` | Topic-to-crawl navigation | active |
| Curated tool/data leads | `crawls/pcna-curated-official-tools-data-structures-pass8/` | Official database/tool leads | raw crawl lead |
| Dataset leads | `crawls/pcna-dataset-repositories-pass9/` | CryptoBench and dataset discovery | raw crawl lead |
| PCNA/pocket context | `crawls/pcna-cryptic-pocket-gat-md-kb-final/` | PCNA, AOH1996, ATX-101, MD, GNN context | raw crawl lead |
| Gap closure | `crawls/pcna-gap-closure-datasets-tools-structures-pass6/` | baselines, datasets, methods, structures | raw crawl lead |
| BioGRID interactions | `crawls/pcna-biogrid-full-pass5/`, `crawls/pcna-biogrid-interactions-pass4/` | interaction-network context | raw crawl lead |
| General GNN context | `crawls/gnn-compbio-autonomous-kb-final/` | computational biology and GNN context | raw crawl lead |
| Local raw intake | `raw/` | governed future immutable dataset intake | currently empty except placeholders |
| Local Phase 2 data scaffolding | `data/` | registries, label template, split template | scaffold only; no adopted dataset files |

## Local Dataset Discovery Note

As of 2026-05-27, `crawls/`, `raw/`, and `data/` do not contain usable downloaded benchmark archives, coordinate files, residue-label files, or split assignments for CryptoBench, PocketMiner, BioLiP/BioLiP2, scPDB, ASD, or PDBbind. Crawl entries remain source leads pending official acquisition and verification.

## Provenance

- Source paths: `docs/scientific_governance/`, `crawls/`, `raw/`, `data/`, `wiki/sources/crawl-map.md`, `reports/phase2/local_dataset_discovery_report.md`
- Confidence: high for directory roles; low/uncertain for unreviewed crawl claims
- Date last updated: 2026-05-27
