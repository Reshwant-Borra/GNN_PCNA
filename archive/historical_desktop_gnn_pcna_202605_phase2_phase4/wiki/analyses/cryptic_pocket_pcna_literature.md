---
type: analysis
status: active
created: 2026-05-28
updated: 2026-05-28
tags: [pcna, cryptic-pocket, literature, md, reference]
aliases: [Cryptic Pocket PCNA Literature, PCNA Cryptic Pocket Synthesis]
author: Advay (parallel track 1c)
confidence: high
evidence_status: verified
---

# Cryptic Pockets in PCNA — Literature Synthesis

Concise synthesis (paraphrased, not copied) of published work bearing on cryptic /
non-canonical pockets in PCNA, MD of PCNA dynamics, AOH1996 mechanism, and experimental
PCNA surface-pocket evidence. One entry per finding: paraphrase, citation, **evidence
type**, **confidence**. Claim language follows governance docs 12 and 14.

> **Headline honest finding:** As of this writing there is **no published PCNA-specific
> cryptic-pocket molecular-dynamics study** that I can cite. The known druggable PCNA
> surfaces (T2AA, AOH1996, ATX-101) all engage the **front-face PIP-box / IDCL region**,
> i.e. a *known interaction interface*, not a confirmed novel cryptic pocket. Cryptic-pocket
> MD methodology in the literature is general (other proteins). This gap is exactly what the
> Phase 4 GNN→MD workflow is positioned to probe — and exactly why governance doc 12 forbids
> calling pocket recovery at the front face "novel."

---

## A. PCNA-targeting small molecules / peptides (experimental)

**AOH1996 / AOH1996-1LE (PDB 8GLA).** Gu L et al., *Cell Chem Biol* 2023;30:1235 (PMID
37531956). A small molecule of the AOH1996 series binds cancer-associated PCNA; the 8GLA
co-crystal shows the ligand (code ZQZ) contacting residues that overlap the PIP-box pocket,
IDCL, and C-terminus (residues 23-47, 121-131, 231-234, 250-253; see [[pcna_structure]]).
*Evidence type:* experimental co-crystal + cellular/animal efficacy. *Confidence:* high for
the structure; the binding site overlaps known interfaces, so it is treated here as a
**positive-control region, not a novel cryptic pocket** (doc 12).

**T2AA.** Punchihewa C et al., *J Biol Chem* 2012;287:14289-14300 (PMID 22337872). A
non-peptide T3-derivative that competes with PIP-box peptides for PCNA (IC50 ~1 µM), blocks
PCNA–pol δ on chromatin and stalls replication. *Evidence type:* biochemical + cellular.
*Confidence:* high that it targets the **PIP-box binding site** — a known interface, not a
cryptic pocket.

**ATX-101 (APIM peptide).** Lemech C et al., *Oncogene* 2023;42:541-553
(DOI 10.1038/s41388-022-02582-6); preclinical glioblastoma efficacy PMC8773508. A
cell-penetrating APIM peptide engaging the front-face APIM/PIP pocket; Phase 1 showed
tolerability and signals of activity. *Evidence type:* clinical (Phase 1) + preclinical.
*Confidence:* high that it engages the known pocket; per doc 12 this does **not** prove every
APIM/PIP-adjacent site is druggable.

## B. PCNA conformational dynamics (experimental / computational)

**Solution dynamics by NMR.** De Biasio A et al., *PLoS One* 2012;7:e48390 (PMID 23110233).
Backbone-dynamics measurements identify the **IDCL (117-135) and the C-terminus** as the
most flexible PCNA regions, both involved in partner binding. *Evidence type:* solution NMR.
*Confidence:* high. *Relevance:* the flexible IDCL is the region most likely to gate
front-face pocket accessibility — directly relevant to whether an apo pocket "opens."

**p15/PAF complex and clamp sliding.** De Biasio A et al., *Nat Commun* 2015;6:6439 (PMID
25762514; PDB 4D2G). p15 binds the front face and the work discusses conformational
implications for clamp sliding on DNA. *Evidence type:* crystallography + biophysics.
*Confidence:* high for the structure; sliding-mechanism inferences are model-dependent.

**Trimer architecture.** Krishna TS et al., *Cell* 1994;79:1233-1243 (PMID 8001157, yeast
1PLQ); Gulbis JM et al., *Cell* 1996;87:297-306 (PMID 8861913, human PCNA–p21, 1AXC).
Establish the homotrimeric ring and the front-face/IDCL binding pocket. *Evidence type:*
crystallography. *Confidence:* high (foundational).

## C. Cryptic-pocket methodology (general, NOT PCNA-specific)

These contextualize *how* cryptic pockets are studied; **none is about PCNA**, and they are
cited as methodology only.

**Structural origins of cryptic sites.** Beglov D et al., *PNAS* 2018
(DOI 10.1073/pnas.1711490115). Cryptic sites tend to occur where transient pockets form near
hydrophobic, flexible regions. *Evidence type:* computational survey. *Confidence:* high as
method context.

**Mixed-solvent MD (MixMD) for cryptic/allosteric sites.** Ghanakota P & Carlson HA,
*J Chem Inf Model* 2016 (and related MixMD work). Probe-solvent MD maps latent surface
pockets. *Evidence type:* computational method. *Confidence:* high as method context;
**flagged as a candidate Phase 4 method** if enhanced sampling is needed (governance doc 13
notes cryptic pockets may require enhanced sampling).

**ML cryptic-site prediction (PocketMiner).** Meller A et al., *Nat Commun* 2023;14:1177. A
graph-neural-network predictor of cryptic-pocket-forming residues from a single structure;
it is one of the project's named baselines ([[PocketMiner]]). *Evidence type:* ML method on
benchmark sets. *Confidence:* high as method context; not validated on PCNA here.

## D. Synthesis and Phase 4 implications

1. **Every experimentally engaged PCNA small-molecule/peptide site to date is the front-face
   PIP-box/IDCL region** — a known interface. There is no published, experimentally
   confirmed *novel cryptic pocket* on PCNA distinct from this region that I can cite.
2. **The IDCL/C-terminus flexibility (NMR, De Biasio 2012)** is the most plausible structural
   basis for any "opening" behavior an MD run might show — and is also exactly the region the
   positive control (8GLA) occupies. This makes apo-vs-AOH1996 MD (Track 3) a meaningful but
   **interpretation-sensitive** experiment.
3. **Governance consequence:** a Phase 4 prediction at the front face must be reported as
   "overlaps a known PCNA interaction interface," never "novel cryptic pocket." A genuinely
   novel claim would require a site *away* from the mapped regions in
   `data/registries/pcna_interface_map.json`, plus the full doc-12 audit, MD pre-registration
   (doc 13), and experimental follow-up (doc 14). None of that is asserted here.

## Related

- [[pcna_structure]], [[pcna_binding_partners]], [[AOH1996]], [[8GLA]], [[ATX-101]],
  [[PocketMiner]]
- `data/registries/pcna_interface_map.json`
- Governance: `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`,
  `docs/scientific_governance/13_MD_VALIDATION_RULES.md`,
  `docs/scientific_governance/14_CLAIM_POLICY.md`

## Provenance

- Verified PMIDs: 37531956, 22337872, 23110233, 25762514, 8001157, 8861913, 31134302,
  29633969, 19752023. Method-context papers cited by author/journal/year/DOI.
- Confidence: high. Evidence status: verified against primary sources.
- Date: 2026-05-28.
