# Interpretability Before Claims

## Purpose

Prevent black-box model outputs from becoming biological claims without understanding what the model relied on.

## Hard Rules

- Interpretability review is required before PCNA claims.
- Interpretability is supportive, not proof.
- Attribution must be checked against shortcut features and null baselines.
- If explanations are unstable or biologically incoherent, claims must be downgraded.

## Required Checks

- Residue importance or attribution for top PCNA predictions.
- Attention visualization if attention is used.
- Gradient or perturbation attribution where feasible.
- Sensitivity to removing chain ID, residue index, ESM/pLM features, and geometric features.
- Comparison to null baselines: accessibility, conservation, B-factor, geometry.
- Stability across seeds.
- Mapping of important residues to PCNA trimer, PIP-box/APIM/IDCL, AOH1996 region, and interfaces.

## Forbidden Actions

- Claiming mechanism from attention weights alone.
- Showing only attractive attribution examples.
- Ignoring attribution that points to shortcut features.
- Making PCNA biological claims from a black-box score alone.

## Examples Of Failure

- Top prediction is driven by chain ID rather than local pocket geometry.
- Attribution highlights solvent exposure only, matching the null baseline.
- Important residues map to non-PCNA partner chains.

## Prevention

Run interpretability after frozen PCNA prediction and before claim audit.

## Compliance Artifact

`reports/phase2/interpretability_before_claims.md`.

## If The Rule Fails

Do not make PCNA site claims. Report prediction as unresolved or exploratory only.
