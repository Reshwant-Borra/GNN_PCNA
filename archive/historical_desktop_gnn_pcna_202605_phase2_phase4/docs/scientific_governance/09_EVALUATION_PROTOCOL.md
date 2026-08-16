# Evaluation Protocol

## Purpose

Define how metrics are produced and interpreted for residue-level PCNA pocket prediction.

## Hard Rules

- Train metrics are diagnostic only.
- Validation metrics are for model selection only.
- Test metrics are reported once after freezing model, threshold policy, baselines, and report plan.
- No combined validation/test headline.
- No test-set threshold tuning.
- Report per-protein metrics.
- Report macro and micro metrics.
- Report AUROC and AUPRC.
- Report top-k residue recovery.
- Report calibration.
- Report confidence intervals.
- Bootstrap confidence intervals over proteins.
- Minimum 3 seeds; 5 preferred.
- Show seed variance.
- Define success criteria before training.

## Required Metrics

- AUROC, macro and micro.
- AUPRC, macro and micro.
- Top-k recovery at k values defined before training.
- Precision at k and recall at k.
- Calibration curve or expected calibration error if scores are interpreted comparatively.
- Bootstrap 95 percent CIs over proteins.
- Per-protein table.
- Seed mean, standard deviation, and range.

## Meaningful Improvement

An improvement is meaningful only if:

- it is observed on validation during selection and on the single frozen test evaluation,
- it improves primary AUPRC or top-k recovery, not only AUROC,
- CIs or seed variance do not make it indistinguishable from baseline,
- the improvement survives required shortcut ablations or is honestly scoped.

## Unstable Performance

Performance is unstable if:

- seed variance changes the conclusion,
- one protein dominates micro metrics,
- macro and micro metrics conflict sharply,
- AUPRC improves while biological realism fails,
- calibration is poor and scores are described as probabilities.

## Forbidden Actions

- Reporting train or validation as final evidence.
- Choosing k, threshold, seed count, or confidence interval method after seeing test.
- Hiding failed seeds.
- Calling high AUROC strong evidence under rare positive labels without AUPRC/top-k.

## Required Checks

- Evaluation config frozen before test.
- Test-used-once log.
- Seed audit.
- Bootstrap audit.
- Baseline same-split audit.
- Calibration audit.

## Examples Of Failure

- Test AUROC is high but AUPRC is near random; report says model is highly accurate.
- Validation and test are combined to increase n.
- Threshold is selected on test to make the AOH1996 gate pass.

## Prevention

Make evaluation script write an immutable run manifest and refuse to run test mode without a frozen model manifest.

## Compliance Artifact

`reports/phase2/evaluation_<run_id>.md`.

## If Metrics Conflict

Report the conflict. Do not average it away. If scientific validity metrics fail, downgrade claims even if numerical metrics look strong.
