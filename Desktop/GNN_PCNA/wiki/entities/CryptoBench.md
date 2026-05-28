---
type: entity
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [entity, benchmark, dataset]
aliases: [CryptoBench]
confidence: medium
evidence_status: verified_for_local_schema_uncertain_for_use
---

# CryptoBench

## What it is

A candidate cryptic-pocket benchmark/source acquired into quarantined raw intake and audited locally for schema, split risk, labels, structures, and PCNA contamination.

## Why it matters for GNN-PCNA

Could provide benchmark data, but only after file inventory, license, label schema, and leakage risks are audited.

## How Codex should use this entity

Treat as an audited but not adopted benchmark candidate. It may support human dataset review and further leakage/label/graph feasibility analysis only.

## What Codex must NOT overclaim

Do not assume CryptoBench labels are true negatives, leakage-free, PCNA-safe, or directly compatible with Phase 2. Do not use the official folds as frozen Phase 2 splits without human review and sequence/homolog clustering.

## Local deep audit findings

- `dataset.json` contains 1,107 apo PDB keys and 5,493 apo-holo cryptic pocket records.
- Cryptic records reference 5,005 unique structures, all present in `cif-files.zip`; all 5,005 required CIF files are readable and expose atom-site loops.
- `noncryptic-pockets.json` contains 14,493 auxiliary noncryptic pocket records, but 6,915 referenced noncryptic auxiliary structures are not present in the local ZIP.
- Labels are pocket residue selection tokens inside apo-holo records, not a dense residue-label table and not explicit true-negative labels.
- Fold files match `folds.json` by apo ID, with no exact UniProt overlap across folds detected, but 6 holo PDB IDs repeat across folds and no local sequence/homolog cluster proof exists.
- Exact PCNA contamination is present: apo `5e0v` in the test fold pairs with holo `3vkx`, UniProt `P12004`, ligand `T3`; CIF text also flags `3vkx` and `5e0v` as PCNA and `2xur`/`3bep` as sliding-clamp related.
- 721 selected residue tokens were absent from parsed atom-site residue IDs in the lightweight audit, so residue numbering/missing-residue policy requires review before graph generation.

## Related governance docs

- `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`
- `docs/scientific_governance/05_SPLIT_PROTOCOL.md`
- `docs/scientific_governance/06_LABELING_RULES.md`
- `docs/scientific_governance/29_BENCHMARK_LIMITATIONS.md`

## Related wiki concepts

- [[Dataset Registry]]
- [[Label Definition]]
- [[Sequence Split Leakage]]
- [[Apo Holo Leakage]]

## Related raw crawl/source paths

- `crawls/pcna-dataset-repositories-pass9/SOURCE_INDEX.md`

## Related V1 references, if any

None canonical.

## Known risks / failure modes

Proxy label semantics, hidden homolog leakage, repeated holo PDB IDs across folds, explicit PCNA test-fold contamination, missing noncryptic auxiliary structures, residue-token mismatches, and unresolved true-negative semantics.

## Open questions

- Should Phase 2 exclude or isolate the PCNA record `5e0v`/`3vkx` before any split freeze?
- Should noncryptic auxiliary records be used at all, given missing referenced CIFs?
- What reviewed rule should handle the 721 selected residue tokens absent from parsed atom-site residue IDs?

## Provenance

- Source paths: governance docs above; crawl path above; `reports/phase2/cryptobench_schema_deep_audit.md`; `reports/phase2/cryptobench_split_risk_audit.md`; `reports/phase2/cryptobench_label_semantics.md`; `reports/phase2/cryptobench_structure_inventory.md`; `reports/phase2/pcna_contamination_screen.md`; `data/registries/cryptobench_schema_summary.json`; `data/registries/cryptobench_fold_summary.json`; `data/registries/cryptobench_structure_index.json`
- Confidence level: high for local audit counts/readability; medium for label-semantics interpretation; low for homolog exclusion.
- Evidence status: verified for local files and machine checks; inferred for biological meaning; uncertain for final scientific usability.
- Date last updated: 2026-05-27
