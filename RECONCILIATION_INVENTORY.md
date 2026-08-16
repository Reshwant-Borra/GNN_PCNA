# Reconciliation Inventory

Created during repository repair from branch `final-consolidation-audit`, starting HEAD
`a3103ec5aaab667790e685615f064a3065d11f3d`.

## Starting State

- Branch: `final-consolidation-audit`
- HEAD: `a3103ec5aaab667790e685615f064a3065d11f3d`
- Working tree: dirty before repair.
- Staged/local consolidation already present before this repair: many historical `Desktop/GNN_PCNA/...` files were staged as moves into `archive/historical_desktop_gnn_pcna_202605_phase2_phase4/`.
- Modified tracked files before repair included `md_validation_4070/analyze_md.py`, `md_validation_4070/run_md.py`, `md_validation_4070/gnn_pocket_search/seed_stability.py`, `scripts/derive_pcna_interface_contacts.py`, research memory/registry files, and tests.

## Recovered Original Artifacts

| Artifact | Status | Evidence |
|---|---|---|
| `md_validation_4070/FROZEN_MD_ANALYSIS_PROTOCOL.json` | RECOVERED_ORIGINAL local-only | Present locally before repair; SHA-256 exactly matched documented `2497def9e4675538dd08051ae6e5a448a41fbd32a1d7dc59cfb528d74d64ce3c`. |
| `md.sh` | RECOVERED_LOCAL_WORKFLOW | Present locally before repair; not present on `origin/main`; depends on local `md_validation_4070/md_workflow.py`. |
| `md_validation_4070/md_workflow.py` | RECOVERED_LOCAL_WORKFLOW | Present locally before repair; not tracked. |
| `data/splits/cryptosite_homology30_split.json` | RECOVERED_ORIGINAL_FROM_GIT_HISTORY | Recovered from commit `d7cf76d674bced192b3c9d2b4f7f4fbf7ac3a228`; SHA-256 `828fd6d4e694cc6e258a2de8e63c4130876a9c7897dd14ccc2db15a3e6c1f06a`. |

## Local-Only Scientific Artifacts

| Path | Role | Git status |
|---|---|---|
| `checkpoints/pcna/best_pcna_v3.ckpt` | 520-dim pretrain checkpoint candidate | ignored local-only |
| `artifacts/go_prep/seed_42/best.ckpt` | frozen seed checkpoint candidate | ignored local-only |
| `artifacts/go_prep/seed_43/best.ckpt` | frozen seed checkpoint candidate | ignored local-only |
| `artifacts/go_prep/seed_44/best.ckpt` | frozen seed checkpoint candidate | ignored local-only |
| `data/graphs_xl/*.pt` | 520-dim graph tensors | ignored local-only |
| `data/esm_features/*.npy` | ESM feature tensors | untracked generated artifacts |
| `data/results/*.json` | split/evaluation/homology reports | untracked before repair |
| `results/per_structure/*.csv,json` | frozen PCNA score summaries | untracked before repair |

## Duplicated Old/New Implementations

- `md_validation_4070/run_in_tmux.sh`: historical launcher. It should not be used as a production entrypoint.
- `md.sh`: canonical launcher after repair.
- `archive/historical_desktop_gnn_pcna_202605_phase2_phase4/`: historical 25-dim/Phase-3 lineage; retained for audit, not canonical 520-dim lineage.
- `src/models/cryptic_gnn.py` and `scripts/run_v3_inference.py`: current 520-dim `PocketGNNXL` inference implementation.

## Missing Or Incomplete Provenance

- Exact 520-dim label manifest file: `MISSING`.
- Exact 520-dim graph manifest file: `MISSING`; only hash `69744b548e812697ba9015c6563ed526f1af2e915b1595badb1dd47fd1b4c64f` is recorded in reports.
- Explicit model config JSON: `MISSING`.
- Durable retrieval location for ignored checkpoint binaries: `MISSING`.
- Deterministic clean-clone reproduction from checkpoint to frozen score artifact: `NOT_DEMONSTRATED`.

## Candidate Authoritative Files

- GNN architecture: `src/models/cryptic_gnn.py`
- 520-dim split: `data/splits/cryptosite_homology30_split.json`
- Evaluation/training report: `data/results/clean_split_evaluation_xl_esm_full.json`
- Frozen extraction policy: `artifacts/diagnostics/seed_stability_rank_fraction_20260815/frozen_extraction_method.json`
- Frozen 1W60 handoff: `artifacts/pre_md_independent_extraction_20260815/final_consensus_pocket_handoff.json`
- MD launcher: `md.sh`
- MD implementation: `md_validation_4070/run_md.py`
- Frozen analysis protocol: `md_validation_4070/FROZEN_MD_ANALYSIS_PROTOCOL.json`
- Analysis implementation: `md_validation_4070/analyze_md.py`
