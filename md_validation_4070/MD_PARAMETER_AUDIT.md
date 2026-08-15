# MD Parameter Audit

Generated: 2026-08-15T18:58:43.139697+00:00

| Parameter | Current value | Source | Original methodology specified? | Appropriateness |
| --- | --- | --- | --- | --- |
| Force field | amber14-all.xml | run_md.py | Project methodology choice | Standard protein force field, acceptable for exploratory PCNA MD |
| Water model | amber14/tip3p.xml | run_md.py | Project methodology choice | Consistent with Amber14 default |
| Ions | neutralized, 0.15 M NaCl | run_md.py | Project methodology choice | Physiological-strength salt assumption |
| Temperature | 310 K | run_md.py | Project methodology choice | Human physiological temperature; not chosen to force opening |
| Pressure | 1 bar | run_md.py | Project methodology choice | Standard NPT pressure |
| Box | 1.0 nm solvent padding | run_md.py | Project methodology choice | Reasonable minimum padding; verify no self-contact after equilibration |
| Constraints | HBonds, rigid water | run_md.py | Project methodology choice | Standard with 2-4 fs biomolecular MD |
| HMR/timestep | HMR 4.0 amu, 4 fs | run_md.py | Methodological refinement | Efficient but must pass smoke/equilibration gates |
| Nonbonded | PME, 1.0 nm cutoff | run_md.py | Project methodology choice | Standard periodic electrostatics |
| Thermostat | LangevinMiddle, 1/ps friction | run_md.py | Project methodology choice | Standard OpenMM integrator |
| Barostat | MonteCarloBarostat, frequency 25 | run_md.py | Project methodology choice | NPT from start; objective density/box checks required |
| Minimization | 5000 iterations default | run_md.py | Project methodology choice | Preflight finite; final max forces require equilibration monitoring |
| Equilibration | 2.0 ns default | run_md.py | Project methodology choice | Must be judged by criteria in EQUILIBRATION_ACCEPTANCE_CRITERIA.json |
| Output | DCD/log every 50 ps | run_md.py | Project methodology choice | Adequate for broad events, not sub-50 ps kinetics |
| Platform | CUDA default; `md.sh` requires CUDA for MD stages with `--require-platform`; raw `run_md.py` can fall back to CPU unless `--require-platform` is supplied | run_md.py, md.sh | Runtime choice | Production should use CUDA/validated GPU, not accidental slow CPU |
| CUDA precision | mixed | run_md.py | Runtime choice | Current launcher/script default for CUDA |

No parameter was changed to encourage pocket opening. Current status is smoke-ready/preflight-ready, not production-approved.
