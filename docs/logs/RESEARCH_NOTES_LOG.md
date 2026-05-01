# RESEARCH_NOTES_LOG.md — Informal Research Log

> Running notes, observations, and ideas. Less formal than experiment logs.
> Add entries with date. Never delete.

---

## 2026-04-30 — System setup

- Project: GNN-based cryptic pocket prediction on PCNA
- AI workflow initialized: NotebookLM MCP → Markdown Brain → Claude → Gemini → ChatGPT
- Key bottleneck: data processing stubs (parse_pdb, graph_construction) must be implemented before any experiments can run
- Positive control: must recover AOH1996 pocket in 8GLA — this is the scientific gate
- Main concern: small training dataset (only 8GLA as PCNA-specific positive). Pre-training on CryptoSite is essential.
- Second concern: MD timescale — 100 ns may not be sufficient for cryptic pocket opening. Enhanced sampling may be needed.
- Architecture (CrypticGNN) is already implemented. Implementation unblocked for the model.
- Next priority: implement parse_pdb.py → graph_construction.py → focal_loss.py → dataset.py → train.py

---

## Template for new entries

```
## YYYY-MM-DD — {Topic}

- Observation / idea / concern
- Any action taken or planned
```
