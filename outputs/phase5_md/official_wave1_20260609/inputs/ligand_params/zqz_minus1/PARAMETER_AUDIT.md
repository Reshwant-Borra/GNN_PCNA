---
type: phase5-zqz-parameter-audit
ligand: ZQZ
date: 2026-06-12
status: PARAMETERS_AUDITED_READY_FOR_SETUP_USE
md_executed: false
launch_authorized: false
do_not_run_md: true
---

# ZQZ Minus-1 Parameter Audit - Phase 5 Wave 1

## Scope

This audit generated the ZQZ ligand-only AMBER parameter package required for the
future `8gla_holo_zqz` setup. It did not prepare protein systems, minimize,
equilibrate, run production MD, generate trajectories, analyze trajectories, or make
scientific claims.

## Parameterization Decision

- Ligand: ZQZ.
- Parameterization input: RCSB ideal SDF deprotonated at the free side-chain carboxyl group; neutral reference retained as `zqz_neutral_reference.sdf` and deprotonated input written as `zqz_minus1_input.sdf`.
- Deposited-coordinate audit: all ZQZ instances in `data/raw_intake/pcna_structures/8GLA.cif`
  were extracted to `deposited_8gla_zqz_instances.pdb` and indexed in JSON.
- Force field: GAFF2.
- Charge model: AM1-BCC through AmberTools `antechamber -c bcc`.
- Protonation state: deprotonated_sidechain_carboxylate.
- Net charge: -1.
- Residue name: ZQZ.
- Software package: AmberTools26 via `dacase::ambertools-dac=26.0.0`.


## Input Audit

- RCSB ideal SDF URL: `https://files.rcsb.org/ligands/download/ZQZ_ideal.sdf`.
- RCSB chemical component CIF URL: `https://files.rcsb.org/ligands/download/ZQZ.cif`.
- SDF formula: `C29H25N2O6-`.
- SDF atom count: 62 total,
  37 heavy.
- Explicit hydrogens present: `True`.
- RDKit formal charge: -1.
- Deposited 8GLA ZQZ instances: 6.

## Commands

| Step | Command | Exit |
|---|---|---:|
| antechamber | `antechamber -i zqz_minus1_input.sdf -fi sdf -o zqz_minus1_gaff2_am1bcc.mol2 -fo mol2 -at gaff2 -c bcc -nc -1 -rn ZQZ -s 2` | 0 |
| parmchk2 | `parmchk2 -i zqz_minus1_gaff2_am1bcc.mol2 -f mol2 -o zqz_minus1_gaff2.frcmod -s gaff2` | 0 |
| tleap | `tleap -f zqz_minus1_tleap.in` | 0 |

## Output Hashes

| Artifact | SHA256 | Size bytes |
|---|---|---:|
| `ANTECHAMBER_AC.AC` | `eb7ff8661bc28c67ec8cea41f385fb77a50bfaff2764296f6e9fbe92b1eafdd7` | 7103 |
| `ANTECHAMBER_AC.AC0` | `3bfaf980ddf162002d2146b26730e693889d74e0fca453b89089fa05d9e3f291` | 7103 |
| `ANTECHAMBER_AM1BCC.AC` | `b8031c7f15633e2ad0861e031b2350b1770aecf882025aa61cc9b43fa3377add` | 7103 |
| `ANTECHAMBER_AM1BCC_PRE.AC` | `1568d6b46cc3e5fb35329714f3beff36d049950121af6bbe31e32c5dba03068b` | 7103 |
| `ANTECHAMBER_BOND_TYPE.AC` | `3bfaf980ddf162002d2146b26730e693889d74e0fca453b89089fa05d9e3f291` | 7103 |
| `ANTECHAMBER_BOND_TYPE.AC0` | `3ac7d3d4cd62f77f9807635abfa7b3cfaefc92fe4bc2cf1cd31d61d1ba78901d` | 7103 |
| `ATOMTYPE.INF` | `32d63e08262b3431508c162e4551c6124e5a228db55675fccbdcd3d5c559f496` | 14221 |
| `ZQZ.cif` | `d06cd3f80bde14e5fd78eb90a57ad68b7e348af8024052422bd1a24b011833fb` | 11558 |
| `commands/antechamber.stderr.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 |
| `commands/antechamber.stdout.log` | `7c32b51d8237993349bb1a655d03665aa49ad02e3064d3ef0b6827aeb604b46e` | 1032 |
| `commands/parmchk2.stderr.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 |
| `commands/parmchk2.stdout.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 |
| `deposited_8gla_zqz_instances.json` | `87ca06d15002786cfa419a5a7536aff43d6f892be8d4aee205cdd2f0ffabbc5d` | 4523 |
| `deposited_8gla_zqz_instances.pdb` | `4cd7ab300ab602a3f12ab7f286ec8ca13b410e89dda007f085960d6fd81965ec` | 17542 |
| `leap.log` | `07ccfd1fc256447987d7b7de22b31b47d129e35ef2b7d09dd295a8886a53e737` | 7536 |
| `sqm.in` | `8c98a40b7ce3ba5e434c3df093655ef7bbf792899c26941f8802aa3db124460b` | 3481 |
| `sqm.out` | `7a84ce353cb2daa74f0887c64715804b29797d7ed5c5d4791b162b4fc7b5b47c` | 19718 |
| `sqm.pdb` | `26f454eff6ef5967840964dc8a9aa33697c846a7a70f2a592b82efd8e979cf8d` | 4898 |
| `zqz_minus1_gaff2.frcmod` | `5d54f0a0bd6389338c5819b7f2b67329cd49c8a7aca81ccbf4f2dd92a97e3d7e` | 2358 |
| `zqz_minus1_gaff2.lib` | `f15cfbd04aab8d27c1802540c769460f2cc0e0ab29ba72c656b09feeb417671f` | 8646 |
| `zqz_minus1_gaff2_am1bcc.mol2` | `a3c4aa562542e18ba2b45f16982ca4e39e111f8dab47ccc27452e9cdf38aeac3` | 6820 |
| `zqz_minus1_input.sdf` | `c6b5546cf152dc2f7b5f3dc1dc6c7db0aa73554026352fc9a2e87f77ee9ba0d6` | 5278 |
| `zqz_minus1_tleap.in` | `3a7468ad1180d9413bdf0a513c34717e601d21312e6e38fca5b6603f45e7ab4b` | 152 |
| `zqz_minus1_tleap.log` | `bc777e5637d50a43fbc5fbb34e6a4e3bf5c5408f53a5715b9124ef0647ce6884` | 1433 |
| `zqz_neutral_reference.sdf` | `0145ff68bcc1a86f84c61d1704edac18522a477e60e6a877eaf7f0c4a0759ae9` | 4419 |
| `zqz_minus1_parameter_audit.json` | `0f1af876c22599eef73d15f3a8f209df7634916fa4c14c91e529111522122e4c` | 41230 |

## Parameter Checks

- MOL2 atom count: 62.
- MOL2 charge sum: -0.998999.
- `tleap` check: Unit is OK; `Exiting LEaP: Errors = 0; Warnings = 1; Notes = 0.`.
- `parmchk2` generated GAFF2 fallback terms in `zqz_minus1_gaff2.frcmod`; these are retained
  and must be linked from future setup manifests.

## Software And Environment

- Platform: `Linux-5.15.167.4-microsoft-standard-WSL2-x86_64-with-glibc2.39`.
- Python: `3.12.13 | packaged by conda-forge | (main, Mar  5 2026, 16:50:00) [GCC 14.3.0]`.
- AMBERHOME: `/root/.local/share/mamba/envs/AmberTools26`.
- CONDA_PREFIX: `/root/.local/share/mamba/envs/AmberTools26`.
- ambertools-dac package: `26.0.0`
  build `py312h2009f2f_0`.

## Remaining Launch Blockers

- Official package still records do_not_run_md: true; execution remains on hold.
- Future explicit Phase 5 launch authorization record is absent.

## Warnings

- ZQZ parameters are ligand-only inputs for future setup; they are not MD results.
- Future 8GLA setup manifest must link PARAMETER_AUDIT.md and all parameter file hashes before minimization.
- The prior neutral -nc 0 package is superseded for production use by human review decision.

## Evidence Status

Evidence status: verified parameter-generation and provenance audit. Confidence: high
for file hashes, command provenance, and `tleap` ligand-unit check. No MD outcome or
biological interpretation exists.
