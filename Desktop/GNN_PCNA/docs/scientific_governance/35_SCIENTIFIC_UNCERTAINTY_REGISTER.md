# Scientific Uncertainty Register

## Purpose

Make uncertainty a first-class project artifact. Phase 2 optimizes for well-characterized uncertainty, not false confidence.

## Hard Rules

- Every major result must state uncertainty.
- Unknowns, weak evidence, contradictory evidence, and assumptions must be registered.
- High-impact uncertainty blocks strong claims.
- Reducing uncertainty requires evidence, not confidence language.

## Register Template

| ID | Uncertainty | Category | Evidence status | Impact | Current handling | Owner | Review date |
|---|---|---|---|---|---|---|---|
| UNC-001 |  | dataset/label/split/model/PCNA/MD/claim | missing/weak/conflicting/strong | low/medium/high/blocking |  |  |  |

## Required Checks

- Dataset uncertainty.
- Benchmark uncertainty.
- Label uncertainty.
- Split leakage uncertainty.
- PCNA mapping uncertainty.
- Model shortcut uncertainty.
- Baseline uncertainty.
- MD setup and interpretation uncertainty.
- Claim uncertainty.

## Forbidden Actions

- Replacing uncertainty with confident wording.
- Hiding uncertainty in appendices while making strong claims.
- Treating unknown as negative or positive by convenience.
- Marking uncertainty resolved without evidence.

## Examples Of Failure

- "The site is allosteric" when mechanism is unknown.
- "MD validates opening" when one trajectory is exploratory.
- "CryptoBench proves generalization" when benchmark bias is unresolved.

## Prevention

Require every report to include an uncertainty section and every claim to cite relevant uncertainty IDs.

## Compliance Artifact

`reports/phase2/scientific_uncertainty_register.md`.

## If The Rule Fails

Downgrade claims to exploratory language and add missing uncertainties before proceeding.
