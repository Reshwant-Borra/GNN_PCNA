# VALIDATION.md — Validation System

→ Links: [[EXPERIMENT_INDEX]] | [[KNOWN_LIMITATIONS]] | [[PIPELINE]] | [[MODELS]]

---

## Positive Control (MUST PASS FIRST)

**Rule: Do not trust any novel pocket prediction until the model recovers the AOH1996 site.**

| Test | Criterion | Status |
|---|---|---|
| AOH1996 pocket mean score (reproduced PCNA fine-tune) | > 0.7 on 8GLA | **PASS** — 0.8676, rank 1 |
| AOH1996 pocket mean score (small, original) | > 0.7 on 8GLA | **FAIL** — 0.5998 |
| AUROC on held-out test split (5 proteins) — reproduced fine-tuned XL | > 0.80 | **0.9390** (seed=42) ✓ |
| AUROC combined val+test (13 proteins) — reproduced fine-tuned XL | > 0.70 | **0.8081** ✓ |
| AUPRC combined val+test (13 proteins) — reproduced fine-tuned XL | > 0.30 | **0.3441** (6.2× above trivial baseline) ✓ |
| AUROC on held-out test split — reproduced pretrain XL | > 0.80 | **0.9494** (5 proteins, seed=42) ✓ |
| ANM apo/holo fold-change delta | > 0 | **+0.247** (0.857→1.104) ✓ |

See `data/results/aoh_gate_results.json` and `data/results/test_split_eval_pcna_reproduced.json`.

**Recommended checkpoint**: `checkpoints/pcna_reproduced/best.ckpt` — fully reproduced PCNA model, complete provenance chain (pretrain seed=42 → finetune seed=42, lr=3e-4, epoch=57).

If these fail → debug before proceeding. See [[RESEARCH_QUESTION]] failure criteria.

---

## Independent Test-Split Evaluation (COMPLETED)

The CryptoSite split (`data/splits/cryptosite_split.json`, seed=42) withholds 13 proteins
from ALL training as a held-out evaluation set (8 val + 5 test). These are different protein
families from PCNA. Labels use ligand-proximity (Cα within 6 Å) — same methodology as
training, applied consistently to unseen structures.

### Primary checkpoint results (pcna_reproduced/best.ckpt, XL, seed=42 end-to-end)

| Split | N proteins | Mean AUROC | Mean AUPRC | Trivial AUPRC | Fold above trivial |
|-------|-----------|-----------|-----------|--------------|-------------------|
| Val (8 proteins) | 8 | 0.7263 | 0.3276 | ~0.07 | ~4.7× |
| Test (5 proteins) | 5 | 0.9390 | 0.3706 | ~0.08 | ~4.6× |
| **Combined (13)** | **13** | **0.8081** | **0.3441** | **~0.056** | **6.2×** |

AUROC is inflated by class imbalance (~5–15% positive residues); **AUPRC is the primary metric**.

Val structures: 2QKH, 1JBP, 2P54, 2XBP, 1K3Y, 1O3P, 1PZO, 1Q5H  
Test structures: 1V48, 3CL7, 1D09, 1M17, 2VO5

### All checkpoints comparison

| Model | Checkpoint | AOH Gate | Val AUROC (8) | Test AUROC (5) | Test AUPRC | Provenance |
|-------|-----------|----------|---------------|----------------|------------|------------|
| PocketGNNXL PCNA fine-tune (reproduced) | `checkpoints/pcna_reproduced/best.ckpt` | **PASS 0.8676** | 0.7263 | **0.9390** | **0.3706** | seed=42 end-to-end, all known |
| PocketGNNXL pretrain (reproduced) | `checkpoints/reproduced_xl/best.ckpt` | FAIL (pretrain only) | 0.7256 | 0.9494 | 0.4011 | seed=42, lr=3e-4, epoch 10 |
| PocketGNNXL fixed (original) | `checkpoints/pcna/best_pcna_v3_fixed.ckpt` | PASS 0.8969 | 0.7717 | 0.9627 | 0.4035 | seed=UNKNOWN (superseded) |
| PocketGNN small (reproduced) | `checkpoints/reproduced/best.ckpt` | FAIL | 0.6093 | 0.7414 | 0.1094 | seed=42, lr=3e-4, epoch 12 |
| PocketGNN small (original) | `checkpoints/pcna/best_pcna.ckpt` | FAIL | 0.5253 | 0.6484 | 0.1659 | SUPERSEDED |

Commands:
```
# Primary: reproduced PCNA fine-tune (PASS gate + full provenance)
python scripts/aoh_gate_check.py --ckpt checkpoints/pcna_reproduced/best.ckpt --model xl
python scripts/run_test_eval.py  # defaults: XL checkpoint, data/graphs_xl, all 13 proteins

# Reproduced pretrain (CryptoSite benchmark only)
python scripts/run_test_eval.py --ckpt checkpoints/reproduced_xl/best.ckpt --model xl --graphs data/graphs_xl
```

Full results:
- `data/results/test_split_eval_best.json` (**primary — 13 proteins, PASS gate + full provenance**)
- `data/results/test_split_eval_reproduced_xl.json` (pretrain only, CryptoSite benchmark)
- `data/results/test_split_eval_best_pcna_v3_fixed.json` (original XL fixed, superseded)

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
| Delta (holo − apo) | — | **+0.247** | — | Consistent with ligand-induced opening hypothesis |

Method: ANM, 7.5 Å cutoff, 20 non-trivial modes. Correlates with MD-RMSF at r~0.6–0.8 (Eyal et al. 2006).

Commands:
```
python scripts/run_nma.py --pdb data/raw/1W60.pdb
python scripts/run_nma.py --pdb data/raw/8GLA.pdb
```

**Interpretation:** The apo→holo fold-change shift (0.857→1.104, Δ=+0.247) is consistent with the expected structural
signature of a ligand-induced cryptic pocket opening. This is a coarse-grained physics-based indicator computed from
crystallographic coordinates using normal modes — it supports but does not confirm the hypothesis. Independent MD
simulation would be required for confirmation.

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
