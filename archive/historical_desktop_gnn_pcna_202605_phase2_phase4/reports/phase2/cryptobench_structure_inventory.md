# CryptoBench Structure Inventory

## Status

- Final audit status: `STRUCTURES_READABLE_FOR_AUDIT_NOT_GRAPHED`
- Graph construction is not authorized by this report.

## Inventory Summary

- ZIP path: `data/raw_intake/cryptobench/files/672a0171eae0bff252ba9ea3_cif-files.zip`
- ZIP SHA-256: `8d15f897bfdfdf61c7d97a29f5f6ca2c5e03d73d8fb89be7da5bbc245cf56ae4`
- ZIP `.cif` count: 5005
- Required PDB IDs from cryptic records: 5005
- Missing cryptic required structures: 0
- Required PDB IDs from noncryptic auxiliary records: 8440
- Missing noncryptic auxiliary structures: 6915
- Extra CIFs not referenced by parsed records: 0
- Required CIFs readable: 5005 / 5005
- Required CIFs with atom_site loop found: 5005 / 5005
- Required CIF atom-site parse issues: 0

## Graph Feasibility

- Residue-level graph construction appears practical in principle for `dataset.json` cryptic records because all 5,005 referenced mmCIF files are present/readable and atom-site loops expose chains and resolved residues.
- Graph construction is not complete for `noncryptic-pockets.json` as-is because 6,915 referenced noncryptic auxiliary structures are not present in the local ZIP.
- The appropriate MVP node granularity is one resolved protein residue per `(structure_id, chain_id, auth_seq_id, insertion_code, residue_name)` record.
- Edge construction from CIFs appears practical for spatial contacts and sequence edges, but final cutoff/atom basis and missing-gap policy must be frozen before graph generation.
- Chain and residue metadata must be preserved exactly; reindexing would violate governance.
- ESM/protein-sequence alignment is feasible but risky unless the project stores both the observed-residue sequence and source/auth numbering map. The bundled example documents a numbering shift for `7w19A`.

## Missing Noncryptic Auxiliary Structure Examples

- `1a3b`
- `1a3e`
- `1a46`
- `1a4w`
- `1a5g`
- `1a61`
- `1a7c`
- `1aaw`
- `1abj`
- `1ad4`
- `1ad8`
- `1afe`
- `1aht`
- `1ai3`
- `1ai8`
- `1aix`
- `1amq`
- `1amr`
- `1ars`
- `1asa`
- `1asc`
- `1asd`
- `1ay6`
- `1b12`
- `1b4d`
- `1b4x`
- `1ba8`
- `1bb0`
- `1bcu`
- `1bfb`
- `1bfc`
- `1bhx`
- `1bjp`
- `1bpy`
- `1br6`
- `1bso`
- `1c1h`
- `1c3m`
- `1c50`
- `1c5w`
- `1c5x`
- `1c5y`
- `1c5z`
- `1c8l`
- `1c9c`
- `1c9e`
- `1ca8`
- `1cbx`
- `1cps`
- `1cze`
- `1d2u`
- `1d3d`
- `1d3p`
- `1d3s`
- `1d4p`
- `1d9i`
- `1dae`
- `1dag`
- `1dai`
- `1ddr`
- `1dds`
- `1df7`
- `1dg5`
- `1dhi`
- `1dhj`
- `1dhs`
- `1dht`
- `1dko`
- `1dll`
- `1dmb`
- `1doj`
- `1dra`
- `1drb`
- `1dx5`
- `1dx6`
- `1dyh`
- `1dyj`
- `1e4h`
- `1e5a`
- `1e7a`
- `1e7b`
- `1e7c`
- `1eax`
- `1efz`
- `1ejn`
- `1emd`
- `1enu`
- `1eny`
- `1eqd`
- `1eqm`
- `1erb`
- `1erx`
- `1eyw`
- `1ez9`
- `1ezf`
- `1f3e`
- `1f57`
- `1f5k`
- `1f5l`
- `1fds`

## Atom-Site Parse Error Examples

None detected by the lightweight parser.

## Residue And Chain Consistency

- Selected residue tokens checked against parsed atom-site residue IDs: 409944.
- Selected residue tokens absent from parsed atom-site residue IDs: 721.
- Selected-chain absence issues: 0.
- Residue numbering is therefore mostly parseable, but not clean enough for graph generation without a reviewed missing-residue/insertion-code policy and residue-level spot checks.

## Machine-Readable Index

- Full per-structure index: `data/registries/cryptobench_structure_index.json`

## Provenance

- Date: 2026-05-27T18:29:47-04:00
- Command: `python scripts/cryptobench_deep_audit.py`
- Source paths: `data/raw_intake/cryptobench/metadata_files/`, `data/raw_intake/cryptobench/labels_or_splits/`, `data/raw_intake/cryptobench/files/672a0171eae0bff252ba9ea3_cif-files.zip`
- Governance paths: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `14_CLAIM_POLICY.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`
- Confidence: high for local schema/count/hash/readability checks; medium for label-semantic interpretation from local README; low for homolog exclusion because no sequence clustering was run.
- Evidence status: verified for local files and machine checks; inferred for biological meaning; uncertain for final scientific usability.
