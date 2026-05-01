# E003: MD Validation — RMSF + DCCM on Predicted Pockets

**Status:** planned
**Date started:** —
**Date completed:** —

→ Links: [[EXPERIMENT_INDEX]] | [[VALIDATION]] | [[PIPELINE]] | [[KNOWN_LIMITATIONS]]

---

## Hypothesis

Predicted novel cryptic pocket candidates on PCNA (from E002) will show elevated RMSF (> 1.5 Å) and a coherent DCCM block compared to background residues in a 100 ns explicit-solvent MD simulation of apo PCNA (1W60).

---

## Goal

Validate at least one novel predicted pocket using MD metrics. Required before claiming any novel cryptic site.

---

## Pipeline Stage

- Stage 6: MD Validation

---

## Data Used

| Type | Source | Path | Notes |
|---|---|---|---|
| MD trajectory | GROMACS/OpenMM self-generated | `data/trajectories/1W60_apo_100ns.xtc` | Not yet generated |
| Topology | Same simulation | `data/trajectories/1W60_apo.gro` | Not yet generated |
| Novel pocket list | From E002 | `results/pockets/novel_pockets.json` | Not yet generated |

---

## Code Files

| File | Status | Role |
|---|---|---|
| `src/md/parse_trajectory.py` | Stub | RMSF, DCCM, volume from trajectory |
| `src/evaluation/score_pockets.py` | Stub | Pocket ranking + residue selection |

---

## Blocking Dependencies

- [ ] E002 passes (pockets predicted)
- [ ] MD trajectory of 1W60 apo generated (50–100 ns, CHARMM36m, TIP3P, 150 mM NaCl)
- [ ] `src/md/parse_trajectory.py` implemented
- [ ] `src/evaluation/score_pockets.py` implemented
- [ ] MDAnalysis installed, fpocket/mdpocket available

---

## MD Simulation Parameters (target)

```yaml
force_field: CHARMM36m
water_model: TIP3P
salt: 150 mM NaCl
simulation_length: 100 ns
timestep: 2 fs
temperature: 310 K
pressure: 1 atm
integrator: Leap-frog
structure: 1W60 (apo, chain A monomer or full trimer)
```

---

## Validation Metrics

| Metric | Target | Actual |
|---|---|---|
| RMSF of pocket residues | > 1.5 Å | — |
| RMSF of background | ~0.5–1.0 Å | — |
| DCCM block coherence | Strong internal correlation | — |
| Pocket volume (max transient) | > 100 Å³ | — |
| Pocket volume (crystal frame) | ~0 Å³ | — |

---

## Results

_Not yet run._

---

## Interpretation

_Fill in after running._

---

## Limitations

- 100 ns may not be sufficient for cryptic pocket opening events (µs–ms timescale possible)
- RMSF is not directional — high RMSF ≠ pocket opening, must check with volume
- DCCM correlation does not imply causation
- If no pocket opens: consider metadynamics or enhanced sampling along pocket volume as CV
- Single trajectory — may not sample full conformational space

---

## Next Action

If E003 shows RMSF + DCCM evidence → extend with volume tracking and snapshot analysis.
If E003 fails to show dynamics → consider enhanced sampling (metadynamics with PLUMED).
