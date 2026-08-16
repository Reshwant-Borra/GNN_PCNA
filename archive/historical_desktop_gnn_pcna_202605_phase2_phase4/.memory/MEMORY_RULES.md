---
status: binding
authority: above wiki, below governance docs
updated: 2026-05-27
---

# Memory Rules — GNN-PCNA Phase 2

These rules govern how Claude Code, Codex, and human reviewers read and write project
memory. They sit above the wiki in authority but below `docs/scientific_governance/`.
Agents must not override these rules.

---

## Authority Order (never violate)

```
docs/scientific_governance/ > primary sources > crawls/ > wiki/ > reports/
```

---

## Write Matrix

| File / Folder | Claude Code | Codex | Human | Mode |
|---|---|---|---|---|
| `CLAUDE.md` | NO | NO | YES | Architecture — human-only |
| `AGENTS.md` | NO | NO | YES | Architecture — human-only |
| `.memory/INDEX.md` | NO | NO | YES | Navigation — human-only |
| `.memory/MEMORY_RULES.md` | NO | NO | YES | Rules — human-only |
| `.memory/PROJECT_STATE.md` | YES | YES | YES | Overwrite targeted sections; always update frontmatter `updated` and `updated_by` |
| `.memory/AGENT_HANDOFF_TEMPLATE.md` | NO (template only) | NO (template only) | YES | Fill in memory; save instances to `reports/phase2/handoff_YYYYMMDD.md` |
| `docs/scientific_governance/` | NO | NO | YES | Scientific law — human-only |
| `wiki/index.md` | NO | NO | YES | Navigation — human-only |
| `wiki/entities/*.md` | YES with provenance | YES with provenance | YES | Append / update |
| `wiki/concepts/*.md` | YES with provenance | YES with provenance | YES | Append / update |
| `wiki/analyses/coding_agent_context.md` | YES — append §25+ only | YES — append §25+ only | YES | Append-only; never delete or rewrite existing sections |
| `wiki/log.md` | YES | YES | YES | **Append-only** — never edit or delete entries |
| `wiki/open_questions/open-questions.md` | YES | YES | YES | Append only; never delete; mark resolved inline |
| `data/registries/` | YES (new files or JSONL append) | YES (new files or JSONL append) | YES | Structured; `download_manifest.jsonl` is append-only via intake scripts |
| `reports/phase2/` | YES (new files only) | YES (new files only) | YES | Never overwrite existing reports — they are permanent audit artifacts |
| `data/raw_intake/` | Via intake scripts only | Via intake scripts only | YES | Hash + manifest step is mandatory; never bypass |

---

## Required Provenance on Every Wiki Write

Every update to `wiki/entities/`, `wiki/concepts/`, or `wiki/analyses/` must include:

- `date:` (YYYY-MM-DD)
- `source:` (file path or governance doc path)
- `confidence:` high / medium / low
- `evidence_status:` verified / inferred / uncertain / speculative

Do not dump raw source text into wiki pages. Summarize and link to source paths.

---

## What Triggers a Write

| Event | Target |
|---|---|
| Durable knowledge learned (entity, concept, relationship) | `wiki/entities/` or `wiki/concepts/` |
| Project decision made (dataset, split, label, policy) | Append to `wiki/log.md` |
| New open question or uncertainty found | Append to `wiki/open_questions/open-questions.md` |
| Session ends with task complete | Update `.memory/PROJECT_STATE.md` |
| Handoff needed between sessions | Fill template; save `reports/phase2/handoff_YYYYMMDD.md` |
| Blocker resolved | Remove from `PROJECT_STATE.md` blocked_items AND log to `wiki/log.md` first |

---

## What Never Triggers a Write

- Temporary debugging or exploratory reads
- Unverified guesses or speculative hypotheses not yet tested
- Raw source dumps (paste text directly from crawls)
- Hallucinated summaries of files not actually read
- One-off exploration with no durable findings
- Re-logging a decision already in `wiki/log.md` (check last 3 entries before appending)

---

## Duplicate Prevention

Before appending to `wiki/log.md` or `wiki/open_questions/open-questions.md`, read the
most recent 3 entries to confirm the same decision or question is not already recorded.

---

## Maximum File Sizes

`.memory/` files should stay under 500 lines. If `PROJECT_STATE.md` or `INDEX.md`
approaches this limit, archive the oldest sections to a new dated file and update the
routing pointer in `INDEX.md`.
