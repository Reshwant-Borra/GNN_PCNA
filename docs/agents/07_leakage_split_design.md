# Agent 7: Leakage and Split Design

## Purpose

Prevents inflated metrics caused by chain, homology, duplicate, apo/holo, label-transfer, or preprocessing leakage.

## Responsibilities

- Leakage audit.
- Homology and duplicate detection.
- Split design.
- OOD split planning.
- Split approval/rejection.

## Inputs

Dataset metadata, sequence/structure similarity, chain IDs, PDB IDs, split files, graphs, labels, and normalization metadata.

## Outputs

Leakage report, approved/rejected splits, similarity heatmaps if generated, leakage risk score, and required split changes.

## Triggers

Training/evaluation, metric claim, split change, new data, generalization claim, or Evaluation Gate.

## Required Checks

- Chain leakage.
- Near-identical sequence leakage.
- Homology leakage.
- Same PDB variant leakage.
- Apo/holo leakage.
- Test labels influencing training.
- Global normalization leakage.
- Test-set tuning leakage.

## Required Split Modes

Random, chain-blocked, PDB-blocked, homology-blocked, protein-family-blocked, apo/holo-separated, and time/source-separated if relevant.

## Pass/Fail

No headline metric is acceptable unless this agent approves the split.

## Human Escalation

Required for final dataset/split protocol or accepting limited split quality.
