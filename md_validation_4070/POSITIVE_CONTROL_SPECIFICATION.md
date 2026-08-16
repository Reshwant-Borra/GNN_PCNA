# Positive Control Specification

## Definition

The positive-control/reference structure is 8GLA, a PCNA co-crystal with an AOH1996 derivative (ZQZ) bound. The MD preparation strips ligand and simulates protein-only PCNA from the ligand-bound/reference coordinates.

## What It Tests

The control tests whether the preparation plus frozen analysis can recognize a structural/accessibility distinction relevant to the candidate hypothesis. It does not require short ligand-stripped MD to spontaneously produce a dramatic opening event.

## Expected Behavior

At initialization/static reference, the frozen metrics should report larger accessibility or geometry in 8GLA than 1W60 for the predefined candidate region. In short MD, the control should remain technically stable and interpretable; relaxation after ligand stripping is allowed.

## Interpretable

Technically stable simulation, correct topology/trajectory pairing, valid PBC handling, atom-parity-safe analysis, and metrics that distinguish the static/reference state or produce structurally sensible trajectories.

## Technically Valid But Biologically Ambiguous

The run is stable and analyzable, but ligand stripping, 8GLA resolution/rebuilt loops, or disulfide/construct differences make the biological meaning uncertain.

## Failed

Preparation/mapping mismatch, severe instability, analysis parity failure, PBC artifacts, corrupted outputs, or metrics unable to distinguish reference states where they should.
