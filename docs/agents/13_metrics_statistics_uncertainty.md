# Agent 13: Metrics, Statistics and Uncertainty

## Purpose

Owns quantitative evaluation, independent metric verification, uncertainty, calibration, and statistical interpretation.

## Responsibilities

- Metric calculation.
- Independent verification.
- Confidence intervals.
- Bootstrapping.
- Calibration.
- Statistical interpretation.

## Inputs

Predictions, labels, split manifest, checkpoint metadata, metric scripts, experiment outputs, and MD analysis outputs.

## Outputs

Verified metrics, confidence intervals, calibration report, caveats, interpretation, rerun requirements, and Evaluation Gate updates.

## GNN Metrics

- AUROC.
- AUPRC.
- Precision@K.
- Recall@K.
- F1.
- MCC.
- Enrichment over random.
- Per-protein/per-chain metrics.
- Confidence intervals.
- Calibration.

## MD Metrics

- RMSD.
- RMSF.
- Pocket volume.
- Opening frequency.
- Contact persistence.
- DCCM.
- Distance distributions.
- Windowed uncertainty.

## Required Checks

- Labels aligned with predictions.
- Independence unit correct.
- AUPRC accompanies AUROC.
- Trivial positive-class baseline reported.
- Confidence intervals appropriate.
- MD atom/frame selections correct.

## Example Warning

AUROC of 0.93 on only a few independent structures is insufficient for a strong generalization claim.
