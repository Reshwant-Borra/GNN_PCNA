# GNN-PCNA — Setup Guide for Reviewers

Everything you need to reproduce results, run inference, or explore the model.

Current project status and MD instructions are not maintained in this setup file.
Use `PROJECT_STATUS.md` for source-of-truth state and
`md_validation_4070/FINAL_MD_EXECUTION_INSTRUCTIONS.md` for MD execution.

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

Current lightweight structure files are in the repo. Large generated graph,
embedding, checkpoint, and trajectory artifacts may be generated/rebuildable or
managed outside git; check `PROJECT_STATUS.md` and the relevant artifact
registries before assuming every large artifact is committed.

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

There is no supported `install.sh` or root `requirements.txt` in the current
repository. Use the dependency set that matches the task you are validating.

For lightweight repository checks:

```bash
python -m pip install -U pip
python -m pip install -e ".[test]"
python -m pip install numpy scipy biopython scikit-learn pandas matplotlib requests beautifulsoup4
```

For GNN inference or graph validation, install PyTorch and PyTorch Geometric
with wheels matching your CPU/CUDA runtime. Example CPU install:

```bash
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install torch-geometric torch-scatter torch-sparse \
  -f https://data.pyg.org/whl/torch-2.1.0+cpu.html
```

For MD validation:

```bash
conda env create -f md_validation_4070/environment.yml
conda activate pcna-md-4070
```

### Final check

```bash
python3 scripts/check_env.py
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

## Step 6 — Run the full feasible lightweight test suite

```bash
python3 -m pytest -v
```

Some ML tests are skipped when PyTorch Geometric is not installed. MD production
is never part of the lightweight test suite.

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

## Step 9 — ANM flexibility analysis — **HISTORICAL / NOT REPRODUCIBLE**

> **`scripts/run_nma.py` does not exist in this repository.** The commands below are retained
> as a record of what was run historically; they cannot be executed from a clean clone. The
> reported values (apo fold-change 0.857, holo fold-change 1.157) are therefore
> **UNVERIFIED** here. No replacement script was fabricated. See `PROVENANCE_GAPS.md`.

```bash
# HISTORICAL ONLY — scripts/run_nma.py is absent; these will fail.
# python scripts/run_nma.py --pdb data/raw/1W60.pdb --cutoff 7.5 --n_modes 20
# python scripts/run_nma.py --pdb data/raw/8GLA.pdb --cutoff 7.5 --n_modes 20
```

This step is not on the MD execution or analysis path and does not gate anything.

---

## Checkpoints

| File | Model | Use |
|---|---|---|
| `checkpoints/pcna_reproduced/best.ckpt` | PocketGNNXL (~13.4M params) | **Recommended** — full provenance, seed=42, AOH gate PASS 0.8676 |
| `checkpoints/pcna/best_pcna_v3_fixed.ckpt` | PocketGNNXL (~13.4M params) | Superseded by `pcna_reproduced` |
| `checkpoints/pcna/best_pcna.ckpt` | PocketGNN small (~907k params) | Baseline comparison only |

---

## 520-dim graph lineage

The full 55-structure `data/graphs_xl` tensor package is treated as an
external generated artifact. A clean clone can retrieve and verify it from the
recorded remote branch:

```bash
python3 scripts/verify_graph_lineage.py --retrieve-from-origin
```

The verifier checks 55 structures, 520-dimensional node features, train/val/test
identity, label counts, and the aggregate graph manifest hash recorded in
`artifacts/provenance/GRAPH_LINEAGE_520_MANIFEST.json`.

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
