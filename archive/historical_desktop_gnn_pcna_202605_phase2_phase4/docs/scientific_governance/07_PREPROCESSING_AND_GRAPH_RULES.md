# Preprocessing And Graph Rules

## Purpose

Constrain structure preprocessing and protein graph construction for residue-level GNN prediction.

## Hard Rules

- Raw structures must be validated before graph generation.
- Chain identity must be verified against registry entries.
- Residue numbering, insertion codes, and chain IDs must be preserved in graph metadata.
- Alternate locations require a deterministic policy.
- Missing residues require a gap policy.
- Graph nodes must align one-to-one with residue records and label entries.
- Edge definitions must be documented.
- Feature definitions must be documented.
- ESM or other protein language model features require model name, version, input sequence, and hash.
- Normalization statistics are fit on train only.
- Graphs are generated after split assignment.
- No stale cached graph reuse without registered hashes.

## Required Graph Metadata

Each graph must include:

- structure ID
- biological assembly/asymmetric-unit status
- chain IDs included and excluded
- residue identifiers including chain, residue number, insertion code, and residue name
- preprocessing command
- source file hash
- split hash
- label hash
- graph-construction code hash
- feature definition hash
- graph hash

## Edge Rules

- Spatial contact edges must state atom basis and cutoff, for example C-alpha distance <= 8 Angstrom.
- Sequential edges must respect missing-residue gaps.
- Symmetry or cross-chain edges must be justified by PCNA trimer biology and ablated.
- DNA/ligand/partner-protein edges must be excluded unless explicitly part of the task.

## Forbidden Actions

- Dropping chains or residues silently.
- Reindexing residues without preserving original identifiers.
- Bridging missing loops as if residues are adjacent.
- Mixing graph caches from different split, label, or feature definitions.
- Using validation/test features to fit scalers.

## Required Checks

- Node count equals expected residues.
- Labels align with residues.
- No NaNs or infinities.
- Chain IDs match registry.
- Missing residue gaps reflected in sequence edges.
- AltLoc policy logged.
- Graph hash stored.

## Examples Of Failure

- PCNA trimer interpreted from asymmetric unit without documenting biological assembly.
- Chain `D` encoded as "other" and later interpreted as PCNA chain C.
- ESM features generated from a sequence with missing residues while graph nodes come from resolved residues.

## Prevention

Make graph generation fail closed when metadata or hashes are missing. Run graph audit immediately after generation and before training.

## Compliance Artifact

`data/graphs/phase2_graph_manifest_<hash>.json` and `reports/phase2/graph_audit.md`.

## If The Rule Fails

Delete no files. Mark graph manifest `FAILED`, quarantine affected graphs, regenerate from raw structures after fixing preprocessing.
