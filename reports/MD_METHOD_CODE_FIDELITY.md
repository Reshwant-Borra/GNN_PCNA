# MD Method Code Fidelity

| Parameter | Documented value | Code location | Effective runtime value | Status |
|---|---|---|---|---|
| Force field | Amber14 | `run_md.py` `ForceField("amber14-all.xml", "amber14/tip3p.xml")` | Amber14 protein | PASS |
| Water | TIP3P | `build_system()` | `amber14/tip3p.xml`, `model="tip3p"` | PASS |
| Salt | 0.15 M NaCl | `--ionic` default, `addSolvent(... ionicStrength=args.ionic)` | 0.15 M | PASS |
| Temperature | 310 K | `--temp` default, Langevin/barostat | 310 K | PASS |
| Pressure | 1 bar | `--pressure` default, `MonteCarloBarostat` | 1 bar | PASS |
| PME | PME | `createSystem(nonbondedMethod=PME)` | PME | PASS |
| Cutoff | 1.0 nm | `nonbondedCutoff=1.0 * unit.nanometer` | 1.0 nm | PASS |
| Constraints | HBonds | `constraints=HBonds`, `rigidWater=True` | HBonds, rigid water | PASS |
| HMR | 4 amu | `--hmr-amu` default with HMR enabled | 4.0 amu hydrogens | PASS |
| Timestep | 4 fs | `dt = 4.0 if args.hmr else 2.0` | 4 fs default | PASS |
| Padding | 1.0 nm | `--padding` default | 1.0 nm | PASS |
| Equilibration | 2 ns | `--equil-ns` default | 2 ns | PASS |
| Output interval | 50 ps | `--report-ps` default | 50 ps DCD/log | PASS |
| Checkpoint cadence | 10 ps | `--checkpoint-ps` default in runbook/code | 10 ps atomic checkpoint | PASS |
| Integrator | Langevin | `LangevinMiddleIntegrator(args.temp, 1/ps, dt)` | LangevinMiddle, 1/ps | PASS |
| Barostat | Monte Carlo | `MonteCarloBarostat(..., 25)` | frequency 25 | PASS |
| CUDA precision | mixed | `--precision` default, launcher requires CUDA | mixed | PASS |
| Seeds | deterministic | `seed = 20260000 + rep`; integrator and barostat seeded | 20260001+ | PASS |

## Remaining Method Fidelity Limits

- CUDA and tmux were not available in this local environment, so runtime platform execution was not validated here.
- Production remains blocked by Gate-6 and unresolved GNN provenance.
- Frozen analysis protocol was reconciled after the static-control gate repair. Old claimed SHA-256: `2497def9e4675538dd08051ae6e5a448a41fbd32a1d7dc59cfb528d74d64ce3c`; current SHA-256: `587f27cf2e402fe50b264d98d3d60fbbdcc8f9095025b2a89d12c7aebd633e56`.
