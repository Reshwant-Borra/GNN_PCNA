# Proposed Label Strategy

Date: 2026-05-27
Created by: Codex
Status: DRAFT - proposed strategy only, no labels frozen

## Governance Boundary

No label definition is frozen by this document. Human label-freeze review and label audit are mandatory before graph generation or training.

Governing rules: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `11_BIOLOGICAL_REALISM_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `14_CLAIM_POLICY.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`.

## Primary Label Candidate L1: CryptoBench Apo-Mapped Cryptic Pocket Residues

Label type: `curated_apo_holo_cryptic_pocket_proxy`

Definition candidate:

- Positive residues are apo-structure residues mapped from holo binding residues in a CryptoBench cryptic binding-site record.
- Holo binding residues are defined by the CryptoBench source as residues within 4.5 Angstrom of the holo ligand.
- A binding site is cryptic under the source definition when the apo/holo binding residue set has at least 2 Angstrom all-atom pocket RMSD and passes the source filtering steps.
- Negatives are residues in the same target chain(s) that are not positive and not ambiguous.
- Ambiguous residues must be masked, not counted as negatives.

Required metadata per label record:

- apo PDB ID, apo chain, biological assembly status, residue numbering, UniProt accession.
- holo PDB ID, holo chain, ligand ID, ligand residue number, ligand chain if present.
- apo residue selection and holo residue selection.
- mapping method and mapping confidence.
- raw file hash, label definition hash, output hash.

Allowed claim scope: benchmark cryptic-pocket residue recovery, not experimental validation of PCNA mechanism or druggability.

## Auxiliary Label Candidate L2: Ligand-Binding Proxy Residues

Sources: BioLiP/BioLiP2, scPDB, possibly PDBbind only if explicitly approved.

Label type: `ligand_binding_proxy`

Definition candidate:

- Positive residues are source-defined ligand-contact or binding-site residues.
- Atom basis, distance threshold, ligand filters, and biological relevance rules must be source-specific and recorded.
- These labels must not be mixed with L1 in the same dataset ID.

Allowed use: auxiliary training, calibration, baseline context, or control experiments.

Forbidden use: reporting as cryptic-pocket truth.

## Auxiliary Label Candidate L3: Allosteric Site Context

Source: ASD after entry-level audit.

Label type: `allosteric_site_context`

Definition candidate:

- Positive residues/sites are curated allosteric-site annotations only when structure, chain, residue mapping, and evidence type are explicitly available.
- Predicted allosite-potential entries must be separated from experimentally supported entries.

Allowed use: biological context or exploratory allosteric-site comparison.

Forbidden use: direct PCNA mechanism claim without PCNA-specific evidence.

## Baseline/Method Label Candidate L4: PocketMiner Simulation-Opening Labels

Source: PocketMiner paper/code/data if local files are acquired.

Label type: `simulation_opening_proxy`

Definition candidate:

- Positive residues are residues participating in pocket formation in future MD windows under the PocketMiner labeling protocol.
- This label type is method-specific and time-window-specific.

Allowed use: baseline reproduction or auxiliary method comparison.

Forbidden use: mixing with CryptoBench apo-holo labels without separate dataset ID.

## Positive Controls

- CryptoBench held-out cryptic pockets after split audit.
- 8GLA/ZQZ PCNA positive-control region only as a declared positive-control gate and only if isolated from training, threshold selection, and model selection.
- PocketMiner validation examples only if not used for training or tuning.

## Negative and Null Baselines

- Random residue ranking.
- Shuffled-label control.
- Residue-type prior.
- SASA/accessibility-only ranking.
- B-factor/flexibility-only ranking if available.
- Local density/geometric-cavity ranking.
- fpocket and P2Rank residue-proximity scores.
- CryptoBench noncryptic pockets if local `noncryptic-pockets.json` or equivalent file is present and audited.

## Required Label Audit Before Freeze

- Label reproducibility from raw structures.
- Chain identity and UniProt mapping check.
- Ligand identity and excluded additive check.
- Positive count per protein and per pocket.
- Ambiguous residue count and mask policy.
- Missing residue and insertion-code policy.
- Graph-node to label-vector alignment plan.
- Representative visualization spot checks for train, validation, test, and PCNA positive controls.

## Current Blockers

- No local label files.
- No raw structure files or hashes.
- No exact CryptoBench schema parsed locally.
- No human approval for L1/L2/L3/L4.
- No PCNA control label mapping freeze.

## Recommendation

Use L1 as the primary Phase 2 label candidate if CryptoBench files pass audit. Keep L2, L3, and L4 separate as auxiliary/context/baseline labels. Do not train or generate graphs until label freeze and human review are complete.

Current readiness: not ready for label freeze.
