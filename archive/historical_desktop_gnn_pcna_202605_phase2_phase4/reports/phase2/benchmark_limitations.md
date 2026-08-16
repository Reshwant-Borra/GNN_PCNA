# Benchmark Limitations Review

Date: 2026-05-27
Created by: Codex
Status: DRAFT - no benchmark adopted

## Scope

This file records limitations that must be resolved before adopting CryptoBench or auxiliary datasets for Phase 2.

## Benchmark Candidates

| Candidate | Source lead | Status | Current limitation |
|---|---|---|---|
| CryptoBench | `crawls/pcna-dataset-repositories-pass9/` | candidate | File inventory, license, label schema, and leakage status unknown. |
| BioLiP/BioLiP2 | `crawls/pcna-curated-official-tools-data-structures-pass8/` | candidate/background | Binding-site annotations may be proxy labels, not cryptic-pocket truth. |
| scPDB | `crawls/pcna-curated-official-tools-data-structures-pass8/` | candidate/background | Ligand-binding site labels require scope and proxy-label review. |
| PDBbind | `crawls/pcna-curated-official-tools-data-structures-pass8/` | candidate/background | Affinity/database scope may drift from residue-level pocket prediction. |
| ASD | `crawls/pcna-curated-official-tools-data-structures-pass8/` | candidate/background | Allosteric entries require PCNA relevance and schema review. |

## Required Checks Before Adoption

| Check | CryptoBench | Auxiliary datasets |
|---|---|---|
| Label generation method known | FAIL | FAIL |
| Label type classified | FAIL | FAIL |
| Residue-level compatibility known | FAIL | FAIL |
| Apo/holo grouping known | FAIL | FAIL |
| Homolog leakage audit possible | FAIL | FAIL |
| PCNA/homolog contamination checked | FAIL | FAIL |
| License/access recorded | FAIL | FAIL |
| Biases documented | FAIL | FAIL |

## Current Decision

No benchmark is adopted. All candidates remain source leads until audited.

## Related Governance

- `docs/scientific_governance/29_BENCHMARK_LIMITATIONS.md`
- `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`
- `docs/scientific_governance/05_SPLIT_PROTOCOL.md`
- `docs/scientific_governance/06_LABELING_RULES.md`

## Conclusion

Benchmark limitations are identified but unresolved. The project may plan dataset verification, but it is not ready for dataset adoption or training.
