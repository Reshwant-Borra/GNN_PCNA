# Null Hypothesis Baselines

## Purpose

Test whether the GNN adds value beyond trivial structural biology. Many apparent AI gains are basic heuristics rediscovered with GPUs.

## Hard Rules

- Null baselines are required before any GNN performance or PCNA claim.
- Null baselines must use the same split and label definition.
- If a null baseline matches or beats the GNN, the GNN cannot be claimed superior.
- Null baseline results must be reported, not hidden.

## Required Null Baselines

- Random residue ranking.
- Shuffled-label control.
- Residue-type prior.
- Solvent-accessibility-only baseline.
- Conservation-only baseline if conservation is available.
- B-factor/flexibility-only baseline if available.
- Local-density/geometric-cavity-only baseline.
- Simple fpocket/P2Rank-derived pocket proximity score where applicable.

## Forbidden Actions

- Comparing only against random.
- Calling GNN novel if accessibility-only explains the result.
- Excluding a baseline because it is too strong.
- Running null baselines on a different split or label definition.

## Required Checks

- Baseline input parity.
- Same split hash.
- Same label hash.
- Per-protein baseline results.
- Macro/micro AUROC and AUPRC.
- Top-k recovery.
- Bootstrap CIs where applicable.

## Examples Of Failure

- GNN top-k recovery is no better than ranking residues by SASA.
- B-factor alone recovers most positives.
- Label prevalence is mostly explained by residue type.

## Prevention

Implement null baselines before training or at latest before the first training evaluation report.

## Compliance Artifact

`reports/phase2/null_hypothesis_baselines.md`.

## If The Rule Fails

Remove GNN value claims. Report the result as a heuristic baseline finding or revise the model/evaluation.
