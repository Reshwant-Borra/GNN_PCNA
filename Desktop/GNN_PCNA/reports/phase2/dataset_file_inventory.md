# Dataset File Inventory

## Conservative Status

- Final status: `RAW_ASSETS_ACQUIRED_NOT_VERIFIED`
- Adoption status: `not_adopted`
- Quarantine status: `raw_unverified`
- Training, graph generation, split freeze, label freeze, evaluation, MD, and claims remain blocked.

## File Inventory

- `alphafold`: 1 downloaded, 0 linked-only, 2226 bytes, status `quarantined`
- `asd`: 0 downloaded, 1 linked-only, 0 bytes, status `candidate`
- `baseline_tools`: 2 downloaded, 0 linked-only, 11821 bytes, status `quarantined`
- `biogrid`: 0 downloaded, 1 linked-only, 0 bytes, status `candidate`
- `biolip`: 0 downloaded, 2 linked-only, 0 bytes, status `candidate`
- `cryptobench`: 44 downloaded, 1 linked-only, 1282249609 bytes, status `quarantined`
- `pcna_structures`: 4 downloaded, 0 linked-only, 1285208 bytes, status `quarantined`
- `pocketminer`: 1 downloaded, 1 linked-only, 14656 bytes, status `quarantined`
- `scpdb`: 0 downloaded, 1 linked-only, 0 bytes, status `candidate`
- `string`: 0 downloaded, 1 linked-only, 0 bytes, status `candidate`

## Provenance

- Date: 2026-05-27T19:03:36-04:00
- Script/command used: `scripts/dataset_intake.py acquire --source alphafold --target P12004`
- Source paths inspected: `data/registries/download_manifest.jsonl`, `data/raw_intake/`, source adapter official URLs
- Confidence level: high for local manifest/report generation; uncertain for external source completeness until official audits finish
- Evidence status: verified for local files and manifest rows; inferred/uncertain for external source content not downloaded
- Python: `3.11.7`
- Unresolved questions: licenses, schemas, leakage, PCNA/homolog screening, label definitions, and human approvals remain unresolved

## Update Note

- Updated at: 2026-05-27T19:03:36-04:00
- Prior useful content was superseded by manifest-derived regenerated sections.
- Reason: governed dataset intake run/report regeneration.

