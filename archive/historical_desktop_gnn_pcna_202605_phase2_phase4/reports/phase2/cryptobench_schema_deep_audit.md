# CryptoBench Schema Deep Audit

## Status

- Final audit status: `LOCAL_SCHEMA_AUDITED_NOT_ADOPTED`
- Adoption status: `not_adopted`
- Allowed use: audit and human review packet only.
- Blocked: training, graph generation, split freeze, label freeze, MD, evaluation claims, and PCNA claims.

## What CryptoBench Contains Locally

- `dataset.json`: 1107 apo PDB keys and 5493 apo-holo pocket records.
- `noncryptic-pockets.json`: 665 apo PDB keys and 14493 additional non-cryptic pocket records.
- `folds.json`: 5 fold buckets: test, train-0, train-1, train-2, train-3.
- `cif-files.zip`: 5005 `.cif` files.
- Cryptic `dataset.json` references 5005 unique structures; 0 are missing from the ZIP.
- Noncryptic auxiliary records reference 8440 unique structures; 6915 are missing from the ZIP.

## Exact Record Fields

| Field | Types | Present | Missing |
| --- | --- | --- | --- |
| apo_chain | {'str': 5493} | 5493 | 0 |
| apo_pocket_selection | {'list': 5493} | 5493 | 0 |
| apo_pymol_selection | {'str': 5493} | 5493 | 0 |
| holo_chain | {'str': 5493} | 5493 | 0 |
| holo_pdb_id | {'str': 5493} | 5493 | 0 |
| holo_pocket_selection | {'list': 5493} | 5493 | 0 |
| holo_pymol_selection | {'str': 5493} | 5493 | 0 |
| is_main_holo_structure | {'bool': 5493} | 5493 | 0 |
| ligand | {'str': 5493} | 5493 | 0 |
| ligand_chain | {'str': 5493} | 5493 | 0 |
| ligand_index | {'str': 5493} | 5493 | 0 |
| pRMSD | {'float': 5493} | 5493 | 0 |
| uniprot_id | {'str': 5493} | 5493 | 0 |

The non-cryptic file uses the same core fields but lacks `pRMSD` and `is_main_holo_structure` in the local payload.

## Structural Meaning Of Fields

- Top-level JSON keys are apo PDB IDs, not individual residues.
- Each value is a list of holo partner records; one apo structure can map to multiple holo structures and ligands.
- `apo_chain`, `holo_chain`, and `ligand_chain` define chain IDs for each paired record.
- `apo_pocket_selection` and `holo_pocket_selection` are lists of chain/residue tokens such as `B_12`; the local README states these are auth asym IDs and auth sequence IDs.
- `pRMSD` and `is_main_holo_structure` describe pocket RMSD and the highest-pRMSD holo structure for that apo context.

## Selection Integrity

| File | Selection field | Records | Min | Max | Mean | Malformed | Wrong chain |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cryptic | apo_pocket_selection | 5493 | 2 | 40 | 16.61 | 0 | 0 |
| cryptic | holo_pocket_selection | 5493 | 2 | 40 | 16.61 | 0 | 0 |
| noncryptic | apo_pocket_selection | 14493 | 2 | 40 | 14.07 | 0 | 0 |
| noncryptic | holo_pocket_selection | 14493 | 2 | 40 | 14.07 | 0 | 0 |

## Duplicate And Malformed Entry Checks

- Duplicate cryptic pair records by apo/chain/holo/ligand key: 296.
- Cryptic required CIF structures missing from ZIP: 0.
- Noncryptic auxiliary required CIF structures missing from ZIP: 6915.
- CIF atom-site parse issues among required structures: 0.
- Chain absence issues for selected apo/holo chains: 0.

Exact selected residue tokens absent from parsed atom-site residue tables: 721. This check uses auth sequence ID and auth sequence ID plus insertion-code forms; final graph generation still needs an approved residue-node policy.

## Provenance

- Date: 2026-05-27T18:29:47-04:00
- Command: `python scripts/cryptobench_deep_audit.py`
- Source paths: `data/raw_intake/cryptobench/metadata_files/`, `data/raw_intake/cryptobench/labels_or_splits/`, `data/raw_intake/cryptobench/files/672a0171eae0bff252ba9ea3_cif-files.zip`
- Governance paths: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `14_CLAIM_POLICY.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`
- Confidence: high for local schema/count/hash/readability checks; medium for label-semantic interpretation from local README; low for homolog exclusion because no sequence clustering was run.
- Evidence status: verified for local files and machine checks; inferred for biological meaning; uncertain for final scientific usability.
