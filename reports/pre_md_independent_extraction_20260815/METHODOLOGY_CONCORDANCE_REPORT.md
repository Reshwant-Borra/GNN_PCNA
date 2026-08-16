# Methodology Concordance Report

Date: 2026-08-15

## Original methodology reconstruction

| Component | Original methodology | Current implementation | Evidence | Status |
| --- | --- | --- | --- | --- |
| Scientific objective | Prioritize candidate PCNA pocket-associated residues for hypothesis-generating MD follow-up. | Same; README and research base explicitly reject binding/druggability proof language. | `README.md`, `docs/research_base/project/CLAIMS_AND_EVIDENCE.md` | MATCH |
| Dataset construction | Use governed source acquisition, PCNA structures, and cryptic-pocket/proxy datasets with provenance. | Source downloads in `data/raw_intake/`, generated graph/ESM artifacts under `data/*`, registries updated. | `reports/phase2/*`, `data/results/split_integrity_520.json` | MATCH |
| Labeling | Proxy residue labels from ligand/proximity/cryptic-pocket sources; PCNA AOH contacts treated as positive-control region. | Same; claims limit proxy-label interpretation. | `scripts/finetune_v3_fixed.py`, `docs/research_base/datasets/LABEL_DEFINITION.md` | MATCH |
| Structural preprocessing | Parse structures to residue/CA coordinates and build graph features. | Root `src/data_processing`, `scripts/build_graphs*.py`. | `docs/CANONICAL_PIPELINE.md` | MATCH |
| Graph construction | Residue graph with spatial and sequential connectivity. | Root graph/model code implements spatial/sequential branches. | `src/data_processing/graph_construction.py`, `src/models/cryptic_gnn.py` | MATCH |
| ESM embeddings | Use sequence/evolutionary embeddings as node features where available. | `data/esm_features/*.npy`, `scripts/build_esm_features.py`; alignment remains a tracked assumption. | `docs/research_base/assumptions/ASSUMPTION_REGISTRY.md` | MATCH |
| Split methodology | Homology-clean validation/test split; avoid leakage. | `data/results/homology30_audit.json` reports PASS for current calibration set. | `data/results/homology30_audit.json` | MATCH |
| Fine-tuning | PCNA fine-tuning/checkpoint selection uses 8GLA roles; final independent extraction must not reuse 8GLA. | Frozen extraction policy excludes 8GLA and 1W60. | `artifacts/pre_md_independent_extraction_20260815/frozen_extraction_method.json` | INTENTIONAL_REFINEMENT |
| Checkpoint selection | Seed-specific checkpoints selected before final target evaluation. | Seeds 42/43/44 frozen with metadata and hashes under `artifacts/go_prep/seed_*`. | `artifacts/go_prep/seed_*/best_meta.json` | MATCH |
| Extraction method | Earlier methods included absolute thresholds and DBSCAN clustering; final method needed unbiased freeze. | Non-PCNA benchmark selected rank-fraction + DBSCAN + size-weighted cluster ranking. | `INDEPENDENT_EXTRACTION_SELECTION_REPORT.md` | INTENTIONAL_REFINEMENT |
| Final target | 1W60/PCNA must not tune extraction parameters. | `select-policy` did not read 1W60; `apply-1w60` consumed frozen policy only. | `scripts/independent_extraction_gate.py`, frozen policy | MATCH |
| Stability gate | Require multi-seed stability before MD. | PASS: literal mean Jaccard 0.6792, 16 consensus residues. | `FINAL_1W60_THREE_SEED_STABILITY_REPORT.md` | MATCH |
| MD follow-up | Control-first, no production MD before governed approval. | No MD launched; Gate-6 approval remains required. | `PROJECT_STATE.md`, final JSON | MATCH |
| Interpretation limits | MD and GNN do not prove binding/druggability. | Explicit in README, reports, research base, final JSON. | `README.md`, `VALIDATION_STATUS.md` | MATCH |

## Legitimate refinements

- Excluded 8GLA from final extraction-method selection because it was already used in fine-tuning/checkpoint-selection roles.
- Replaced absolute-score threshold selection with a scale-invariant rank-fraction method selected on non-PCNA structures.
- Added size-weighted cluster ranking because independent non-PCNA metrics favored it; this was frozen before final 1W60 application.

## Unresolved ambiguities

- The non-PCNA calibration set is small. It is eligible by current provenance, but future contamination or label-mapping evidence would invalidate the policy.
- Some operational ResearchOS artifact timestamps remain empty due immutable registry append behavior; updated hashes and commands are recorded in notes.
