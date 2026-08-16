# Label Supervision Risks

## Summary

CryptoBench pocket selections can be considered candidate benchmark supervision only if Phase 2 explicitly treats them as partial, proxy pocket-region labels.

## Risks

| Risk | Status | Consequence |
| --- | --- | --- |
| Unlisted residues are not true negatives | Blocking for dense BCE without policy | Metrics can reward false background assumptions. |
| Pocket selections are proxy labels | Known | Cannot claim experimental cryptic truth for every residue. |
| Noncryptic auxiliary structures missing | Known | Noncryptic records cannot be used as complete negative supervision. |
| Residue-token mapping failures | 721 failures | Label-node alignment can break. |
| PCNA contamination | Known | PCNA final interpretation would be leaked if not isolated. |

## Defensible Direction

- Use cryptic pocket selections as positive/partial-label supervision only after mapping failures are resolved or masked.
- Treat unselected residues as unlabeled/background for training design until a human-approved negative policy exists.
- Do not mix noncryptic auxiliary records into training before missing structures and semantics are resolved.

## Provenance

- Date: 2026-05-27T19:09:22-04:00
- Command: `python scripts/phase2_remediation_packet.py`
- Source paths: `reports/phase2/cryptobench_*`, `data/registries/cryptobench_*`, `data/registries/dataset_inventory.json`, `data/raw_intake/`
- Governance paths: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`
- Confidence: high for local file-derived counts and registry generation; medium for recommended remediation status; low for unresolved homolog safety until clustering is run.
- Evidence status: verified for local artifacts; inferred for planning recommendations; uncertain for final scientific usability.
