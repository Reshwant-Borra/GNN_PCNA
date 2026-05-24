# VALIDATION_STATUS.md

Last updated: 2026-05-24T00:00:00Z
Updated by: human (initial bootstrap)
Status: current

---

## Validation Question

Does PocketGNNXL V3 generalize to unseen proteins with known cryptic pockets, and can it recover the experimentally confirmed AOH1996 binding site on PCNA?

---

## Structural Evidence (ANM)

| Metric | Apo (1W60) | Holo (8GLA) | Delta | Interpretation |
|---|---|---|---|---|
| ANM fold-change vs global | 0.857 | 1.157 | +0.300 | Pocket stiffens in apo; softens when AOH1996 binds |
| Internal DCCM | 0.0995 | 0.2093 | +0.1098 | Increased coordinated motion in holo pocket |

Script: `scripts/run_nma.py`. ProDy, cutoff 7.5 Å, 20 modes, chains A+B of 8GLA only.
Results: `data/results/nma_apo_holo_comparison.json`

---

## MD Evidence

| Metric | Target | Actual |
|---|---|---|
| Per-residue RMSF of pocket | > 1.5 Å | PENDING — trajectory analysis not run |
| Pocket volume (transient max) | > 100 Å³ | PENDING |
| DCCM from trajectory | Coherent block | PENDING |

MD: CHARMM36m + TIP3P, 356,789 atoms, OpenMM 8.1, 4 fs HMR, 100 ns, Google Cloud L4.
DCD file: `data/md/1W60_production.dcd` (needs transfer from cloud).
Analysis script: `scripts/run_md_analysis.py`

---

## Metrics Used

- AUROC (area under ROC) — general discriminative power
- AUPRC (area under precision-recall) — better for class imbalance
- Lift over trivial baseline — AUPRC / (pocket_residue_fraction)
- ANM fold-change — pocket flexibility relative to global protein
- DCCM — coordinated internal motion of pocket residues

---

## Evidence Classification

| Claim | Current classification |
|---|---|
| GNN generalizes to held-out proteins | strongly_supported_computationally |
| AOH1996 site recovered | strongly_supported_computationally |
| Pocket has dynamic flexibility | moderately_supported (ANM only; MD pending) |
| Novel cryptic sites exist on PCNA | hypothesis_generating |

---

## Contradictions

None identified.

---

## Safe Interpretation

- "PocketGNNXL V3 achieves held-out AUROC 0.8081 on 13 CryptoSite proteins."
- "The model recovers the AOH1996 site with mean score 0.8676 (threshold 0.700)."
- "ANM analysis shows elevated flexibility in the holo pocket region (fold-change delta +0.300)."
- "MD validation is pending; pocket opening has not yet been confirmed from trajectory."

## Disallowed Interpretation

- "The novel sites are validated cryptic pockets." (requires MD volume evidence)
- "The model proves new druggable sites exist." (requires experimental validation)

---

## Required Follow-Up

1. Run `scripts/run_md_analysis.py` after DCD transfer → RMSF, volume, DCCM
2. If pocket opens (volume > 100 Å³ transiently): upgrade CLAIM-0005
3. If pocket does not open in 100 ns: consider metadynamics
4. Regenerate 9B8T with chains B/C/D before any 9B8T claim
