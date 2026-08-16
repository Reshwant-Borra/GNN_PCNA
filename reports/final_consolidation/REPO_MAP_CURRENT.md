# Repository Map Current

## Summary

- Active GNN implementation: root `src/` + selected root `scripts/` consolidated from `origin/graph-leakage-fix`.
- Active MD implementation: `md_validation_4070/` from current `main`.
- Historical nested worktree: moved from `Desktop/GNN_PCNA/` to `archive/historical_desktop_gnn_pcna_202605_phase2_phase4/`.
- Active interface-map provenance migrated to `data/registries/` and `scripts/`.
- Full per-file classification: `FILE_CLASSIFICATION.csv`.

## Directory classification

| Path | Classification | Purpose |
|---|---|---|
| `src/` | CANONICAL | GNN package |
| `scripts/` | CANONICAL | GNN/data commands and source acquisition utilities |
| `md_validation_4070/` | CANONICAL | MD prep/run/analyze and GNN handoff |
| `data/raw_intake/` | KEEP_PROVENANCE | official source downloads |
| `data/registries/` | KEEP_REFERENCE | active registries/interface maps |
| `docs/research_base/` | CANONICAL | scientific knowledge base |
| `reports/final_consolidation/` | KEEP_PROVENANCE | this audit |
| `archive/historical_desktop_gnn_pcna_202605_phase2_phase4/` | ARCHIVE | historical nested project tree |
| `research_os*` | KEEP_REFERENCE | governance framework; not production GNN/MD path |
| `results/`, `data/results/` | GENERATED_REBUILDABLE | imported small summaries only; regenerate for final release |
| `node_modules/`, `package*.json` | DELETE_CANDIDATE | untracked unrelated JS dependency tree/package files |
