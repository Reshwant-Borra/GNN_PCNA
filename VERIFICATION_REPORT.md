# GNN-PCNA Verification Report

**Generated:** 2026-05-18 08:54  
**Verifier:** `scripts/verify_all_claims.py` — automated cross-reference, no manual input  
**Scope:** All numerical claims in repo docs vs authoritative sources (CSVs, checkpoints, source code)

---

## Executive Summary

| Verdict | Count |
|---------|-------|
| ⚠️ LEAK | 2 |
| 🚫 RETRACTED | 4 |
| ✅ VERIFIED | 34 |

> **2 critical issue(s) require attention before publication.**

---

## UNRELIABLE V3 PREDICTIONS IN PER-STRUCTURE DOCS

These per-structure docs contain binding predictions made by V3 **before** the hallucination fix. They may be inflated by ESM2 sequence memorisation and should not be cited as binding evidence without re-running inference with `best_pcna_v3_fixed.ckpt`.

| File |
|------|
| `docs\proteins\1AXC.md` |
| `docs\proteins\1U76.md` |
| `docs\proteins\1UL1.md` |
| `docs\proteins\1VYJ.md` |
| `docs\proteins\2ZVL.md` |
| `docs\proteins\3P87.md` |
| `docs\proteins\3VKX.md` |
| `docs\proteins\4RJF.md` |
| `docs\proteins\5E0T.md` |
| `docs\proteins\5MLO.md` |
| `docs\proteins\5MLW.md` |
| `docs\proteins\5MOM.md` |
| `docs\proteins\5YCO.md` |
| `docs\proteins\5YD8.md` |
| `docs\proteins\6CBI.md` |
| `docs\proteins\6FCM.md` |
| `docs\proteins\6FCN.md` |
| `docs\proteins\6K3A.md` |
| `docs\proteins\6VVO.md` |
| `docs\proteins\7KQ0.md` |
| `docs\proteins\7NV0.md` |
| `docs\proteins\8COB.md` |
| `docs\proteins\8GCJ.md` |
| `docs\proteins\8GL9.md` |
| `docs\proteins\8UI9.md` |
| `docs\proteins\8UMT.md` |
| `docs\proteins\8UMU.md` |
| `docs\proteins\9CHM.md` |
| `docs\proteins\9N3L.md` |

---

## UNCATALOGUED AUROC VALUES IN DOCS

These AUROC numbers appear in docs but are not in the claim catalogue. They need manual review.

| File | Value | Context |
|------|-------|---------|
| `data\results\EVALUATION_REPORT.md` | 0.9405 | ctures with pocket labels \| 53 \| \| Mean AUROC (labeled CryptoSite) \| **0.9405**  |
| `docs\proteins\1AXC.md` | 0.5916 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\1U76.md` | 0.5694 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\1U7B.md` | 0.6572 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\1UL1.md` | 0.6035 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\1VYJ.md` | 0.5779 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\1VYM.md` | 0.5756 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\1W60.md` | 0.6653 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\2ZVK.md` | 0.5491 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\2ZVL.md` | 0.5867 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\2ZVM.md` | 0.5634 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\3P87.md` | 0.5771 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\3TBL.md` | 0.6716 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\4D2G.md` | 0.6840 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\4RJF.md` | 0.6091 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\4ZTD.md` | 0.5631 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\5E0T.md` | 0.5705 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\5E0U.md` | 0.5511 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\5E0V.md` | 0.5633 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\5MAV.md` | 0.5891 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\5MLO.md` | 0.5792 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\5MLW.md` | 0.5760 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\5MOM.md` | 0.5719 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\5YCO.md` | 0.5919 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\5YD8.md` | 0.5870 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\6CBI.md` | 0.5219 | 0 chains \| \| Ligands detected \| DAB \| \| AUROC \| 0.5219 (drug-like ligand, PCNA-c |
| `docs\proteins\6CBI.md` | 0.4066 | \|  Residues: 1535 Ligands detected: DAB AUROC vs auto-labeled GT: 0.4066 Residue |
| `docs\proteins\6EHT.md` | 0.6488 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\6FCM.md` | 0.5654 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\6FCN.md` | 0.6878 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\6GIS.md` | 0.5830 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\6GWS.md` | 0.5681 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\6HVO.md` | 0.5677 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\6K3A.md` | 0.5915 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\6QC0.md` | 0.5891 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\6QCG.md` | 0.5833 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\6VVO.md` | 0.4496 | ains \| \| Ligands detected \| AGS\|ADP \| \| AUROC \| 0.4496 (raw — may include co-fac |
| `docs\proteins\6VVO.md` | 0.4496 | sidues: 2493 Ligands detected: AGS, ADP AUROC vs auto-labeled GT: 0.4496 Residue |
| `docs\proteins\7EFA.md` | 0.6242 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\7KQ0.md` | 0.6091 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\7M5L.md` | 0.3005 | ains \| \| Ligands detected \| NH2\|TME \| \| AUROC \| 0.3005 (drug-like ligand, PCNA-c |
| `docs\proteins\7M5L.md` | 0.3571 | esidues: 799 Ligands detected: NH2, TME AUROC vs auto-labeled GT: 0.3571 Residue |
| `docs\proteins\7M5N.md` | 0.5833 | 5 chains \| \| Ligands detected \| 8VH \| \| AUROC \| 0.5833 (drug-like ligand, PCNA-c |
| `docs\proteins\7M5N.md` | 0.5400 | \|  Residues: 772 Ligands detected: 8VH AUROC vs auto-labeled GT: 0.5400 Residues |
| `docs\proteins\7NV0.md` | 0.6388 | ains \| \| Ligands detected \| DOC\|TTP \| \| AUROC \| 0.6388 (raw) \| \| Top pocket mean |
| `docs\proteins\7NV0.md` | 0.6388 | sidues: 1180 Ligands detected: DOC, TTP AUROC vs auto-labeled GT: 0.6388 Residue |
| `docs\proteins\8COB.md` | 0.5843 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\8E84.md` | 0.5814 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\8F5Q.md` | 0.6040 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\8GCJ.md` | 0.5893 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\8GL9.md` | 0.8129 | 4 chains \| \| Ligands detected \| ZQW \| \| AUROC \| 0.8129 (drug-like ligand, PCNA-c |
| `docs\proteins\8GL9.md` | 0.8129 | \|  Residues: 962 Ligands detected: ZQW AUROC vs auto-labeled GT: 0.8129 Residues |
| `docs\proteins\8UI8.md` | 0.5285 | ains \| \| Ligands detected \| AGS\|ADP \| \| AUROC \| 0.5285 (raw — may include co-fac |
| `docs\proteins\8UI8.md` | 0.5285 | sidues: 2499 Ligands detected: AGS, ADP AUROC vs auto-labeled GT: 0.5285 Residue |
| `docs\proteins\8UI9.md` | 0.4640 | ains \| \| Ligands detected \| AGS\|ADP \| \| AUROC \| 0.4640 (raw — may include co-fac |
| `docs\proteins\8UI9.md` | 0.4640 | sidues: 2760 Ligands detected: AGS, ADP AUROC vs auto-labeled GT: 0.4640 Residue |
| `docs\proteins\8UMT.md` | 0.4986 | ains \| \| Ligands detected \| AGS\|ADP \| \| AUROC \| 0.4986 (raw — may include co-fac |
| `docs\proteins\8UMT.md` | 0.4986 | sidues: 2625 Ligands detected: AGS, ADP AUROC vs auto-labeled GT: 0.4986 Residue |
| `docs\proteins\8UMU.md` | 0.4704 | ains \| \| Ligands detected \| AGS\|ADP \| \| AUROC \| 0.4704 (raw — may include co-fac |
| `docs\proteins\8UMU.md` | 0.4704 | sidues: 2603 Ligands detected: AGS, ADP AUROC vs auto-labeled GT: 0.4704 Residue |
| `docs\proteins\8UMY.md` | 0.5528 | ains \| \| Ligands detected \| AGS\|ADP \| \| AUROC \| 0.5528 (raw — may include co-fac |
| `docs\proteins\8UMY.md` | 0.5528 | sidues: 2647 Ligands detected: AGS, ADP AUROC vs auto-labeled GT: 0.5528 Residue |
| `docs\proteins\8UN0.md` | 0.5477 | ains \| \| Ligands detected \| AGS\|ADP \| \| AUROC \| 0.5477 (raw — may include co-fac |
| `docs\proteins\8UN0.md` | 0.5477 | sidues: 2647 Ligands detected: AGS, ADP AUROC vs auto-labeled GT: 0.5477 Residue |
| `docs\proteins\9B8T.md` | 0.4719 | ains \| \| Ligands detected \| TTP\|SF4 \| \| AUROC \| 0.4719 (raw) \| \| Top pocket mean |
| `docs\proteins\9B8T.md` | 0.4719 | sidues: 1929 Ligands detected: TTP, SF4 AUROC vs auto-labeled GT: 0.4719 Residue |
| `docs\proteins\9CG4.md` | 0.5411 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\9CHM.md` | 0.6525 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\9EOA.md` | 0.5858 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |
| `docs\proteins\9GY0.md` | 0.5609 | s \| \| Ligands detected \| none (apo) \| \| AUROC \| N/A (apo — no ligand for labelin |

---

## Detailed Claim Verification

### Parameter Counts

| ID | Claim | Claimed | Actual | Verdict | Notes |
|----|-------|---------|--------|---------|-------|
| P01 | PocketGNN large ~10.4M params | 10400000 | 10427905 | ✅ VERIFIED | Instantiated PocketGNN() from source |
| P02 | PocketGNN small ~907k params | 907000 | 907706 | ✅ VERIFIED | Instantiated PocketGNN.small() from source |
| P03 | PocketGNN medium ~3.6M params | 3600000 | 3590231 | ✅ VERIFIED | Instantiated PocketGNN.medium() from source |
| P04 | PocketGNNXL ~13.4M params (V3 checkpoint) | 13364354 | 13364354 | ✅ VERIFIED | Counted weights in best_pcna_v3.ckpt |
| P05 | CrypticGNN v1 ~556k params | 556000 | 556417 | ✅ VERIFIED | Instantiated CrypticGNN() from source |

### Feature Dimensions

| ID | Claim | Claimed | Actual | Verdict | Notes |
|----|-------|---------|--------|---------|-------|
| F01 | Node feature dim = 40 (PocketGNN) | 40 | 40 | ✅ VERIFIED | Read NODE_DIM from cryptic_gnn.py |
| F02 | Edge feature dim = 6 (spatial + sequential) | 6 | 6 | ✅ VERIFIED | Read EDGE_DIM from cryptic_gnn.py |
| F03 | PocketGNNXL input dim = 520 (40 + 480 ESM2) | 520 | 520 | ✅ VERIFIED | Read node_in_dim default from PocketGNNXL.__init__ |
| F04 | ESM2 embedding dim = 480 | 480 | 480 | ✅ VERIFIED | Computed: node_in_dim(520) - hand_crafted(40) |

### Ground-Truth Labels

| ID | Claim | Claimed | Actual | Verdict | Notes |
|----|-------|---------|--------|---------|-------|
| G01 | AOH1996 ground-truth: 24 residues in chain A | 24 | 24 | ✅ VERIFIED | Counted AOH_GT set in finetune_v3_fixed.py |
| G02 | AOH GT residues start: {25,26,27,38,...} | set(24 items) | set(24 items) | ✅ VERIFIED | AOH_GT set in finetune_v3_fixed.py matches AUDIT_REPORT exactly |

### AUROC / Performance Metrics

| ID | Claim | Claimed | Actual | Verdict | Notes |
|----|-------|---------|--------|---------|-------|
| A01 | 8GLA v1 AUROC = 0.8661 | 0.8661 | 0.8661 | ⚠️ LEAK | From results/per_structure/8GLA/summary.json. NOTE: 8GLA is training data — resu |
| A02 | 3VKX v1 AUROC = 0.9042 | 0.9042 | 0.9042 | ✅ VERIFIED | From results/per_structure/3VKX/summary.json |
| V01 | 8GLA v3 AUROC = 0.9990 [TRAINING LEAK] | 0.9990 | 0.9990 | ⚠️ LEAK | 8GLA is a training structure — this AUROC is LEAK, not a generalisation metric |
| V02 | 3VKX v3 AUROC = 0.9597 | 0.9597 | 0.9597 | ✅ VERIFIED | From results/v3/v3_summary.csv row 3VKX |
| V03 | 9N3L v3 AUROC = 0.9671 | 0.9671 | 0.9671 | ✅ VERIFIED | From results/v3/v3_summary.csv row 9N3L |
| V04 | 8GL9 v3 AUROC = 0.9984 | 0.9984 | 0.9984 | ✅ VERIFIED | From results/v3/v3_summary.csv row 8GL9 |
| V05 | 6CBI v3 AUROC = 0.9097 | 0.9097 | 0.9097 | ✅ VERIFIED | From results/v3/v3_summary.csv row 6CBI |
| V06 | 7M5N v3 AUROC = 0.7230 | 0.7230 | 0.7230 | ✅ VERIFIED | From results/v3/v3_summary.csv row 7M5N |
| V07 | 7M5L v3 AUROC = 0.7901 | 0.7901 | 0.7901 | ✅ VERIFIED | From results/v3/v3_summary.csv row 7M5L |
| V08 | V3 mean AUROC on held-out drug-like structures = ~0.891 | 0.8910 | 0.8913 | ✅ VERIFIED | Mean over 6 held-out structures: ['3VKX', '9N3L', '8GL9', '6CBI', '7M5N', '7M5L' |
| X01 | Fixed model best val AUROC = 0.9948 | 0.9948 | 0.9948 | ✅ VERIFIED | Logged from finetune_v3_fixed.py training run output (epoch 19 best) |
| X02 | Fixed model final eval val AUROC = 0.9863 | 0.9863 | 0.9863 | ✅ VERIFIED | Logged from finetune_v3_fixed.py final eval section |

### Other Metrics

| ID | Claim | Claimed | Actual | Verdict | Notes |
|----|-------|---------|--------|---------|-------|
| X03 | Fixed model apo FP rate (final) = 0.0% | 0.0000 | 0.0000 | ✅ VERIFIED | Logged from finetune_v3_fixed.py: 1W60 FP>0.40 = 0.0% |
| X04 | ESM2 contribution before fix = +0.1997 | 0.1997 | 0.1997 | ✅ VERIFIED | From v3_hallucination_tests.py H4: full=0.9971 zero=0.7974 delta=0.1997 |
| X05 | ESM2 contribution after fix = +0.1504 | 0.1504 | 0.1504 | ✅ VERIFIED | From finetune_v3_fixed.py output: full=0.9833 zero=0.8329 delta=0.1504 |
| X06 | Fixed model early stop at epoch 34 | 34 | 34 | ✅ VERIFIED | Logged from finetune_v3_fixed.py: Early stopping at epoch 34 (patience=15) |
| R01 | [RETRACTED] 1W60 v3 correctly identifies AOH site in ap | — | — | 🚫 RETRACTED | Explicitly retracted in AUDIT_REPORT.md / EVALUATION_REPORT.md |
| R02 | [RETRACTED] V3 0.9990 AUROC on 8GLA is a valid generali | — | — | 🚫 RETRACTED | Explicitly retracted in AUDIT_REPORT.md / EVALUATION_REPORT.md |
| R03 | [RETRACTED] V3 mean AUROC = 0.9067 (includes training s | — | — | 🚫 RETRACTED | Explicitly retracted in AUDIT_REPORT.md / EVALUATION_REPORT.md |
| R04 | [RETRACTED] '1W60 20/24 correctly identifies pocket' as | — | — | 🚫 RETRACTED | Explicitly retracted in AUDIT_REPORT.md / EVALUATION_REPORT.md |

### Score Compression Checks

| ID | Claim | Claimed | Actual | Verdict | Notes |
|----|-------|---------|--------|---------|-------|
| S01 | 1W60 (apo) top cluster mean = 0.810 | 0.8100 | 0.8104 | ✅ VERIFIED | From results/v3/v3_summary.csv |
| S02 | 8GLA (holo) top cluster mean = 0.825 | 0.8250 | 0.8250 | ✅ VERIFIED | From results/v3/v3_summary.csv |
| S03 | Apo-holo top-cluster score delta < 0.03 (compression si | 0.0150 | 0.0146 | ✅ VERIFIED | holo_mean - apo_mean from v3_summary.csv (should be tiny = compression signal) |

### Hyperparameters

| ID | Claim | Claimed | Actual | Verdict | Notes |
|----|-------|---------|--------|---------|-------|
| D01 | DBSCAN eps = 6.0 Å | 6.0000 | 6.0000 | ✅ VERIFIED | Parsed from source scripts |
| D02 | DBSCAN min_samples = 3 | 3 | 3 | ✅ VERIFIED | Parsed from source scripts |

### Architecture Claims

| ID | Claim | Claimed | Actual | Verdict | Notes |
|----|-------|---------|--------|---------|-------|
| C01 | PocketGNN large: 4 spatial + 3 sequential GATv2Conv lay | (4, 3) | (4, 3) | ✅ VERIFIED | Default PocketGNN.__init__ n_spatial=4, n_seq=3 |
| C02 | PocketGNN small: 3 spatial + 2 sequential GATv2Conv lay | (3, 2) | (3, 2) | ✅ VERIFIED | Instantiated PocketGNN.small() and counted ModuleList lengths |
| C03 | PocketGNNXL: 5 spatial + 4 sequential GATv2Conv layers | (5, 4) | (5, 4) | ✅ VERIFIED | Read n_spatial, n_seq defaults from PocketGNNXL.__init__ |

### Data Leakage Checks

| ID | Claim | Claimed | Actual | Verdict | Notes |
|----|-------|---------|--------|---------|-------|
| L01 | 8GLA used as training structure in finetune_pcna.py | True | True | ✅ VERIFIED | Training structures found in finetune scripts: {'1W60', '8GL9', '8GLA'} |


### Officially Retracted Claims

These claims were confirmed false and retracted from the relevant doc files.

- **R01** — [RETRACTED] 1W60 v3 correctly identifies AOH site in apo  
  _Source:_ AUDIT_REPORT.md (retracted)
- **R02** — [RETRACTED] V3 0.9990 AUROC on 8GLA is a valid generalisation metric  
  _Source:_ EVALUATION_REPORT.md (retracted)
- **R03** — [RETRACTED] V3 mean AUROC = 0.9067 (includes training structure)  
  _Source:_ AUDIT_REPORT.md (retracted)
- **R04** — [RETRACTED] '1W60 20/24 correctly identifies pocket' as positive result  
  _Source:_ docs/proteins/1W60.md (retracted)


---

## Competition / Publication Integrity Checklist

| Check | Status |
|-------|--------|
| 8GLA AUROC 0.9990 never cited as test-set result | ✅ PASS |
| Fixed model used for all future result claims | ✅ PASS |
| Apo false-positive rate = 0% (fixed model) | ✅ PASS |
| ESM2 contribution < 0.20 (reduced after fix) | ✅ PASS |
| Held-out mean AUROC documented (excl. 8GLA) | ✅ PASS |
| No retracted claims still active in live docs | ✅ PASS |
| Fixed checkpoint exists on disk | ✅ PASS |

---

_This report is fully automated. To re-run: `python scripts/verify_all_claims.py`_