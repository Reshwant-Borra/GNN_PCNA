# Friend Crawl — Summary Statistics
**Date:** 2026-05-27
**Source archive:** GNN_PNCA_crawled_data.zip
**Crawler version:** 2.0-multidomain

---

## 1. Structure Counts by Source

| Source | Count |
|---|---|
| RCSB PDB (experimental) | 72 |
| AlphaFold predicted | 0 |
| **Total PDB files on disk** | **149** |

Note: This crawl is PCNA-focused (UniProt P12004 and PCNA-interacting partners), not a generic
proteome sweep. The ~20,000 AlphaFold / ~23,771 mmCIF description in PROJECT_STATE.md refers to
a larger planned crawl; this archive contains the current PCNA-specific subset.

---

## 2. AlphaFold vs Experimental

| Category | Count |
|---|---|
| Experimental (X-ray / cryo-EM) | 72 |
| AlphaFold predicted | 0 |

---

## 3. Resolution Distribution (experimental structures, n=72)

| Bucket | Count |
|---|---|
| <1.5Å | 0 |
| 1.5–2.0Å | 5 |
| 2.0–2.5Å | 14 |
| 2.5–3.0Å | 25 |
| >3.0Å | 28 |

- Mean: 2.79Å
- Median: 2.84Å
- Min: 1.88Å
- Max: 3.77Å

---

## 4. Chain Count Distribution

| Chain Count | Structures |
|---|---|
| 1 chain | 2 |
| 2 chains | 5 |
| 3 chains | 6 |
| 4+ chains | 59 |

Note: PCNA is a homotrimeric ring; most structures have 6 chains (two trimers per asymmetric unit)
or 3 chains (one trimer), which explains the high 4+ count.

---

## 5. Ligand Presence

| | Count |
|---|---|
| Structures with HETATM records | 63 |
| Structures without HETATM | 9 |

Note: HETATM includes water molecules and ions in addition to true ligands; ligand_ids were not
individually parsed in this crawl pass — field is  for all records.

---

## 6. Confidence Score Distribution (AlphaFold pLDDT)

No AlphaFold structures present in this crawl. Section not applicable.

---

## 7. Missing Residue Rate

Missing residue counts were not extracted in this crawl pass; field is  for all records.
CA-completeness is available: 55 / 72 structures have CA completeness = 1.0.

---

## 8. Parsed Features

| | Count |
|---|---|
| Structures with ESM-2 embeddings (.npy) | 146 |
| % of total PDB structures | 202% |

Feature type: ESM-2 per-residue embeddings, shape (N_residues, 480), float32.

---

## 9. Duplicate PDB ID Count

0 duplicate PDB IDs detected across the 72 catalog records.

---

## 10. Estimated Storage Breakdown

| Component | Size |
|---|---|
| Raw PDB files | 114.9 MB |
| ESM-2 feature arrays | 227.4 MB |
| Graphs (.pt) | — |
| Research papers (HTML/PDF) | — |
| **Total archive** | **5.68 GB** |

---

## 11. PCNA-Specific Coverage

| | Count |
|---|---|
| UniProt P12004 confirmed | 65 |
| Other (PCNA-interacting, non-P12004) | 7 |
| Known PCNA structures from prompt targets found | 5 (1AXC, 1W60, 1VYM, 1VYJ, 6GIS) |

---

## 12. Anomalies and Flags

- **No AlphaFold structures:** This crawl predates integration of AlphaFold predictions.
- **No sub-1.5Å structures:** Lowest resolution is 1.88Å (1U7B).
- **Ligand IDs not parsed:** HETATM presence confirmed but individual ligand codes not extracted.
- **Missing residue counts not extracted:** CA completeness used as proxy.
- **6 structures failed fetch_session validation** (not in registry).
- **5e0v and 3vkx present:** These are the PCNA contamination records identified in the CryptoBench audit; they are correctly included here as PCNA structures.
