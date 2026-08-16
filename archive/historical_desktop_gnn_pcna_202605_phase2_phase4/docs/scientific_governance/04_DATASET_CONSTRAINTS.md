# Dataset Constraints

## Purpose

Ensure Phase 2 datasets support valid residue-level prediction of PCNA candidate cryptic/allosteric pocket regions without mystery data, split leakage, or hidden preprocessing assumptions.

## Hard Rules

- A dataset registry is required before graph generation.
- Every source requires license/citation, download method, biological system, structure IDs, chain IDs, label definition, split assignment, leakage risks, and hashes.
- No unlabeled mystery data may enter training, validation, or test.
- No duplicated protein systems, homolog clusters, apo/holo pairs, or ligand variants may cross splits.
- Chain mapping must identify target protein chains, partner peptide/protein chains, DNA/RNA chains, ligands, and excluded chains.
- Missing residues must be reported and either masked, excluded, or handled by a documented graph rule.
- Ligand/protein complexes must define whether interface residues from multiple chains can be positive.
- Feature-normalization statistics must be fit on train only.
- No validation or test data may determine preprocessing thresholds, label thresholds, feature scaling, class weights, focal-loss alpha, or filters.

## Inclusion Criteria

- Protein structures with resolvable residue-node mapping.
- Labels reproducible from raw structure files or curated benchmark annotations.
- Structure IDs and chain IDs can be verified against PDB, UniProt, or source metadata.
- If used for final PCNA claims, PCNA structures must be isolated from model selection.

## Exclusion Criteria

- Structures with unknown chain identity.
- Bytecode-only, generated-only, or manually edited structures without provenance.
- Ambiguous labels that cannot be regenerated.
- Apo/holo or homolog systems that would contaminate a split.
- Any PCNA-specific structure used in tuning when later claimed as final independent PCNA evidence.

## DATASET_REGISTRY.md Template

```markdown
# Dataset Registry

## Dataset: <name>
- Source:
- Download/access method:
- License/citation:
- Biological system:
- Structure IDs:
- Chain IDs:
- Target chains:
- Non-target protein chains:
- DNA/RNA chains:
- Ligands:
- Label definition:
- Preprocessing steps:
- Split assignment:
- Leakage risks:
- Apo/holo grouping:
- Sequence cluster:
- Structural similarity notes:
- Provenance hashes:
- Owner:
- Review status:
```

## Forbidden Actions

- Generating graphs before the registry and split protocol are frozen.
- Mixing curated cryptic-pocket labels with C-alpha ligand-proximity labels without separate dataset IDs.
- Reusing V1 `data/graphs`, `data/graphs_xl`, or PCNA graphs without registering their hashes and leakage status.
- Calling 8GLA/AOH1996 labels independent validation if 8GLA influenced training, fine-tuning, threshold selection, or model selection.

## Required Checks

- Dataset registry completeness check.
- Source hash check.
- Duplicate system check.
- Sequence clustering check.
- Apo/holo grouping check.
- Chain mapping check.
- Label-definition consistency check.
- Train-only normalization check.

## Examples Of Failure

- A CryptoSite-derived structure is labeled by ligand proximity but reported as curated cryptic-pocket ground truth.
- `1W60` and `8GLA` are treated as unrelated because their PDB IDs differ.
- Chain A is assumed to be PCNA in a complex where PCNA is chains B/C/D.

## Prevention

Make dataset loading impossible without a registry entry. The loader should fail closed when a source hash, chain mapping, or split assignment is missing.

## Compliance Artifact

`docs/scientific_governance/DATASET_REGISTRY.md` plus `reports/phase2/dataset_audit.md`.

## If The Rule Fails

Pause training and graph generation. Quarantine the dataset version, repair the registry, rerun leakage checks, and regenerate downstream artifacts.
