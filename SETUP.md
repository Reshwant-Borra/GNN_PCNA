# GNN-PCNA — Setup Guide for Reviewers

Everything you need to reproduce results, run inference, or explore the model.

---

## Step 0 — Check your environment first

After cloning, run this before anything else:

```bash
python scripts/check_env.py
```

It checks every dependency and tells you exactly what to install if anything is missing. If it prints `[PASS] All checks passed`, skip to Step 4.

---

## Step 1 — Clone

```bash
git clone https://github.com/Reshwant-Borra/GNN_PCNA.git
cd GNN_PCNA
```

All PDB files, graph tensors, and trained checkpoints are **already in the repo**. No download step needed.

---

## Step 2 — Create a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

---

## Step 3 — Install dependencies

> **Do NOT run `pip install -r requirements.txt` directly.** `torch-scatter` and `torch-sparse` require a wheel URL matching your CUDA build. Use the install script instead.

```bash
# CPU-only (default — works on any machine)
bash install.sh

# NVIDIA GPU — CUDA 11.8
bash install.sh cu118

# NVIDIA GPU — CUDA 12.1
bash install.sh cu121

# Windows
install.bat        # CPU
install.bat cu118  # NVIDIA GPU
```

### Final check

```bash
python scripts/check_env.py
# Should show [PASS] for every line
```

---

## Step 4 — Run the AOH1996 positive-control check

This confirms the checkpoint retained its fine-tuning signal. Note: 8GLA was part of fine-tuning, so this is a **sanity check** (positive control), not independent validation. A PASS means the checkpoint is intact; novel predictions on other structures are hypotheses requiring experimental follow-up.

```bash
python scripts/aoh_gate_check.py
```

Expected output:
```
AOH1996 pocket mean score : 0.8676
Gate threshold            : 0.700
Verdict                   : PASS
```

---

## Step 5 — Run the held-out test evaluation

Evaluates the model on 5 proteins never seen during training or validation.

```bash
python scripts/run_test_eval.py
```

Results written to `data/results/test_split_eval.json`.

---

## Step 6 — Run the full test suite

```bash
python -m pytest -v
```

Expected: **16 passed**. All tests pass with PyG installed.

If you see `11 skipped` with a message about `torch_geometric not installed`, go back to Step 3b.

---

## Step 7 — Run per-structure analysis

```bash
python scripts/per_structure_analysis.py
```

Output: `results/per_structure/{PDB_ID}/` for each structure (~5–15 min on CPU).

---

## Step 8 — Launch the Streamlit UI

```bash
streamlit run src/ui/app.py
```

Opens at `http://localhost:8501`. The UI defaults to `checkpoints/pcna_reproduced/best.ckpt`.

---

## Step 9 — Reproduce the ANM flexibility analysis

```bash
python scripts/run_nma.py --pdb data/raw/1W60.pdb --cutoff 7.5 --n_modes 20
python scripts/run_nma.py --pdb data/raw/8GLA.pdb --cutoff 7.5 --n_modes 20
```

Expected: apo fold-change = 0.857, holo fold-change = 1.157.
Results written to `data/results/nma_1W60.json` and `data/results/nma_8GLA.json`.

---

## Checkpoints

| File | Model | Use |
|---|---|---|
| `checkpoints/pcna_reproduced/best.ckpt` | PocketGNNXL (~13.4M params) | **Recommended** — full provenance, seed=42, AOH gate PASS 0.8676 |
| `checkpoints/pcna/best_pcna_v3_fixed.ckpt` | PocketGNNXL (~13.4M params) | Superseded by `pcna_reproduced` |
| `checkpoints/pcna/best_pcna.ckpt` | PocketGNN small (~907k params) | Baseline comparison only |

---

## Key results already computed

These files are committed — no recomputation needed to verify numbers:

| File | Contents |
|---|---|
| `data/results/EVALUATION_REPORT.md` | Full per-structure AUROC table |
| `data/results/v3_summary.csv` | V3 per-structure scores |
| `data/results/nma_apo_holo_comparison.json` | ANM flexibility comparison |
| `data/splits/cryptosite_split.json` | Train/val/test split manifest |
| `data/manifests/pdb_checksums.json` | SHA256 checksums for all 149 PDB files |
| `VERIFICATION_REPORT.md` | Automated claim verification (52 VERIFIED, 0 WRONG) |

---

## Troubleshooting

| Error | Fix |
|---|---|
| `ModuleNotFoundError: torch_geometric` | Run Step 3b — PyG is a separate install from PyTorch |
| `ModuleNotFoundError: torch_scatter` | Re-run Step 3b with the correct CUDA tag (`+cpu`, `+cu118`, `+cu121`) |
| `11 tests skipped` in pytest | PyG not installed — run Step 3b |
| `UnicodeEncodeError: cp1252` | Prefix command with `PYTHONIOENCODING=utf-8` |
| `AUROC = 0.5` on a structure | Expected for apo structures — no ligand means no positive labels |
| Streamlit not found | `pip install streamlit` |

---

## What is NOT in this repo

- MD trajectories (not generated — no trajectory data available)
- ESM2 feature cache (generated on-the-fly at inference time)
- Raw crawled catalog beyond the committed `data/catalog/` files

---

*GNN-PCNA | Python 3.10–3.12 | PyTorch 2.1 | PyTorch Geometric 2.4+*
