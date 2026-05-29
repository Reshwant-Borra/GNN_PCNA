# Project-Specific GNN and MD Rules

## Default Scientific Posture

Any impressive result is suspicious until independently checked.

Prefer a weaker true claim over a stronger unsupported claim.

## Safe Claim Bias

Prefer:

- "candidate pocket-associated residue region"
- "computationally predicted region"
- "partially supported by structural proximity"
- "requires further validation"
- "MD under the tested conditions did not strongly support pocket opening"

Avoid unless explicitly approved:

- "validated cryptic pocket"
- "confirmed novel residues"
- "MD proves opening"
- "discovered binding site"
- "generalizes broadly"

## GNN Evaluation Rules

- Residues are not automatically independent samples.
- Report AUPRC with AUROC for sparse positives.
- Report positive-class baseline.
- Bootstrap at protein or structure level for generalization claims.
- Positive-control recovery is not independent validation if related data influenced training or thresholding.
- The GNN must beat simple baselines under leakage-clean splits.

## Leakage Rules

Check:

- Chain leakage.
- PDB leakage.
- Duplicate leakage.
- Homology leakage.
- Apo/holo leakage.
- Label transfer leakage.
- Feature normalization leakage.
- Test-set tuning leakage.
- Old checkpoint leakage.

## Preprocessing Rules

Verify:

- PDB residue numbers map to graph nodes.
- Chain IDs are preserved.
- Node labels align with residues.
- Edge thresholds are correct.
- Coordinates are not mixed.
- Apo/holo alignment does not leak ligand information.
- Symmetry priors operate per-position, not globally.

## Biological Realism Rules

Predicted residues must be checked for:

- Physical proximity.
- Solvent accessibility.
- Coherent structural clustering.
- PCNA ring architecture consistency.
- Chain and symmetry correctness.
- Relationship to known AOH1996-associated residues.
- Mechanistic plausibility.

## MD Validation Rules

MD can support:

- Simulation stability.
- Local flexibility changes.
- Contact persistence.
- Pocket opening frequency.
- Distance distribution shifts.

MD does not automatically support:

- Existence of a cryptic pocket.
- Ligand binding.
- Experimental validation.
- Novel residue confirmation.

Required MD checks:

- RMSD.
- RMSF.
- Pocket volume over time.
- Opening frequency.
- Contact persistence.
- DCCM with convention documented.
- Frame/window uncertainty.
- Topology and trajectory provenance.

## Paper Rules

Claim strength levels:

- Proven experimentally.
- Strongly supported computationally.
- Moderately supported.
- Suggestive.
- Hypothesis-generating.
- Unsupported.
- Contradicted.

The paper cannot use wording stronger than the Claim Registry allows.
