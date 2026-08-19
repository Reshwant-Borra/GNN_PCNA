# PCNA MD validation - analysis report (final_consensus_1w60_20260815)

PBC-artifact suspected in any replicate (frame-to-frame jump > 0.3 nm): **False**
Duplicate frame-count risk in any complete replicate: **False**
Skipped incomplete/missing replicates: **0**

## Per-replicate

| role | pdb | rep | RMSD mean (nm) | max frame-jump (nm) | pocket RMSF (nm) | pocket SASA (nm^2) | open-like fraction | frame count | PBC-artifact? |
|---|---|---|---|---|---|---|---|---|
| control | 8GLA | rep01 | 0.168 | 0.117 | 0.098 | 8.3 | 0.200 | ok | False |
| control | 8GLA | rep02 | 0.161 | 0.095 | 0.089 | 8.0 | 0.040 | ok | False |
| control | 8GLA | rep03 | 0.142 | 0.104 | 0.121 | 8.6 | 0.560 | ok | False |

## Positive-control gate (the anti-false-negative check)

The production gate uses the trajectory-derived control gate below; pooled apo/control SASA separation is descriptive only and cannot satisfy Gate-6.

- trajectory control gate: **FAIL**
- qualifying control replicates: 2/3
- static frame-zero separation used: False
- reason: FAIL: control trajectories did not demonstrate trajectory-derived dynamics beyond static starting-state separation plus per-frame noise.

## Descriptive apo/control SASA contrast (not a gate)

- apo     (1W60) pocket SASA:  n/a
- control (8GLA) pocket SASA:  n/a
- control - apo: n/a  (Cohen's d n/a)
- independent replicates: n/a control / n/a apo; per-replicate consistent: n/a
- **Interpretable: False**
- apo/control complete pair unavailable; positive-control comparison requires both roles
- _Caveat:_ 

## Structure-prep caveats (read the gate WITH these)

- **8GLA**: biological assembly '1', 50 internal residues rebuilt by PDBFixer. (8GLA is 3.77 A - side-chain rotamers are modeled, not observed; treat pocket SASA magnitude as approximate.)
