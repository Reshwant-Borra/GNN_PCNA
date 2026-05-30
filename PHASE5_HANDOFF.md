# Phase 5 Handoff — Post-MD Analysis and Paper

**Branch:** `codex/phase5-runpod-md-package`
**Date:** 2026-05-30
**For:** Co-author taking the MD outputs from RunPod through to the research paper.
**Author note:** Reshwant ran the time-crunch MD on RunPod; he is handing off the
post-MD analysis + paper writing. This file is the single entry point.

---

## TL;DR — what you need to do

1. **Set up the environment** → see `docs/PHASE5_SETUP.md`.
2. **Drop the RunPod outputs** into `outputs/phase5_md/time_crunch_1axc_25ns/`
   (structure shown below). `outputs/phase5_md/` is gitignored on purpose — large MD
   artifacts live outside git.
3. **Run the analysis script:**
   ```bash
   python scripts/phase5_analyze_1axc_md.py \
     --run-root outputs/phase5_md/time_crunch_1axc_25ns \
     --windows 239-243 28-32 206-210 134-138 \
     --reference-window 118-122
   ```
4. **QA trajectories first**, then interpret per pre-registration. Do not change the
   pre-registered hypotheses to match the data.
5. **Get human review** of the MD interpretation before any claim language is finalized.
6. **Write the paper** with the claim guardrails in this file. Do not exceed them.

---

## What is on this branch (everything you need)

### Plan and execution package
- `reports/phase5/time_crunch_validation_plan_20260529.md` — full plan and rationale.
- `reports/phase5/runpod_execution_package_20260529.md` — RunPod execution package.

### Phase 5 scripts (already on branch)
- `scripts/phase5_prepare_1axc_openmm.py` — system prep (1AXC, remove p21, add Hs).
- `scripts/phase5_run_1axc_openmm.py` — production runner (3 × 25 ns).
- `scripts/phase5_analyze_1axc_md.py` — **post-MD analysis (this is what you run).**
- `scripts/phase5_runpod_one_shot.sh` — RunPod one-shot launcher (already used).

### Pre-registered MD hypotheses (binding — read before analysis)
- `reports/phase4/md/1axc/pre_registration.md` — 1AXC apo-from-p21 hypothesis.
- `reports/phase4/md/8gla/pre_registration.md` — deferred positive control reference.
- `reports/phase4/md/5e0v/pre_registration.md` — deferred reference.

### Phase 4 inference artifacts (paper "Results — model" section inputs)
- `reports/phase4/phase4_inference_results_20260529.json` — per-residue scores, 103 PCNA structures.
- `reports/phase4/phase4_candidate_report_20260529.md` — ranked candidate regions.
- `reports/phase4/phase4_candidate_prioritization_20260529.md` — Tier 1A/1B/2/3 list.
- `reports/phase4/phase4_interface_overlap_20260529.md` — known-interface overlap analysis.
- `reports/phase4/phase4_pcna_audit_20260529.md` — PCNA-specific audit.
- `reports/phase4/gate6_authorization_20260529.md` — GATE 6 authorization record.
- `reports/phase4/gate7_md_decision_draft_20260529.md` — Wave 1 candidate rationale.
- `reports/phase4/heuristic_score_analysis.md` + `reports/phase4/figures/*.png`.

### Phase 3 model + test artifacts (paper "Methods/Results — model" section inputs)
- `reports/phase3/test_evaluation_20260529.md` — **FINAL test results, one-shot used.**
  Test macro-AUPRC: **0.2034** [0.1825, 0.2275] 95% CI. Do not re-run.
- `reports/phase3/model_freeze_gate4_20260529.md` — frozen checkpoint record.
- `reports/phase3/first_training_results_20260528.md` — training results.
- All Phase 3 baseline / training / graph release reports.
- `data/registries/split_manifest_frozen.json` — frozen splits (hash: `24dd5e347d880108`).
- `data/labels/label_manifest.json` — frozen labels.

### Governance (read these before writing claim language)
- `docs/scientific_governance/13_MD_VALIDATION_RULES.md` — MD evidence rules.
- `docs/scientific_governance/14_CLAIM_POLICY.md` — **what you can and cannot say.**
- `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md` — PCNA-specific rules.
- `docs/scientific_governance/10_BASELINE_REQUIREMENTS.md` — superiority-claim gate.
- `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md` — first MD interpretation is a
  human-review gate.
- `docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md` — MANIFEST rules.
- `docs/scientific_governance/00_COMPACT_INDEX.md` — index to all 40 governance docs.

### Memory and routing
- `.memory/PROJECT_STATE.md` — current phase state, blockers, next tasks.
- `.memory/INDEX.md` — task-to-file routing table.
- `CLAUDE.md` / `AGENTS.md` — operating instructions for AI agents working in the repo.

---

## What is NOT on this branch (intentional)

| Path | Why excluded | Action if you need it |
|---|---|---|
| `outputs/phase5_md/` | RunPod MD trajectories — too large for git. | Copy from RunPod into this directory locally. |
| `data/graphs/*.npz`, `data/graphs/*_meta.json` | 1,101 training graph tensors — large, regenerable. | Not needed for post-MD or paper. Regenerable from `src/phase3_graphs/` if ever needed. |
| `data/raw_intake/` | Quarantined raw CIFs — governance excludes from git. | Not needed for post-MD or paper. |
| `crawls/` | Raw source-evidence crawls. | Not needed for post-MD or paper. |

---

## Expected RunPod output layout (drop here)

After copying from RunPod, the directory should look like:

```
outputs/phase5_md/time_crunch_1axc_25ns/
├── MANIFEST.md                              # auto-generated by run script
├── inputs/
│   ├── 1axc_pcna_apo_from_p21_prepared.pdb
│   └── 1axc_pcna_apo_from_p21_structure_audit.json
├── replicate_01/
│   ├── trajectory.dcd                       # the big one (~hundreds of MB)
│   ├── solvated_initial.pdb                 # topology for mdtraj
│   ├── state.csv
│   ├── checkpoint.chk
│   ├── final.pdb
│   ├── progress.json
│   └── COMPLETE.json
├── replicate_02/   # same structure
└── replicate_03/   # same structure
```

If the RunPod run packaged everything as a `.tgz`, the package will be at
`outputs/phase5_md/packages/phase5_time_crunch_1axc_25ns_*_status0.tgz` — untar into
`outputs/phase5_md/` and the structure above appears.

---

## Post-MD critical-path checklist

### Step 1 — Trajectory QA (do before anything else)
- Confirm `COMPLETE.json` exists in each replicate dir. If any replicate is missing,
  report N replicates honestly — do not backfill.
- Look at `state.csv` per replicate: temperature ~300 K stable, density ~1.0 g/cm³,
  no energy blow-up.
- Run the analysis script (it produces backbone RMSD plots — your stability check):
  ```bash
  python scripts/phase5_analyze_1axc_md.py \
    --run-root outputs/phase5_md/time_crunch_1axc_25ns
  ```
- Verify the trimer is intact (no chain drift). The script computes per-replicate
  backbone CA RMSD; any replicate with RMSD > ~0.5 nm growing without plateau is
  suspicious and must be flagged in the MANIFEST.

### Step 2 — Per-window metrics (the analysis script does this)

Script writes to `outputs/phase5_md/time_crunch_1axc_25ns/analysis/`:
- `rmsd_timeseries.csv` + `rmsd_timeseries.png` — global stability.
- `window_rmsf.csv` — per-residue RMSF for each candidate window per replicate.
- `window_summary.csv` — mean/max RMSF per window per replicate + backbone RMSD context.
- `window_rmsf_summary.png` — across-replicate window comparison.
- `analysis_summary.json` — counts and built-in limitation statements.

Windows analyzed:
- Tier 1A: `239-243`, `28-32`, `206-210`
- Tier 2 control: `134-138` (IDCL/PIP-adjacent)
- Read-only reference: `118-122` (internal IDCL/front-face reference — **not** the
  official 8GLA positive control, which was deferred)

### Step 3 — Pre-registered interpretation table

Per `docs/scientific_governance/13_MD_VALIDATION_RULES.md`, for each window mark one of:
**supports / partially supports / inconclusive / weakens / contradicts** the hypothesis
in `reports/phase4/md/1axc/pre_registration.md`.

Negative and inconclusive outcomes are valid evidence — report them. Do not
post-hoc rewrite hypotheses to match results.

Suggested output: `reports/phase5/interpretation_table_YYYYMMDD.md`.

### Step 4 — Human-review gate

Per `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`, the first MD interpretation
requires human review. Record the decision at
`reports/phase5/md_interpretation_human_review_YYYYMMDD.md`.

### Step 5 — Claim audit before paper text is finalized

Apply `docs/scientific_governance/14_CLAIM_POLICY.md`. The MD section is allowed
language similar to:

> "Short-timescale exploratory MD of 1AXC apo-from-p21 was performed (3 × 25 ns).
> Under this limited setup, the specified windows showed/did not show early local
> flexibility or geometry changes. Results are hypothesis-generating and require
> longer simulations and the deferred 8GLA positive-control system."

The MD section is **not** allowed to claim: validated site, druggable, binding
confirmed, therapeutic, mechanism, novel pocket established, superior to other
methods.

### Step 6 — Session-close memory updates (per `CLAUDE.md`)
- Update `.memory/PROJECT_STATE.md` (move GATE 7 from blocked → executed with limitations).
- Append a single entry to `wiki/log.md` (decision + evidence status).
- Save a handoff at `reports/phase5/handoff_YYYYMMDD.md` using `.memory/AGENT_HANDOFF_TEMPLATE.md`.
- Append any new blockers to `wiki/open_questions/open-questions.md`.

---

## Paper-section guidance (what to write, what to gate)

### Methods / Model
- Architecture: GraphSAGE-3L spatial-only (hidden_dim=128).
- Frozen checkpoint: `checkpoints/phase3/spatial_only_fold1_seed1_best.pt`.
- Splits: PCNA cluster `cluster_id_30=1168` is holdout-only — no PCNA in train/val.
- Training: 12 runs (4 folds × 3 seeds), val macro-AUPRC 0.1897 ± 0.0091 spatial-only.
- Test: **one-shot** on 214 held-out structures, macro-AUPRC **0.2034** [0.1825, 0.2275].
- Source: `reports/phase3/test_evaluation_20260529.md`.

### Results — Model
- Per-residue inference on 103 PCNA structures (`reports/phase4/phase4_inference_results_20260529.json`).
- Candidate windows ranked → Tier 1A/1B/2/3
  (`reports/phase4/phase4_candidate_prioritization_20260529.md`).
- Known-interface overlap audit
  (`reports/phase4/phase4_interface_overlap_20260529.md`).
- Trimer-interface high-scoring region (170-179, 152-156) — explainable by known clamp
  geometry, **not** druggability.

### Results — MD
- 1AXC apo-from-p21, 3 × 25 ns, time-crunch exploratory.
- Per-window RMSF and backbone RMSD trends.
- Pre-registered interpretation table.
- **Mandatory caveats** (do not omit any):
  - Short-timescale.
  - Single starting structure.
  - 8GLA positive-control system deferred.
  - Tier 1B trimer-interface candidates deferred (Wave 2, enhanced sampling required).
  - 1AXC apo-from-p21 may reflect relaxation from a peptide-bound conformation.

### Limitations / Future Work
- **Externally-published baseline tools (fpocket, P2Rank, PocketMiner) were not run.**
  Per `docs/scientific_governance/10_BASELINE_REQUIREMENTS.md`, do NOT make any
  "better than state-of-the-art" claim until these are run on the frozen test split.
  State this limitation explicitly.
- 8GLA positive-control MD deferred.
- Wave 2 (trimer-interface Tier 1B) deferred to enhanced-sampling MD.

### Hard claim guardrails (re-read before submission)
- No "validated cryptic pocket."
- No "druggable target."
- No "therapeutic" / "drug discovery" claim.
- No "binding site discovered."
- No "outperforms [tool]" without external baselines.
- No "mechanism of [process]" from MD alone.

---

## Quick reference — the "everything pushed?" verification

If something below is missing, the branch was not synced — ping Reshwant.

```bash
git fetch origin codex/phase5-runpod-md-package
git status                       # should be clean, up to date with remote
git log --oneline origin/main..  # should show 5 phase5 commits

# These files must exist on the branch:
ls reports/phase5/time_crunch_validation_plan_20260529.md
ls reports/phase5/runpod_execution_package_20260529.md
ls scripts/phase5_prepare_1axc_openmm.py
ls scripts/phase5_run_1axc_openmm.py
ls scripts/phase5_analyze_1axc_md.py
ls scripts/phase5_runpod_one_shot.sh
ls envs/phase5_md_runpod.yml
ls reports/phase4/md/1axc/pre_registration.md
ls reports/phase4/phase4_candidate_prioritization_20260529.md
ls reports/phase3/test_evaluation_20260529.md
ls docs/scientific_governance/13_MD_VALIDATION_RULES.md
ls docs/scientific_governance/14_CLAIM_POLICY.md
ls .memory/PROJECT_STATE.md
ls PHASE5_HANDOFF.md
ls docs/PHASE5_SETUP.md
```

---

## Contact / handoff status

- Reshwant: ran RunPod MD; handoff complete after this file is pushed.
- Co-author (you): post-MD analysis through paper.
- Any blocker found mid-analysis → log it in
  `wiki/open_questions/open-questions.md` with date and source path.
