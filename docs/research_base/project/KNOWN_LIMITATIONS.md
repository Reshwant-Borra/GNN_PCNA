# Known Limitations

- Current shell cannot run ML/MD tests; required conda environment is absent.
- GNN outputs are prioritization scores, not calibrated binding probabilities.
- AOH1996-region recovery is positive-control overlap with known interfaces, not novel-pocket evidence.
- MD can support dynamics/openness, not prove ligand binding or druggability.
- MD also does not prove therapeutic relevance or experimental existence of a cryptic pocket.
- Large checkpoints/ESM/graph tensors from graph-leakage-fix were not imported into active tree during this cleanup.
- PRE-MD STABILITY PASS authorizes only a governed MD handoff request. It is not Gate-6 human approval and is not production-MD authorization.
- The frozen extraction policy was selected on five non-PCNA validation structures. This is better than tuning on 1W60/PCNA, but still a small calibration benchmark.
- Symmetry-normalized PCNA agreement is supplementary. Literal chain-aware Jaccard remains the primary stability gate metric.
- Structure preparation is smoke-ready/preflight-passed, not production-approved. 8GLA is low resolution at 3.77 A, required internal residue rebuilding, and has Cys135-Cys162 disulfides not declared in 1W60.
