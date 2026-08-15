# PCNA MD RTX 4070 Run Package

Status: CURRENT LAUNCHER-FIRST INSTRUCTIONS.

This file supersedes the older `run_in_tmux.sh` and direct `python run_md.py`
instructions. Use the repository root launcher only.

## Setup

Run on the RTX 4070 Linux machine:

```bash
cd /path/to/GNN_PCNA
conda activate pcna-md-4070 || conda env create -f md_validation_4070/environment.yml && conda activate pcna-md-4070
nvidia-smi
command -v tmux
test -x ./md.sh || chmod +x ./md.sh
```

OpenMM must expose the CUDA platform. If tmux is missing, `md.sh` refuses to run
MD outside tmux.

## Current Next Command

```bash
./md.sh smoke
```

This launches a 0.1 ns 8GLA control smoke test in tmux and then runs the frozen
analyzer on the available output.

## Useful Commands

```bash
./md.sh status
./md.sh attach
./md.sh control5
./md.sh benchmark
./md.sh production
./md.sh analyze
```

Do not run `control5` until smoke passes. Do not run production until smoke,
analysis validation, 3 x 5 ns control-first validation, and real human Gate-6
approval are complete.

## Current Scientific Scope

The GNN identifies where on PCNA to investigate. MD tests whether that frozen
predicted region reproducibly exhibits predefined accessibility, geometry,
flexibility, correlated-motion, or cavity-like dynamics under the simulated
conditions.

MD does not prove ligand binding, druggability, therapeutic relevance, or
experimental existence of a cryptic pocket.

## Resume Behavior

Closing SSH or a terminal is safe after detaching from tmux. tmux does not
protect against machine reboot or cloud instance destruction. Checkpoint/restart
works only if the disk survives.

Per-replicate restart files include `state.chk`, `state.prev.chk`,
`checkpoint_meta.json`, `STATUS.json`, `RESUME_AUDIT.json`, `PROVENANCE.json`,
and `DONE.json`.

Primary runbook: `md_validation_4070/FINAL_MD_EXECUTION_INSTRUCTIONS.md`.
