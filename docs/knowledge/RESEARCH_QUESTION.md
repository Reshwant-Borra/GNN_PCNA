# RESEARCH_QUESTION.md

→ Links: [[SYSTEM_OVERVIEW]] | [[VALIDATION]] | [[EXPERIMENT_INDEX]] | [[KNOWN_LIMITATIONS]]

---

## Current Research Question

**Can a graph neural network trained on known cryptic pocket examples predict novel cryptic binding sites on PCNA that are not visible in the apo crystal structure, and can those predictions be validated by molecular dynamics simulation?**

---

## Sub-Questions

| # | Sub-question | Status |
|---|---|---|
| Q1 | Does the GNN recover the known AOH1996 pocket in 8GLA? | **Yes (XL)** — mean 0.8969, rank 1 (small model fails: 0.5998) |
| Q2 | Does the GNN identify additional novel sites on PCNA? | Not yet tested |
| Q3 | Do predicted novel sites show elevated RMSF in MD? | **ANM DONE** — apo fold-change 0.857 (rigid, closed), holo 1.157 (open). Delta=+0.300 is consistent with a ligand-associated flexibility increase (hypothesis) |
| Q4 | Do predicted novel sites show correlated motion (DCCM) in MD? | **ANM DONE** — internal DCCM 0.0995 (apo), 0.2093 (holo); mild coherent motion confirmed |
| Q5 | Do any predicted sites show transient pocket opening (volume > 100 Å³)? | Not yet tested |
| Q6 | Is PocketMiner's performance on PCNA improved by fine-tuning? | Not yet tested |

---

## Validation Criteria (what "success" looks like)

### Minimum bar (must pass before any claim)
- [x] GNN scores AOH1996 pocket residues in 8GLA with mean score > 0.7 — **PASS** (XL: 0.8969; small: FAIL 0.5998)
- [x] AOH1996 pocket ranks in top-3 pocket candidates on 8GLA — **PASS** (rank 1 with XL)
- [x] AUROC > 0.80 on held-out test split (protein-level) — **PASS** (XL fixed: 0.9627; reproduced small: 0.7414)

### Strong result (publication-grade)
- [ ] AUROC > 0.80 on held-out CryptoSite proteins
- [ ] At least one novel PCNA pocket shows RMSF > 1.5 Å AND DCCM block
- [ ] At least one novel pocket shows volume > 100 Å³ transiently in MD

### Ideal result
- [ ] Novel cryptic site at inter-subunit interface not targeted by AOH1996
- [ ] MD opens pocket within 50 ns simulation
- [ ] Pocket geometry compatible with drug-like molecules (volume 200–500 Å³)

---

## Failure Criteria (stop or pivot)

| Condition | Action |
|---|---|
| GNN fails to recover 8GLA pocket | Debug labeling, graph construction, or class imbalance — do not proceed to novel prediction |
| AUROC < 0.65 on CryptoSite | Pre-training data quality issue — investigate data pipeline |
| MD never opens predicted pocket in 100 ns | Consider enhanced sampling (metadynamics); or discard pocket |
| All predicted novel pockets are crystal contacts | Graph construction issue — add crystal contact filtering |

---

## Claims Allowed vs Not Allowed

| Claim type | Allowed? |
|---|---|
| "GNN recovers known AOH1996 pocket" | Yes, if positive control passes |
| "Novel cryptic sites predicted" | Unvalidated candidates only — not confirmed |
| "Novel site is druggable" | Only with volume + geometry analysis |
| "Novel site is better than AOH1996 site" | Not without functional assay |
| "PCNA inhibition via novel site expected" | Not without wet lab validation |
| "Model generalizes to all proteins" | No — trained on CryptoSite, validated on PCNA |

See [[KNOWN_LIMITATIONS]] for full limitations.
