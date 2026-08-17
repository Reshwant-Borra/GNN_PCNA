# Independent Pre-Smoke Re-Audit — PCNA GNN → Frozen Pocket Handoff → MD

**Date:** 2026-08-16
**Commit audited:** `b4d9d7c331d39b4193cb4eaf3fdbacaca2954972` (branch `final-consolidation-audit`)
**Also covers `main` `d14f6e1`** — `git diff b4d9d7c d14f6e1` is empty; the trees are identical and only two merge commits differ.
**Method:** fresh clone at the exact commit, no access to ignored/untracked local files. Every finding below was produced by executing code, not by reading it.

---

## Verdict

### CONDITIONAL GO — READY FOR RTX 4070 SMOKE WITH NONBLOCKING ISSUES

Authorizes **only** `./md.sh smoke`. Does **not** authorize control5, benchmark, Gate-6, or production.

| | |
|---|---|
| Confirmed smoke blockers | **0** |
| Major issues before control5 / production | **9** |
| Prior audit findings fixed | **7** |
| Test suite | 113 passed · 3 failed · 4 skipped |

---

## 1. What the repair pass genuinely fixed

Each of these was re-tested by execution, not accepted from the repair report.

| Prior finding | Status | Evidence |
|---|---|---|
| **BLOCKER** — `gnn_pocket_search/run_all_in_tmux.sh` launched 3×100 ns control + 3×100 ns apo outside all gates | **FIXED** | Executed with and without arguments: prints `HISTORICAL_DISABLED`, exits 2, launches nothing. Whole-repo search found only 5 shell scripts; no other MD launcher exists. |
| Clean clone could not validate the 55-structure `data/graphs_xl` lineage | **FIXED** | Validation without retrieval fails closed (exit 1). `--retrieve-from-origin` pulls 55/55; every SHA-256 matches; aggregate hash `69744b54…` exact; splits 43/6/6; all node dims 520; 1630 positives. Recorded retrieval commit `d7cf76d` matches GitHub exactly. |
| `scripts/check_env.py` checked obsolete graph/checkpoint locations | **FIXED** | Now validates frozen checkpoints (3/3), checkpoint registry, frozen handoff, frozen MD protocol, canonical launcher, graph lineage, MD stack, tmux. |
| Convergence / time-block analysis missing | **FIXED** | Implemented and verified on 10/10 deterministic cases (below). |
| Replica aggregation incomplete | **FIXED** | Replicate is the independent unit; disagreement cannot hide in the mean (below). |
| Final analysis did not hard-fail on frame count | **FIXED** | 6/6 invalid completion cases now refused with exit 1 (below). |
| `--allow-incomplete` output unlabelled | **FIXED** | Aliased into the diagnostic path and marked `DIAGNOSTIC_ONLY - NOT_FOR_SCIENTIFIC_INTERPRETATION`. |

---

## 2. The frozen GNN hypothesis is intact

Nothing in the repair moved the science.

**Checkpoints** — all three SHA-256 exact, 53,485,974 bytes each:

```
seed 42  03d01eba42eb7f6da01c0147dea434b1e1797bd2302e8a178d6bbd9b19526ce5
seed 43  7f145d6f54d03744f71c0224df4f170ad4aab388387e242234ebffda1acae17b
seed 44  0a739dec47248651499942207b82139e5dea8bebfafe5ed50aabcbbdfd6aa3f6
```

**Architecture** — `PocketGNNXL`, `node_encoder.0.weight` = (384, 520), `load_state_dict(strict=True)` clean for all three, 13,364,354 params. Feature contract 40 graph + 480 ESM2-t12 = 520 confirmed at runtime.

**Inference rerun from the clean clone** — 510 rows per seed:

| Seed | Max abs Δscore | Mean abs Δ | Order mismatches | Candidate |
|---|---|---|---|---|
| 42 | 0.0 | 0.0 | 0 | exact — score CSV **byte-identical** |
| 43 | 0.0 | 0.0 | 0 | exact — score CSV **byte-identical** |
| 44 | 1.0e−4 | 1.96e−7 | 0 | exact |

The seed-44 difference is one residue, **A69 GLY 0.2168 vs 0.2167** — its raw score sits on the `%.4f` rounding midpoint, so a last-ulp CPU difference flips the printed digit. It scores 0.217 against a 0.4 clustering threshold and carries cluster label `−1` in both runs. Zero effect on the candidate.

**Consensus re-derived from my own regenerated scores** (not copied from any artifact) — every value exact:

```
Jaccard 42/43 = 0.7058823529411765     centroid 42/43 = 4.454146836872908 A
Jaccard 42/44 = 0.7                    centroid 42/44 = 1.393831349595412 A
Jaccard 43/44 = 0.631578947368421      centroid 43/44 = 5.091160048852773 A
mean          = 0.6791537667698658
3/3 core = 11   >=2/3 = 16   1/3 fringe = 4   union = 20
6 A near-overlap = 0.90625 / 1.0 / 0.8888888888888888
PRE-MD STABILITY: PASS
```

Extraction policy `independent_mcc_rank_fraction_size_weighted_cluster` is unmodified and still selected without PCNA (`selected_without_pcna: true`, five non-PCNA calibration structures).

**Structure preparation** reproduces exactly: both systems build 3-chain biological assemblies (hard-fail otherwise), 1W60 0 rebuilt residues, 8GLA 50; all 20 candidate residues resolve in both with the expected resnames; apo/control atom parity **280/280 = 100%**.

**MD parameters: 28 of 28 documented values match the code**, including seeding of the integrator, barostat *and* initial velocities.

---

## 3. Issues to resolve — none blocks smoke

Ordered by importance. Each states the stage it blocks.

### 3.1 The positive-control gate passes pure noise — **blocks control5 interpretation, Gate-6, production**

This is the one that matters scientifically.

`FROZEN_MD_ANALYSIS_PROTOCOL.json` states its own negative diagnostic:

> *"starting structures differ plus tiny random coordinate noise must fail because static separation alone is not dynamic validation"*

I built exactly that: three replicates of the **real prepared 8GLA homotrimer, completely static**, plus 0.10 Å i.i.d. Gaussian jitter. No motion, no dynamics, pure numerical noise. Run through the real analyzer and the real gate:

```
rep1: pocket_RMSF=0.01704 nm  open_like_fraction=1.0  SASA=843.6 A2  hull=609.9 A3
rep2: pocket_RMSF=0.01707 nm  open_like_fraction=1.0  SASA=843.0 A2  hull=610.1 A3
rep3: pocket_RMSF=0.01702 nm  open_like_fraction=1.0  SASA=843.9 A2  hull=611.9 A3

STATUS                        : PASS
qualifying control replicates : 3 / 3
issues                        : NONE
```

Mechanism, isolated by sweeping noise amplitude and starting structure:

| System | σ (Å) | RMSF (nm) | SASA (Å²) | Hull (Å³) | Open fraction | Gate |
|---|---|---|---|---|---|---|
| 8GLA | 0.02 | 0.00353 | 842.0 | 610.0 | 1.00 | FAIL |
| 8GLA | 0.10 | 0.01765 | 842.7 | 609.3 | 1.00 | **PASS** |
| 1W60 | 0.10 | 0.01728 | 789.8 | 513.0 | 0.00 | FAIL |

*(thresholds: SASA ≥ 808.568, hull ≥ 560.687, RMSF ≥ 0.015 nm)*

1. **The openness thresholds are the midpoints between static prepared 1W60 and static prepared 8GLA**, and the control system *is* 8GLA. Its static values sit above both midpoints by construction, so `open_like_fraction = 1.0` is granted by the starting coordinates before any physics runs. The 1W60 row proves it from the other side: identical noise, 0.00 open fraction. What separates them is which crystal structure you started from, not what happened during the trajectory.
2. **The only remaining discriminator is the RMSF floor of 0.015 nm** (0.15 Å), crossed by i.i.d. jitter somewhere between σ = 0.02 Å and σ = 0.10 Å — far below crystallographic coordinate error, let alone protein motion.

The gate correctly refuses frame-zero *differencing*, but it still inherits the static separation through absolute thresholds — the same circularity by another route.

**Why it does not block smoke:** smoke runs one replicate, the gate requires three, and `md.sh smoke` never consults it. **Why it must be fixed before control5:** if this gate reads PASS, an eventual apo negative is uninterpretable — the gate would have certified assay sensitivity it never demonstrated. That is exactly the false-negative failure the control-first design exists to prevent.

**Direction of a fix** (not implemented — this is an audit): require a discriminator noise cannot produce. Compare the control's open-like fraction against a *noise-only control built from the same starting structure*; or require a minimum count of qualifying opening/closing transitions; or require pocket RMSF to exceed that of a matched static-plus-noise reference rather than an absolute floor.

**Reproduce:** build three static 8GLA replicates with σ = 0.10 Å jitter, run `analyze_md.analyze_replicate` then `analyze_md.evaluate_control_interpretability`.

---

### 3.2 `gate6_approved()` accepts statements that withhold approval — **blocks production**

`md_workflow.py:137` lower-cases `research_os_memory/HUMAN_DECISIONS.md`, requires the substring `"gate 6"`/`"gate-6"` plus `"approved"`, and rejects only on `"not approved"`, `"not granted"`, `"required_before_md"`. Tested:

```
gate6_approved()=True   <- 'Gate 6: NOT YET APPROVED. Do not start production MD.'
gate6_approved()=True   <- 'Gate 6 is pending. Gate 5 was approved on 2026-08-01.'
gate6_approved()=True   <- 'GATE-6: approval WITHHELD pending control5. (Gate 4 approved.)'
gate6_approved()=False  <- 'Gate 6: NOT APPROVED'
gate6_approved()=True   <- 'Gate 6: approved by human reviewer.'
```

Three of four negative statements read as approval — "NOT YET APPROVED" evades the check because "yet" breaks the bigram. This is the single control the entire production architecture rests on, and it is a substring match over free prose. It should be a structured decision record: a dedicated JSON with an explicit boolean, an approver and a timestamp.

---

### 3.3 The smoke gate can never read PASS — **blocks progression to production**

`./md.sh smoke` runs 0.1 ns at 4 fs. `run_md.py` computes `production_ns = (final_step − equil_steps) × dt_ns` = `25000 × 4e-6`, which in IEEE-754 is exactly `0.09999999999999999`. Two readers compare without tolerance:

- `md_workflow.py:92` — `float(...) >= 0.1`
- `scripts/md_readiness_gate.py:112` — `float(...) < 0.1`

Four other comparisons in the same codebase already use `+1e-9`. Reproduced by writing the exact `DONE.json` a successful smoke produces:

```
$ ./md.sh status
gates:
  smoke_0p1ns: PENDING          <- after a fully successful smoke
runs:
  8GLA/rep01: COMPLETE step=525000 prod=0.100 ns   <- simultaneously reported complete

$ python scripts/md_readiness_gate.py
MD READINESS GATE: FAIL
- control smoke production_ns < 0.1
```

Fails in the safe direction (refuses rather than permits), so it is not a smoke blocker — but `md.sh`'s own post-smoke instruction is "Next after completion: `./md.sh status`", and that command will report the smoke gate as PENDING. Two-line fix.

---

### 3.4 Production-scale detection uses AND — **blocks production**

`run_md.py is_production_scale()` requires `replicates >= 3` **and** `ns >= 100`. Probed directly:

```
3 x 100 ns   -> production   gated=True     300 ns total
1 x 500 ns   -> diagnostic   gated=False    500 ns total
2 x 100 ns   -> diagnostic   gated=False    200 ns total
2 x 1000 ns  -> diagnostic   gated=False   2000 ns total
6 x 99 ns    -> diagnostic   gated=False    594 ns total
```

In fairness: this is documented as "defense in depth, not the primary gate", the primary control is that `md.sh` offers no such entry point, and exploiting it requires deliberately hand-writing an unsupported command line. But the stated goal — production-scale invocation fails closed — is not met in general. A total-nanosecond budget (`replicates × ns`) closes it.

The canonical path *is* solid: direct 3×100 ns is refused, a mislabeled `--md-stage smoke` is refused, and a forged authorization token is rejected on git-commit binding.

---

### 3.5 Local RMSD does not compute what it says it computes — **blocks final interpretation**

`summary.json["rmsd_protocol"]["local_region_rmsd"]` declares measurement of "region CA **after scaffold alignment**". `analyze_md.py:629` calls `md.rmsd(protein, protein, 0, atom_indices=region_ca)`, and mdtraj superposes on the atoms it is given — so the region is aligned to itself, discarding the prior scaffold superposition.

Demonstrated on the real prepared 1W60 assembly by rigidly displacing a 20-residue CA region 0.5 nm while holding the scaffold fixed:

```
md.rmsd(..., atom_indices=region)              = 0.000437 nm
manual: region RMSD after scaffold alignment   = 0.500000 nm
internal deformation (sd 0.05 nm)              = 0.088766 nm   <- correctly detected
```

The metric is **blind to rigid-body motion of the pocket relative to the core** — exactly the motion a lid or loop swinging open would produce. It feeds `convergence["local_rmsd_nm"]` and so affects reported per-region convergence status.

Scope note: the frozen protocol requires only "backbone/CA RMSD after PBC imaging and alignment; stability descriptor only". It does **not** mandate a separate local RMSD, so this is not "a required metric is missing" — it is that the artifact describes a metric it does not compute. Either the description or the computation should change.

Related: `analyze_md.kabsch_rmsd_nm` (line 486) is never called anywhere in that file — dead code — and `tests/test_rmsd_protocol.py` tests only that dead helper, so the production RMSD path has no test coverage. (`run_md.py`'s own `_kabsch_rmsd_nm` *is* used, for the post-run sanity gate.)

---

### 3.6 Equilibration is unobserved — **blocks control5 / production acceptance**

In `run_replicate`, `sim.step(equil_steps)` runs the full 2 ns equilibration *before* any reporter is attached; the checkpoint, DCD and StateData reporters are appended afterwards. No temperature, pressure, density, potential-energy or box-vector series exists for the equilibration window.

`EQUILIBRATION_ACCEPTANCE_CRITERIA.json` specifies criteria that need exactly that data — "no sustained drift > 15 K after the first 20 percent", "no monotonic runaway over the final half", a final density range, "no abrupt discontinuity" in box vectors. **None can currently be evaluated.** Pressure is not logged at all, in any stage.

Also note the equilibration call sits outside the try/except that wraps production, so an exception there propagates as an uncaught traceback with no `FAILED.json`. A silent NaN blow-up would still be caught at the end by the finiteness gate.

---

### 3.7 Retraining is not reproducible from a clean clone — **blocks end-to-end reproducibility claims**

`checkpoints/pcna/best_pcna_v3.ckpt` — the pretrain base that `finetune_v3_fixed.py` fine-tunes from — is absent, has no retrieval location in `REPRODUCIBILITY_MANIFEST.json` (unlike the seed-42 clean-split checkpoint, which does), and its recorded provenance path is a personal machine. It causes both real test failures.

Be precise about what this does and does not undermine:

- **Handoff reproducibility is closed.** The three fine-tuned checkpoints are tracked, hash-verified, and reproduce the pocket exactly. That is what MD consumes.
- **Training reproducibility is not closed.** Nobody can rebuild those checkpoints from source.

Papers and competition submissions should state that distinction rather than claim end-to-end reproducibility.

---

### 3.8 Ghost paths in active code and setup docs — **blocks clean-clone reproduction of the GNN side**

- `data/splits/cryptosite_split.json` is referenced by five non-archive files — `scripts/homology_check.py`, `scripts/compute_validation_metrics.py`, `scripts/run_test_eval.py`, `src/training/dataset.py`, `src/training/train.py` — and **does not exist**. Only `cryptosite_homology30_split.json` is present. `homology_check.py` crashes with an unhandled `FileNotFoundError` at import.
- `SETUP.md` Step 9 instructs `python scripts/run_nma.py …` with expected results (apo 0.857, holo 1.157). That script does not exist anywhere in the repository.
- The `SETUP.md` Checkpoints table lists three paths absent from a clean clone and marks `checkpoints/pcna_reproduced/best.ckpt` **"Recommended"**, while omitting the checkpoints that *are* tracked (`artifacts/go_prep/seed_{42,43,44}/best.ckpt`). A new collaborator following SETUP.md is pointed away from the only working artifacts.

---

### 3.9 Housekeeping

- **No `.gitattributes`.** On any Windows clone with `core.autocrlf=true`, every documented SHA-256 mismatches and `protocol_ok()` fails — including the frozen protocol, which reads `a743140…` instead of `587f27cf…`. It fails closed, so it is safe, but it will read as catastrophic to the next person who clones on Windows. `* text=auto eol=lf` settles it permanently. (Windows `MAX_PATH` separately drops ~60 `archive/` files unless `core.longpaths=true`.)
- **A frozen artifact was hand-edited after generation.** Re-running `apply-1w60` reproduces the tracked handoff on every field except `gate6_human_approval`: the code writes `"REQUIRED_BEFORE_MD"`, the tracked artifact says `"REQUIRED_BEFORE_PRODUCTION_MD"`. The tracked wording is the semantically correct one for the current staged workflow — the generator should be updated to match so the artifact is byte-regenerable.
- **Two `smoke_safety_checks` fields are constants, not measurements.** `catastrophic_bond_or_geometry_failure` is the literal `False`; `candidate_region_mapping_integrity` is a fixed string. Both are true by construction, but they read as verified checks inside a self-describing safety block.
- **Silent-failure paths.** If `scipy` were unavailable, `convex_hull_volume_A3` returns NaN for every frame and the openness mask silently becomes all-False — `open_like_fraction` reads 0.0 with `available: True` and no stated reason. (`environment.yml` pins scipy, but `md.sh require_deps` does not check it.) An unreadable `production.log` makes `_parse_log_times` return `[]`, silently skipping the duplicate-time and output-interval completion checks.

---

### 3.10 Outside the MD path, but act on it — a live credential is committed

`start_gateway.sh` contains a hard-coded Telegram bot token in plaintext, and then runs an unattended loop that polls `git fetch origin agents` every 30 seconds and automatically pulls and restarts on any new commit — so write access to that branch is code execution on the host.

Nothing to do with MD and not a smoke blocker, but **the token should be revoked and rotated**, and treated as compromised regardless of repository visibility: it is in git history and deleting the line does not remove it. The auto-pull loop deserves a separate look.

---

## 4. Verified correct by deterministic test

These were checked by reconstructing the mathematics against known answers, not by trusting function names.

**Kabsch RMSD** — identical sets 6.4e−16; pure translation 1.5e−15; 40° rotation 7.4e−16; rotation+translation 1.9e−15; reflection correctly *not* fitted (1.828); two atoms 0.4 nm apart after fit → exactly 0.200000.

**DCCM** — over 4000 frames with constructed correlations: C(0,1) = +1.0000, C(0,2) = −1.0000, C(0,3) = +0.0096, diagonal all 1, symmetric, and unchanged when one atom's amplitude is scaled ×17 (correctly normalised).

**Convex hull, including units** — 1 nm cube → 1000.0000 Å³; 0.5 nm cube → 125.0000 Å³; unit tetrahedron → 166.6667 Å³; degenerate inputs → NaN.

**Convergence** — 5/5 stationary → `STABLE_BLOCKS`; 5/5 drifting → `DRIFTING_BLOCKS`; noiseless ramp, mid-run step change caught; constant stable; NaNs filtered; short series → `INSUFFICIENT_DATA`. A +5 drift under sd-20 noise reads STABLE, which is correct behaviour for a 0.5×sd criterion, not a miss.

**Replica aggregation** — with a deliberately contradictory control set (0.95 / 0.05 / 0.50, one diagnostic-only, one apo replicate missing the metric):

```
independent_unit           : replicate
per_replicate values       : [0.95, 0.05, 0.5]
mean 0.5000  sd 0.4500  range [0.05, 0.95]  95%CI [-0.0092, 1.0092]
failed_or_incomplete_count : 1
apo (metric missing)       : support 1/2, mean 0.1   <- missing value did not corrupt the mean
```

Disagreement cannot be hidden by averaging.

**Opening-event rule** — ≥2 consecutive frames enforced exactly; isolated single frames excluded; trailing runs correctly closed.

**Openness thresholds** — recomputed from `static_reference_analysis.json`: core (471.714+530.919)/2 = 501.317; supported SASA (778.027+839.109)/2 = 808.568; supported hull (511.12+610.253)/2 = 560.687. All exact.

**Cross-tool SASA comparability** — the static references use Biopython ShrakeRupley, trajectory analysis uses mdtraj. On the same prepared 8GLA assembly: 843.6 Å² vs the recorded 839.109 Å², 0.5% agreement. Checked and **not** a finding.

**Completion enforcement** — all six invalid cases refused with exit 1 through the real CLI: missing `DONE.json`; truncated trajectory; `FAILED.json` present; duplicate frames; inconsistent output interval; duplicate log times. Diagnostic override is permitted only under an explicit flag and is marked `DIAGNOSTIC_ONLY - NOT_FOR_SCIENTIFIC_INTERPRETATION` at both summary and replicate level, with the control gate still reading FAIL. Diagnostic output cannot satisfy a scientific gate.

---

## 5. Production entry points — complete inventory

| Path | Classification | Verified behaviour |
|---|---|---|
| `md.sh` | CANONICAL_GATED | Only launcher. Production path calls the gate first under `set -euo pipefail`. |
| `md_validation_4070/run_md.py` | CANONICAL_GATED | Production-scale invocation refuses without valid authorization. |
| `md_validation_4070/run_in_tmux.sh` | DEPRECATED (delegating) | Prints notice, then `exec "$ROOT/md.sh" "$@"`. No args → exit 2. Inherits all gating. |
| `…/gnn_pocket_search/run_all_in_tmux.sh` | HISTORICAL_DISABLED | Exit 2 with and without args; launches nothing. |
| `…/gnn_pocket_search/run_pocket_search.sh` | DIAGNOSTIC_NONPRODUCTION | GNN inference + gate-enforced handoff export. No MD invocation. |
| `agents/orchestrator.py` | NON-MD | Grep for `md.sh` / `run_md` across `agents/` returns nothing. |

`./md.sh production` fails closed:

```
$ ./md.sh production
PRODUCTION BLOCKED: Gate-6 human approval required.
EXIT=1
```

No approval was created during this audit. `docs/CANONICAL_PIPELINE.md`'s launcher classification table matches this inventory item for item.

---

## 6. Test suite

**3 failed · 113 passed · 4 skipped** (`python -m pytest tests/ -q`, 43 s).

| Failed test | Root cause | Assessment |
|---|---|---|
| `test_checkpoint_loading.py::test_v3_checkpoint_loads` | `checkpoints/pcna/best_pcna_v3.ckpt` absent | Real — see §3.7 |
| `test_pre_md_release_gate.py::test_two_seeded_retrains_are_bitwise_identical` | Same missing pretrain checkpoint | Real — same root cause |
| `test_scientific_guardrails.py::test_documented_choice_is_not_bug…` | `context_provenance.py:355` tests `"decisions/" in h` while `hits` holds `str(p.relative_to(root))` — backslashes on Windows | **Windows-only**; passes on Linux |

The four skips are honest — two historical optional checkpoints, one historical script explicitly outside the canonical MD path, one "no checkpoint to test against".

The suite grew from 95 to 113 passing tests in this repair pass, and the added suites (production bypass regression, MD analysis enforcement, graph lineage manifest, August GNN provenance regression) cover exactly the areas the previous audit flagged. Two of them genuinely lock in fixes I re-verified independently.

---

## 7. Recommended order of work

1. **Run `./md.sh smoke`** on the 4070 box. Needs tmux and a working OpenMM CUDA platform; the launcher refuses without both.
2. **Expect `./md.sh status` to report `smoke_0p1ns: PENDING`** even on success (§3.3). Read `outputs/8GLA/rep01/DONE.json` directly, or fix the two comparisons first.
3. **Inspect the smoke artifacts before control5** — `MINIMIZATION.json` (8GLA's pre-minimization potential energy is genuinely enormous: 2.8×10¹³ → −2.62×10⁶ kJ/mol in preflight, max force 6.9×10¹⁵ → 2749; confirm it resolves the same way), `prep_audit.json` (3 chains, 50 rebuilt residues, Cys135–Cys162 disulfides), the backbone RMSD in `DONE.json`, and the temperature/density columns in `production.log`.
4. **Fix §3.1 before control5.** A control gate that passes static noise cannot certify assay sensitivity, and every downstream interpretation of an apo negative depends on it.
5. **Fix §3.2 before Gate-6.**
6. **Revoke the Telegram token (§3.10)** independently of everything else.

---

## 8. Scope note on what the MD tests

Worth stating plainly in any write-up, because a reviewer will find it quickly.

The fine-tune target is a hard-coded residue-number set (`scripts/finetune_v3_fixed.py:55`):

```python
AOH_GT = {25,26,27,38,39,40,41,42,44,45,46,47,
          123,125,126,128,231,232,233,234,250,251,252,253}
```

with `labels[i] = 1.0 if r.resid in AOH_GT else 0.0` on 8GLA chain A, and the same residue numbers labeled `0.0` on apo 1W60. The frozen MD pocket is **15 of those 16** (only S43 is outside `AOH_GT`; the IDCL cluster 123/125/126/128 and 231/250–253 are dropped). Checkpoint selection used chain-B AUROC on 8GLA — a homotrimer copy of the training chain with identical labels — and `fp_apo_pct` (100% / 91.7% / 22.9% for seeds 42/43/44) was recorded but not selection-limiting.

The repository already documents this correctly: `LIMITATIONS.md §4.1` calls the AOH gate a sanity check and "not an independent performance metric" (LEAK verdict in `VERIFICATION_REPORT.md`); `GO_CHECKLIST.md:119` records the deliberate decision to "accept a *known* site (AOH1996) as the MD target and report the novel-pocket arm as not yet supported"; `GNN_PCNA_Failure_Assessment_2026-07.md §9` permits only "clean recovery of the known AOH1996 site".

So the MD question is **not** "where is the pocket" but **"is this known drug site cryptic in the apo state?"** — a legitimate, unanswered dynamics question about a clinical-stage target, and the right use of MD. Two cautions:

- The pocket JSON's `apo_role` calls this "the independently predicted candidate region". The *extraction policy* was independent of PCNA (verified — genuine anti-circularity). The *scores* were not. Qualify that phrase or drop it.
- The AOH overlap is documented in `GO_CHECKLIST` / `LIMITATIONS` / the failure assessment, but **not** in `pockets/final_consensus_1w60_20260815.json` or the frozen protocol — the artifacts a reader of the MD results actually opens. One sentence in the pocket description closes the gap.

The cross-family benchmark (AUPRC 0.2513 / AUROC 0.8649 on the homology-clean 30% split, 3 seeds, with the ablation ladder 0.1071 → 0.1923 → 0.2513) is a methods result on held-out non-PCNA structures and is **not** circular. It stands on its own.

---

## 9. Environment used

Clean clone on Windows 11, Python 3.12.8, torch 2.10.0+cpu, OpenMM 8.5.1, mdtraj 1.11.1, gemmi 0.7.5, scipy 1.17.1, Biopython 1.87.

The repository was not modified during the audit: `git status --porcelain` reported zero tracked-file changes on completion. No production MD was run, no model was retrained, and no gate approval was created.
