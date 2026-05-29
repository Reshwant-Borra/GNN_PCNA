# Phase 4 Candidate Prioritization — Phase 5 MD Candidates

**Date:** 20260529
**Reclassified:** 20260529 — tier assignments corrected; no scores, residue ranges, or ranking values changed

> **Scope:** These are hypothesis-generating candidate regions for Phase 5 molecular
> dynamics validation. They are NOT validated sites. MD validation is required before
> any scientific claim (governance doc 13).
>
> **Reclassification note:** The initial Phase 4 tier definitions grouped trimer-interface
> candidates (170-174, 175-179, 152-156, 110-114, 145-149, 140-144, 180-184, 185-189)
> into Tier 1 alongside genuinely no-overlap novel candidates. This was a scientific
> classification error. The corrected schema (Tier 1A / 1B / 2 / 3) preserves all
> raw scores and residue assignments while correctly describing the interface context
> of each candidate group. See `gate7_md_decision_draft_20260529.md` for the full
> justification, in particular the explicit Tier 1B inclusion/exclusion rationale.

---

## Corrected Priority Tiers

**Tier 1A — No-interface-overlap candidates:** High max-score regions with NO overlap
with any known interface (PIP-box, IDCL, APIM, trimer interface, AOH1996 contact region).
These are computationally predicted PCNA surface regions with no known functional
annotation. They are NOT validated sites and novelty requires experimental confirmation.

**Tier 1B — Trimer-interface candidates:** High max-score regions overlapping the
head-to-tail subunit-subunit interface of the PCNA homotrimer. Structurally characterized
contact region; mechanistically distinct from front-face (PIP/APIM) interfaces. High
scores likely reflect model sensitivity to trimer-interface geometry. Standard apo MD
of the assembled trimer cannot sample ring-opening events on 100 ns timescales — a
specialized enhanced-sampling protocol is required. **Deferred to MD Wave 2.**

**Tier 2 — Interface-adjacent controls:** High max-score regions overlapping the IDCL,
PIP-box binding site, or APIM site. Expected to score highly. Useful as positive
controls distinguishable from the Tier 3 AOH1996 recovery.

**Tier 3 — Positive control (AOH1996 region):** Regions overlapping the AOH1996
contact region in 8GLA. Recovery is a sanity check confirming the model detects known
cryptic/front-face pocket regions. Does NOT validate novel-site predictions
(governance doc 12). AOH1996/8GLA recovery is ALWAYS framed as positive-control
confirmation, never as evidence of a novel druggable site.

---

## Tier 1A — No-interface-overlap candidates (15 regions)

| Rank | Residues | Max Score | Mean Score | Interface Overlap |
|------|----------|-----------|------------|-------------------|
| 1    | 239-243  | 0.8472    | 0.7117     | none              |
| 2    | 28-32    | 0.8157    | 0.7430     | none              |
| 3    | 206-210  | 0.8087    | 0.6137     | none              |
| 4    | 157-161  | 0.7969    | 0.5705     | none              |
| 5    | 49-53    | 0.7874    | 0.6552     | none              |
| 6    | 64-68    | 0.7841    | 0.7362     | none              |
| 7    | 33-37    | 0.7545    | 0.6637     | none              |
| 8    | 244-248  | 0.7539    | 0.6723     | none              |
| 9    | 69-73    | 0.7303    | 0.6652     | none              |
| 10   | 54-58    | 0.7279    | 0.6625     | none              |
| 11   | 220-224  | 0.7200    | 0.5789     | none              |
| 12   | 192-196  | 0.6998    | 0.6455     | none              |
| 13   | 59-63    | 0.6970    | 0.6346     | none              |
| 14   | 225-229  | 0.6873    | 0.5872     | none              |
| 15   | 211-215  | 0.6872    | 0.6282     | none              |

## Tier 1B — Trimer-interface candidates (specialized MD required, 8 regions)

> **Structural note:** Residues 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183,
> 185 and 153, 154 are canonical trimer-interface residues (inter-subunit heavy-atom
> contacts ≤4.5 Å in PDB 1AXC; derived via `scripts/derive_pcna_interface_contacts.py`).
> These residues are buried in the assembled homotrimer. Standard 100 ns apo MD cannot
> sample ring-opening. These candidates are DEFERRED to MD Wave 2 pending a specialized
> enhanced-sampling pre-registration and separate human decision.

| Rank | Residues | Max Score | Mean Score | Interface Overlap  |
|------|----------|-----------|------------|--------------------|
| 1    | 170-174  | 0.9233    | 0.8681     | trimer_interface   |
| 2    | 175-179  | 0.8892    | 0.8459     | trimer_interface   |
| 3    | 152-156  | 0.8761    | 0.8057     | trimer_interface   |
| 4    | 110-114  | 0.7578    | 0.6187     | trimer_interface   |
| 5    | 145-149  | 0.7224    | 0.6498     | trimer_interface   |
| 6    | 140-144  | 0.7016    | 0.6578     | trimer_interface   |
| 7    | 180-184  | 0.6903    | 0.5645     | trimer_interface   |
| 8    | 185-189  | 0.6873    | 0.6152     | trimer_interface   |

## Tier 2 — Interface-adjacent controls (IDCL / PIP-box / APIM overlap, 1 region)

| Rank | Residues | Max Score | Mean Score | Interface Overlap              |
|------|----------|-----------|------------|--------------------------------|
| 1    | 134-138  | 0.7699    | 0.5868     | idcl, pip_box_binding_site     |

## Tier 3 — Positive control (AOH1996 / 8GLA recovery, 6 regions)

| Rank | Residues | Max Score | Mean Score | Interface Overlap                                              |
|------|----------|-----------|------------|----------------------------------------------------------------|
| 1    | 118-122  | 0.9300    | 0.8199     | aoh1996_contact_region, idcl, pip_box_binding_site             |
| 2    | 23-27    | 0.8354    | 0.7191     | aoh1996_contact_region                                         |
| 3    | 123-127  | 0.7949    | 0.6308     | aoh1996_contact_region, apim_site, idcl, pip_box_binding_site  |
| 4    | 251-255  | 0.7440    | 0.5444     | aoh1996_contact_region, pip_box_binding_site                   |
| 5    | 40-44    | 0.7411    | 0.5991     | aoh1996_contact_region, apim_site, pip_box_binding_site        |
| 6    | 129-133  | 0.7031    | 0.5006     | aoh1996_contact_region, apim_site, idcl, pip_box_binding_site  |

---

## Phase 5 MD Planning Notes

1. **MD Wave 1 recommended targets:** Positive control (118-122) + Tier 1A top-3
   (239-243, 28-32, 206-210) + Tier 2 interface-adjacent control (134-138).
2. **MD Wave 2 (deferred):** Tier 1B candidates (170-174, 175-179, 152-156 and lower).
   Requires specialized enhanced-sampling protocol and separate human decision before any
   simulation runs.
3. MD sampling must follow governance doc 13 (`13_MD_VALIDATION_RULES.md`).
4. No structural or mechanistic claims until MD + human review complete.
5. Full GATE 7 decision package: `reports/phase4/gate7_md_decision_draft_20260529.md`.

---

*Original generation: 2026-05-29T23:06:44.804782+00:00*
*Reclassified: 2026-05-29 — Tier 1 split into Tier 1A (no interface overlap) and Tier 1B
(trimer-interface overlap). No score changes. Authorization: `gate6_authorization_20260529.md`.*
