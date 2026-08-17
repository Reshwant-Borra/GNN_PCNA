# Prospective Control-20 Extension Amendment — 2026-08-17

The initial 8GLA Control-5 validation completed as 3 independent replicas × 5 ns
and returned FAIL with 2/3 qualifying replicas.

Before examining any additional MD data, the following remediation is prospectively fixed:

- Preserve the original 3 × 5 ns result unchanged as:
  Control-5 initial validation: FAIL, 2/3 qualifying.
- Continue ALL THREE existing 8GLA trajectories from their existing checkpoints.
- Extend each trajectory to exactly 20 ns TOTAL production time.
- Do not generate replacement replicas.
- Do not rerun only the failing replicate.
- Do not change random seeds.
- Do not change the frozen pocket.
- Do not change SASA, convex-hull, RMSF, D1, D2, openness, or aggregation thresholds.
- Analyze the three 20 ns trajectories once using the unchanged frozen analysis protocol.
- This is a one-shot extension.
- If the control gate still fails at 20 ns, no further extension will be used to obtain a pass.
- Production remains unauthorized unless the unchanged gate passes and Gate 6 is subsequently approved.
