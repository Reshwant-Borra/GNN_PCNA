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

## Analysis Phase

Required metrics:

- RMSD.
- RMSF.
- Pocket volume over time.
- Opening frequency.
- Contact persistence.
- DCCM.
- Distance distributions.
- Windowed uncertainty.

## Interpretation Categories

- Supports claim.
- Partially supports claim.
- Inconclusive.
- Weakens claim.
- Contradicts claim.

## Critical Distinction

Stable RMSD supports simulation stability. It does not by itself validate cryptic pocket opening.
