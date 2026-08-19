# Control-20 Forensic Methodology Audit

Audited: 2026-08-19. Auditor: Claude (forensic/methodology audit role), acting on
`C:\Users\reshw\Desktop\GNN_PCNA_FINAL`, branch `audit/control20-forensic-methodology`
(branched from `control20-extension`, commits `cb65934`, `03b6eb2`, `f1b4838`).
Cross-referenced against the sibling clone `C:\Users\reshw\Desktop\GNN_PCNA` (branch `main`,
no Control-20 data present there).

No trajectories, DONE.json files, DCDs, or historical reports were altered, deleted, or
regenerated. No MD was run. No thresholds, residue definitions, or gate logic were changed.
Three narrowly-scoped software/reporting patches were applied and are documented in full in
§18-19 and §26.

---

## 1. Executive Verdict

**MIXED_FINDINGS_REQUIRE_NEW_PROSPECTIVE_PROTOCOL**

The frozen Control-20 gate result is **FAIL** and is **accepted as-is**. It is not overturned,
reinterpreted, or worked around anywhere in this audit. `qualifying_control_replicates = 2`,
the frozen requirement is `3`, and per the prospective amendment no further extension of *this*
experiment is permitted regardless of this audit's findings.

The "mixed" classification reflects three independent, non-outcome-dependent findings that
survive scrutiny at the same strength they would have if rep02 had scored 0.25 instead of 0.13
(see the outcome-dependence certification in §24):

1. **All three replicates**, including the two that qualify, show **persistent block-to-block
   drift (`DRIFTING_BLOCKS`)** in RMSD, SASA, and CA-hull volume across essentially every region,
   for the entire 15 ns analyzed window (5-20 ns). This is evidence the system may not have
   reached a stationary sampling regime at this timescale — a **sampling limitation**, not
   necessarily a stable biological negative.
2. Three of the gate's five numeric floors (`minimum_open_like_fraction = 0.20`,
   `minimum_pocket_rmsf_nm = 0.015`, and the three absolute A²/Å³ openness thresholds) are
   **prospectively frozen but not accompanied by an analytic or literature-derived
   justification**, unlike D1/D2, which are. This is a **design weakness**, not a **design
   invalidity** — nothing here shows the gate is incoherent or wrong, only under-justified in
   this specific corner.
3. No implementation bug was found that touches the Control-5/Control-20 data actually
   analyzed. One serious, now-fixed prep bug (§13) predates this data and is confirmed absent
   from it.

None of these three findings license treating Control-20 as a PASS, as inconclusive-therefore-
ignorable, or as evidence the gate should be redesigned retroactively. They jointly support
recommending a **new, independently justified, prospectively frozen follow-up protocol** (§27)
rather than either accepting this result as a final biological negative or attempting to rescue
it.

---

## 2. Immutable Observed Results

**Control-5** (3 x 5 ns, `outputs_control5_5ns_FAIL_2of3_20260817_163213/`, preserved verbatim):
FAIL, 2/3 qualifying (`rep02` disqualified solely on open-like fraction).

**Control-20** (3 x 20 ns total, same three replicates continued from their Control-5
checkpoints, `outputs_control5/`): **FAIL, 2/3 qualifying.** Confirmed directly from
`md_validation_4070/outputs_control5/analysis/summary.json`:

| Replicate | n_frames | equil discarded | qualifies | open_like_fraction | D1 (thr 0.1732) | D2 (thr 0.1382) | Only failure |
|---|---|---|---|---|---|---|---|
| rep01 | 400 (20.0 ns) | 100 (5.0 ns) | **true** | 0.4067 | 0.6226 | 0.5128 | — |
| rep02 | 400 (20.0 ns) | 100 (5.0 ns) | **false** | 0.1300 | 0.3950 | 0.5384 | open-like fraction 0.130 < 0.200 |
| rep03 | 400 (20.0 ns) | 100 (5.0 ns) | **true** | 0.2767 | 0.5205 | 0.4839 | — |

`qualifying_control_replicates = 2`, required = 3. `control_interpretability_gate.status =
"FAIL"`. `CONTROL_INTERPRETABILITY_REPORT.md`: `CONTROL INTERPRETABLE: FAIL`. Gate 6:
**not approved** (no `GATE6_DECISION.json` exists in `md_validation_4070/`). Production:
**not authorized** (verified — §19).

Every number in the audit brief that was checked against the live `summary.json` (thresholds,
per-replicate D1/D2/openness, rebuilt-residue counts, chain sizes, equilibration discard) matched
exactly. No discrepancy between the reported evidence and the repository's actual state was
found.

---

## 3. Trajectory Integrity

All three replicates: `n_frames: 400`, `frame_count_status: "ok"`, `duplicate_log_times: false`,
`pbc_artifact_suspected: false`, `completion_status: "PASS"`, `completion_issues: []`.
`pbc_artifact_suspected_any: false`, `duplicate_frame_count_risk_any: false` at the summary
level. `production_log_status: "ok"` for all three. This is **Level 1 (technically valid
trajectories)** in the claim hierarchy (§28) and is fully supported.

Control-20 genuinely continued the Control-5 checkpoints in place: `outputs_control5/8GLA/rep0N/`
contains `state.prev.chk` alongside `state.chk`, `RESUME_AUDIT.json`, and a `DONE.stale.*.json`
per replicate (the Control-5-era `DONE.json`, superseded and preserved, not deleted, when
Control-20 finished). No `equilibration.log`/`MINIMIZATION.json` timestamp indicates a fresh
minimization or re-equilibration; the extension resumed from the existing checkpoint per the
amendment's requirement. The one production-affecting bug found in the prep pipeline (§13) is
confirmed, via `prep_audit.json`, to have been fixed *before* Control-5 ran, so both Control-5
and Control-20 share one unbroken, already-repaired system build — there is no discontinuity
between the two stages beyond the intended checkpoint continuation.

---

## 4. 0.20 Threshold Provenance

`CONTROL_MIN_OPEN_LIKE_FRACTION = 0.20` was introduced in commit `0fedaa3` ("Reconcile PCNA
reproducibility gates"), authored 2026-08-15 23:31:59 -0400 (2026-08-16 03:31 UTC). Control-5's
three replicates completed between 2026-08-17T21:06Z and 2026-08-18T01:32Z (per their
`DONE.stale.*.json` timestamps). **The threshold was frozen roughly two days before any
Control-5 data existed — genuinely prospective**, matching `FROZEN_MD_ANALYSIS_PROTOCOL.json`'s
`"frozen_before_meaningful_control_md": true` and `"frozen_utc": "2026-08-16T00:00:00+00:00"`.

**Prospectively defined: YES. Scientifically justified: PARTIALLY, and only by adjacency.**
The commit that introduces `0.20` (`md_validation_4070/analyze_md.py` diff in `0fedaa3`)
contains no comment, docstring, or citation explaining why 0.20 rather than 0.10, 0.15, or 0.30.
`FROZEN_MD_ANALYSIS_PROTOCOL.json`'s `dynamic_discriminators.threshold_derivation` field
explicitly states its derivation applies to **D1 and D2 only** ("Both thresholds are computed
from the ANALYTIC null distribution... they are not derived from... any control-5 or production
MD outcome"); no equivalent `threshold_derivation` entry exists for
`minimum_open_like_fraction` or `minimum_pocket_rmsf_nm`. Both read as round-number engineering
heuristics, not as values derived from a null distribution, a power calculation, a literature
precedent for PCNA/IDCL opening frequency, or an independent pilot dataset. This is a real gap:
0.20 is not scientifically indefensible, but the repository does not currently substantiate it
beyond "it is a round number chosen before we looked," which is a *provenance* virtue and a
*justification* gap simultaneously.

---

## 5. Absolute Openness Threshold Provenance

`core_sasa_A2 = 501.317`, `supported_sasa_A2 = 808.568`, `supported_ca_convex_hull_volume_A3 =
560.687` (`FROZEN_MD_ANALYSIS_PROTOCOL.json:210-213`, matching `outputs_control5/analysis/
summary.json:1886-1890` exactly). Introduced alongside the `0.20` floor in commit `0fedaa3`
(2026-08-15), also prospective.

`thresholds_source`: **"prepared 1W60 and ligand-stripped prepared 8GLA static references
before candidate production"** (`FROZEN_MD_ANALYSIS_PROTOCOL.json:208`). This is the important
caveat: these are **midpoints between exactly two single static structures** (one apo/closed
reference, one AOH1996-derivative-bound/open reference) — an n=1-per-class geometric threshold,
not a distribution-derived or ensemble-derived cutoff. `FROZEN_MD_ANALYSIS_PROTOCOL.json:217`
self-discloses this: `"status": "adopted as a geometric descriptor, not a ligand-volume
estimate; validated only as static reference discriminator before production"`. The commit
message for the gate v1→v2 supersession (`analyze_md.py:568-576`,
`FROZEN_MD_ANALYSIS_PROTOCOL.json:232`) independently confirms the *static* 8GLA reference sits
at SASA 839.109 Ų and hull 610.253 Å³ — both comfortably above these midpoints — which is why a
motionless 8GLA structure alone would trivially "pass" openness (this is precisely the loophole
v2's D1/D2 discriminators were built to close).

No MD outcome was used to set these numbers (both were fixed before Control-5 ran), so there is
no leakage/circularity risk from Control-5 or Control-20 data. The genuine limitation is
statistical thinness (n=1 per anchor), not data leakage or after-the-fact tuning. Units, chain
selection (chain index 0 = prepared chain A, matching `pcna_chain_residue_mapping.json` and the
`interface_chain_indices` convention used throughout `analyze_md.py`), and atom selections
(SASA over `supported_ge2of3` region residues, Shrake-Rupley, protein-context, atom-key parity
enforced — `FROZEN_MD_ANALYSIS_PROTOCOL.json:195-213`) all check out as internally consistent
with the summary output. Precision (three decimal places) is cosmetic, not a claim of accuracy
beyond what a single static structure's SASA/hull calculation can support — this is a minor,
harmless overprecision, not a defect.

---

## 6. D1 Mathematical Audit

**D1**: lag-1 Pearson autocorrelation `r1` of the supported-region CA convex-hull-volume time
series (`analyze_md.py:600-611`), rejection threshold `r1 >= 3.0 / sqrt(N)`
(`analyze_md.py:614-618`).

**Derivation.** For a stationary white-noise (IID) series of length N, the lag-1 sample
autocorrelation has an asymptotic standard error of approximately `1/sqrt(N)` (a standard
result — Bartlett's formula for the autocorrelation of white noise) and a small negative bias
(mean ≈ `-1/N`), which the code's own comment states correctly (`analyze_md.py:585`). A
threshold of `k_sigma / sqrt(N)` with `k_sigma = 3.0` is therefore an approximate **one-sided,
~3-sigma rejection of the null "these frames are independent."** This is mathematically sound
as an approximate large-N Gaussian test; with N=300 production frames it is a reasonable
regime for the normal approximation to hold.

**Is using N = 300 (the actual analyzed frame count) pseudoreplication?** No. The null
hypothesis being tested is *literally* "these N frames are IID" — using the true frame count N
in a test of exactly that null is correct by construction, not an inflation of an independent
sample size for inference about a different quantity. This is a different situation from
computing a frame-pooled confidence interval on a physical quantity (which *would* be
pseudoreplication, and which this codebase correctly avoids — see §9).

**Verdict: mathematically valid**, for the specific, narrow claim it is used to support
("this trajectory is distinguishable from IID per-frame coordinate noise"). It does not claim
convergence, does not claim biological significance, and does not claim reproducibility across
replicates — those are separately gated (open-like fraction, RMSF floor, 3/3 replicate count).

---

## 7. D2 Mathematical Audit

**D2**: mean |DCCM| (dynamic cross-correlation) among supported-region CA atoms
(`analyze_md.py:621-625`), rejection threshold `mean|c| >= 3.0 * sqrt(2/pi) / sqrt(N)`.

**Derivation.** For IID per-frame noise, each pairwise correlation coefficient `c_ij` is
approximately `N(0, 1/N)` for large N (again the standard asymptotic result for the sampling
distribution of a Pearson correlation under independence). The expected absolute value of a
zero-mean Gaussian with variance `1/N` is `sqrt(2/(pi*N))` (the half-normal mean,
`analyze_md.py:597`: `_HALF_NORMAL_MEAN = sqrt(2/pi)`). A threshold of `k_sigma` times that
expectation is a reasonable, if slightly informal (it thresholds a multiple of the null mean
rather than a mean-plus-k-SD interval), one-sided rejection of the same IID null, now on a
spatial-collectivity statistic. It correctly identifies that independent per-atom noise
produces *no* systematic |DCCM| elevation (mean tends to the null floor as N grows), while
genuine collective motion of a contiguous backbone region does not vanish with N. The empirical
static-noise surrogate reported alongside D2 in every row (`region_internal_mean_abs_dccm ≈
0.026` for all three replicates' surrogates) is close to the analytic null floor at N=300
(`sqrt(2/pi)/sqrt(300) ≈ 0.046`, same order of magnitude, difference attributable to the
surrogate being a finite Monte Carlo draw rather than the asymptotic expectation) — a useful
internal consistency check that the analytic approximation is behaving as intended.

**Verdict: mathematically valid** for the same narrow claim as D1. Using `k_sigma x E[|c|]`
rather than `E[|c|] + k_sigma x SD[|c|]` is a simplification (the two are close for a half-normal
at these values, but not identical); this does not change the qualitative conclusion for any of
the three replicates, whose observed |DCCM| (0.48-0.54) exceeds the threshold (0.138) by a
factor of 3.5-3.9x — far outside the margin any correction to the threshold's exact form could
plausibly close.

---

## 8. Null-Model Audit

The static-noise surrogate (`analyze_md.py:628-661`) draws IID per-frame Gaussian coordinate
noise around each replicate's own frame-0 region coordinates, with per-axis sigma set to
reproduce that replicate's *own* observed RMSF (`sigma = rmsf/sqrt(3)`). This is reported
alongside D1/D2 as diagnostic context, and is explicitly **not** what gates the decision — the
gate uses the analytic IID-null thresholds (§6-7), which do not depend on any drawn sample. This
separation is correct and matters: the surrogate could not leak into or bias the gate outcome
even in principle, since the gate's numeric threshold is a closed-form function of N alone.

Is the null "too weak," making D1/D2 "nearly guaranteed to favor real MD"? For a slow collective
coordinate like CA-hull volume sampled every 50 ps, yes — genuine MD trajectories are expected
to be strongly autocorrelated at that cadence almost by construction, so D1/D2 are not a
stringent test of "is this good MD," only of "is this distinguishable from a static crystal
structure plus white noise." That is exactly the narrow claim the protocol documents it as
testing (`FROZEN_MD_ANALYSIS_PROTOCOL.json:257`, `"negative_diagnostic"`), and the three
existing regression tests (`tests/test_control_gate_static_noise.py`) pin precisely that
narrow claim, not a broader one. No overstatement of what D1/D2 support was found in the code;
the overstatement problem is confined to the top-level `reason` string (§18), now fixed.

---

## 9. Replicate-Level Statistical Audit

Replicate, not frame, is correctly used as the independent unit throughout. `aggregate_replicates
()` (`analyze_md.py:510-`) explicitly groups by role and computes mean/SD/CI/range across the
**replicate-level** values only (`"independent_unit": "replicate"` is stamped into every
aggregate block), never across the 300 analyzed frames within a replicate. `summary.json`
confirms this for every reported aggregate (`replicate_count: 3`, `per_replicate:` listing
exactly 3 values). No instance of frame-level pooling masquerading as a larger sample size (i.e.
no false "n=900") was found anywhere in `analyze_md.py` or the emitted `summary.json`.

**One real statistical bug was found and fixed (see §18/§26 for the patch):** the aggregate 95%
CI used `1.96 * sd / sqrt(n)` (`analyze_md.py:532`, pre-patch) — the large-sample normal
approximation — for as few as **n=3 replicates**. For n=3 (df=2), the correct two-sided 95%
Student's-t critical value is **4.303**, not 1.96; the code was silently reporting an interval
close to a ~68-75% confidence level while labeling it "approx_95ci." This never affected the
gate's PASS/FAIL decision (the gate uses only per-replicate qualification counts, never this
aggregate CI), but it did understate the honest uncertainty of every descriptive replicate-level
aggregate in the summary (open-like fraction, RMSF, SASA, etc.) for both Control-5 and
Control-20. Fixed to use the correct t-critical value (§18); the fix widens every reported CI,
which is the opposite of outcome-shopping.

---

## 10. Convergence Audit

`assess_convergence()` (`analyze_md.py:482-507`): splits the analyzed series into 3 blocks,
compares only the **first vs. last** block mean, against a threshold of `0.5 x pooled_sd` of the
*entire* series (not per-block). This is a **heuristic diagnostic, not a validated statistical
convergence test** (it is not a Geweke diagnostic, block-standard-error test with
autocorrelation-corrected variance, or Gelman-Rubin-style multi-chain statistic). Because
`pooled_sd` is computed over the whole (possibly drifting) series, a real drift inflates the very
threshold used to judge that drift — a self-referential leniency. Despite that generosity,
**every region, every metric, every replicate reports `overall_status: "DRIFTING_BLOCKS"`**,
with `monotonic_block_means: true` in the majority of cases for RMSD, SASA, and hull volume in
the `core_3of3` and `supported_ge2of3` regions across all three replicates. This is not
borderline: the first-to-last block shift exceeds the generous threshold consistently and in a
directionally consistent (monotonic) way, which is the signature of genuine ongoing relaxation
rather than noise that happens to drift once.

**This is currently correctly treated as informational only** — `evaluate_control_interpretability
()` never reads `convergence` and it does not gate PASS/FAIL. That is the right design choice
today (a heuristic should not silently become a hard gate), and this audit does not recommend
changing that for the *current* frozen experiment. But the evidentiary meaning of the observation
should not be minimized either: **persistent, monotonic drift through the full 15 ns analyzed
window, in both qualifying and non-qualifying replicates alike, is evidence the system has not
reached a stationary sampling regime at 20 ns total.** Classification: **SAMPLING LIMITATION**,
supported independently of the specific open-like-fraction numbers (§24).

---

## 11. Equilibration Audit

`EQUIL_NS = 5.0` (`analyze_md.py:31`) was introduced 2026-07-17 (commit `48371e9`), over three
weeks before any Control-5 data existed — prospectively fixed, but, like the 0.20 floor, with no
inline derivation from this system's actual relaxation diagnostics (temperature/pressure/density
stabilization is governed by the separate `EQUILIBRATION_ACCEPTANCE_CRITERIA.json`, which gates
the *pre-production* NVT/NPT phase, not the choice of how much of *production* to discard as
burn-in). The 5 ns production discard is a round-number convention, applied uniformly and
correctly to both Control-5 and Control-20 (confirmed: `equil_frames: 100` at `dt_ns: 0.05` in
every replicate's `summary.json` entry, i.e. exactly 5.0 ns discarded from all three 20 ns
trajectories, leaving the reported 300 frames / 15 ns).

The convergence evidence in §10 directly bears on whether 5 ns was adequate: if it were, the
*post-discard* window would be expected to show substantially less directional drift than it
does. Instead, drift persists (and is frequently monotonic) through the entire remaining 15 ns.
This does not mean 5 ns was an unreasonable a priori choice — it means the data now available
suggests it was **not sufficient for this specific system**, which is a legitimate finding to
report, not a license to retroactively change the discard window and reanalyze (which this audit
explicitly did not do — the discard window used throughout this report is the frozen 5.0 ns,
unchanged).

---

## 12. 8GLA Structural Suitability

8GLA is `RCSB 8GLA — "Co-crystal structure of caPCNA bound to the AOH1996 derivative,
AOH1996-1LE"`, X-ray, 3.77 Å, R-work 0.2051, R-free 0.26 (`MD_STRUCTURE_VALIDATION.json:112-118`;
confirmed against the live RCSB record, see Sources). AOH1996 is a published, rationally
designed small-molecule PCNA inhibitor (Gu lab, *Cell Chemical Biology* 2023, PMC10592352) that
disrupts PCNA-RPB1/chromatin interactions and induces transcription-dependent DNA double-strand
breaks — a genuine, independently characterized PCNA-targeting ligand, not an arbitrary or
fabricated reference. This is a legitimate structural basis for a positive control.

3.77 Å is a modest-resolution structure (R-free 0.26 is on the higher, less-precise end for a
structure at this resolution) with 4 deposited polymer instances and 92 unmodeled polymer
monomers (`MD_STRUCTURE_VALIDATION.json:119-120`). Combined with the 50 internally rebuilt
residues (§13), overall model precision — especially side-chain geometry in regions that
*were* rebuilt — is modest. The specific pocket region analyzed is not among those regions
(§13), which materially limits, but does not eliminate, this concern: the surrounding fold and
crystallographic B-factors at 3.77 Å are still lower-confidence than a higher-resolution
structure would provide, and this affects the credibility of the *absolute* SASA/hull reference
values derived from this single structure (§5) more than it affects the *trajectory-derived*
D1/D2 discriminators, which depend on relative motion rather than absolute starting geometry.

---

## 13. Structural Preparation / Rebuilt Residues

`prep_audit.json` for the trajectories actually analyzed
(`outputs_control5/8GLA/prep/prep_audit.json`): assembly `1`, chains A/B/C = 253/253/254
residues, **50 internal residues rebuilt by PDBFixer**, explicitly flagged: *"if this is large
and the structure is low-resolution (e.g. 8GLA 3.77 A), treat pocket side-chain geometry as
modeled, not observed."*

**Critical check — do the rebuilt residues overlap the analyzed pocket?** No, for all three
chains. `MD_STRUCTURE_VALIDATION.json:131-331` records, per chain, the deposited structure's
`internal_gaps` (chain A: residues 93-97, 105-110, 164-167, 184-193; chain B: 82-84, 162-167,
185-194; chain C: 92-97, 105-109, 121-123, 162-167, 185-193, plus more) and separately lists
`candidate_missing: []` and populated `candidate_residue_names` (GLU25, ALA26, CYS27, GLN38 ...
PRO234, TYR250, LEU251, ALA252) for **every** pocket residue used in `core_3of3` /
`supported_ge2of3` / the fringe regions. None of the frozen pocket residues (25-27, 38-47,
231-234, 250-252) fall inside any deposited internal gap in any of the three chains — **the
pocket geometry driving D1, D2, RMSF, SASA, and hull volume is built from experimentally
observed electron density, not from PDBFixer-modeled loops.** This substantially narrows the
scope of the "modeled, not observed" caveat: it is a real limitation on the crystal structure's
overall precision and on portions of the model *outside* the analyzed region, not a limitation
that directly fabricates the geometry being measured.

**A serious, now-resolved bug was found in the prep code's history.** Comment at
`run_md.py:1224-1230` (fix landed in commit `47f954b`, 2026-08-12): before the fix, PDBFixer
could not detect 8GLA's internal gaps because the rebuilt gemmi structure was written without
SEQRES records, so it reported `internal_missing_residues_rebuilt: 0` despite ~50 genuinely
unresolved residues; OpenMM then silently bonded the flanking residues across each gap,
producing **13 covalent bonds up to 10.79 Å (nominal bond length 1.33 Å), one carrying 183,222
kJ/mol of strain** — and, critically, the comment notes this occurred *only* in the control
system, i.e. an undisclosed asymmetry between exactly the two systems (8GLA control vs. 1W60
apo) whose pocket SASA the protocol differences. `MD_STRUCTURE_VALIDATION.json` still contains
a record of the pre-fix run showing `internal_missing_residues_rebuilt: 0` for 8GLA
(line 520-521) alongside the corrected run showing `50` (line 620-621) — both snapshots are
preserved in that file, which is itself good provenance hygiene (nothing was overwritten to
hide the earlier defect).

**Classification: SOFTWARE BUG, RESOLVED, PRE-DATES CURRENT DATA.** The fix (SEQRES-carrying +
a hard fail-closed runtime assertion, `assert_no_impossible_bonds()`, `run_md.py:1314-1355`,
which `sys.exit`s on any bond longer than 2.5 Å before every simulation) landed 2026-08-12, five
days before Control-5 began. `outputs_control5/8GLA/prep/prep_audit.json` shows
`internal_missing_residues_rebuilt: 50` (the corrected value), confirming the trajectories
analyzed in this audit used the repaired code path. This bug does **not** invalidate Control-5
or Control-20. It is documented here because the audit brief specifically asked whether an
implementation bug could be present, and because the fail-closed assertion it motivated is a
material, ongoing safeguard worth recording.

---

## 14. Ligand-State Audit

Confirmed via `prep_audit.json` note ("Protein-only, peptides/ligands/waters dropped by >= 200 aa
filter") and `FROZEN_MD_ANALYSIS_PROTOCOL.json:189-192` ("AOH1996-derivative-bound reference,
ligand stripped for protein-only MD"): **AOH1996-1LE is removed before MD.** 8GLA is simulated
as an **apo trajectory launched from a holo (ligand-bound) crystallographic starting
conformation**, not as a liganded simulation.

This is a legitimate design, but it is a scientifically distinct question from "does a bound
ligand keep the pocket open," and the audit brief's framing (§12/§13 of the brief) was right to
ask it explicitly. The hypothesis actually being tested is closer to: *does the GNN-predicted
pocket geometry, once placed in a conformation known to accommodate a real inhibitor, remain
MD-accessible without that inhibitor holding it there?* Under that framing, **rep02 relaxing
toward a lower open-like fraction (0.13) after ligand removal is not obviously anomalous — it is
a physically plausible outcome of removing a stabilizing ligand contact**, not necessarily a
pipeline defect or even necessarily a "wrong" answer about the pocket's biological relevance.
This matters directly for the claim-hierarchy discussion in §20-21 and §28: passing this gate at
3/3 would have shown something stronger and more specific ("this pocket conformation is
MD-stable without the ligand across independent replicas") than "the pipeline works," and this
audit found no contamination of that distinction — `FROZEN_MD_ANALYSIS_PROTOCOL.json:192`
explicitly disclaims the weaker static-comparison claim ("Static... separation is descriptive
only and cannot pass the gate").

---

## 15. Force-Field and MD Protocol Audit

AMBER14SB + TIP3P (`run_md.py:1295`), PME electrostatics with 1.0 nm cutoff, HBonds constraints,
hydrogen mass repartitioning (4 amu) with a 4 fs timestep (`run_md.py:1358-1367`), Monte Carlo
barostat (`run_md.py:1369`). These are standard, defensible choices for a homotrimeric protein
system and are not flagged as bugs or as unusual departures from common practice. The
`assert_no_impossible_bonds()` fail-closed check (§13) runs before every `Simulation` is
constructed. Control-20 resumed each replicate from its own `state.chk`
(`RESUME_AUDIT.json`/`checkpoint_meta.json` present per replicate), consistent with "same three
replicates, same checkpoints, no new minimization, no new equilibration, no seed changes" as the
amendment requires; no evidence of DCD concatenation artifacts, duplicate frames, or a time reset
was found (`duplicate_log_times: false`, `frame_count_status: "ok"` for all three replicates in
both stages).

---

## 16. GNN → Pocket → MD Provenance

`analysis_regions` in `outputs_control5/analysis/summary.json:1784-1850` matches the audit
brief's frozen residue sets exactly: `core_3of3 = [25,26,38,39,40,41,42,44,45,46,47]`,
`supported_ge2of3` adds `[27,43,232,233,234]`, `seed_specific_uncertain_fringe_1of3 =
[231,250,251,252]`. `PCNA_CHAIN_AND_RESIDUE_MAPPING.md` independently confirms these as
CORE (11 residues selected by all 3 GNN seeds), SUPPORTED FRINGE (5 residues, 2/3 seeds), and
SEED-SPECIFIC/UNCERTAIN FRINGE (4 residues, 1/3 seed). The MD pocket is traceably derived from
the frozen 3-seed GNN consensus, not from a later hand-selected residue list — no discrepancy
was found between the GNN's reported support table and the residues actually analyzed by
`analyze_md.py`.

---

## 17. GNN Reproducibility Limitation

The GNN's own 3-seed mean Jaccard reproducibility is **0.6792**
(`reports/strong_robustness_20260815/CURRENT_06792_GEOMETRIC_DIAGNOSIS.md`), a moderate value
that the repository itself already treats with appropriate caution elsewhere: that same document
states a stricter internal `>=0.75` mean-Jaccard target was adopted *after* seeing the 0.6792
result, as "a new voluntary internal release standard," explicitly **not** represented as a
literature-derived universal threshold. This is honest, pre-existing self-scrutiny, not
something introduced by this audit.

No MD outcome — PASS or FAIL, Control-5 or Control-20 — can retroactively raise the GNN's own
localization reproducibility above 0.68. Passing the MD control gate would support Level 2-4
claims (§28); it cannot support Level 5-7 claims about the GNN's general reliability as a pocket
predictor. Failing it, likewise, says nothing new about the GNN's reproducibility either way.

---

## 18. Failure-Message Semantic Audit

**Confirmed defect (now patched, §26).** Pre-patch, `evaluate_control_interpretability()`'s FAIL
`reason` was a single fixed string regardless of *why* the gate failed:
`"FAIL: control trajectories did not demonstrate trajectory-derived dynamics beyond static
starting-state separation plus per-frame noise."`

This is false as a description of the actual Control-20 result. rep01 and rep03 clearly reject
the static-noise null (D1 0.62 and 0.52 vs. threshold 0.173; D2 0.51 and 0.48 vs. threshold
0.138 — 3-4x over threshold). **rep02 also rejects it** (D1 0.395 vs. 0.173; D2 0.538 vs. 0.138)
— its *only* recorded issue is `"open-like fraction 0.130 below 0.200"`
(`summary.json:1638-1640`). All three replicates demonstrated trajectory-derived dynamics
distinguishable from a jittered static structure; the gate failed because only 2/3 reproducibly
cleared the open-like-fraction floor, which is a **different, narrower, and more specific**
failure than "no dynamics were observed." The two statements are not equivalent, and conflating
them (as the pre-patch code did) risks materially understating what the MD actually showed.

**Classification: DOCUMENTATION/REPORTING BUG.** This does not change `status`, `qualifies`,
`issues`, or `qualifying_control_replicates` for any replicate or the gate overall — it is a
human-readable text field only. Patched per §24's instruction to fix reporting semantics without
altering gate outcomes; see §26 for the exact diff and the regression tests that pin both the old
message's continued correctness for the genuinely-static case and the new message's correctness
for this case.

---

## 19. Workflow / Status-State Audit

The literal string `"control5_interpretability: PENDING"` described hypothetically in the audit
brief **does not exist anywhere in the current repository** (grepped across all tracked and
untracked files) — that specific staleness bug, as literally described, was not reproduced.

**Gate 6**, however, was independently verified end-to-end: `md_workflow.py`'s `gate6_decision()`
(`md_workflow.py:202-274`) requires a machine-readable `GATE6_DECISION.json` with
`kind == "PCNA_MD_GATE6_DECISION"`, `schema_version == 1`, `approved is True` (boolean, not a
prose match), a non-empty `approved_by`, and a valid ISO-8601 `approved_utc`. The code's own
comment block (`md_workflow.py:174-188`) documents that an earlier prose-matching heuristic
(`"gate 6" in text and "approved" in text and not "not approved" in text`) was replaced for
exactly the failure mode where "Gate 6: NOT YET APPROVED" would slip past a naive negative-word
list. No `md_validation_4070/GATE6_DECISION.json` exists on disk — confirmed by direct filesystem
check — so `gate6_approved()` returns `False`, and `write_production_authorization()`
(`md_workflow.py:314-367`) refuses to write an authorization artifact without it. **Gate 6 is
correctly PENDING; production is correctly blocked**, independent of and in addition to the
control-gate FAIL (§22).

**A related, real provenance gap was found and patched (§26).** `write_control_report()` wrote
`CONTROL_INTERPRETABILITY_REPORT.md` to a single fixed path with no field recording which
`--outdir` (and therefore which stage — Control-5 vs. Control-20) produced a given verdict. The
**only** reason the Control-5 FAIL result currently survives on disk is that a human manually
copied the file to a hand-typed backup name
(`CONTROL_INTERPRETABILITY_REPORT_5ns_FAIL_2of3_20260817_163213.md`) before running Control-20 —
this was a manual convention, not an enforced one. Had Control-5 and Control-20 produced
different verdicts and no one had remembered to copy the file, the distinct historical Control-5
result would have been silently lost. Patched to record the source outdir in the report and to
auto-archive the outgoing report whenever the outdir or verdict is about to change (§26),
converting the existing manual convention into an enforced one, matching the requirement that a
historical Control-5 result and the current Control-20 result remain distinguishable.

---

## 20. What Control-20 Actually Demonstrates

- **Level 1 (technically valid trajectories): established.** Complete, artifact-free, correctly
  continued from checkpoint, no duplicate frames, no PBC artifacts (§3).
- **Level 2 (genuine correlated molecular dynamics, distinguishable from static-plus-noise):
  established for all three replicates**, by wide margins on both D1 and D2 (§6, §7, §18).
- **Level 3 (predefined pocket-opening behavior occurs at all): established for all three
  replicates** — even the disqualified rep02 shows open-like frames 13% of the time, not zero.
- **Level 4 (reproducible across independent replicas at the frozen 3/3 bar): NOT established.**
  2/3, not 3/3. This is the actual, specific, and now-accurately-reported locus of the FAIL.

---

## 21. What Control-20 Does NOT Demonstrate

- That the GNN-predicted pocket is a stable, reproducibly open state across independent
  replicas under this protocol (Level 4 fails).
- That 20 ns is a sufficient sampling horizon for this system to reach a stationary regime —
  the persistent, largely monotonic block-drift through the entire 15 ns analyzed window (§10)
  argues the opposite.
- Anything about the GNN's general pocket-prediction reliability beyond what its own 0.6792
  mean-Jaccard reproducibility already states (§17) — MD outcomes at this level cannot move
  that number.
- That the pocket is biologically or drug-functionally relevant (Levels 6-7) — that would
  require evidence this experiment was never designed to produce.

---

## 22. Is Production Scientifically Authorized?

**NO.** The frozen control gate is FAIL (2/3 < 3/3 required). Gate 6 has no signed decision
artifact and is independently verified PENDING (§19). `md.sh production`'s preflight
(`md_workflow.py:420-448`) reads `control_interpretability_gate.status` directly from the live
analysis summary and refuses to proceed when it is not `"PASS"`. Nothing in this audit creates,
implies, or should be read as creating authorization. This audit did not run, and this report
does not recommend running, `./md.sh production`.

---

## 23. Recommended Next Step

**NEW PROSPECTIVE CONTROL PROTOCOL** (see `PROPOSED_FUTURE_MD_VALIDATION_PROTOCOL.md`, §27),
for reasons independent of rep02's specific number (§24):

- The persistent convergence drift (§10) suggests 20 ns may be too short to distinguish a
  genuine negative from an under-sampled trajectory for this system; a future protocol should
  prospectively specify a longer sampling horizon and/or a formal convergence-based stopping
  rule, decided *before* seeing new data.
- The open-like-fraction floor, RMSF floor, and absolute openness thresholds should, in a
  future protocol, be accompanied by an explicit derivation (analytic, literature-based, or
  power-calculation-based) with the same rigor already applied to D1/D2, rather than remaining
  round-number heuristics.
- The three-way conflation flagged in §14 (GNN positive control vs. MD pipeline positive control
  vs. pocket-opening reproducibility positive control) should be split into separately named and
  separately gated hypotheses in any future protocol, so a future PASS or FAIL is unambiguous
  about which of the three claims it actually supports.

This is explicitly **not** a recommendation to reanalyze the existing Control-5/Control-20
trajectories under new thresholds, and does not change their frozen FAIL result.

---

## 24. Outcome-Dependence Audit

Explicit certification: **none of the substantive recommendations in this report are
outcome-dependent on rep02's specific 0.130 value.**

- The convergence/sampling-horizon concern (§10, §23) is drawn from block-drift evidence present
  in **rep01 and rep03 as well** — the two replicates that *qualified*. If rep02 had scored 0.25
  and the gate had fully PASSED, this audit would have reported the identical convergence
  finding, because it does not depend on which replicates qualified.
- The threshold-justification gap (§4, §5, §23) is a documentation/derivation completeness
  observation that holds regardless of the specific numeric outcome — it is about *how* 0.20 and
  0.015 nm are justified in the record, not about whether they happened to be cleared.
- The failure-message and provenance-archiving patches (§18, §19, §26) fix *reporting*
  mechanisms that would have been equally wrong (or equally silent, respectively) had the
  outcome been a PASS.

Asking the brief's own control question directly: *would this audit recommend the same new
prospective protocol if rep02 had instead scored 0.25 (i.e., a full 3/3 PASS)?* **Yes** — the
convergence and threshold-justification findings would be unchanged, though the urgency and
framing would shift from "resolve an unresolved FAIL" to "strengthen a PASS before leaning on it
for stronger claims." What this audit does **not** do, and would not do under any outcome, is
propose changing the *current* frozen gate's thresholds, residue definitions, or replicate
requirements to alter the Control-5/Control-20 verdict itself.

---

## 25. Remaining Risks

- The absolute openness thresholds (§5) rest on single static structures per class; a future
  protocol relying on tighter geometric margins should not assume these numbers generalize
  beyond the specific 8GLA/1W60 pair used to set them.
- 3.77 Å resolution and R-free 0.26 (§12) limit confidence in fine-grained side-chain
  geometry across the model generally, even though the specific pocket residues analyzed were
  experimentally resolved, not rebuilt (§13).
- The convergence heuristic (§10) is informational only by design; it should not be
  silently promoted into a hard gate without independent validation of the block-drift test
  itself against a known-converged reference trajectory.
- GATE6_DECISION.template.json exists in the repository (`md_validation_4070/
  GATE6_DECISION.template.json`) as a template only — it is not itself a decision and does not
  approve anything; confirmed it contains no `approved: true` filled-in artifact.

---

## 26. Final Scientific Claim Language

**For a methods/limitations section:**

> Positive-control validation used three independent 20 ns MD replicates of PCNA (PDB 8GLA,
> AOH1996-derivative-bound conformation, ligand removed for protein-only simulation). All three
> replicates exhibited backbone dynamics statistically distinguishable from a static structure
> with matched per-frame coordinate noise (lag-1 autocorrelation and mean |DCCM| both exceeded
> their analytic 3-sigma IID-null thresholds by 2.9-4.5x). However, only 2 of 3 replicates
> reproducibly satisfied the pre-registered pocket-openness-frequency criterion (open-like
> fraction >= 0.20 of analyzed frames); the third scored 0.13. Under the pre-registered
> 3-of-3 replicate-reproducibility requirement, the control gate therefore returned FAIL, and no
> production MD was authorized. Block-wise convergence diagnostics showed persistent,
> frequently monotonic drift through the full 15 ns analyzed window in all three replicates
> (including the two that qualified), suggesting the sampling horizon used may be insufficient
> to establish whether this is a stable result.

**What may be claimed:** the MD pipeline produces artifact-free, checkpoint-continuable
trajectories (Level 1); the analyzed 8GLA replicates show genuine collective backbone motion,
not static-plus-noise (Level 2); predefined pocket-opening behavior occurs at non-trivial
frequency in all three replicates (Level 3).

**What may NOT be claimed:** that the pocket reproducibly opens across independent replicates
under this protocol (Level 4 — explicitly failed); that this result validates the GNN's general
pocket-prediction reliability (Levels 5-7 — out of scope for any MD outcome here); that 20 ns was
established as an adequate sampling horizon for this system (the convergence evidence points the
other way).

---

## Appendix: Software Patches Applied by This Audit

Three narrowly-scoped patches, each with regression tests, none of which changes any gate
threshold, residue definition, replicate requirement, or PASS/FAIL outcome for Control-5 or
Control-20:

1. **`md_validation_4070/analyze_md.py`, `evaluate_control_interpretability()`**: the FAIL
   `reason` string now distinguishes "no replicate rejected the static-noise null" from "N/3
   replicates rejected it, but fewer than 3/3 met every qualification criterion," and adds a new
   `replicates_with_detected_dynamics` field. PASS-path reason text is byte-identical to before.
   Tests: `tests/test_control_gate_reason_semantics.py` (new).
2. **`md_validation_4070/analyze_md.py`, `aggregate_replicates()`**: replicate-level
   `approx_95ci_across_replicates` now uses the correct Student's t critical value for the
   sample size (e.g. 4.303 for n=3, not 1.96), with a new `approx_95ci_method` field recording
   which value was used. This widens every reported CI; it cannot make any result look more
   favorable. Tests: `tests/test_control_gate_reason_semantics.py` (new).
3. **`md_validation_4070/md_workflow.py`, `write_control_report()`**: the report now records its
   source `--outdir` and auto-archives the outgoing report under a timestamped filename whenever
   the outdir or verdict is about to change, converting the previously manual Control-5 backup
   convention into an enforced one. Tests: `tests/test_control_report_stage_provenance.py`
   (new).

Full test results, including pre-existing/environmental failures unrelated to these patches, are
recorded in the companion JSON (`test_results` key) and in the git commit for this branch.

---

### Sources consulted

- [RCSB PDB - 8GLA](https://www.rcsb.org/structure/8GLA)
- [Small molecule targeting of transcription-replication conflict for selective chemotherapy — PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10592352/)
- [Small molecule targeting of transcription-replication conflict for selective chemotherapy — Cell Chemical Biology](https://www.cell.com/cell-chemical-biology/fulltext/S2451-9456(23)00221-0)
