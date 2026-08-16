# Final MD Execution Instructions

This is the execution manual for the remaining PCNA GNN -> MD validation workflow.
It uses the repository's current launcher and gates. Do not substitute ad hoc
commands unless you are deliberately debugging a failed stage.

Frozen analysis protocol:

```text
md_validation_4070/FROZEN_MD_ANALYSIS_PROTOCOL.json
SHA-256: 587f27cf2e402fe50b264d98d3d60fbbdcc8f9095025b2a89d12c7aebd633e56
Previous pre-reconciliation SHA-256: 2497def9e4675538dd08051ae6e5a448a41fbd32a1d7dc59cfb528d74d64ce3c
```

Default pocket/config used by `md.sh`:

```text
final_consensus_1w60_20260815
```

Primary launcher:

```bash
./md.sh smoke
./md.sh status
./md.sh attach
./md.sh control5
./md.sh benchmark
./md.sh production
./md.sh analyze
```

`md.sh` starts MD stages inside tmux. If tmux is missing, it refuses to run MD
outside tmux.

# Phase 1 - RTX 4070 Setup

Run these on the RTX 4070 Linux machine, not on the Mac.

## 1. Enter The Repository

**COMMAND TO RUN**

```bash
cd /path/to/GNN_PCNA
```

**EXPECTED RESULT**

You are in the repository root and `md.sh` exists.

If this fails, use the actual path where the repository was copied or cloned.

## 2. Activate Or Create The MD Environment

**COMMAND TO RUN**

```bash
conda activate pcna-md-4070 || conda env create -f md_validation_4070/environment.yml && conda activate pcna-md-4070
```

**EXPECTED RESULT**

The active Python environment contains OpenMM, pdbfixer, gemmi, mdtraj, numpy,
pandas, scipy, and matplotlib.

If conda is unavailable, install Miniforge/Mambaforge first, then rerun the
command. Do not continue with the system Python unless it has the same packages.

## 3. Verify GPU, CUDA/OpenMM, tmux, Disk, And Launcher

**COMMAND TO RUN**

```bash
nvidia-smi
python - <<'PY'
import openmm as mm
platforms = [mm.Platform.getPlatform(i).getName() for i in range(mm.Platform.getNumPlatforms())]
print("OpenMM platforms:", platforms)
assert "CUDA" in platforms, "OpenMM CUDA platform is missing"
PY
command -v tmux
df -h .
test -x ./md.sh || chmod +x ./md.sh
```

**EXPECTED RESULT**

- `nvidia-smi` shows the RTX 4070 and NVIDIA driver.
- OpenMM platforms include `CUDA`.
- `command -v tmux` prints a tmux path.
- `df -h .` shows enough free disk for the next stage.
- `md.sh` is executable.

If CUDA is missing from OpenMM, fix the conda/OpenMM CUDA installation before
running MD. If tmux is missing, install it, for example:

```bash
sudo apt-get update && sudo apt-get install -y tmux
```

# Phase 2 - 0.1 ns Smoke Test

The smoke stage launches one 0.1 ns 8GLA control run, then runs the analyzer on
the available output. It uses CUDA, tmux, the frozen pocket/config, checkpointing,
trajectory writing, and analysis compatibility checks.

**COMMAND TO RUN**

```bash
./md.sh smoke
```

**EXPECTED RESULT**

The launcher prints:

- tmux session name: `pcna_smoke`
- persistent log path under `md_validation_4070/logs/`
- command file path under `md_validation_4070/logs/`
- detach instruction: `Ctrl-b` then `d`
- reattach instruction: `./md.sh attach pcna_smoke`

## tmux Persistence Procedure

1. Launch:

```bash
./md.sh smoke
```

2. If attached to tmux, detach with:

```text
Ctrl-b then d
```

3. Close the terminal or SSH connection.

4. Reconnect to the RTX 4070 machine and return to the repository:

```bash
cd /path/to/GNN_PCNA
conda activate pcna-md-4070
```

5. Check status:

```bash
./md.sh status
```

6. Reattach if needed:

```bash
./md.sh attach
```

Closing the terminal or SSH connection is safe after detaching from tmux.
Turning off/rebooting the machine is different; that requires checkpoint recovery.

# Phase 2 Pass/Fail - Smoke

Use the automated status summary first.

**COMMAND TO RUN**

```bash
./md.sh status
```

**EXPECTED PASS CONDITIONS**

- `smoke_0p1ns: PASS`
- `analysis_validation: PASS`
- `8GLA/rep01` shows `COMPLETE`
- `DONE.json` exists for `md_validation_4070/outputs/8GLA/rep01`
- no NaNs/nonfinite energies in the sanity gate
- trajectory is readable by `analyze_md.py`
- no PBC artifact flag
- no duplicate frame-count risk
- checkpoint/status/provenance files exist

Important files if troubleshooting is needed:

```text
md_validation_4070/outputs/8GLA/rep01/DONE.json
md_validation_4070/outputs/8GLA/rep01/STATUS.json
md_validation_4070/outputs/8GLA/rep01/PROVENANCE.json
md_validation_4070/outputs/8GLA/rep01/RESUME_AUDIT.json
md_validation_4070/outputs/analysis/summary.json
md_validation_4070/outputs/analysis/REPORT.md
```

If PASS, continue to Phase 3.

If FAIL, STOP. Do not run `control5` or production until the failure is understood.

# Phase 3 - Control-First Validation

This stage launches:

```text
3 independent x 5 ns 8GLA control simulations
```

The seeds are deterministic in `run_md.py`:

```text
rep01: 20260001
rep02: 20260002
rep03: 20260003
```

The stage runs `run_md.py --run control --replicates 3 --ns 5`, then
`analyze_md.py`, then writes `md_validation_4070/CONTROL_INTERPRETABILITY_REPORT.md`.

**COMMAND TO RUN**

```bash
./md.sh control5
```

**EXPECTED RESULT**

The launcher starts tmux session:

```text
pcna_control5
```

Check progress:

```bash
./md.sh status
```

Attach:

```bash
./md.sh attach
```

Detach:

```text
Ctrl-b then d
```

## Control Validation Pass/Fail

**COMMAND TO RUN**

```bash
./md.sh status
```

**EXPECTED PASS CONDITIONS**

- `control5_interpretability: PASS`
- `8GLA/rep01`, `8GLA/rep02`, and `8GLA/rep03` are `COMPLETE`
- each control replicate has at least 5 ns production
- `md_validation_4070/CONTROL_INTERPRETABILITY_REPORT.md` contains:

```text
CONTROL INTERPRETABLE: PASS
```

If control validation fails, STOP. Do not proceed to production merely because
the simulations technically completed.

# Phase 4 - Gate-6 Decision

Gate-6 is a human decision. The repository does not provide an approval command.
The current implementation expects approval to be recorded in:

```text
research_os_memory/HUMAN_DECISIONS.md
```

The production helper checks this file for `gate 6` or `gate-6` and `approved`,
and rejects obvious negative markers such as `not approved`, `not granted`, or
`required_before_md`.

Before recording approval, inspect at minimum:

```text
md_validation_4070/outputs/analysis/REPORT.md
md_validation_4070/outputs/analysis/summary.json
md_validation_4070/CONTROL_INTERPRETABILITY_REPORT.md
md_validation_4070/FROZEN_MD_ANALYSIS_PROTOCOL.json
md_validation_4070/FROZEN_MD_ANALYSIS_PROTOCOL.sha256
md_validation_4070/GATE6_PACKET_FINAL_PRE_MD_READINESS.md
md_validation_4070/MD_READINESS_REPORT.md
```

Gate-6 should require:

- smoke PASS
- analysis validation PASS
- control-first stage completed
- control analysis interpretable
- no unresolved trajectory/topology/PBC issue
- no unresolved major scientific setup issue
- frozen protocol hash:
  `587f27cf2e402fe50b264d98d3d60fbbdcc8f9095025b2a89d12c7aebd633e56`

To record approval, append a specific human decision entry to
`research_os_memory/HUMAN_DECISIONS.md`. Example format:

```markdown
## Gate-6 - PCNA MD production approval

- Date: YYYY-MM-DD
- Decision maker: <name>
- Request: Approve production PCNA MD after RTX 4070 smoke and control-first validation.
- Decision: approved
- Scope: 3 x 100 ns 8GLA control and 3 x 100 ns 1W60 apo/candidate using frozen protocol hash 587f27cf2e402fe50b264d98d3d60fbbdcc8f9095025b2a89d12c7aebd633e56.
- Evidence: md_validation_4070/outputs/analysis/REPORT.md; md_validation_4070/CONTROL_INTERPRETABILITY_REPORT.md.
- Rationale: <brief rationale>
- Follow-up: Run cloud benchmark, then production on NVIDIA GPU.
```

After recording Gate-6, commit the approval and relevant validation outputs so the
cloud worktree is clean. Production is intentionally blocked if the git worktree
is dirty.

# Phase 5 - Move To Cloud

Move the repository to a Linux cloud machine with NVIDIA GPU support. Do not run
production on the Mac.

Transfer at minimum:

- repository code
- `md.sh`
- `md_validation_4070/`
- `md_validation_4070/FROZEN_MD_ANALYSIS_PROTOCOL.json`
- `md_validation_4070/FROZEN_MD_ANALYSIS_PROTOCOL.sha256`
- `md_validation_4070/outputs/` from RTX validation
- `md_validation_4070/CONTROL_INTERPRETABILITY_REPORT.md`
- `research_os_memory/HUMAN_DECISIONS.md` with Gate-6 approval
- data files needed by structure prep, especially `data/raw_intake/pcna_structures/`
- git history/commit state needed by provenance and the production dirty-tree gate

Recommended transfer method:

```bash
rsync -a --info=progress2 /path/to/GNN_PCNA/ user@cloud-host:/path/to/GNN_PCNA/
```

Do not transfer unnecessary disposable test directories. Preserve validation
outputs and approval records.

On the cloud machine, production will still fail unless the worktree is clean.
Commit or otherwise synchronize the exact approved state before running
`./md.sh production`.

# Phase 6 - Cloud Setup

Run on the cloud NVIDIA Linux machine.

## 1. Enter The Repository And Activate Environment

**COMMAND TO RUN**

```bash
cd /path/to/GNN_PCNA
conda activate pcna-md-4070 || conda env create -f md_validation_4070/environment.yml && conda activate pcna-md-4070
```

## 2. Verify CUDA/OpenMM, tmux, Storage, And Project State

**COMMAND TO RUN**

```bash
nvidia-smi
python - <<'PY'
import openmm as mm
platforms = [mm.Platform.getPlatform(i).getName() for i in range(mm.Platform.getNumPlatforms())]
print("OpenMM platforms:", platforms)
assert "CUDA" in platforms, "OpenMM CUDA platform is missing"
PY
command -v tmux
df -h .
git status --short
./md.sh status
```

**EXPECTED RESULT**

- NVIDIA GPU and driver are visible.
- OpenMM includes `CUDA`.
- tmux is installed.
- disk space is adequate.
- `git status --short` is empty before production.
- `./md.sh status` shows validation gates from the transferred RTX results.

Scientific parameters must remain identical between RTX 4070 and cloud. Hardware
differences may be recorded in provenance, and CUDA device choice is scientifically
neutral.

# Phase 7 - Cloud Benchmark

The benchmark is for performance planning only. It is not a scientific result.

**COMMAND TO RUN**

```bash
./md.sh benchmark
```

This starts tmux session:

```text
pcna_benchmark
```

It runs a short 8GLA control benchmark in:

```text
md_validation_4070/benchmark_outputs
```

It reports:

- measured ns/day
- estimated hours per 100 ns replicate
- estimated wall time for six 100 ns replicates sequentially
- estimated wall time for six replicates on 3 GPUs
- estimated wall time for six replicates on 6 GPUs

Do not change scientific parameters just to improve benchmark speed.

# Phase 8 - Production MD

Production is:

```text
3 x 100 ns 8GLA control
3 x 100 ns 1W60 apo/candidate
6 independent 100 ns trajectories = 600 ns aggregate MD
```

**COMMAND TO RUN**

```bash
./md.sh production
```

The command first runs the fail-closed production gate. It refuses to start unless
required conditions pass. If Gate-6 is missing, it prints:

```text
PRODUCTION BLOCKED: Gate-6 human approval required.
```

Before production, verify:

- CUDA GPU is available
- tmux is installed
- Gate-6 is recorded
- frozen protocol and hash exist
- RTX validation results were transferred
- smoke and control-first gates pass
- structure-prep gate passes
- storage preflight passes
- checkpoint/restart system is in place
- provenance will record a clean git state

Production starts tmux session:

```text
pcna_production
```

The current launcher runs the six trajectories sequentially in this session.

# Cloud Parallelization

Recommended scientific model: independent single-GPU trajectories. Do not try to
split one trajectory across multiple GPUs.

Current implementation support:

- `./md.sh production` supports the safe 1-GPU sequential workflow.
- The current `md.sh` does not expose a safe `run replicate N only` command.
- `run_md.py` has deterministic replicate numbering but no launcher-supported
  start-replicate option.
- Therefore, safe 3-GPU or 6-GPU production parallelization is not directly
  supported by the current launcher without a small code change.

## 1 GPU

Use the supported command:

```bash
./md.sh production
```

This runs all six 100 ns trajectories sequentially.

## 3 GPUs

Not directly supported by the current launcher. The scientifically appropriate
plan would be three independent single-GPU jobs followed by the next three, but
the current launcher does not provide commands to isolate replicate numbers safely.

## 6 GPUs

Not directly supported by the current launcher. The scientifically appropriate
plan would be six independent single-GPU jobs, but the current launcher does not
provide commands to isolate all six replicates safely.

# tmux During Production

Use `md.sh` for normal tmux operations.

List sessions and stage status:

```bash
./md.sh status
```

Attach to the latest PCNA session:

```bash
./md.sh attach
```

Attach to a named session:

```bash
./md.sh attach pcna_production
```

Detach:

```text
Ctrl-b then d
```

Session names:

```text
pcna_smoke
pcna_control5
pcna_benchmark
pcna_production
pcna_analyze
```

tmux protects against terminal or SSH disconnection. It does not protect against
cloud instance destruction. Checkpoints protect restart only if the disk containing
the checkpoint files survives.

# If A Run Stops

Use the normal launcher/resume path. Do not manually edit DCD files or checkpoint
files.

## 1. Check Status

```bash
./md.sh status
```

Status meanings:

- `RUNNING`: process appears active.
- `RESUMABLE`: checkpoint exists and the process is not running.
- `FAILED`: a `FAILED.json` exists; inspect the reason before retrying.
- `COMPLETE`: `DONE.json` exists and passed target-aware validation.
- `NOT_STARTED`: no run artifacts exist for that replicate.

## 2. Confirm Checkpoint Artifacts

For the affected replicate, check for:

```text
state.chk
state.prev.chk
checkpoint_meta.json
STATUS.json
RESUME_AUDIT.json
PROVENANCE.json
```

## 3. Resume Through The Normal Stage Command

Use the same high-level command for the interrupted stage:

```bash
./md.sh smoke
```

or:

```bash
./md.sh control5
```

or:

```bash
./md.sh production
```

The runner detects `state.chk`, validates frame/checkpoint consistency, appends
outputs safely, and records the resume event in `RESUME_AUDIT.json`.

If status is `FAILED`, inspect `FAILED.json`. Do not delete checkpoints or
trajectories unless you have decided to discard that replicate and rerun it from
scratch.

# Phase 9 - Final Analysis

After production completes:

**COMMAND TO RUN**

```bash
./md.sh analyze
```

This starts tmux session:

```text
pcna_analyze
```

The analyzer requires valid `DONE.json` by default and skips incomplete
replicates. It writes:

```text
md_validation_4070/outputs/analysis/REPORT.md
md_validation_4070/outputs/analysis/summary.json
md_validation_4070/outputs/analysis/per_replicate.csv
md_validation_4070/outputs/analysis/pocket_parity.json
```

Frozen metrics include:

- RMSD
- RMSF
- SASA
- DCCM summaries
- CA convex-hull geometric descriptor
- open-like fraction/event summaries
- PBC and duplicate-frame checks
- core/support/fringe region groupings

The final scientific analysis must distinguish:

- 3/3 GNN core
- 2/3 supported region
- 1/3 uncertain fringe

The primary conclusion should center on the 3/3 core. Do not change metrics after
examining candidate production trajectories.

# Interpreting The Result

## Supported

Multiple independent candidate replicates show consistent predefined
pocket-like/accessibility/geometry behavior and the validated control/analysis
pipeline behaves appropriately.

## Partially Supported

Some predefined metrics or replicates support the hypothesis, but evidence is
incomplete or heterogeneous.

## Weakened

The validated pipeline works, adequate sampling was obtained, but the predicted
region does not reproducibly show the expected behavior.

## Inconclusive

Sampling, control behavior, variability, or technical issues prevent a defensible
conclusion.

Never force a positive interpretation. Do not claim ligand binding, druggability,
or proof of a cryptic pocket from these simulations alone.

# Important Execution Warnings

> Do not run production on the Mac.
>
> Do not run production before Gate-6.
>
> Do not modify the frozen analysis after examining candidate production results.
>
> Do not delete checkpoints while a run is incomplete.
>
> Do not delete the cloud instance before copying final trajectories/results to
> persistent storage.
>
> Do not assume tmux protects against instance termination.
>
> Do not mix outputs from different protocol hashes.
>
> Do not overwrite completed replicates.
>
> Preserve raw trajectories, logs, hashes, provenance, and final analysis outputs.

# Quick Start - Commands Only

## RTX 4070

```bash
cd /path/to/GNN_PCNA
conda activate pcna-md-4070 || conda env create -f md_validation_4070/environment.yml && conda activate pcna-md-4070
nvidia-smi && command -v tmux && df -h .
test -x ./md.sh || chmod +x ./md.sh
```

```bash
./md.sh smoke
```

```bash
./md.sh status
```

Only after smoke PASS:

```bash
./md.sh control5
```

```bash
./md.sh status
```

Gate-6: inspect the smoke/control/analysis reports, then append a real human
approval entry to:

```text
research_os_memory/HUMAN_DECISIONS.md
```

Commit/synchronize the approved clean state before cloud production.

## Cloud

```bash
cd /path/to/GNN_PCNA
conda activate pcna-md-4070 || conda env create -f md_validation_4070/environment.yml && conda activate pcna-md-4070
nvidia-smi && command -v tmux && df -h . && git status --short
```

```bash
./md.sh benchmark
```

Only after all gates, including Gate-6:

```bash
./md.sh production
```

```bash
./md.sh status
```

```bash
./md.sh analyze
```
