# Repository Structure

Canonical active directories:

```text
src/                         # active GNN package consolidated from graph-leakage-fix
scripts/                     # active GNN/data utility scripts plus governed acquisition scripts
md_validation_4070/          # active MD prep/run/analyze and GNN-to-MD handoff tools
data/raw_intake/             # official downloaded source structures/metadata
_data generated externally_  # data/raw, data/esm_features, data/graphs*, checkpoints are generated/rebuildable or artifact-managed
data/registries/             # active registries including PCNA interface map
reports/final_consolidation/ # this audit
reports/pre_md_independent_extraction_20260815/ # independent extraction selection + final stability reports
reports/phase2/              # historical source acquisition reports
research_os*/                # research-governance framework, retained as reference infrastructure
docs/research_base/          # canonical scientific knowledge base
archive/historical_desktop_gnn_pcna_202605_phase2_phase4/ # archived nested historical worktree
```

`Desktop/GNN_PCNA/` is no longer an active path. Unique active provenance was migrated to root before archiving.

Current pre-MD artifacts:

```text
artifacts/pre_md_independent_extraction_20260815/
  predeclared_extraction_selection_spec.json
  frozen_extraction_method.json
  independent_extraction_selection_results.json
  final_1w60_three_seed_stability_report.json
  final_consensus_pocket_handoff.json
```

These artifacts are authoritative for the final pre-MD extraction/stability gate. They do not authorize production MD without human Gate-6 approval.

Post-pass stronger robustness diagnostics are under:

```text
artifacts/strong_robustness_20260815/
reports/strong_robustness_20260815/
```

These diagnostics are authoritative for the later internal release-readiness assessment. They did not freeze a replacement extraction policy and did not launch MD.
