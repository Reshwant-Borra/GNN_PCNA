---
type: index
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [wiki, index, phase2, codex-memory]
aliases: [GNN-PCNA Phase 2 Knowledge Base]
confidence: high
evidence_status: verified
---

# GNN-PCNA Phase 2 Knowledge Base

This is the main navigation dashboard for Codex. Use it to avoid random repo scanning and to find the right governance rules, source paths, entities, concepts, risks, and implementation context.

## 1. Start Here

Use this section at the start of every task.

- [AGENTS.md](../AGENTS.md) - Codex operating instructions and required startup routine.
- [[Coding Agent Context]] - compact memory page Codex should read often.
- [[Governance Summary]] - map of binding scientific law.
- [[Phase2 Build Map]] - governed build order and stop points.

Most important: `AGENTS.md` and [[Coding Agent Context]].

**Fast orientation (recommended):** Read `.memory/PROJECT_STATE.md` (current state
snapshot, ~470 tokens) and `.memory/INDEX.md` (task-type routing table, ~410 tokens)
before scanning the full wiki. This saves ~1,400 tokens of orientation cost and tells
you exactly which files to load for your specific task type.

## 2. Binding Governance

Governance docs are project law. Wiki pages summarize and route; governance files decide.

- [docs/scientific_governance/](../docs/scientific_governance/) - binding scientific constraints, gates, and verification rules.
- [00_README.md](../docs/scientific_governance/00_README.md) - governance entrypoint.
- [16_CODING_AGENT_RULES.md](../docs/scientific_governance/16_CODING_AGENT_RULES.md) - rules for Codex and other coding agents.
- [37_PHASE2_IMPLEMENTATION_PLAN.md](../docs/scientific_governance/37_PHASE2_IMPLEMENTATION_PLAN.md) - governed Phase 2 build order.

Use this section before any task touching dataset, labels, splits, graph construction, model logic, evaluation, MD, PCNA interpretation, or claims.

## 3. Source and Evidence Navigation

Use this section when a task needs source context or provenance.

- [[Source Map]] - source authority, promotion rules, and registry template.
- [[Crawl Map]] - topic-to-crawl navigation without bulk ingesting crawl text.
- [[Source Trust Levels]] - how to classify and use evidence.
- [crawls/](../crawls/) - raw evidence and prior context corpus. Treat as leads until verified.

Most important: [[Source Trust Levels]] before using any source.

## 4. Core Project Context

Use this section to understand the Phase 2 rebuild and known traps.

- [[Overview]] - top-level project memory.
- [[Phase2 Build Map]] - implementation sequence.
- [[V1 Failure Lessons]] - old implementation lessons and non-reuse rules.
- [[Risk Register]] - active project risks.

Most important: [[V1 Failure Lessons]] before touching old artifacts.

## 5. Entities

Use entity pages when a task mentions a protein, ligand, structure, dataset, tool, or database.

- [[PCNA]]
- [[AOH1996]]
- [[ATX-101]]
- [[PocketMiner]]
- [[CryptoBench]]
- [[fpocket]]
- [[P2Rank]]
- [[BioLiP]]
- [[scPDB]]
- [[PDBbind]]
- [[ASD]]
- [[8GLA]]
- [[1W60]]
- [[UniProt P12004]]

Entity pages tell Codex what the entity is, why it matters, what not to overclaim, and where to inspect raw sources.

## 6. Concepts

Use concept pages when a task touches scientific method, labels, leakage, metrics, graph construction, or claims.

- [[Cryptic Pockets]]
- [[Allosteric Sites]]
- [[Protein Graph Construction]]
- [[Residue Level Prediction]]
- [[Sequence Split Leakage]]
- [[Apo Holo Leakage]]
- [[Homolog Leakage]]
- [[Proxy Ligand Labels]]
- [[Biological Realism]]
- [[MD Validation Limits]]
- [[Top K Recovery]]
- [[AUPRC vs AUROC]]
- [[Bootstrap Confidence Intervals]]
- [[Provenance Tracking]]
- [[Scientific Claim Control]]
- [[Dataset Registry]]
- [[Split Protocol]]
- [[Label Definition]]
- [[Graph Node Label Alignment]]
- [[Baseline Comparison]]
- [[Unexpected Results Policy]]

Most important: leakage, label, provenance, and claim-control pages before implementation.

## 7. Implementation Guidance

Use this section to decide what can be built and what must wait.

- [[Coding Agent Context]]
- [[Dataset Strategy]]
- [[Evaluation Strategy]]
- [[Baseline Strategy]]
- [[MD Validation Strategy]]
- [[Wiki Update Rules]]

Most important: [[Coding Agent Context]] before coding and [[Wiki Update Rules]] after durable discoveries.

## 8. Risks and Open Questions

Use this section when context is missing or a task exposes uncertainty.

- [[Risk Register]]
- [[Open Questions]]

If a missing assumption affects science, record it before coding.

## 9. Decision Log

- [[Log]]

Append durable project decisions, source-use decisions, wiki maintenance, and implementation-relevant context updates.
