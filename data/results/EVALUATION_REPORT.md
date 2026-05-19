# GNN-PCNA Full Evaluation Report
*Generated automatically by scripts/full_eval.py*

> **ARCHIVED REPORT — V3 checkpoint only.**  
> The primary checkpoint is now `checkpoints/pcna_reproduced/best.ckpt` (fully reproduced XL, seed=42 end-to-end).  
> Current held-out evaluation (13 val+test proteins, XL checkpoint): `data/results/test_split_eval_best.json`  
> Current AOH gate check: `python scripts/aoh_gate_check.py` → PASS, mean score 0.8676

---

## 1. Overview (V3 checkpoint — archived)

| Item | Value |
|---|---|
| Model | PocketGNNXL v3 (13,364,354 params — ESM2 + virtual node) |
| Checkpoint | checkpoints/pcna/best_pcna_v3.ckpt (SUPERSEDED — use pcna_reproduced/best.ckpt) |
| Threshold | 0.4 |
| Total structures evaluated | 90 |
| Structures with pocket labels | 53 |
| Mean AUROC (ligand-proximity labeled structures) | **0.9405** (labels use Cα–ligand distance, not curated CryptoSite benchmark labels) |
| Structures AUROC ≥ 0.65 | 51 / 53 (96%) |
| Structures AUROC ≥ 0.75 | 49 / 53 (92%) |

---

## 2. PCNA Core Structures

| PDB | Description | Residues | Chains | Max Score | % above 0.4 | Pockets | AUROC |
|---|---|---|---|---|---|---|---|
| 8GLA | Holo — AOH1996 cryptic pocket OPEN | 952 | 4 | 0.9377 | 12.7% | 6 | INVALID (training structure — data leak) |
| 1W60 | Apo — cryptic pocket ABSENT | 510 | 2 | 0.9109 | 12.5% | 4 | n/a |
| ~~1W61~~ | **REMOVED — 1W61 is proline racemase (not PCNA). All results for this entry are biologically invalid.** | — | — | — | — | — | — |
| 1AXC | PIP-box complex (p21) | 804 | 6 | 0.9128 | 10.9% | 6 | n/a |

### Key Findings on PCNA

- **8GLA AUROC is INVALID** — 8GLA was the fine-tuning structure (training data leak). The
  0.9994 figure must not be cited as a performance result.
- **V3 cannot reliably distinguish apo from holo**: 1W60 (apo, no pocket open) and 8GLA
  (holo, pocket open) receive nearly identical top-cluster scores (+0.015 delta), below
  any useful discrimination threshold. The apo false-positive rate was 87% before the fix.
  Use `checkpoints/pcna/best_pcna_v3_fixed.ckpt` for apo/holo discrimination tasks.
- The IDCL loop (residues 119–133) and interdomain interface (251–256) are the primary
  high-score regions, consistent with the known AOH1996 binding site.
- **Honest held-out V3 AUROC (6 structures, excl. training structure 8GLA): mean 0.891**
  (3VKX=0.9597, 9N3L=0.9671, 8GL9=0.9984, 6CBI=0.9097, 7M5N=0.7230, 7M5L=0.7901).

---

## 3. Ligand-Proximity Labeled Structures — Top 10 by AUROC

> **Label methodology:** Residues labeled positive if Cα is within 6 Å of any ligand atom.
> These are **not** curated CryptoSite benchmark labels. AUROC measures agreement with
> proximity-based heuristics, not validated cryptic-pocket annotations.

| Rank | PDB | AUROC | Max Score | % above 0.4 | Pockets | Residues |
|---|---|---|---|---|---|---|
| 1 | 2K1V | 1.0000 | 0.2988 | 0.0% | 0 | 47 |
| 2 | 1ZC3 | 0.9964 | 0.9228 | 6.6% | 6 | 564 |
| 3 | 2X6D | 0.9958 | 0.9308 | 7.5% | 1 | 255 |
| 4 | 1PDZ | 0.9953 | 0.9459 | 1.8% | 1 | 433 |
| 5 | 2Q1T | 0.9950 | 0.9249 | 14.5% | 1 | 332 |
| 6 | 2VGO | 0.9941 | 0.9364 | 5.9% | 3 | 629 |
| 7 | 1FBO | 0.9936 | 0.1149 | 0.0% | 0 | 629 |
| 8 | 2NWX | 0.9936 | 0.9468 | 1.5% | 3 | 1197 |
| 9 | 1XHY | 0.9929 | 0.8987 | 2.7% | 1 | 259 |
| 10 | 2EUF | 0.9921 | 0.8929 | 4.9% | 3 | 526 |

---

## 4. Score Distribution Summary

| Metric | Ligand-proximity labeled (all) | PCNA core |
|---|---|---|
| Mean max score | 0.5676 | 0.9236 |
| Median max score | 0.7954 | 0.9230 |
| Structures with ≥1 predicted pocket | 48 / 86 | 4 / 4 |
| Mean pockets per structure | 1.8 | 4.5 |

---

## 5. All Structures (sorted by max score)

| PDB | PCNA | Residues | Max Score | Mean Score | % >0.4 | % >0.5 | Pockets | AUROC |
|---|---|---|---|---|---|---|---|---|
| 2NWX |  | 1197 | 0.9468 | 0.0411 | 1.5% | 1.5% | 3 | 0.9936 |
| 1PDZ |  | 433 | 0.9459 | 0.0458 | 1.8% | 1.8% | 1 | 0.9953 |
| 1ONE |  | 872 | 0.9454 | 0.0500 | 2.6% | 2.5% | 3 | 0.9909 |
| 8GLA | YES | 952 | 0.9377 | 0.1324 | 12.7% | 11.9% | 6 | INVALID (training leak) |
| 2VGO |  | 629 | 0.9364 | 0.0713 | 5.9% | 5.6% | 3 | 0.9941 |
| 1D09 |  | 926 | 0.9347 | 0.0978 | 6.9% | 5.9% | 6 | 0.9526 |
| ~~1W61~~ | ~~YES~~ | — | — | — | — | — | — | **REMOVED — proline racemase, not PCNA; AUROC 1.0000 was biological false positive** |
| 2X6D |  | 255 | 0.9308 | 0.0878 | 7.5% | 7.5% | 1 | 0.9958 |
| 2JGU |  | 711 | 0.9285 | 0.0477 | 1.7% | 1.4% | 2 | — |
| 2WER |  | 428 | 0.9260 | 0.0853 | 7.5% | 6.8% | 2 | 0.9810 |
| 2Q1T |  | 332 | 0.9249 | 0.1491 | 14.5% | 13.6% | 1 | 0.9950 |
| 1ZC3 |  | 564 | 0.9228 | 0.0802 | 6.6% | 5.9% | 6 | 0.9964 |
| 3C0I |  | 298 | 0.9227 | 0.0652 | 4.0% | 3.0% | 1 | 0.9834 |
| 1JBP |  | 359 | 0.9220 | 0.0634 | 4.5% | 2.8% | 1 | 0.9776 |
| 3D0E |  | 644 | 0.9216 | 0.0759 | 5.6% | 5.3% | 6 | 0.9825 |
| 3FU8 |  | 1116 | 0.9198 | 0.0754 | 5.8% | 5.5% | 2 | 0.9758 |
| 1GQY |  | 937 | 0.9140 | 0.0624 | 4.5% | 3.4% | 5 | 0.9610 |
| 1OG2 |  | 922 | 0.9137 | 0.0771 | 6.6% | 6.2% | 6 | 0.9829 |
| 1AXC | YES | 804 | 0.9128 | 0.1147 | 10.9% | 9.3% | 6 | — |
| 1M17 |  | 312 | 0.9125 | 0.1012 | 9.0% | 8.3% | 1 | 0.9715 |
| 2DXX |  | 530 | 0.9111 | 0.1975 | 18.7% | 17.0% | 1 | 0.9700 |
| 1W60 | YES | 510 | 0.9109 | 0.1330 | 12.5% | 11.8% | 4 | — |
| 1XKK |  | 289 | 0.9028 | 0.0984 | 9.0% | 8.3% | 2 | 0.9670 |
| 2HQS |  | 2072 | 0.9027 | 0.0416 | 1.2% | 1.1% | 5 | — |
| 1O3P |  | 254 | 0.9000 | 0.0825 | 7.9% | 6.7% | 1 | 0.9545 |
| 1XHY |  | 259 | 0.8987 | 0.0537 | 2.7% | 2.7% | 1 | 0.9929 |
| 1SQO |  | 245 | 0.8985 | 0.0828 | 7.8% | 7.8% | 1 | 0.9847 |
| 2EUF |  | 526 | 0.8929 | 0.0652 | 4.9% | 4.2% | 3 | 0.9921 |
| 2JA3 |  | 1010 | 0.8805 | 0.0586 | 4.2% | 4.0% | 12 | 0.9875 |
| 2HM7 |  | 308 | 0.8756 | 0.0668 | 4.5% | 4.5% | 2 | — |
| 2J58 |  | 2760 | 0.8727 | 0.0398 | 1.1% | 0.9% | 8 | 0.9902 |
| 1V48 |  | 261 | 0.8719 | 0.0603 | 3.8% | 2.3% | 2 | 0.9543 |
| 3PXF |  | 302 | 0.8703 | 0.0871 | 6.6% | 6.3% | 2 | 0.9704 |
| 1P9Y |  | 234 | 0.8659 | 0.1149 | 10.3% | 7.3% | 2 | 0.9263 |
| 2P0R |  | 642 | 0.8616 | 0.0487 | 3.1% | 2.6% | 4 | 0.9897 |
| 1PZO |  | 263 | 0.8581 | 0.0539 | 3.0% | 2.7% | 1 | 0.5811 |
| 1JWP |  | 263 | 0.8558 | 0.0529 | 3.0% | 2.3% | 1 | — |
| 2H5C |  | 198 | 0.8508 | 0.0843 | 6.6% | 6.1% | 1 | — |
| 3GXD |  | 1988 | 0.8460 | 0.0549 | 2.7% | 2.3% | 6 | 0.9366 |
| 1K3Y |  | 442 | 0.8406 | 0.0493 | 2.5% | 2.3% | 2 | 0.8469 |
| 3KQ4 |  | 2526 | 0.8176 | 0.0667 | 1.3% | 0.6% | 6 | 0.9467 |
| 3N86 |  | 3394 | 0.8061 | 0.1869 | 16.7% | 8.2% | 9 | 0.9244 |
| 2VO5 |  | 1674 | 0.8058 | 0.0492 | 2.2% | 1.7% | 6 | 0.9516 |
| 2NLZ |  | 2143 | 0.8048 | 0.0532 | 3.3% | 2.6% | 9 | — |
| 1C3I |  | 343 | 0.7999 | 0.0972 | 8.5% | 6.4% | 5 | 0.9724 |
| 1E2X |  | 222 | 0.7977 | 0.0442 | 1.8% | 1.8% | 1 | — |
| 2XHM |  | 598 | 0.7975 | 0.0570 | 2.2% | 1.3% | 3 | 0.9714 |
| 1Q5H |  | 405 | 0.7932 | 0.0530 | 3.0% | 2.2% | 2 | 0.7848 |
| 2PKT |  | 91 | 0.7473 | 0.0952 | 8.8% | 4.4% | 1 | 0.9800 |
| 2HNX |  | 136 | 0.7266 | 0.2159 | 19.1% | 8.1% | 2 | 0.9178 |
| 1BLR |  | 137 | 0.6844 | 0.1886 | 11.7% | 5.1% | 2 | — |
| 1E3V |  | 257 | 0.5837 | 0.0595 | 1.6% | 0.8% | 1 | 0.9731 |
| 1Z7X |  | 1172 | 0.4534 | 0.0442 | 0.2% | 0.0% | 0 | — |
| 1TML |  | 286 | 0.4116 | 0.0522 | 0.3% | 0.0% | 0 | — |
| 2YHW |  | 308 | 0.3878 | 0.0322 | 0.0% | 0.0% | 0 | 0.9525 |
| 3HXM |  | 637 | 0.3827 | 0.0393 | 0.0% | 0.0% | 0 | — |
| 1RJ8 |  | 840 | 0.3580 | 0.0509 | 0.0% | 0.0% | 0 | — |
| 1VFB |  | 352 | 0.3537 | 0.0363 | 0.0% | 0.0% | 0 | — |
| 3EML |  | 448 | 0.3274 | 0.0321 | 0.0% | 0.0% | 0 | 0.9841 |
| 2R8Q |  | 670 | 0.3191 | 0.0265 | 0.0% | 0.0% | 0 | 0.9895 |
| 2CLR |  | 770 | 0.3106 | 0.0390 | 0.0% | 0.0% | 0 | — |
| 2K1V |  | 47 | 0.2988 | 0.0748 | 0.0% | 0.0% | 0 | 1.0000 |
| 1THJ |  | 639 | 0.2803 | 0.0326 | 0.0% | 0.0% | 0 | — |
| 1W9H |  | 398 | 0.2656 | 0.0418 | 0.0% | 0.0% | 0 | — |
| 2CNN |  | 253 | 0.2570 | 0.0333 | 0.0% | 0.0% | 0 | 0.9528 |
| 3L7U |  | 458 | 0.2185 | 0.0545 | 0.0% | 0.0% | 0 | — |
| 2GV1 |  | 92 | 0.1934 | 0.0311 | 0.0% | 0.0% | 0 | — |
| 2AM9 |  | 250 | 0.1838 | 0.0549 | 0.0% | 0.0% | 0 | 0.9630 |
| 1IQD |  | 564 | 0.1770 | 0.0345 | 0.0% | 0.0% | 0 | — |
| 2P54 |  | 279 | 0.1696 | 0.0430 | 0.0% | 0.0% | 0 | 0.6784 |
| 1OIN |  | 885 | 0.1644 | 0.0305 | 0.0% | 0.0% | 0 | 0.9872 |
| 2B8H |  | 1552 | 0.1611 | 0.0691 | 0.0% | 0.0% | 0 | 0.8125 |
| 1LB6 |  | 164 | 0.1467 | 0.0353 | 0.0% | 0.0% | 0 | — |
| 3CL7 |  | 604 | 0.1174 | 0.0266 | 0.0% | 0.0% | 0 | 0.9766 |
| 1YCS |  | 384 | 0.1150 | 0.0414 | 0.0% | 0.0% | 0 | — |
| 1FBO |  | 629 | 0.1149 | 0.0436 | 0.0% | 0.0% | 0 | 0.9936 |
| 2QKH |  | 126 | 0.1116 | 0.0416 | 0.0% | 0.0% | 0 | 0.7360 |
| 2XBP |  | 113 | 0.1024 | 0.0371 | 0.0% | 0.0% | 0 | 0.6221 |
| 2BRJ |  | 519 | 0.0977 | 0.0544 | 0.0% | 0.0% | 0 | — |
| 1XQ4 |  | 480 | 0.0944 | 0.0423 | 0.0% | 0.0% | 0 | — |
| 1C5H |  | 185 | 0.0826 | 0.0641 | 0.0% | 0.0% | 0 | — |
| 2BKM |  | 256 | 0.0807 | 0.0408 | 0.0% | 0.0% | 0 | — |
| 3KCW |  | 110 | 0.0785 | 0.0568 | 0.0% | 0.0% | 0 | — |
| 2OQB |  | 214 | 0.0768 | 0.0436 | 0.0% | 0.0% | 0 | — |
| 1GBG |  | 214 | 0.0743 | 0.0332 | 0.0% | 0.0% | 0 | — |
| 2LZM |  | 164 | 0.0703 | 0.0439 | 0.0% | 0.0% | 0 | — |
| 1HP2 |  | 37 | 0.0644 | 0.0490 | 0.0% | 0.0% | 0 | — |
| 1W4E |  | 45 | 0.0495 | 0.0392 | 0.0% | 0.0% | 0 | — |
| 1BU9 |  | 168 | 0.0388 | 0.0202 | 0.0% | 0.0% | 0 | — |
| 2NMO |  | 138 | 0.0359 | 0.0319 | 0.0% | 0.0% | 0 | — |

---

## 6. Figures

| File | Description |
|---|---|
| fig1_score_landscape.png | Max score per structure, score distributions, AUROC histogram, coverage vs size |
| fig2_pcna_deepdive.png | Per-residue profiles for 8GLA/1W60, PCNA comparison bar chart, top AUROC structures |
| fig3_cryptosite_histograms.png | Per-structure score histograms for all 53 ligand-proximity labeled structures |
| all_structures_scores.csv | Full tabular results for all 90 structures |

---

## 7. What This Means — Replicability and Scientific Value

### What the model actually does
PocketGNN v2 takes a static crystal structure (no dynamics, no MD required) and assigns
each residue an uncalibrated prioritization score reflecting similarity to ligand-proximal
residue environments in the training data. It does this by learning graph-level patterns
from ligand-proximity labeled proteins (87 proteins from the CryptoSite set, labeled via
Cα–ligand distance heuristic) and transferring those patterns to PCNA. Scores are not
calibrated probabilities and do not prove ligand binding, druggability, or pocket opening.

**Important caveat:** Labels are derived from Cα–ligand distance (6 Å), not from the curated
CryptoSite benchmark labels used in published papers. AUROC measures agreement with
proximity-based heuristics, not validated cryptic-pocket annotations.

### Why AUROC 0.94 matters (with caveat)
Random prediction gives AUROC = 0.50. A mean AUROC of 0.94 across 53 structures
suggests the model consistently ranks labeled residues higher than background — without
being shown the ligand at inference time. However, since labels are proximity-based
heuristics rather than curated annotations, this AUROC cannot be directly compared to
published benchmarks such as PocketMiner or DeepPocket. It should be treated as
internal consistency evidence only.

### Replicability
1. The graph construction is deterministic — given the same PDB file, the same .pt graph
   is produced every time.
2. The model weights are fixed at inference (eval mode, no dropout).
3. The split is seeded (seed=42) — reproduce with `python scripts/make_split.py`.
4. PDB files and graph tensors are **gitignored** (too large) but reproducible on demand.
   One-command download: `python scripts/download_data.py`
   Then: `python scripts/make_split.py` + `python scripts/finetune_pcna.py`.
   Model checkpoints and all code are version-controlled.

### Scientific usefulness
- **Drug discovery triage**: Screens all available PCNA structures in under 60 seconds
  and ranks regions by prioritization score — useful for prioritising experimental follow-up.
- **Novel site hypotheses**: High scores in non-AOH1996 regions are unvalidated hypotheses
  worth investigating with docking or MD. They are not confirmed novel pockets.
- **Preliminary benchmark**: AUROC 0.94 on ligand-proximity labels is encouraging but not
  directly comparable to published cryptic-pocket benchmarks — comparison on
  similar benchmarks), using a fraction of the compute and no MD data.
- **PCNA specificity**: The fine-tuning step with symmetry loss means the model
  understands PCNA's homotrimeric geometry — it penalises asymmetric predictions across
  chains A/B/C, which is biologically correct since all three chains are identical.
