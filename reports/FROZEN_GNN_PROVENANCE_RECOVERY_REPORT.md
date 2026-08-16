# Frozen GNN Provenance Recovery Report

Verdict: NO-GO for the final frozen GNN handoff.

The historical `d9efd97400f24cb1cd9ab55cf112c174f2a610e405714758f688cd4944cad193` score artifact was recovered and reproduced from branch `pcna-xl-esm-full-final-framing` at `d7cf76d674bced192b3c9d2b4f7f4fbf7ac3a228` using checkpoint `0114999ea9237b44f114c5a23a8529cb6939e80450339d71c07178ccd2d3addf`. This is a real recovered lineage, not a reconstruction.

The active August MD handoff remains unresolved because it says it derives from a three-seed consensus using local-only checkpoints `03d01eba42eb7f6da01c0147dea434b1e1797bd2302e8a178d6bbd9b19526ce5`, `7f145d6f54d03744f71c0224df4f170ad4aab388387e242234ebffda1acae17b`, and `0a739dec47248651499942207b82139e5dea8bebfafe5ed50aabcbbdfd6aa3f6`. Those checkpoints are not durably retrievable and were not shown to reproduce the committed handoff.

## Recovered d9efd Lineage

- Source branch: `origin/pcna-xl-esm-full-final-framing`
- Source commit: `d7cf76d674bced192b3c9d2b4f7f4fbf7ac3a228`
- Checkpoint: `checkpoints/clean_split/xl_esm_full/seed_42/best.ckpt`
- Checkpoint SHA-256: `0114999ea9237b44f114c5a23a8529cb6939e80450339d71c07178ccd2d3addf`
- Checkpoint bytes: `53485974`
- Checkpoint metadata SHA-256: `e6a3e7fe747fe39081099682f7547e81d4dff599f15f8cfc45f9ba5f9f795154`
- Graph manifest hash: `69744b548e812697ba9015c6563ed526f1af2e915b1595badb1dd47fd1b4c64f`
- Split SHA-256, committed LF bytes: `828fd6d4e694cc6e258a2de8e63c4130876a9c7897dd14ccc2db15a3e6c1f06a`
- Split SHA-256, CRLF bytes recorded in metadata: `a88bd6e6885aec63cb47077eab779fa1cbc5e8a6a29b27e02faa61fdcb6d3ee7`
- Frozen score artifact: `results/per_structure/summary_table.csv`
- Frozen score artifact SHA-256: `d9efd97400f24cb1cd9ab55cf112c174f2a610e405714758f688cd4944cad193`

## Feature Contract

The recovered checkpoint input layer has shape `[384, 520]`. The 520-dim contract is 40 hand-crafted graph features plus 480 ESM2 t12 features from `facebook/esm2_t12_35M_UR50D`. The full feature schema is recorded in `artifacts/provenance/FROZEN_FEATURE_SCHEMA.json` with SHA-256 `360189099c521ef2d05576a998bd44a247bc36063e1318987d1181e3e634a285`.

## Label Manifest

No standalone historical 520-dim label manifest was recovered. The recovered label carrier is the original graph tensors summarized by `data/results/split_integrity_520.json`; a derived manifest has been written to `artifacts/provenance/FROZEN_LABEL_MANIFEST_DERIVED_FROM_GRAPHS.json` with SHA-256 `5fbe5c79648641429c2ae70661bfec069b04d528261825fbc9cf0f96702f9d4c`. This derived file must not be represented as the missing original label manifest.

The recovered 520-dim graph-label carrier has 55 structures, 43 train / 6 validation / 6 test, 36,211 nodes, and 1,630 positive labels.

## Frozen-Output Identity Test

Byte equality was not achieved for regenerated `summary_table.csv` because the rerun emitted LF/path-separator differences and tiny floating-point formatting changes under a newer local torch/PyG environment. Score-level identity passed a strict absolute tolerance of `1e-5`: 59 score files, 65,358 rows, max absolute score difference `1.0000000000287557e-06`, mean absolute score difference `2.5046666054651342e-08`, zero residue ordering mismatches, and zero top-residue mismatches.

The identity test is recorded in `artifacts/provenance/FROZEN_OUTPUT_IDENTITY_TEST.json` with SHA-256 `0c26571039296216af52ac1bf38036aab13d59510797e2cc53749a05c4337a13`.

## Remaining Contradiction

The d9efd lineage and the August three-seed MD handoff lineage are not the same. The project cannot declare final frozen-GNN provenance GO until the August handoff is either cryptographically tied to its own durable three-seed checkpoint package and reproduced, or explicitly refrozen to the recovered d9efd lineage.
