# Readiness Gate

## Purpose

Score whether Phase 2 is ready for training, evaluation, MD interpretation, or claims.

## Hard Rules

- FAIL blocks downstream work.
- WARNING permits only scoped exploratory or limited claims.
- PASS requires artifacts, not verbal assurance.

## Scoring

Each category is scored:

- PASS: documented, audited, and no blocking issue.
- WARNING: usable only with scoped limitations.
- FAIL: blocks downstream work.

## Categories

| Category | PASS evidence | WARNING | FAIL |
|---|---|---|---|
| Dataset readiness | registry complete, sources hashed | minor unresolved metadata | missing registry or mystery data |
| Scope readiness | project scope audit complete | minor wording caveat | scope drift into therapy/clinical claims |
| Uncertainty readiness | uncertainty register complete | uncertainty scoped but unresolved | high-impact uncertainty missing |
| Benchmark readiness | benchmark limitations documented | benchmark noisy but scoped | benchmark adopted without audit |
| Data lifecycle readiness | accepted/excluded/quarantined statuses tracked | minor metadata gap | removal or reuse without reason |
| Split readiness | leakage audit PASS | small sample caveat | leakage or invalid split |
| Human review readiness | required decisions recorded | approved with limitations | mandatory human gate missing |
| Label readiness | reproducible labels and audit | ambiguous residues masked | label mismatch or undefined labels |
| Biological data sanity readiness | pretraining biology review PASS | warning requiring scoped training | biologically nonsensical labels/structures |
| Graph readiness | graph metadata and hashes complete | nonblocking structure caveat | graph-label mismatch |
| Red-team readiness | high-risk attacks addressed | open medium-risk issue | unresolved high-risk attack |
| Null baseline readiness | trivial baselines run or plan frozen pretraining | strong heuristic noted | null baselines missing for claims |
| Architecture readiness | batch/logit/shortcut audits PASS | ablation pending for nonclaim run | batch leakage or shortcut |
| Training readiness | upstream gates PASS | limited exploratory run | dataset/split/label/graph fail |
| Evaluation readiness | frozen protocol and seeds | small CI caveat | test reused or no CIs |
| Biological realism readiness | plausibility audit PASS | unresolved mechanism | implausible prediction |
| Interpretability readiness | attribution/ablation review complete | unstable but disclosed | black-box PCNA claim |
| MD readiness | pre-registration and setup PASS | exploratory single trajectory | no pre-registration |
| Pre-MD readiness | reality check complete | hypothesis narrow/limited | no falsifiable hypothesis |
| AI hallucination readiness | AI claims sourced or uncertainty-marked | weakly sourced language scoped | unsupported generated science |
| Claim readiness | claim audit PASS | hypothesis-only wording | forbidden wording |
| Reproducibility readiness | manifests complete | minor environment caveat | unreproducible result |
| Publication readiness | final readiness complete | internal draft only | external claims before readiness |

## Hard Gates

- No training if dataset, split, label, or graph readiness fails.
- No training if benchmark, biological data sanity, human review, red-team, uncertainty, or data lifecycle readiness fails.
- No claims if biological, MD, or claim readiness fails.
- No PCNA claims if interpretability, null-baseline, PCNA-specific, uncertainty, or AI hallucination readiness fails.
- No final report if reproducibility fails.
- No external-facing writeup if publication readiness fails.

## Forbidden Actions

- Averaging PASS and FAIL categories into an overall pass.
- Treating WARNING as permission for strong claims.
- Ignoring reproducibility failure because metrics look good.

## Required Checks

- Each category scored with evidence link.
- Each WARNING has limitation language.
- Each FAIL has remediation owner.

## Examples Of Failure

- Evaluation readiness passes while test was used during model selection.
- Claim readiness passes before baseline audit.
- MD readiness passes without pre-registration.
- Training readiness passes without biological data sanity review.
- PCNA claim readiness passes without uncertainty and interpretability audits.

## Prevention

Use the readiness table as a blocking gate in reviews and reports.

## Compliance Artifact

`reports/phase2/readiness_gate.md`.

## If Gate Fails

Stop downstream work and remediate the failed category.
