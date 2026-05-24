# Stale Artifact Policy

## Purpose

An artifact is not safe because it exists. It must be current relative to its inputs, code, environment, and claims.

## Status Values

- `current`: Valid for associated claim and dependencies.
- `stale`: Upstream dependency changed; regenerate before reuse.
- `invalid`: Produced by wrong code, wrong data, leakage, or incorrect assumptions.
- `superseded`: Replaced by a newer artifact.
- `draft`: Exploration only.
- `archived`: Preserved for history.

## Stale Triggers

Mark downstream artifacts stale when any dependency changes:

- Raw data.
- Processed data.
- Split.
- Label definition.
- Preprocessing code.
- Feature definition.
- Model architecture.
- Training code.
- Checkpoint.
- Metric code.
- MD trajectory/topology.
- MD analysis code.
- Figure script.
- Claim wording.
- Known bug affecting output.

## Invalid Triggers

Mark invalid when:

- Produced with leakage.
- Wrong checkpoint.
- Wrong labels.
- Wrong chain/residue mapping.
- Broken metric script.
- Silent skipped inputs.
- Contradicted by audit.
- Missing provenance for a major claim.

## Stale Propagation Example

```text
graph_construction.py changed
  -> graph files stale
  -> checkpoints trained on old graphs stale
  -> metrics from old checkpoints stale
  -> figures from old metrics stale
  -> paper tables using those metrics stale
```

## Paper-Grade Rule

An artifact can support paper text only if:

- Status is `current`.
- Provenance is complete.
- Relevant gates pass.
- It links to a claim.
- No unresolved critical findings affect it.
