---
type: concept
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [concept, labels, proxy-risk]
aliases: [Proxy Ligand Labels]
confidence: high
evidence_status: verified
---

# Proxy Ligand Labels

## Definition

Labels derived from ligand proximity, ligand contacts, or binding-site annotations that may only approximate the desired biological concept.

## Why it matters for GNN-PCNA

Cryptic-pocket truth cannot be assumed from ligand proximity alone.

## How it can go wrong

A model can learn ligand/structure artifacts while reports claim cryptic or allosteric biology.

## Governance rules that apply

`06_LABELING_RULES.md`, `11_BIOLOGICAL_REALISM_RULES.md`, `14_CLAIM_POLICY.md`.

## Coding implications

Store proxy labels with explicit label type and claim limitations.

## Related entities

[[BioLiP]], [[scPDB]], [[PDBbind]], [[8GLA]]

## Related raw crawl/source paths

`crawls/pcna-curated-official-tools-data-structures-pass8/`

## Related implementation files, if any

None canonical yet.

## Verification questions Codex should ask

- What exactly makes a residue positive?
- Is this proxy label allowed for training or only analysis?

## Open questions

- Which proxy labels, if any, are approved?

## Provenance

- Source paths: governance docs above
- Confidence level: high
- Date last updated: 2026-05-27
