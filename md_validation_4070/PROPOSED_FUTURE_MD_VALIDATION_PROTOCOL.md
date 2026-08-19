# Proposed Future MD Validation Protocol

**STATUS: PROPOSED. NOT PART OF CONTROL-5. NOT PART OF CONTROL-20. NOT RETROACTIVE.**
**REQUIRES A NEW PROSPECTIVE FREEZE, RECORDED BEFORE ANY NEW MD IS RUN, BEFORE IT HAS ANY
STANDING.**

This document does not apply to, reinterpret, or overturn the existing Control-5 or Control-20
results. Both remain historically **FAIL** under their own frozen protocol
(`FROZEN_MD_ANALYSIS_PROTOCOL.json`, SHA-256 pinned in
`FROZEN_MD_ANALYSIS_PROTOCOL.sha256`), regardless of anything proposed here. This document exists
only because `CONTROL20_FORENSIC_METHODOLOGY_AUDIT.md` §23/§27 concluded that a *future*
experiment, if one is ever run, would benefit from addressing three specific, independently
motivated gaps. It must not be used to justify reanalyzing the existing Control-5/Control-20
trajectories under different rules.

---

## 1. Motivation (traced to specific audit findings, not to the outcome)

1. **Sampling horizon.** All three existing Control-20 replicates show `DRIFTING_BLOCKS`
   convergence status through the entire 15 ns analyzed window (post-5-ns-discard), in both
   qualifying and non-qualifying replicates. This is independent of any specific replicate's
   open-like fraction and would have been reported identically under a full PASS.
2. **Threshold justification.** `minimum_open_like_fraction` (0.20), `minimum_pocket_rmsf_nm`
   (0.015), and the absolute SASA/hull openness thresholds are prospectively frozen but lack an
   analytic, literature, or power-calculation-based derivation, unlike D1/D2.
3. **Hypothesis conflation.** "GNN found a relevant region," "the MD pipeline produces
   interpretable dynamics," and "this specific pocket conformation reproducibly stays
   MD-accessible without its ligand" are three different claims currently tested by one combined
   gate.

## 2. Proposed changes (for a NEW experiment only)

- **Sampling horizon and stopping rule.** Prospectively specify either (a) a longer minimum
  per-replicate production length chosen independently of any pilot MD from this system, or
  (b) a formal, pre-registered convergence criterion (e.g., a block-standard-error or
  autocorrelation-corrected effective-sample-size test, not the current first-vs-last-block
  heuristic) that must be met before the trajectory is analyzed for openness/reproducibility at
  all. Either choice must be frozen and hashed before any new MD is launched.
- **Threshold derivation.** Any new open-like-fraction or RMSF floor should cite an explicit
  basis: an analytic null (as D1/D2 already do), a literature precedent for PCNA/IDCL opening
  frequency, or a pre-registered power calculation for the target replicate count. If none is
  available, the floor should be explicitly labeled as an engineering heuristic in the frozen
  protocol document itself, rather than presented alongside the analytically-derived D1/D2
  without distinction.
- **Absolute geometric thresholds.** If SASA/hull midpoint thresholds are reused, derive them
  from an ensemble (e.g. a short pre-production apo/holo comparison across several starting
  conformations or crystal forms) rather than a single static structure per class, to reduce
  sensitivity to any one structure's crystallographic idiosyncrasies.
- **Separate the three hypotheses.** Name and gate them independently:
  - *GNN localization control*: does the frozen pocket residue set reproduce across GNN seeds
    above a pre-declared reproducibility bar? (Already tracked separately — 0.6792 mean
    Jaccard — this should simply be cited explicitly as its own claim rather than left implicit.)
  - *MD pipeline interpretability control*: do control trajectories reject the static-plus-noise
    null? (This is what D1/D2 already test well; keep as-is.)
  - *Pocket-opening reproducibility control*: does the specific pocket conformation remain
    MD-accessible, reproducibly, across independent replicates, with or without its native
    ligand? (State explicitly whether the new experiment tests the liganded or apo-from-holo
    condition, and consider running both if resources allow, since they are different
    hypotheses.)

## 3. What this document does NOT authorize

- It does not authorize production MD.
- It does not authorize rerunning or extending the existing Control-5/Control-20 trajectories.
- It does not change `FROZEN_MD_ANALYSIS_PROTOCOL.json`, its SHA-256, or any threshold currently
  in force.
- It does not change Gate 6, which remains PENDING and requires a human-signed
  `GATE6_DECISION.json` regardless of any future protocol described here.

Any new experiment following this proposal requires its own prospective freeze, its own SHA-256
pinned protocol document, and its own Gate 6 review before production.
