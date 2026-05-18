# VALIDATION.md — Validation System

→ Links: [[EXPERIMENT_INDEX]] | [[KNOWN_LIMITATIONS]] | [[PIPELINE]] | [[MODELS]]

---

## Positive Control (MUST PASS FIRST)

**Rule: Do not trust any novel pocket prediction until the model recovers the AOH1996 site.**

| Test | Criterion | Status |
|---|---|---|
| AOH1996 pocket mean score (small, best_pcna.ckpt) | > 0.7 on 8GLA | **FAIL** — 0.5998 |
| AOH1996 pocket mean score (XL, best_pcna_v3.ckpt) | > 0.7 on 8GLA | **PASS** — 0.8969 |
| AOH1996 pocket rank (XL) | Top-3 candidates on 8GLA | **PASS** — rank 1 |
| AUROC on CryptoSite held-out | > 0.80 | Not measured (same-structure eval only) |

See `data/results/aoh_gate_results.json` for exact values and commands used.

If these fail → debug before proceeding. See [[RESEARCH_QUESTION]] failure criteria.

---

## Pocket Scoring Validation

### Metrics

| Metric | Formula | Interpretation |
|---|---|---|
| AUROC | Area under ROC curve | 0.5 = random, 1.0 = perfect |
| AUPRC | Area under Precision-Recall | Better for imbalanced datasets |
| Top-k recovery | Fraction of known pockets in top-k predictions | Used in PocketMiner benchmark |
| Mean pocket score | Mean score over pocket residues | Sanity check |

### Split rules
- **Protein-level split** — never residue-level split
- PCNA chains A/B/C are near-identical: treat as one protein for split purposes
- Pre-training: CryptoSite protein-level split (train/val/test)
- Fine-tuning: PCNA-specific (8GLA as train-positive, 1W60 as negative)

### Class imbalance
- ~5–15% of residues are pocket-positive
- Focal loss (γ=2, α=0.25) is the default
- Always report both AUROC and AUPRC (AUPRC is more meaningful for imbalanced data)

---

## MD Validation Metrics

### RMSF (Root Mean Square Fluctuation)

| Property | Detail |
|---|---|
| What it measures | Per-residue positional fluctuation over MD trajectory |
| Formula | `RMSF_i = sqrt(mean((r_i(t) - <r_i>)²))` |
| MDAnalysis call | `rmsf = MDAnalysis.analysis.rms.RMSF(atomgroup).run()` |
| Cryptic pocket signature | RMSF > 1.5–2.0 Å for pocket residues vs ~0.5–1.0 Å background |
| Caveats | High RMSF ≠ pocket opening; must cross-check with volume |

### DCCM (Dynamic Cross-Correlation Matrix)

| Property | Detail |
|---|---|
| What it measures | Correlated motion between pairs of residues |
| Formula | `C_ij = <Δr_i · Δr_j> / sqrt(<Δr_i²><Δr_j²>)` |
| Values | +1 = fully correlated, −1 = anti-correlated, 0 = uncorrelated |
| Cryptic pocket signature | Pocket residues show high internal correlation + anti-correlation with "gate" residues |
| Caveats | Correlation ≠ causation; use as supporting evidence only |

### Pocket Volume Tracking

| Property | Detail |
|---|---|
| What it measures | Pocket volume per MD frame |
| Tool | fpocket / MDpocket (fpocket-based) |
| Command | `mdpocket --trajectory_file traj.xtc --trajectory_format xtc -f topology.pdb` |
| Cryptic pocket threshold | Volume > 100 Å³ transiently (ideally > 200–500 Å³ for drug-like) |
| Strong evidence | Volume opens AND closes within trajectory (transient, not permanently open) |

---

## Code Validation

| Check | When to run |
|---|---|
| Unit test: graph construction | Before any training |
| Unit test: focal loss | Before any training |
| Smoke test: forward pass on 1W60 | After model load |
| Integration test: full pipeline on 1W60 | Before claiming pipeline works |
| Positive control test: recover 8GLA pocket | Before novel prediction |

See `docs/implementation/TESTING.md` for test strategy details.

---

## Scientific Validation Checklist

Before reporting any result:

- [ ] Positive control (8GLA pocket recovery) passes
- [ ] Train/val/test split is protein-level, not residue-level
- [ ] No data leakage between PCNA chains in split
- [ ] Class imbalance handled (focal loss or weighted BCE)
- [ ] AUROC + AUPRC reported (not just AUROC)
- [ ] Novel pockets have RMSF evidence from MD
- [ ] Novel pockets have DCCM evidence from MD
- [ ] Crystal contact regions flagged and excluded from claims
- [ ] All limitations from [[KNOWN_LIMITATIONS]] acknowledged in writeup
