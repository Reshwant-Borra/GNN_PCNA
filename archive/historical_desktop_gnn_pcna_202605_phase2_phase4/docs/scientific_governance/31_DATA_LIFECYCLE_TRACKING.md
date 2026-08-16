# Data Lifecycle Tracking

## Purpose

Track why data enters, changes, leaves, or is quarantined in Phase 2.

## Hard Rules

- Every structure, graph, label file, split entry, and benchmark item must have lifecycle status.
- Data removal must record a reason.
- Quarantined data may not be used for training, evaluation, or claims.
- Lifecycle decisions must be reproducible and reviewable.

## Lifecycle Statuses

- candidate
- accepted
- excluded
- quarantined
- deprecated
- superseded
- historical_reference_only

## Required Removal Reason Codes

- homolog_leakage
- apo_holo_leakage
- duplicate_system
- chain_ambiguity
- missing_residue_problem
- altloc_ambiguity
- label_uncertainty
- low_structure_quality
- nonbiological_ligand
- source_unavailable
- license_unclear
- provenance_missing
- pcna_final_holdout
- stale_artifact

## Forbidden Actions

- Removing data without a reason.
- Reintroducing excluded data without review.
- Using quarantined V1 artifacts as Phase 2 truth.
- Changing lifecycle status after seeing metrics without logging it.

## Required Checks

- Lifecycle log exists before graph generation.
- Every excluded item has reason code.
- Every accepted item has source and hash.
- Every status change has date, owner, and rationale.

## Examples Of Failure

- A PDB is removed because it hurts metrics but marked "quality issue" without evidence.
- A PCNA structure leaks into training because its holdout status was not tracked.
- A stale graph cache is reused because no lifecycle registry exists.

## Prevention

Use lifecycle status as an input to dataset loaders and split builders.

## Compliance Artifact

`data/registries/data_lifecycle_registry.json` and `reports/phase2/data_lifecycle_audit.md`.

## If The Rule Fails

Quarantine the affected dataset version and rerun dataset, split, label, and graph audits.
