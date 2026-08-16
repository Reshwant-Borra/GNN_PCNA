# Model Architecture Constraints

## Purpose

Prevent model code from learning batch artifacts, shortcut features, or invalid probability semantics.

## Hard Rules

- No batch leakage.
- In PyG batches, never use `h.mean(dim=0)` or any global mean across mixed proteins for graph context.
- Use graph-aware aggregation such as `scatter_mean(h, batch, dim=0)` and broadcast by `batch`.
- If training with `BCEWithLogitsLoss`, model forward must return logits and must not apply final sigmoid.
- Sigmoid is allowed only for reporting, ranking, calibration, and visualization.
- Chain-ID features require justification and ablation.
- Residue-index features require justification and ablation.
- Ranking-loss sampling must not use first-N deterministic residue ordering.
- Focal-loss alpha and class weights must be computed from train only.
- Architecture components require scientific and engineering justification.
- Major components require ablations.

## Forbidden Patterns

```python
h_global = h.mean(dim=0)
return torch.sigmoid(logits)  # during BCEWithLogits training
alpha = labels_all.mean()     # includes val/test
positives = y.nonzero()[:k]   # deterministic first-N ranking sample
features.append(raw_residue_number)  # without documented ablation
```

## Forbidden Actions

- Training a model whose forward output/loss pairing is unclear.
- Adding global graph context without batch-aware aggregation.
- Adding chain ID, residue index, or symmetry priors without ablation.
- Computing any class-balance parameter from validation or test labels.

## Required Architecture Audit

- Loss function and output semantics.
- Batch isolation.
- Feature list and shortcut risk.
- Chain-ID ablation.
- Residue-index ablation if present.
- No-ESM ablation if ESM is used.
- No-virtual-node/global-context ablation if used.
- Basic GCN/GAT baseline.
- Parameter count and config hash.

## Shortcut-Feature Audit

Run at minimum:

- no-chain-ID ablation
- residue-number permutation or removal
- graph-size correlation check
- per-protein metric review
- PCNA positive-control check separated from final validation

## Batch-Isolation Audit

Batch two proteins in different orders and verify each protein's logits match single-protein inference within numerical tolerance.

## Required Checks

- Static scan for forbidden patterns.
- Unit test for batch isolation.
- Loss/output semantics test.
- Shortcut-feature ablation plan before training.

## Examples Of Failure

- A virtual node averages all residues in a batch, causing validation proteins to influence training-protein predictions during batched evaluation.
- Model returns sigmoid scores and training uses `BCEWithLogitsLoss`, weakening or distorting gradients.
- Chain one-hot appears useful only because 8GLA ligand is on specific chains.

## Prevention

Add architecture tests before training. A model cannot be trained until the audit passes.

## Compliance Artifact

`reports/phase2/architecture_audit.md`, `reports/phase2/batch_isolation_audit.md`, and ablation reports.

## If The Rule Fails

Stop training. Patch the architecture, rerun architecture tests, invalidate affected checkpoints, and retrain.
