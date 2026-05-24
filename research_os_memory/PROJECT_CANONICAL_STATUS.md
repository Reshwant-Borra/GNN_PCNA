# PROJECT_CANONICAL_STATUS.md

Last updated: 2026-05-24T00:00:00Z
Updated by: human (initial bootstrap)
Status: current

---

## Project Goal

Predict cryptic binding pockets on PCNA (Proliferating Cell Nuclear Antigen) using a dual-branch GNN + ESM2 embedding architecture. Validate novel predictions with MD simulation. Produce a research paper.

## Current Research Question

Can a GNN trained on known cryptic pockets (CryptoSite) generalize to identify novel cryptic sites on PCNA, including the AOH1996 site and previously unknown sites?

## Current Hypothesis

PocketGNNXL V3, trained on CryptoSite and fine-tuned on PCNA structures, will recover the AOH1996 ground-truth pocket and identify additional candidate cryptic sites that show dynamic flexibility in MD simulation.

## Current Status Summary

Model training complete. Held-out evaluation complete. ANM analysis complete. MD simulation in-progress (100 ns likely done on Google Cloud L4). Paper drafted (v2, section 3.8 pending MD results).

---

## Dataset Status

| Dataset | Status | Notes |
|---|---|---|
| 59 PCNA structures | Current | Downloaded, graphs built |
| CryptoSite (87 proteins) | Current | train=42, val=8, test=5 |
| 8GLA (AOH1996-bound) | Current | Fine-tuning only; NOT in held-out eval |
| 1W60 (apo) | Current | Not in any split |
| 9B8T | INVALID | Chain assignment wrong — see issue_registry.json ISSUE-0001 |

Split file: `data/splits/cryptosite_split.json`

## Model Status

| Model | Params | Checkpoint | Status |
|---|---|---|---|
| PocketGNN V1 | ~907k | `checkpoints/pcna_reproduced/best.ckpt` | Superseded |
| PocketGNNXL V3 | ~13.4M | `checkpoints/pcna_reproduced/best.ckpt` | **Current** |

Active checkpoint: `checkpoints/pcna_reproduced/best.ckpt` (seed=42, PocketGNNXL V3)

## Validation Status

| Test | Criterion | Result | Status |
|---|---|---|---|
| AOH1996 gate | Mean score > 0.700 on 8GLA | 0.8676 | **PASS** |
| Held-out AUROC | > 0.80 | 0.8081 | **PASS** |
| Held-out AUPRC | > trivial | 0.3441 (baseline 0.0557, 6.2× lift) | **PASS** |
| ANM delta | Holo > apo | +0.300 (0.857 → 1.157) | **PASS** |
| MD pocket opening | RMSF + volume evidence | Pending trajectory analysis | **PENDING** |

## Paper Status

- Draft: `docs/GNN_PCNA_Research_Paper_v2.docx`
- Builder: `scripts/build_paper_docx.py`
- Sections complete: Introduction, Methods, Results 3.1–3.7, Conclusions, References, Glossary
- Section pending: 3.8 (MD results — waiting on trajectory analysis)
- Authors: Advay, Reshwant Borra

---

## Current Blockers

1. MD trajectory analysis not yet run — `scripts/run_md_analysis.py` needs DCD file
2. 9B8T must be regenerated with correct chains (B/C/D) before any 9B8T claim

## Next Steps

1. Transfer `1W60_production.dcd` from L4 (wormhole receive or gcloud storage cp)
2. Run `scripts/run_md_analysis.py` → RMSF, pocket volumes, DCCM
3. Fill section 3.8 in paper, add Table 5
4. Regenerate 9B8T with correct chains
5. Final paper review and submission
