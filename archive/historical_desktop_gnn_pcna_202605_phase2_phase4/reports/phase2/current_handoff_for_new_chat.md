# Phase 2 Current Handoff For New Chat

## Status

- Date: 2026-05-27
- Evidence status: verified for local files, manifests, hashes, and reports; uncertain for scientific usability until deep audit.
- Confidence level: high for workflow/provenance status.
- Current status: `CRYPTOBENCH_READY_FOR_SCHEMA_AUDIT`
- Not ready for: training, graph generation, split freeze, label freeze, MD, evaluation, or claims.

## What Was Built

Implemented a governed Dataset Intake Agent:

- CLI: `scripts/dataset_intake.py`
- Validator: `scripts/validate_dataset_intake.py`
- Schema-first audit script: `scripts/cryptobench_schema_first_audit.py`
- Package: `src/phase2_intake/`
- Tests: `tests/test_phase2_intake.py`

Capabilities:

- Official-source adapters for CryptoBench/OSF/GitHub, RCSB PCNA structures, BioLiP, scPDB, PDBbind, ASD, PocketMiner, fpocket/P2Rank, AlphaFold, BioGRID/STRING, and PubMed metadata.
- Dry-run mode.
- Quarantined raw-intake writes under `data/raw_intake/<source_name>/`.
- Append-only manifest at `data/registries/download_manifest.jsonl`.
- Dataset inventory at `data/registries/dataset_inventory.json` and `.csv`.
- SHA-256 hashing for completed downloads.
- Explicit license/schema/trust/quarantine statuses.
- 500 MB single-file/archive approval gate.
- 20 GB total source cap.
- No training, graph generation, MD, split freeze, label freeze, or dataset adoption.

## What Was Acquired Locally

CryptoBench official OSF/GitHub assets were acquired into quarantined raw intake:

- OSF project metadata.
- OSF file/folder listings.
- OSF MIT license metadata.
- GitHub repository metadata.
- `dataset.json`.
- `folds.json`.
- train/test fold JSON files.
- `noncryptic-pockets.json`.
- small support/code/model files.
- `cif-files.zip`.

Targeted RCSB PCNA structures were also acquired:

- `8GLA` metadata and mmCIF.
- `1W60` metadata and mmCIF.

Raw files are intentionally not committed to Git. They remain local under `data/raw_intake/` and are represented by manifest/inventory/report hashes.

## CryptoBench Bulk Archive

- Path: `data/raw_intake/cryptobench/files/672a0171eae0bff252ba9ea3_cif-files.zip`
- Size: `1,145,203,712 bytes`
- SHA-256: `8d15f897bfdfdf61c7d97a29f5f6ca2c5e03d73d8fb89be7da5bbc245cf56ae4`
- Approval record: `data/registries/bulk_download_approvals.json`
- ZIP inventory: 5,005 `.cif` files under `cif-files/`
- Total uncompressed size from ZIP metadata: `4,537,113,269 bytes`
- Archive can be opened with Python `zipfile`.
- Archive has not been extracted into canonical graph/data folders.

## Key Reports

- `reports/phase2/friend_dataset_acquisition_report.md`
- `reports/phase2/dataset_acquisition_log.md`
- `reports/phase2/dataset_file_inventory.md`
- `reports/phase2/license_and_terms_review.md`
- `reports/phase2/dataset_schema_first_pass.md`
- `reports/phase2/dataset_adoption_recommendation.md`
- `reports/phase2/cryptobench_schema_first_audit.md`

## Validation Already Run

Passing checks:

- `python scripts/validate_dataset_intake.py`
- `python scripts/phase2_foundation_check.py`
- `python -m unittest discover -s tests -v`

## Important Governance State

- All raw assets remain `raw_unverified`.
- Dataset adoption status remains `not_adopted`.
- CryptoBench is ready for formal schema audit only.
- Split freeze is not authorized.
- Label freeze is not authorized.
- Graph generation is not authorized.
- Training is not authorized.
- MD is not authorized.
- Scientific claims are not authorized.

## Next Step

The next correct step is the full CryptoBench schema and biological audit phase, using `docs/next_prompts/cryptobench_deep_audit_prompt.md`.

Do not proceed to training, graph construction, split freeze, label freeze, MD, or claims until the deep audit and human review gates pass.

