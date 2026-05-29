# Biological Realism Rules

## Purpose

Ensure predicted residue clusters are biologically plausible before they become PCNA candidate-pocket claims.

## Hard Rules

- Predictions must be checked against known biology.
- Predicted pockets must be structurally plausible.
- Solvent accessibility must be checked.
- Conservation should be checked where possible.
- PCNA stability and trimer integrity must be considered.
- Literature consistency is required.
- No mechanism claim is allowed if the biological mechanism is unclear.
- Uncertainty must be stated.

## Biological Realism Checklist

- Is the predicted site physically accessible?
- Does it overlap known interaction interfaces?
- Does it disrupt essential PCNA structure or trimer integrity?
- Is it conserved or variable in a way consistent with the hypothesis?
- Is it plausible as a cryptic, allosteric, or candidate pocket region?
- Is there literature support for local flexibility, dynamics, ligandability, or interface relevance?
- Does MD support, contradict, or fail to resolve it?
- What alternative explanations exist, including label leakage or shortcut features?

## Forbidden Actions

- Calling a buried inaccessible cluster a pocket without evidence of opening.
- Treating cancer relevance as druggability.
- Treating overlap with PIP-box/APIM interface as novelty.
- Ignoring PCNA trimer or DNA-clamp function.
- Claiming therapeutic relevance from GNN score alone.

## Required Checks

- SASA/accessibility check.
- Pocket geometry check.
- Interface-overlap check.
- Conservation review if available.
- Trimer-interface review.
- Literature/source-index review.
- Alternative-explanation table.

## Examples Of Failure

- Top-ranked residues sit inside the PCNA ring interface and would destabilize the clamp, but the report calls them druggable.
- Prediction overlaps the known IDCL/PIP-box region and is described as novel.
- A region is conserved because it is structurally essential, not because it is a useful allosteric target.

## Prevention

Run biological realism audit after prediction and before MD or claims. Use [12_PCNA_SPECIFIC_CHECKS.md](12_PCNA_SPECIFIC_CHECKS.md) for PCNA-specific mapping.

## Compliance Artifact

`reports/phase2/biological_realism_audit.md`.

## If The Rule Fails

Do not advance the prediction to MD or claims. Reclassify it as biologically implausible, known-interface overlap, or unresolved.
