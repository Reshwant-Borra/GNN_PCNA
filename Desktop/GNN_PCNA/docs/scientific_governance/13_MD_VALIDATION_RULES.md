# MD Validation Rules

## Purpose

Define molecular dynamics as hypothesis testing, not confirmation theater. The purpose of MD is to test the hypothesis, not confirm the desired story.

## Hard Rules

- MD is supportive evidence, not definitive proof.
- A single 100 ns trajectory is exploratory.
- Negative MD results are valid.
- Unexpected MD results must be reported honestly.
- Do not force interpretation to match the hypothesis.
- RMSD/RMSF alone do not prove pocket opening or binding.
- Pocket volume, DCCM, interface distances, ligand stability, and contact persistence may help but still require cautious interpretation.
- Replicates are preferred.
- Enhanced sampling may be needed for cryptic pockets.
- Apo and ligand-bound or docked systems must be compared carefully.
- Same protonation, chain, biological assembly, force field, and structure policy must be used unless differences are justified.

## Required Statement

We do not build expecting one MD result and then panic when MD gives unexpected results. MD can support, weaken, redirect, or falsify the working hypothesis. All outcomes are evidence.

## MD Pre-Registration Template

```markdown
# MD Pre-Registration

## System
- Structure:
- Chains:
- Ligand/docked molecule:
- Force field:
- Water/ions:
- Protonation policy:
- Duration and replicates:
- Random seeds:

## Hypothesis

## Expected observations

## Alternative outcomes

## Interpretation if pocket does not open

## Interpretation if pocket opens

## Interpretation if simulation is unstable

## Claim allowed if positive

## Claim allowed if negative

## Metrics
- RMSD:
- RMSF:
- Pocket volume:
- DCCM:
- Interface distances:
- Ligand stability/contact persistence:
```

## Forbidden Actions

- Calling MD "validation" without pre-registration.
- Treating no pocket opening as failed MD.
- Treating ligand stability in one docked trajectory as binding-site proof.
- Claiming therapeutic relevance from MD alone.
- Comparing apo and ligand-bound simulations with different setup policies.

## Required Checks

- Setup provenance audit.
- Equilibration and stability audit.
- Trajectory quality audit.
- Metric interpretation audit.
- Positive, negative, and unexpected outcome interpretation table.
- Claim audit under [14_CLAIM_POLICY.md](14_CLAIM_POLICY.md).

## Examples Of Failure

- Pocket volume increases briefly and the report says the site is validated.
- A docked ligand leaves the site and the team discards the trajectory as a failed run.
- RMSF decreases at an interface and is interpreted as proof of functional disruption.

## Prevention

Pre-register interpretation before simulation. Use [22_UNEXPECTED_RESULTS_POLICY.md](22_UNEXPECTED_RESULTS_POLICY.md) when outcomes differ from the expected story.

## Compliance Artifact

`reports/phase2/md/<system_id>/pre_registration.md`, `MANIFEST.md`, and `md_interpretation_audit.md`.

## If The Rule Fails

Do not use the trajectory for claims. It may be archived as exploratory only after provenance is preserved.
