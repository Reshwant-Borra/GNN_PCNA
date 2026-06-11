# ZQZ Ligand Parameter Placeholder

Status: TEMPLATE_ONLY_PARAMETERS_NOT_GENERATED

Required before production:

- `zqz_gaff2_am1bcc.mol2`
- `zqz_gaff2.frcmod`
- `zqz_tleap.in`
- `zqz_tleap.log`
- `zqz_parameter_audit.json`
- `PARAMETER_AUDIT.md`

Production setup must fail closed until `PARAMETER_AUDIT.md` exists and records input
hashes, output hashes, AmberTools versions, charge method, net charge, command lines,
warnings, and manual review.
