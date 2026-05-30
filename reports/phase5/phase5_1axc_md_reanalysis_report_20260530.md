# Phase 5 — 1AXC MD Re-analysis Report (RMSF / Pocket Dynamics)

**Date:** 2026-05-30
**Author:** automated re-analysis (Claude) on Advay's workstation
**System:** 1AXC PCNA homotrimer, apo-from-p21, time-crunch RunPod run
**Run root (external, not committed):** `outputs/phase5_md/time_crunch_1axc_25ns/`
**Scripts:** `scripts/phase5_analyze_1axc_md_fixed.py`, `scripts/phase5_pocket_dynamics_1axc.py`
**Result artifacts (committed):** `reports/phase5/md_reanalysis_1axc/`

> **Governance status — READ FIRST.** This document reports **metrics and an analyst's
> candidate reading only**. Per `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`,
> *first MD interpretation* is a mandatory human gate, and per
> `reports/phase4/gate7_md_decision_draft_20260529.md` **GATE 7 was never authorized** —
> this run executed ahead of that gate as an exploratory time-crunch triage. Nothing here
> is an approved scientific conclusion or a paper-ready claim. Any supports/weakens/falsifies
> statement requires a recorded decision by **Reshwant-Borra** citing this evidence packet.

---

## 1. Required statement (doc 13)

MD can support, weaken, redirect, or falsify the working hypothesis. All outcomes are
evidence. Negative and inconclusive MD results are valid and are reported honestly. Absence
of pocket opening is not a failed run.

## 2. What was actually run

| Item | Value |
|---|---|
| Structure | 1AXC, human PCNA homotrimer (3 chains × 261 res), p21 peptide removed (apo-from-p21) |
| Engine / FF | OpenMM 8.2, AMBER14, TIP3P, ~62k residues solvated (~287k atoms) |
| Hardware | RunPod NVIDIA B200, $30 hard budget |
| replicate_01 | **complete, 25 ns**, 250 frames @ 0.1 ns/frame — **the only usable replicate** |
| replicate_02 | **incomplete** — killed at budget wall, 41 frames (< the 5 ns equilibration window) |
| replicate_03 | not run (budget) |
| Positive control (8GLA AOH1996) | **not run** — deferred |

Effective statistical power: **n = 1**, 25 ns, single structure, no positive control.

## 3. The original analysis was corrupted — and is now fixed

The RunPod analysis (`scripts/phase5_analyze_1axc_md.py`) reported physically impossible
numbers: backbone RMSD **2.468 nm (~25 Å)** and per-window RMSF **1–3 nm**. A stable folded
protein sits at RMSD ~0.2–0.3 nm and loop RMSF ~0.05–0.3 nm.

Root cause (confirmed): the script **superposed without first imaging periodic boundaries**.
The PCNA *trimer* wraps across the periodic box, so the rigid-body fit periodically failed,
producing ~4 nm RMSD spikes at isolated frames that dragged the mean up. Secondary bugs: RMSF
was computed about *frame 0* rather than the mean position, and `replicate_02` (incomplete)
was treated as a valid replicate.

**Corrected pipeline** (`scripts/phase5_analyze_1axc_md_fixed.py`):
1. `make_molecules_whole` + `image_molecules` **before** superposition.
2. Align on a stable core = protein Cα **excluding** the analyzed windows (no circularity).
3. RMSF about the **mean** position.
4. Discard first **5 ns** equilibration before RMSF.
5. Flag incomplete replicates.

The run log shows the *simulation itself* was stable throughout (potential energy flat at
~−2.68M kJ/mol, T = 300 K, density ~1.01 g/mL) — so the trajectory is sound and salvageable;
only the analysis was wrong.

## 4. Corrected stability & RMSF results (replicate_01, 200 frames post-equil)

**Backbone Cα RMSD:** mean **0.255 nm**, max 0.305, final 0.287 — flat plateau, textbook-stable
trimer (was a bogus 2.468 nm → ~10× artifact removed).

**Per-window Cα RMSF:**

| Window | Tier | Cα RMSF (nm) | vs 118-122 ref |
|---|---|---|---|
| 239-243 | 1A (novel cand A) | 0.081 | 0.65× |
| 28-32 | 1A (novel cand B) | 0.081 | 0.65× |
| 206-210 | 1A (novel cand C) | 0.074 | 0.59× |
| 134-138 | 2 (IDCL-adjacent ctrl) | 0.084 | 0.67× |
| **118-122 reference** | 3 (IDCL ctrl) | **0.126** | 1.00× |

RMSF dropped from the corrupted 1–3 nm to **0.07–0.13 nm** (~20–30× artifact removed). All
candidate windows are *less* flexible than the IDCL reference.

## 5. Pocket-dynamics metrics (RMSF alone cannot answer "does the pocket move")

Computed per monomer (chains 0/1/2 as informal triplicates), rep1, post-equil. Front-face
PIP-box pocket = residues 40-44, 117-135, 230-235, 251-253 (the pre-registration hypothesis).

**Heavy-atom RMSF (Å) — includes sidechains:** candidate windows **0.92–1.03**; front-face
pocket **1.44**; IDCL ref 118-122 **1.50**. Even with sidechains, candidates are rigid.

**Per-region SASA (Å², opening manifests as SASA fluctuation):**

| Region | SASA mean | SASA std | CV | range |
|---|---|---|---|---|
| front_face_pip_pocket | 2324 | 71 | 3.1% | 346 |
| cand 239-243 | 331 | 23 | 7.0% | 137 |
| cand 28-32 | 182 | 16 | 9.1% | 78 |
| cand 206-210 | 202 | 21 | 10.3% | 102 |
| cand 134-138 | 148 | 23 | 15.9% | 117 |
| ref 118-122 | 447 | 21 | 4.7% | 111 |

**Front-face pocket cross-wall Cα distances (Å, pocket "mouth"):** 44-251 = 9.4 ± 0.26
(range 1.4); 42-234 = 16.7 ± 0.33 (range 1.9); 128-252 = 12.1 ± 0.82 (range 4.1); 122-232 =
29.4 ± 1.07 (range 5.4).

## 6. Does the pocket have dynamics? (candidate reading — NOT an approved conclusion)

**Modest local flexibility, but no cryptic opening event observed in this window.**

- There **is** measurable motion: sidechain-level fluctuation (heavy-atom RMSF ~1–1.5 Å),
  mild pocket-surface breathing (front-face SASA range ~346 Å², CV ~3%), and some mouth
  breathing at 128-252 (~4 Å range).
- There is **no large-scale open↔close transition** and **no evidence the GNN-predicted
  candidate windows behave as dynamic cryptic pockets**: 239-243 / 28-32 / 206-210 are rigid
  (heavy RMSF ~1 Å, CV 7–10%, mouth distances stable to <1 Å).
- The **only genuinely flexible regions are the already-known IDCL** (118-122 ref and the
  134-138 IDCL-adjacent control) — i.e. expected, not novel.

## 7. Good or bad for the project — honest assessment

**Process / data quality: GOOD.** The simulation is valid and stable; a serious analysis
artifact was caught and corrected; the project now has defensible, reproducible exploratory
metrics instead of garbage numbers. Catching the PBC bug before it reached the paper is a win.

**Scientific signal for the thesis (GNN finds novel dynamic/cryptic PCNA sites):
WEAK / NON-SUPPORTIVE so far, but UNDERPOWERED → inconclusive, not falsifying.** Under this
tested setup the top GNN candidate windows did not open or behave as flexible cryptic pockets;
the dynamics live in the known IDCL. That is *not* what you'd hope to see if these windows were
novel breathing pockets. **But** 20 ns of usable sampling, n = 1, a single apo-from-p21
structure, and no 8GLA positive control mean cryptic-opening events (ns–µs timescale) may
simply be unsampled. Per doc 13 this is a valid negative/inconclusive result, **not** a
falsification of the candidates.

**Bottom line:** the honest paper-safe statement is *"under a short exploratory 1AXC apo
setup, the top candidate windows showed no cryptic-pocket opening; observed flexibility was
confined to the known IDCL; result is exploratory and underpowered."* Reporting MD as
**preliminary / deferred** remains fully defensible. Do **not** claim support for novel
druggable sites from this run.

## 8. Limitations

Short timescale (25 ns − 5 ns equil = 20 ns usable); n = 1 (rep2 incomplete, rep3 absent);
single structure; apo-from-p21 (relaxation from a peptide-bound state); no 8GLA positive
control; SASA / distance / Rg are pocket-opening **proxies**, not true pocket-volume
(no fpocket/MDpocket run); 3 monomers are not independent replicates.

## 9. Required human decision (doc 26 — first MD interpretation)

This packet is ready for human review. To proceed to any interpretation/paper use, record in
`reports/phase4/gate7_authorization_YYYYMMDD.md` + `reports/phase2/human_review_log.md`:
review decision ID, reviewer (Reshwant-Borra), date, evidence packet paths (this report +
`reports/phase5/md_reanalysis_1axc/`), decision (approve / approve-with-limitations / reject),
and limitations. **No agent may approve this gate.**

## 10. Reproduction

Env: fresh venv with `mdtraj numpy pandas matplotlib`. Trajectories preserved externally
(zip / RunPod package; `outputs/phase5_md/` is gitignored). Run:
`python scripts/phase5_analyze_1axc_md_fixed.py` then `python scripts/phase5_pocket_dynamics_1axc.py`.
