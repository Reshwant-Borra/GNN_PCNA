# GNN-PCNA

GNN-PCNA is a residue-level graph-neural-network and MD-validation project for prioritizing candidate PCNA pocket regions.

Primary current source of truth: `PROJECT_STATUS.md`.

Practical MD runbook: `md_validation_4070/FINAL_MD_EXECUTION_INSTRUCTIONS.md`.

## What is being studied?

Human PCNA (UniProt P12004), especially AOH1996/ZQZ-adjacent PCNA interface regions and candidate pockets predicted from GNN residue scores.

## Current Scientific Question

The GNN identifies where on PCNA to investigate. MD tests whether that frozen predicted region reproducibly exhibits predefined accessibility, geometry, flexibility, correlated-motion, or cavity-like dynamics under the simulated conditions.

This is a hypothesis-generation workflow, not a binding-proof workflow.

## What the model predicts

The GNN outputs per-residue prioritization scores. Scores are clustered into candidate pocket regions. They are not calibrated binding probabilities.

## Training data

The project uses ligand/proximity and cryptic-pocket-related proxy labels with homology/split controls. AOH1996/ZQZ contacts from PDB 8GLA are a positive-control region, not independent novelty evidence.

## What MD tests

MD tests whether the selected region shows interpretable dynamics/openness under a positive-control-first protocol:

1. control: ligand-stripped 8GLA, open AOH1996/ZQZ site;
2. apo: 1W60 PCNA;
3. analysis: RMSD/RMSF/SASA/DCCM/openness with atom-parity controls.

MD does not prove ligand binding, druggability, therapeutic relevance, mechanism, or experimental existence of a cryptic pocket.

## Current status

Frozen 1W60 GNN handoff is `MODERATE / EXPLORATORY PASS` with mean literal Jaccard `0.6792`.

Structure/preparation validation is smoke-ready, the frozen analysis protocol is hashed, and infrastructure restart behavior has been validated on disposable technical runs. The 0.1 ns RTX 4070 smoke test has not yet passed in current status artifacts. Production remains blocked.

```text
PRODUCTION BLOCKED: Gate-6 human approval required.
```

## Exact next command

Run the launcher-first 0.1 ns RTX 4070 smoke test:

```bash
./md.sh smoke
```

## Canonical directories

- `src/` — GNN model/data/evaluation package
- `scripts/` — GNN/data commands
- `md_validation_4070/` — MD prep, execution, analysis, and GNN-to-MD handoff
- `data/raw_intake/` — official source downloads
- `data/registries/` — active project registries
- `docs/research_base/` — facts, assumptions, decisions, inferences, sources
- `reports/final_consolidation/` — final audit outputs
- `artifacts/pre_md_independent_extraction_20260815/` — frozen extraction policy and final 1W60 pre-MD stability artifacts
- `reports/strong_robustness_20260815/` and `artifacts/strong_robustness_20260815/` — post-pass stronger internal robustness audit outputs
- `archive/` — historical material not part of the executable path

Generated/rebuildable artifact directories include `data/raw/`, `data/esm_features/`, `data/graphs*`, `checkpoints/`, `results/`, and MD trajectory outputs unless explicitly registered as final artifacts.

## Research base

Start at `docs/research_base/INDEX.md`.
