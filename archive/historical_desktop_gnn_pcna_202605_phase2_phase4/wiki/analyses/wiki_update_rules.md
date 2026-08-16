---
type: analysis
status: active
created: 2026-05-27
updated: 2026-05-27
tags: [wiki, memory, codex]
aliases: [Wiki Update Rules]
confidence: high
evidence_status: verified
---

# Wiki Update Rules

## Codex should update wiki when

- durable project knowledge is learned
- a new source is used
- a new source path becomes important
- a new decision is made
- an assumption is discovered
- an uncertainty is discovered
- a V1 failure mode is found
- a governance implication is identified
- an implementation rule becomes clear

## Codex should NOT update wiki for

- temporary debugging noise
- unverified guesses
- raw dumps
- one-off logs
- hallucinated summaries
- unsupported conclusions

## Every wiki update needs

- date
- source path
- confidence level
- status: verified / inferred / uncertain / speculative
- related governance doc
- related crawl path if applicable

## Where to update

- Decisions: [[Log]]
- Unresolved questions: [[Open Questions]]
- Entity knowledge: `wiki/entities/`
- Concept knowledge: `wiki/concepts/`
- Implementation memory: [[Coding Agent Context]]
- Source navigation: [[Source Map]] and [[Crawl Map]]

## Provenance

- Source paths: `AGENTS.md`, `docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md`, `34_AI_HALLUCINATION_DETECTION.md`
- Confidence level: high
- Date last updated: 2026-05-27
