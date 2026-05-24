# Artifact Schema

## Artifact Entry

```json
{
  "artifact_id": "ART-0001",
  "path": "",
  "artifact_type": "raw_data|processed_data|split|graph|checkpoint|training_log|prediction|metric|md_trajectory|md_topology|md_analysis|figure|table|report|paper_draft|memory|other",
  "created_at": "",
  "updated_at": "",
  "created_by_agent": "",
  "git_commit": "",
  "git_dirty": false,
  "dataset_hash": "",
  "checkpoint_hash": "",
  "environment_hash": "",
  "machine": "",
  "command": "",
  "inputs": [],
  "outputs": [],
  "status": "current|stale|invalid|superseded|draft|archived",
  "status_reason": "",
  "associated_claims": [],
  "associated_experiments": [],
  "associated_figures": [],
  "associated_tables": [],
  "associated_reports": [],
  "dependencies": [],
  "downstream_artifacts": [],
  "notes": ""
}
```

## Must Track

- Raw PDBs.
- Processed PDBs.
- Graphs.
- Splits.
- Checkpoints.
- Training logs.
- Predictions.
- Metrics.
- Per-structure reports.
- MD trajectories.
- MD topologies.
- MD analysis outputs.
- Figures.
- Tables.
- Paper drafts.

## Paper-Grade Requirements

Artifact may support paper text only if:

- Status is `current`.
- Provenance fields are complete.
- Relevant gates passed.
- It links to a claim.
- No unresolved critical finding affects it.
