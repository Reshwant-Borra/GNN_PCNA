# Negative Result Success Criteria

## Purpose

Define what counts as a successful Phase 2 project even if the expected positive story does not happen.

## Hard Rules

- Negative, mixed, and inconclusive results can be successful if they are reproducible, well-governed, and honestly interpreted.
- No one may force positive interpretation to satisfy the original story.
- Success criteria must be defined before final evaluation and MD interpretation.

## Successful Negative Outcomes

The project can be successful if:

- The GNN does not beat baselines, but the comparison is fair and reproducible.
- MD does not show pocket opening, but the hypothesis was tested cleanly.
- No novel PCNA pocket emerges, but known-interface recovery and limitations are clear.
- A benchmark is found too noisy or biased for strong claims.
- Dataset leakage controls reduce data size and force narrower claims.
- Biological realism audit rejects a top prediction.
- AOH1996 positive control fails and prevents unsafe PCNA claims.

## Forbidden Actions

- Retuning until a desired positive result appears.
- Hiding mediocre metrics, failed baselines, or negative MD.
- Calling negative MD a failed simulation without evidence.
- Rewriting the hypothesis after results without logging it.

## Required Checks

- Predefine what negative outcomes mean.
- Log negative outcomes in [22_UNEXPECTED_RESULTS_POLICY.md](22_UNEXPECTED_RESULTS_POLICY.md).
- Update allowed claims based on evidence.
- Include limitations and uncertainty.

## Examples Of Failure

- Baseline beats GNN and the report still claims AI discovery.
- No pocket opening is observed and the trajectory is omitted.
- PCNA prediction overlaps known interface but is framed as novel.

## Prevention

Make negative-result success part of readiness and publication review.

## Compliance Artifact

`reports/phase2/negative_result_success_review.md`.

## If The Rule Fails

Freeze claims and rewrite conclusions around the actual evidence.
