# Final Project Audit Template

## Purpose

Provide the mandatory final audit structure for Phase 2 readiness decisions.

## Hard Rules

- Every section must be filled or explicitly marked not applicable with justification.
- The final decision must be one of the listed options.
- Missing provenance, claim, evaluation, biology, or dataset evidence blocks preliminary claims.

## Forbidden Actions

- Leaving unresolved risks out of the final decision.
- Using this template as a narrative report without evidence links.
- Selecting a readiness decision that conflicts with failed gates.

## Required Checks

- Source-of-truth check.
- Dataset/split/label/graph check.
- Evaluation/baseline check.
- Biological/PCNA/MD check.
- Provenance/claim check.

## Examples Of Failure

- Final decision says READY FOR PRELIMINARY CLAIMS while claim readiness is FAIL.
- MD section omits an unexpected negative trajectory.
- Baseline audit is blank but superiority language remains.

## Prevention

Fill this template from completed audit artifacts, not from memory or summary prose.

## Compliance Artifact

Completed copy of this template in `reports/phase2/final_project_audit.md`.

## If This Audit Fails

Use the final decision to identify the blocking category and apply [19_STOP_CONDITIONS.md](19_STOP_CONDITIONS.md).

## Executive Summary

- Audit ID:
- Date:
- Reviewer(s):
- Scope:
- Final decision:

## Source-Of-Truth Status

- Canonical repo/branch/commit:
- Canonical dataset registry:
- Canonical split:
- Canonical results directory:
- Stale artifact status:

## Project Scope Audit

- Scope decision:
- Out-of-scope claims removed:
- Remaining scope risks:

## Assumption Status

| Assumption ID | Status | Evidence | Risk |
|---|---|---|---|

## Scientific Uncertainty Status

| Uncertainty ID | Status | Impact | Claim effect |
|---|---|---|---|

## Benchmark Limitations Audit

- Benchmark(s):
- Label origin:
- Known noise/bias:
- Accepted limitations:

## Data Lifecycle Audit

- Lifecycle registry:
- Excluded/quarantined data:
- Removal reason completeness:

## Human Review Gate Audit

- Source freeze:
- Dataset adoption:
- Split freeze:
- Label freeze:
- First training:
- First PCNA prediction:
- First MD interpretation:
- Preliminary/final claims:

## Dataset Audit

- Registry complete:
- Inclusion/exclusion criteria met:
- Chain mapping complete:
- Leakage risks:

## Split Audit

- Split hash:
- Sequence cluster audit:
- Structural similarity audit:
- Apo/holo grouping:
- PCNA isolation:

## Label Audit

- Label definition:
- Positive/negative/ambiguous rules:
- Label-node alignment:
- Label provenance:

## Biological Data Sanity Audit

- Example structures inspected:
- PCNA interfaces inspected:
- AOH1996/8GLA mapping inspected:
- Label distributions:
- Residue accessibility:
- Decision:

## Graph Audit

- Graph manifest:
- Node/residue alignment:
- Feature definitions:
- Graph hashes:

## Architecture Audit

- Output/loss semantics:
- Batch isolation:
- Shortcut-feature audit:
- Ablations:

## Evaluation Audit

- Validation-only selection:
- Test-used-once:
- AUROC/AUPRC/top-k/calibration:
- Bootstrap CIs:
- Seed variance:

## Baseline Audit

- PocketMiner:
- fpocket:
- P2Rank:
- Simple baseline:
- GNN ablations:

## Null Hypothesis Baseline Audit

- Accessibility-only:
- Conservation-only:
- B-factor/flexibility-only:
- Geometry-only:
- Residue-type prior:
- Shuffled-label control:

## Red-Team Audit

- High-risk attacks:
- Resolved attacks:
- Remaining risks:

## Biological Realism Audit

- Accessibility:
- Structural plausibility:
- Conservation:
- Alternative explanations:

## PCNA-Specific Audit

- Trimer mapping:
- PIP-box/APIM comparison:
- AOH1996/8GLA positive-control status:
- ATX-101 framing:

## Interpretability Audit

- Attribution method:
- Shortcut sensitivity:
- Seed stability:
- PCNA mapping:

## MD Interpretation Audit

- Pre-MD reality check:
- Pre-registration:
- Setup provenance:
- Trajectory quality:
- Positive/negative/unexpected outcome interpretation:
- Claim limits:

## AI Hallucination Audit

- Generated scientific text checked:
- Unsupported statements removed:
- Source or uncertainty markers present:

## Provenance Audit

- Commit/config/dataset/split hashes:
- Seeds:
- Commands:
- Environment:
- Reproducibility status:

## Claim Audit

- Allowed claims:
- Forbidden claims removed:
- Evidence mapping:
- Limitations:

## Negative Result Success Review

- Negative/mixed results:
- Honest interpretation:
- Success criteria met:

## Publication Readiness

- Figure provenance:
- Literature grounding:
- Statistical rigor:
- Limitations section:
- Final uncertainty statement:

## Unresolved Risks

| Risk | Severity | Owner | Required action |
|---|---|---|---|

## Final Allowed Claims

- 

## Final Forbidden Claims

- 

## Readiness Decision

Choose one:

- READY FOR TRAINING
- READY FOR EVALUATION
- READY FOR PRELIMINARY CLAIMS
- NOT READY - DATASET ISSUE
- NOT READY - BIOLOGY ISSUE
- NOT READY - EVALUATION ISSUE
- NOT READY - PROVENANCE ISSUE
- NOT READY - CLAIM ISSUE

## Sign-Off

- Reviewer:
- Date:
- Conditions:
