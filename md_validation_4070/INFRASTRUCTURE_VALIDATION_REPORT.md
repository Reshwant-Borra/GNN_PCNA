# MD Infrastructure Validation Report

Generated: 2026-08-15

## Scope

Disposable infrastructure-only OpenMM runs were performed on this Mac with the
OpenCL platform because tmux and CUDA are not installed locally. These were not
scientific MD results and were not production runs.

## tmux Persistence

Not executable on this Mac: `tmux` is not installed. The new launcher was tested
for fail-closed behavior and prints an installation message instead of running MD
outside tmux.

## Controlled Interruption And Resume

Test command target: 8GLA control, 1 replicate, 100 integration steps, 4 fs
timestep, 1-step DCD/log output, 1-step checkpoint interval, disposable output
directory.

- Initial disposable completion: 5 steps, valid checkpoint/DCD/DONE.
- Extension to 20 steps: resumed from step 5 and completed.
- Controlled interruption target: 100 steps.
- SIGTERM sent during the run.
- Runner caught the signal and wrote `STATUS=RESUMABLE`.
- Checkpoint at interruption: step 44.
- Restart discovered `state.chk` and resumed from step 44.
- Final `DONE.json`: 100/100 target steps, `resumed=true`.
- Final DCD frame count: 100.
- Final log time rows: 100.
- Duplicate log times: false.
- Duplicate frame-count risk: false.
- Resume audit events recorded: 3 total resume events across the staged
  disposable extension/interruption test.

## Analysis Compatibility

`analyze_md.py` read the resumed DCD with the matching `system_solvated.pdb`.

- Topology mismatch: not observed.
- Trajectory corruption: not observed.
- Atom-count mismatch: not observed.
- PBC artifact flag: false.
- Duplicate-frame artifact flag: false.
- Frozen region metrics emitted: core/support/fringe RMSF, SASA, DCCM summaries,
  CA convex-hull volume, and open-like fraction.

## Production Campaign

No 100 ns production campaign was launched.
