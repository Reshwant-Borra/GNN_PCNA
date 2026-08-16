# Validation Status

Last updated: 2026-08-15T16:58:48Z
Updated by: codex.strong_robustness_audit
Status: current

## Validation question

Do candidate pocket-associated residues predicted by the GNN show:
(a) structural proximity to known AOH1996 contacts,
(b) physical plausibility (accessibility, clustering),
(c) MD support for flexibility / pocket opening under tested conditions?

## Structural/pre-MD evidence

`artifacts/pre_md_independent_extraction_20260815/final_1w60_three_seed_stability_report.json` reports PRE-MD STABILITY `PASS` under the frozen independent extraction policy. Literal mean pairwise Jaccard is 0.6792 and the three-seed consensus contains 16 residues.

`artifacts/strong_robustness_20260815/strong_robustness_summary.json` reports that a later post-pass stronger internal robustness target was not achieved. The stricter target asks for mean literal pairwise Jaccard >=0.75 and minimum pairwise >=0.65 before production-MD release readiness. No materially better independent extraction policy was found, no second 1W60 evaluation was run, and no production MD was launched.

## MD evidence

No production MD was launched in this task. MD evidence remains `inconclusive`.

## Metrics used

Pending Metrics Agent verification.

## Evidence classification

Original pre-MD extraction/stability gate: `supports_claim` for the narrow claim that the frozen workflow yields a seed-stable 1W60 candidate region under the original exploratory gate.

Post-pass stronger internal robustness target: `inconclusive` / not achieved for production-MD release readiness.

Binding/druggability/in-vivo pocket claims: `does_not_address_claim`.

MD opening claims: `inconclusive`.

## Contradictions

(none recorded yet)

## Safe interpretation

The GNN highlights a candidate region. MD has not been shown to validate cryptic
pocket opening under the tested conditions.

## Disallowed interpretation

- "MD validated the cryptic pocket"
- "MD proves opening"

## Required follow-up

- Strengthen the independent non-PCNA validation benchmark or explicitly accept exploratory-risk MD in a legitimate human Gate-6 decision.
- Obtain legitimate human Gate-6 approval before any MD.
- After future approved MD, classify evidence explicitly as supportive / partially supportive / inconclusive / weakening / contradictory.

## Final Pre-MD Benchmark Expansion - 2026-08-15

Supported:
- Three frozen seeds rank the same PCNA neighborhood reasonably consistently.
- Current physical pocket localization is substantially more stable than literal boundary membership.
- Current result has an 11-residue 3/3 core and 16-residue >=2/3 consensus.
- Current extraction policy was independently selected and remains the best-supported policy after final expansion audit.

Uncertainty:
- Exact pocket boundary is not fully stable.
- Literal Jaccard is moderate rather than excellent.
- Independent extraction benchmark remains limited to five eligible non-PCNA validation proteins.
- Computational prediction does not establish druggability or binding.

Not established:
- Actual ligand binding.
- Druggability.
- Biological efficacy.
- Experimentally confirmed pocket opening.
- Therapeutic relevance.

MD readiness: PROCEED TO CONTROL-FIRST MD only after human Gate-6 approval; production MD has not started.

