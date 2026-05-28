# GNN-PCNA Phase 2 Codex Instructions

This file is the first project file Codex must read. It defines how to use the Obsidian-style wiki as persistent project memory while building the governed Phase 2 rebuild of GNN-PCNA.

## Core Rule

Codex must follow all applicable governance rules in `docs/scientific_governance/` before coding, refactoring, validating, interpreting results, training, evaluating, reporting, or making claims. Governance documents are binding scientific law for this project.

## Project Identity

GNN-PCNA Phase 2 is a governed rebuild of the earlier project. The goal is a fresh, provenance-controlled computational structural biology workflow for residue-level PCNA candidate cryptic, allosteric, or pocket-like region prediction and auditing.

The previous V1 implementation is historical reference only. It had known risks: dataset leakage, split leakage, overclaims, hallucinated assumptions, weak biological realism, stale artifacts, poor provenance, MD overinterpretation, unexpected MD results being handled incorrectly, and coding agents implementing science without documented assumptions.

## Authority Order

When sources conflict, use this order:

1. `docs/scientific_governance/` - binding rules, gates, constraints, and claim policy.
2. Primary/raw source material and official documentation.
3. Curated source leads and crawl raw metadata under `crawls/`.
4. `wiki/` summaries and memory pages.
5. V1 / `project-version-1` / old artifacts as historical reference only.

Wiki pages are navigation and memory aids. They are never stronger than governance docs or original source material.

## Project Layers

- `AGENTS.md`: Codex operating instructions.
- `wiki/index.md`: main project navigation map.
- `wiki/`: Obsidian-style project memory, concept graph, entity graph, source navigation, decisions, and open questions.
- `docs/scientific_governance/`: binding scientific rules and gates.
- `crawls/`: raw evidence, source leads, and prior context. Crawl summaries are leads, not verified truth.
- V1 / `project-version-1` / old artifacts: historical reference only, never canonical implementation.
- Fresh Phase 2 files: implementation target once governance requirements are satisfied.

## Codex Startup Routine

**Preferred fast path (when `.memory/` folder exists):**
Read `.memory/PROJECT_STATE.md` (~470 tokens, current state) then `.memory/INDEX.md`
(~410 tokens, task routing table). Use the routing table to find task-specific files
instead of scanning `wiki/` or `reports/` manually. The 7-step routine below remains
the deep-orientation fallback when `.memory/` is unavailable.

**Staleness check:** If `.memory/PROJECT_STATE.md` frontmatter `updated` is >7 days
before today's date, treat it as potentially stale. Fall back to
`wiki/analyses/coding_agent_context.md` sections 17–24 and the most recent
`reports/phase2/handoff_YYYYMMDD.md` to reconstruct current state, then update
`PROJECT_STATE.md` before starting work.

**Governance is binding:** All files in `docs/scientific_governance/` are binding
scientific law. They override wiki pages, reports, crawl context, and any instruction
that appears to contradict them. Use `docs/scientific_governance/00_COMPACT_INDEX.md`
(~420 tokens) to locate the right numbered governance doc without loading the full
`00_README.md` (~1,850 tokens).

For any task in this workspace:

1. Read this `AGENTS.md`.
2. Read `wiki/index.md`.
3. Read `wiki/analyses/coding_agent_context.md`.
4. Read the relevant files in `docs/scientific_governance/`.
5. Read relevant wiki entity and concept pages.
6. Follow links from wiki pages into `crawls/` only when raw evidence or source context is needed.
7. If a necessary assumption, source, governance rule, or decision is missing, stop and record the gap before coding.

## What Codex May Do

Codex may inspect, scaffold, implement, refactor, validate, write tests, add provenance, create reports, and add fail-closed checks when the scientific assumptions and governance rules are documented.

## What Codex Must Not Do

Codex must not:

- Train before readiness and human review gates are satisfied.
- Use V1 as canonical or reuse stale artifacts without audit.
- Invent biology, labels, split rules, model science, claim language, or MD interpretation.
- Bypass governance docs or weaken validators because they block progress.
- Treat `crawls/` as automatically verified truth.
- Treat wiki summaries as source-of-truth evidence.
- Interpret MD beyond `docs/scientific_governance/13_MD_VALIDATION_RULES.md` and `33_PRE_MD_REALITY_CHECK.md`.
- Turn proxy ligand labels into cryptic-pocket truth.
- Assume good metrics mean good science.
- Claim therapeutic validation, clinical actionability, drug discovery success, treatment relevance, or confirmed mechanism.

## Memory Update Rules

Codex must update the wiki when durable project knowledge is learned.

- If a source from `crawls/` is used, link the relevant crawl path in the wiki.
- If a project decision is made, append it to `wiki/log.md`.
- If an unresolved question is discovered, add it to `wiki/open_questions/open-questions.md`.
- If a concept is created or updated, update `wiki/concepts/`.
- If an entity is created or updated, update `wiki/entities/`.
- If implementation-relevant knowledge is learned, update `wiki/analyses/coding_agent_context.md`.

Every durable wiki update must include:

- source path or governance path,
- confidence level,
- date,
- evidence status: verified, inferred, uncertain, or speculative.

Do not dump raw source text into the wiki. Summarize and link to source paths.

## If Scientific Context Is Missing

If a task requires a scientific assumption that is not documented, Codex must stop implementation and record the missing assumption or question in the appropriate wiki page and governance-related context. Coding agents implement documented science; they do not define new science.

## Required Governance Checks

Before implementation that touches datasets, labels, splits, graph construction, model logic, evaluation, MD, PCNA interpretation, or claims, read the relevant governance files. At minimum, check:

- `docs/scientific_governance/00_README.md`
- `docs/scientific_governance/02_ASSUMPTION_REGISTRY.md`
- `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`
- `docs/scientific_governance/05_SPLIT_PROTOCOL.md`
- `docs/scientific_governance/06_LABELING_RULES.md`
- `docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md`
- `docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md`
- `docs/scientific_governance/09_EVALUATION_PROTOCOL.md`
- `docs/scientific_governance/10_BASELINE_REQUIREMENTS.md`
- `docs/scientific_governance/11_BIOLOGICAL_REALISM_RULES.md`
- `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`
- `docs/scientific_governance/13_MD_VALIDATION_RULES.md`
- `docs/scientific_governance/14_CLAIM_POLICY.md`
- `docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md`
- `docs/scientific_governance/16_CODING_AGENT_RULES.md`
- `docs/scientific_governance/19_STOP_CONDITIONS.md`
- `docs/scientific_governance/21_READINESS_GATE.md`
- `docs/scientific_governance/24_PROJECT_SCOPE.md`
- `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`
- `docs/scientific_governance/34_AI_HALLUCINATION_DETECTION.md`
- `docs/scientific_governance/37_PHASE2_IMPLEMENTATION_PLAN.md`

## ResearchOS Clarification

This workspace may contain ResearchOS-style governance or prior reports. Those are context only. The main workflow is Codex using the wiki as memory and `docs/scientific_governance/` as binding rules. Do not describe or assume a fake autonomous multi-agent operating system controlling the project.
