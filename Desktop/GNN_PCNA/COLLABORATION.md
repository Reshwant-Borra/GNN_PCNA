# Collaboration Boundaries — GNN-PCNA

Two developers are working in parallel on this repo:

- **Owner (Reshwant)** — finishing Phase 2 (data, governance, splits, labels)
- **Friend** — building Phase 3 (model, training, evaluation, baselines)

Phase 3 can be built in parallel with Phase 2 **as a framework only** — no training may
run until Phase 2 blockers are resolved and datasets/splits/labels are frozen. Check
`.memory/PROJECT_STATE.md` to see current blocker status before attempting any training.

---

## What Each Person Owns

| Area | Owner | Notes |
|---|---|---|
| `data/` (all subfolders) | Reshwant | All dataset decisions, registries, splits, labels |
| `docs/scientific_governance/` | Reshwant | Scientific law — both read, only Reshwant edits |
| `reports/phase2/` | Reshwant | Phase 2 audit trail — append only, Reshwant manages |
| `.memory/PROJECT_STATE.md` | Reshwant | Phase 2 drives project state; Friend reads but defers to Reshwant for updates |
| `wiki/` | Shared | Both append; follow rules in `.memory/MEMORY_RULES.md` |
| `src/phase3_model/` | Friend | GNN architecture |
| `src/phase3_training/` | Friend | Training harness |
| `src/phase3_evaluation/` | Friend | Evaluation and metrics pipeline |
| `src/baselines/` | Friend | fpocket, P2Rank, PocketMiner wrappers |
| `reports/phase3/` | Friend | Phase 3 experiment reports |
| `src/phase2_intake/` | Reshwant | Data intake pipeline — Friend does not modify |
| `scripts/` | Reshwant | Audit and validation scripts — Friend does not modify |
| `AGENTS.md`, `CLAUDE.md` | Reshwant | Instruction files — Friend reads, does not edit |

---

## What Friend Must NOT Touch

Friend's Claude Code agent must never modify:

```
data/                          ← all dataset/split/label decisions are Reshwant's
docs/scientific_governance/   ← scientific law, human-only edits
reports/phase2/                ← Reshwant's audit trail
scripts/                       ← Reshwant's validation scripts
src/phase2_intake/             ← Reshwant's intake pipeline
CLAUDE.md                      ← Reshwant's agent instructions
AGENTS.md                      ← shared instructions, Reshwant manages
.memory/INDEX.md               ← human-only
.memory/MEMORY_RULES.md        ← human-only
```

---

## What Friend CAN Build Now (Before Phase 2 Completes)

Friend can fully build the Phase 3 framework in anticipation of frozen data:

- **GNN model architecture** in `src/phase3_model/` — design the graph encoder,
  residue-level prediction head, and any ablation variants
- **Training harness** in `src/phase3_training/` — data loader stubs (using frozen
  split manifest interface), training loop, checkpointing; use placeholder paths for
  data until splits are frozen
- **Evaluation pipeline** in `src/phase3_evaluation/` — metrics (AUPRC, AUROC, Top-K
  Recovery), bootstrap CIs per `docs/scientific_governance/09_EVALUATION_PROTOCOL.md`
- **Baseline wrappers** in `src/baselines/` — fpocket, P2Rank, PocketMiner adapters
- **Tests** in `tests/phase3/` — unit tests for model components and metric functions
- **Phase 3 reports folder** — create `reports/phase3/` for experiment tracking

---

## What Friend Must Wait For

Friend's code must not run training, evaluation on test data, or make any results claims
until ALL of these are cleared in `.memory/PROJECT_STATE.md`:

1. CryptoBench adoption approved (blocker 1)
2. PCNA isolation policy approved (blocker 2)
3. Sequence clustering complete (blocker 3)
4. Residue mapping failure policy resolved (blocker 4)
5. Label policy approved (blocker 5)
6. Split frozen (blocker 6)

Build the training harness to accept a frozen split manifest path as input. Use a
`--dry-run` flag or similar guard so the pipeline cannot accidentally train on unfrozen
data.

---

## Governance Rules Apply to Both

Both developers and both Claude Code agents must follow `docs/scientific_governance/`.
Friend must read at minimum before implementing Phase 3:

- `docs/scientific_governance/16_CODING_AGENT_RULES.md`
- `docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md`
- `docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md`
- `docs/scientific_governance/09_EVALUATION_PROTOCOL.md`
- `docs/scientific_governance/10_BASELINE_REQUIREMENTS.md`
- `docs/scientific_governance/14_CLAIM_POLICY.md`
- `docs/scientific_governance/19_STOP_CONDITIONS.md`
- `docs/scientific_governance/21_READINESS_GATE.md`
- `docs/scientific_governance/37_PHASE2_IMPLEMENTATION_PLAN.md`

Use `docs/scientific_governance/00_COMPACT_INDEX.md` to locate additional docs fast.

---

## Merge / Conflict Avoidance

- Friend works on a separate branch: `phase3-model-framework`
- Reshwant works on: `phase2-dataset-investigation` (or `main` after Phase 2 merges)
- Neither merges to `main` without reviewing the other's recent changes in their owned area
- If Friend needs to update `wiki/` or `.memory/PROJECT_STATE.md`, coordinate with Reshwant first to avoid conflicts
- `data/registries/` and `reports/phase2/` are append-only from Friend's perspective — never rewrite, never delete

---

## Quick Reference for Friend's Claude Code Agent

**Read first:**
1. `CLAUDE.md` — project rules and governance
2. `.memory/PROJECT_STATE.md` — current blockers (training is blocked until these clear)
3. `.memory/INDEX.md` — task routing
4. `COLLABORATION.md` — this file, boundaries

**Your working directories:**
`src/phase3_model/` · `src/phase3_training/` · `src/phase3_evaluation/` · `src/baselines/` · `reports/phase3/` · `tests/phase3/`

**Do not touch:**
`data/` · `docs/scientific_governance/` · `reports/phase2/` · `scripts/` · `src/phase2_intake/` · `CLAUDE.md` · `AGENTS.md`
