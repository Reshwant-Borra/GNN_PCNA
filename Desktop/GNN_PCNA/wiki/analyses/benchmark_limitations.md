---
type: analysis
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [benchmark, limitations, phase2]
aliases: [Benchmark Limitations]
confidence: medium
evidence_status: inferred
---

# Benchmark Limitations

## Current limitation summary

No benchmark is adopted. The main limitation is not dataset absence in the world; it is absence of a locally inventoried, hashed, licensed, schema-verified, leakage-audited Phase 2 dataset.

## CryptoBench limitations

- The workspace has OSF metadata and crawl extracts, not the actual CIF, split, or JSON label files.
- The OSF metadata records a license relationship and copyright holder/year, but the exact data license name and terms have not been resolved locally.
- The label definition is an apo-holo crypticity proxy based on pocket residue RMSD and holo ligand-contact residues, not direct experimental proof of every residue-level cryptic pocket.
- Official split information must be audited under Phase 2 rules. CryptoBench reports sequence-similarity controls, but Phase 2 still requires no UniProt, homolog, apo/holo, ligand-variant, duplicate-assembly, or PCNA leakage across splits.
- PCNA and PCNA-homolog presence is unknown.

## Auxiliary source limitations

- BioLiP/BioLiP2 and scPDB binding residues are proxy ligand labels, not cryptic-pocket truth.
- PDBbind is affinity-centered and structurally useful, but not a residue-level cryptic-pocket benchmark. Current official access and license status require verification before any use.
- ASD is allosteric-context data; it does not by itself establish PCNA allosteric mechanism or cryptic-pocket labels.
- PocketMiner labels and outputs are method-specific and simulation-derived. They are useful for baselines and comparison, but not interchangeable with CryptoBench apo-holo labels.

## Readiness implication

Benchmark readiness remains FAIL for training and graph generation. Dataset investigation can continue, but split freeze and label freeze require local file inventory, data hashes, schema audit, leakage tables, and human review.

## Provenance

- Source paths: `docs/scientific_governance/29_BENCHMARK_LIMITATIONS.md`; `reports/phase2/dataset_investigation_report.md`; `reports/phase2/proposed_split_strategy.md`; `reports/phase2/proposed_label_strategy.md`; crawl paths listed in [[Benchmark Strategy]]
- Confidence level: medium
- Evidence status: inferred from current investigation
- Date: 2026-05-27
