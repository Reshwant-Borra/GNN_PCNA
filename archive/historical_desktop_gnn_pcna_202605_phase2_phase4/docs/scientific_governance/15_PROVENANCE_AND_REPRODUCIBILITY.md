# Provenance And Reproducibility

## Purpose

Make every Phase 2 artifact traceable and reproducible.

## Hard Rules

Every artifact must include:

- commit hash
- config hash
- dataset hash
- split hash
- seed
- command
- timestamp
- environment
- input file hashes
- output file hash

Artifacts include:

- splits
- graphs
- labels
- model checkpoints
- metrics
- figures
- MD trajectories
- MD analyses
- reports
- source indexes

## Reproducibility Manifest Template

```markdown
# Reproducibility Manifest

- Artifact ID:
- Artifact path:
- Created by:
- Created at:
- Commit hash:
- Config hash:
- Dataset hash:
- Split hash:
- Label hash:
- Graph hash:
- Seed:
- Command:
- Environment:
- Input files and hashes:
- Output file hash:
- Upstream manifests:
- Downstream reports:
- Known limitations:
```

## Forbidden Actions

- Using stale artifacts.
- Using unregistered caches.
- Manually editing generated files without notes.
- Renaming checkpoints without preserving manifest.
- Copying reports between runs without updating hashes.

## Required Checks

- Hash completeness.
- Command reproducibility.
- Environment capture.
- Seed capture.
- Cache registration.
- Manual-edit notes.

## Examples Of Failure

- `best.ckpt` exists but no one can identify the dataset, split, seed, or command.
- A graph file was regenerated after split changes but kept the same filename.
- An MD trajectory is analyzed without protonation, force-field, or input structure provenance.

## Prevention

Artifact writers must emit manifests by default. Reports must refuse to summarize artifacts without manifests.

## Compliance Artifact

`reports/phase2/provenance_audit.md`.

## If The Rule Fails

The artifact cannot support claims. Reproduce it from registered inputs or mark it `UNREPRODUCIBLE_DO_NOT_USE`.
