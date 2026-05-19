# Running the PCNA MD Simulation on a CUDA Machine

The pre-built system is already here — no structure prep needed. Just install, clone, and run.

## Requirements

- NVIDIA GPU with CUDA 11.x or 12.x
- Anaconda or Miniconda ([download](https://docs.conda.io/en/latest/miniconda.html))
- ~15 GB free disk space (trajectory will be ~8 GB)

## Setup (one time, ~10 minutes)

```bash
# 1. Clone the repo
git clone https://github.com/Reshwant-Borra/GNN_PCNA.git
cd GNN_PCNA

# 2. Create conda environment with CUDA-enabled OpenMM
#    (conda auto-detects your CUDA version and installs the right build)
conda create -n pcna_md python=3.11 -y
conda activate pcna_md
conda install -c conda-forge openmm mdanalysis scipy pandas -y

# 3. Verify CUDA was detected
python -c "
from openmm import Platform
platforms = [Platform.getPlatform(i).getName() for i in range(Platform.getNumPlatforms())]
print('Platforms:', platforms)
assert 'CUDA' in platforms, 'CUDA not found — check NVIDIA drivers'
print('CUDA OK')
"
```

## Run the simulation

```bash
# Full 100 ns run (~8 hours on RTX 3080, ~5 hours on RTX 4090)
python scripts/run_simulation_local.py

# Shorter test run (10 ns, ~50 min on RTX 3080)
python scripts/run_simulation_local.py --ns 10

# Expected output:
#   data/md/1W60_production.dcd   (~8 GB for 100 ns)
#   data/md/1W60_topology.pdb
#   data/md/production.log
#   data/results/md_run_metadata.json
```

## After the run — send results back

Only 2 files are needed for analysis (the topology is small, the DCD is large):

```bash
# Option A: copy over network
scp data/md/1W60_production.dcd  advay@<your-ip>:~/GNN_PNCA/data/md/
scp data/md/1W60_topology.pdb    advay@<your-ip>:~/GNN_PNCA/data/md/

# Option B: upload to Google Drive and share the folder

# Option C: if the friend keeps it, run analysis there too
python scripts/run_md_analysis.py
# Then send back only data/results/md_rmsf_1W60.json (10 KB) and md_dccm_1W60.npy (~1 MB)
```

## Expected timing by GPU

| GPU          | Speed (ns/day) | 100 ns wall time |
|---|---|---|
| RTX 4090     | ~80–120        | ~1 hour          |
| RTX 3080/4080| ~40–70         | ~2–3 hours       |
| RTX 3070     | ~25–40         | ~3–4 hours       |
| RTX 3060     | ~15–25         | ~5–8 hours       |
| GTX 1080 Ti  | ~10–15         | ~8–12 hours      |

## Checkpoint / resume

If the run is interrupted, resume from the last checkpoint:

```python
# Add to run_simulation_local.py before simulation.step(PROD_STEPS):
simulation.loadCheckpoint('data/md/production.chk')
```

Or just re-run — OpenMM overwrites the DCD from scratch. Keep `production.chk` safe.
