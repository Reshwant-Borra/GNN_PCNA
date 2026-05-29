---
type: analysis
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [risks, phase2]
aliases: [Risk Register]
confidence: high
evidence_status: verified
---

# Risk Register

## Active risks

| Risk | Why it matters | Control |
|---|---|---|
| Dataset leakage | Invalid metrics | `04`, `05`, `29`, split audit |
| Proxy labels | Wrong scientific target | `06`, label freeze, claim limits |
| V1 artifact reuse | Stale/noncanonical implementation | [[V1 Failure Lessons]] |
| Weak provenance | Unclaimable artifacts | `15`, manifests, hashes |
| MD overinterpretation | Unsupported validation claims | `13`, `33`, claim audit |
| Baseline weakness | Unsupported model value | `10`, `28` |
| Biological implausibility | Metric-only science | `11`, `12`, `25` |
| AI hallucinated science | Unsupported claims | `16`, `34`, wiki source rules |

## Provenance

- Source paths: `docs/scientific_governance/03_FAILURE_MODE_CATALOG.md`, `19_STOP_CONDITIONS.md`
- Confidence level: high
- Date last updated: 2026-05-27
