# CryptoBench Leakage Remediation

## Current Status

- Official folds are not Phase 2-freezable.
- Exact apo IDs do not overlap across folds.
- Exact UniProt IDs shared across folds: 0.
- Holo PDB IDs repeated across folds: 6.
- Homolog leakage remains unresolved because no approved sequence clustering has been run.

## Repeated Holo PDB IDs Across Folds

| Holo PDB | Folds | Apo IDs |
| --- | --- | --- |
| 2fzc | test, train-1 | 2air, 9atc |
| 2fzg | test, train-1 | 2air, 9atc |
| 4f04 | test, train-1 | 2air, 9atc |
| 5qya | test, train-0 | 3e9p, 4ilg |
| 6a5y | train-1, train-3 | 4n5g, 6hl0 |
| 7fo6 | test, train-0 | 3e9p, 4ilg |

## Required Remediation

- Build a system grouping key from UniProt ID, apo PDB, holo PDB, ligand, apo/holo pair, and sequence cluster.
- Run sequence clustering before split assignment; a tool and threshold still require human approval.
- Group all apo/holo records and ligand variants for a protein system into one split.
- Isolate PCNA and PCNA-like sliding clamps from model development.
- Treat official folds as source metadata only unless they pass the stricter Phase 2 leakage audit.

## Structure Similarity Planning

- Use structural review only after sequence grouping to catch remote homologs and sliding-clamp-like structures.
- Candidate methods: Foldseek/DALI-style review if available, or documented manual review for PCNA/sliding-clamp hits.
- No structure-similarity threshold is frozen in this packet.

## Provenance

- Date: 2026-05-27T19:09:22-04:00
- Command: `python scripts/phase2_remediation_packet.py`
- Source paths: `reports/phase2/cryptobench_*`, `data/registries/cryptobench_*`, `data/registries/dataset_inventory.json`, `data/raw_intake/`
- Governance paths: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`
- Confidence: high for local file-derived counts and registry generation; medium for recommended remediation status; low for unresolved homolog safety until clustering is run.
- Evidence status: verified for local artifacts; inferred for planning recommendations; uncertain for final scientific usability.
