---
type: phase5-zqz-chemistry-decision
ligand: ZQZ
date: 2026-06-11
status: APPROVED_HUMAN_REVIEW_RESOLVED
md_executed: false
launch_authorized: false
do_not_run_md: true
resolved_by: reports/phase5/human_review_decision_package_20260612.md
approved_charge_state: -1
supersedes_neutral_nc0: true
---

# ZQZ Protonation, Tautomer, And Net-Charge Decision Record - Phase 5 Wave 1

## Scope

This record documents the independent ZQZ chemistry review requested by the
2026-06-12 adversarial pre-launch audit (`reports/phase2/handoff_20260612.md`).
It does not authorize MD setup, ligand re-parameterization, minimization,
equilibration, production, trajectory generation, trajectory analysis, or claims.
The official Wave 1 package still records `do_not_run_md: true`.

This record fail-closes the Wave 1 prelaunch package until either a documented
re-parameterization at the chosen physiological charge state exists or a human
launch reviewer explicitly authorizes the current neutral form with the
sensitivity-analysis caveats below.

## Decision

**Status:** RESOLVED BY HUMAN REVIEW. The human launch reviewer approved
deprotonated ZQZ with net charge -1 on 2026-06-12 in
`reports/phase5/human_review_decision_package_20260612.md`.

**Approved scientific default for pH 7.4 free solution:** ZQZ net charge -1
(side-chain glutamic acid carboxylate deprotonated). This requires future
re-parameterization with `antechamber ... -nc -1` and a new audited package,
not the current `-nc 0` package.

**Neutral package status:** The current neutral (`-nc 0`) package is superseded
for production use. It remains preserved as a historical audit artifact only.

This resolution does not authorize MD. Future explicit human launch
authorization is still required. The current prelaunch state remains
`do_not_run_md: true`.

## Human Resolution

- Decision date: 2026-06-12.
- Reviewer role: human launch reviewer.
- Decision source: user instruction in Codex session, recorded in
  `reports/phase5/human_review_decision_package_20260612.md`.
- Approved option: deprotonated ZQZ, net charge `-1`.
- Required follow-up: replacement audited GAFF2/AM1-BCC package at net charge
  `-1`; neutral `-nc 0` package marked superseded for production use.
- Launch authorization: false.
- MD executed: false.

## Follow-Up Artifact Completion

The approved replacement package was generated on 2026-06-12:

- Active package:
  `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz_minus1/`
- Human-readable audit:
  `reports/phase5/zqz_minus1_parameter_audit_20260612.md`
- Machine-readable audit:
  `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz_minus1/zqz_minus1_parameter_audit.json`
- Package hashes:
  `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz_minus1/zqz_minus1_package_hashes.json`
- Neutral package supersession marker:
  `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz/SUPERSEDED_FOR_PRODUCTION_USE.md`

No protein system setup, minimization, equilibration, production, trajectory
generation, trajectory analysis, interpretation, launch authorization, or
claims were performed.

## Structural Evidence Used

Source files inspected on 2026-06-11 (no MD run):

| Path | SHA256 |
|---|---|
| `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz/zqz_input.sdf` | `0145ff68bcc1a86f84c61d1704edac18522a477e60e6a877eaf7f0c4a0759ae9` |
| `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz/sqm.in` | `efe843aaef228c6f3176900d593628ddeb6173bd0be8fd477c3217547ffa44e5` |
| `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz/zqz_parameter_audit.json` | `c667ea6e9e0bab0229b1386deb5473fa50371ef2d7bad1b3bccd0c25d8d6e2e7` |
| `data/raw_intake/pcna_structures/8GLA.cif` | `914f86a9ec6744143d8c9869643af58740d8a13e1d52f66b4fb8ec501a3ab487` |

External references inspected (no MD run):

- RCSB chemical component dictionary record for ZQZ: `https://files.rcsb.org/ligands/download/ZQZ.cif`.
- RCSB ideal SDF: `https://files.rcsb.org/ligands/download/ZQZ_ideal.sdf`.
- Deposited 8GLA structure metadata in `data/raw_intake/pcna_structures/8GLA_metadata.json`.

## Verified Structural Facts

The following facts are derived from the SDF connectivity table and the
SQM atom geometry that AmberTools26 generated for the current parameter package.
They are independent of the RCSB chemical-component name string.

1. The molecular formula is `C29H26N2O6`. The ligand contains exactly two
   nitrogen atoms.
2. The two nitrogen atoms (SDF atoms 30 and 31; sqm.in `N1` and `N2`) are both
   secondary amide nitrogens. `N1` is acylated by a naphthalene-1-carbonyl group;
   `N2` is attached to a 2-(3-methoxyphenoxy)phenyl ring and to the alpha-carbonyl
   carbon. Both are non-titratable at pH 7.4.
3. The side-chain delta carbon (SDF atom 28; sqm.in `C28`) carries:
   - a `C=O` bond to SDF atom 33 (sqm.in `O2`); SDF bond record `33-28` is order 2;
   - a `C-O` bond to SDF atom 34 (sqm.in `O3`); SDF bond record `28-34` is order 1;
   - a `C-C` bond to SDF atom 27 (sqm.in `C27`); SDF bond record `28-27` is order 1.
   The fourth coordination is implied by valence.
4. SDF atom 63 (sqm.in `H26`) is bonded to SDF atom 34 (`O3`); SDF bond record
   `34-63` is order 1. The O-H distance in the SDF coordinates is approximately
   0.97 Angstrom, consistent with an O-H covalent bond.
5. The side-chain group is therefore a free carboxylic acid `-C(=O)OH`, not a
   carboxamide `-C(=O)NH2`. If it were a carboxamide, the formula would require a
   third nitrogen.
6. The deposited 8GLA structure has six ZQZ ligand instances, each with 37 heavy
   atoms, formal charge 0, on auth chains A and B per the preparation audit.

The RCSB CCD descriptive name "N-[2-(3-methoxyphenoxy)phenyl]-N~2~-(naphthalene-1-carbonyl)-L-alpha-glutamine"
uses "alpha-glutamine" in the sense of an alpha-carboxamide capping of L-glutamic
acid, not a gamma-carboxamide side chain. The structure-derived classification
is the controlling fact for force-field parameterization.

## Bound-State pKa Considerations

1. The intrinsic aqueous pKa of a Glu/Asp-like aliphatic carboxylic acid is
   approximately 3.5-4.5 in solution. At pH 7.4 the deprotonated carboxylate is
   the dominant solution-state species by roughly three to four log units.
2. Local environment can shift apparent pKa values upward. Hydrophobic-pocket
   stabilization, nearby aromatic faces, and absence of nearby basic residues can
   raise apparent pKa values by 2-3 log units in some protein cases. Whether this
   applies to ZQZ in the 8GLA pocket is not established by the local repository
   evidence and would require explicit literature or independent calculation.
3. The 8GLA crystal structure resolution is 3.77 Angstrom and is below the
   <=3.5 Angstrom quality threshold per the 8GLA preparation audit. Hydrogen
   positions are not directly resolved at this resolution, so the deposited
   protonated form is not experimental evidence for a protonated bound state.
4. The RCSB ideal SDF intentionally provides a neutral, fully protonated
   chemistry representation suitable for general use; it is not a pH-7.4 microstate
   prediction.
5. The current package generated AM1-BCC charges for the neutral form. The
   electrostatic environment around the protonated `-COOH` differs materially from
   that around the deprotonated `-COO-`. Re-parameterization at `-nc -1` therefore
   cannot be approximated by post-hoc neutralization counterion shifts.

## Required Bound-State Evidence Before Any Neutral-Form MD

If a future human reviewer wishes to authorize Wave 1 MD with the current
neutral `-nc 0` ZQZ package, the launch authorization record must include all
of the following before launch:

1. A pKa-shift hypothesis identifying which 8GLA-bound contacts (residues per
   chain) stabilize the protonated form.
2. A literature citation or independent calculation (for example PROPKA, H++,
   PypKa, or an explicit constant-pH calculation) supporting a shifted apparent
   pKa above pH 7.4 in the bound state.
3. A pre-registered sensitivity plan that runs at least one bound-state replicate
   with `-nc -1` for `8gla_holo_zqz` and reports both outcomes honestly.
4. A documented planned-deviation entry under
   `docs/scientific_governance/14_CLAIM_POLICY.md` and the Wave 1 manifest
   templates that limits interpretation to "supportive MD evidence under the
   tested protonation policy".

Without these items, the prelaunch package must remain fail-closed and the
current ZQZ parameters must not be used for production MD.

## Required Re-Parameterization If Pre-Registered Charge State Changes

If the launch authorization adopts the recommended deprotonated `-nc -1` state:

1. Rebuild the ZQZ template input with the deprotonated alpha-side carboxylate.
   This may use the same RCSB ideal SDF as input but must remove the proton on
   atom 34 (`O3`) and use an explicit `-nc -1` flag.
2. Regenerate AM1-BCC charges via
   `antechamber -i zqz_input_minus1.sdf -fi sdf -o zqz_gaff2_am1bcc_minus1.mol2 -fo mol2 -at gaff2 -c bcc -nc -1 -rn ZQZ -s 2`.
3. Regenerate `parmchk2` GAFF2 fallback terms and a new audited tleap unit.
4. Write a new audited package `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz_minus1/`
   with `PARAMETER_AUDIT.md`, JSON audit, and package hashes following the same
   provenance template as the current neutral package.
5. Add a new chemistry-decision record entry that supersedes the neutral one and
   names the future human authorizer.
6. Re-link the new package from the future `8gla_holo_zqz` setup manifest. The
   current neutral package must be archived as `SUPERSEDED_DO_NOT_USE`.

## Allowed And Forbidden Language Until Decision Is Resolved

Allowed:

- "ZQZ protonation/net-charge state pending human decision".
- "Neutral GAFF2/AM1-BCC ZQZ parameters are not authorized for MD use without
  a bound-state pKa justification".
- "The current Wave 1 package is fail-closed pending the chemistry decision".

Forbidden:

- "ZQZ is neutral at pH 7.4" without a documented bound-state pKa justification.
- "AOH1996/ZQZ mechanism confirmed" or any equivalent claim.
- "Bound state of ZQZ is established by 8GLA" because 8GLA is 3.77 Angstrom
  resolution and hydrogen positions are not resolved.

## Evidence Status

Evidence status: structural facts verified from local SDF connectivity and
sqm.in geometry; pKa expectations cite general organic chemistry rather than
ZQZ-specific bound-state measurements. Confidence: high for structural identity
and intrinsic pKa range; low for any specific bound-state pKa value because no
ZQZ titration evidence exists in this repository.

Governance consulted: `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`,
`docs/scientific_governance/13_MD_VALIDATION_RULES.md`,
`docs/scientific_governance/14_CLAIM_POLICY.md`,
`docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md`,
`docs/scientific_governance/19_STOP_CONDITIONS.md`,
`docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`,
`docs/scientific_governance/33_PRE_MD_REALITY_CHECK.md`.
