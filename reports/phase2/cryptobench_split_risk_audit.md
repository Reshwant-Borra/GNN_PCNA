# CryptoBench Split Risk Audit

## Status

- Final audit status: `SPLIT_RISK_UNRESOLVED_NOT_FROZEN`
- The provided folds are usable as source metadata, not as a Phase 2 frozen split.

## Fold Integrity

| Fold | folds.json apo | fold file apo | Keys match | Missing | Extra |
| --- | --- | --- | --- | --- | --- |
| test | 222 | 222 | True | 0 | 0 |
| train-0 | 219 | 219 | True | 0 | 0 |
| train-1 | 222 | 222 | True | 0 | 0 |
| train-2 | 222 | 222 | True | 0 | 0 |
| train-3 | 222 | 222 | True | 0 | 0 |

## Leakage Checks Available From Local Files

- Duplicate apo IDs across folds: 0.
- Duplicate fold assignments in `folds.json`: 0.
- UniProt IDs appearing in more than one fold: 0.
- UniProt IDs shared between train folds and test: 0.
- Holo PDB IDs appearing in more than one fold: 6.

## Interpretation

- The fold files are internally consistent with `folds.json` if the table above reports `True` for each fold.
- The local split files do not include sequence-cluster IDs, homolog-cluster IDs, structural similarity clusters, or an apo/holo grouping proof.
- Repeated UniProt IDs across folds are direct leakage risks under Phase 2 governance, even if benchmark authors intended a different evaluation design.
- Homolog leakage risk remains unresolved until sequence clustering and structural review are run under an approved protocol.
- Split freeze is not feasible from these files alone.

## Train/Test Shared UniProt IDs

None detected by exact UniProt ID. Homolog risk remains unresolved.

## Provenance

- Date: 2026-05-27T18:29:47-04:00
- Command: `python scripts/cryptobench_deep_audit.py`
- Source paths: `data/raw_intake/cryptobench/metadata_files/`, `data/raw_intake/cryptobench/labels_or_splits/`, `data/raw_intake/cryptobench/files/672a0171eae0bff252ba9ea3_cif-files.zip`
- Governance paths: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `14_CLAIM_POLICY.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`
- Confidence: high for local schema/count/hash/readability checks; medium for label-semantic interpretation from local README; low for homolog exclusion because no sequence clustering was run.
- Evidence status: verified for local files and machine checks; inferred for biological meaning; uncertain for final scientific usability.
