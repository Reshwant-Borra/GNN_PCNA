# Biological Data Sanity Review

## Purpose

Require biological plausibility review before training. This prevents days of training on labels, structures, or graph features that are biologically nonsensical.

## Hard Rules

- This review is required before any first Phase 2 training run.
- The review must inspect data before model fitting, not only after prediction.
- Manual review is mandatory; agents and scripts may prepare evidence but cannot replace human biological review.
- If label distributions, pocket definitions, chain mapping, accessibility, or PCNA controls look biologically wrong, training must not start.

## Required Checks

- Manually inspect representative structures from each dataset tier.
- Inspect known PCNA interfaces, including PIP-box/APIM/IDCL regions.
- Inspect AOH1996/8GLA positive-control mapping and leakage status.
- Inspect label distributions per protein, per chain, and per structure class.
- Inspect pocket definitions and atom/distance criteria.
- Inspect residue accessibility for positives and high-risk negatives.
- Inspect missing residues, alternate conformations, biological assembly status, and chain identity.
- Inspect whether positives cluster at biologically plausible surfaces rather than parser artifacts.
- Compare curated cryptic-pocket labels against proxy ligand-proximity labels if both are used.

## Forbidden Actions

- Training before this review is completed.
- Treating all unannotated residues as biologically true negatives without review.
- Assuming a benchmark is biologically sane because it has a name or citation.
- Ignoring inaccessible or buried positives.
- Ignoring PCNA trimer biology until after prediction.

## Review Template

| Item | Evidence | PASS/WARNING/FAIL | Notes | Reviewer |
|---|---|---|---|---|
| Example structures inspected |  |  |  |  |
| PCNA interfaces inspected |  |  |  |  |
| AOH1996/8GLA mapping inspected |  |  |  |  |
| Label distributions inspected |  |  |  |  |
| Pocket definitions inspected |  |  |  |  |
| Residue accessibility inspected |  |  |  |  |
| Missing residues/AltLoc inspected |  |  |  |  |

## Examples Of Failure

- Most positives are buried and inaccessible but are treated as pocket residues.
- PCNA labels map to the wrong chain or non-PCNA partner chain.
- A dataset uses ligand contacts from biologically irrelevant crystallization additives.
- One protein family dominates positives and makes labels look easier than they are.

## Prevention

Perform this review immediately after dataset, split, and label draft creation and before graph generation or training.

## Compliance Artifact

`reports/phase2/biological_data_sanity_review.md`.

## If The Rule Fails

Do not train. Fix labels, filters, chain mapping, or dataset scope, then repeat the review.
