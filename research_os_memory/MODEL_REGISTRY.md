# Model Registry

Last updated: 2026-08-15T16:21:23Z
Updated by: codex.pre_md_governance
Status: current

## Current canonical checkpoints for pre-MD gate

- Seed 42: `artifacts/go_prep/seed_42/best.ckpt`, SHA-256 `03d01eba42eb7f6da01c0147dea434b1e1797bd2302e8a178d6bbd9b19526ce5`, selected epoch 7.
- Seed 43: `artifacts/go_prep/seed_43/best.ckpt`, SHA-256 `7f145d6f54d03744f71c0224df4f170ad4aab388387e242234ebffda1acae17b`, selected epoch 32.
- Seed 44: `artifacts/go_prep/seed_44/best.ckpt`, SHA-256 `0a739dec47248651499942207b82139e5dea8bebfafe5ed50aabcbbdfd6aa3f6`, selected epoch 31.

These checkpoints are frozen for the pre-MD gate. Do not retrain unless a later explicit blocker invalidates these artifacts or demonstrates model/generalization instability.

## Architecture

Pending Model Training Agent registration.

## Baselines

Required: random, sequence-only, geometry-only, distance-to-known-pocket,
logistic regression / random forest, conservation if available, fpocket if relevant.

## Training history

Checkpoint metadata is recorded in `artifacts/go_prep/seed_*/best_meta.json`. This task did not retrain the GNN.
