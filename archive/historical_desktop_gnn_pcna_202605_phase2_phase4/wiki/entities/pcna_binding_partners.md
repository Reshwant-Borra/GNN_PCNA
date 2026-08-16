---
type: entity
status: active
created: 2026-05-28
updated: 2026-05-28
tags: [entity, pcna, binding-partners, interfaces, reference]
aliases: [PCNA Binding Partners, PCNA Interaction Partners]
author: Advay (parallel track 1b)
confidence: high
evidence_status: verified
---

# PCNA Binding Partners Catalog

Catalog of structurally characterized human PCNA interaction partners, for cross-checking
whether Phase 4 predictions overlap **known** PCNA interfaces or fall on **unmapped**
surface. **Every entry cites a PDB structure and/or a PMID.** No partner or residue is
invented. Use with `data/registries/pcna_interface_map.json` and
`scripts/check_prediction_overlap.py`.

## Key fact: most partners share one front-face pocket

Canonical PIP-box (PIPM) partners — and APIM partners, now classed as non-canonical PIPMs —
dock the **same** front-face hydrophobic pocket: PCNA residues **40-44, 117-135 (IDCL),
230-235, 251-253** (Müller R et al., *Cell Mol Life Sci* 2019;76:4923-4943, PMID 31134302;
APIM-pocket equivalence: Hara K et al., *Acta Crystallogr F* 2018, PMID 29633969). So a
prediction landing in that pocket overlaps *many* known partners at once and is **not** a
novel site (governance doc 12).

## Catalog

| Partner protein | Motif type | PCNA residues involved | PDB ID | Citation (PMID) | Relevance to cryptic-pocket hypothesis |
|---|---|---|---|---|---|
| p21 / CDKN1A (CIP1/WAF1) | PIP-box | Front-face PIPM pocket: 40-44, 117-135, 230-235, 251-253 (high-affinity PIP-box; peptide also reaches across surface) | 1AXC | 8861913 (Gulbis 1996) | **Known site.** Defining human PIP-box complex; the canonical PIPM pocket. |
| FEN1 (flap endonuclease 1) | PIP-box | Front-face PIPM pocket (FEN1 res 331-350 PIP-box) | 1U7B | 15576034 (Bruning & Shamoo 2004) | **Known site.** Replication/repair partner; same pocket. |
| DNA pol δ subunit p66 / POLD3 | PIP-box | Front-face PIPM pocket (p66 PIP-box peptide) | 1U76 | 15576034 (Bruning & Shamoo 2004) | **Known site.** Replicative polymerase tethering; same pocket. |
| p15 / PAF (PCLAF, KIAA0101; UniProt Q15004) | PIP-box | Front-face PIPM pocket; "tightly bound to the front-face of PCNA" | 4D2G | 25762514 (De Biasio 2015) | **Known site.** Implicated in clamp sliding; same pocket. |
| ALKBH2 (AlkB homolog 2) | APIM | APIM site = same front-face pocket (40, 47, 126-129, 233, 234) | (no complex PDB in this set) | 19752023 (Gilljam 2009) | **Known site.** Motif-defining APIM partner; APIM = non-canonical PIPM. |
| APIM consensus peptide | APIM | 40, 47, 126, 127, 128, 129, 233, 234 | 5YD8 | 29633969 (Hara 2018) | **Known site.** Shows APIM occupies the PIP-box pocket. |
| AOH1996-1LE (small molecule; AOH1996 series) | small-molecule ligand (not a peptide motif) | ZQZ contacts: 23, 25-27, 38-41, 44-47, 121, 123-126, 128, 129, 131, 231-234, 250-253 | 8GLA | 37531956 (Gu 2023) | **Positive-control region** overlapping the PIPM pocket/IDCL/C-terminus. Recovery is a sanity check, never novel-site validation (doc 12). |
| ATX-101 (APIM-based therapeutic peptide) | APIM (derived) | Engages the APIM/PIP front-face pocket (no deposited PCNA co-structure in this set) | (none in set) | DOI 10.1038/s41388-022-02582-6 (Phase 1, 2023); PMC8773508 (preclinical) | APIM-derived PCNA-targeting agent; engageability of the pocket ≠ druggability of every predicted pocket (doc 12). |

### Notes on coverage and honesty

- Several registry structures are PCNA–partner complexes corroborating the table: 1AXC
  (p21), 1U7B (FEN1), 1U76 (p66), 4D2G (p15), 5YD8 (APIM). Their presence is recorded in
  `data/registries/friend_crawl_registry.json`.
- "Front-face PIPM pocket" is used where a partner binds the canonical pocket but a
  partner-specific per-residue contact list was not separately re-derived here; the pocket
  residues are the literature set (Müller 2019, PMID 31134302). Per-structure contacts can
  be re-derived with `scripts/derive_pcna_interface_contacts.py` if needed.
- This catalog is **not exhaustive** — PCNA has >200 candidate APIM partners alone (Gilljam
  2009) and many more PIP-box partners (DNMT1, CDT1, LIG1, MSH3/6, XPG, etc.). Only
  structurally/citation-anchored entries are listed to avoid invented assignments.

## Related

- [[pcna_structure]], [[cryptic_pocket_pcna_literature]], [[PCNA]]
- `data/registries/pcna_interface_map.json`, `scripts/check_prediction_overlap.py`
- Governance: `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`

## Provenance

- PDB/PMID anchored: 1AXC (8861913), 1U7B & 1U76 (15576034), 4D2G (25762514), 5YD8
  (29633969), 8GLA (37531956); ALKBH2/APIM (19752023); ATX-101 (10.1038/s41388-022-02582-6,
  PMC8773508); pocket residues (31134302).
- Confidence: high. Evidence status: verified.
- Date: 2026-05-28.
