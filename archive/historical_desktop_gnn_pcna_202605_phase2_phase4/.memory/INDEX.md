---
updated: 2026-05-27
maintainer: human-only
note: agents may NOT edit this file — write permission is human-only
---

# Memory Index — GNN-PCNA Phase 2

This is the task-routing table. Read it immediately after `.memory/PROJECT_STATE.md`.
It tells you exactly which files to open for each task type — do NOT scan `wiki/` or
`reports/` randomly.

---

## Always Read First

- `.memory/PROJECT_STATE.md` — current phase, blockers, next tasks (~470 tokens)

---

## Task Routing Table

### Data Audit / Dataset Investigation

Load in this order:

1. `data/registries/dataset_inventory.json`
2. `data/registries/cryptobench_candidate_cleaned_registry.json`
3. `reports/phase2/cryptobench_adoption_decision.md`
4. `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`
5. `docs/scientific_governance/29_BENCHMARK_LIMITATIONS.md`

Deeper reads (load only if needed):
- `reports/phase2/cryptobench_leakage_remediation.md`
- `docs/scientific_governance/05_SPLIT_PROTOCOL.md`
- `docs/scientific_governance/06_LABELING_RULES.md`
- `data/registries/potential_homolog_risks.json`
- `data/registries/residue_mapping_failures.json`

---

### Implementation (scripts, src, tests)

Load in this order:

1. `docs/scientific_governance/16_CODING_AGENT_RULES.md` ← **always first**
2. `docs/scientific_governance/37_PHASE2_IMPLEMENTATION_PLAN.md`
3. `wiki/analyses/coding_agent_context.md` (sections 17–24 for current status)

Then use `docs/scientific_governance/00_COMPACT_INDEX.md` to find the specific numbered
governance doc for the component you are implementing. Do not read all 40 docs.

---

### Governance Review

Load in this order:

1. `docs/scientific_governance/00_COMPACT_INDEX.md` (~420 tokens, 1-page map)
2. The specific numbered doc identified by the map

Do not read `00_README.md` (~1,850 tokens) just to locate one file — use the compact
index instead.

---

### Split / Label Freeze Planning

Load in this order:

1. `docs/scientific_governance/05_SPLIT_PROTOCOL.md`
2. `docs/scientific_governance/06_LABELING_RULES.md`
3. `reports/phase2/proposed_phase2_split_strategy.md`
4. `reports/phase2/proposed_label_policy.md`
5. `data/registries/potential_homolog_risks.json`

Deeper reads:
- `reports/phase2/pcna_isolation_policy.md`
- `data/registries/cryptobench_fold_summary.json`
- `data/registries/residue_mapping_failures.json`

---

### Biology / PCNA / Claims Review

Load in this order:

1. `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`
2. `docs/scientific_governance/14_CLAIM_POLICY.md`
3. `wiki/entities/PCNA.md`
4. `reports/phase2/pcna_contamination_screen.md`
5. `reports/phase2/pcna_isolation_policy.md`

---

### Session Handoff

1. Fill `.memory/AGENT_HANDOFF_TEMPLATE.md` schema **in working memory** (do not write to the template file itself)
2. Save the completed instance as `reports/phase2/handoff_YYYYMMDD.md`
3. Update `.memory/PROJECT_STATE.md` — move completed items to "What Is Done", remove resolved blockers, update "Next Tasks", replace "Last Session Summary" paragraph, refresh frontmatter `updated` and `updated_by`
4. If a durable decision was made: append to `wiki/log.md`
5. If a new question was found: append to `wiki/open_questions/open-questions.md`

---

## Full Memory Map (deep orientation only — use sparingly)

- `wiki/index.md` — full Obsidian wiki navigation dashboard
- `wiki/analyses/coding_agent_context.md` — 24-section detailed agent context
- `docs/scientific_governance/00_COMPACT_INDEX.md` — 1-page governance doc map
- `docs/scientific_governance/00_README.md` — full governance entrypoint (~1,850 tokens)
- `reports/phase2/` — 30+ permanent audit/decision reports
- `data/registries/` — 14 machine-readable JSON/JSONL registries
- `wiki/concepts/` — 20+ concept reference pages
- `wiki/entities/` — 14+ entity reference pages

---

## Write Permissions (quick reference — full rules in `.memory/MEMORY_RULES.md`)

### Agents MAY write

| Target | Mode |
|---|---|
| `.memory/PROJECT_STATE.md` | Overwrite targeted sections; always update `updated` date |
| `wiki/log.md` | **Append-only** — never edit existing entries |
| `wiki/open_questions/open-questions.md` | Append only; never delete |
| `wiki/analyses/coding_agent_context.md` | Append new numbered sections (§25+) only |
| `wiki/entities/*.md`, `wiki/concepts/*.md` | Update/append with required provenance |
| `reports/phase2/` | New files only — never overwrite existing reports |
| `data/registries/` | New files or JSONL append only |

### Agents must NOT write

```
CLAUDE.md  ·  AGENTS.md  ·  .memory/INDEX.md  ·  .memory/MEMORY_RULES.md
.memory/AGENT_HANDOFF_TEMPLATE.md  ·  docs/scientific_governance/  ·  wiki/index.md
```
