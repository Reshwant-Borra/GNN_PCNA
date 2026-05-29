---
type: report
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [phase2, datasets, provenance, local-discovery]
confidence: high
evidence_status: verified
---

# Local Dataset Discovery Report

## Scope

This discovery pass inspected local candidate dataset locations only. It did not train, build graphs, run MD, freeze labels, freeze splits, or adopt datasets.

Inspected directories:

- `crawls/`
- `raw/`
- `data/`
- expected related directories: `archives/`, `datasets/`, `dataset/`, `outputs/`, `output/`, `cache/`, `artifacts/`

Governance constraints applied: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, and `31_DATA_LIFECYCLE_TRACKING.md`.

## Inventory Summary

| Location | Local result | Phase 2 usability |
|---|---|---|
| `crawls/` | 50,979 files, about 203 MB. Mostly `.md` and `.json` crawl outputs, source indexes, extracted summaries, raw API metadata, and generated knowledge-base files. | Useful as candidate evidence and source leads only. Not usable as adopted datasets. |
| `raw/` | Contains only `.gitkeep` placeholders under `raw/` and `raw/assets/`. | Empty raw intake. No usable dataset assets. |
| `data/` | Contains registry JSON files plus split and label templates. | Governance scaffolding only. No real split, label, or dataset records. |
| `archives/` | Not present. | No local archives. |
| `datasets/`, `dataset/` | Not present. | No local datasets. |
| `outputs/`, `output/`, `cache/`, `artifacts/` | Not present. | No local processed dataset outputs found. |

File-type discovery found no compressed dataset archives or structure coordinate files in `crawls/`, `raw/`, or `data/` with the searched extensions: `.zip`, `.tar`, `.tar.gz`, `.tgz`, `.gz`, `.bz2`, `.xz`, `.7z`, `.rar`, `.pdb`, `.cif`, `.mmcif`, `.sdf`, `.mol2`, `.parquet`, `.csv`, or `.tsv`.

## Discovered Candidate Evidence

These entries are source leads or metadata only. They are not adopted Phase 2 datasets.

| Candidate | Local paths | What is locally present | Missing for Phase 2 use | Trust level | Usable now? |
|---|---|---|---|---|---|
| CryptoBench | `crawls/pcna-dataset-repositories-pass9/raw/osf/osf-pz4a9.json`; `crawls/pcna-dataset-repositories-pass9/extracts/0015-cryptobench.md`; `crawls/pcna-gap-closure-datasets-tools-structures-pass6/extracts/0041-cryptobench-cryptic-protein-ligand-binding-sites-dataset-and-benchmark.md`; `crawls/pcna-cryptic-pocket-gat-md-kb-1000-pass2/extracts/0832-cryptobench-cryptic-protein-ligand-binding-sites-dataset-and-benchmark..md` | OSF node metadata and paper/extract leads. The OSF record identifies a public CryptoBench project and related file endpoint, but no OSF file listing or downloaded dataset files were found locally. | Actual files, file inventory, hashes, exact license name, schema, residue/pocket label files, official splits, CIF/mmCIF/PDB structures, chain mapping, apo/holo grouping, PCNA/homolog contamination screen. | Medium as a source lead; low as local data. | No. Strong primary benchmark candidate pending acquisition and audit. |
| PocketMiner-related assets | `crawls/pcna-curated-official-tools-data-structures-pass8/raw/curated/curated-PocketMiner paper PMC.json`; `crawls/pcna-curated-official-tools-data-structures-pass8/raw/curated/curated-Mickdub-gvp pocket_pred branch.json`; `crawls/pcna-curated-official-tools-data-structures-pass8/knowledge_base/sources/5-curated-pocketminer-paper-pmc.md`; `crawls/pcna-gap-closure-datasets-tools-structures-pass6/knowledge_base/entities/pocketminer.md` | Paper/repository leads and generated knowledge-base context. | Code checkout, exact model/data release, labels, simulation provenance, hashes, same-split baseline feasibility, license. | Medium as a baseline/method lead; low as local data. | No. Candidate baseline reference only. |
| BioLiP/BioLiP2 | `crawls/pcna-curated-official-tools-data-structures-pass8/raw/curated/curated-BioLiP biologically relevant ligand-protein binding database.json`; `crawls/pcna-curated-official-tools-data-structures-pass8/knowledge_base/sources/dataset_id-https-zhanggroup.org-biolip.md`; `crawls/pcna-gap-closure-datasets-tools-structures-pass6/raw/figshare/figshare-10.6084-m9.figshare.23641701.v1.json`; `crawls/pcna-gap-closure-datasets-tools-structures-pass6/extracts/1351-biolip2-source-code.md` | Official page lead, BioLiP/BioLiP2-related source leads, and metadata. | Downloaded BioLiP/BioLiP2 annotations, exact version, license, schema, binding residue tables, structure files, chain/residue mapping, proxy-label approval. | Medium as a source lead; low as local data. | No. Candidate auxiliary/background source only. |
| scPDB | `crawls/pcna-curated-official-tools-data-structures-pass8/raw/curated/curated-scPDB protein-ligand binding site database.json`; `crawls/pcna-curated-official-tools-data-structures-pass8/knowledge_base/sources/dataset_id-http-bioinfo-pharma.u-strasbg.fr-scpdb.md` | Official page lead and generated source page. | Downloaded scPDB archive, license, schema, structure/ligand files, binding-site mapping, version, leakage audit. | Medium as a source lead; low as local data. | No. Candidate auxiliary/baseline reference only. |
| ASD / ASBench | `crawls/pcna-curated-official-tools-data-structures-pass8/raw/curated/curated-Allosteric Database ASD.json`; `crawls/pcna-curated-official-tools-data-structures-pass8/knowledge_base/sources/dataset_id-http-mdl.shsmu.edu.cn-asd.md`; `crawls/pcna-gap-closure-datasets-tools-structures-pass6/extracts/1261-asbench-benchmarking-sets-for-allosteric-discovery.md`; `crawls/pcna-gap-closure-datasets-tools-structures-pass6/extracts/1262-asd-v2.0-updated-content-and-novel-features-focusing-on-allosteric-regulation.md`; `crawls/pcna-gap-closure-datasets-tools-structures-pass6/extracts/1306-asd-v3.0-unraveling-allosteric-regulation-with-structural-mechanisms-and-biologi.md` | Official page lead and allosteric benchmark/paper extracts. | Downloaded ASD/ASBench records, version, license, site mapping, chain/residue mapping, PCNA relevance audit, label-scope decision. | Medium as a context lead; low as local data. | No. Context/reference only unless separately audited. |
| PDBbind | `crawls/pcna-curated-official-tools-data-structures-pass8/raw/curated/curated-PDBbind protein-ligand binding affinity database.json`; `crawls/pcna-curated-official-tools-data-structures-pass8/knowledge_base/sources/dataset_id-http-www.pdbbind.org.cn.md`; `crawls/pcna-datasets-tools-repos-pass7/raw/kaggle/kaggle-madukacharles-pdbbind-protein-ligand-binding-affinity-dataset.json`; `crawls/pcna-datasets-tools-repos-pass7/raw/github/github-kcncell-pdbbind_dataset.json`; `crawls/pcna-datasets-tools-repos-pass7/raw/github/github-saharctech-binding-free-energy-prediction-pdbbind_refined_dataset.json` | Official page lead plus third-party repository/Kaggle metadata. | Official downloaded PDBbind package, license/access approval, exact version, refined/general/core split files, structure archives, affinity labels, residue-label mapping if any. | Medium as a source lead; low as local data. Third-party mirrors are risky until verified. | No. Not suitable as primary cryptic-pocket benchmark. |
| Apo/holo grouping data | CryptoBench and pocket-related crawl extracts; PCNA PDB metadata JSON under `crawls/*/raw/pdb/` | PDB API metadata for some PCNA-related structures and crawl mentions of apo/holo concepts. | Materialized apo/holo group table, structure coordinates, sequence clustering, biological assembly mapping, duplicate collapse table. | Low as local data. | No. |
| Split metadata | `data/splits/phase2_split_TEMPLATE.json`; crawl-generated `knowledge_base/entities/splits.md` files | Template only plus generated crawl entities. | Real split assignments, split provenance, leakage audit, human approval. | High for template existence; low for usable split data. | No. |
| Residue labels | `data/labels/phase2_labels_TEMPLATE.json`; crawl-generated `knowledge_base/entities/labels.md`, `labeling.md`, `residue.md` files | Template only plus generated crawl entities. | Real residue label records, label definition freeze, chain/residue mapping, ambiguity flags, human approval. | High for template existence; low for usable labels. | No. |
| Benchmark manifests / hashes | `data/registries/source_registry.json`; `data/registries/data_lifecycle_registry.json`; `crawls/*/crawl_manifest.json`; `crawls/*/SOURCE_INDEX.md` | Source registry, lifecycle registry, crawl manifests, and source indexes. | Dataset-level manifests with downloaded file paths, checksums, licenses, schema, record counts, and adoption status. | High for provenance scaffolding; low for dataset completeness. | No adopted benchmark manifest yet. |
| Structure archives / coordinate assets | None found by extension search. PDB records in crawls are JSON metadata, not coordinate files. | No `.pdb`, `.cif`, `.mmcif`, `.sdf`, or `.mol2` assets found in inspected dataset locations. | Downloaded canonical coordinate files and structure archive manifest. | High confidence negative finding for inspected paths. | No. |
| Processed dataset artifacts | None found in `data/`, `raw/`, or expected artifact/output dirs. Crawl knowledge-base JSON/Markdown is generated metadata, not processed Phase 2 data. | No graph, tensor, feature, label, or preprocessed benchmark artifacts found. | Governed preprocessing outputs after dataset adoption only. | High confidence negative finding for inspected paths. | No. |

## Completeness Assessment

No focused dataset is complete locally.

- CryptoBench: source lead exists, but actual data files are absent.
- PocketMiner: method/source leads exist, but no usable released data/code checkout or labels were found.
- BioLiP/BioLiP2: source leads exist, but no downloaded annotation package was found.
- scPDB: source lead exists, but no downloaded archive was found.
- ASD/ASBench: source leads exist, but no downloaded records were found.
- PDBbind: source and third-party mirror leads exist, but no official archive or local data package was found.

## Schema Visibility

Current schema visibility is insufficient for freeze.

- The only visible local Phase 2 label schema is `data/labels/phase2_labels_TEMPLATE.json`.
- The only visible local Phase 2 split schema is `data/splits/phase2_split_TEMPLATE.json`.
- Crawl metadata schemas are source-specific API or generated crawl formats. They do not define benchmark labels or splits.

## Provenance Quality

Current provenance is adequate for source navigation but inadequate for dataset adoption.

Strengths:

- `data/registries/source_registry.json` records crawl bundles and trust status.
- `crawls/*/SOURCE_INDEX.md` and `crawls/*/crawl_manifest.json` provide crawl-level provenance.
- Governance explicitly prevents treating crawls as truth.

Limitations:

- No dataset file hashes exist because no dataset files are present.
- No local license text or accepted dataset license record exists for CryptoBench or auxiliary datasets.
- No record-level provenance maps labels to source structures/residues.
- No split provenance or leakage-audit table exists.

## Stale, Duplicate, and Unverified Risks

- Crawl knowledge-base files are generated summaries and may duplicate, paraphrase, or stale-copy source claims.
- PDBbind appears through official and third-party leads; third-party mirrors must not be used without official-version reconciliation.
- Multiple crawl passes mention the same candidates, which increases duplicate evidence risk but does not increase verification confidence.
- PCNA PDB JSON metadata exists in several crawl folders, but coordinate files are absent and metadata duplication has not been resolved.
- No prior processed Phase 2 artifacts were found. If V1 artifacts exist outside the inspected paths, governance still classifies them as historical reference only.

## Phase 2 Usability Decision

No local dataset asset should be adopted or frozen from this discovery pass.

Acceptable to use now:

- `crawls/` entries as source leads for later acquisition and verification.
- `data/registries/` as governance scaffolding.
- split and label templates as templates only.

Not acceptable to use now:

- crawl-generated knowledge-base files as labels, splits, benchmark manifests, or biological truth.
- third-party PDBbind mirrors as canonical data.
- any inferred label/split information from extracts without original dataset files.

## Recommended Canonical Source Path Moving Forward

The canonical Phase 2 dataset source should be a new governed raw intake of official dataset files, starting with CryptoBench:

1. Acquire CryptoBench from official project-linked sources only.
2. Store immutable downloaded files under a governed raw intake path.
3. Record exact URLs, retrieval date, license, citation, file sizes, and SHA-256 hashes.
4. Materialize a dataset file inventory before any parsing.
5. Inspect schema and label definitions before graph construction.
6. Build leakage-audit tables before split/label freeze.
7. Require human dataset, label, split, and biological sanity approvals before training.

Auxiliary sources should follow the same intake process only if a human reviewer approves their role.

## Unresolved Blockers

- CryptoBench official file listing and local file acquisition are missing.
- Exact CryptoBench license name and terms remain unresolved.
- No structure coordinate files exist locally for any focused dataset.
- No local residue-label files exist.
- No local apo/holo grouping table exists.
- No local split assignments exist.
- No local benchmark manifest with hashes exists.
- No human dataset-adoption, split-freeze, or label-freeze approval exists.

## Conclusion

The workspace already contains useful discovery metadata, but not usable dataset assets. Phase 2 is not ready for dataset adoption, split freeze, label freeze, graph construction, training, MD, or claims. The next scientifically defensible step is official CryptoBench acquisition and checksum-backed intake, followed by schema, license, label, and leakage audits.

## Provenance

- Source paths: `crawls/`, `raw/`, `data/`, `data/registries/source_registry.json`, `data/registries/data_lifecycle_registry.json`, `data/splits/phase2_split_TEMPLATE.json`, `data/labels/phase2_labels_TEMPLATE.json`, `crawls/pcna-dataset-repositories-pass9/raw/osf/osf-pz4a9.json`, `crawls/pcna-curated-official-tools-data-structures-pass8/raw/curated/curated-PocketMiner paper PMC.json`, `crawls/pcna-curated-official-tools-data-structures-pass8/raw/curated/curated-BioLiP biologically relevant ligand-protein binding database.json`, `crawls/pcna-curated-official-tools-data-structures-pass8/raw/curated/curated-scPDB protein-ligand binding site database.json`, `crawls/pcna-curated-official-tools-data-structures-pass8/raw/curated/curated-PDBbind protein-ligand binding affinity database.json`, `crawls/pcna-curated-official-tools-data-structures-pass8/raw/curated/curated-Allosteric Database ASD.json`
- Governance paths: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `31_DATA_LIFECYCLE_TRACKING.md`
- Confidence level: high for local file inventory and absence of archives/coordinate files in inspected paths; medium for classification of crawl leads; low for dataset suitability until official files are acquired
- Evidence status: verified for local inventory; inferred for intended candidate roles; uncertain for final adoption
- Date: 2026-05-27
