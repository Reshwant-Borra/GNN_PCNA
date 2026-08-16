# Reproducibility Report

Date: 2026-08-15

## Environment

- Python used for this pass: `python3`
- This shell lacks ML/MD dependencies such as torch, torch_geometric, numpy, sklearn, OpenMM, MDTraj, MDAnalysis, and BioPython.
- `scripts/independent_extraction_gate.py` is stdlib-only and did not retrain or rescore the GNN.

## Commands executed

```bash
python3 scripts/independent_extraction_gate.py select-policy
python3 scripts/independent_extraction_gate.py apply-1w60
```

Validation commands:

```bash
python3 -m pytest tests/test_scientific_guardrails.py tests/test_pre_md_release_gate.py -q
python3 -m pytest tests -q
rg -n "Desktop/GNN_PCNA" . --glob '!archive/**' --glob '!node_modules/**' --glob '!reports/final_consolidation/**'
```

Actual results in `.venv_gnn_pcna`:

- Targeted governance/pre-MD tests: `25 passed, 4 skipped`.
- Full repository tests: `90 passed, 7 skipped`.
- Registry validation: all seven ResearchOS JSON registries OK.
- Active old-path check: no executable dependency on `Desktop/GNN_PCNA`; remaining matches are documentation/provenance statements or generated historical diagnostics.
- `Desktop/` contains zero files.
- `gnn_pcna_pre_md_v3.zip`: not found.
- Production MD process/artifact check: no running MD process detected; no trajectory/log files created by this task.

## Active artifacts

- `artifacts/pre_md_independent_extraction_20260815/predeclared_extraction_selection_spec.json`
- `artifacts/pre_md_independent_extraction_20260815/frozen_extraction_method.json`
- `artifacts/pre_md_independent_extraction_20260815/independent_extraction_selection_results.json`
- `artifacts/pre_md_independent_extraction_20260815/final_1w60_three_seed_stability_report.json`
- `artifacts/pre_md_independent_extraction_20260815/final_consensus_pocket_handoff.json`

## Provenance

Artifacts and experiment records were registered in `research_os_registries/artifact_registry.json` and `research_os_registries/experiment_registry.json`. The decision registry contains a non-human process decision that is explicitly not Gate-6 approval.

## Missing external dependencies

Production ML/MD commands cannot run in this shell. No production MD was launched.

## Next reproducible action

Review Gate-6 packet. After legitimate human approval only, activate the MD environment and run preparation validation/smoke tests before production MD.
