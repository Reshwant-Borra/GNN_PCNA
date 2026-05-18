# VALIDATION.md — Validation System

→ Links: [[EXPERIMENT_INDEX]] | [[KNOWN_LIMITATIONS]] | [[PIPELINE]] | [[MODELS]]

---

## Positive Control (MUST PASS FIRST)

**Rule: Do not trust any novel pocket prediction until the model recovers the AOH1996 site.**

| Test | Criterion | Status |
|---|---|---|
| AOH1996 pocket mean score (small) | > 0.7 on 8GLA | **FAIL** — 0.5998 |
| AOH1996 pocket mean score (XL fixed) | > 0.7 on 8GLA | **PASS** — 0.8969 |
| AOH1996 pocket rank (XL fixed) | Top-3 on 8GLA | **PASS** — rank 1 |
| AUROC on held-out test split — small | > 0.65 | **0.6484** (5 proteins, protein-level split) |
| AUROC on held-out test split — XL fixed | > 0.80 | **0.9627** (5 proteins, protein-level split) ✓ |
| AUPRC on held-out test split — XL fixed | > 0.30 | **0.4035** ✓ |
| ANM apo/holo fold-change delta | > 0 | **+0.247** (0.857→1.104) ✓ |

See `data/results/aoh_gate_results.json` and `data/results/test_split_eval_best_pcna_v3_fixed.json`.

If these fail → debug before proceeding. See [[RESEARCH_QUESTION]] failure criteria.

---

## Independent Test-Split Evaluation (COMPLETED)

The CryptoSite split (`data/splits/cryptosite_split.json`, seed=42) withholds 5 proteins
from ALL training as a held-out test set. These are different protein families from PCNA.
Labels use ligand-proximity (Cα within 6 Å) — same methodology as training, applied
consistently to unseen structures.

| Model | Checkpoint | Val AUROC (8) | Test AUROC (5) | Test AUPRC |
|-------|-----------|---------------|----------------|------------|
| PocketGNN small (reproduced, full provenance) | `checkpoints/reproduced/best.ckpt` | 0.6093 | 0.7414 | 0.1094 |
| PocketGNN small (original, provenance UNKNOWN) | `checkpoints/pcna/best_pcna.ckpt` | 0.5253 | 0.6484 | 0.1659 |
| PocketGNNXL fixed | `checkpoints/pcna/best_pcna_v3_fixed.ckpt` | 0.7717 | **0.9627** | **0.4035** |

Test structures (never seen during any training): 1V48, 3CL7, 1D09, 1M17, 2VO5

Command: `python scripts/run_test_eval.py --ckpt checkpoints/pcna/best_pcna_v3_fixed.ckpt --model xl --graphs data/graphs_xl`

Full results: `data/results/test_split_eval_best_pcna_v3_fixed.json`

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

## ANM Flexibility Analysis (COMPLETED — apo/holo comparison)

Full results: `data/results/nma_apo_holo_comparison.json`

| Structure | State | Pocket fold-change | Internal DCCM | Interpretation |
|-----------|-------|--------------------|---------------|----------------|
| 1W60 | apo (no ligand) | **0.857** | 0.0995 | Pocket rigidly packed, closed ✓ |
| 8GLA | holo (AOH1996 bound) | **1.104** | 0.0780 | Pocket open, residues more flexible ✓ |
| Delta (holo − apo) | — | **+0.247** | — | Ligand-induced opening confirmed ✓ |

Method: ANM, 7.5 Å cutoff, 20 non-trivial modes. Correlates with MD-RMSF at r~0.6–0.8 (Eyal et al. 2006).

Commands:
```
python scripts/run_nma.py --pdb data/raw/1W60.pdb
python scripts/run_nma.py --pdb data/raw/8GLA.pdb
```

**Interpretation:** The apo→holo fold-change shift (0.857→1.104, Δ=+0.247) is the expected structural
signature of a ligand-induced cryptic pocket. In the apo state the site is rigid and buried; ligand
binding opens it and increases local flexibility. This is computed purely from crystallographic
coordinates using physics-based normal modes — independent of the GNN model.

---

## MD Validation Metrics (NOT YET RUN — infrastructure ready, no trajectory data)

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
