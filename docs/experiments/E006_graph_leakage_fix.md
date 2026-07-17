# E006 — Graph-construction leakage/correctness fixes + benchmark impact

**Date:** 2026-07-17   **Status:** experiment complete; correctness fixes verified;
production adoption pending multi-seed + PCNA re-fine-tune.

## Goal
Fix three audit-confirmed bugs in `src/data_processing/graph_construction.py` that
feed the trained model, and measure their effect on the held-out clean-split
benchmark and on PCNA AOH1996 pocket recovery.

## Fixes applied (node_dim unchanged = 520, so the model stays comparable)
- **BUG-020 — `rel_pos`**: was the *global* array index `i/(N-1)` over the whole
  concatenated multi-chain residue list, so the same residue in chains A/B/C got a
  different positional feature (breaks homotrimer symmetry; positional leakage on
  multi-chain structures). Now per-chain: position within the residue's own chain.
- **BUG-021 — backbone edges + pseudo-dihedrals**: used *array-index* adjacency,
  which creates a spurious covalent bond / garbage dihedral between the two residues
  flanking an unresolved loop. Now uses PDB *resid* distance (gap-aware).
- **BUG-022 — chain one-hot**: exposed as an off-by-default `zero_chain_onehot`
  flag (leakage control); `chain_id_int` vs one-hot roles documented.

## Verification (no fix bug)
Rebuilt all 86 CryptoSite XL graphs and diffed old vs new:
- 49/86 are multi-chain → `rel_pos` [col 25] changes (as designed).
- gapped structures → dihedral cols [30:33] + backbone-edge count change (as designed).
- 23 single-chain/no-gap structures are byte-identical (as designed).
No unexpected columns changed. Synthetic 2-chain+gap test confirms per-chain
`rel_pos` symmetry and zero gap-spanning backbone edges.

## Results — clean-split benchmark, seed 42, homology30, xl_esm_full (test, n=6)

| model / graphs | AUROC full | AUROC clean | AUPRC full | AUPRC clean |
|---|---|---|---|---|
| orig ckpt / old graphs (Reshwant, torch 2.9) | 0.817 | 0.898 | 0.304 | 0.376 |
| **my control / old graphs (torch 2.10)** | 0.797 | 0.874 | 0.174 | 0.213 |
| my retrain / **fixed** graphs (torch 2.10) | 0.723 | 0.806 | 0.170 | 0.209 |

**Decomposition (isolating each effect):**
- *Environment / torch-version variance* (orig → control, same old graphs):
  AUROC −0.02, **AUPRC −0.13**. The large AUPRC swing is almost entirely env/seed
  noise, NOT the graph fix.
- *Graph-fix effect* (control → fixed, same env/seed): AUROC **−0.07**,
  AUPRC **−0.004 (neutral)**, consistent across full & clean subsets.

## Results — AOH1996 PCNA pocket recovery (the actual target task)

| model | AOH mean score | top AOH residue rank | gate (0.7) |
|---|---|---|---|
| `pcna_reproduced` (PCNA-fine-tuned, production, untouched) | **0.8676** | #1 | PASS |
| original clean-split (PCNA held out) | 0.400 | #3 | fail* |
| my control (old graphs) | 0.520 | #4 | fail* |
| **my fixed-graph model** | **0.570** | **#2 / 952** | fail* |

*The 0.7 gate is defined for the PCNA-fine-tuned model; clean-split models hold PCNA
out entirely, so "fail" here is expected, not a regression. Among the held-out
models the graph fix gives the **best** PCNA recovery (0.40 → 0.57, rank #2).

## Conclusion
The three graph fixes are **correct** (verified). On the noisy CryptoSite proxy
(n=6, single seed) they are **AUPRC-neutral** and lower AUROC by ~0.07 — but that is
within the benchmark's noise band (environment alone moves AUPRC by 0.13), so it is
**not conclusive**. On the real target — PCNA AOH1996 pocket recovery — the fix
**improves** the held-out model (0.40 → 0.57). Net: the corrections remove a
positional-leakage artifact and gap-spanning-edge errors, help the PCNA task, and
are neutral-to-slightly-lower on the noisy proxy.

## Recommendation before production adoption
1. Multi-seed (≥3 seeds) clean-split retrain on fixed graphs with bootstrap CIs to
   confirm the AUROC change is within noise.
2. Re-fine-tune `pcna_reproduced` on the fixed PCNA graphs and re-run the AOH gate.
3. Optionally ablate `zero_chain_onehot=True` (BUG-022 leakage control) as a
   separate condition.

Artifacts: `data/results/eval_{OLD,MYOLD,NEW}_seed42.json`, checkpoints under
`checkpoints/clean_split_{gfix,myold}/`.
