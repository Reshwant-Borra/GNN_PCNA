# Gate-6 Packet: Final Pre-MD Readiness

Status: AWAITING HUMAN APPROVAL

## GNN Handoff

- Extraction policy: `independent_mcc_rank_fraction_size_weighted_cluster`
- Literal mean Jaccard: `0.6792`
- Interpretation: `MODERATE / EXPLORATORY PASS`
- 3/3 core: 11 residues
- >=2/3 supported region: 16 residues
- Full union: 20 residues, with 4 seed-specific residues treated as exploratory only

## Validation Artifacts

- Structure validation: `MD_STRUCTURE_VALIDATION_REPORT.md`
- Assumption audit: `MD_ASSUMPTION_AND_SOURCE_AUDIT.md`
- Positive control: `POSITIVE_CONTROL_SPECIFICATION.md`
- Frozen analysis: `FROZEN_MD_ANALYSIS_PROTOCOL.json`
- Frozen analysis SHA-256: `587f27cf2e402fe50b264d98d3d60fbbdcc8f9095025b2a89d12c7aebd633e56`
- Previous pre-reconciliation SHA-256: `2497def9e4675538dd08051ae6e5a448a41fbd32a1d7dc59cfb528d74d64ce3c`
- Replicate/duration plan: `MD_REPLICATE_AND_DURATION_PLAN.md`
- Readiness gate: `python scripts/md_readiness_gate.py`

## Gate Status

Not approved. Human approval is required after smoke, trajectory-analysis validation, and control interpretability pass.

## Next Legitimate Command

```bash
./md.sh smoke
```

Run this from the repository root on the RTX 4070 Linux machine. Production remains blocked until smoke, analysis validation, 3 x 5 ns control-first validation, and a real human Gate-6 approval are complete.
