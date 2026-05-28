# CryptoBench Label Semantics

## Status

- Final audit status: `LABEL_SEMANTICS_PROXY_NOT_FROZEN`
- Label freeze is not authorized.

## What The Labels Are

- The local files provide pocket residue selections per apo-holo record.
- The labels are residue-token annotations within pocket selections, but the dataset object is apo/holo-pair-level rather than a direct dense residue-label table.
- The positive class in `dataset.json` is best described as CryptoBench cryptic binding-site pocket residue selections.
- The local README describes paired apo and holo pocket selections and ligand metadata, but it does not make every unlisted residue a verified biological non-pocket residue.

## Positive, Noncryptic, Negative, And Unlabeled Semantics

| Class | Local source | Granularity | Governed interpretation |
| --- | --- | --- | --- |
| Cryptic positive | `dataset.json` `apo_pocket_selection` / `holo_pocket_selection` | Residue-level tokens inside apo-holo records | Benchmark cryptic binding-site positives, not independent experimental proof for every residue |
| Noncryptic pocket | `noncryptic-pockets.json` | Residue-level tokens inside apo-holo-like records | Additional non-cryptic pockets; not true negative residue labels |
| True negatives | Not explicitly enumerated | No direct true-negative table found | Unlisted residues must be treated as unlabeled or benchmark-background until a reviewed rule says otherwise |
| Ambiguous | Not explicitly marked | No ambiguity mask found | Must be defined before graph generation/training |

## Biological Meaning

- The labels appear biologically motivated by apo-holo ligand-binding contexts and pocket RMSD, but they remain benchmark annotations and proxy labels for Phase 2.
- The labels are not sufficient to claim validated cryptic biology for PCNA or any individual residue without source review and biological sanity checks.
- `noncryptic-pockets.json` suggests the benchmark distinguishes cryptic from non-cryptic pocket contexts, which is useful for audit, but it does not solve the true-negative problem.
- Likely biases include ligand availability bias, solved-structure/publication bias, apo-holo pairing bias, ligand class/size bias, chain/residue-numbering bias, and protein-family bias.

## Feasibility For Residue-Level Learning

- Feasible in principle: residue tokens can be mapped to chain/auth sequence IDs in mmCIF files.
- Not ready: a graph node table must preserve chain, auth sequence ID, insertion code, residue name, missing-residue policy, and label mask.
- ESM alignment is feasible only after a governed sequence extraction and missing-residue/index-shift policy. The bundled example explicitly warns that annotation indices can shift from dataset residue numbering.

## Provenance

- Date: 2026-05-27T18:29:47-04:00
- Command: `python scripts/cryptobench_deep_audit.py`
- Source paths: `data/raw_intake/cryptobench/metadata_files/`, `data/raw_intake/cryptobench/labels_or_splits/`, `data/raw_intake/cryptobench/files/672a0171eae0bff252ba9ea3_cif-files.zip`
- Governance paths: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `14_CLAIM_POLICY.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`
- Confidence: high for local schema/count/hash/readability checks; medium for label-semantic interpretation from local README; low for homolog exclusion because no sequence clustering was run.
- Evidence status: verified for local files and machine checks; inferred for biological meaning; uncertain for final scientific usability.
