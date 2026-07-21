# GNN-PCNA — Incident Report & Remediation

**Date:** 2026-06-21  **Author:** Claude (Opus 4.8), on Advay's workstation
**Scope:** repo `Reshwant-Borra/GNN_PNCA`, all branches. Trigger: the Phase-5 MD validation
came back "negative"; task was to find why, make sure it can't recur, fix the GNN, rerun it,
report the cryptic pocket, and produce a 4070 MD re-run package.

**Method:** (1) direct diagnosis + local CPU reproduction of the model; (2) a 51-unit
multi-agent audit (537 agents, ~4.6M tokens) with adversarial dual-lens verification across
the model, MD, eval, research_os, paper_engine, and agent code. The audit hit the API session
limit during verification, so **11 findings are adversarially-confirmed**, 15 were rejected by
verification, and ~200 raw reviewer findings were left unverified (listed as "needs review").

---

## A. Headline: the MD result was not "negative biology" — it was an invalid test

The previous MD (1AXC, 25 ns, RunPod) concluded the GNN's candidate windows "showed no
cryptic-pocket opening." That conclusion is **uninterpretable**, for stacked reasons:

| # | Defect | Why it invalidates the negative | Status |
|---|--------|--------------------------------|--------|
| M1 | **Wrong "apo": 1AXC is p21-bound** (peptide deleted = "apo-from-p21"), relaxing from a bound state. Earlier the team also mis-used 5E0V (S228I+FEN1 variant). | Not a true apo conformation → wrong starting ensemble. | **Fixed**: 4070 pkg uses true apo **1W60**. |
| M2 | **No positive control** (8GLA holo never simulated). | Without showing the method can detect the *known* open pocket, a "no opening" reading means nothing. | **Fixed**: 8GLA is the built-in positive control + auto gate. |
| M3 | **Analyzed arbitrary "novel windows"** (239-243, 206-210, 28-32) — **not** the validated AOH1996 pocket. | Tested the wrong residues. | **Fixed**: analysis targets the AOH1996 pocket residues. |
| M4 | **n = 1** (rep2 died at the budget wall at 41 frames; rep3 never ran); ~20 ns usable. | Cryptic opening is ns–µs; 20 ns single-run almost never samples it → absence ≠ evidence. | **Fixed**: resumable 3×100 ns; killed runs continue. |
| M5 | **Solvated topology not saved** with the trajectory. | Downstream analysis (and paper_engine MD figures) were blocked. | **Fixed**: `system_solvated.pdb` saved next to every DCD. |
| M6 | **Analysis was numerically corrupt** (RMSD 2.468 nm ≈ 25 Å, RMSF 1–3 nm). | Garbage metrics. Root causes confirmed by audit below (C1, C2). | **Fixed** in `_fixed.py` and re-implemented correctly in the 4070 pkg. |

Per the project's own `docs/scientific_governance/13_MD_VALIDATION_RULES.md`, a negative MD is
a valid result — **but only if the test was capable of producing a positive.** M2+M4 mean it
wasn't. The honest status of the old run is **inconclusive/underpowered, not negative.**

---

## B. Adversarially-confirmed code findings (11)

### Critical — direct cause of the 25 Å artifact (MD analysis)
- **C1 `scripts/phase5_analyze_1axc_md.py:123-127` — RMSF computed about frame 0, not the mean.**
  Drift from the start frame is counted as "fluctuation," inflating RMSF. Fix: `mean_xyz =
  traj.xyz[:,ca,:].mean(0)`; deviate from that (or `mdtraj.rmsf`). *(verified, conf 0.85)*
- **C2 `phase5_analyze_1axc_md.py:82,95-101` — no PBC imaging before superposition.** A trimer
  wrapped across the periodic box gives ~7–10 nm jumps → 25 Å RMSD. Fix: `traj.image_molecules(
  inplace=True)` before any `superpose`/`rmsd`. *(verified, conf 0.95)*

### High
- **C3 `phase5_run_1axc_openmm.py:252` — MonteCarloBarostat active during the "NVT" phase.**
  The barostat is added before equilibration, so the intended constant-volume NVT is actually
  NPT. Fix: add the barostat only after NVT, or `setFrequency(0)` during NVT. *(conf 0.85)*
- **C4 `phase5_pocket_dynamics_1axc.py` — three monomers labeled "informal triplicates"
  (pseudoreplication).** Chains in one box are correlated, not independent replicates; this
  inflates confidence. Fix: drop "triplicates"; independent replicates need separate runs.
  *(conf 0.70)*
- **C5 `src/data_processing/fetch_structures.py:152-154` — 8GLA (3.77 Å) bypasses the 3.5 Å
  resolution hard-fail** via the `PCNA_CORE_IDS` allowlist. The holo positive control is below
  the pipeline's own quality bar, silently. Fix: raise the bar to 4.0 Å *with justification*,
  or flag the override. *(conf 0.80)*

### Medium
- **C6 `fetch_structures.py:138-140` — chain-count validation is advertised in the docstring but
  never enforced.** *This is the gap that lets wrong-chain structures (the 1AXC / 9B8T class of
  bug) pass as valid.* Fix: add `expected_chains` and fail when it mismatches. *(conf 0.90)*
- **C7 `fetch_structures.py:279`-style checkpoint resume — step count read from a possibly-absent
  `progress.json`, not the checkpoint**, risking duplicate appended frames on resume. Fix: derive
  `run_steps` from `simulation.currentStep`. *(conf 0.72)* *(the 4070 pkg already derives steps
  from the context, not a JSON.)*
- **C8 `fetch_structures.py:167` — Cα-completeness threshold is 90% in code but 95% in the
  docstring.** Silent quality-bar drift. Fix: make them match. *(conf 0.95)*
- **C9 `fetch_structures.py:183-187` — cached files are marked `skipped`, overwriting a `failed`
  verification.** A truncated/corrupt cached PDB is silently accepted. Fix: only mark `skipped`
  when verification passes. *(conf 0.90)*

15 further findings were **rejected** by adversarial verification (e.g., several "leakage" and
"hardcoded number" alarms turned out to be false). ~200 reviewer findings across the 51 units
were **not reached by verification** before the session cap — they are unconfirmed and should be
re-run after the limit resets (the workflow is resumable).

---

## C. The GNN model itself — reran and reproduces exactly (no defects found)

The model is **not** the problem. On local CPU from `checkpoints/pcna_reproduced/best.ckpt`:
- **AOH1996 gate:** pocket mean **0.8676**, top residue **#1/952**, gate **PASS** (recorded 0.8676 ✓)
- **Held-out 13 proteins:** **AUROC 0.8081, AUPRC 0.3441** (recorded 0.8081 / 0.3441 ✓)

### One scientific nuance surfaced on rerun (flag for human gate — NOT silently changed)
At **matched pocket residues**, the GNN scores the AOH1996 site ~**0.87 in holo (8GLA)** and
~**0.91 in apo (1W60)** → per-residue holo−apo Δ ≈ **−0.04**. The recorded `disc_score = 0.741`
is `mean(holo pocket) − mean(ALL apo residues = 0.127)` = foreground-vs-background, **not** an
apo↔holo discriminator. Implication: the GNN correctly **flags the pocket site from the closed
apo structure** (good for cryptic-site prediction) but gives **no residue-level opening signal on
its own** → the "cryptic/dynamic" claim depends entirely on MD. This raises the stakes on getting
the MD right, and it should be reviewed by Reshwant before any metric wording is changed
(governance: model/eval is Reshwant's, behind a human gate).

---

## D. What was fixed, and how

1. **MD validation pipeline — rebuilt** as `md_validation_4070/` (run_md.py, analyze_md.py,
   environment.yml, README): true apo 1W60 + holo 8GLA positive control, AOH1996-pocket-targeted
   analysis, resumable 3×100 ns, topology saved with every DCD, HMR+4 fs, **PBC-imaged analysis
   with an automatic positive-control gate that reports "inconclusive" instead of "negative" when
   the metric can't separate open from closed.** This directly remediates M1–M6, C1–C4, C7.
2. **GNN reran & verified** — AOH gate + held-out eval reproduce the recorded numbers exactly
   (`md_validation_4070/RERUN_EVIDENCE.md`).
3. **`src/data_processing/fetch_structures.py` (C5,C6,C8,C9)** — exact patches are documented
   above. **Not auto-applied**: this is Reshwant's model branch and the project governance
   requires a human gate for model/data-pipeline changes. Recommend Reshwant apply C6 (chain-count
   enforcement) first — it's the structural guard against the recurring chain-assignment bug.

## E. Recommended next steps (for the human gate)
1. Reshwant authorizes GATE 7; friend runs the 4070 package (8GLA control first).
2. Apply C5/C6/C8/C9 to `fetch_structures.py` (C6 is the priority).
3. After the session limit resets, resume the audit workflow to verify the remaining ~200
   reviewer findings (`Workflow({scriptPath, resumeFromRunId:"wf_1d5eb77e-7ef"})`).
4. Do not state "no cryptic opening" until the positive-control gate in analyze_md.py reads
   `interpretable: true`.
