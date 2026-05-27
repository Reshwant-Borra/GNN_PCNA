---
type: analysis
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [dataset, strategy]
aliases: [Dataset Strategy]
confidence: high
evidence_status: inferred
---

# Dataset Strategy

## Strategy

Build a registered, auditable dataset before graph generation or training. Treat `crawls/` as source leads, not a ready dataset.

Current investigation result: the workspace contains templates, registries, crawl metadata, and source leads, but no downloaded Phase 2 benchmark structure/label files are adopted. `data/` contains only registry, split, and label templates. CryptoBench is the strongest primary benchmark candidate, but the actual OSF dataset files must still be downloaded or otherwise inventoried, hashed, licensed, and audited before any freeze.

## Required before use

License, citation, download method, biological system, structure IDs, chains, label definition, split assignment, leakage risks, lifecycle status, and hashes.

## Dataset roles proposed from investigation

| Source | Proposed role | Status | Rationale |
|---|---|---|---|
| [[CryptoBench]] | primary benchmark candidate | candidate, not frozen | Remote paper/GitHub describe apo-holo cryptic binding-site records, train-test splits, CIF files, and PyMOL scripts. Local workspace has only OSF metadata/extract, not dataset files. |
| [[BioLiP]]/BioLiP2 | auxiliary proxy-label or annotation source; background | candidate/background | Provides biologically curated ligand-protein interaction annotations and binding residues, but ligand-contact annotations are not cryptic-pocket truth. |
| [[scPDB]] | auxiliary proxy-label or baseline reference | candidate/background | Binding-site residues are ligand-proximity definitions around ligandable sites; useful for controls, not primary cryptic labels. |
| [[PDBbind]] | excluded from primary benchmark; possible affinity/background source | risky/background | Affinity dataset does not define residue-level cryptic pockets and current official access/licensing require verification. |
| [[ASD]] | allosteric context/reference only unless entry-level site mapping is audited | candidate/background | Allosteric protein/modulator/site data are useful context, but allostery cannot be transferred to PCNA claims without site mapping and evidence review. |
| [[PocketMiner]] related data | baseline/method reference; possible auxiliary simulation-label source | candidate/baseline | Labels are simulation-opening proxies and must not be mixed with curated apo-holo cryptic labels without separate dataset IDs. |

## Current foundation artifacts

- Dataset registry template: `docs/scientific_governance/DATASET_REGISTRY.md`
- Source registry: `data/registries/source_registry.json`
- Lifecycle registry: `data/registries/data_lifecycle_registry.json`
- Dataset audit: `reports/phase2/dataset_audit.md`
- Benchmark limitations: `reports/phase2/benchmark_limitations.md`

No dataset is adopted yet.

## Freeze blockers

- CryptoBench OSF file inventory, file hashes, exact data license name, schema, and local paths are missing.
- PCNA/PCNA-homolog contamination in CryptoBench and auxiliary sources has not been checked.
- Homolog grouping, apo/holo grouping, duplicate structure grouping, and biological assembly grouping have not been materialized as tables.
- The approved sequence clustering tool and threshold are not frozen.
- Exact label-definition choice is still proposed, not human-approved.
- Human dataset-adoption, split-freeze, and label-freeze review records are missing.

## Governance

`04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `29_BENCHMARK_LIMITATIONS.md`, `31_DATA_LIFECYCLE_TRACKING.md`.

## Provenance

- Source paths: governance docs above; `crawls/pcna-dataset-repositories-pass9/SOURCE_INDEX.md`; `crawls/pcna-dataset-repositories-pass9/raw/osf/osf-pz4a9.json`; `crawls/pcna-dataset-repositories-pass9/extracts/0015-cryptobench.md`; `crawls/pcna-curated-official-tools-data-structures-pass8/SOURCE_INDEX.md`; `crawls/pcna-gap-closure-datasets-tools-structures-pass6/`; `docs/scientific_governance/DATASET_REGISTRY.md`; reports added under `reports/phase2/`
- External primary/official sources used: CryptoBench paper DOI `10.1093/bioinformatics/btae745`; `https://github.com/skrhakv/CryptoBench`; `https://osf.io/pz4a9/`; BioLiP/BioLiP2 official page and NAR 2023 paper; scPDB NAR 2015 paper; ASD official page; PocketMiner Nature Communications 2023 paper
- Confidence level: high for no local adopted dataset files and required process; medium for remote source summaries; low for final dataset suitability until local files are inspected
- Evidence status: verified for local inventory; inferred for proposed roles; uncertain for freeze readiness
- Date last updated: 2026-05-27
