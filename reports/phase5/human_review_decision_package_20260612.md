---
type: phase5-human-review-decision-package
date: 2026-06-12
status: APPROVED_DECISIONS_RECORDED_FOLLOWUP_ARTIFACTS_COMPLETE_LAUNCH_BLOCKED
scope: close-scientific-decision-blockers-only
md_executed: false
launch_authorized: false
do_not_run_md: true
supersedes_launch_hold: false
review_decision: approved
reviewer_role: human-launch-reviewer
zqz_decision: deprotonated_net_charge_minus1
force_field_water_decision: ff19SB_OPC_Joung_Cheatham_OPC_ions
followup_artifacts_status: complete
decision_records:
  - reports/phase5/zqz_chemistry_decision_20260611.md
  - reports/phase5/force_field_water_policy_decision_20260611.md
governance:
  - docs/scientific_governance/13_MD_VALIDATION_RULES.md
  - docs/scientific_governance/14_CLAIM_POLICY.md
  - docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md
  - docs/scientific_governance/19_STOP_CONDITIONS.md
  - docs/scientific_governance/21_READINESS_GATE.md
  - docs/scientific_governance/26_HUMAN_REVIEW_GATES.md
  - docs/scientific_governance/33_PRE_MD_REALITY_CHECK.md
  - docs/scientific_governance/34_AI_HALLUCINATION_DETECTION.md
---

# Phase 5 Wave 1 Human-Review Decision Package

## Scope And Non-Authorization Statement

This package is for human review of the two remaining scientific decision
blockers before any future Phase 5 launch authorization can be considered:

1. ZQZ protonation and net-charge state.
2. Force-field and water-model policy.

The human review decision recorded here authorizes ligand-only ZQZ
re-parameterization as a follow-up artifact. It does not authorize protein
system setup, minimization, equilibration, production, trajectory generation,
trajectory analysis, interpretation, claims, or launch. It does not modify
`do_not_run_md: true` in the official Wave 1 package and does not create a
Phase 5 launch authorization.

Current launch verdict remains `STILL_NOT_READY_FOR_LAUNCH`.

## Approved Human Review Decisions

Decision source: user instruction in the Codex session on 2026-06-12.

Reviewer role: human launch reviewer.

Launch authorization status: not authorized.

MD execution status: not run.

Approved ZQZ decision:

- Deprotonated ZQZ is approved as the official Wave 1 ligand microstate.
- Net charge is approved as `-1`.
- A replacement audited GAFF2/AM1-BCC parameter package is required before
  future setup use.
- The prior neutral `-nc 0` package must be marked superseded for production
  use.

Approved force-field/water decision:

- AMBER ff19SB is approved as the official Wave 1 protein force field.
- OPC is approved as the official Wave 1 water model.
- Joung-Cheatham OPC-compatible ions are approved as the official Wave 1 ion
  parameter policy.

Follow-up artifacts required by the approval:

- [x] Generate replacement audited ZQZ `-1` parameter package.
- [x] Mark neutral `-nc 0` package superseded for production use.
- [x] Update manifest templates to ff19SB + OPC + Joung-Cheatham OPC-compatible ions.
- [x] Update readiness report.
- [x] Update provenance records.
- [x] Update fail-closed checks.

This approval closes the two scientific decision choices only. It does not
authorize MD launch.

## Follow-Up Artifact Completion

Completed on 2026-06-12:

- Replacement audited ZQZ `-1` package:
  `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz_minus1/`.
- Human-readable `-1` audit:
  `reports/phase5/zqz_minus1_parameter_audit_20260612.md`.
- Neutral package supersession marker:
  `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz/SUPERSEDED_FOR_PRODUCTION_USE.md`.
- Updated manifest templates:
  `outputs/phase5_md/official_wave1_20260609/MANIFEST_TEMPLATE.md` and
  `outputs/phase5_md/official_wave1_20260609/systems/*/setup_manifest_TEMPLATE.md`.
- Updated readiness report:
  `reports/phase5/wave1_readiness_report_20260610.md`.
- Updated provenance registry:
  `data/registries/phase5_wave1_preparation_audit_20260610.json`.
- Updated fail-closed checks:
  `src/phase5_md/wave1.py` and `tests/phase5/test_wave1_preflight.py`.

Production status remains `BLOCKED_FAIL_CLOSED`.

## Evidence Packet Reviewed

Primary decision records:

- `reports/phase5/zqz_chemistry_decision_20260611.md`
- `reports/phase5/force_field_water_policy_decision_20260611.md`

Current package and readiness records:

- `reports/phase5/official_wave1_execution_package_20260609.md`
- `reports/phase5/wave1_readiness_report_20260610.md`
- `reports/phase5/zqz_parameter_audit_20260611.md`
- `outputs/phase5_md/official_wave1_20260609/inputs/ligand_params/zqz/PARAMETER_AUDIT.md`

Governance constraints:

- `docs/scientific_governance/13_MD_VALIDATION_RULES.md`
- `docs/scientific_governance/14_CLAIM_POLICY.md`
- `docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md`
- `docs/scientific_governance/19_STOP_CONDITIONS.md`
- `docs/scientific_governance/21_READINESS_GATE.md`
- `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`
- `docs/scientific_governance/33_PRE_MD_REALITY_CHECK.md`
- `docs/scientific_governance/34_AI_HALLUCINATION_DETECTION.md`

## Decision 1: ZQZ Protonation And Net Charge

### Decision Required

The reviewer must select the ZQZ protonation/net-charge policy for future Wave 1
planning:

- Option A: retain the current neutral `-nc 0` GAFF2/AM1-BCC package only with
  a documented bound-state pKa-shift justification and sensitivity plan.
- Option B: adopt deprotonated ZQZ at net charge `-1` as the default pH 7.4
  state and require a new audited ligand-parameter package before any future
  setup use.

### Evidence For Neutral ZQZ

- The current audited ZQZ parameter package was generated as neutral
  GAFF2/AM1-BCC with `antechamber ... -nc 0`.
- The RCSB ideal SDF and chemical-component representation encode a neutral,
  fully protonated ligand form.
- A neutral bound form could be scientifically defensible if the protein pocket
  shifts the relevant carboxyl pKa upward enough to keep the side-chain
  carboxyl group protonated near pH 7.4.

Limitations of the neutral evidence:

- The RCSB ideal SDF is a chemistry representation, not a pH 7.4 microstate
  prediction.
- The 8GLA resolution is 3.77 Angstrom, so hydrogen positions are not resolved
  and do not establish the bound protonation state.
- No repository evidence currently documents a ZQZ-specific bound-state pKa
  shift.
- Neutral `-nc 0` changes ligand electrostatics materially relative to a
  carboxylate and cannot be treated as a harmless counterion-only difference.

### Evidence For Net Charge -1

- The SDF connectivity and generated SQM geometry show a free side-chain
  carboxylic acid: atom 28 is bonded as `C=O` to atom 33 and `C-O` to atom 34,
  and atom 34 is bonded to hydrogen atom 63.
- The molecular formula `C29H26N2O6` contains only two nitrogen atoms. A
  side-chain carboxamide interpretation would require an additional nitrogen.
- The ligand therefore contains a Glu-like free carboxyl group, not a
  side-chain amide.
- For a typical aliphatic carboxylic acid, the dominant solution-state form at
  pH 7.4 is deprotonated. The exact bound-state pKa for ZQZ in 8GLA remains
  unmeasured in this repository.

Limitations of the `-1` evidence:

- The solution-state pH 7.4 expectation does not prove the bound state in the
  8GLA pocket.
- A sufficiently shifted bound-state pKa could make neutral ZQZ plausible, but
  that requires explicit evidence or calculation before relying on the neutral
  package.

### Recommended Choice

Recommended reviewer decision: **Option B, adopt ZQZ net charge `-1` as the
default pH 7.4 policy and require re-parameterization before any future setup
use.**

Reason: the structure-derived chemistry identifies a free carboxylic acid, and
the repository does not currently contain ZQZ-specific evidence that the bound
state remains neutral at pH 7.4. This recommendation is a conservative
scientific default, not a launch authorization.

### Consequences Of Each Choice

| Choice | Consequences |
|---|---|
| Neutral `-nc 0` with documented pKa-shift justification | Current ligand package may remain a candidate setup input only after the reviewer records the pKa-shift hypothesis, pocket-contact rationale, evidence or calculation, and sensitivity plan. Interpretation must be limited to the tested protonation policy. Risk remains that ZQZ electrostatics and contacts reflect an unjustified protonated carboxyl group. |
| Neutral `-nc 0` without pKa-shift justification | Not acceptable for future Wave 1 setup use. The current fail-closed blocker remains open. |
| Net charge `-1` | Requires a new deprotonated ZQZ input, new `antechamber ... -nc -1` AM1-BCC charges, new GAFF2/tleap audit, new hashes, and updated setup manifests before any future use. The current neutral package should be archived or marked superseded for production use if the `-1` package replaces it. This choice better matches the default pH 7.4 chemistry but adds rework before any later launch can be considered. |

### Reviewer Sign-Off: ZQZ

Reviewer decision:

- [x] Approve deprotonated ZQZ, net charge `-1`, and require new audited
      parameter package before future setup use.
- [ ] Approve neutral ZQZ, net charge `0`, only with the bound-state pKa-shift
      justification and sensitivity plan recorded below.
- [ ] Reject both options pending additional chemistry review.

Required reviewer fields:

- Reviewer name: not specified in prompt; recorded by role.
- Reviewer role: human launch reviewer.
- Decision date: 2026-06-12.
- Selected option: deprotonated ZQZ, net charge `-1`.
- Required follow-up artifacts: replacement audited ZQZ `-1` package; neutral
  package supersession marker; updated manifests, readiness report, provenance,
  and preflight checks.
- Evidence or calculation supporting selected option: structural evidence in
  `reports/phase5/zqz_chemistry_decision_20260611.md`; human review approval
  recorded in this package.
- Sensitivity analysis required, if any: none required by this approval before
  package replacement; any future MD interpretation remains governed by doc 13.
- Limitations to carry into any future manifest: ligand-only re-parameterization
  is not MD execution, setup, trajectory evidence, interpretation, or a claim.
- Signature: approved by human launch reviewer instruction in Codex session.

## Decision 2: Force Field And Water Model

### Decision Required

The reviewer must select the force-field/water-model policy for future Wave 1
planning:

- Option A: `ff19SB + OPC` with Joung-Cheatham OPC-compatible ions.
- Option B: `ff19SB + TIP3P` as a documented deviation.
- Option C: another documented policy, such as `ff14SB + TIP3P`, only with a
  specific rationale and revised manifests.

### Evidence For ff19SB + OPC

- The force-field/water decision record identifies `ff19SB + OPC` as the
  internally consistent default because ff19SB was parameterized and validated
  with OPC.
- OPC better reproduces several bulk water properties than TIP3P, reducing a
  known solvent-model systematic for a study where solvent-mediated
  accessibility and local dynamics are central observables.
- Using the same ff/water/ion policy across `8gla_holo_zqz`,
  `8gla_apo_from_holo`, and `1axc_apo_from_p21` supports controlled comparison
  under the MD governance rules.

Limitations of `ff19SB + OPC`:

- It may require updated ion parameters and engine/environment checks.
- Existing package text currently lists TIP3P, so adopting OPC requires a
  recorded policy update before any future setup work.
- No prepared-system benchmark exists yet, so runtime, stability, and storage
  consequences remain planning assumptions.

### Evidence For ff19SB + TIP3P

- The official Wave 1 package currently lists AMBER ff19SB with TIP3P water.
- TIP3P is widely used in legacy Amber workflows and may be easier to align
  with older literature or engine environments.
- It may be defensible if a reviewer records a compatibility or
  literature-replication rationale before any future setup.

Limitations of `ff19SB + TIP3P`:

- It removes the water-model consistency used in ff19SB development.
- The decision record flags potential bias in helix stability and side-chain
  flexibility, which are relevant to RMSF, DCCM, and pocket-accessibility
  comparisons.
- It must be treated as a documented deviation, not the scientific default.

### Recommended Choice

Recommended reviewer decision: **Option A, `ff19SB + OPC` with
Joung-Cheatham OPC-compatible ions as the default Wave 1 policy.**

Reason: it is the most internally consistent ff19SB pairing and better aligned
with a comparative cryptic-pocket dynamics study. This recommendation is a
policy choice for future setup planning only; it does not authorize MD.

### Consequences Of Each Choice

| Choice | Consequences |
|---|---|
| `ff19SB + OPC` | Requires updating future setup manifests to OPC, naming OPC-compatible ion parameters, and ensuring the selected engine/environment supports the policy. It preserves ff19SB/water-model consistency and is the recommended default for future Wave 1 setup planning. |
| `ff19SB + TIP3P` | Avoids changing the current package text and may improve compatibility with legacy workflows, but it must be recorded as a planned deviation. Future interpretation must be limited to "under the ff19SB + TIP3P setup" and must not make absolute stability, transition, or broad mechanism claims from this pairing. |
| Other documented policy, such as `ff14SB + TIP3P` | Requires a specific literature-replication or compatibility rationale, revised manifests, and clear labeling as a deviation from the recommended default. Comparability with current ff19SB planning records must be re-audited. |

### Reviewer Sign-Off: Force Field And Water Model

Reviewer decision:

- [x] Approve `ff19SB + OPC` with Joung-Cheatham OPC-compatible ions as the
      future Wave 1 default.
- [ ] Approve `ff19SB + TIP3P` as a documented deviation with rationale below.
- [ ] Approve another documented policy with rationale below.
- [ ] Reject all options pending additional MD setup review.

Required reviewer fields:

- Reviewer name: not specified in prompt; recorded by role.
- Reviewer role: human launch reviewer.
- Decision date: 2026-06-12.
- Selected force-field/water/ion policy: AMBER ff19SB + OPC + Joung-Cheatham
  OPC-compatible ions.
- Rationale for selected policy: approved scientific default from
  `reports/phase5/force_field_water_policy_decision_20260611.md`.
- Engine/environment constraints, if any: none recorded in this approval.
- Required follow-up artifacts: updated manifest templates, readiness report,
  provenance records, and preflight checks.
- Limitations to carry into any future manifest: policy selection is not launch
  authorization; no setup or MD may run until a separate future launch record
  exists.
- Signature: approved by human launch reviewer instruction in Codex session.

## Combined Reviewer Closure Checklist

Before either open blocker can be treated as resolved, the reviewer must confirm:

- [x] The ZQZ decision above is completed, dated, and signed.
- [x] The force-field/water-model decision above is completed, dated, and signed.
- [x] Any required re-parameterization, sensitivity analysis, or setup-manifest
      updates are listed as follow-up artifacts.
- [x] The official package still remains on hold unless and until a separate
      future launch authorization is created.
- [x] No MD setup, minimization, equilibration, production, trajectory analysis,
      interpretation, or claims are authorized by this decision package.

## Final Reviewer Attestation

I have reviewed the evidence packet and selected scientific policies for the
two open Phase 5 Wave 1 decision blockers. I understand that this decision
package closes or redirects scientific policy questions only. It does not
authorize MD and does not supersede `do_not_run_md: true`.

- Reviewer name: not specified in prompt; recorded by role.
- Reviewer role: human launch reviewer.
- Date: 2026-06-12.
- ZQZ decision selected: deprotonated ZQZ, net charge `-1`; generate replacement
  audited package; mark neutral `-nc 0` package superseded for production use.
- Force-field/water decision selected: AMBER ff19SB + OPC + Joung-Cheatham
  OPC-compatible ions.
- Follow-up artifacts required before any future launch authorization:
  replacement audited ligand package, supersession marker, updated manifests,
  updated readiness report, updated provenance records, and updated fail-closed
  checks.
- Signature: approved by human launch reviewer instruction in Codex session.

## Evidence Status

Evidence status: verified for local report paths, package status, ZQZ
connectivity facts, and fail-closed launch state; inferred for ZQZ bound-state
pKa because no ZQZ-specific titration evidence exists in this repository;
planning-only for future engine/runtime consequences because no prepared-system
benchmark exists.

Confidence: high for the need to close both decisions before launch can be
considered; high for the ZQZ free-carboxyl structural classification; medium
for the practical ff/water-model recommendation because final feasibility
depends on the future execution environment and benchmark.

No MD was run. No launch authorization was created.
