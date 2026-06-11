---
type: phase5-ligand-parameterization-plan
ligand: ZQZ
date: 2026-06-10
status: PLAN_ONLY_PARAMETERS_NOT_GENERATED
md_executed: false
---

# ZQZ Parameterization Plan - Phase 5 Wave 1

## Official Workflow

Use AMBER-compatible ligand parameters for the `8gla_holo_zqz` system:

- Protein force field: AMBER ff19SB, as specified in the official Wave 1 package.
- Ligand force field: GAFF2.
- Charge method: AM1-BCC through AmberTools `antechamber` (`-c bcc`), unless a later
  documented deviation is approved before launch.
- Proposed net charge: 0, based on the RCSB ZQZ ligand record formal charge 0. This
  must be re-verified from the exact protonated input before parameter generation.
- Required tools: AmberTools26 `antechamber`, `parmchk2`, `tleap`, and `sqm`.

AmberTools26 is selected because the official AmberTools page identifies AmberTools26
as available and lists `antechamber`, `tleap`, `sqm`, and GAFF2-related updates. Record
the exact local executable versions at launch time; do not substitute an older version
without planned-deviation documentation.

## Required Inputs

- Deposited 8GLA mmCIF hash from `data/raw_intake/pcna_structures/8GLA.cif`.
- Extracted ZQZ coordinate file with all deposited ZQZ instances tracked.
- Single audited ligand template input for parameterization, with explicit hydrogens,
  stereochemistry, protonation/tautomer state, atom names, residue name `ZQZ`, and
  net charge.
- Human-readable ligand audit note confirming whether the deposited ligand state is
  used as-is or rebuilt from RCSB ideal SDF.

## Required Outputs

- `zqz_gaff2_am1bcc.mol2`
- `zqz_gaff2.frcmod`
- `zqz_tleap.in`
- `zqz_tleap.log`
- `zqz_parameter_audit.json`
- `PARAMETER_AUDIT.md`

All outputs must include SHA256 hashes, generation commands, AmberTools version strings,
input hashes, net charge, atom count, warning/error logs, and manual-review notes.

## Fail-Closed Behavior

Future production setup must refuse to continue if
`outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz/PARAMETER_AUDIT.md`
is absent, incomplete, or not linked from the system setup manifest. This turn intentionally
does not generate production parameters.

## Example Future Commands

These commands are documentation only and must not be run until launch is explicitly
authorized:

```bash
antechamber -i zqz_input.sdf -fi sdf -o zqz_gaff2_am1bcc.mol2 -fo mol2 -at gaff2 -c bcc -nc 0 -rn ZQZ
parmchk2 -i zqz_gaff2_am1bcc.mol2 -f mol2 -o zqz_gaff2.frcmod -s gaff2
tleap -f zqz_tleap.in
```

Evidence status: plan only. Confidence: high for required workflow shape; parameter
quality remains unaudited until outputs exist.
