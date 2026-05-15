# Known Limitations

## Biological / Structural

- **Static graph problem**: Crystal structure captures one conformation; cryptic pockets are by definition absent in the apo crystal. The model must generalize across conformational space.
- **Single ground-truth pocket**: Only one confirmed cryptic site (AOH1996/8GLA). This severely limits supervised training on PCNA itself — pre-training on external datasets is essential.
- **Crystal contacts in 1W60**: Lattice packing may occlude surface regions that are accessible in solution.
- **Homotrimer symmetry**: All 3 chains nearly identical — risk of data leakage if chains treated as independent test samples.

## Model

- **Edge cutoff sensitivity**: Results are sensitive to the 8–10 Å distance cutoff. Pockets at domain interfaces may be missed with tight cutoffs.
- **No explicit hydrogen bonding**: Current edge features don't encode H-bond geometry, which matters for pocket stability.
- **GNN depth vs. over-smoothing**: >5 layers tends to blur node representations; use residual connections and test 3–4 layers first.
- **Label imbalance**: Pocket residues are ~5–15% of all residues; model may collapse to predicting all-negative without careful loss weighting.

## MD Validation

- **Timescale gap**: Cryptic pockets may open on µs–ms timescales; standard 50–100 ns MD may not capture opening events.
- **Force field limitations**: CHARMM36m may not perfectly reproduce pocket dynamics; consider replica exchange or enhanced sampling if pockets don't open.
- **RMSF is not directional**: High RMSF indicates flexibility but doesn't confirm pocket opening; must cross-check with volume tracking.
- **DCCM interpretation**: Correlation doesn't imply causation; high DCCM between pocket residues is supporting evidence, not proof.

## Computational

- **GPU memory**: Full PCNA trimer graph at 8 Å cutoff is dense (~800 residues × ~10 edges each). Batch size may need to be 1–4 on 16 GB GPUs.
- **MD cost**: 100 ns explicit solvent PCNA trimer ≈ 3–7 days on a single GPU node (OpenMM).

---

## Related

[[VALIDATION]] · [[MODELS]] · [[BIOLOGY_PCNA]] · [[RESEARCH_QUESTION]] · [[EXPERIMENT_INDEX]] · [[md_validation_notes]]
