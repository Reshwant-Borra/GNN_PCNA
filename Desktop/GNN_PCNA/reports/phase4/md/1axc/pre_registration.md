# MD Pre-Registration — 1AXC (top non-control candidate)

> Pre-registered per `docs/scientific_governance/13_MD_VALIDATION_RULES.md` **before** any
> simulation. Written 2026-05-28 by Advay (parallel track 3c). Hypothesis registration, not
> a result and not a claim. Setup values PROPOSED; must match the 8GLA / 5E0V systems (doc 13).
>
> **Required statement (doc 13):** MD can support, weaken, redirect, or falsify the working
> hypothesis. All outcomes are evidence.

## How this candidate was selected (and an honest caveat)

1AXC is the **rank-2 entry and top `candidate`-role structure** in
`data/registries/phase4_candidate_manifest.json` (rank 1 is the 8GLA positive control). It
was selected by the deterministic Track-2 rule: has_ligand + highest `heuristic_pocket_score`
(0.1147) among quality-passing structures, resolution 2.60 Å.

**Caveat (do not skip):** 1AXC is itself the canonical **PCNA–p21 PIP-box complex** (Gulbis
JM et al., *Cell* 1996;87:297-306, PMID 8861913); its "ligand" is the p21 peptide and its
elevated heuristic score plausibly reflects the **occupied front-face PIP-box pocket**, not a
novel cryptic site. So its MD hypothesis is necessarily about **front-face pocket persistence
after peptide removal**, which overlaps the 8GLA theme. A cleaner "unknown candidate" for a
genuinely cryptic-pocket question would be a high-resolution structure with no front-face
partner — e.g. **8F5Q** (rank 3, 1.90 Å, no heuristic score). This limitation arises because
only 4 of 72 structures carry heuristic scores and 3 of those are known complexes (see
`reports/phase4/heuristic_score_analysis.md`). Recorded for Reshwant's selection decision.

## System
- Structure: PDB **1AXC** — human PCNA homotrimer (chains A/C/E) + p21 C-terminal PIP-box
  peptide (chains B/D/F, p21 res 143-160). Resolution 2.60 Å. PMID 8861913.
- Chains: PCNA homotrimer A/C/E. Two systems: **(i) holo** (p21 peptide retained),
  **(ii) apo-from-holo** (p21 removed).
- Ligand/docked molecule: p21 PIP-box peptide (a peptide partner, not a small molecule).
- Force field: PROPOSED AMBER ff19SB — confirm; identical across systems.
- Water/ions: PROPOSED TIP3P, 150 mM NaCl — confirm.
- Protonation policy: PROPOSED pH 7.4 standard states; identical across systems.
- Duration and replicates: PROPOSED ≥3 × 100 ns replicates per system.
- Random seeds: record per replicate in MANIFEST.md.

## Hypothesis
After removing the p21 peptide, does the front-face PIP-box pocket (40-44, 117-135, 230-235,
251-253) **remain accessible** or collapse? Compared against the 5E0V apo-WT reference and the
8GLA AOH1996 system (identical setup), this probes whether the heuristic-high 1AXC pocket is a
stable surface feature.

## Expected observations
If a stable pocket, apo-from-holo 1AXC retains partial pocket volume at the IDCL/40-47 patch
with elevated IDCL flexibility; if induced by p21, the pocket contracts.

## Alternative outcomes
Pocket collapse (peptide-induced fit); full persistence (stable site); transient
opening/closing (cryptic/dynamic).

## Interpretation if pocket does not open
Valid result: "under the tested setup the 1AXC front-face pocket did not persist after p21
removal." No druggability claim.

## Interpretation if pocket opens
"Supportive computational evidence that the 1AXC front-face pocket can remain accessible
without the p21 peptide under the tested setup." This **overlaps a known PCNA interaction
interface** and is NOT a novel-site claim (doc 12).

## Interpretation if simulation is unstable
Archive as exploratory only; no claims; re-examine setup (doc 13).

## Claim allowed if positive
"Supportive MD evidence for accessibility of a known PCNA front-face interface under the
tested setup; hypothesis-generating; overlaps known PIP-box interface; requires experimental
validation." (doc 12/14 allowed wording.)

## Claim allowed if negative
"Under the tested setup, MD did not support persistent apo accessibility of the 1AXC
front-face pocket." Negative results valid.

## Metrics
- RMSD: backbone per chain vs. start.
- RMSF: per residue; IDCL (117-135), C-terminus.
- Pocket volume: front-face PIP/IDCL region time series.
- DCCM: inter-domain/inter-subunit correlations.
- Interface distances: 40-47 / IDCL / 250-253 pocket-framing distances.
- Ligand stability/contact persistence: p21 peptide contact persistence (holo system).

## Provenance
- Structure: `data/registries/friend_crawl_registry.json` (1AXC). Selection:
  `data/registries/phase4_candidate_manifest.json` (rank 2, top candidate). Interface
  residues: `data/registries/pcna_interface_map.json`. Identity: PMID 8861913.
- Status: PRE-REGISTRATION ONLY. No simulation run. No claims.
