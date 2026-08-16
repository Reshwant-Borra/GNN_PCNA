# Unexpected Results Policy

## Purpose

Unexpected results are not failure. They are information. Do not force the project to tell the original story if the evidence says otherwise.

## Core Rule

The SARC proposal asks whether GNN prediction plus MD can identify and test candidate PCNA hidden sites. It does not require that the first hypothesis be confirmed. Negative, mixed, or surprising outcomes must be preserved and interpreted honestly.

## Hard Rules

- Unexpected results must be logged.
- The original hypothesis and post-result interpretation must be separated.
- Negative evidence cannot be discarded because it weakens the story.

## Result Handling

| Unexpected result | What it means | What it does NOT mean | Allowed interpretation | Forbidden interpretation | Next scientific step |
|---|---|---|---|---|---|
| MD does not show pocket opening | Under tested conditions, opening was not observed. | MD failed or site is impossible forever. | Evidence against accessible opening on that timescale/setup. | Hide trajectory or claim opening anyway. | Check setup, consider replicates/enhanced sampling, downgrade claim. |
| Predicted site is inaccessible | Static site lacks physical access. | Model useless globally. | Prediction fails realism audit or needs cryptic-opening evidence. | Call it druggable anyway. | Reclassify or test dynamics cautiously. |
| Model performs worse than baseline | Baseline is stronger on this task/split. | Project failed. | GNN design is not yet superior; baseline may be preferred. | Cherry-pick metrics. | Analyze errors, revise model or claims. |
| AOH1996 positive control fails | Model does not recover known PCNA control under declared gate. | No PCNA science can be done. | Current model/checkpoint not trusted for PCNA claims. | Lower threshold after seeing result. | Debug labels, mapping, split status, model. |
| Metrics vary wildly by seed | Training/evaluation unstable. | Best seed is valid headline. | Evidence is uncertain. | Report only best seed. | Increase seeds, simplify model, report instability. |
| PCNA prediction overlaps known interface | Model finds known PCNA biology. | Result is invalid. | Known-interface recovery or non-novel candidate. | Claim novel pocket. | Map overlap and decide whether to study known interface. |
| Dataset becomes too small after leakage controls | Valid data are limited. | Leakage should be tolerated. | Claims must be narrower and CIs wider. | Reintroduce leaked data. | Seek more data or frame exploratory. |
| Baseline beats GNN | Existing method is stronger. | Need to hide baseline. | GNN is not superior under tested conditions. | Claim superiority elsewhere. | Study why; maybe use baseline for PCNA ranking. |
| Biological realism audit flags prediction | Prediction conflicts with biology. | Metrics are meaningless for all tasks. | This candidate should not support claims. | Push to MD to rescue story. | Reject, reclassify, or seek stronger evidence. |

## Required Checks

- Pre-result expectation recorded.
- Observed result recorded.
- Allowed and forbidden interpretations selected.
- Next scientific step chosen.

## Examples Of Failure

- Baseline beats the GNN and the baseline table is removed.
- AOH1996 positive control fails and the threshold is changed afterward.
- MD does not show opening and the trajectory is labeled useless without analysis.

## Prevention

Pre-register criteria and use this table before rewriting conclusions.

## Forbidden Actions

- Treating unexpected evidence as a nuisance.
- Rewriting hypotheses after seeing results without recording it.
- Tuning on test or MD outcomes to recover the desired story.
- Calling negative MD "failed simulation" by default.

## Compliance Artifact

`reports/phase2/unexpected_results_log.md`.

## If This Policy Is Violated

Freeze the report or result, add a contradiction audit, and rewrite conclusions to match evidence.
