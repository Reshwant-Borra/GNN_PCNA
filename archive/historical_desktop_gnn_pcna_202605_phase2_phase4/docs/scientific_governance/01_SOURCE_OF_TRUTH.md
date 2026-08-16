# Source Of Truth

## Purpose

Define where truth lives so Phase 2 cannot drift across stale Downloads trees, Obsidian copies, unregistered graph caches, old checkpoints, or bytecode-only replicas.

## Hard Rules

- There is one canonical repository: `https://github.com/Reshwant-Borra/GNN_PCNA`.
- There is one canonical Phase 2 governance directory: `docs/scientific_governance/`.
- There is one canonical dataset registry: `docs/scientific_governance/DATASET_REGISTRY.md` when created.
- There is one canonical split protocol: [05_SPLIT_PROTOCOL.md](05_SPLIT_PROTOCOL.md) plus a frozen split assignment file.
- There is one canonical context pack: the approved ResearchOS/source-index pack referenced by a manifest, not loose Obsidian notes.
- There is one canonical results directory: `reports/phase2/` or another path explicitly registered before use.
- No stale `Downloads`, desktop scratch trees, Obsidian exports, bytecode-only copies, old graph caches, or unregistered checkpoints may act as truth.
- Old graph caches may be reused only if registered with source hash, split hash, graph-construction code hash, and label hash.
- Checkpoints are valid only with dataset hash, split hash, config hash, seed, command, commit hash, and training log.

## Canonical Naming

- Dataset registry: `docs/scientific_governance/DATASET_REGISTRY.md`
- Split assignment: `data/splits/phase2_split_<YYYYMMDD>_<hash>.json`
- Label manifest: `data/labels/phase2_labels_<hash>.json`
- Graph manifest: `data/graphs/phase2_graph_manifest_<hash>.json`
- Checkpoint manifest: `checkpoints/phase2/<run_id>/MANIFEST.md`
- Metrics report: `reports/phase2/evaluation_<run_id>.md`
- MD manifest: `reports/phase2/md/<system_id>/MANIFEST.md`

## Forbidden Actions

- Treating `docs/vault`, Obsidian notes, crawl folders, or generated summaries as canonical without a registered manifest.
- Loading `.pt` graphs because they exist rather than because their hash is registered.
- Reporting metrics from a checkpoint whose training data and split cannot be reconstructed.
- Copying V1 checkpoints or graphs into Phase 2 without labeling them as historical controls.
- Using the SARC proposal as proof that a biological statement is true; it is project intent, not validation.

## Required Checks

- Source-of-truth audit lists canonical repo, branch, commit, dataset registry, split file, results path, and context pack.
- Artifact drift check compares current hashes against registered hashes.
- Deprecation check confirms old artifacts are marked and excluded.
- Human or ResearchOS review confirms no result was copied from an unregistered location.

## Examples Of Failure

- A coding agent finds `data/graphs_xl/8GLA.pt` from V1 and treats it as Phase 2 input without checking whether 8GLA influenced model selection.
- A report quotes an Obsidian note as final evidence even though the source index calls it an extract.
- A checkpoint named `best.ckpt` is used because it produces a strong AOH1996 score, but no split hash exists.

## Prevention

Every loader must require a manifest path. Every report must include artifact hashes. Every stale artifact must be moved out of the canonical path or marked `DEPRECATED_DO_NOT_USE.md` with reason, date, owner, and replacement.

## Compliance Artifact

`reports/phase2/source_of_truth_audit.md` must list all canonical paths and their hashes. It must cross-reference [15_PROVENANCE_AND_REPRODUCIBILITY.md](15_PROVENANCE_AND_REPRODUCIBILITY.md).

## If The Rule Fails

Freeze the affected result. Do not delete it. Mark it `NONCANONICAL_DO_NOT_CLAIM`, identify the canonical replacement, and rerun any downstream work from registered inputs.
