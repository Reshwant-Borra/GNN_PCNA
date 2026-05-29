# Gate System

## Purpose

Gates prevent the project from advancing before assumptions are verified.

Status values:

- `not_started`
- `in_progress`
- `pass`
- `warning`
- `fail`
- `blocked`
- `stale`

## Gate 1: Research Design

Pass only if:

- Research question is clear.
- Hypothesis and null hypothesis exist.
- Success and failure criteria exist.
- Required controls and baselines are listed.
- Validation plan exists.
- Falsification criteria are explicit.

Human approval:

- Final research question.
- Major hypothesis change.

## Gate 2: Dataset

Pass only if:

- Dataset sources are documented.
- PDB IDs and chains are known.
- Label definition is explicit.
- Missing data is documented.
- Residue numbering rules are known.
- Dataset is biologically relevant.

Fail if labels, chains, or positives/negatives are ambiguous.

## Gate 3: Leakage

Pass only if:

- Chain leakage checked.
- PDB leakage checked.
- Duplicate leakage checked.
- Homology leakage checked.
- Apo/holo leakage checked.
- Feature normalization leakage checked.
- Split manifest recorded.

Critical rule:

- No headline metric can be accepted unless this gate passes.

## Gate 4: Preprocessing

Pass only if:

- Residue mapping verified.
- Chain mapping verified.
- Graph nodes match residues.
- Labels align with nodes.
- Coordinates are not mixed.
- Features are leakage-safe.
- Symmetry operations are correct.

Critical rule:

- If preprocessing fails, model metrics are invalid.

## Gate 5: Code

Pass only if:

- Code reviewed.
- Scientific assumptions checked.
- Critical tests do not skip.
- Missing dependencies fail clearly.
- Old checkpoints are not loaded accidentally.
- Outputs are provenance-recorded.

## Gate 6: Evaluation

Pass only if:

- Metrics independently verified.
- AUPRC accompanies AUROC for sparse positives.
- Uncertainty reported.
- Independence unit documented.
- Results tied to checkpoint, data, split, code, and environment.

## Gate 7: Validation

Pass only if:

- Validation addresses exact claim.
- Structural plausibility checked.
- MD artifacts current.
- RMSD/RMSF/DCCM/volume/contact metrics correct.
- Evidence classified as support, partial support, inconclusive, weakening, or contradiction.

## Gate 8: Claim

Pass only if:

- Paper claims match evidence.
- Limitations are stated.
- Figures and captions do not overclaim.
- Citations support exact statements.
- Disallowed wording removed.

## Gate 9: Figure

Pass only if:

- Axes and units are shown.
- Uncertainty shown when relevant.
- Controls visible.
- Scale honest.
- Caption matches evidence.
- Inputs are current.

## Gate 10: Submission Readiness

Pass only if:

- Code reproducible.
- Metrics verified.
- Leakage checked.
- Preprocessing checked.
- Biology checked.
- Validation classified.
- Claims audited.
- Figures audited.
- Provenance complete.
- Human approval recorded.

## Stale Gate Policy

A gate becomes stale when relevant data, code, splits, checkpoints, metric scripts, MD analysis scripts, claim wording, or known bugs change.
