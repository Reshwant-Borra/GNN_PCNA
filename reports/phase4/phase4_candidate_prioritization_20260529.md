# Phase 4 Candidate Prioritization — Phase 5 MD Candidates

**Date:** 20260529

> **Scope:** These are hypothesis-generating candidate regions for Phase 5
> molecular dynamics validation. They are NOT validated sites.
> MD validation is required before any scientific claim (governance doc 13).

## Priority tiers

**Tier 1 (Primary MD targets):** High max-score regions that do NOT overlap
known PIP-box / IDCL / AOH1996 contact region — potential novel surface regions.

**Tier 2 (Interface-adjacent):** High max-score regions overlapping known
interfaces — useful for positive-control MD validation.

**Tier 3 (Positive control):** 8GLA-region recovery for model sanity check.

## Tier 1 — Potential novel surface regions (23 regions)

| Rank | Residues | Max Score | Mean Score | Interface Overlap |
|------|----------|-----------|------------|-------------------|
| 1 | 170-174 | 0.9233 | 0.8681 | trimer_interface |
| 2 | 175-179 | 0.8892 | 0.8459 | trimer_interface |
| 3 | 152-156 | 0.8761 | 0.8057 | trimer_interface |
| 4 | 239-243 | 0.8472 | 0.7117 | none |
| 5 | 28-32 | 0.8157 | 0.7430 | none |
| 6 | 206-210 | 0.8087 | 0.6137 | none |
| 7 | 157-161 | 0.7969 | 0.5705 | none |
| 8 | 49-53 | 0.7874 | 0.6552 | none |
| 9 | 64-68 | 0.7841 | 0.7362 | none |
| 10 | 110-114 | 0.7578 | 0.6187 | trimer_interface |
| 11 | 33-37 | 0.7545 | 0.6637 | none |
| 12 | 244-248 | 0.7539 | 0.6723 | none |
| 13 | 69-73 | 0.7303 | 0.6652 | none |
| 14 | 54-58 | 0.7279 | 0.6625 | none |
| 15 | 145-149 | 0.7224 | 0.6498 | trimer_interface |
| 16 | 220-224 | 0.7200 | 0.5789 | none |
| 17 | 140-144 | 0.7016 | 0.6578 | trimer_interface |
| 18 | 192-196 | 0.6998 | 0.6455 | none |
| 19 | 59-63 | 0.6970 | 0.6346 | none |
| 20 | 180-184 | 0.6903 | 0.5645 | trimer_interface |
| 21 | 225-229 | 0.6873 | 0.5872 | none |
| 22 | 185-189 | 0.6873 | 0.6152 | trimer_interface |
| 23 | 211-215 | 0.6872 | 0.6282 | none |

## Tier 2 — Interface-adjacent regions (1 regions)

| Rank | Residues | Max Score | Mean Score | Interface Overlap |
|------|----------|-----------|------------|-------------------|
| 1 | 134-138 | 0.7699 | 0.5868 | idcl, pip_box_binding_site |

## Tier 3 — Positive control (6 regions)

| Rank | Residues | Max Score | Mean Score | Interface Overlap |
|------|----------|-----------|------------|-------------------|
| 1 | 118-122 | 0.9300 | 0.8199 | aoh1996_contact_region, idcl, pip_box_binding_site |
| 2 | 23-27 | 0.8354 | 0.7191 | aoh1996_contact_region |
| 3 | 123-127 | 0.7949 | 0.6308 | aoh1996_contact_region, apim_site, idcl, pip_box_binding_site |
| 4 | 251-255 | 0.7440 | 0.5444 | aoh1996_contact_region, pip_box_binding_site |
| 5 | 40-44 | 0.7411 | 0.5991 | aoh1996_contact_region, apim_site, pip_box_binding_site |
| 6 | 129-133 | 0.7031 | 0.5006 | aoh1996_contact_region, apim_site, idcl, pip_box_binding_site |

## Next steps

1. Select Tier 1 + Tier 2 regions for Phase 5 MD sampling.
2. MD sampling must follow governance doc 13 (MD_VALIDATION_RULES).
3. No structural or mechanistic claims until MD + human review.

---
*Generated: 2026-05-29T23:06:44.804782+00:00*
*Authorization: `C:\Users\reshw\Desktop\GNN_PCNA\reports\phase4\gate6_authorization_20260529.md`*