# GNN rerun evidence (2026-06-21, local CPU reproduction)

Reproduced from `pcna-xl-esm-full-final-framing` checkpoint
`checkpoints/pcna_reproduced/best.ckpt` (XL, seed 42), torch 2.10 CPU.

## 1. AOH1996 gate (positive control) — PASS
`python scripts/aoh_gate_check.py --ckpt checkpoints/pcna_reproduced/best.ckpt --model xl`
- AOH1996 pocket mean score **0.8676** (recorded 0.8676 ✓), median 0.9211
- Top AOH residue ranked **#1 of 952**, gate threshold 0.7 → **PASS**

## 2. Held-out generalization — reproduced exactly
`python scripts/run_test_eval.py` → combine 8 val + 5 test (13 proteins, never trained/finetuned):
- **AUROC 0.8081**, **AUPRC 0.3441** (recorded 0.8081 / 0.3441 ✓)
- val mean AUROC 0.7263, test mean AUROC 0.9390

## 3. Cryptic-pocket nuance found on rerun (FLAG FOR HUMAN GATE — do not silently change metric)
At **matched pocket residues**, the GNN scores the AOH1996 site high in BOTH forms:
- holo 8GLA pocket mean **0.868**
- apo  1W60 **same-residue** mean **0.907**
- mean holo−apo delta **−0.040** (essentially zero / slightly apo-favoring)

The recorded `disc_score = 0.741` is **mean(holo pocket) − mean(ALL apo residues = 0.127)**,
i.e. pocket-foreground vs whole-structure-background — NOT an apo↔holo discriminator.
Implication: the GNN flags the pocket site from the closed apo structure (good for cryptic-site
*prediction*) but provides **no residue-level opening signal by itself** → the cryptic (dynamic)
claim depends on MD, which is exactly why the MD validation must be done correctly.

## Top-15 residues on 8GLA (by score)
Dominated by AOH pocket residues (chain A 25/26/27/232/39/233/251/250…), confirming the model
concentrates signal on the AOH1996 site. (Note: 8GLA graph contains chains A–D; AOH ground
truth is A+B only — chain-identity should be confirmed, consistent with the prior 9B8T chain bug.)
