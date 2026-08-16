---
type: source
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [sources, trust, provenance]
aliases: [Source Trust Levels]
confidence: high
evidence_status: verified
---

# Source Trust Levels

Use these levels before relying on any source.

## 1. Binding Governance

`docs/scientific_governance/`.

Highest authority for project rules, gates, allowed actions, stop conditions, and claim language. Codex must follow these rules even if a crawl summary, V1 artifact, or wiki page suggests otherwise.

## 2. Primary Evidence

Peer-reviewed paper, official dataset, official database, official documentation, official structure entry, or official tool documentation.

Use for scientific or implementation facts after checking relevance, scope, and governance constraints.

## 3. Strong Implementation Reference

Official repo, benchmark implementation, well-documented tool, reproducible example, or maintained package documentation.

Use for implementation patterns, command syntax, schema expectations, and reproducibility details. Do not convert tool behavior into scientific truth without evidence.

## 4. Useful Background

Review, tutorial, explanatory source, noncanonical summary, or method overview.

Use for orientation and vocabulary. Do not use as the only basis for Phase 2 scientific claims.

## 5. Raw Crawl Lead

Extracted source, crawl metadata, or generated crawl knowledge under `crawls/` not yet verified.

Use as a pointer to evidence. Inspect the underlying path, URL, metadata, and governance relevance before using it.

## 6. Historical Reference

V1 notes, old code, old graphs, old checkpoints, old reports, or `project-version-1` material.

Use only for lessons, architecture ideas, and known failure examples. Audit before reuse. Never use as canonical Phase 2 implementation or evidence.

## 7. Excluded/Noisy

Duplicate, low-quality, contradictory, outdated, unsupported, irrelevant, or provenance-poor source.

Do not use for implementation or claims. Preserve the exclusion reason if it affected a decision.

## Provenance

- Source paths: `docs/scientific_governance/`, `crawls/`, V1/old artifacts if present
- Confidence: high
- Date last updated: 2026-05-27
