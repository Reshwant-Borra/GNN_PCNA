# Pre-MD Reality Check

## Purpose

Force MD to test a specific biological hypothesis instead of running simulations and retrofitting a story afterward.

## Hard Rules

- This check is required before any MD interpretation.
- The biological hypothesis must be specific and falsifiable.
- Expected, alternative, negative, unstable, and artifact explanations must be written before interpretation.
- MD is not allowed as "let's see what happens" evidence for claims.

## Required Checks

- What exact biological hypothesis is being tested?
- Which PCNA structure, chains, assembly, ligand state, and protonation policy are used?
- Which predicted site or interface is tested?
- What observation would support the hypothesis?
- What observation would weaken or contradict it?
- What observation would be inconclusive?
- What setup artifacts could mimic the expected result?
- What claim is allowed if MD is positive?
- What claim is allowed if MD is negative?

## Forbidden Actions

- Starting MD interpretation without a hypothesis.
- Calling any motion near the site "validation."
- Ignoring force-field, ligand-parameter, protonation, or equilibration artifacts.
- Changing the hypothesis after viewing trajectories without logging it.

## Examples Of Failure

- Running ligand-bound PCNA MD and later deciding the relevant metric is whichever changed most.
- Interpreting RMSF differences as mechanism without interface or pocket analysis.
- Treating ligand escape as failed MD instead of evidence under the registered setup.

## Prevention

Complete this check before [13_MD_VALIDATION_RULES.md](13_MD_VALIDATION_RULES.md) interpretation and [22_UNEXPECTED_RESULTS_POLICY.md](22_UNEXPECTED_RESULTS_POLICY.md).

## Compliance Artifact

`reports/phase2/md/<system_id>/pre_md_reality_check.md`.

## If The Rule Fails

MD may be archived as exploratory only. It cannot support claims.
