# Split Freeze Plan

Date: 2026-05-27
Created by: Codex
Status: DRAFT - no split frozen

## Rule

Split before graph generation. No training, graph generation, or evaluation may happen until split assignment is frozen with human review.

## Planned Artifacts

- Split assignment template: `data/splits/phase2_split_TEMPLATE.json`
- Future frozen split: `data/splits/phase2_split_<YYYYMMDD>_<hash>.json`
- Split audit: `reports/phase2/split_audit.md`
- Human review log: `reports/phase2/human_review_log.md`

## Required Decisions Before Freeze

| Decision | Status | Blocker |
|---|---|---|
| Dataset items accepted | blocked | No dataset adopted. |
| Sequence clustering tool/version | open | Tool and threshold not chosen. |
| Sequence identity threshold | open | Requires scientific decision. |
| Structural similarity review method | open | Requires scientific decision. |
| Apo/holo grouping method | open | Requires source records. |
| PCNA final holdout list | open | Requires human scientific decision. |
| 8GLA/AOH1996 positive-control status | open | Requires leakage status. |

## Human Gate

Required gate: Split freeze.

Decision ID placeholder: `HR-SPLIT-001`

Required evidence packet:

- dataset registry
- source audit
- benchmark limitations
- sequence cluster table
- apo/holo grouping table
- PCNA isolation statement
- positive-control status for 8GLA/AOH1996

## Current Readiness

Split readiness: FAIL. The plan exists, but no split can be frozen yet.
