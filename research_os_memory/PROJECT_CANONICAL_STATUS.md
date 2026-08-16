# Project Canonical Status

Last updated: 2026-08-15T16:58:48Z
Updated by: codex.strong_robustness_audit
Status: current

## Project goal

GNN-PCNA + molecular-dynamics validation: identify candidate pocket-associated
residues on PCNA, assess them with computational baselines and MD, and produce a
manuscript whose claims are proportional to the evidence.

## Current research question

Can a leakage-clean GNN identify candidate AOH1996-associated pocket residues
on PCNA that hold up under structural realism and MD analysis?

## Current hypothesis

There exists a pocket-associated residue region near known AOH1996 contacts
that a GNN can flag with above-baseline performance under leakage-clean splits.

## Current status summary

Repository consolidation is complete enough for the pre-MD gate: root `src/`, `scripts/`, `tests/`, `docs/research_base/`, and `md_validation_4070/` are canonical. The nested `Desktop/GNN_PCNA/` tree is archived as historical provenance.

The final extraction policy was selected on non-PCNA structures only and frozen at `artifacts/pre_md_independent_extraction_20260815/frozen_extraction_method.json`.

The frozen policy was applied once to 1W60 seed outputs 42/43/44. PRE-MD STABILITY is `PASS` under the original exploratory gate; this permits a governed Gate-6 handoff request only.

A later POST-PASS STRONGER INTERNAL ROBUSTNESS REQUIREMENT asks for mean literal pairwise Jaccard >=0.75 and minimum pairwise >=0.65 before production-MD release readiness. The current 1W60 result remains mean 0.6792 with minimum pairwise 0.6316, so the stronger internal target is not achieved. The strong-robustness audit found a shared physical pocket core with nontrivial boundary/fringe extension disagreement, found no materially better independent extraction policy, and did not run a second 1W60 evaluation.

## Current blockers

- Strong internal robustness target is not achieved.
- Human Gate-6 approval is not recorded and must not be fabricated.
- Production MD has not started and must not start until a legitimate human Gate-6 decision explicitly accepts the remaining robustness risk.
- Runtime ML/MD dependencies are not active in this shell.

## Next steps

1. Strengthen the independent non-PCNA validation benchmark or explicitly decide whether exploratory-risk MD is acceptable.
2. Do not tune extraction on 1W60 and do not retrain unless future independent evidence demonstrates model instability.
3. If a legitimate human Gate-6 approval is later recorded, run MD preparation, preparation validation, and smoke tests before any production MD.
