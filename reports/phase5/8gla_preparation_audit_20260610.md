---
type: phase5-structure-preparation-audit
pdb_id: 8GLA
date: 2026-06-10
status: PREPARATION_AUDIT_ONLY
md_executed: false
---

# 8GLA Preparation Audit - Phase 5 Wave 1

## Scope

This audit verifies deposited structure metadata, biological assembly selection, PCNA
chain mapping, canonical residue numbering, ligand location, and setup caveats for the
official Wave 1 positive-control systems. No minimization, equilibration, production,
trajectory generation, parameterization, or trajectory analysis was run.

## Source Files And Hashes

| Path | SHA256 | Size bytes |
|---|---|---:|
| `data/raw_intake/pcna_structures/8GLA.cif` | `914f86a9ec6744143d8c9869643af58740d8a13e1d52f66b4fb8ec501a3ab487` | 837379 |
| `data/raw_intake/pcna_structures/8GLA_metadata.json` | `f5281ca8fad1055dfeaf32b9de3070dd87a9131577790a28250ef173f3f4dead` | 19677 |
| `data/raw_intake/pcna_structures/8GLA_assembly1.json` | `fa2dcd3eac8a3d435d6da4579472d8225ef0289caf58e8a5fd87a61aff9c5f05` | 6100 |

## Experimental Metadata

- Structure title: Co-crystal structure of caPCNA bound to the AOH1996 derivative, AOH1996-1LE
- Method: X-RAY DIFFRACTION
- Resolution: 3.77 A
- R-work/R-free: 0.2051 / 0.26
- Primary PMID: 37531956
- RCSB revision date: 2024-10-16T00:00:00.000+00:00

## Biological Assembly And Chain Mapping

- Official Wave 1 assembly: RCSB biological assembly 1.
- Assembly 1 is recorded as trimeric with oligomeric count 3.
- Wave 1 PCNA auth chains: A, B, C.
- Deposited chain D is excluded from Wave 1 because it belongs to deposited assembly 2.
- All deposited PCNA chains map to UniProt P12004 residues 1-261 through `struct_ref_seq`.

## Missing Residues

| Chain | Missing residues |
|---|---|
| A | 1, 94, 95, 96, 106, 107, 108, 109, 165, 166, 185, 186, 187, 188, 189, 190, 191, 192, 255, 256, 257, 258, 259, 260, 261 |
| B | 83, 163, 164, 165, 166, 186, 187, 188, 189, 190, 191, 192, 193, 254, 255, 256, 257, 258, 259, 260, 261 |
| C | 1, 93, 94, 95, 96, 106, 107, 108, 122, 163, 164, 165, 166, 186, 187, 188, 189, 190, 191, 192, 199, 256, 257, 258, 259, 260, 261 |

## Candidate Window Completeness

| Candidate | Residues | Chain completeness |
|---|---:|---|
| PC-118 | 118-122 | A: complete; B: complete; C: missing 122 |

## ZQZ Ligand Identity And Location

- Ligand code: ZQZ.
- Identity: N-[2-(3-methoxyphenoxy)phenyl]-N~2~-(naphthalene-1-carbonyl)-L-alpha-glutamine.
- Formula/formal charge: C29 H26 N2 O6; formal charge 0.
- Assembly 1 contains six ZQZ instances assigned to chains A and B in deposited coordinates.

| Ligand label asym | Auth chain | Auth seq | Heavy atoms | Contacts <=4.5 A |
|---|---|---:|---:|---|
| E | A | 301 | 37 | A:40,44,45,46,47,126,234,250,251,252 |
| F | A | 302 | 37 | A:128,131,232,233,234,250,252,253 |
| G | A | 303 | 37 | A:25,26,27,38,39,40,41,44,121,123,124,125,126 |
| J | B | 301 | 37 | B:40,44,45,46,47,126,128,234,250,251,252 |
| K | B | 302 | 37 | B:128,129,231,232,233,234,250,252,253 |
| L | B | 303 | 37 | B:23,25,26,27,38,39,40,41,44,47,121,123,124,125,126 |

## Alternate Locations And Occupancy

- Alternate-location atom records: 0.
- Atom records with occupancy < 1.0: 0.
- Insertion codes: 0.

## Structural Caveats

- 8GLA resolution is 3.77 A and below the <=3.5 A quality threshold; it is authorized as a positive-control system only.
- Assembly 1 contains PCNA chains A/B/C; chain C is missing residue 122 in the PC-118 window.
- ZQZ appears as six ligand instances in assembly 1, contacting chains A and B in deposited coordinates; no ZQZ contacts were detected on chain C in assembly 1.
- No alternate locations or atom occupancies below 1.0 were detected in atom_site.

## Preparation Decision

8GLA is suitable only as the authorized positive-control starting structure after the
launch hold is lifted and ZQZ parameters are audited. The missing residue 122 on chain C
must be recorded in any future setup manifest and considered during positive-control
metric definition. This is not a novel-site validation structure.

Evidence status: verified from deposited mmCIF/RCSB metadata. Confidence: high for
chain/assembly/ligand facts; no MD outcome claim is made.
