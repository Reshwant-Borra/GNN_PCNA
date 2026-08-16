# Stop Conditions

## Purpose

Define when Phase 2 must pause.

## Stop Table

| Stop condition | Trigger | Freeze | Reviewer | Remediation allowed | Resume when |
|---|---|---|---|---|---|
| Leakage found | Shared system/homolog/apo-holo across splits | splits, graphs, checkpoints, metrics | split owner and critic | rebuild split and downstream artifacts | split audit PASS |
| Split invalid | Split made after graphs or tuned after metrics | downstream artifacts | evaluation owner | new frozen split | split hash registered |
| Labels uncertain | Label definition ambiguous or unreproducible | labels, graphs, checkpoints | label owner | relabel or mask | label audit PASS |
| Graph-label mismatch | node count or residue mapping mismatch | graphs, checkpoints | preprocessing owner | regenerate graphs | graph audit PASS |
| Provenance broken | missing hashes/commands/seeds | affected artifact | provenance owner | reproduce or quarantine | manifest complete |
| Shortcut features | chain/index/size shortcut detected | model, metrics | model owner | ablate/remove | shortcut audit PASS |
| Metrics unstable | seed variance changes conclusion | claims | evaluation owner | more seeds or downgrade | stability reported |
| Baselines missing | superiority claim without fair baseline | claims | evaluation owner | run baseline or remove claim | baseline audit PASS |
| MD contradicts core hypothesis | pre-registered negative outcome | MD claims | MD owner and biology reviewer | reframe hypothesis | interpretation updated |
| Biological implausibility | inaccessible, unstable, or trimer-conflicting site | prediction, MD plan, claims | biology reviewer | reject or reclassify site | realism audit PASS |
| Claim exceeds evidence | forbidden wording or unsupported inference | report/figure | claim reviewer | rewrite | claim audit PASS |
| Agent invented assumption | undocumented science in code/report | affected work | human/reviewer | document and review | assumption verified |
| Source of truth unclear | conflicting artifact paths or versions | all downstream work | provenance owner | reconcile canonical source | source audit PASS |
| Stale artifact detected | old cache/checkpoint used unregistered | affected run | provenance owner | quarantine and regenerate | artifact registered |
| No way to reproduce result | command/env/hash missing | result and claims | provenance owner | rerun from manifest | reproduction succeeds |
| Scope drift | project drifts into drug discovery, therapeutic, clinical, or treatment claims | claims and external text | scope reviewer | rewrite or remove scope-violating content | scope audit PASS |
| Human gate missing | split/label/training/PCNA/MD/claim gate lacks human decision | downstream artifacts | human reviewer | record review or rerun after review | human review log complete |
| Biological data sanity fails | labels or structures are biologically implausible before training | labels, graphs, training | biology reviewer | fix labels/data or narrow scope | sanity review PASS |
| Red-team blocker | adversarial audit finds unresolved high-risk shortcut or benchmark issue | training or claims | red-team reviewer | run ablations/baselines or downgrade | red-team issue resolved |
| Null baseline wins | trivial heuristic matches or beats GNN under same split | performance claims | evaluation owner | report honestly or revise model | claim downgraded |
| Benchmark quality unresolved | label noise/bias/source uncertainty not documented | dataset/evaluation | benchmark owner | complete benchmark limitations | benchmark audit PASS |
| AI hallucination found | generated scientific text lacks source or uncertainty marker | report/claim/code comment | claim reviewer | replace with sourced/uncertain text | hallucination audit PASS |
| Uncertainty missing | high-impact uncertainty unregistered | claims and reports | uncertainty owner | register and scope uncertainty | uncertainty register updated |
| Interpretability missing | PCNA claim lacks attribution/ablation review | PCNA claims | model reviewer | run interpretability audit | interpretability PASS |
| Pre-MD reality check missing | MD interpreted without falsifiable hypothesis | MD claims | MD reviewer | complete reality check or mark exploratory | MD gate PASS |

## Hard Rules

- Stop means pause scientific use, not delete files.
- Frozen artifacts must be preserved for audit.
- Work can continue only outside the affected dependency chain.

## Forbidden Actions

- Continuing to use a frozen artifact for claims.
- Deleting evidence of a failed run.
- Retuning the same test set after a stop condition.

## Required Checks

- Stop trigger documented.
- Affected artifacts listed.
- Reviewer assigned.
- Remediation and resume criteria recorded.

## Examples Of Failure

- Leakage is found but only the final report language is softened.
- A stale checkpoint is replaced without preserving the original provenance problem.
- MD contradicts the hypothesis and the result is omitted.
- A coding agent writes a confident biological rationale without source or uncertainty marker.
- First training starts without human split/label freeze.

## Prevention

Use the stop table as an operational log and require reviewer sign-off before work resumes.

## Compliance Artifact

`reports/phase2/stop_condition_log.md`.

## If Stop Conditions Are Ignored

The affected result is invalid for Phase 2 and cannot support claims.
