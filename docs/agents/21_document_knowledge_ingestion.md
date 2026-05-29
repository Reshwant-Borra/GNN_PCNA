# Agent 21: Document and Knowledge Ingestion

## Purpose

Ingests external documents — papers, PDFs, Markdown notes, experiment reports, Claude/chat transcripts, crawler output, and web research — into the ResearchOS memory system, Source Registry, and Obsidian vault. Creates structured links between ingested sources and existing claims, experiments, artifacts, and issues.

Obsidian integration is central: every ingested source produces a wikilinked Obsidian note in `Obsidian/GNN_PNCA/docs/sources/`.

## Responsibilities

- Accept one or more file paths, directories, or transcript paths as input.
- Detect source type: PDF, Markdown, TXT, JSON (arxiv/crawler metadata), HTML, or Claude/chat transcript.
- Extract text and metadata (title, authors, date, DOI/URL if available).
- Chunk content by section (heading-based for structured docs, paragraph for unstructured).
- Generate per-source summaries: short (1 sentence), abstract-length, and a structured claims list.
- Auto-tag each source: `topic[]`, `relevance_score (0–1)`, `domains[]`, `source_type`.
- Extract structured claims from each source: `{claim_text, evidence_type, metrics[], limitations[]}`.
- Assign a stable SRC-XXXX ID (auto-increment from `research_os_registries/source_registry.json`).
- Write a SRC entry to `research_os_registries/source_registry.json`.
- Write one Obsidian note per source to `Obsidian/GNN_PNCA/docs/sources/SRC-{XXXX}_{slug}.md`.
- Update `Obsidian/GNN_PNCA/docs/sources/_SOURCE_INDEX.md` with a new row.
- Propose links: for each ingested source, suggest which claim_ids, experiment_ids, and artifact_ids it supports.
- Emit an ingest report to `data/artifacts/<task_id>/ingest_report.json`.

## Inputs

- `paths`: list of file paths to ingest (PDF, .md, .txt, .json, .html)
- `dir`: directory to batch-ingest (all recognized file types)
- `transcript`: path to a Claude/chat transcript file
- `source_type_override`: optional; force a specific parser
- `tag_claims`: if true, attempt claim extraction from each source
- `merge_knowledge`: if true, propose additions to `docs/knowledge/` files (user-confirmed step)

Accepted source types:
- PDFs (papers, reports): `pdfplumber` text extraction
- Markdown (experiment logs, meeting notes, NotebookLM distilled notes): frontmatter + section parse
- TXT (abstracts, notes): paragraph chunking
- JSON (arxiv/PMC crawler metadata from `research/rmsf_md_research/data/`): field extraction
- HTML (crawled tutorials/docs from `research/rmsf_md_research/data/docs/`): BeautifulSoup
- Claude/chat transcripts from `Obsidian/Claude/Chat History/`: role-tagged message extraction

## Outputs

1. `research_os_registries/source_registry.json` — updated with new SRC entries
2. `Obsidian/GNN_PNCA/docs/sources/SRC-{XXXX}_{slug}.md` — one Obsidian note per source
3. `Obsidian/GNN_PNCA/docs/sources/_SOURCE_INDEX.md` — updated index row
4. `data/artifacts/<task_id>/ingest_report.json` — full ingest report (IDs, summaries, link proposals)
5. stdout: per-source summary with SRC-ID, slug, topics, and proposed links

## Obsidian Note Format

Each source note follows this template:

```markdown
---
src_id: SRC-{XXXX}
title: "{title}"
source_type: pdf | markdown | json | html | transcript
topics: [topic1, topic2]
relevance: 0.0–1.0
date_ingested: YYYY-MM-DD
original_path: "..."
---

# {title}

**SRC-ID:** SRC-{XXXX}
**Type:** {source_type}
**Topics:** {topics}
**Relevance:** {relevance}

→ Links: [[_SOURCE_INDEX]] | [[relevant knowledge file]]

---

## Summary

{abstract-length summary}

---

## Key Claims

| Claim | Evidence type | Notes |
|---|---|---|
| {claim_text} | {evidence_type} | {notes} |

---

## Methods / Metrics

{extracted methods or metrics}

---

## Limitations

{extracted limitations}

---

## Links to Project

| Type | ID | Rationale |
|---|---|---|
| claim | CLAIM-XXXX | {why this source supports the claim} |
| experiment | EXP-XXXX | {why this source informs the experiment} |
```

## Source Registry Entry Format

```json
{
  "id": "SRC-0001",
  "created": "YYYY-MM-DDTHH:MM:SSZ",
  "updated": "YYYY-MM-DDTHH:MM:SSZ",
  "status": "current",
  "created_by": "agent-21",
  "title": "...",
  "source_type": "pdf",
  "original_path": "...",
  "doi": null,
  "url": null,
  "authors": [],
  "date_published": null,
  "topics": [],
  "relevance_score": 0.0,
  "short_summary": "...",
  "abstract_summary": "...",
  "extracted_claims": [],
  "linked_claims": [],
  "linked_experiments": [],
  "linked_artifacts": [],
  "obsidian_note": "Obsidian/GNN_PNCA/docs/sources/SRC-0001_{slug}.md",
  "notes": ""
}
```

## Triggers

- User runs `python agents/ingest.py --path <file>` or orchestrator `ingest` intent.
- After downloading a batch of arXiv/PMC papers via `research/rmsf_md_research/crawl_rmsf.py`.
- After completing a NotebookLM extraction (distilled note → ingest as MD source).
- After completing a significant Claude/chat session (transcript → ingest to capture decisions).
- When a new paper or protocol is referenced in a claim, experiment, or paper section.

## Link Proposal Rules

- If a source contains a benchmark metric matching a claim metric: propose link to that CLAIM-ID.
- If a source describes a method used in an experiment: propose link to that EXP-ID.
- If a source validates or contradicts a checkpoint result: propose link to that ART-ID.
- If a source describes a bug or incorrect assumption: propose a new ISSUE entry.
- All proposals are emitted in the ingest report; none are applied automatically without review.

## Required Checks

- Do not create duplicate SRC entries for the same file (check path hash).
- Do not claim a source "proves" anything — always emit claims as `suggestive` or lower unless the source is primary experimental data with methodology.
- Do not apply link proposals or merge into `docs/knowledge/` without human confirmation.

## Pass/Fail

Passes if:
- Every ingested source has a SRC-ID in `source_registry.json`.
- Every SRC-ID has a corresponding Obsidian note.
- `_SOURCE_INDEX.md` is updated.
- Ingest report is written to artifacts.

Fails if:
- Source is parsed but not registered.
- Obsidian note is not written.
- Duplicate SRC created for an already-ingested path.
- Claims are extracted at too-high a strength without evidence.

## Human Escalation

Escalate when:
- A source directly contradicts an accepted claim (propose ISSUE + claim downgrade for human approval).
- A source suggests the held-out split is contaminated (flag immediately).
- A source is a chat transcript that contains a human override decision not yet in `HUMAN_DECISIONS.md`.
