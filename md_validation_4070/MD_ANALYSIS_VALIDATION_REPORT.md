# MD Analysis Validation Report

Status: PARTIAL STATIC PASS; TRAJECTORY VALIDATION PENDING.

## Static Reference Sanity Check

Prepared protein-only 1W60 and ligand-stripped 8GLA references were analyzed before candidate production.

| Region | 1W60 SASA (A^2) | 8GLA SASA (A^2) | Delta | 1W60 hull (A^3) | 8GLA hull (A^3) | Delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| core_3of3 | 471.714 | 530.919 | 59.205 | 184.252 | 185.313 | 1.061 |
| supported_ge2of3 | 778.027 | 839.109 | 61.082 | 511.12 | 610.253 | 99.133 |
| full_union_exploratory | 886.56 | 938.598 | 52.038 | 749.953 | 888.507 | 138.554 |

Atom parity is 100 percent for core, supported, and union heavy atoms in prepared static references.

## Trajectory Analysis Status

RMSD, RMSF, SASA, DCCM, PBC imaging, output frame count, and topology/trajectory pairing still require the exact smoke trajectory. Do not launch candidate production until that validation passes.

Machine-readable metrics: `static_reference_analysis.json`.
