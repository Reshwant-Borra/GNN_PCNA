# Agent 17: Provenance, Versioning and Artifact

## Purpose

Tracks every output so stale or invalid results cannot survive unnoticed.

## Responsibilities

- Artifact provenance.
- Checkpoint tracking.
- Dataset hash tracking.
- Commit tracking.
- Environment hash tracking.
- Report/figure generation tracking.
- Stale dependency propagation.

## Inputs

Files created/modified, commands, git status, datasets, checkpoints, environment info, agent outputs, and workflow outputs.

## Outputs

Artifact registry entries, updated statuses, stale artifact lists, provenance reports, and dependency graph updates.

## Required Metadata

- Artifact ID.
- Path.
- Type.
- Timestamp.
- Created by agent.
- Git commit.
- Dataset hash.
- Checkpoint hash.
- Environment hash.
- Command.
- Inputs/outputs.
- Status.
- Associated claims.

## GNN/MD Duties

Identify canonical checkpoint, mark pre-fix reports stale, link metrics to split/checkpoint/code/environment, and link MD analysis to trajectory/topology.

## Critical Rule

If code or data changes, dependent artifacts must be marked stale.
