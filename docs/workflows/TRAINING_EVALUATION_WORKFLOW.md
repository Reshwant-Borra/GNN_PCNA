# Training and Evaluation Workflow

## Purpose

Train and evaluate models without accepting leaky or inflated metrics.

## Agents

- Context.
- Dataset Integrity.
- Leakage.
- Preprocessing.
- Model Training.
- Scientific Code Review.
- Testing.
- Metrics.
- Provenance.
- Contradiction.
- Claim if results affect paper.

## Steps

1. Load dataset, split, and checkpoint status.
2. Confirm label definition.
3. Run Dataset Gate.
4. Run Leakage Gate.
5. Run Preprocessing Gate.
6. Define baselines.
7. Review training code.
8. Run tests.
9. Train/evaluate.
10. Register checkpoint, logs, predictions, metrics.
11. Independently verify metrics.
12. Compute uncertainty at correct independence level.
13. Compare against baselines.
14. Check contradictions with old reports.
15. Update claim registry with safe metric language.

## Required Metrics

- AUROC.
- AUPRC.
- Positive-class baseline.
- Fold over random.
- Precision@K.
- Recall@K.
- Per-protein or per-structure metrics.
- Confidence intervals.

## Required Baselines

- Random.
- Sequence-only.
- Geometry-only.
- Distance-to-known-pocket.
- Logistic regression or random forest.
- Conservation baseline if available.
- fpocket or comparable tool if relevant.

## Pass Criteria

Pass only if Dataset, Leakage, Preprocessing, Code, Evaluation, and Provenance checks pass.
