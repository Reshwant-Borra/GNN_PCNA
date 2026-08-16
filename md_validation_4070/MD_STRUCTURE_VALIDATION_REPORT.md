# MD Structure Validation Report

Generated: 2026-08-15T18:58:43.139697+00:00

Status: PASS FOR PREPARATION PREFLIGHT; NOT YET PRODUCTION READY because the 0.1 ns smoke and equilibration gates have not passed.

## Key Findings

- 1W60 assembly 1 protein chain count after operators: 3 (expected 3).
- 8GLA assembly 1 protein chain count after operators: 3 (expected 3).
- PDBFixer rebuilt 50 internal residues for 8GLA and 0 for 1W60.
- 8GLA is 3.77 A resolution and declares 4 disulfides, including Cys135-Cys162 per chain; 1W60 declares none.
- Prepared static heavy-atom parity for supported region: 116/116.
- Severe prepared-protein close contacts <1.5 A: 1W60=0, 8GLA=35.

## Default-Minimization Preflight

| System | Initial PE (kJ/mol) | Final PE (kJ/mol) | Initial max force | Final max force | Rebuilt internal residues | Solvated atoms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1W60 | -1.4e+06 | -2.61e+06 | 2.22e+05 | 2.68e+03 | 0 | 156106 |
| 8GLA | 2.82e+13 | -2.62e+06 | 6.88e+15 | 2.75e+03 | 50 | 156451 |

The high initial 8GLA energy reflects severe generated-coordinate/solvent contacts before minimization. Default minimization resolves this to finite negative energy, but production is still gated on smoke and equilibration stability.

Machine-readable details: `MD_STRUCTURE_VALIDATION.json`.
