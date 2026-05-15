# PocketMiner — Distilled Notes

**Source:** PocketMiner paper (Durrant Lab, ~2023)
**Status:** Needs NotebookLM extraction — notes below from paper_notes.md only

---

## Architecture

- GNN trained on CryptoSite dataset (~93 apo/holo protein pairs)
- Graph: residue-level, edges by Cα–Cα distance
- Labels: residues near cryptic pocket in holo structure
- Key result: AUROC ~0.85 on held-out CryptoSite proteins
- Needs NotebookLM extraction: exact architecture (layer type, hidden dim, edge features)
- Needs NotebookLM extraction: exact feature set used

---

## Dataset

- CryptoSite: ~93 protein pairs
- Needs NotebookLM extraction: train/val/test split details
- Needs NotebookLM extraction: whether PCNA was in the training set

---

## Metrics

| Metric | Value | Notes |
|---|---|---|
| AUROC | ~0.85 | Held-out CryptoSite proteins |
| Other metrics | Needs NLM extraction | |

---

## Limitations

- Trained on general proteins — may need fine-tuning for PCNA
- Needs NotebookLM extraction: what limitations the authors stated

---

## Relevance to GNN-PCNA

- Primary baseline to beat
- Architecture is very similar to ours (CrypticGNN) — compare designs
- Should be tested on PCNA to establish what our starting point is
- If PocketMiner already recovers 8GLA pocket: use as pre-trained weights

---

## Merge Target

→ Update `docs/knowledge/MODELS.md` baselines section after full NLM extraction

---

## Related

[[MODELS]] · [[VALIDATION]] · [[paper_notes]] · [[deepallo_notes]] · [[extraction_template]]
