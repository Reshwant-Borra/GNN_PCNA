# Phase 2 Implementation Plan

## Purpose

Provide a handoff plan for a new chat or implementation agent. This plan does not authorize training. It describes the exact order to implement governance-first Phase 2.

## Hard Rules

- Build a fresh Phase 2 pipeline.
- Use V1 only as historical reference.
- Use `crawls/` as a source/context pack, not a ready dataset.
- Stop the first milestone at governed data: registries, splits, labels, graph audits, biological sanity, benchmark limitations, red-team pretraining review, and readiness gates.
- Do not train until human review gates and readiness gates pass.

## Implementation Phases

1. Source and scope freeze.
2. Assumption and uncertainty registry.
3. Source registry from `crawls/`.
4. Benchmark limitations review for CryptoBench and auxiliary datasets.
5. Dataset registry and data lifecycle registry.
6. Split protocol and human split freeze.
7. Label protocol and human label freeze.
8. Biological data sanity review before graph generation/training.
9. Graph generation manifest and graph audit.
10. Red-team audit and null-baseline plan.
11. Readiness gate: stop at governed data.
12. Only later: baselines, training, PCNA prediction, interpretability, MD, claims, publication readiness.

## Context Already Available

- `docs/scientific_governance/` contains Phase 2 governance.
- `BORRA_#1_SARC.pdf` states the project intent.
- `crawls/pcna-cryptic-pocket-gat-md-kb-final/` contains PCNA, AOH1996/8GLA, PIP-box/APIM, MD, GNN, and source-index context.
- `crawls/pcna-dataset-repositories-pass9/` identifies CryptoBench OSF and other dataset leads.
- `crawls/pcna-curated-official-tools-data-structures-pass8/` identifies curated source leads: BioLiP, scPDB, ASD, PocketMiner, fpocket, GROMACS, CHARMM36m, PyG, MDAnalysis, OpenMM.
- GitHub `main` branch contains ResearchOS-style gating infrastructure.
- GitHub `project-version-1` branch contains the older GNN-PCNA implementation and known caveats.

## Context Still Needed Before Building Scientific Data

- Actual Phase 2 repository branch decision and local checkout of the source implementation.
- Download/access method for CryptoBench files, including license and file inventory.
- Exact CryptoBench label schema and whether labels are residue-level, pocket-level, apo/holo-paired, or structure-level.
- Whether BioLiP/BioLiP2/scPDB/PDBbind will be downloaded locally or only used as source leads.
- Sequence clustering tool choice and threshold.
- Structural similarity review method.
- PCNA structure list for final holdout and positive controls.
- Human reviewer identity or role for mandatory review gates.
- Whether ESM/pLM features are part of MVP graph generation or deferred until after governed data.

## Forbidden Actions

- Starting with model code.
- Downloading and training on a benchmark before `BENCHMARK_LIMITATIONS.md` is completed.
- Treating crawled metadata as downloaded dataset content.
- Treating V1 graphs or checkpoints as Phase 2 artifacts.
- Skipping human review because scripts pass.

## Required Checks

- Governance file index complete.
- Source registry maps every source used by code.
- Dataset registry maps every dataset item.
- Lifecycle registry records accepted/excluded/quarantined status.
- Human gates recorded.
- Readiness gate blocks until all required artifacts exist.

## Examples Of Failure

- New chat starts by porting V1 training scripts.
- CryptoBench is assumed valid without inspecting labels.
- PCNA prediction is run before baseline and biological sanity checks.

## Prevention

Tell every new agent: "Implement only documented science. If a scientific assumption is missing, stop and document the assumption instead of inventing it."

## Compliance Artifact

This plan plus `reports/phase2/readiness_gate.md` and the required review reports.

## If The Rule Fails

Pause implementation and return to the first missing governance artifact.
