---
type: phase5-md-results
system: 1AXC human PCNA homotrimer (apo-from-p21)
status: analysis_complete_corrected
result_class: negative_inconclusive
date: 2026-05-30
---

# Phase 5 MD Results — 1AXC PCNA (apo-from-p21), 25 ns exploratory triage

**System:** human PCNA homotrimer (3 chains × 261 res), p21 peptide removed.
OpenMM 8.2, AMBER14, TIP3P, ~287k atoms. RunPod B200.

**Sampling (effective):** n = 1. replicate_01 = full 25 ns (250 frames @ 0.1 ns);
replicate_02 = incomplete (41 frames, killed at budget wall) — not a valid
replicate; replicate_03 not run. No 8GLA positive control. Analysis after
discarding 5 ns equilibration (200 frames used).

**Analysis correction:** the original RunPod analysis was corrupted (missing PBC
imaging → RMSD 2.468 nm, RMSF 1–3 nm, physically impossible). Re-run with
`image_molecules` before superposition, core alignment excluding the measured
windows, RMSF about the mean position. The simulation itself was stable
(potential energy flat ~−2.68M kJ/mol, T = 300 K, ρ = 1.01 g/mL).

**Stability (replicate_01):** backbone Cα RMSD mean 0.255 nm, max 0.305 nm,
final 0.287 nm. Flat plateau = stable trimer.

## Per-window Cα RMSF (nm)

| Window  | Role                        | RMSF  | vs ref |
|---------|-----------------------------|-------|--------|
| 239–243 | novel candidate A           | 0.081 | 0.65×  |
| 28–32   | novel candidate B           | 0.081 | 0.65×  |
| 206–210 | novel candidate C           | 0.074 | 0.59×  |
| 134–138 | IDCL-adjacent control       | 0.084 | 0.67×  |
| 118–122 | IDCL/PIP positive control   | 0.126 | 1.00×  |

## Pocket-dynamics metrics (rep1, 3 monomers as informal triplicates)

- **Heavy-atom RMSF (Å):** candidates 0.92–1.03; front-face PIP pocket 1.44; IDCL ref 1.50.
- **Region SASA (Å², mean / CV):** front-face pocket 2324 / 3.1%; 239–243 331 / 7.0%;
  28–32 182 / 9.1%; 206–210 202 / 10.3%; 134–138 148 / 15.9%; ref 118–122 447 / 4.7%.
- **Front-face pocket mouth distances (Å, mean ± SD, range):** 44–251 9.4 ± 0.26 (1.4);
  42–234 16.7 ± 0.33 (1.9); 128–252 12.1 ± 0.82 (4.1); 122–232 29.4 ± 1.07 (5.4).

## Pocket-opening event check (per region × monomer)

No sustained opening in any monomer. Novel candidates showed only transient SASA
excursions of ~18–26% lasting 2–7 of 200 frames with ~zero second-half drift
(jitter, returns to baseline). Front-face PIP pocket essentially static (5–8%
amplitude). Largest single-frame mouth breath: 128–252 ~14.5 Å vs 11.5 Å baseline
(~26%, not sustained). Only sustained widening was in 134–138 (the known-flexible
IDCL-adjacent control, ~55% transient, +6–13% drift), i.e. expected loop motion.

## Result statement

Under this short exploratory 1AXC apo setup, the GNN-predicted novel candidate
pockets (239–243, 28–32, 206–210) remained rigid and did not open; the front-face
PIP pocket did not reopen after p21 removal; observed flexibility was confined to
the known IDCL. **This is a valid negative/inconclusive result — not falsification:**
25 ns / n = 1 / no positive control cannot sample ns–µs cryptic-opening events.
No druggability, validated-site, or novel-site claims are supported.

## Limitations

25 ns usable; n = 1 (rep2 incomplete, rep3 absent); single structure; apo-from-p21
(relaxation from a peptide-bound state); no 8GLA positive control; SASA/distance/Rg
are opening proxies, not true pocket-volume (no fpocket/MDpocket); 3 monomers not
independent. First-MD-interpretation human gate (doc 26) not yet recorded.
