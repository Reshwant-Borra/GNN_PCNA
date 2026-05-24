# CURRENT_CLAIMS.md

Last updated: 2026-05-24T00:00:00Z
Updated by: human (initial bootstrap)
Status: current

Every claim maps to `../research_os_registries/claim_registry.json`.

---

## Accepted Claims

| ID | Claim | Strength | Evidence |
|---|---|---|---|
| CLAIM-0001 | PocketGNNXL V3 achieves AUROC 0.8081 on 13 held-out CryptoSite proteins | strongly_supported_computationally | `data/results/test_split_eval_best.json`, checkpoint `pcna_reproduced/best.ckpt` |
| CLAIM-0002 | PocketGNNXL V3 recovers the AOH1996 binding site on 8GLA (mean score 0.8676, threshold 0.700) | strongly_supported_computationally | `data/results/aoh_gate_check.json` |
| CLAIM-0003 | Holo PCNA (8GLA) pocket shows elevated ANM flexibility vs global (fold-change 1.157; delta +0.300 vs apo 0.857) | moderately_supported | `data/results/nma_apo_holo_comparison.json` |
| CLAIM-0004 | PocketGNNXL V3 (+ESM2) outperforms PocketGNN V1 by +0.228 AUROC on internal fine-tuning structures | strongly_supported_computationally | Internal eval; labeled as non-generalizing |

---

## Partially Supported Claims

| ID | Claim | What's missing | Notes |
|---|---|---|---|
| CLAIM-0005 | The AOH1996 pocket is a cryptic site (not visible in apo but opens dynamically) | MD trajectory evidence of transient opening | ANM shows holo flexibility; MD pending |

---

## Hypothesis-Generating Claims

| ID | Claim | Status |
|---|---|---|
| CLAIM-0006 | Novel cryptic sites beyond AOH1996 exist on PCNA | No MD validation yet; requires E003 results |

---

## Unsupported Claims

_None currently asserted._

---

## Contradicted Claims

_None._

---

## Allowed Wording

- "candidate cryptic site" (not "validated cryptic site" without MD evidence)
- "suggestive of dynamic flexibility" (not "confirmed pocket opening" without MD volume evidence)
- "held-out AUROC 0.8081 on 13 CryptoSite proteins" (always specify N=13)
- "internal fine-tuning evaluation, not generalization" for Table 1 data

## Disallowed Wording

- "validated cryptic pocket" for any site without both RMSF + volume MD evidence
- "proven" for any computational result
- "8GLA AOH1996 site is a novel finding" — it is the GROUND TRUTH, not a novel prediction
- Any 9B8T-specific claim until regenerated with correct chains

## Claims Requiring Human Approval Before Paper Inclusion

- CLAIM-0005 upgrade to "strongly_supported" (requires MD RMSF + volume evidence)
- CLAIM-0006 promotion to any supported tier (requires MD results)
