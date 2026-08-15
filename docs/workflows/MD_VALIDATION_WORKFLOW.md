# MD Validation Workflow

## Purpose

Plan, audit, and interpret molecular dynamics validation without overclaiming.

## Agents

- Context.
- Compute Planning.
- Validation.
- Biological Realism.
- Metrics.
- Provenance.
- Contradiction.
- Claim.
- Figure if plots involved.

## Planning Phase

Before MD:

- Define validation question.
- Define exact claim tested.
- Define expected signal.
- Define failure criteria.
- Estimate timescale, runtime, cost, and storage.
- Define trajectory, topology, force field, solvent, temperature, pressure, and equilibration.
- Define analysis outputs.
- Request human approval for expensive compute.

## Current Execution Phase Order

`GNN frozen -> structure/preparation validation -> MD parameter validation -> frozen analysis -> 0.1 ns smoke -> analysis validation -> 3 x 5 ns control-first validation -> human Gate-6 -> benchmark on chosen production GPU -> production MD -> frozen final analysis`.

Use `./md.sh` from the repository root. Do not run ad hoc production commands.

## Analysis Phase

Current frozen metrics implemented in `md_validation_4070/analyze_md.py`:

- RMSD as a global stability/PBC-artifact check.
- RMSF as a local flexibility measure.
- SASA as a local accessibility measure.
- DCCM summaries as correlated-motion measures.
- Region-level geometry/openness using supported-region SASA and CA convex-hull thresholds.
- Core/support/fringe summaries.

High RMSF alone is not evidence of a cryptic pocket. CA convex-hull volume is a geometric descriptor, not a ligand-volume estimate. No current frozen MDpocket/fpocket cavity-volume metric is implemented.

## Interpretation Categories

- Supports claim.
- Partially supports claim.
- Inconclusive.
- Weakens claim.
- Contradicts claim.

## Critical Distinction

Stable RMSD supports simulation stability. It does not by itself validate cryptic pocket opening.
