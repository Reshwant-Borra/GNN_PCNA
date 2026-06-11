---
type: phase5-zqz-parameter-audit
ligand: ZQZ
date: 2026-06-11
status: PARAMETERS_AUDITED_READY_FOR_SETUP_USE
md_executed: false
---

# ZQZ Parameter Audit - Phase 5 Wave 1

## Scope

This audit generated the ZQZ ligand-only AMBER parameter package required for the
future `8gla_holo_zqz` setup. It did not prepare protein systems, minimize,
equilibrate, run production MD, generate trajectories, analyze trajectories, or make
scientific claims.

## Parameterization Decision

- Ligand: ZQZ.
- Parameterization input: RCSB ideal SDF, copied as `zqz_input.sdf`.
- Deposited-coordinate audit: all ZQZ instances in `data/raw_intake/pcna_structures/8GLA.cif`
  were extracted to `deposited_8gla_zqz_instances.pdb` and indexed in JSON.
- Force field: GAFF2.
- Charge model: AM1-BCC through AmberTools `antechamber -c bcc`.
- Net charge: 0.
- Residue name: ZQZ.
- Software package: AmberTools26 via `dacase::ambertools-dac=26.0.0`.

## Input Audit

- RCSB ideal SDF URL: `https://files.rcsb.org/ligands/download/ZQZ_ideal.sdf`.
- RCSB chemical component CIF URL: `https://files.rcsb.org/ligands/download/ZQZ.cif`.
- SDF formula: `C29H26N2O6`.
- SDF atom count: 63 total,
  37 heavy.
- Explicit hydrogens present: `True`.
- RDKit formal charge: 0.
- Deposited 8GLA ZQZ instances: 6.

## Commands

| Step | Command | Exit |
|---|---|---:|
| antechamber | `antechamber -i zqz_input.sdf -fi sdf -o zqz_gaff2_am1bcc.mol2 -fo mol2 -at gaff2 -c bcc -nc 0 -rn ZQZ -s 2` | 0 |
| parmchk2 | `parmchk2 -i zqz_gaff2_am1bcc.mol2 -f mol2 -o zqz_gaff2.frcmod -s gaff2` | 0 |
| tleap | `tleap -f zqz_tleap.in` | 0 |

## Output Hashes

| Artifact | SHA256 | Size bytes |
|---|---|---:|
| `ANTECHAMBER_AC.AC` | `28ec357344a28d18b97e53a0f3564a1d4aa34dc7ba3be5c268a538b6ac92c2ca` | 7214 |
| `ANTECHAMBER_AC.AC0` | `8275175a3640f7e1c6762ced26eddb7751463f54df1e1f97ff557c08341a6679` | 7214 |
| `ANTECHAMBER_AM1BCC.AC` | `ffbf3325a9cb0de88cabdada699fdd23eb31c49a6dc50c5661904438d31ecf53` | 7214 |
| `ANTECHAMBER_AM1BCC_PRE.AC` | `aca325262258fcb9a469e52d2277d983ce639bd3f4410a2769d468fbdbe546f7` | 7214 |
| `ANTECHAMBER_BOND_TYPE.AC` | `8275175a3640f7e1c6762ced26eddb7751463f54df1e1f97ff557c08341a6679` | 7214 |
| `ANTECHAMBER_BOND_TYPE.AC0` | `22df6be3b7154bfce9fd788c64e327dec46c0672e7378d2c42eceba55dabb412` | 7214 |
| `ATOMTYPE.INF` | `f82a1b095fb21c7b2d422bb6527289e8b34f52ac36e68725cd209794765fe62a` | 14373 |
| `README_TEMPLATE.md` | `75b7811e0f2c07084e3de4a61ccf7010c6014fff7e1547b108d5bbfdff26a7c6` | 536 |
| `ZQZ.cif` | `d06cd3f80bde14e5fd78eb90a57ad68b7e348af8024052422bd1a24b011833fb` | 11558 |
| `commands/antechamber.stderr.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 |
| `commands/antechamber.stdout.log` | `7c32b51d8237993349bb1a655d03665aa49ad02e3064d3ef0b6827aeb604b46e` | 1032 |
| `commands/parmchk2.stderr.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 |
| `commands/parmchk2.stdout.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 |
| `deposited_8gla_zqz_instances.json` | `87ca06d15002786cfa419a5a7536aff43d6f892be8d4aee205cdd2f0ffabbc5d` | 4523 |
| `deposited_8gla_zqz_instances.pdb` | `4cd7ab300ab602a3f12ab7f286ec8ca13b410e89dda007f085960d6fd81965ec` | 17542 |
| `leap.log` | `c8adc0e4d14acb2deed22c754a540620efe26dd37bc0484481c37b7ce3cac710` | 14324 |
| `sqm.in` | `efe843aaef228c6f3176900d593628ddeb6173bd0be8fd477c3217547ffa44e5` | 3534 |
| `sqm.out` | `ae5c4e1a38e196ad3f305cc500f5ae786d0a17db9e76e2d40958af9ce66a835b` | 19729 |
| `sqm.pdb` | `54954af6b432eaaf70e5249863dbbb0892837913489893703108e468ff5ee874` | 4977 |
| `zqz_gaff2.frcmod` | `080fa468a97f71948dc571d070727aaff4fd115c1d52983280f673cb0415b430` | 2225 |
| `zqz_gaff2.lib` | `3ebc718f0c08f1db38eb33303d75c30bafddf2fc271ecbfbcd8a2acc6ff9243e` | 8773 |
| `zqz_gaff2_am1bcc.mol2` | `a3056f06d64231fd55df83b28a4ed4759adcfa3fba31427c4c41609b641a61a3` | 6926 |
| `zqz_input.sdf` | `0145ff68bcc1a86f84c61d1704edac18522a477e60e6a877eaf7f0c4a0759ae9` | 4419 |
| `zqz_tleap.in` | `95db50242da74531cddcbd57e828c2ea4cda601d21a6791269c92bbde8f0d71b` | 131 |
| `zqz_tleap.log` | `9573480efe3400065431fd7b657f31145856e496ea563ccb570ece33e07ecc63` | 1253 |
| `zqz_parameter_audit.json` | `c667ea6e9e0bab0229b1386deb5473fa50371ef2d7bad1b3bccd0c25d8d6e2e7` | 38777 |

## Parameter Checks

- MOL2 atom count: 63.
- MOL2 charge sum: -0.003.
- `tleap` check: Unit is OK; errors 0, warnings 0, notes 0.
- `parmchk2` generated GAFF2 fallback terms in `zqz_gaff2.frcmod`; these are retained
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

## Evidence Status

Evidence status: verified parameter-generation and provenance audit. Confidence: high
for file hashes, command provenance, and `tleap` ligand-unit check. No MD outcome or
biological interpretation exists.
