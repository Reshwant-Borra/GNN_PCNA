# Label Freeze Plan

Date: 2026-05-27
Created by: Codex
Status: DRAFT - no label definition frozen

## Rule

Exact label definitions are required before preprocessing. No labels may be generated or used until the label definition is reviewed and frozen.

## Planned Artifacts

- Label manifest template: `data/labels/phase2_labels_TEMPLATE.json`
- Future frozen label manifest: `data/labels/phase2_labels_<hash>.json`
- Label audit: `reports/phase2/label_audit.md`
- Human review log: `reports/phase2/human_review_log.md`

## Required Decisions Before Freeze

| Decision | Status | Blocker |
|---|---|---|
| Label type | open | Curated cryptic pocket vs ligand-proximity vs interface vs positive-control labels not chosen. |
| Atom basis | open | C-alpha, side-chain heavy atom, all heavy atom, ligand heavy atom, or curated annotation not chosen. |
| Distance threshold | open | No threshold approved. |
| Ambiguous residue handling | open | Mask/exclude/assign rule not approved. |
| Ligand inclusion/exclusion | open | Biological ligands/additives/waters/ions rules not approved. |
| PCNA positive-control label handling | open | 8GLA/AOH1996 status unresolved. |

## Human Gate

Required gate: Label freeze.

Decision ID placeholder: `HR-LABEL-001`

Required evidence packet:

- dataset registry
- source audit
- benchmark limitations
- label definition
- label reproducibility plan
- biological data sanity review

## Current Readiness

Label readiness: FAIL. The plan exists, but no label definition can be frozen yet.
