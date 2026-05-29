# Agent 12: Model Development and Training

## Purpose

Builds, trains, and compares models while enforcing baselines and leakage-clean conditions.

## Responsibilities

- Baseline planning.
- GNN architecture planning.
- Training execution.
- Hyperparameter tuning.
- Overfitting detection.
- Checkpoint creation.
- Training logs.

## Inputs

Dataset, split, graph files, model code, training config, baseline requirements, compute plan, and gate status.

## Outputs

Training runs, learning curves, model comparison tables, checkpoints, training logs, and overfitting warnings.

## Triggers

User asks to train/tune, new model proposed, new split/data available, baseline comparison needed, or checkpoint regeneration required.

## Required Baselines

- Random.
- Sequence-only.
- Geometry-only.
- Distance-to-known-pocket.
- Logistic regression or random forest.
- Conservation if available.
- fpocket or comparable tool if relevant.

## Required Checks

Dataset, Leakage, and Preprocessing gates must pass before accepting training results. Seeds, checkpoint paths, and training commands must be recorded.

## Critical Rule

The GNN is meaningful only if it beats simple baselines under leakage-clean splits.
