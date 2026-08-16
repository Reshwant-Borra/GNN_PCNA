---
type: entity
status: active
created: 2026-05-28
updated: 2026-05-28
tags: [entity, pcna, structure, biology, reference]
aliases: [PCNA Structure, PCNA Structural Biology]
author: Advay (parallel track 1a)
confidence: high
evidence_status: verified
---

# PCNA Structural Biology

Reference page for interpreting Phase 4 PCNA predictions against known structure and
biology. **Every residue number on this page is cited to a PDB structure or a PMID.** No
biology is invented. Claim language follows governance docs 12 and 14.

> Scope note: This is a reference page, not a results page. It makes no prediction and no
> therapeutic claim. See [[pcna_binding_partners]] and the machine-readable
> `data/registries/pcna_interface_map.json`.

## 1. PCNA is a homotrimeric sliding clamp (not a monomer)

Human PCNA (UniProt **P12004**, **261 aa**) assembles into a **homotrimer** that encircles
duplex DNA as a ring-shaped sliding clamp; each protomer has two topologically identical
domains and the three subunits associate head-to-tail to close the ring (Krishna TS et al.,
*Cell* 1994;79:1233-1243, PMID 8001157, yeast PCNA; human PCNA trimer in Gulbis JM et al.,
*Cell* 1996;87:297-306, PMID 8861913). Phase 4 interpretation must treat PCNA as a trimer:
chain identity and biological assembly must be resolved before any per-residue prediction is
read (governance doc 12, structural-mapping checklist).

- UniProt canonical numbering: **P12004, residues 1-261**. Ordered residues in the crystal
  structures used here span ~1-255; the C-terminal tail is frequently disordered.
- PDB author numbering for the human PCNA entries used in this project (1AXC, 8GLA, 5YD8,
  5E0V) follows UniProt P12004 numbering.

## 2. The three main functional regions

### 2a. PIP-box binding site (front-face hydrophobic pocket)

Canonical PIP-box (PIP-motif, "PIPM") partners bind a front-face hydrophobic pocket formed
by residues **40-44, 117-135 (the IDCL), 230-235, and 251-253** (Müller R et al., *Cell Mol
Life Sci* 2019;76:4923-4943, PMID 31134302). The defining human structure is the
PCNA–p21 complex, PDB **1AXC** (Gulbis 1996, PMID 8861913), in which the p21 C-terminal
PIP-box peptide (p21 residues 143-160) binds this pocket. Structurally derived PCNA contacts
to the p21 peptide in 1AXC (heavy-atom ≤4.5 Å, this work; reproduce via
`scripts/derive_pcna_interface_contacts.py`) span residues 40, 43-47, 118-129, 131, 133,
232-234, 250-255, plus extended surface contacts (27, 29, 67-69, 96, 97, 208, 211) because
the p21 peptide reaches across the PCNA surface (Gulbis 1996).

### 2b. APIM site

The AlkB-homologue-2 PCNA-Interacting Motif (APIM), consensus **(K/R)-(F/Y/W)-(L/I/V/A)-
(L/I/V/A)-(K/R)**, was identified as a second widespread PCNA-binding motif (Gilljam KM
et al., *J Cell Biol* 2009;186:645-654, PMID 19752023). Structurally, an APIM peptide binds
the **same** front-face pocket as the PIP-box: PCNA residues **Met40, Leu47, Leu126, Gly127,
Ile128, Pro129, Val233, Pro234** (PDB **5YD8**; Hara K et al., *Acta Crystallogr F*
2018;74:214-221, PMID 29633969), which classified APIM as a non-canonical PIPM subgroup
rather than a structurally distinct site. **The APIM site overlaps the PIP-box site; it is
not an independent surface.**

### 2c. Interdomain connecting loop (IDCL)

The IDCL is the flexible loop linking the two PCNA domains, **residues 117-135** (Müller
2019, PMID 31134302). It forms part of the PIPM binding pocket and is a primary recognition
element for PCNA partners. (The Track-1 brief's "~119-133" is a subset of this range.) The
IDCL and C-terminus are among the most flexible PCNA regions in solution NMR (De Biasio A
et al., *PLoS One* 2012;7:e48390, PMID 23110233).

## 3. Trimer interface residues

The ring-closing, head-to-tail subunit interface buries a β-sheet contact surface.
Structurally derived inter-subunit contacts among the PCNA trimer chains A/C/E of PDB 1AXC
(heavy-atom ≤4.5 Å, this work) cover residues **74, 77, 78, 80-83, 108-117, 143, 146, 147,
149-151, 153, 154, 173-183, 185** (reproduce via `scripts/derive_pcna_interface_contacts.py`;
underlying trimer architecture established in Krishna 1994 PMID 8001157 and Gulbis 1996 PMID
8861913). Predictions overlapping these residues carry **trimer-interface risk** (a pocket
predicted at a buried oligomerization interface may be a crystal/assembly artifact;
governance doc 12).

## 4. AOH1996 / 8GLA — positive control, NOT proof of a novel site

PDB **8GLA** is the co-crystal of cancer-associated PCNA with the AOH1996 derivative
**AOH1996-1LE** (ligand code **ZQZ**), 3.77 Å (Gu L et al., *Cell Chem Biol* 2023;30:1235,
PMID 37531956). PCNA residues contacting ZQZ (heavy-atom ≤4.5 Å, this work) are **23, 25-27,
38-41, 44-47, 121, 123-126, 128, 129, 131, 231-234, 250-253**. This region **substantially
overlaps the PIP-box pocket, the IDCL, and the C-terminus** (shared residues include 40,
44-47, 121, 123-126, 128, 129, 131, 232-234, 250-253), and the ZQZ ligand contacts residues
across two PCNA chains in 8GLA.

**Governance framing (doc 12):** 8GLA/AOH1996 is a **positive control / sanity check only**.
Recovering this region indicates "positive-control recovery of the AOH1996/8GLA region" and
"overlap with a known PCNA interaction interface" — it does **not** validate a novel-site
prediction, and 8GLA may have influenced any prior pipeline, so its recovery is not
independent validation.

## 5. ATX-101 — evidence framing (what it does and does not mean)

ATX-101 is a cell-penetrating peptide built around the **APIM** motif that targets PCNA and
has entered clinical study (Phase 1: Lemech C et al., *Oncogene* 2023;42:541-553, PMID via
DOI 10.1038/s41388-022-02582-6; preclinical glioblastoma efficacy: PMC8773508). Per
governance doc 12, ATX-101 must be framed as **an APIM-derived PCNA-targeting agent**. Its
existence shows the APIM/PIP front-face pocket is engageable by a peptide — it does **not**
prove that "every APIM/PIP-adjacent site is druggable," and it does not establish that any
GNN-predicted PCNA pocket is a drug target.

## 6. Allowed and forbidden claim language (copied from governance doc 12)

**Allowed PCNA claim language:**
- "candidate PCNA cryptic pocket region"
- "computationally predicted PCNA surface region"
- "overlaps a known PCNA interaction interface"
- "positive-control recovery of the AOH1996/8GLA region"
- "hypothesis-generating site for follow-up"

**Forbidden PCNA claim language:**
- "validated PCNA drug target"
- "new therapeutic site"
- "confirmed resistance-proof pocket"
- "AOH1996 mechanism proven by the model"
- "ATX-101 proves this site is druggable"
- "PCNA cancer relevance proves clinical actionability"

## Related

- [[pcna_binding_partners]], [[cryptic_pocket_pcna_literature]], [[PCNA]], [[8GLA]],
  [[AOH1996]], [[ATX-101]], [[UniProt_P12004]]
- Machine-readable: `data/registries/pcna_interface_map.json`
- Governance: `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`,
  `docs/scientific_governance/14_CLAIM_POLICY.md`

## Provenance

- Residue numbers sourced from: PDB 1AXC (PMID 8861913), 8GLA (PMID 37531956), 5YD8
  (PMID 29633969); UniProt P12004; Müller 2019 (PMID 31134302); Gilljam 2009 (PMID
  19752023); Krishna 1994 (PMID 8001157); De Biasio 2012 (PMID 23110233).
- Structurally derived lists reproduce via `scripts/derive_pcna_interface_contacts.py`.
- Confidence: high. Evidence status: verified against primary sources.
- Date: 2026-05-28.
