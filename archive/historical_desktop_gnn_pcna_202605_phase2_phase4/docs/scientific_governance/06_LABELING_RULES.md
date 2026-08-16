# Labeling Rules

## Purpose

Define how residue labels are created and audited so model outputs mean what reports say they mean.

## Hard Rules

- Exact label definitions are required before preprocessing.
- Distance thresholds must be documented with atom basis: C-alpha, side-chain heavy atom, all residue heavy atoms, ligand heavy atoms, or curated annotation.
- Ligand/contact definitions must identify ligand IDs, biologically relevant ligands, excluded crystallization additives, ions, waters, DNA/RNA, and partner chains.
- Positive, negative, and ambiguous residue rules must be explicit.
- Ambiguous residues must be masked or assigned under a documented rule, not silently counted as negatives.
- No post-hoc relabeling to improve metrics.
- Labels must be reproducible from raw structures.
- Labels must map correctly to graph nodes.
- Label type must be named: curated cryptic pocket, ligand-proximity pocket, allosteric site, interface, positive-control contact, or candidate region.

## Acceptable Labels

- Curated cryptic-pocket annotations from a benchmark, with source citation and residue mapping.
- Heavy-atom residue-to-ligand contact labels with ligand IDs and thresholds.
- PCNA positive-control labels for 8GLA/AOH1996 derivative ZQZ, explicitly marked positive control.
- Interface labels for PIP-box/APIM comparison, explicitly not used as cryptic-pocket positives unless justified.

## Bad Labels

- "Residues near the known pocket" without threshold or atom definition.
- C-alpha labels reported as experimentally verified cryptic-pocket labels.
- Labeling predicted residues as positives after model inference.
- Treating all unannotated residues as true negatives when the benchmark only marks known positives.

## Forbidden Actions

- Changing the distance cutoff after seeing validation/test metrics.
- Using PCNA residue-number lookups on non-PCNA chains.
- Labeling known PIP-box/APIM interface residues as novel pockets without separate category.
- Dropping residues without updating label-node alignment.

## Required Checks

- Label reproducibility from raw structure.
- Label-node alignment check.
- Positive count per protein.
- Ambiguous residue count.
- Ligand identity check.
- Chain identity check.
- Spot-check visualization for representative train, validation, test, and PCNA positive-control structures.

## Examples Of Failure

- A residue with missing C-alpha is skipped in graph nodes but still present in the label vector.
- ZQZ in 8GLA is treated as parent AOH1996 without noting derivative status.
- An interface residue is counted as cryptic because a ligand happens to be near it in a holo structure.

## Prevention

Generate labels with a deterministic script that writes raw input hash, label definition hash, structure ID, chain ID, residue numbering scheme, and output hash.

## Compliance Artifact

`data/labels/phase2_labels_<hash>.json` and `reports/phase2/label_audit.md`.

## If The Rule Fails

Stop training and evaluation. Fix label generation, regenerate graphs, and invalidate checkpoints trained on bad labels.
