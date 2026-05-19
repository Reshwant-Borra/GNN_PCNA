# BIOLOGY_PCNA.md — PCNA Biology Context

→ Links: [[SYSTEM_OVERVIEW]] | [[DATASETS]] | [[VALIDATION]] | [[MODELS]]

---

## PCNA as a Molecular Clamp

| Property | Detail |
|---|---|
| Full name | Proliferating Cell Nuclear Antigen |
| Function | Homotrimeric sliding clamp for DNA polymerase δ/ε during replication |
| Scaffold role | Recruits DNA repair, replication, and chromatin factors via PIP-box motif |
| Structure | 3 identical subunits (~29 kDa each), total ~87 kDa ring |
| Symmetry | C3 homotrimer — all 3 chains nearly identical |
| Key interface | Subunit-subunit interface at the IDCL (Interdomain Connecting Loop) |
| PDB apo | 1W60 (human, 2.35 Å, no ligand) |
| PDB holo | 8GLA (human, AOH1996 derivative AOH1996-1LE (ligand ZQZ) bound, resolution 3.77 A, chains A-D in asymmetric unit) |

---

## Why PCNA Is Difficult to Drug

- **No obvious deep pocket** in the apo crystal structure — flat ring topology
- PIP-box interface is broad and shallow — hard to target with small molecules
- Homotrimer symmetry: any inhibitor must disrupt function of all 3 subunits
- Prior attempts focused on PIP-box blockade — high required concentration
- **Cryptic pockets** offer a solution: sites that open dynamically, invisible in apo structure

---

## AOH1996 — Known PCNA Inhibitor

| Property | Detail |
|---|---|
| Drug name | AOH1996 |
| Developer | City of Hope (~2023) |
| Mechanism | Disrupts PCNA-dependent DNA repair and replication in cancer cells |
| Binding site | IDCL region — a cryptic site not visible in 1W60 |
| PDB structure | 8GLA — shows AOH1996 derivative (ZQZ/AOH1996-1LE) bound |
| Site geometry | Needs NotebookLM extraction — exact residue contacts TBD |
| Selectivity | Cancer cells over-express PCNA; normal cells less affected |

**Why this matters for us:**
- The AOH1996 binding site is our **positive control** and **ground truth pocket**
- We must recover this site before trusting any novel prediction
- Labeling: residues within 6 Å of AOH1996 in 8GLA = positive class

---

## ATX-101

- Another PCNA-targeting molecule (distinct from AOH1996)
- Mechanism: Needs NotebookLM extraction
- Binding site geometry vs. AOH1996: Needs NotebookLM extraction
- Relevant if we want a second known-pocket positive control

---

## Known Pocket / Interface Regions to Watch

| Region | Description | Cryptic? |
|---|---|---|
| IDCL (Glu119–Lys164) | Interdomain connecting loop; AOH1996 binds here | Yes — confirmed |
| PIP-box interface | Binds PIP-box peptides (p21, FEN1, etc.) | No — visible in apo |
| Subunit-subunit interface | Between chains A–B, B–C, C–A | Possibly — DeepAllo relevant |
| Back face (opposite PIP) | Less studied | Unknown — needs analysis |

---

## Crystal Contacts in 1W60 (Important Caveat)

- 1W60 is a crystal structure — lattice packing may occlude surface residues
- Crystal contacts might mask regions that are accessible in solution
- Must flag pocket candidates near crystal contact regions
- Needs verification: which residues in 1W60 are in crystal contact?
- → This is a data processing concern; see [[PIPELINE]] Stage 1

---

## What Needs NotebookLM Extraction

- [ ] Exact AOH1996 binding residues in 8GLA (from original paper)
- [ ] ATX-101 binding site geometry
- [ ] IC50 / binding affinity of AOH1996
- [ ] PCNA cancer overexpression data (cell lines, fold change)
- [ ] Crystal contact residues in 1W60
- [ ] Any other known cryptic sites on PCNA from literature
- [ ] IDCL dynamics from prior MD studies (if any)

See `docs/notebooklm/distilled_notes/pcna_biology_notes.md` for extracted facts.
