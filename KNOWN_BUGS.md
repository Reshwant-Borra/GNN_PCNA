# KNOWN_BUGS.md

## Active Issues

> For scope limitations (asymmetric units, labeling approximations, metric caveats) see **[LIMITATIONS.md](LIMITATIONS.md)**.

### BUG-007: Core ML scripts require torch_geometric not installed by default
- **Status**: fixed (2026-05-22)
- **Affected**: `scripts/run_test_eval.py`, `scripts/aoh_gate_check.py`, `src/training/train.py`
- **Description**: All model scripts fail with `ModuleNotFoundError: No module named 'torch_geometric'` in a fresh Python environment. PyTorch Geometric requires a separate install step that most users miss.
- **Reproduction**: `python scripts/run_test_eval.py --help` in a clean venv.
- **Fix**: Follow setup instructions step 3 exactly — PyG must be installed before PyTorch.

### BUG-008: pytest skips all model tests with "torch missing" even when torch is installed
- **Status**: fixed (2026-05-22)
- **Affected**: `tests/`
- **Description**: 11 of 16 tests are skipped even with torch 2.x installed, because the skip guard checks for `torch_geometric` (absent), not `torch`. False confidence from "5 passed" result.
- **Fix**: Separate skip guards for torch vs torch_geometric; CI should fail hard when PyG unavailable.

### BUG-009: `download_data.py --verify` fails if manifest doesn't exist
- **Status**: open
- **Affected**: `scripts/download_data.py`
- **Description**: Running `--verify` before ever running the script prints "No manifest found" and exits silently. Since files are already in git, manifest should be pre-committed.
- **Fix**: Commit `data/manifests/pdb_checksums.json` or auto-generate from existing files.

### BUG-010: Per-structure docs contain pre-fix V3 predictions
- **Status**: open
- **Affected**: `results/per_structure/*/report.txt` and related files
- **Description**: Per-structure reports were generated before the apo-negative fix; scores in those files reflect the superseded checkpoint.
- **Fix**: Regenerate with `python scripts/per_structure_analysis.py` using `best_pcna_v3_fixed.ckpt`.

### BUG-011: Random CryptoSite split has homology leakage
- **Status**: fixed (2026-05-22)
- **Affected**: `data/splits/cryptosite_split.json`, previous benchmark reporting
- **Description**: The old random split placed homologous structures across train and held-out sets, invalidating headline benchmark claims.
- **Fix**: Added MMseqs2 30% homology-clean splitting, split integrity validation, clean-split ablation training, and clean evaluation scripts. Final four-condition, three-seed rerun completed in E004.

### BUG-012: Clean benchmark provenance was insufficient
- **Status**: fixed (2026-05-22)
- **Affected**: `src/training/train.py`
- **Description**: Checkpoints did not record enough provenance to defend split hash, graph hash, command, environment, condition, node dimension, seed, and git commit.
- **Fix**: `best_meta.json` now records clean benchmark provenance fields for new runs. Final clean-split checkpoints include the required provenance.

---

## Pocket-dynamics correctness overhaul (2026-07-17)

Root cause of "the MD pocket has no dynamics": the analysis measured the wrong
thing, not flat biology. Proven empirically on the 1AXC 25 ns trajectory —
whole-trimer alignment gave backbone RMSD **27 Å** (the "corrupt" false negative);
per-chain alignment gives **1.7–2.6 Å**, and the pocket then shows a volume
fluctuation range of **~430 Å³**, SASA range **~313 Å²**, and a 122–232 mouth
opening/closing of **~5.4 Å**. PBC imaging was NOT the cause (it changes nothing
here — each chain is already whole).

### BUG-013: Pocket "volume" was a convex hull over all 3 chains (whole ring)
- **Status**: fixed (2026-07-17)
- **Affected**: `scripts/run_md_analysis.py`, `src/md/parse_trajectory.py`
- **Description**: Pocket residues were matched by residue number across chains A/B/C, so the convex hull spanned the ~80 Å ring (~20,000 Å³) and was rigid → flat "no dynamics".
- **Fix**: Per-chain pocket hulls (chain-qualified selection). Volume/SASA/mouth are rigid-motion invariant so they need no alignment, only single-chain restriction.

### BUG-014: RMSF/DCCM computed on UNALIGNED coordinates (MDAnalysis pitfall)
- **Status**: fixed (2026-07-17)
- **Affected**: `scripts/run_md_analysis.py`, `src/md/parse_trajectory.py`
- **Description**: `align.AlignTraj(u, ref, in_memory=False)` never rewires the Universe, so RMSF/DCCM ran on unaligned frames dominated by whole-trimer tumbling.
- **Fix**: Rewrote in mdtraj with explicit per-chain `superpose` on a core that EXCLUDES the pocket (no circularity); RMSF about the mean.

### BUG-015: Whole-trimer alignment conflates inter-subunit motion (27 Å RMSD)
- **Status**: fixed (2026-07-17) — the real driver of the false negative.
- **Fix**: All MD metrics are computed per chain after per-chain core alignment; a backbone-RMSD sanity gate (<5 Å) flags any regression.

### BUG-016: Chain-agnostic pocket mask contaminated the pocket set with chain C
- **Status**: fixed (2026-07-17). `AOH_GT_BY_CHAIN` (A,B only) for eval; `MD_POCKET_RESSEQ` applied per chain for the n=3 MD triplicate.

### BUG-017: `fraction_open_frames` threshold (100 Å³) saturated to 1.0
- **Status**: fixed (2026-07-17) — metric removed/replaced by the per-chain volume/SASA fluctuation statistics.

### BUG-018: DCCM used `abs()` (sign destroyed); no per-chain alignment
- **Status**: fixed (2026-07-17) — signed, chain-averaged DCCM after per-chain core alignment.

### BUG-019: `run_md_analysis.py` hard-exited on a missing default 1W60 DCD; figures read the old flat schema
- **Status**: fixed (2026-07-17) — auto-discovers an available trajectory (incl. the 1AXC 25 ns run), honest structure labelling, `make_md_figures.py` rewritten to plot the per-chain volume traces.

---

## Analysis & data-integrity fixes (2026-07-17, batch 2)

Applied and compile-verified; none change the trained model or its inputs:

- **`scripts/run_nma.py`** — fixed the run-breaking `None`-format crash (fail-fast + `_fmt` guard); added seeded permutation tests so the "elevated flexibility / cryptic pocket" interpretation is gated on significance instead of a marginal fold-change; HETATM `CA` (calcium) no longer injected into the Cα network; falsy-0.0 guard. ANM cutoff left at 7.5 Å (changing it would move the published 0.857/1.157 numbers) — documented only.
- **`src/data_processing/fetch_structures.py`** — chain-count Check-3 now enforced (core IDs warn, non-core hard-fail only on explicit `expected_chains`); cached files re-verified instead of blindly skipped; resolution waiver + insertion-code/None-resolution now auditable. Verified **zero** pass/fail verdict changes across 149 structures.
- **`scripts/phase5_analyze_1axc_md_fixed.py`** / **`phase5_pocket_dynamics_1axc.py`** — RMSF made chain-aware (no trimer triple-count), per-chain reference ratio, insufficient-frames-after-equil guard, consistent `incomplete_replicate` tagging, Rg/SASA over-read caveats.
- **`md_validation_4070/run_md.py`** — real post-run sanity gate (NaN/energy/RMSD → `FAILED.json`, not `DONE`), HMR mass 1.5→4.0 amu for the 4 fs step, resume no longer double-writes frames, equilibration decoupled from the production ns budget, barostat seeded.
- **`md_validation_4070/analyze_md.py`** — frame interval read from log (not hardcoded), pocket SASA/Rg computed per chain, short-trajectory equil-skip warns, Cohen's-d caveat + per-replicate positive-control gate.
- **`src/evaluation/score_pockets.py`** — clusters actually sorted by mean_score; B-factor guard fixed (`>=66`, preserves element/charge columns).
- **`scripts/dump_cryptic_pocket.py`** — dead `holo_mean` removed; holo/apo/delta now aggregated over the same matched-residue set; empty-match guarded.

---

## Model-input / dataset bugs — CONFIRMED; co-author cleared to fix (needs retrain)

Confirmed by the 2026-07-17 audit. The co-author has approved changing them, but
each one alters the graph node features or the residue set, so it is **not a
hotfix**: applying the code change alone would desync the trained checkpoint
(`checkpoints/pcna_reproduced/best.ckpt`) from its reported AUROC/AUPRC. Fix them
as ONE scoped experiment — code change + `build_graphs` rebuild + finetune +
clean re-eval — so the headline numbers stay valid. (Not done in this pass; they
do not affect the MD-validation "no dynamics" failure this session targeted.)

### BUG-020: `graph_construction.py` `rel_pos` is a global index over the concatenated multi-chain residue list
- **Status**: open (requires retrain). Breaks homotrimer symmetry — the same residue in chains A/B/C gets different positional values.

### BUG-021: Backbone edges / `is_backbone` / pseudo-dihedrals span residue-numbering gaps
- **Status**: open (requires retrain). Separation is measured in array index, not `resid`, so gaps (missing residues) create spurious covalent edges and bogus dihedrals; contact-graph `seq_sep` has the same array-index bug.

### BUG-022: Explicit chain one-hot lets the model distinguish identical subunits and shortcut the A/B-only label
- **Status**: open (requires retrain / ablation). Also: the one-hot map `unique_chains[:3]` and `chain_id_int` (uncapped) diverge and can mislabel columns for >3 chains.

### BUG-023: `cryptic_gnn.py` virtual node aggregates `mean(dim=0)` over the whole tensor
- **Status**: open (training only). Leaks across proteins when multiple graphs are batched. Single-graph inference (how all per-structure scoring runs) is unaffected, so reported eval numbers stand; fix for batched training. Also: `focal_loss` runs BCE on sigmoid probs (use logits/BCEWithLogits); `ranking_loss` samples pos/neg by array order not randomly.

### BUG-024: `parse_pdb.py` drops modified-standard residues (MSE) and insertion codes; SASA computed over waters+ligand
- **Status**: partially mitigated (2026-07-17). Fixed the SILENT failure path only — SASA failure now warns instead of zeroing the whole structure without signal. The residue-set changes (include MSE→MET, honour insertion codes) and the SASA target (protein-only) all alter node features and are left for the rebuild+retrain.

## Template

```
### BUG-001: <short title>
- **Status**: open | investigating | fixed
- **Affected**: src/path/to/file.py
- **Description**: What goes wrong.
- **Reproduction**: Minimal steps.
- **Root cause**: (fill in when known)
- **Fix**: (fill in when resolved)
```

## Resolved

### BUG-001: `_build_backbone_edges` O(N²) Python loop
- **Status**: fixed (2026-05-15)
- **Affected**: `src/data_processing/graph_construction.py`
- **Description**: Nested Python for-loop was O(N²). For a 900-residue PCNA trimer = 810,000 iterations, causing multi-second graph construction.
- **Fix**: Vectorized with numpy broadcasting — `same_chain = chain_ids[:, None] == chain_ids[None, :]` + `np.where()`.

### BUG-002: `is_interface` O(N²) Python loop
- **Status**: fixed (2026-05-15)
- **Affected**: `src/data_processing/graph_construction.py`
- **Description**: Same O(N²) issue for cross-chain interface flag computation.
- **Fix**: `cross_chain = chain_ids[:, None] != chain_ids[None, :]`; `is_interface = (cross_chain & (dist_matrix < 8.0)).any(axis=1)`.

### BUG-003: PocketGNN forward symmetry prior semantically wrong
- **Status**: fixed (2026-05-15)
- **Affected**: `src/models/cryptic_gnn.py`
- **Description**: `sym_weight=0.1` default caused `h_mean = h_fused.mean(dim=0)` which averages ALL residues globally (not per-position across chains). Pulled every residue toward a global mean — uninformative and harmful to training.
- **Fix**: Changed default `sym_weight=0.0`. Symmetry is correctly enforced via `symmetry_loss()` in the loss function, which groups by `resid` across chains.

### BUG-004: `CrypticGNN` missing `param_count()` method
- **Status**: fixed (2026-05-15)
- **Affected**: `src/models/cryptic_gnn.py`
- **Description**: `src/ui/app.py` calls `model.param_count()` on whichever model is loaded. `PocketGNN` had the method; `CrypticGNN` did not, causing `AttributeError` when using the v1-baseline option.
- **Fix**: Added `param_count()` to `CrypticGNN`.

### BUG-005: UI B-factor replacement crashes on short PDB lines
- **Status**: fixed (2026-05-15)
- **Affected**: `src/ui/app.py`
- **Description**: `line[:60] + f"{prob:6.2f}" + line[66:]` raises `IndexError` if the PDB line is shorter than 66 characters (e.g., some ATOM records from non-standard files).
- **Fix**: Guard with `if len(line) >= 66` before slicing.

### BUG-006: `train.py main()` hardcodes large model, saves by loss not AUROC
- **Status**: fixed (2026-05-15)
- **Affected**: `src/training/train.py`
- **Description**: `main()` always instantiated `PocketGNN()` (large), ignored `CrypticGNN`, had no `--model-size`, `--resume`, or `--phase` args, and saved checkpoint by best val_loss instead of best AUROC.
- **Fix**: Added `--model_size`, `--resume`, `--phase` args; checkpoint now saved by best AUROC; two-stage training (pretrain → finetune with symmetry loss) properly wired.

---

## Related

[[BUG_LOG]] · [[CLAUDE]] · [[EXPERIMENT_INDEX]] · [[CHANGELOG]]
