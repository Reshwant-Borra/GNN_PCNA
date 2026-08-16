# MD Assumption And Source Audit

Generated: 2026-08-15T18:58:43.139697+00:00

| Choice | Current value | Source/evidence | Source type | Confidence | Alternative | Effect if wrong |
| --- | --- | --- | --- | --- | --- | --- |
| Starting apo structure | 1W60 | RCSB metadata title `NATIVE HUMAN PCNA`; local md handoff | direct | high | Other apo structures | Wrong starting state can make apo dynamics uninterpretable. |
| Positive-control/reference | 8GLA ligand-stripped protein | RCSB metadata title co-crystal with AOH1996 derivative; local positive-control docs | direct plus methodological inference | medium | No control or other holo structures | Control may not validate metric sensitivity if structural differences are unrelated or not stable after ligand stripping. |
| Biological assembly | Homotrimer assembly 1 for both structures | RCSB assembly metadata and run_md.py gemmi assembly construction | direct | high | ASU only | ASU-only simulation recurs the prior wrong-assembly failure. |
| Chain selection | Prepared chains A/B/C; primary candidate on chain index 0 | GNN handoff chain A and run_md chain renaming | direct/inferred | medium | Analyze all symmetry equivalents | Wrong chain mapping can test the wrong physical region. |
| Missing residues | Rebuild internal gaps with PDBFixer; do not fabricate terminal tails | run_md.py and prep_audit.json | methodological refinement | medium | Model all missing residues or none | Modeled loops, especially 8GLA 50 internal residues, may affect local geometry. |
| Histidines/protonation | PDBFixer hydrogens at pH 7.4; no manual histidine override | run_md.py defaults | inferred methodology | medium | Manual PROPKA/PDB2PQR review | Incorrect histidine tautomer/charge can perturb local H-bonding. |
| Disulfides | 8GLA has Cys135-Cys162 disulfides; 1W60 does not declare disulfides | 8GLA struct_conn and metadata | direct | high | Force matched disulfide state or use alternate control | Construct/oxidation difference may affect dynamics outside the pocket. |
| Ligands/cofactors | Remove ligands, ions, crystallographic waters before protein-only MD | run_md.py protein-only filter | methodological choice | medium | Parameterize ZQZ and retain ligand | Ligand-stripped control starts from open-like coordinates but may relax; it is not guaranteed to stay open. |
| Force field/water | Amber14 protein, TIP3P water | run_md.py and environment.yml | methodological choice | medium | CHARMM36m/OPC | Force-field choice affects flexibility and solvent exposure. |
| Salt/thermodynamic state | 0.15 M NaCl, 310 K, 1 bar | run_md.py defaults | methodological choice | medium | Crystal conditions or 300 K | Dynamics and stability may differ. |
| Timestep/HMR | 4 fs with HMR 4.0 amu, HBond constraints | run_md.py | methodological choice | medium | 2 fs no HMR | Too aggressive timestep could destabilize; smoke/equil gates must catch this. |
| Trajectory output | 50 ps default | run_md.py | methodological choice | medium | 10 ps or 100 ps | Event duration estimates are limited by output interval. |
| Analysis alignment | Protein CA excluding pocket | analyze_md.py and frozen protocol | methodological choice | medium | All CA or domain-specific alignment | Circular alignment can suppress pocket motion. |
| Pocket definition | Core primary, supported >=2/3 primary extension, full union exploratory | membership CSV and final handoff | direct | high | Treat all 20 equally | Boundary uncertainty can otherwise dominate interpretation. |
