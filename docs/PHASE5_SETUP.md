# Phase 5 Setup — Install Everything to Run Post-MD Analysis

**Purpose:** stand up a working environment from a blank machine to run
`scripts/phase5_analyze_1axc_md.py` on RunPod-produced trajectories.

**Read first:** `PHASE5_HANDOFF.md` at the repo root.

---

## 1. System requirements

| Item | Minimum | Recommended |
|---|---|---|
| OS | Linux (Ubuntu 22.04+), macOS, or Windows 11 + WSL2 | Linux |
| Python | 3.11 (pinned in the env file) | 3.11 |
| RAM | 8 GB | 16 GB+ |
| Disk free | 20 GB (for MD trajectories + analysis outputs) | 50 GB+ |
| GPU | Not required for **analysis** (CPU is fine) | Only needed if re-running MD |

The analysis script (`scripts/phase5_analyze_1axc_md.py`) is CPU-only and reads the
`.dcd` trajectories produced on RunPod. You do not need a GPU just to do post-MD
analysis and paper writing.

---

## 2. Install Miniforge (recommended conda distribution)

Miniforge is the cleanest conda installer; it defaults to the `conda-forge` channel
that the project's env file uses.

### Linux / macOS
```bash
# Download installer
curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh
bash Miniforge3-$(uname)-$(uname -m).sh -b -p "$HOME/miniforge3"

# Activate
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda --version
```

### Windows (PowerShell)
Download the Windows installer from
`https://github.com/conda-forge/miniforge/releases/latest` (file
`Miniforge3-Windows-x86_64.exe`), run it, and then in a new PowerShell session:
```powershell
conda --version
```

If you already have **Anaconda** or **Miniconda**, that works too — just make sure
the `conda-forge` channel is available.

---

## 3. Clone the repo and check out the Phase 5 branch

```bash
git clone https://github.com/Reshwant-Borra/GNN_PCNA.git
cd GNN_PCNA
git fetch origin codex/phase5-runpod-md-package
git checkout codex/phase5-runpod-md-package

# Sanity check
git status                       # clean, up to date with remote
git log --oneline -5
```

---

## 4. Create the conda environment

The env file is committed at `envs/phase5_md_runpod.yml`:

```yaml
name: phase5-md
channels:
  - conda-forge
dependencies:
  - python=3.11
  - openmm=8.2.*
  - pdbfixer
  - mdtraj
  - mdanalysis
  - numpy
  - pandas
  - matplotlib
  - tqdm
  - pyyaml
  - pip
```

Install it:

```bash
conda env create -f envs/phase5_md_runpod.yml
conda activate phase5-md
```

If `conda env create` is slow, install `mamba` first and use it as a drop-in:
```bash
conda install -n base -c conda-forge mamba -y
mamba env create -f envs/phase5_md_runpod.yml
conda activate phase5-md
```

---

## 5. Verify the install

```bash
# Python + OpenMM
python -c "import openmm; print('openmm', openmm.__version__)"
python -c "import pdbfixer; print('pdbfixer OK')"

# Analysis-time imports
python -c "import mdtraj, numpy, pandas, matplotlib; print('analysis deps OK')"

# OpenMM self-test (skip GPU section if no GPU; CPU platform must pass)
python -m openmm.testInstallation
```

If anything errors, see Troubleshooting below.

---

## 6. Drop the RunPod outputs into place

The MD trajectories are NOT in git (they are gitignored — see `.gitignore`). They
come from RunPod separately.

Expected location after copy:

```
outputs/phase5_md/time_crunch_1axc_25ns/
├── MANIFEST.md
├── inputs/
│   ├── 1axc_pcna_apo_from_p21_prepared.pdb
│   └── 1axc_pcna_apo_from_p21_structure_audit.json
├── replicate_01/{trajectory.dcd, solvated_initial.pdb, state.csv, checkpoint.chk, final.pdb, progress.json, COMPLETE.json}
├── replicate_02/...
└── replicate_03/...
```

### Option A — Reshwant sent you a `.tgz` package
```bash
mkdir -p outputs/phase5_md
tar -xzf phase5_time_crunch_1axc_25ns_*_status0.tgz -C outputs/phase5_md
ls outputs/phase5_md/time_crunch_1axc_25ns/
```

### Option B — Pull from RunPod directly via `runpodctl` or `scp`
```bash
# Whatever method gives you the files into:
#   outputs/phase5_md/time_crunch_1axc_25ns/
# The directory structure above must match.
```

---

## 7. Run the post-MD analysis

```bash
conda activate phase5-md

python scripts/phase5_analyze_1axc_md.py \
  --run-root outputs/phase5_md/time_crunch_1axc_25ns \
  --windows 239-243 28-32 206-210 134-138 \
  --reference-window 118-122
```

Outputs are written to `outputs/phase5_md/time_crunch_1axc_25ns/analysis/`:
- `rmsd_timeseries.csv`, `rmsd_timeseries.png`
- `window_rmsf.csv`
- `window_summary.csv`
- `window_rmsf_summary.png`
- `analysis_summary.json`

Use those CSVs/PNGs as the basis for the per-window interpretation table described
in `PHASE5_HANDOFF.md`, Step 3.

---

## 8. Optional extras (only if you also want to re-run / extend MD)

These are NOT needed for analysis + paper writing. Skip unless you are extending the
campaign.

### GPU / CUDA
RunPod containers already ship CUDA. For local re-runs you would need:
- NVIDIA driver supporting CUDA 12.x.
- A CUDA-capable GPU with ≥ 24 GB VRAM (40+ recommended for PCNA trimer + solvent).

OpenMM via conda-forge bundles CUDA support. Verify with:
```bash
python -m openmm.testInstallation   # CUDA platform should appear
```

### MD tooling for re-runs
The same `phase5-md` env supports the prep + run scripts:
```bash
python scripts/phase5_prepare_1axc_openmm.py --dry-run
python scripts/phase5_run_1axc_openmm.py --help
python scripts/phase5_run_1axc_openmm.py --smoke-test --platform CPU
```

`--smoke-test` runs a tiny 0.01 ns workflow on CPU to validate the install end-to-end.

---

## 9. Optional — Phase 3 / Phase 4 deps (only if you need to regenerate model figures)

The analysis you actually need does NOT require these. But if you want to re-render a
training-loss curve or recompute a baseline plot from scratch, the rest of the project
uses (roughly):

```bash
# Separate env so it does not clash with phase5-md
conda create -n gnn-pcna python=3.11 -y
conda activate gnn-pcna
pip install torch torch-geometric numpy pandas scikit-learn matplotlib biopython
# For ESM features:
pip install fair-esm
```

This is not pinned because Phase 3/4 are frozen and you have all the report outputs
already. Avoid touching the model unless absolutely necessary; the test set is
one-shot-locked (`reports/phase3/.test_evaluation_lock`).

---

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| `conda env create` hangs on solving | Switch to `mamba` (Step 4). |
| `ImportError: openmm` after activate | You did not activate the env: `conda activate phase5-md`. |
| `python -m openmm.testInstallation` reports CUDA failure but CPU passes | Fine for analysis. Only matters if you re-run MD on GPU. |
| `Prepared input PDB not found` from analysis script | The RunPod outputs were not copied into `outputs/phase5_md/time_crunch_1axc_25ns/inputs/`. See Step 6. |
| `Solvated topology PDB not found for replicate_*` | Same — incomplete copy. Each replicate dir must contain `solvated_initial.pdb`. |
| `No protein/CA atoms found in trajectory.dcd` | The `.dcd` is corrupt or empty. Check `progress.json` and `COMPLETE.json` for that replicate. |
| Conda very slow on Windows | Use WSL2 + Ubuntu; it is dramatically faster. |
| Out of disk on analysis | Each 25 ns DCD can be hundreds of MB. Ensure ≥ 20 GB free under the repo. |
| `matplotlib` errors about display backend | The script saves PNGs to disk; no display needed. If it fails, set `MPLBACKEND=Agg`. |

---

## 11. What you should NOT install / touch

- Do **not** install or modify any package that requires re-running the test set —
  the test split is one-shot-locked at `reports/phase3/.test_evaluation_lock`.
- Do **not** install AlphaFold or any structure-prediction tool. Out of scope for the
  paper.
- Do **not** install fpocket / P2Rank / PocketMiner just to "fill in the limitation."
  Running them properly requires the full frozen-test pipeline and a governance
  decision (per `docs/scientific_governance/10_BASELINE_REQUIREMENTS.md`). For now,
  state the absence as a limitation in the paper.

---

## 12. Final check before you start analysis

```bash
conda activate phase5-md
python -c "import openmm, pdbfixer, mdtraj, numpy, pandas, matplotlib; print('OK')"
ls outputs/phase5_md/time_crunch_1axc_25ns/replicate_01/trajectory.dcd
ls outputs/phase5_md/time_crunch_1axc_25ns/inputs/1axc_pcna_apo_from_p21_prepared.pdb
```

All three commands succeed → you are ready. Go to `PHASE5_HANDOFF.md` and start at
"Post-MD critical-path checklist".
