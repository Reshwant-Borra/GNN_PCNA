# Dataset Registry

Date created: 2026-05-27
Created by: Codex
Status: TEMPLATE - no dataset adopted

## Rule

No data may be used for graph generation, training, evaluation, MD interpretation, or claims unless it has a complete registry entry, lifecycle status, source provenance, split assignment, label definition, and required human review.

## Dataset Entries

No dataset is adopted yet.

## Candidate Dataset Template

```markdown
## Dataset: <name>
- Dataset ID:
- Lifecycle status: candidate | accepted | excluded | quarantined | deprecated | superseded | historical_reference_only
- Source:
- Source registry ID:
- Download/access method:
- License/citation:
- Biological system:
- Structure IDs:
- Chain IDs:
- Target chains:
- Non-target protein chains:
- DNA/RNA chains:
- Ligands:
- Label definition:
- Label type:
- Preprocessing steps:
- Split assignment:
- Leakage risks:
- Apo/holo grouping:
- Sequence cluster:
- Structural similarity notes:
- Provenance hashes:
- Owner:
- Human review decision ID:
- Review status:
```

## Candidate Leads To Review

| Candidate | Source registry ID | Current status | Required next step |
|---|---|---|---|
| CryptoBench | CRAWL-013 | candidate | Verify file inventory, license, label schema, and leakage risks. |
| BioLiP/BioLiP2 | CRAWL-012 | candidate/background | Decide whether source is in scope or background only. |
| scPDB | CRAWL-012 | candidate/background | Decide whether source is in scope or background only. |
| PDBbind | CRAWL-012 | candidate/background | Decide whether source is in scope or background only. |
| ASD | CRAWL-012 | candidate/background | Decide whether source is in scope or background only. |
| PCNA PDB/UniProt probes | CRAWL-003, CRAWL-010 | candidate/context | Verify official PDB/UniProt records and PCNA holdout/control status. |

## Required Governance

- `04_DATASET_CONSTRAINTS.md`
- `05_SPLIT_PROTOCOL.md`
- `06_LABELING_RULES.md`
- `15_PROVENANCE_AND_REPRODUCIBILITY.md`
- `29_BENCHMARK_LIMITATIONS.md`
- `31_DATA_LIFECYCLE_TRACKING.md`

## Current Readiness

Dataset readiness: FAIL. Registry template exists, but no dataset has been accepted.
