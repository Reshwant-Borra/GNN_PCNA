---
type: phase5-md-wave1-execution-package
date: 2026-06-09
status: PRE_EXECUTION_PACKAGE_ONLY
decision_id: phase5_gate7_wave1_authorization_20260609
authorization: reports/phase4/gate7_authorization_20260609.md
do_not_run_md: true
launch_authorized: false
governance:
  - docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md
  - docs/scientific_governance/13_MD_VALIDATION_RULES.md
  - docs/scientific_governance/14_CLAIM_POLICY.md
  - docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md
  - docs/scientific_governance/26_HUMAN_REVIEW_GATES.md
---

# Official Phase 5 MD Wave 1 Execution Package

## Status

This is the official Phase 5 MD Wave 1 execution package. It is a pre-execution
runbook, human-review decision record, and provenance plan only. The 2026-06-12
follow-up generated an audited ligand-only ZQZ replacement parameter package; no
MD system setup, minimization, equilibration, production run, trajectory
generation, trajectory analysis, interpretation, or claims were executed.

The deprecated time-crunch RunPod workflow is out of scope and must not be used for
this official Wave 1 plan.

## Authorization

Gate authorization:
`reports/phase4/gate7_authorization_20260609.md`

Primary decision package:
`reports/phase4/gate7_md_decision_draft_20260529.md`

The user explicitly instructed that MD must not be run yet. Execution remains on hold
until a later explicit launch authorization. Current package flags remain
`do_not_run_md: true` and `launch_authorized: false`.

## Wave 1 Scientific Scope

Wave 1 tests whether the model-prioritized PCNA regions show local dynamic
accessibility or pocket-like behavior under pre-registered, controlled MD setups.

MD is supportive evidence only. Negative and inconclusive outcomes are valid.

## Required Systems

| System ID | Starting structure | Ligand/partner state | Required replicates | Production length | Primary role |
|---|---|---|---:|---:|---|
| `8gla_holo_zqz` | PDB 8GLA | ZQZ retained | 3 | 100 ns each | AOH1996/ZQZ positive-control holo system |
| `8gla_apo_from_holo` | PDB 8GLA | ZQZ removed | 3 | 100 ns each | AOH1996/IDCL pocket persistence/collapse |
| `1axc_apo_from_p21` | PDB 1AXC | p21 peptides removed | 3 | 100 ns each | Tier 1A candidates and IDCL-adjacent control |

One `1axc_apo_from_p21` trajectory set is sufficient for the Wave 1 windows on that
same prepared structure: `239-243`, `28-32`, `206-210`, and `134-138`. Do not create
duplicate 1AXC production trajectories solely by residue window unless a later human
decision requests that.

## Candidate Windows

| Candidate ID | Residues | Tier | System | Interpretation role |
|---|---:|---|---|---|
| `PC-118` | 118-122 | 3 | `8gla_holo_zqz`, `8gla_apo_from_holo` | Positive control; AOH1996/IDCL sanity check |
| `T1A-239` | 239-243 | 1A | `1axc_apo_from_p21` | Top no-interface candidate |
| `T1A-28` | 28-32 | 1A | `1axc_apo_from_p21` | Second no-interface candidate; verify AOH1996-region independence |
| `T1A-206` | 206-210 | 1A | `1axc_apo_from_p21` | Third no-interface candidate |
| `T2-134` | 134-138 | 2 | `1axc_apo_from_p21` | IDCL/PIP-adjacent comparator; not a novel-site claim |

Tier 1B trimer-interface candidates (`170-174`, `175-179`, `152-156`) are not in this
execution package. They require Wave 2 enhanced-sampling planning and separate approval.

## Shared Setup Policy

Use this setup policy unless a deviation is documented before execution:

- PCNA assembly: biological trimer preserved.
- Protein force field: AMBER ff19SB.
- Water model: OPC.
- Ion policy: neutralize and use 150 mM NaCl with Joung-Cheatham OPC-compatible
  ion parameters.
- ZQZ ligand policy: use the approved deprotonated ZQZ package with net charge -1
  from `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz_minus1/`.
- Protonation: pH 7.4 standard-state policy, same across systems.
- Temperature/pressure: standard production MD settings must be recorded in the run
  manifest before launch.
- Seeds: fixed and recorded per replicate.
- Trajectory frame interval: choose before execution and use consistently across
  systems; record in `MANIFEST.md`.
- All setup scripts/commands must write input hashes, environment details, and command
  lines before production starts.

## Planned Seeds

| System ID | Replicate 1 | Replicate 2 | Replicate 3 |
|---|---:|---:|---:|
| `8gla_holo_zqz` | 2026060911 | 2026060912 | 2026060913 |
| `8gla_apo_from_holo` | 2026060921 | 2026060922 | 2026060923 |
| `1axc_apo_from_p21` | 2026060931 | 2026060932 | 2026060933 |

If any seed changes, record the reason in the system manifest before production.

## Structure Preparation Requirements

### 8GLA

- Verify deposited asymmetric unit and biological trimer assembly before production.
- Identify canonical PCNA chains and map residues to UniProt P12004 numbering.
- Record missing residues, insertion codes, alternate locations, non-PCNA chains,
  ions, waters, and ZQZ ligand placement.
- `8gla_holo_zqz`: retain ZQZ and use the approved audited ZQZ net-charge -1
  package before any future minimization.
- `8gla_apo_from_holo`: remove ZQZ from the same starting coordinates, then minimize
  and equilibrate under the same policy.
- Flag 8GLA resolution (3.77 Angstrom) in all manifests and interpretation; it is a
  force-included positive control only.

### 1AXC

- Verify biological PCNA trimer and PCNA chain mapping.
- Remove p21 peptide chains for `1axc_apo_from_p21`.
- Confirm the trimer remains intact and the IDCL/front-face region is not malformed
  after peptide removal and minimization.
- Record p21 removal as a setup transformation; do not treat 1AXC as a clean apo
  crystal structure.

## ZQZ Ligand Parameterization Requirement

Before any `8gla_holo_zqz` production run:

- use the approved deprotonated ZQZ net-charge -1 parameter package;
- record software versions, command lines, charge model, input ligand file, and output
  parameter hashes;
- confirm ZQZ chemistry, protonation/tautomer assumptions, and atom naming;
- run a setup audit for ligand connectivity and contacts before production.

Human review approved deprotonated ZQZ with net charge -1 on 2026-06-12. The active
audited GAFF2/AM1-BCC package is:

- `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz_minus1/PARAMETER_AUDIT.md`
- `reports/phase5/zqz_minus1_parameter_audit_20260612.md`

The previous neutral `-nc 0` package under
`outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz/` is superseded
for production use and retained only as historical provenance.

## Planned Output Root

Use this output root unless changed by a later launch instruction:

```text
outputs/phase5_md/official_wave1_20260609/
  MANIFEST.md
  inputs/
    8gla/
    1axc/
    ligand_params/zqz_minus1/
    ligand_params/zqz/  # superseded neutral package retained for provenance only
  systems/
    8gla_holo_zqz/
      setup_manifest.md
      replicate_01/
      replicate_02/
      replicate_03/
    8gla_apo_from_holo/
      setup_manifest.md
      replicate_01/
      replicate_02/
      replicate_03/
    1axc_apo_from_p21/
      setup_manifest.md
      replicate_01/
      replicate_02/
      replicate_03/
  analysis/
    trajectory_qa/
    rmsd_rmsf/
    pocket_accessibility/
    dccm/
    interface_distances/
    ligand_contacts/
```

Large trajectory outputs should remain outside git. Manifests, interpretation tables,
and human-review records should be committed when complete and reviewed.

## Future Execution Sequence

Do not execute these steps until the user explicitly authorizes launch.

1. Record git commit, branch, dirty-state summary, machine, and environment.
2. Prepare 8GLA and 1AXC input systems.
3. Link the approved audited ZQZ net-charge -1 ligand parameters.
4. Write setup manifests with input hashes.
5. Minimize each system.
6. Equilibrate each system under identical policy where comparable.
7. Run 3 x 100 ns production for each required system.
8. Write per-replicate completion records and output hashes.
9. Run trajectory QA before any scientific interpretation.
10. Run pre-registered analyses.
11. Produce an interpretation table.
12. Obtain human review of first MD interpretation.
13. Run claim audit before any report/manuscript claim.

## Stop Conditions Before Production

Do not start production if any condition below occurs:

- 8GLA biological trimer mapping is unresolved.
- 1AXC PCNA chain mapping is unresolved.
- Canonical residue numbering cannot be mapped for candidate windows.
- Active ZQZ net-charge -1 ligand parameters are missing or unaudited.
- Prepared systems lose PCNA trimer integrity during minimization/equilibration.
- Temperature, pressure, density, or energy behavior is unstable during equilibration.
- The output root already contains unregistered trajectory files.
- The environment or command provenance cannot be captured.

## Required Analyses After Future Runs

Trajectory QA must come first:

- replicate completion records;
- temperature, pressure, density, and energy stability;
- backbone RMSD per chain and full trimer;
- trimer integrity / inter-subunit distance checks;
- audit of any unstable or incomplete replicate.

Pre-registered scientific metrics:

- RMSD: backbone, per chain, versus starting structure.
- RMSF: per residue, focused on IDCL and candidate windows.
- Pocket/accessibility: AOH1996/ZQZ contact region and Tier 1A windows.
- DCCM: candidate-window coupling with IDCL/front-face and inter-subunit motions.
- Interface distances: pocket-framing distances for IDCL/front-face and candidate windows.
- Ligand stability/contact persistence: ZQZ heavy-atom contacts in `8gla_holo_zqz`.

The interpretation table must classify each candidate/system outcome as one of:
supports, partially supports, inconclusive, weakens, or contradicts.

## Claim Limits

Allowed language after reviewed analysis is limited to cautious computational wording,
such as "supportive MD evidence", "hypothesis-generating", "under the tested setup",
or "requires experimental validation".

Forbidden language includes validated binding site, druggable target, therapeutic
target, confirmed mechanism, clinically actionable, or proof of ligand binding.

## Package Verification Checklist

- [x] Gate 7 authorization record created.
- [x] Time-crunch workflow excluded.
- [x] Wave 1 systems specified.
- [x] Replicate count and production length specified.
- [x] Seeds specified.
- [x] Structure-preparation requirements specified.
- [x] ZQZ parameterization requirement specified.
- [x] Human review approved deprotonated ZQZ with net charge -1.
- [x] Neutral ZQZ `-nc 0` package marked superseded for production use.
- [x] Human review approved ff19SB + OPC with Joung-Cheatham OPC-compatible ions.
- [x] Output layout specified.
- [x] Stop conditions specified.
- [x] Post-run analysis and human-review gates specified.
- [x] MD execution not run.

## Evidence Status

Evidence status: pre-execution planning, human-review decisions, and ligand-only
ZQZ replacement parameter provenance. No MD system setup or MD outcome exists.

Confidence: high for governance scope and required systems; no confidence statement is
made about MD outcomes because no MD has been run.

