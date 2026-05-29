---
type: phase3-framework-rebuild-report
date: 2026-05-28
agent: codex
status: audit_ready_no_training
---

# Phase 3 Framework Rebuild Report - 2026-05-28

## Summary

Codex rebuilt the governed Phase 3 data pipeline and framework skeleton because the reported
Friend Phase 3 implementation was not present on local `main` or inspected remote branches.
No real training, fine-tuning, gradient computation, graph tensor generation, baseline run,
test-set evaluation, or scientific claim was performed.

The rebuilt framework uses frozen Phase 2 CryptoBench artifacts only. The Friend/40GB crawl
is explicitly rejected as a Phase 3 supervised source.

## Implemented Artifacts

| Artifact | Path | Status |
|---|---|---|
| Phase 3 data package | `src/phase3_data/` | implemented |
| Dry-run training gate | `src/phase3_training/` | implemented, real training blocked |
| Model interface stubs | `src/phase3_model/` | interface only |
| Evaluation interface stubs | `src/phase3_evaluation/` | interface only |
| Baseline interface stubs | `src/baselines/` | interface only |
| Phase 3 tests | `tests/phase3/` | passing |
| Input validation manifest | `data/registries/phase3_input_validation_20260528.json` | PASS |
| CIF extraction manifest | `data/registries/phase3_cif_extraction_manifest_20260528.json` | PASS |
| Dataset index | `data/registries/phase3_dataset_index_20260528.json` | PASS, 1,101 entries |
| Residue audit manifest | `data/registries/phase3_residue_audit_manifest_20260528.json` | PASS, 1,101 structures |

## Provenance

Commands run:

```powershell
$env:PYTHONPATH='src'; python -m phase3_data.cli validate-inputs --output data/registries/phase3_input_validation_20260528.json
$env:PYTHONPATH='src'; python -m phase3_data.cli verify-or-extract-cifs --output data/registries/phase3_cif_extraction_manifest_20260528.json
$env:PYTHONPATH='src'; python -m phase3_data.cli build-index --split all --output data/registries/phase3_dataset_index_20260528.json
$env:PYTHONPATH='src'; python -m phase3_data.cli audit-residues --split all --output data/registries/phase3_residue_audit_manifest_20260528.json
python -m pytest tests/test_phase2_intake.py tests/phase3
$env:PYTHONPATH='src'; python -m phase3_training.cli --root .
$env:PYTHONPATH='src'; python -m phase3_training.cli --root . --real-training
```

Input hashes:

| Input | SHA-256 |
|---|---|
| `data/registries/split_manifest_frozen.json` | `84d24f92694027b19a534c3bec3fa020e684d1d61bdd6b5763ade65cb2d7f308` |
| `data/labels/label_manifest.json` | `1c902a091561bb6e8e30bb612a3347d29b90b7965842e59d586fceb8a13b7113` |
| `data/registries/excluded_records.json` | `c7bcf1a7541e6f7a138149b86ffa3cae473a1f64a1ba798728993b055996480a` |
| `data/registries/sequence_cluster_assignments.json` | `a59c109ca15f58bfc82a4f41e45b35606a2386e08998f90e41f7176c82e12892` |
| `data/raw_intake/cryptobench/files/672a0171eae0bff252ba9ea3_cif-files.zip` | `8d15f897bfdfdf61c7d97a29f5f6ca2c5e03d73d8fb89be7da5bbc245cf56ae4` |

Output hashes:

| Output | SHA-256 |
|---|---|
| `data/registries/phase3_input_validation_20260528.json` | `7ea1725ceb0622ce53ae17d358c51b1a7afbbf0923f202e6c1babfc81ec8224e` |
| `data/registries/phase3_cif_extraction_manifest_20260528.json` | `e7a65fa6fd2a3e54d962625a216ecdb4349d8ee8a5f8ed98c2eba31c2876f5ee` |
| `data/registries/phase3_dataset_index_20260528.json` | `168bf56cb674f05d724d8e711254e64b3d029e252a8bdf5edc258c6bbdfe491b` |
| `data/registries/phase3_residue_audit_manifest_20260528.json` | `54e1681880bf09df5a372514098e7516d74511cfebf25970adb3a7c7a2bef9d0` |

## Audit Results

- CIF archive extraction: PASS. Extracted `5,005` `.cif` files under `data/raw_intake/cryptobench/cif-files/`.
- Dataset index: PASS. Indexed `1,101` non-excluded frozen structures. Fold distribution: test=214, train-0=220, train-1=223, train-2=222, train-3=222.
- Exclusions: all 6 records from `data/registries/excluded_records.json` skipped.
- PCNA isolation: no `cluster_id_30=1168` structures appear in the Phase 3 dataset index.
- Residue audit: PASS across `1,101` structures.
- Residue nodes audited: `371,651`.
- Positive labels aligned: `16,335`.
- Masked labels on nodes: `3,696`.
- Masked label entries without nodes: `8`, recorded explicitly and excluded from loss.
- Background/unlisted residues: `351,620`, recorded as positive-unlabeled background, not true negatives.
- Residues with alternate location IDs: `4,380`, recorded for human review.
- Residues without CA atom: `22`, recorded for human review.

No edge policy, atom cutoff, feature policy, model architecture, class weighting, baseline
execution, or evaluation threshold was chosen. The residue audit manifest records
`UNAPPROVED_NOT_GENERATED` for edge and feature policy.

## Verification

`python -m pytest tests/test_phase2_intake.py tests/phase3`:

```text
16 passed in 0.23s
```

Dry-run trainer:

```text
status: DRY_RUN_ONLY
training: NOT_PERFORMED
gradients: NOT_COMPUTED
```

Real-training attempt:

```text
Phase 3 training blocked: Real Phase 3 training is blocked until the data pipeline/graph audit has human sign-off.
```

## Governance Read

- `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`
- `docs/scientific_governance/05_SPLIT_PROTOCOL.md`
- `docs/scientific_governance/06_LABELING_RULES.md`
- `docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md`
- `docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md`
- `docs/scientific_governance/09_EVALUATION_PROTOCOL.md`
- `docs/scientific_governance/10_BASELINE_REQUIREMENTS.md`
- `docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md`
- `docs/scientific_governance/16_CODING_AGENT_RULES.md`
- `docs/scientific_governance/19_STOP_CONDITIONS.md`
- `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`

## Remaining Gates

- Human review is required before first graph release and before any real Phase 3 training.
- Edge definition, atom basis, cutoff, and feature policy remain unapproved and were not invented.
- Model architecture, baselines, evaluation protocol instantiation, test-set evaluation, and claims remain future gated work.

Confidence: high for local implementation, artifact counts, hashes, and test results.
Evidence status: verified for generated artifacts and tests; unresolved for future graph/model science.
