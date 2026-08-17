# Provenance gaps and ghost paths

Date: 2026-08-16 · Branch: `presmoke-repair-20260816`

This file records what is **not** retrievable from a clean clone. Nothing here was fabricated
or substituted. Where an artifact is missing, it is named as missing.

---

## 1. Reproducibility: two different claims, only one of which is closed

These are frequently conflated. They are not the same claim.

### FROZEN_HANDOFF_REPRODUCIBILITY — **CLOSED**

The three final checkpoints and the candidate handoff reproduce from tracked artifacts:

| Seed | SHA-256 |
|---|---|
| 42 | `03d01eba42eb7f6da01c0147dea434b1e1797bd2302e8a178d6bbd9b19526ce5` |
| 43 | `7f145d6f54d03744f71c0224df4f170ad4aab388387e242234ebffda1acae17b` |
| 44 | `0a739dec47248651499942207b82139e5dea8bebfafe5ed50aabcbbdfd6aa3f6` |

Consensus: mean literal Jaccard `0.6791537667698658`; 3/3 core = A25 A26 A38 A39 A40 A41 A42
A44 A45 A46 A47; ≥2/3 support adds A27 A43 A232 A233 A234; 1/3 fringe = A231 A250 A251 A252;
union = 20 residues.

**This is what MD consumes**, and it is sufficient for the MD arm to proceed. Enforced by
`tests/test_august_gnn_provenance_regression.py` and
`tests/test_frozen_provenance_bindings.py`.

### FULL_RETRAINING_REPRODUCIBILITY — **NOT CLOSED**

`checkpoints/pcna/best_pcna_v3.ckpt` is the 520-dimensional pretrain checkpoint that all three
seeds were fine-tuned from. It is:

* referenced as an absolute developer path
  (`/Users/rishiborra/Desktop/GNN_PCNA/checkpoints/pcna/best_pcna_v3.ckpt`) in
  `artifacts/go_prep/seed_4{2,3,4}/best_meta.json` and
  `artifacts/provenance/AUGUST_THREE_SEED_CHECKPOINT_REGISTRY.json`;
* **not tracked** (`checkpoints/` is git-ignored, `*.ckpt` is git-ignored);
* **not present** in this working tree;
* recorded in `RECONCILIATION_INVENTORY.md` as "ignored local-only".

Consequence: **you cannot retrain the three seeds end-to-end from a clean clone.** The
pretraining stage cannot be reproduced, because its input checkpoint is unavailable and no
digest for it was ever recorded.

**Do not claim end-to-end training reproducibility anywhere.** No checkpoint was invented to
close this gap. To close it properly, someone must locate the original
`best_pcna_v3.ckpt`, record its SHA-256, and publish it (or the recipe that regenerates it
bit-for-bit) as a tracked, retrievable artifact.

---

## 2. Ghost paths in active code and documentation

| Path | Referenced by | Status | Action taken |
|---|---|---|---|
| `data/splits/cryptosite_split.json` | `scripts/compute_validation_metrics.py:20`, `scripts/homology_check.py:17`, `scripts/run_test_eval.py:149` | **ABSENT** | Marked historical below. Not on the MD path. |
| `scripts/run_nma.py` | `SETUP.md` Step 9 | **ABSENT** — the script does not exist | `SETUP.md` Step 9 marked HISTORICAL / NOT REPRODUCIBLE |
| `checkpoints/pcna/best_pcna_v3.ckpt` | `artifacts/go_prep/*/best_meta.json`, `artifacts/provenance/AUGUST_THREE_SEED_CHECKPOINT_REGISTRY.json`, `VERIFICATION_REPORT.md` | **ABSENT** | See §1. Left recorded as-is; the registries are historical evidence and must not be rewritten. |
| `data/md/1W60_production.dcd` | `paper_engine/figures/md.py`, `paper/manuscript.md` | **ABSENT** | See `paper/LINEAGE_AUDIT.md`; classified UNVERIFIED. |
| `checkpoints/pcna_reproduced/best.ckpt` | `SETUP.md` Step 8 (Streamlit UI default) | **ABSENT** until the user retrains | Documented as a runtime output, not a tracked artifact. |

### Scripts that consume the absent split

`scripts/compute_validation_metrics.py`, `scripts/homology_check.py` and
`scripts/run_test_eval.py` are **Phase-2/Phase-3 historical analysis scripts**. They are not
part of the MD execution or analysis path and are not invoked by `md.sh`, `run_md.py`,
`analyze_md.py` or `md_workflow.py`. They will fail with a missing-file error if run. They are
retained as a record of what was done, not as runnable entry points.

No replacement split file was fabricated.

---

## 3. Machine-specific paths

* `paper/figures/figures_manifest.json` records absolute Windows paths of the form
  `C:\Users\advay\GNN_PNCA\...` for figure outputs and data sources. Non-portable; not a
  scientific defect. Recorded in `paper/LINEAGE_AUDIT.md`.
* `artifacts/go_prep/*/best_meta.json` and the checkpoint registry record absolute macOS paths
  under `/Users/rishiborra/`. These are historical provenance records and are deliberately
  left unmodified.

---

## 4. Line endings and hash stability

`.gitattributes` was added so that files whose SHA-256 is part of the scientific record are
checked out with LF on every platform. Without it, a Windows clone with `core.autocrlf=true`
would rewrite them and every recorded digest would appear to fail.

`artifacts/**`, `outputs/**` and `reports/**` are explicitly marked `-text` (byte-preserved):
some committed CSVs there already contain CRLF and their bytes are part of the completed
record, so normalising them now would alter frozen evidence.

All documented hashes were re-verified after adding `.gitattributes`. See
`tests/test_frozen_provenance_bindings.py`.
