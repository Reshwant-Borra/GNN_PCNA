# Collaboration Boundaries - GNN-PCNA

Two developers are working in parallel on this repo:

- **Owner (Reshwant)** - Phase 2 data, governance, splits, labels, and project state.
- **Friend** - Phase 3 model, training, evaluation, and baselines.

Phase 2 is complete as of 2026-05-27. Phase 3 implementation is authorized, but real
training still requires a verified data pipeline and explicit human sign-off.

---

## Current Coordination Status - 2026-05-28

- Phase 2 split and label manifests are frozen and human-approved.
- `reports/phase2/split_manifest_approval_20260527.md` authorizes removal of the Phase 3
  dry-run guard, but it does **not** bypass the human gate for the first real training run.
- Friend's full Phase 3 framework is reported by prior handoff text, but it is **not
  verified as present on this local `main` checkout**. As of this inspection, `src/phase3_*`,
  `src/baselines`, `tests/phase3`, and `reports/phase3` are absent locally.
- Friend completed and pushed/merged the Phase 2 crawl metadata support artifacts:
  `data/registries/friend_crawl_registry.json`, `data/registries/friend_feature_schema.json`,
  `data/registries/friend_crawl_homolog_groups.json`, `reports/phase2/friend_crawl_stats.md`,
  and `data/raw_intake/friend_sample/`.
- Friend is currently unavailable per Reshwant's handoff note. If Friend remains unavailable,
  Reshwant may continue or rebuild portions of Phase 3 independently in Codex. Document any
  ownership exception in the session handoff and wiki log.
- Do not assume the finalized Phase 3 codebase exists remotely until the branch or files are
  inspected directly.

---

## Friend / 40GB Crawl Use Policy

The committed crawl metadata describes a PCNA-focused experimental subset, not a governed
supervised training benchmark. Use it as follows:

1. **Phase 3 supervised benchmark training:** no. Use frozen CryptoBench only.
2. **Phase 4 external inference/discovery:** yes, after the Phase 3 model is frozen and
   provenance/holdout constraints are preserved.
3. **Future pretraining or expansion:** possible only under a separate governance decision
   with deduplication, clustering, benchmark-contamination checks, lifecycle status changes,
   and human approval.

Rationale: governance requires registry completeness, label definitions, split/leakage
control, provenance, and human review before any dataset enters training. The crawl metadata
currently has no computed homolog groups, incomplete ligand IDs/missing-residue fields, and
many PCNA/PCNA-associated records that must remain holdout-only.

---

## Ownership Table

| Area | Owner | Notes |
|---|---|---|
| `data/` | Reshwant | Dataset decisions, registries, splits, labels |
| `docs/scientific_governance/` | Reshwant | Scientific law; read by agents, edited only by Reshwant/human |
| `reports/phase2/` | Reshwant | Phase 2 audit trail; existing files are permanent |
| `.memory/PROJECT_STATE.md` | Reshwant | Current state snapshot; agents may update per memory rules |
| `wiki/` | Shared | Append/update with provenance per `.memory/MEMORY_RULES.md` |
| `src/phase2_intake/` | Reshwant | Governed intake pipeline |
| `scripts/` | Reshwant | Audit and validation scripts |
| `src/phase3_model/` | Friend | GNN architecture, unless Reshwant authorizes Codex rebuild |
| `src/phase3_training/` | Friend | Training harness, unless Reshwant authorizes Codex rebuild |
| `src/phase3_evaluation/` | Friend | Evaluation and metrics, unless Reshwant authorizes Codex rebuild |
| `src/baselines/` | Friend | fpocket, P2Rank, PocketMiner wrappers |
| `reports/phase3/` | Friend | Phase 3 experiment reports |
| `tests/phase3/` | Friend | Phase 3 tests |
| `AGENTS.md`, `CLAUDE.md` | Reshwant | Human-managed instruction files |

---

## What Friend Must Not Touch Without Coordination

Friend's agent must not modify:

```text
data/
docs/scientific_governance/
reports/phase2/
scripts/
src/phase2_intake/
CLAUDE.md
AGENTS.md
.memory/INDEX.md
.memory/MEMORY_RULES.md
```

Friend may contribute small read-only registry/support artifacts into Reshwant-owned folders
only when Reshwant reviews them before use in scientific decisions.

---

## What Phase 3 Can Build

Phase 3 can include:

- `src/phase3_model/` - graph encoder, residue-level prediction head, ablations.
- `src/phase3_training/` - data loader interface, training loop, checkpointing, dry-run guard.
- `src/phase3_evaluation/` - AUPRC, AUROC, Top-K recovery, bootstrap CIs.
- `src/baselines/` - fpocket, P2Rank, PocketMiner adapters.
- `tests/phase3/` - unit tests and contract tests.
- `reports/phase3/` - experiment tracking after the folder/code exists.

Phase 3 loaders must use frozen Phase 2 artifacts:

```text
data/registries/split_manifest_frozen.json
data/labels/labels_{apo_pdb_id}.json
data/raw_intake/cryptobench/cif-files/
data/registries/excluded_records.json
```

Do not use original CryptoBench `folds.json` for training splits.

---

## Training Gate

No real training may run until:

1. The Phase 3 data pipeline is implemented against frozen Phase 2 outputs.
2. The pipeline excludes all 6 records in `data/registries/excluded_records.json`.
3. `label=-1` residues are masked/excluded from loss, not treated as negatives.
4. PCNA cluster `cluster_id_30=1168` is excluded from train and validation.
5. Graph/label/provenance audits pass.
6. A human reviewer signs off on the data pipeline.

Governance applies to both developers and both agents. At minimum, read:

```text
docs/scientific_governance/16_CODING_AGENT_RULES.md
docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md
docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md
docs/scientific_governance/09_EVALUATION_PROTOCOL.md
docs/scientific_governance/10_BASELINE_REQUIREMENTS.md
docs/scientific_governance/14_CLAIM_POLICY.md
docs/scientific_governance/19_STOP_CONDITIONS.md
docs/scientific_governance/21_READINESS_GATE.md
docs/scientific_governance/26_HUMAN_REVIEW_GATES.md
```

---

## Merge / Conflict Avoidance

- Friend should work on a Phase 3 branch until the code can be reviewed.
- Reshwant/Codex should not assume Friend's unpushed local code exists on `main`.
- Neither developer should rewrite the other's owned files without coordination or a recorded exception.
- Existing `reports/phase2/*.md` files must not be overwritten; create new handoff/report files only.
