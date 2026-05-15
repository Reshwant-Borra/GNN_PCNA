# KNOWN_BUGS.md

## Active Issues

_None — all known issues resolved as of 2026-05-15._

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
