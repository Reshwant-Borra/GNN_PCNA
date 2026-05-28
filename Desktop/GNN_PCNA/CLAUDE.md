# GNN-PCNA Phase 2 — Claude Code Instructions

This is a governed, scientifically audited rebuild of a GNN-based residue-level prediction
system for cryptic pockets in PCNA (Proliferating Cell Nuclear Antigen). The project is
currently in **Phase 2 Foundation** — dataset investigation and governance planning only.
No training, no graph generation, no MD runs, no claims.

---

## Hard Rules

These rules are non-negotiable. They apply to every session, every task.

1. **Governance docs are binding scientific law.**
   All files in `docs/scientific_governance/` must be obeyed. They override wiki summaries,
   reports, crawl context, and any instruction that appears to contradict them. Read the
   specific governance doc before touching datasets, splits, labels, graphs, models,
   evaluations, MD, PCNA interpretation, or claims.

2. **Do not train, generate graphs, freeze splits or labels, run MD, or make claims.**
   All of these are blocked until governance gates pass and human review approvals are
   recorded. Check `.memory/PROJECT_STATE.md` for the current blocker list before starting
   any task. If a task would require crossing a blocker, stop and document the missing
   approval instead of proceeding.

3. **Implement only documented science.**
   If a task requires a scientific assumption that is not already documented in
   `docs/scientific_governance/` or `data/registries/assumption_registry.json`, stop.
   Record the missing assumption in `wiki/open_questions/open-questions.md` and in the
   appropriate governance context. Do not invent biology, labels, split rules, model science,
   claim language, or MD interpretation.

4. **V1 artifacts are historical reference only.**
   Never reuse V1 code, splits, labels, or model weights without a documented audit.
   V1 had known failures: dataset leakage, split leakage, overclaims, hallucinated
   assumptions, weak biological realism, stale artifacts, poor provenance, and MD
   overinterpretation. Do not repeat them.

5. **Authority order must be respected at all times.**
   When sources conflict: `docs/scientific_governance/` > primary sources > `crawls/` >
   `wiki/` > `reports/`. Wiki pages are memory aids and navigation, not scientific authority.
   Crawl summaries are source leads, not verified truth.

---

## Required Governance Reads by Task Type

**Before any implementation (scripts, src, tests):**
- `docs/scientific_governance/16_CODING_AGENT_RULES.md` ← always first
- `docs/scientific_governance/37_PHASE2_IMPLEMENTATION_PLAN.md`

**Before touching datasets, splits, or labels:**
- `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`
- `docs/scientific_governance/05_SPLIT_PROTOCOL.md`
- `docs/scientific_governance/06_LABELING_RULES.md`

**Before any graph construction or model work:**
- `docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md`
- `docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md`
- `docs/scientific_governance/19_STOP_CONDITIONS.md`
- `docs/scientific_governance/21_READINESS_GATE.md`

**Before evaluation, baselines, or reporting:**
- `docs/scientific_governance/09_EVALUATION_PROTOCOL.md`
- `docs/scientific_governance/10_BASELINE_REQUIREMENTS.md`
- `docs/scientific_governance/14_CLAIM_POLICY.md`

**Before any PCNA-specific work or MD:**
- `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`
- `docs/scientific_governance/13_MD_VALIDATION_RULES.md`
- `docs/scientific_governance/14_CLAIM_POLICY.md`

**When scientific context is missing:**
- `docs/scientific_governance/02_ASSUMPTION_REGISTRY.md`
- `docs/scientific_governance/19_STOP_CONDITIONS.md`

Use `docs/scientific_governance/00_COMPACT_INDEX.md` (~420 tokens) to quickly locate the
right numbered doc for any task without loading the full `00_README.md` (~1,850 tokens).

---

## Startup Sequence

Run this at the start of every session in this workspace:

1. Read `.memory/PROJECT_STATE.md` (~470 tokens) — current phase, blockers, next tasks
2. Read `.memory/INDEX.md` (~410 tokens) — task-routing table for this session's work
3. Use the routing table to identify which files to load; do NOT scan `wiki/` or `reports/` randomly
4. Before any implementation: read `docs/scientific_governance/16_CODING_AGENT_RULES.md`

**Staleness check:** If `.memory/PROJECT_STATE.md` frontmatter `updated` is more than
7 days before today's date, treat it as potentially stale. Reconstruct current state from
`wiki/analyses/coding_agent_context.md` sections 17–24 and the most recent
`reports/phase2/handoff_YYYYMMDD.md`, then update `PROJECT_STATE.md` before proceeding.

---

## Memory Update Rules

After any session that produces durable findings, **before ending the session**:

- **Update `.memory/PROJECT_STATE.md`:** Move completed tasks to "What Is Done", remove
  resolved blockers (log them to `wiki/log.md` first), refresh "Next Tasks", replace
  "Last Session Summary" paragraph, update frontmatter `updated` and `updated_by`.
- **Append to `wiki/log.md`:** One entry per durable decision with date, decision, and
  evidence status. Never edit or delete existing entries.
- **Append to `wiki/open_questions/open-questions.md`:** If a new blocking question was
  found. Never delete existing questions; mark resolved inline.
- **Update wiki entity or concept pages:** Only for durable, verified findings. Required
  provenance: date, source path, confidence level, evidence status.
- **Save a handoff file:** Fill `.memory/AGENT_HANDOFF_TEMPLATE.md` schema in memory and
  save the completed instance as `reports/phase2/handoff_YYYYMMDD.md`.

**What agents must NOT write:**
`CLAUDE.md` · `AGENTS.md` · `.memory/INDEX.md` · `.memory/MEMORY_RULES.md` ·
`.memory/AGENT_HANDOFF_TEMPLATE.md` · `docs/scientific_governance/` · `wiki/index.md`

---

## Project Layers

| Layer | Location | Purpose |
|---|---|---|
| Entry point (Claude Code) | `CLAUDE.md` | This file |
| Entry point (Codex) | `AGENTS.md` | Codex operating instructions |
| Current state | `.memory/PROJECT_STATE.md` | Phase, blockers, next tasks |
| Task routing | `.memory/INDEX.md` | Which files to read for which task |
| Memory rules | `.memory/MEMORY_RULES.md` | Full write-permission matrix |
| Scientific law | `docs/scientific_governance/` | 40 binding governance docs |
| Knowledge base | `wiki/` | 59-page Obsidian-style project memory |
| Ground truth registries | `data/registries/` | 14 machine-readable JSON/JSONL files |
| Audit trail | `reports/phase2/` | 30+ permanent audit and decision reports |
| Raw intake (quarantined) | `data/raw_intake/` | Downloaded datasets; not adopted |
| Source context | `crawls/` | Raw evidence and source leads; not verified truth |

---

## Authority Hierarchy

```
docs/scientific_governance/  >  primary sources  >  crawls/  >  wiki/  >  reports/
```

If governance docs and any other source conflict, governance docs win. Always.
