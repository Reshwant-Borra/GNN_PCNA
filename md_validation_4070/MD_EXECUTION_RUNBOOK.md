# MD Execution Runbook

This repository is now tmux-first for MD execution. Use `../md.sh` from the
repository root.

## Checkpoint and Output Cadence

- Trajectory/log output remains the frozen 50 ps cadence.
- Checkpoints are written every 10 ps by default.
- The 10 ps checkpoint cadence is operational only: it reduces lost wall time after
  interruption without changing scientific sampling, force-field parameters, or the
  frozen analysis protocol.
- 10-25 ps DCD output was considered for transient pocket behavior, but the frozen
  protocol is framed around ns-scale accessibility/openness events with a minimum
  duration of two saved frames. Changing production output from 50 ps before any
  evidence of inadequacy would increase storage 2-5x without a predeclared need.

## Restart Files Per Replicate

- `state.chk`: latest atomic OpenMM checkpoint.
- `state.prev.chk`: previous checkpoint fallback if `state.chk` is unreadable.
- `checkpoint_meta.json`: checkpoint write count and recent checkpoint timestamps.
- `STATUS.json`: current state such as `RUNNING`, `RESUMABLE`, `FAILED`, or
  `COMPLETE`.
- `RESUME_AUDIT.json`: checkpoint selected, previous/resumed step and time, DCD
  frame count at resume, and resume event count.
- `PROVENANCE.json`: hardware, software, git state, scientific parameters, input
  hashes, random seed, timestamps, and final simulation time.
- `DONE.json`: written only after target steps complete and the sanity gate passes.

## Launcher Commands

```bash
./md.sh smoke
./md.sh status
./md.sh attach
./md.sh control5
./md.sh benchmark
./md.sh production
./md.sh analyze
```

`production` fails closed until all readiness gates pass, including recorded
Gate-6 human approval. tmux protects terminal/SSH disconnects; it does not
protect against machine reboot or cloud instance destruction. Checkpoint/restart
works only when the storage containing `state.chk`, `state.prev.chk`, trajectory,
log, and JSON state files survives.
