# Publication Readiness

## Purpose

Define what must be true before any external-facing writeup, abstract, poster, paper, preprint, or submission.

## Hard Rules

- Publication readiness requires reproducibility, provenance, benchmark fairness, statistical rigor, biological plausibility, uncertainty statements, and claim audit.
- No figure, table, metric, or MD result may appear without provenance.
- Negative and unexpected results must be included if they affect conclusions.
- Limitations must be explicit and visible.

## Required Checks

- Source-of-truth audit complete.
- Assumption and uncertainty registers complete.
- Dataset, benchmark, split, label, graph audits PASS.
- Biological data sanity review PASS.
- Red-team audit addressed.
- Null baselines reported.
- Evaluation metrics include AUROC, AUPRC, top-k, calibration, CIs, seed variance.
- PCNA-specific audit PASS for PCNA claims.
- Interpretability audit complete for model-derived biological claims.
- MD pre-registration, reality check, and interpretation audit complete if MD is discussed.
- Figure provenance complete.
- Claim audit PASS.
- Human final-claims review recorded.

## Forbidden Actions

- Writing final conclusions before readiness.
- Omitting limitations because they weaken impact.
- Publishing only positive seeds, positive sites, or positive MD outcomes.
- Presenting exploratory MD as validation.

## Examples Of Failure

- Paper draft includes a GNN superiority claim without same-split baselines.
- Figure lacks command, input hash, or source artifact.
- Limitations omit benchmark label noise or PCNA leakage risk.

## Prevention

Run publication readiness as the final gate after [23_FINAL_PROJECT_AUDIT_TEMPLATE.md](23_FINAL_PROJECT_AUDIT_TEMPLATE.md).

## Compliance Artifact

`reports/phase2/publication_readiness.md`.

## If The Rule Fails

Do not submit or share externally as a final result. Use only as internal draft.
