# MD Replicate And Duration Plan

## Staging

1. Technical smoke: 1 8GLA control replicate, 0.1 ns production, default equilibration, execution only, launched by `./md.sh smoke`.
2. Control-first validation: 3 independent 8GLA control replicates, 5 ns production each after the frozen equilibration protocol, launched by `./md.sh control5`. Purpose: stability, analysis interpretability, and metric responsiveness, not proof of biology.
3. Benchmark after Gate-6 on the chosen production GPU: short 8GLA benchmark, launched by `./md.sh benchmark`; performance only, not scientific evidence.
4. Production, only after all gates and explicit human Gate-6 approval: 3 independent 8GLA control replicates and 3 independent 1W60 candidate/apo replicates, 100 ns production each, launched by `./md.sh production`.

## Seeds

Replicate seeds are the existing run_md.py deterministic seeds: 20260001, 20260002, 20260003 for integrator and barostat.

## Why 100 ns For Production

The prior 20-25 ns single-run design was underpowered and uninterpretable. 100 ns x 3 remains exploratory for cryptic-pocket dynamics, which can be slower than this, but gives a reasonable near-term opportunity to detect ns-scale accessibility changes without adapting duration after observing favorable candidate behavior.

## Early Stop Conditions

Stop only for technical failure: NaNs, nonfinite energies, temperature runaway, box collapse, severe unfolding/RMSD gate failure, chain separation, corrupted trajectory, topology/trajectory mismatch, failed checkpoint/restart, invalid residue mapping, or failed analysis parity/PBC checks.

Scientific no-opening is not an early stop condition.
