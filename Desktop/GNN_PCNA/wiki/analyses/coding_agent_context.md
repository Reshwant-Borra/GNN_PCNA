---
type: analysis
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [codex, startup, phase2, governance]
aliases: [Coding Agent Context]
confidence: high
evidence_status: verified
---

# Coding Agent Context

## 1. Project goal

Build a fresh governed Phase 2 GNN-PCNA workflow for residue-level PCNA candidate cryptic/allosteric/pocket-like region prediction and auditing.

## 2. What Phase 2 means

Phase 2 means governance-first rebuild, not V1 continuation. Data, labels, splits, graphs, baselines, MD, and claims must pass documented gates.

## 3. What V1 mistakes must not repeat

Leakage, stale artifacts, overclaims, weak provenance, hallucinated assumptions, weak biological realism, MD overinterpretation, and coding agents inventing science.

## 4. What files define scientific law

`docs/scientific_governance/` defines binding rules. Start with `00_README.md`, `16_CODING_AGENT_RULES.md`, and `37_PHASE2_IMPLEMENTATION_PLAN.md`.

## 5. How to use the wiki

Read `wiki/index.md`, then relevant entity/concept/analysis pages. Use the wiki as a memory map, not final evidence.

## 6. How to use crawls/

Use `crawls/` as raw evidence and source leads. Follow [[Crawl Map]] to targeted paths. Do not treat crawl summaries as verified truth.

## 7. How to use V1

Historical reference only. Audit any V1 component before reuse. Do not copy V1 artifacts into Phase 2.

## 8. What cannot be invented

Biology, labels, split rules, graph science, model methodology, MD interpretation, claim language, or missing assumptions.

## 9. What must exist before training

Dataset registry, lifecycle registry, split audit, label freeze, graph audit, provenance manifests, red-team audit, null-baseline plan, human gates, and readiness gate.

## 10. What must exist before claims

Evaluation, baselines, biological realism audit, PCNA-specific audit, interpretability audit, uncertainty register, provenance, claim audit, and human review.

## 11. What must exist before MD interpretation

Pre-MD reality check, pre-registered question, setup provenance, comparison policy, and allowed positive/negative claim language.

## 12. Allowed claim language

Use cautious computational structural biology language: "candidate region", "hypothesis-generating", "consistent with", "requires follow-up", "exploratory".

## 13. Forbidden claim language

Do not say validated target, therapeutic target, clinically actionable, confirmed mechanism, drug discovery success, treatment relevance, or MD validated binding.

## 14. Required gates

Follow `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, and `19_STOP_CONDITIONS.md`.

## 15. What to do when uncertain

Stop if uncertainty is scientific. Record the gap in [[Open Questions]] and, when relevant, update the governance-linked context.

## 16. How to update wiki memory

Follow [[Wiki Update Rules]]. Log decisions in [[Log]] and update relevant entity/concept pages with source path, confidence, date, and evidence status.

## 17. Current Phase 2 foundation status

Data-foundation scaffolding exists under `reports/phase2/`, `data/registries/`, `data/splits/`, `data/labels/`, and `docs/scientific_governance/DATASET_REGISTRY.md`.

Use `python scripts/phase2_foundation_check.py` to verify scaffold completeness. Current readiness is dataset planning only; training remains blocked.

## 18. Dataset investigation status

Dataset Investigation + Freeze phase has started, but no dataset is frozen. Local `data/` contains templates and registries only; no canonical CryptoBench, BioLiP/BioLiP2, scPDB, PDBbind, ASD, or PocketMiner-related structure/label files are adopted. CryptoBench is the leading primary benchmark candidate, but local file inventory, hashes, license resolution, schema audit, PCNA/homolog contamination checks, split audit, and human dataset/split/label review are still required.

## Provenance

- Source paths: `AGENTS.md`, `docs/scientific_governance/00_README.md`, `16_CODING_AGENT_RULES.md`, `37_PHASE2_IMPLEMENTATION_PLAN.md`, `reports/phase2/readiness_gate.md`, `reports/phase2/dataset_investigation_report.md`, `reports/phase2/proposed_split_strategy.md`, `reports/phase2/proposed_label_strategy.md`
- Confidence level: high
- Date last updated: 2026-05-27
