---
type: analysis
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [benchmark, dataset, phase2]
aliases: [Benchmark Strategy]
confidence: medium
evidence_status: inferred
---

# Benchmark Strategy

## Strategy

Use one primary residue-level cryptic-pocket benchmark if it survives audit, and keep ligand-binding, affinity, allosteric, and simulation-opening sources in separate roles with separate label types.

## Proposed primary benchmark

CryptoBench is the leading primary benchmark candidate because its paper and repository describe apo structures, paired holo structures, ligand identifiers, apo and holo pocket residue selections, CIF files, train-test splits, and PyMOL visualization scripts. Its reported cryptic-site definition is based on apo-holo binding-site change, not generic ligand contact alone.

CryptoBench is not frozen because the workspace has only crawl metadata and source leads. The actual OSF files, schema, hashes, license name, PCNA/homolog contamination status, and split audit are still missing.

## Proposed auxiliary and reference roles

| Source | Proposed use |
|---|---|
| BioLiP/BioLiP2 | Auxiliary ligand-binding-site proxy labels or annotation context only. |
| scPDB | Auxiliary ligandable-site proxy labels or geometry/baseline reference only. |
| PDBbind | Background affinity/source context; exclude from primary residue-level cryptic benchmark. |
| ASD | Allosteric-site context/reference only unless entry-level site mappings are audited. |
| PocketMiner | Same-split baseline method and source of simulation-opening label context; not a primary benchmark without a separate label ID. |

## Split strategy candidates

1. Candidate S1: CryptoBench-derived Phase 2 split. Start from CryptoBench official split only as an input, then rebuild or verify grouping by UniProt ID, apo/holo pair, ligand variants, duplicate PDB assemblies, and sequence clusters. Use the stricter of the benchmark threshold and the Phase 2 approved threshold. No PCNA or close PCNA homolog may influence model selection.
2. Candidate S2: Strict Phase 2 de novo split. Ignore benchmark-provided train/test assignments and create a new grouped split from raw CryptoBench records after local file inventory. Group by UniProt ID, apo structure, holo structure family, ligand variants, sequence cluster, and structural-similarity flags. This is scientifically preferred if the official split does not meet governance.
3. Candidate S3: Evaluation-only benchmark. Use CryptoBench only as an external benchmark after training on a separate source. This is only viable if label compatibility and leakage from any training source are audited.

## Benchmark controls

- Positive controls: held-out CryptoBench apo-holo cryptic pockets; PCNA 8GLA/ZQZ only as a declared positive-control gate if isolated from tuning; PocketMiner test examples only if not used for model selection.
- Negative/null controls: random residue ranking, shuffled labels, residue-type prior, SASA/accessibility-only, B-factor/flexibility-only if available, local-density/geometric cavity, fpocket/P2Rank proximity scores, and CryptoBench noncryptic pockets if the file is present and audited.
- Required metrics: macro/micro AUPRC and AUROC, top-k recovery, precision/recall at frozen k, calibration, per-protein tables, seed variance, and bootstrap confidence intervals over proteins.

## Freeze status

Not ready for split + label freeze. The strategy is ready for human review as a proposed evidence packet, but no canonical benchmark foundation can be frozen until local files and audits exist.

## Provenance

- Source paths: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `09_EVALUATION_PROTOCOL.md`, `10_BASELINE_REQUIREMENTS.md`, `28_NULL_HYPOTHESIS_BASELINES.md`, `29_BENCHMARK_LIMITATIONS.md`; `crawls/pcna-dataset-repositories-pass9/`; `crawls/pcna-curated-official-tools-data-structures-pass8/`; `crawls/pcna-gap-closure-datasets-tools-structures-pass6/`
- External sources: CryptoBench paper DOI `10.1093/bioinformatics/btae745`; `https://github.com/skrhakv/CryptoBench`; `https://osf.io/pz4a9/`; BioLiP/BioLiP2 official page and NAR 2023 paper; scPDB NAR 2015 paper; ASD official page; PocketMiner Nature Communications 2023 paper
- Confidence level: medium
- Evidence status: inferred for strategy, uncertain for adoption
- Date: 2026-05-27
