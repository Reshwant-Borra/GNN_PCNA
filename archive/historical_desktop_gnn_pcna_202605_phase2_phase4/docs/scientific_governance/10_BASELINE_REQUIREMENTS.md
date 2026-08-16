# Baseline Requirements

## Purpose

Prevent claims of model value without fair comparisons.

## Hard Rules

- Baselines are required before superiority or novelty-performance claims.
- Baselines must use the same split.
- Baselines must use the same label definition or clearly state incompatibility.
- Baseline inputs and outputs require provenance.
- No claim of superiority without same-split comparison.

## Required Baselines Where Applicable

- PocketMiner.
- fpocket.
- P2Rank.
- Simple geometric pocket baseline.
- Conservation baseline if available.
- Solvent exposure baseline if available.
- GCN/GAT/basic GNN baseline.
- No-ESM ablation.
- No-virtual-node or no-global-context ablation.
- No-chain-ID ablation.
- Random baseline.

## Weak Baseline Warning

Random baseline alone is never enough. A random baseline can establish that the task is not trivial, but it cannot establish the GNN is useful for PCNA candidate pocket discovery.

## Forbidden Actions

- Comparing Phase 2 metrics to published PocketMiner numbers if labels, splits, positive rates, and datasets differ, unless framed as non-equivalent context.
- Omitting fpocket/P2Rank because the GNN outperforms random.
- Calling a baseline "failed" because it contradicts the expected story.

## Required Checks

- Same split check.
- Same label-definition check.
- Input structure parity check.
- Baseline version and command logged.
- Baseline output hash.
- Per-protein baseline comparison.

## Examples Of Failure

- GNN AUPRC is compared to PocketMiner published PR-AUC without running PocketMiner on the Phase 2 split.
- fpocket predicts the known PCNA interface but the report excludes it because it is not novel.
- No-chain-ID ablation performs the same, but chain-ID feature remains unexplained.

## Prevention

Run baselines before final test claims and include them in the readiness gate.

## Compliance Artifact

`reports/phase2/baseline_audit.md` plus baseline manifests.

## If The Rule Fails

Remove superiority language. Report model results as internal performance only until baselines are complete.
