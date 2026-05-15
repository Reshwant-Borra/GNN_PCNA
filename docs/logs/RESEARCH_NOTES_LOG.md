# RESEARCH_NOTES_LOG.md — Informal Research Log

> Running notes, observations, and ideas. Less formal than experiment logs.
> Add entries with date. Never delete.

---

## 2026-05-14 — Data crawl + pipeline bootstrap

### Structures acquired
- **112 raw PDB files** downloaded to `data/raw/`, **90 stripped** to `data/processed/`
- Core PCNA set (4): `1W60` (apo 3.15Å), `8GLA` (AOH1996 holo 3.77Å), `1AXC` (p21 PIP-box 2.6Å), `1W61` (RFC 2.1Å)
- **CryptoSite benchmark**: 87/93 proteins downloaded (6 failed: 2×404, 2×incomplete Cα, 2×resolution > 3.5Å)
- **RCSB search P12004**: 102 PCNA structures found, 96 UniProt cross-refs confirmed

### Priority structure ranking (for pipeline use)

| Priority | PDB ID | Resolution | Use |
|---|---|---|---|
| 1 | 8GLA | 3.77 Å | Ground truth — AOH1996 pocket labeling |
| 2 | 1W60 | 3.15 Å | Apo baseline — cryptic pocket absent |
| 3 | 4RJF | 2.0 Å | Highest-res apo — better node features |
| 4 | 1U7B | 1.88 Å | Highest resolution overall; PIP-box bound |
| 5 | 8F5Q | 1.9 Å | PCNA + PIP box, high resolution |
| 6 | 9N3L | 1.9 Å | **Novel inhibitor (HSP90alpha inh.)** — check if cryptic site |
| 7 | 1AXC | 2.6 Å | PIP-box complex; structural diversity |
| 8 | 2ZVL/2ZVM | 2.3–2.5 Å | DNA polymerase κ/ι complexes |

### Key observations
- **Dataset is interface-biased**: most holo structures are PIP-box bound (IDCL interface), not the AOH1996 cryptic site — good for negative controls but careful with labeling
- **9N3L is a new lead**: HSP90alpha inhibitor bound — not AOH1996 — could be a second cryptic pocket; worth investigating
- **Data augmentation possible**: PCNA homotrimer (chains A/B/C) → each structure gives 3 training examples
- **CryptoSite set is robust**: 87 proteins spanning diverse fold families → strong pre-training signal
- **No existing PCNA cryptic pocket dataset**: 8GLA remains the only PCNA-specific positive example; pre-training on CryptoSite is non-negotiable

### Verification layer results
- Resolution filter (> 3.5Å): caught `2C32` (7.0Å), `3BYH` (12.0Å) — correctly excluded from training set
- Cα completeness (< 90%): caught `1H8A` (82%), `2DR2` (83%) — backbone incomplete, would break graph construction
- 404 errors: `1DLN`, `1NRY` — obsolete PDB entries (superseded); not needed
- 8GLA kept despite 3.77Å — is ground truth, exception hardcoded in `fetch_structures.py`

### Infrastructure standing up
- `src/data_processing/fetch_structures.py` implemented (Stage 1 pipeline)
- `agents/pcna_crawler.py` live — RCSB + UniProt + web crawl modes
- CrypticGNN forward pass verified: input `(N, 26)` → output `(N,)` in [0,1]
- PyTorch Geometric 2.7.0 + torch 2.10 CPU confirmed working
- Ollama running: `gpt-oss:20b`, `llama3`, `llama3.2` available; CPU-only (Intel Arc not used on Windows)

### Next priority (unblocked)
1. Implement `parse_pdb.py` (stubs exist, fetch_structures strips the files)
2. Implement `graph_construction.py` (depends on parse_pdb)
3. Implement `loss.py` + `dataset.py` + `train.py`
4. Run E001 (baseline GNN on CryptoSite) — 87 structures now available

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

---

## Related

[[paper_notes]] · [[BIOLOGY_PCNA]] · [[RESEARCH_QUESTION]] · [[EXPERIMENT_INDEX]] · [[KNOWN_LIMITATIONS]]
