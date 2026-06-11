---
type: phase5-structure-preparation-audit
pdb_id: 1AXC
date: 2026-06-10
status: PREPARATION_AUDIT_ONLY
md_executed: false
---

# 1AXC Preparation Audit - Phase 5 Wave 1

## Scope

This audit verifies the 1AXC PCNA trimer, p21 peptide removal policy, residue numbering,
candidate-window completeness, and apo-from-p21 limitations for the official Wave 1
`1axc_apo_from_p21` system. No minimization, equilibration, production, trajectory
generation, or trajectory analysis was run.

## Source Files And Hashes

| Path | SHA256 | Size bytes |
|---|---|---:|
| `data/raw_intake/pcna_structures/1AXC.cif` | `56ff84ea5ff2e6bd8cb8e783ec906c9ea687f5aecf74b9163bcd54262d4351af` | 865375 |
| `data/raw_intake/pcna_structures/1AXC_metadata.json` | `40181cdc665d9d7ddab317e0d8ac96539b837d985f80626deb6b071626f3493f` | 15800 |

## Experimental Metadata

- Structure title: HUMAN PCNA
- Method: X-RAY DIFFRACTION
- Resolution: 2.6 A
- R-work/R-free: 0.192 / 0.289
- Primary PMID: 8861913
- RCSB revision date: 2024-04-03T00:00:00.000+00:00

## Biological Assembly And Chain Mapping

- Biological assembly 1 is the deposited hexameric complex: PCNA trimer A/C/E plus
  p21 peptide chains B/D/F.
- Wave 1 PCNA auth chains: A, C, E.
- p21 peptide chains that must be removed for `1axc_apo_from_p21`: B, D, F.
- PCNA chains map to UniProt P12004 residues 1-261 through `struct_ref_seq`.
- p21 peptide chains map to UniProt P38936 residues 139-160 through `struct_ref_seq`.

## Missing Residues

| Chain | Missing residues |
|---|---|
| A | 107, 108, 187, 188, 189, 190, 256, 257, 258, 259, 260, 261 |
| C | 107, 108, 186, 187, 188, 189, 190, 256, 257, 258, 259, 260, 261 |
| E | 189, 190, 256, 257, 258, 259, 260, 261 |

## Candidate Window Completeness

| Candidate | Residues | Chain completeness |
|---|---:|---|
| T1A-239 | 239-243 | A: complete; C: complete; E: complete |
| T1A-28 | 28-32 | A: complete; C: complete; E: complete |
| T1A-206 | 206-210 | A: complete; C: complete; E: complete |
| T2-134 | 134-138 | A: complete; C: complete; E: complete |

## Alternate Locations And Occupancy

- Alternate-location atom records: 0.
- Atom records with occupancy < 1.0: 0.
- Insertion codes: 0.

## Apo-From-p21 Limitations And Assumptions

- 1AXC is a p21-bound PCNA complex, not a clean apo crystal structure.
- Apo-from-p21 preparation must remove chains B/D/F and record the transformation before any minimization.
- Waters are present in the deposited structure and must be handled by the future setup policy.
- No alternate locations or atom occupancies below 1.0 were detected in atom_site.

- Removing p21 exposes a formerly peptide-bound PIP/IDCL surface; this transformation must be logged as setup, not treated as an experimentally observed apo state.
- The future launch preflight must verify trimer integrity and IDCL/front-face geometry after peptide removal and before production.

## Preparation Decision

1AXC satisfies the Wave 1 residue-window numbering requirement for 239-243, 28-32,
206-210, and 134-138 on all three PCNA chains. Future production remains blocked until
explicit launch authorization and complete manifests exist.

Evidence status: verified from deposited mmCIF/RCSB metadata. Confidence: high for
chain/window facts; no MD outcome claim is made.
