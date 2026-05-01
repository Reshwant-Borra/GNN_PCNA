# DeepAllo — Distilled Notes

**Source:** DeepAllo paper (~2022)
**Status:** Needs NotebookLM extraction — notes below from paper_notes.md only

---

## Architecture

- Attention-based GNN targeting allosteric communication pathways
- Identifies residues that transmit conformational signals (not just geometric pockets)
- Needs NotebookLM extraction: exact architecture, input features, training data

---

## Task

- Allosteric site prediction (related to but distinct from cryptic pocket prediction)
- Could identify pockets at inter-subunit interfaces

---

## Relevance to PCNA

- PCNA has known allosteric coupling between subunit interfaces (A–B, B–C, C–A)
- DeepAllo could identify interface pockets missed by geometric methods
- Needs NotebookLM extraction: does DeepAllo predict allosteric sites in homotrimers?

---

## Metrics

- Needs NotebookLM extraction: what datasets and metrics DeepAllo reports

---

## Limitations

- Needs NotebookLM extraction

---

## Merge Target

→ Update `docs/knowledge/MODELS.md` baselines section after full NLM extraction
