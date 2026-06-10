---
type: human-review-gate-authorization
gate: GATE_7_MD_WAVE_1
decision_id: phase5_gate7_wave1_authorization_20260609
date: 2026-06-09
reviewer: Reshwant-Borra
decision: approved
scope: official Phase 5 MD Wave 1 only
status: AUTHORIZED_WITH_LIMITATIONS
governance:
  - docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md
  - docs/scientific_governance/13_MD_VALIDATION_RULES.md
  - docs/scientific_governance/14_CLAIM_POLICY.md
  - docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md
  - docs/scientific_governance/26_HUMAN_REVIEW_GATES.md
evidence_packet:
  - reports/phase4/gate7_md_decision_draft_20260529.md
  - reports/phase4/phase4_candidate_prioritization_20260529.md
  - reports/phase4/phase4_candidate_report_20260529.md
  - reports/phase4/phase4_pcna_audit_20260529.md
  - reports/phase4/phase4_interface_overlap_20260529.md
  - data/registries/pcna_interface_map.json
  - reports/phase4/gate6_authorization_20260529.md
---

# GATE 7 Authorization - Official Phase 5 MD Wave 1

## Human Decision

On 2026-06-09, Reshwant-Borra approved GATE 7 Wave 1 authorization based on
`reports/phase4/gate7_md_decision_draft_20260529.md` and the binding governance
requirements.

Decision: **APPROVED WITH LIMITATIONS**.

This authorization permits preparation and later execution of the official Phase 5 MD
Wave 1 plan. It does not run MD and does not authorize any claim or interpretation
without the later MD interpretation human-review gate.

## Authorized Scope

Official Phase 5 MD Wave 1 includes:

| Group | Residues | Structure/system | Role |
|---|---:|---|---|
| Positive control | 118-122 | 8GLA holo with ZQZ retained | AOH1996/ZQZ contact persistence and setup sanity check |
| Positive control | 118-122 | 8GLA apo-from-holo with ZQZ removed | AOH1996/IDCL pocket persistence or collapse |
| Tier 1A candidate | 239-243 | 1AXC apo-from-p21 PCNA trimer | Highest no-interface-overlap candidate |
| Tier 1A candidate | 28-32 | 1AXC apo-from-p21 PCNA trimer | Second no-interface-overlap candidate |
| Tier 1A candidate | 206-210 | 1AXC apo-from-p21 PCNA trimer | Third no-interface-overlap candidate |
| Interface-adjacent control | 134-138 | 1AXC apo-from-p21 PCNA trimer | IDCL/PIP-adjacent comparator |

Minimum planned sampling: **at least 3 replicates x 100 ns per required system**.

The same force-field, water/ion, protonation, trimer-assembly, residue-mapping, and
trajectory-analysis policy must be used across comparable systems unless a deviation is
recorded before execution.

## Required Statement

We do not build expecting one MD result and then panic when MD gives unexpected results.
MD can support, weaken, redirect, or falsify the working hypothesis. All outcomes are
evidence. Negative MD results are valid and will be reported honestly. The absence of
pocket opening is not a failed run, and ligand stability in one trajectory is not
binding-site proof.

## Explicit Exclusions

This authorization does not cover:

- the deprecated Phase 5 time-crunch RunPod workflow;
- any `3 x 25 ns` shortcut workflow;
- MD Wave 2 or Tier 1B trimer-interface candidates (`170-174`, `175-179`, `152-156`);
- enhanced sampling, metadynamics, umbrella sampling, or monomer PCNA simulations;
- any claim that a candidate is validated, druggable, therapeutic, clinically relevant,
  or mechanistically confirmed;
- final paper language, figures, or external claims.

Wave 2 requires a separate enhanced-sampling pre-registration and separate human
authorization.

## Execution Hold

The current user instruction says: **DO NOT RUN THE MD VALIDATION YET AT ALL**.

Therefore, this record authorizes the official Gate 7 Wave 1 plan but leaves execution
on hold until a later explicit user instruction authorizes launch. No setup command,
parameterization command, production command, trajectory generation, or analysis command
is run by this artifact.

## Preconditions Before Any Future Launch

- Official Wave 1 execution package prepared and reviewed.
- PCNA chain and biological-assembly mapping verified for 8GLA and 1AXC.
- ZQZ ligand parameterization method chosen, versioned, and recorded before 8GLA holo
  production.
- Input structure hashes recorded.
- Environment, command, seed, and output manifest templates ready.
- Stop conditions defined for unstable equilibration, missing chains, failed ligand
  parameters, or unresolved residue numbering.

## Required Post-MD Gates

Before any MD result can support text in a report or manuscript:

1. trajectory QA and setup provenance audit must be complete;
2. pre-registered metrics must be reported, including negative or inconclusive outcomes;
3. an interpretation table must classify each candidate as supports, partially supports,
   inconclusive, weakens, or contradicts;
4. first MD interpretation must receive human review under
   `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`;
5. claim audit must pass under `docs/scientific_governance/14_CLAIM_POLICY.md`.

## Evidence Status

Evidence status: verified decision record for human authorization; no MD outputs.

Confidence: high for authorization scope and source paths; no claim about simulation
outcomes.

