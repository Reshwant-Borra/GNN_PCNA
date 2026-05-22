# E003: MD Validation — RMSF + DCCM on AOH1996 Pocket (1W60 Apo)

**Status:** smoketest complete (6.4 ns) — full 100 ns pending
**Date started:** 2026-05-21
**Date completed (smoketest):** 2026-05-21

→ Links: [[EXPERIMENT_INDEX]] | [[VALIDATION]] | [[PIPELINE]] | [[KNOWN_LIMITATIONS]]

---

## Hypothesis

The AOH1996 cryptic pocket residues on apo PCNA (1W60) will show elevated RMSF and coherent correlated motion (DCCM) relative to background residues in explicit-solvent MD simulation, confirming that the GNN-predicted site has intrinsic dynamic character even without ligand.

---

## Goal

Provide all-atom conformational evidence for or against cryptic pocket dynamics at the AOH1996 site. Required before claiming any novel cryptic site in the paper.

---

## How We Found This / Background

The overnight web crawler (15.1 h, 446 Ollama-scored docs) identified the CDK8/CycC 500 ns MDAnalysis paper (PubMed pmid_29737445) as the direct workflow template. That paper uses the same stack — MDAnalysis, per-residue RMSF, pocket volume time series — on a cryptic allosteric site. We adapted that methodology directly.

ANM (Anisotropic Network Model) on the static structures gave us the baseline:
- Apo 1W60 fold-change: **0.857** (pocket sub-global rigidity)
- Holo 8GLA fold-change: **1.157** (pocket above-global flexibility)
- Delta: +0.300

All-atom MD was required to confirm whether this signal holds in explicit solvent with full dynamics.

---

## Simulation Setup

| Parameter | Value |
|---|---|
| Structure | 1W60 (apo PCNA, chains A+B, no ligand) |
| Force field | CHARMM36m |
| Water model | TIP3P |
| Salt | 150 mM NaCl |
| Temperature | 310 K |
| Pressure | 1 bar |
| Timestep | 4 fs (HMR) |
| Electrostatics | PME |
| Software | OpenMM 8.1 |
| Total atoms | 356,789 |
| Hardware | Google Cloud NVIDIA L4 GPU (~140 ns/day) |
| Co-author | Reshwant Borra |

---

## Analysis Pipeline

1. Reshwant ran OpenMM simulation on L4 GPU, output: `1W60_production.dcd` + `1W60_solvated.pdb`
2. Files transferred via Wormhole (P2P, codes: `6-october-brickyard` for DCD, `2-breakaway-jawbone` for topology)
3. `python scripts/run_md_analysis.py --top data/md/1W60_solvated.pdb --traj data/md/1W60_production.dcd --stride 10`
4. `python scripts/make_md_figures.py --dpi 300`
5. `python scripts/build_paper_docx.py` (auto-fills section 3.8)

**MDAnalysis version:** 2.10.0
**Alignment:** backbone alignment to first frame via `AlignTraj(in_memory=False)`
**RMSF:** computed on Cα atoms every 10th frame (stride=10)
**DCCM:** two-pass Cα displacement cross-correlation

---

## Ground Truth Pocket Residues

AOH1996 contact residues (within 6 Å of ZQZ in 8GLA, chains A+B):

```
Chain A: 25,26,27,38,39,40,41,42,44,45,46,47,123,125,126,128,231,232,233,234,250,251,252,253
Chain B: 23,25,26,27,38,39,40,41,42,44,45,46,47,123,125,126,128,231,232,233,234,250,251,252
```

50 residues total matched in the solvated topology.

---

## Smoketest Results (6.4 ns)

| Metric | Value | ANM Baseline | Notes |
|---|---|---|---|
| Trajectory length | 6.4 ns | — | 636 frames, 10 ps/frame |
| Pocket mean RMSF | **3.355 Å** | — | AOH1996 contact residues |
| Background mean RMSF | **4.032 Å** | — | All other protein Ca |
| **Fold-change** | **0.832** | 0.857 | Pocket is 17% more rigid than background |
| **Pocket internal DCCM** | **0.3018** | 0.0995 | 3× higher than ANM predicted |
| Mean pocket volume | 19,683 Å³ | — | Cα convex hull (closed state baseline) |
| Max pocket volume | 21,745 Å³ | — | No major opening events at 6.4 ns |

---

## Interpretation

**Fold-change 0.832:** The AOH1996 pocket residues are slightly more rigid than background at 6.4 ns, consistent with the pocket being in a closed conformation. This matches ANM (0.857) directionally. The pocket has not opened in the smoketest window, which is expected — cryptic pocket opening is typically a rare event on the µs timescale.

**DCCM 0.3018 vs ANM 0.0995:** The all-atom MD reveals 3× stronger correlated motion at pocket residues than the harmonic ANM model predicted. The pocket residues are moving together as a coordinated unit even in the closed state. This is a positive signal — it means the pocket has collective dynamic character, a prerequisite for opening.

**What this means for the paper:** The smoketest confirms the MD pipeline is working and the pocket is dynamically interesting. The fold-change below 1.0 is expected and honest — we are not claiming the pocket opens at 6.4 ns. The 100 ns production run is needed to observe transient opening events.

---

## How These Numbers Are Used

- **Fold-change** goes into paper section 3.8 as direct MD confirmation of the ANM signal
- **DCCM** is the stronger result — correlated motion is independent evidence supporting pocket druggability
- **Pocket volume time series** (fig4b) shows the closed-state baseline; spikes in the 100 ns run would be opening events
- All numbers auto-populate section 3.8 of the paper when `build_paper_docx.py` is run after `run_md_analysis.py`

---

## Output Files

| File | Description |
|---|---|
| `data/results/md_rmsf_1W60.json` | Per-residue RMSF, fold-change |
| `data/results/md_dccm_1W60.npy` | 522×522 DCCM matrix |
| `data/results/md_pocket_volume.json` | Volume time series |
| `data/results/md_apo_comparison.json` | Summary + ANM comparison |
| `data/results/fig4a_md_rmsf.png` | Per-residue RMSF figure |
| `data/results/fig4b_md_pocket_vol.png` | Pocket volume time series |
| `data/results/fig4c_md_dccm.png` | DCCM heatmap |

---

## Limitations

- 6.4 ns smoketest is too short to observe cryptic pocket opening (µs–ms timescale)
- RMSF is not directional — high RMSF ≠ pocket opening; must correlate with volume spikes
- Cα convex hull overestimates true pocket volume; MDpocket/fpocket needed for accurate cavity volumes
- DCCM from 63 frames (stride=10 on 636 frames) is statistically limited — full 100 ns will give more reliable matrix
- Single trajectory — may not sample full conformational space

---

## Next Steps

- [ ] Receive full 100 ns production DCD from Reshwant via Wormhole
- [ ] Rerun `run_md_analysis.py` on full trajectory (expect fold-change closer to or above 1.0)
- [ ] Check pocket volume time series for transient spikes > 25,000 Å³
- [ ] If pocket doesn't open in 100 ns: run metadynamics with pocket volume as collective variable
- [ ] Update paper section 3.8 with final numbers

---

## Validation Criteria

| Criterion | Target | Smoketest | Status |
|---|---|---|---|
| Fold-change > 1.0 (pocket more flexible than bg) | Yes | 0.832 | Pending full run |
| DCCM > 0.1 (coherent pocket motion) | Yes | **0.3018** | PASS |
| Pocket volume spike > 25,000 Å³ | Yes | 21,745 max | Pending full run |
| Pipeline runs end-to-end | Yes | Yes | PASS |
