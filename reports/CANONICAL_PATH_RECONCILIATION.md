# Canonical Path Reconciliation

| Documented path | Exists | Current? | Action |
|---|---:|---:|---|
| `data/raw_intake/pcna_structures/` | YES | YES | Keep active |
| `scripts/acquire_phase2_governed.py` | YES | YES | Keep active |
| `scripts/download_data.py` | NO | NO | Reclassify as historical/missing; not active for current clone |
| `data/raw/*.pdb` | PARTIAL | GENERATED | Existing local subset only; rebuild instructions required for full set |
| `src/data_processing/parse_pdb.py` | YES | YES | Keep active |
| `src/data_processing/graph_construction.py` | YES | YES | Keep active |
| `scripts/build_esm_features.py` | YES | YES | Keep active |
| `data/esm_features/*.npy` | PARTIAL | GENERATED | External/generated; not complete committed provenance |
| `scripts/build_graphs.py` | YES | YES | Keep active |
| `scripts/build_graphs_xl.py` | YES | YES | Keep active |
| `data/graphs_xl/*.pt` | PARTIAL | GENERATED/IGNORED | External/generated; graph manifest missing |
| `scripts/make_homology_split.py` | YES | YES | Keep active |
| `scripts/validate_split_integrity.py` | YES | YES | Keep active |
| `data/splits/cryptosite_homology30_split.json` | YES | YES | Recovered from Git history |
| `scripts/finetune_v3_fixed.py` | YES | YES | Keep active |
| `src/models/cryptic_gnn.py` | YES | YES | Keep active |
| `scripts/evaluate_clean_split.py` | YES | YES | Keep active |
| `scripts/independent_extraction_gate.py` | YES | YES | Keep active |
| `artifacts/pre_md_independent_extraction_20260815/frozen_extraction_method.json` | YES | YES | Track active |
| `artifacts/pre_md_independent_extraction_20260815/final_consensus_pocket_handoff.json` | YES | YES | Track active |
| `scripts/run_v3_inference.py` | YES | YES | Keep active |
| `md_validation_4070/gnn_pocket_search/export_handoff.py` | YES | YES | Keep active |
| `md_validation_4070/gnn_pocket_search/handoff_to_pocket.py` | YES | YES | Keep active |
| `md_validation_4070/pockets/final_consensus_1w60_20260815.json` | YES | YES | Keep active |
| `md.sh` | YES | YES | Recovered local workflow; canonical launcher |
| `md_validation_4070/run_md.py` | YES | YES | Keep active |
| `md_validation_4070/analyze_md.py` | YES | YES | Keep active |
| `md_validation_4070/FROZEN_MD_ANALYSIS_PROTOCOL.json` | YES | YES | Recovered local file; reconciled after control-gate repair; current SHA differs from old claimed hash |

Active paths checked: 28.
Broken active paths fixed or reclassified: 2.
Historical/superseded paths reclassified: `scripts/download_data.py`, old direct `run_in_tmux.sh` production path, archived 25-dim Phase-3 lineage.
