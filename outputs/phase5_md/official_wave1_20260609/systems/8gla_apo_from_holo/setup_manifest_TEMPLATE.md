# Setup Manifest Template - 8gla_apo_from_holo

- System ID: `8gla_apo_from_holo`
- Status: TEMPLATE_ONLY_DO_NOT_RUN
- Starting structure: 8GLA
- Ligand/partner state: ZQZ removed
- Required replicates: 3
- Planned production length: 100 ns per replicate
- Seeds: 2026060921, 2026060922, 2026060923
- Protein force field: AMBER ff19SB
- Water model: OPC
- Ion policy: neutralize and 150 mM NaCl using OPC-compatible ions
- Ion parameters: Joung-Cheatham OPC-compatible ions
- Protonation policy: pH 7.4 standard-state policy, identical across comparable systems
- Input coordinate hash:
- Prepared coordinate hash:
- Topology hash:
- ZQZ parameter audit path: `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz_minus1/PARAMETER_AUDIT.md`
- ZQZ parameter hashes: `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz_minus1/zqz_minus1_package_hashes.json`
- Environment:
- Commands:
- Stop conditions triggered:
- Manual deviations:

Do not use this template as evidence of a completed setup. A future launch run must
copy it to `setup_manifest.md`, fill every required field, and link audited inputs.
