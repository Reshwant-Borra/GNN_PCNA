# Dataset Acquisition Log

## Conservative Status

- Final status: `RAW_ASSETS_ACQUIRED_NOT_VERIFIED`
- Adoption status: `not_adopted`
- Quarantine status: `raw_unverified`
- Training, graph generation, split freeze, label freeze, evaluation, MD, and claims remain blocked.

## Acquisition Summary

- Dry run: `True`
- Sources: none
- Downloaded: 0
- Skipped: 0
- Linked only: 0
- Failed: 0
- Downloaded bytes: 1283534817
- Stop markers: none

## Provenance

- Date: 2026-05-27T17:54:12-04:00
- Script/command used: `scripts/dataset_intake.py report`
- Source paths inspected: `data/registries/download_manifest.jsonl`, `data/raw_intake/`, source adapter official URLs
- Confidence level: high for local manifest/report generation; uncertain for external source completeness until official audits finish
- Evidence status: verified for local files and manifest rows; inferred/uncertain for external source content not downloaded
- Python: `3.11.7`
- Unresolved questions: licenses, schemas, leakage, PCNA/homolog screening, label definitions, and human approvals remain unresolved

## Update Note

- Updated at: 2026-05-27T17:54:12-04:00
- Prior useful content was superseded by manifest-derived regenerated sections.
- Reason: governed dataset intake run/report regeneration.

