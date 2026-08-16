# Dataset Investigation Report

Date: 2026-05-27
Created by: Codex
Status: DRAFT - investigation packet, no dataset frozen

## Governance Boundary

This report starts the Dataset Investigation + Freeze phase. It does not authorize training, final GNN construction, graph generation, MD, split freeze, or label freeze.

Governing rules: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `09_EVALUATION_PROTOCOL.md`, `10_BASELINE_REQUIREMENTS.md`, `14_CLAIM_POLICY.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`, `37_PHASE2_IMPLEMENTATION_PLAN.md`.

## Local Inventory

| Area | Finding | Freeze implication |
|---|---|---|
| `data/` | Only templates and registries are present: split template, label template, source registry, lifecycle registry, assumption registry. | No local dataset is adopted. |
| `raw/` | No candidate benchmark structure/label files found by file scan. | No raw benchmark foundation exists locally. |
| `crawls/` | Contains source leads, OSF metadata, curated source pointers, papers, and generated knowledge-base notes. | Useful evidence map, not dataset content. |
| CryptoBench local files | `crawls/pcna-dataset-repositories-pass9/raw/osf/osf-pz4a9.json` and `extracts/0015-cryptobench.md` exist. | Metadata only; no CIF/label/split files locally. |
| BioLiP/scPDB/PDBbind/ASD local files | Curated JSON source-lead records exist under `crawls/pcna-curated-official-tools-data-structures-pass8/raw/curated/`. | Source leads only. |
| PocketMiner local files | Paper/repo leads exist in crawls; no same-split baseline outputs or local dataset files. | Baseline candidate only. |

## Dataset Assessments

| Dataset | What it contains | Intended use | Strengths | Leakage risks | Biological limitations | Proposed Phase 2 role |
|---|---|---|---|---|---|---|
| CryptoBench | Remote sources describe apo structures, paired holo structures, ligand identifiers, apo/holo pocket residue selections, train-test splits, CIF files, and PyMOL scripts. Local workspace contains only OSF metadata and source extracts. | Cryptic binding-site benchmark and possible primary residue-level benchmark candidate. | Purpose-built for cryptic binding sites; apo-holo construction; sequence clustering and split controls reported by source; much closer to Phase 2 than generic ligand datasets. | Must verify no shared UniProt/family/apo-holo/ligand-variant/duplicate assembly across Phase 2 splits; reported PocketMiner overlap risk includes three PocketMiner training apo structures with >95% similarity to CryptoBench test apo structures; PCNA/homolog status unknown. | Label is a benchmark definition based on apo-holo pocket RMSD and holo ligand-contact residues, not direct experimental proof for every residue. | Primary benchmark candidate, not frozen. |
| BioLiP/BioLiP2 | Biologically relevant ligand-protein interactions, binding residues, binding affinity annotations, catalytic residues, EC/GO terms, and database crosslinks; BioLiP2 uses mmCIF and includes peptide/DNA/RNA ligand classes. | Annotation source, auxiliary proxy labels, biological ligand-contact context. | Curated for biological relevance rather than raw PDB ligand presence; large and updated. | High duplicate/homolog/ligand-variant risk if used directly; chain and ligand identity must be audited. | Ligand contact is not cryptic-pocket truth; may encode known accessible pockets and ligand/source biases. | Auxiliary training source only if separately labeled as ligand-binding proxy; otherwise background. |
| scPDB | Ligandable binding-site entries built from PDB complexes; binding site defined around one ligand with protein residues near ligand heavy atoms. | Ligandable-site proxy source and geometry/reference baseline. | Explicit residue-contact style site definition; processed protein/ligand/binding-site structures. | Redundant proteins/ligands and apo/holo leakage likely unless regrouped; PDB-derived duplicates require audit. | Binding-site proximity does not imply crypticity or allostery. | Auxiliary proxy or baseline reference; not primary. |
| PDBbind | Protein-ligand complexes with experimental affinity values such as Kd, Ki, IC50 and structure files in general/refined/core sets. | Affinity/source context; possible ligand-complex background. | Standard affinity benchmark with many PDB-linked complexes. | Known train/test leakage concerns in the literature; duplicate protein/ligand families; official access/licensing unresolved in this investigation. | Affinity labels are not residue-level cryptic labels and invite drug-discovery scope drift. | Exclude from primary benchmark; background only unless separately governed. |
| ASD | Allosteric proteins, allosteric modulators, interactions, sites, allosite potential predictions, PPI allostery, and related annotations. | Allosteric context, possible site-reference source after entry audit. | Directly related to allostery; official database has downloadable sections and literature citations. | Homolog and mechanism leakage if allosteric families cross splits; predicted allosite potential is not ground truth. | Allosteric annotation does not establish PCNA cryptic-pocket mechanism; PCNA coverage unknown. | Background/allosteric reference only for now. |
| PocketMiner-related datasets | PocketMiner paper describes MD-derived residue labels for pocket opening over 40 ns windows and a 39-example apo/holo cryptic-pocket validation set. | Same-split baseline and method comparison; possible auxiliary simulation-label source. | Direct cryptic-pocket method; residue-level predictions; useful baseline. | Published metrics are not same-split Phase 2 evidence; overlap with CryptoBench must be audited. | Simulation-opening labels differ from apo-holo cryptic-site labels and should not be mixed. | Baseline candidate, not primary dataset. |

## Exact Task Definition Candidate

Primary candidate task: given an apo protein structure with residue nodes, score each residue for membership in a known cryptic ligand-binding site defined by paired holo evidence. Evaluate whether top-ranked residues recover the benchmark cryptic-site residues for held-out proteins.

Scope language: residue-level candidate cryptic-pocket-region prediction for computational structural biology. No druggability, therapeutic, clinical, or mechanism validation claims.

## Leakage Investigation

| Risk | Current status | Required audit before freeze |
|---|---|---|
| Homolog leakage | Unresolved. CryptoBench reports sequence controls, but Phase 2 has not run its own clustering. | Build sequence cluster table, group by UniProt/family, confirm no homologs across train/val/test. |
| Apo/holo leakage | Unresolved. CryptoBench records are apo-holo pairs and one apo may pair to multiple holo structures. | Group all apo/holo records, ligand variants, repeated apo structures, and alternate holo structures before split. |
| Duplicate structures | Unresolved. CryptoBench source includes a duplicate holo-homomer removal step, but local files are absent. | Hash structures, group duplicate PDB IDs/assemblies/chains and redundant homomers. |
| Ligand-label ambiguity | High risk for all ligand-derived sources. | Record ligand IDs, excluded additives, atom basis, residue thresholds, ambiguous residues, and biological relevance rules. |
| PCNA contamination | Unknown. | Screen PDB IDs, UniProt IDs, names, sequence clusters, and structural homologs against PCNA/P12004 and PCNA-like clamps. |
| Split feasibility | Plausible for CryptoBench, not verified locally. | Download/inventory files, create split candidate, run leakage audit, obtain human review. |

## Source Evidence Used

Local paths:

- `crawls/pcna-dataset-repositories-pass9/SOURCE_INDEX.md`
- `crawls/pcna-dataset-repositories-pass9/raw/osf/osf-pz4a9.json`
- `crawls/pcna-dataset-repositories-pass9/extracts/0015-cryptobench.md`
- `crawls/pcna-curated-official-tools-data-structures-pass8/SOURCE_INDEX.md`
- `crawls/pcna-curated-official-tools-data-structures-pass8/raw/curated/`
- `crawls/pcna-gap-closure-datasets-tools-structures-pass6/`

External sources checked:

- CryptoBench paper: `https://doi.org/10.1093/bioinformatics/btae745`
- CryptoBench GitHub: `https://github.com/skrhakv/CryptoBench`
- CryptoBench OSF: `https://osf.io/pz4a9/`
- BioLiP/BioLiP2: `https://zhanggroup.org/BioLiP/`, NAR 2023 BioLiP2 paper
- scPDB: NAR 2015 scPDB paper
- ASD: `https://mdl.shsmu.edu.cn/ASD/`
- PocketMiner: `https://doi.org/10.1038/s41467-023-36699-3`
- PDBbind context: PDBbind literature/review sources; current `www.pdbbind.org.cn` did not resolve to usable PDBbind content during this investigation.

## Recommendation

Acceptable as candidates:

- CryptoBench as primary benchmark candidate after local file and leakage audit.
- BioLiP/BioLiP2 and scPDB as auxiliary proxy-label sources only if separate label IDs and leakage controls are approved.
- ASD as allosteric context/reference only.
- PocketMiner as same-split baseline candidate.

Risky or excluded for primary benchmark:

- PDBbind should be excluded from primary Phase 2 cryptic-pocket benchmarking because its labels are affinity-centered, not residue-level cryptic-pocket labels.
- Any BioLiP/scPDB/PDBbind ligand-contact labels must be excluded from cryptic-pocket truth unless explicitly scoped as proxy labels.

## Freeze Readiness

Dataset readiness: FAIL.
Benchmark readiness: FAIL.
Split readiness: FAIL.
Label readiness: FAIL.

The project is not ready for split + label freeze. The project is ready for the next investigation step: acquire or inventory CryptoBench files, resolve license, parse schema, hash files, screen PCNA/homologs, and prepare a human review packet.
