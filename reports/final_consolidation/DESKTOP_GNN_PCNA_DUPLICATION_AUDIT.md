# Desktop/GNN_PCNA Duplication Audit

## Answers

1. Introduced: May 2026, with Phase 2/3/4 commits adding files under `Desktop/GNN_PCNA/`.
2. Origin: historical working-copy/project tree used for phase work; later graph-leakage-fix moved active code to root-level paths.
3. Accidental filesystem-path commit: partly yes in the sense that `Desktop/GNN_PCNA/` encoded a local path inside the repo. It also contained deliberate phase deliverables.
4. Current main imports/reads it: before migration, `md_validation_4070/pockets/aoh1996.json` referenced two paths inside it. After migration, no active canonical reference should require `Desktop/GNN_PCNA/`.
5. Unique source code: yes, including interface derivation and historical phase scripts. Active interface scripts were migrated to root.
6. Unique scientific evidence/provenance: yes, especially PCNA interface maps, phase reports, wiki, labels/manifests. Preserved in archive; active interface map migrated.
7. Historical Phase 2/3/4 material: mostly yes.
8. Current MD/GNN command requirement: no command should require the old `Desktop/GNN_PCNA/` path after migration.
9. Newer/superior files: current MD fixes live outside it; root-level GNN from graph-leakage-fix is the preferred executable code. Nested material is mainly provenance.
10. Valuable unique contents migrated: `derive_pcna_interface_contacts.py`, `check_prediction_overlap.py`, `pcna_interface_map.json`, `pcna_interface_contacts_derived.json`.

## Recommendation

PARTIALLY_MIGRATE_THEN_REMOVE

Implemented as: migrate active unique files to root, then archive the remaining tree at `archive/historical_desktop_gnn_pcna_202605_phase2_phase4/` rather than delete unique provenance.
