# E004: Homology-Clean Benchmark Remediation

**Status:** completed
**Date started:** 2026-05-22
**Date completed:** 2026-05-22

-> Links: [[EXPERIMENT_INDEX]] | [[VALIDATION]] | [[KNOWN_LIMITATIONS]] | [[BUG_LOG]]

---

## Completion Summary

Phase 2 clean-split remediation is complete. The MMseqs2 30% homology-clean split passed leakage audit, all four clean-split ablation conditions were trained for seeds 42/43/44, and final evaluation was written to `data/results/clean_split_evaluation.json` and `data/results/clean_split_summary.md`.

Use this interpreter:

```powershell
.\.venv-clean\Scripts\python.exe
```

Final commands run:

```powershell
.\.venv-clean\Scripts\python.exe scripts\train_ablation_suite.py --skip-env-check --conditions xl_geometry --seeds 43 44
.\.venv-clean\Scripts\python.exe scripts\train_ablation_suite.py --skip-env-check --conditions xl_esm_zero --seeds 42 43 44
.\.venv-clean\Scripts\python.exe scripts\train_ablation_suite.py --skip-env-check --conditions xl_esm_full --seeds 42 43 44
.\.venv-clean\Scripts\python.exe scripts\evaluate_clean_split.py --conditions small_geometry xl_geometry xl_esm_zero xl_esm_full --seeds 42 43 44
```

Final benchmark summary:

| Condition | Seeds | Test AUPRC mean | 95% CI | Test AUROC mean | Degenerate test structures |
|---|---:|---:|---|---:|---:|
| small_geometry | 3 | 0.1551 | 0.0549-0.2426 | 0.7626 | 2 |
| xl_geometry | 3 | 0.1923 | 0.1161-0.2682 | 0.8325 | 2 |
| xl_esm_zero | 3 | 0.1071 | 0.0465-0.1773 | 0.6815 | 2 |
| xl_esm_full | 3 | 0.2513 | 0.1267-0.3815 | 0.8649 | 2 |

Interpretation: `xl_esm_full` is the strongest condition, but the gap versus `xl_esm_zero` means the final benchmark is ESM2-augmented and sequence context is a major confound. Geometry-only XL remains above the small model, but the result should be framed as exploratory candidate prioritization, not validated cryptic-pocket prediction.

---

## Why This Remediation Exists

The old benchmark cannot support final scientific claims.

Previously known issues that still frame the work:

- The old CryptoSite split was random, not homology-clustered.
- Leakage was detected in the old split:
  - `1O3P` / `1SQO`: 99.18%
  - `1M17` / `1XKK`: 92.39%
  - `1JBP` / `3D0E`: 34.63%
- The old homology checker was unreliable for final science because it reported impossible negative identity statistics.
- ESM2 confounding is now resolved for reporting: `xl_esm_full` is strongest, while `xl_esm_zero` drops substantially, so sequence/ESM2 contribution is a major confound.
- Clean validation is much weaker than the old headline numbers.
- GNN rerun is required for final benchmark claims.
- MD rerun is not required for this remediation; current MD/ANM evidence should remain preliminary.
- 8GLA is only a positive-control sanity check because it is in PCNA fine-tuning.
- Do not report 8GLA AUROC as independent performance.
- Use "GNN-prioritized candidate residue cluster", not "validated cryptic pocket".
- State that current MD fold-change `<1.0` is not supportive of enhanced apo pocket flexibility.

Final benchmark claims must cite clean-split AUPRC with confidence intervals and disclose ESM2 contribution.

---

## What Was Implemented

### New Scripts

| File | Purpose |
|---|---|
| `scripts/make_homology_split.py` | Extract chain FASTA from labeled CryptoSite PDBs, run MMseqs2 at 30% identity, collapse chain clusters into structure-level connected components, split components, and write the split/audit. |
| `scripts/validate_split_integrity.py` | Validate every split ID has exactly one graph, labels, feature dimension, non-empty node set, and degenerate-label flagging. |
| `scripts/train_ablation_suite.py` | Run the required four-condition, three-seed clean ablation suite. |
| `scripts/evaluate_clean_split.py` | Evaluate clean split with validation-selected MCC threshold, AUPRC primary, AUROC secondary, structure-bootstrap CIs, and degenerate-label exclusion. |

### Updated Code

| File | Change |
|---|---|
| `src/training/train.py` | Added seed control, homology-audit fail-fast, `--zero_esm`, `--condition`, split hash, graph manifest hash, command, environment summary, git commit, seed, node dimension, and provenance in `best_meta.json`. |
| `scripts/check_env.py` | PyG, `torch_scatter`, and `torch_sparse` are hard requirements for ML commands. |
| `tests/test_graph_shape.py` | Model/graph tests now fail if PyG is missing instead of silently skipping. |
| `tests/test_checkpoint_loading.py` | Checkpoint tests now fail if PyG or expected checkpoints are missing instead of giving false confidence. |
| `.gitignore` | Added `.venv-clean/` and `tools/` so local setup binaries are not accidentally committed. |

### Updated Docs

| File | Change |
|---|---|
| `README.md` | Old random-split headline benchmark numbers are superseded and should not be cited. |
| `LIMITATIONS.md` | Clean-split AUPRC with CIs is required; old split is superseded. |
| `KNOWN_BUGS.md` | Added/updated bugs for PyG hard requirement, test skip false confidence, homology leakage, and provenance gaps. |
| `docs/logs/BUG_LOG.md` | Mirrored critical remediation bugs. |
| `docs/knowledge/VALIDATION.md` | Rewritten around the clean-split rules and PCNA reporting cleanup. |
| `docs/experiments/EXPERIMENT_INDEX.md` | Added E004 entry. |

---

## Environment Setup Completed

Created local workspace venv:

```powershell
python -m venv .venv-clean --system-site-packages
```

Installed missing ML packages into `.venv-clean`:

```powershell
.\.venv-clean\Scripts\python.exe -m pip install biopython torch-geometric torch-scatter torch-sparse -f https://data.pyg.org/whl/torch-2.9.0+cpu.html
```

Environment check passes with:

```powershell
.\.venv-clean\Scripts\python.exe scripts\check_env.py
```

Observed versions:

- Python: 3.11.7
- Torch: 2.9.1+cpu
- torch_geometric: 2.7.0
- torch_scatter: 2.1.2+pt29cpu
- torch_sparse: 0.6.18+pt29cpu
- Biopython: 1.87

Local MMseqs2 setup:

- Downloaded `mmseqs-win64.zip` from GitHub release `18-8cc5c`.
- Unpacked under `tools/mmseqs-win64/mmseqs`.
- BusyBox helper setup was needed.
- MMseqs2 only ran successfully outside the sandbox because the sandbox caused BusyBox signal-pipe permission errors.
- Verified version hash: `8cc5ce367b5638c4306c2d7cfc652dd099a4643f`.

`tools/` is ignored and should be treated as local setup, not a project artifact.

---

## Artifacts Generated

### Split and Audit

| Artifact | Status | Notes |
|---|---|---|
| `data/splits/cryptosite_homology30_split.json` | created | MMseqs2 30% homology-clean split. |
| `data/results/homology30_audit.json` | created | PASS; no leakage detected. |
| `data/results/mmseqs_homology30_work/cryptosite_chains.fasta` | created | Chain-level FASTA used by MMseqs2. |
| `data/results/mmseqs_homology30_work/cryptosite_homology30_cluster.tsv` | created | MMseqs2 cluster TSV. |
| `data/results/mmseqs_homology30_work/cryptosite_homology30_rep_seq.fasta` | created | MMseqs2 representative sequences. |
| `data/results/mmseqs_homology30_work/cryptosite_homology30_all_seqs.fasta` | created | MMseqs2 clustered sequences. |

Audit result:

- Verdict: `PASS`
- Leakage: `False`
- Structure-level components: `49`
- Split counts:
  - train: `43`
  - val: `6`
  - test: `6`

### Integrity Reports

| Artifact | Status | Notes |
|---|---|---|
| `data/results/split_integrity_40.json` | created | Passed for `data/graphs`, expected node dim 40. |
| `data/results/split_integrity_520.json` | created | Passed for `data/graphs_xl`, expected node dim 520. |

Integrity results:

- 40-dim graph manifest hash: `47fd6d722550ebd1b0f11b5cc3a12987c082d1ca1f5f6a18219ad871662878ac`
- 520-dim graph manifest hash: `69744b548e812697ba9015c6563ed526f1af2e915b1595badb1dd47fd1b4c64f`
- Degenerate-label structures flagged: `6`
- Degenerate structures are not a validator failure; clean evaluation excludes them from aggregate metrics while listing them.

### Clean Evaluation Outputs

| Artifact | Status | Notes |
|---|---|---|
| `data/results/clean_split_evaluation.json` | created | Final all-condition evaluation for four conditions x three seeds. |
| `data/results/clean_split_summary.md` | created | Final all-condition clean-split summary. |
| `data/results/clean_split_evaluation_xl_geometry.json` | created | Three-seed `xl_geometry` condition evaluation. |
| `data/results/clean_split_summary_xl_geometry.md` | created | Three-seed `xl_geometry` condition summary. |
| `data/results/clean_split_evaluation_xl_esm_zero.json` | created | Three-seed `xl_esm_zero` condition evaluation. |
| `data/results/clean_split_summary_xl_esm_zero.md` | created | Three-seed `xl_esm_zero` condition summary. |
| `data/results/clean_split_evaluation_xl_esm_full.json` | created | Three-seed `xl_esm_full` condition evaluation. |
| `data/results/clean_split_summary_xl_esm_full.md` | created | Three-seed `xl_esm_full` condition summary. |
| `data/results/clean_split_evaluation_xl_geometry_seed42.json` | created | Partial result for `xl_geometry` seed 42 only. |
| `data/results/clean_split_summary_xl_geometry_seed42.md` | created | Partial summary for `xl_geometry` seed 42 only. |

Do not treat the partial XL seed-42 result as a final condition result; use the all-condition summary above.

---

## Training Completed

### small_geometry

Condition definition:

- Model: `PocketGNN.small`
- Graph dir: `data/graphs`
- Node dim: `40`
- ESM2: not used
- Seeds required: `42`, `43`, `44`
- Status: complete

Checkpoints:

- `checkpoints/clean_split/small_geometry/seed_42/best.ckpt`
- `checkpoints/clean_split/small_geometry/seed_42/best_meta.json`
- `checkpoints/clean_split/small_geometry/seed_43/best.ckpt`
- `checkpoints/clean_split/small_geometry/seed_43/best_meta.json`
- `checkpoints/clean_split/small_geometry/seed_44/best.ckpt`
- `checkpoints/clean_split/small_geometry/seed_44/best_meta.json`

Training results:

| Seed | Best validation AUROC | Notes |
|---:|---:|---|
| 42 | 0.6652 | Early stopped at epoch 35. |
| 43 | 0.6583 | Early stopped at epoch 44. |
| 44 | 0.6626 | Early stopped at epoch 31. |

Clean test evaluation:

| Condition | Seeds | Test AUPRC mean | 95% CI | Test AUROC mean | Degenerate test structures |
|---|---:|---:|---|---:|---:|
| small_geometry | 3 | 0.1551 | 0.0549-0.2426 | 0.7626 | 2 |

Per-seed test metrics:

| Seed | Validation-selected threshold | Test AUPRC | Test AUROC |
|---:|---:|---:|---:|
| 42 | 0.38427725434303284 | 0.17968969294466844 | 0.7485249591567558 |
| 43 | 0.42855003476142883 | 0.168042056063546 | 0.7667511988665646 |
| 44 | 0.4545102119445801 | 0.11764436685556401 | 0.7723786748942547 |

### xl_geometry

Condition definition:

- Model: `PocketGNNXL`
- Graph dir: `data/graphs`
- Node dim: `40`
- ESM2: not used
- Seeds required: `42`, `43`, `44`
- Status: complete

Completed checkpoints:

- `checkpoints/clean_split/xl_geometry/seed_42/best.ckpt`
- `checkpoints/clean_split/xl_geometry/seed_42/best_meta.json`
- `checkpoints/clean_split/xl_geometry/seed_43/best.ckpt`
- `checkpoints/clean_split/xl_geometry/seed_43/best_meta.json`
- `checkpoints/clean_split/xl_geometry/seed_44/best.ckpt`
- `checkpoints/clean_split/xl_geometry/seed_44/best_meta.json`

Training result:

| Seed | Best validation AUROC | Notes |
|---:|---:|---|
| 42 | 0.7200 | Early stopped at epoch 35. CPU runtime about 10 minutes. |
| 43 | 0.7081 | Early stopped at epoch 33. |
| 44 | 0.6968 | Early stopped at epoch 36. |

Clean test evaluation:

| Condition | Seeds | Test AUPRC mean | 95% CI | Test AUROC mean | Degenerate test structures |
|---|---:|---:|---|---:|---:|
| xl_geometry | 3 | 0.1923 | 0.1161-0.2682 | 0.8325 | 2 |

### xl_esm_zero

Condition definition:

- Model: `PocketGNNXL`
- Graph dir: `data/graphs_xl`
- Node dim: `520`
- ESM2: columns 40: zeroed during training and evaluation
- Seeds required: `42`, `43`, `44`
- Status: complete

Training results:

| Seed | Best validation AUROC | Notes |
|---:|---:|---|
| 42 | 0.6250 | Early stopped at epoch 30. |
| 43 | 0.7352 | Early stopped at epoch 25. |
| 44 | 0.6907 | Early stopped at epoch 26. |

Clean test evaluation:

| Condition | Seeds | Test AUPRC mean | 95% CI | Test AUROC mean | Degenerate test structures |
|---|---:|---:|---|---:|---:|
| xl_esm_zero | 3 | 0.1071 | 0.0465-0.1773 | 0.6815 | 2 |

### xl_esm_full

Condition definition:

- Model: `PocketGNNXL`
- Graph dir: `data/graphs_xl`
- Node dim: `520`
- ESM2: full ESM2 features retained
- Seeds required: `42`, `43`, `44`
- Status: complete

Training results:

| Seed | Best validation AUROC | Notes |
|---:|---:|---|
| 42 | 0.8071 | Early stopped at epoch 28. |
| 43 | 0.8015 | Early stopped at epoch 22. |
| 44 | 0.8039 | Early stopped at epoch 22. |

Clean test evaluation:

| Condition | Seeds | Test AUPRC mean | 95% CI | Test AUROC mean | Degenerate test structures |
|---|---:|---:|---|---:|---:|
| xl_esm_full | 3 | 0.2513 | 0.1267-0.3815 | 0.8649 | 2 |

---

## Phase 2 Completion Status

Required training:

| Condition | Seed 42 | Seed 43 | Seed 44 | Status |
|---|---|---|---|---|
| small_geometry | complete | complete | complete | done |
| xl_geometry | complete | complete | complete | done |
| xl_esm_zero | complete | complete | complete | done |
| xl_esm_full | complete | complete | complete | done |

Required final evaluation:

- Final `scripts/evaluate_clean_split.py` was run across all four conditions after all checkpoints existed.
- The final `data/results/clean_split_evaluation.json` contains all four conditions and all three seeds.
- The final `data/results/clean_split_summary.md` contains all four rows.

Documentation updated:

- `README.md` records final clean-split AUPRC and CI.
- `LIMITATIONS.md` records final clean-split numbers and ESM2 interpretation.
- `docs/knowledge/VALIDATION.md` records final accepted benchmark result.
- This E004 file is marked completed.
- `docs/experiments/EXPERIMENT_INDEX.md` E004 row records the final result.
- No new bugs appeared during remaining XL runs.

### Full Remaining Work Checklist

Use this checklist in a new chat to avoid losing work.

#### A. Finish Required Training Runs

- [x] `small_geometry` seed 42
- [x] `small_geometry` seed 43
- [x] `small_geometry` seed 44
- [x] `xl_geometry` seed 42
- [x] `xl_geometry` seed 43
- [x] `xl_geometry` seed 44
- [x] `xl_esm_zero` seed 42
- [x] `xl_esm_zero` seed 43
- [x] `xl_esm_zero` seed 44
- [x] `xl_esm_full` seed 42
- [x] `xl_esm_full` seed 43
- [x] `xl_esm_full` seed 44

Expected checkpoint layout for each completed run:

```text
checkpoints/clean_split/<condition>/seed_<seed>/best.ckpt
checkpoints/clean_split/<condition>/seed_<seed>/best_meta.json
```

Every `best_meta.json` must contain:

- seed
- condition
- model size
- node dimension
- split hash
- graph manifest hash
- command
- environment summary
- git commit
- homology audit path
- `zero_esm` flag

#### B. Evaluate All Completed Runs

- [x] Evaluate `small_geometry` seeds 42/43/44.
- [x] Evaluate partial `xl_geometry` seed 42 separately.
- [ ] Re-run final evaluation after all required checkpoints exist.
- [ ] Confirm final `clean_split_evaluation.json` has all four conditions.
- [ ] Confirm final `clean_split_summary.md` has all four conditions.
- [ ] Confirm test metrics use validation-selected threshold only.
- [ ] Confirm bootstrap confidence intervals resample structures, not residues.
- [ ] Confirm degenerate-label structures are listed individually and excluded from aggregate claims.

Final evaluation command:

```powershell
.\.venv-clean\Scripts\python.exe scripts\evaluate_clean_split.py --conditions small_geometry xl_geometry xl_esm_zero xl_esm_full --seeds 42 43 44
```

#### C. Interpret ESM2 Confounding

After final evaluation, compare:

- `small_geometry`
- `xl_geometry`
- `xl_esm_zero`
- `xl_esm_full`

Interpretation rules:

- If `xl_geometry` performs near `small_geometry`, do not claim strong structural learning from XL architecture alone.
- If `xl_esm_full` is much stronger than `xl_esm_zero`, label results as ESM2-augmented and treat sequence contribution as a major confound.
- If `xl_esm_zero` remains strong, then ESM2 columns are not the only driver, but still compare to `xl_geometry`.
- If clean test AUPRC is near positive-fraction baseline, frame the project as a pipeline prototype rather than a validated predictor.
- Do not use old random-split AUROC/AUPRC numbers as headline results.

#### D. Documentation To Update After Final Results

- [x] `README.md`
  - Replace any remaining benchmark narrative with final clean-split AUPRC and CI.
  - Keep AUROC secondary.
  - State whether the final result is geometry-only, ESM2-augmented, or weak/prototype-level.
- [x] `LIMITATIONS.md`
  - Add final clean split metrics.
  - Explicitly discuss homology-clean split size and limitations.
  - Discuss degenerate structures and label sparsity.
  - Discuss ESM2 confounding based on ablation result.
- [x] `docs/knowledge/VALIDATION.md`
  - Add final benchmark table.
  - State final accepted checkpoint/condition if one is chosen.
  - State that AUPRC is primary.
- [x] `docs/experiments/E004_homology_clean_benchmark.md`
  - Add final metrics.
  - Mark completed only after final evaluation and documentation are done.
- [x] `docs/experiments/EXPERIMENT_INDEX.md`
  - E004 row records `completed` and the final clean-split result.
- [x] `KNOWN_BUGS.md` and `docs/logs/BUG_LOG.md`
  - Add any new issues found during remaining XL runs.
  - BUG-011 and BUG-012 no longer require rerun after final ablation completion.
- [x] `docs/logs/DECISIONS.md`
  - Add a decision entry for the final benchmark framing and whether ESM2 is a confound.

#### E. Artifact Cleanup And Commit Decisions

- [ ] Decide whether `checkpoints/clean_split/` should be tracked, moved to large-file storage, or documented as local artifact only.
- [ ] Decide whether `data/results/mmseqs_homology30_work/*.fasta` and `*.tsv` should be tracked.
- [ ] Keep `.venv-clean/` ignored.
- [ ] Keep `tools/` ignored.
- [ ] Do not commit generated `__pycache__` modifications.
- [ ] If tracked bytecode files show as modified, restore them before commit:

```powershell
git restore -- src/data_processing/__pycache__/graph_construction.cpython-311.pyc src/models/__pycache__/cryptic_gnn.cpython-311.pyc src/training/__pycache__/train.cpython-311.pyc tests/__pycache__/test_checkpoint_loading.cpython-311-pytest-7.4.0.pyc tests/__pycache__/test_graph_shape.cpython-311-pytest-7.4.0.pyc
```

#### F. Validation And Sanity Checks

- [x] Run `.\.venv-clean\Scripts\python.exe scripts\check_env.py`.
- [x] Run `.\.venv-clean\Scripts\python.exe -m pytest tests -q`.
- [x] Re-run `scripts/validate_split_integrity.py` for 40-dim graphs if graphs change.
- [x] Re-run `scripts/validate_split_integrity.py` for 520-dim graphs if graphs change.
- [x] Confirm `data/results/homology30_audit.json` still reports `PASS` and `leakage_detected: false`.
- [x] Confirm no PDB ID appears in more than one split.
- [x] Confirm no component appears in more than one split.
- [x] Confirm `best.ckpt` loads for every final run.
- [x] Confirm checkpoint node dimension matches graph node dimension in evaluation.

#### G. PCNA Reporting Cleanup Still Needed

- [ ] Keep `8GLA` only as a positive-control sanity check.
- [ ] Never report `8GLA` AUROC as independent performance.
- [ ] Regenerate PCNA per-structure reports only after selecting the final checkpoint.
- [ ] Use "GNN-prioritized candidate residue cluster", not "validated cryptic pocket".
- [ ] State that current MD fold-change `<1.0` is not supportive of enhanced apo pocket flexibility.
- [ ] Do not claim druggability, docking readiness, apo-to-holo opening, or AOH1996 mechanism from the GNN alone.

#### H. Final Acceptance Criteria

- [x] Homology audit reports zero train-to-val/test leakage at 30% identity.
- [x] Degenerate-label structures are excluded from aggregate claims.
- [x] Three-seed clean-split results are available for all four conditions.
- [x] ESM2 ablation separates sequence contribution from geometry contribution.
- [x] Headline claims cite clean-split AUPRC with confidence intervals.
- [x] AUROC appears only as secondary/supporting metric.
- [x] Documentation contains no stale random-split or contaminated-split headline numbers.
- [x] Final scientific framing matches the actual ablation result.

---

## Exact Commands Run

Run from repo root: `C:\Users\reshw\GNN_PNCA`

### 1. XL geometry

```powershell
.\.venv-clean\Scripts\python.exe scripts\train_ablation_suite.py --skip-env-check --conditions xl_geometry --seeds 43 44
```

### 2. XL ESM-zero ablation

```powershell
.\.venv-clean\Scripts\python.exe scripts\train_ablation_suite.py --skip-env-check --conditions xl_esm_zero --seeds 42 43 44
```

### 3. XL ESM-full ablation

```powershell
.\.venv-clean\Scripts\python.exe scripts\train_ablation_suite.py --skip-env-check --conditions xl_esm_full --seeds 42 43 44
```

### 4. Final evaluation

```powershell
.\.venv-clean\Scripts\python.exe scripts\evaluate_clean_split.py --conditions small_geometry xl_geometry xl_esm_zero xl_esm_full --seeds 42 43 44
```

### 5. Verify tests

```powershell
.\.venv-clean\Scripts\python.exe -m pytest tests -q
```

Expected current test result:

- `16 passed, 1 warning`

---

## Issues Encountered During This Work

### Missing PyG stack

Problem:

- Base Python had Torch but not Biopython or PyG packages.
- `scripts/check_env.py` failed on:
  - `biopython`
  - `torch_geometric`
  - `torch_scatter`
  - `torch_sparse`

Resolution:

- Created `.venv-clean` and installed packages there.
- Do not assume base Python is valid. Use `.venv-clean`.

### Network sandbox blocked pip

Problem:

- Initial `pip install` failed with proxy/network errors.

Resolution:

- Re-ran install with elevated network approval.

### MMseqs2 missing

Problem:

- `where.exe mmseqs` found nothing.
- No conda/mamba/micromamba available.

Resolution:

- Used official MMseqs2 Windows release asset from GitHub.
- Installed locally under ignored `tools/`.

### MMseqs2 BusyBox permission issue

Problem:

- `mmseqs.bat version` failed in sandbox with:
  - BusyBox helper install needed.
  - signal-pipe permission error.

Resolution:

- Ran BusyBox helper install outside sandbox.
- MMseqs2 must be run outside sandbox if the same signal-pipe error recurs.

### MMseqs2 tmp folder broke pytest discovery

Problem:

- Running `pytest` from repo root collected into `data/results/mmseqs_homology30_work/tmp/latest`, causing:
  - `OSError: [WinError 1920] The file cannot be accessed by the system`

Resolution:

- Removed `data/results/mmseqs_homology30_work/tmp`.
- Run tests explicitly as `pytest tests -q`.
- The persistent MMseqs2 work artifacts are FASTA/TSV files only.

### CLI relative-path printing bugs

Problem:

- `validate_split_integrity.py` and `evaluate_clean_split.py` wrote outputs but crashed when printing `relative_to(REPO)` on relative `--out` paths.

Resolution:

- Added `display_path()` helper to both scripts.
- Reran validators/evaluators successfully.

### Tracked bytecode churn

Problem:

- Running tests/training modified tracked `__pycache__` files that already exist in git.

Resolution:

- Restored tracked bytecode files with `git restore`.
- If they reappear in `git status`, restore them again before committing.

### CPU-only runtime

Problem:

- Current environment reports `torch.cuda.is_available() == False`.
- XL runs are CPU-only and slow.

Resolution:

- Continue on CPU if acceptable.
- If GPU becomes available, rerun from same scripts with same seeds and document environment changes.

---

## Current Git/Workspace Notes

Expected modified tracked files from remediation:

- `.gitignore`
- `README.md`
- `LIMITATIONS.md`
- `KNOWN_BUGS.md`
- `docs/experiments/EXPERIMENT_INDEX.md`
- `docs/experiments/E004_homology_clean_benchmark.md`
- `docs/knowledge/VALIDATION.md`
- `docs/logs/BUG_LOG.md`
- `scripts/check_env.py`
- `src/training/train.py`
- `tests/test_checkpoint_loading.py`
- `tests/test_graph_shape.py`

Expected new tracked candidates:

- `scripts/make_homology_split.py`
- `scripts/validate_split_integrity.py`
- `scripts/train_ablation_suite.py`
- `scripts/evaluate_clean_split.py`
- `data/splits/cryptosite_homology30_split.json`
- `data/results/homology30_audit.json`
- `data/results/split_integrity_40.json`
- `data/results/split_integrity_520.json`
- `data/results/clean_split_evaluation.json`
- `data/results/clean_split_summary.md`
- `data/results/clean_split_evaluation_xl_geometry_seed42.json`
- `data/results/clean_split_summary_xl_geometry_seed42.md`
- `data/results/mmseqs_homology30_work/cryptosite_chains.fasta`
- `data/results/mmseqs_homology30_work/cryptosite_homology30_cluster.tsv`
- `data/results/mmseqs_homology30_work/cryptosite_homology30_rep_seq.fasta`
- `data/results/mmseqs_homology30_work/cryptosite_homology30_all_seqs.fasta`
- `checkpoints/clean_split/...` checkpoint outputs, if large-file policy allows them

Expected ignored local setup:

- `.venv-clean/`
- `tools/`

Pre-existing unrelated untracked files were present before/around this work and should not be reverted casually:

- `analysis_pilot/`
- `data/md/1W60_production.dcd`
- `data/md/1W60_topology.pdb`
- `data/md/equil_npt.chk`
- `data/md/equil_nvt.chk`
- `data/md/production.log`

---

## Acceptance Criteria Status

The final benchmark is acceptable for reporting with the limitations documented above.

Completed:

- Homology audit: done, PASS.
- Degenerate-label structures excluded from aggregate claims: implemented and used.
- Three-seed clean-split results for all four conditions: done.
- ESM2 ablation separating sequence contribution from geometry contribution: done.
- All headline claims cite clean-split AUPRC with confidence intervals: done.
- Documentation contains no stale random-split or contaminated-split headline numbers: done.

Scientific framing:

- Final claim: ESM2-augmented GNN has exploratory signal for candidate residue prioritization.
- Geometry-only XL remains above the small model, but ESM2/sequence contribution is a major confound because `xl_esm_full` is strongest and `xl_esm_zero` is weakest.
- Do not claim validated cryptic-pocket prediction, druggability, docking readiness, apo-to-holo opening, or AOH1996 mechanism from this benchmark.
