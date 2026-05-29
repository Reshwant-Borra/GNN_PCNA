# Obsidian Memory System Report

Date: 2026-05-27

## Files Created Or Updated

- `AGENTS.md`
- `wiki/index.md`
- `wiki/overview.md`
- `wiki/log.md`
- `wiki/sources/source-map.md`
- `wiki/sources/crawl-map.md`
- `wiki/sources/source-trust-levels.md`
- `wiki/entities/*.md`
- `wiki/concepts/*.md`
- `wiki/analyses/*.md`
- `wiki/open_questions/open-questions.md`

## How AGENTS.md Now Instructs Codex

`AGENTS.md` now tells Codex to use the wiki as persistent project memory and to follow `docs/scientific_governance/` as binding scientific law. It defines the startup routine, authority order, allowed work, forbidden work, memory-update rules, and the clarification that this project is not using a fake autonomous ResearchOS operating system as the main workflow.

## How The Wiki Acts As Memory

The wiki now acts as:

- table of contents
- source navigation layer
- entity graph
- concept graph
- implementation context
- open question tracker
- risk register
- decision log

Codex should begin at `wiki/index.md`, read `wiki/analyses/coding_agent_context.md`, then navigate to relevant governance, source, entity, and concept pages.

## How The Wiki Maps To Crawls

`wiki/sources/crawl-map.md` maps project topics to crawl directories and source indexes without ingesting all crawl text. The crawl map points Codex to relevant paths such as:

- `crawls/pcna-cryptic-pocket-gat-md-kb-final/`
- `crawls/pcna-dataset-repositories-pass9/`
- `crawls/pcna-curated-official-tools-data-structures-pass8/`
- `crawls/pcna-gap-closure-datasets-tools-structures-pass6/`
- `crawls/pcna-biogrid-full-pass5/`
- `crawls/pcna-biogrid-interactions-pass4/`
- `crawls/gnn-compbio-autonomous-kb-final/`

Crawl summaries remain leads, not verified truth.

## Governance Versus Wiki

`docs/scientific_governance/` is binding authority. The wiki is a memory and navigation layer. If a wiki page conflicts with governance, governance wins. If a crawl summary conflicts with governance, governance wins. If V1 conflicts with Phase 2 governance, Phase 2 governance wins.

## How Codex Should Update Memory

Codex should update the wiki when durable project knowledge is learned, a source is used, a decision is made, a V1 failure is found, a governance implication becomes clear, or an unresolved question is discovered.

Every wiki update should include:

- date
- source path
- confidence level
- evidence status
- related governance doc
- related crawl path if applicable

## Remaining Gaps

- Local V1 / `project-version-1` path or branch is not confirmed in the root checkout.
- Fresh Phase 2 implementation path or branch is not confirmed in the wiki.
- CryptoBench file inventory, license, and label schema are unresolved.
- Sequence clustering tool and threshold are unresolved.
- PCNA final holdout and positive-control structure list is unresolved.
- MVP baseline set is unresolved.
- MD scope and any pre-registered MD question are unresolved.

## Next Recommended Ingestion Targets

1. `docs/scientific_governance/00_README.md`
2. `docs/scientific_governance/01_SOURCE_OF_TRUTH.md`
3. `docs/scientific_governance/16_CODING_AGENT_RULES.md`
4. `docs/scientific_governance/37_PHASE2_IMPLEMENTATION_PLAN.md`
5. `crawls/pcna-dataset-repositories-pass9/SOURCE_INDEX.md`
6. `crawls/pcna-curated-official-tools-data-structures-pass8/SOURCE_INDEX.md`
7. `crawls/pcna-cryptic-pocket-gat-md-kb-final/SOURCE_INDEX.md`

## Provenance

- Source paths: user task, `AGENTS.md`, `wiki/index.md`, `docs/scientific_governance/`, `crawls/*/SOURCE_INDEX.md`
- Confidence level: high for memory-system structure; low for unresolved source content
- Evidence status: verified for files created; uncertain for unreviewed crawl claims
