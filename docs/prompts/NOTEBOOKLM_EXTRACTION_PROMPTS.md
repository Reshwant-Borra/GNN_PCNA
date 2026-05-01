# NOTEBOOKLM_EXTRACTION_PROMPTS.md — Reusable NotebookLM Prompts

> Paste these into NotebookLM after loading the relevant paper as a source.
> Save outputs to docs/notebooklm/distilled_notes/.

---

## Extract Method Architecture

```
Extract the exact model architecture described in this paper.

Format as bullet points:
- Architecture type: (GNN / CNN / transformer / etc.)
- Layer type(s): (GCN / GAT / GIN / etc.)
- Number of layers: ...
- Hidden dimension: ...
- Input features (node): ...
- Input features (edge): ...
- Output: ...
- Activation functions: ...
- Pooling strategy: ...
- Loss function: ...
- Optimizer + learning rate: ...
- Key hyperparameters: ...

Only use information from the loaded source.
Do not speculate. Cite the section number for each claim (e.g., "Section 3.1").
Mark anything not stated in the paper as "Not stated."
```

---

## Extract Dataset Details

```
Extract all dataset information from this paper.

Format as bullet points:
- Dataset name(s): ...
- Number of proteins: ...
- Number of protein pairs (apo/holo): ...
- Source of dataset: ...
- Availability: (publicly available / contact authors / not available)
- Train / validation / test split: ...
- Positive examples: ...
- Negative examples: ...
- Any preprocessing described: ...

Only use information from the loaded source.
Do not speculate. Cite the section for each claim.
Mark anything not stated as "Not stated."
```

---

## Extract Evaluation Metrics

```
Extract all quantitative results and evaluation metrics from this paper.

Format as a markdown table:
| Metric | Value | Dataset | Compared against | Notes |

Include:
- Primary reported metrics (AUROC, AUPRC, accuracy, F1, etc.)
- Baseline comparisons
- Ablation study results (if any)
- Statistical significance (if reported)

Only use information from the loaded source.
Do not speculate. Cite the table/figure number for each result.
```

---

## Extract Limitations

```
List all limitations of the method described in this paper.

Format as bullet points, in two sections:

## Limitations stated by authors:
- ...

## Potential limitations not stated (from your reading):
- ...

For the "stated by authors" section: cite the exact section or phrase from the paper.
For "potential limitations": mark clearly as your interpretation.
Keep each bullet under 25 words.
```

---

## Compare Two Papers

```
Compare these two papers loaded as sources in this notebook.

Format as a comparison table:
| Dimension | Paper 1: {name} | Paper 2: {name} |
|---|---|---|
| Task | | |
| Architecture type | | |
| Layer type | | |
| Input features | | |
| Dataset | | |
| Primary metric (AUROC) | | |
| Key limitation | | |
| Applicability to homotrimers | | |
| Code availability | | |
| Relevance to PCNA | | |

Only use information from the loaded sources.
Mark anything not stated as "Not stated."
```

---

## Produce Obsidian-Ready Summary

```
Summarize this paper as compact bullet-point notes for a research knowledge base.

Format exactly as:

## Method
- [max 5 bullets, each under 20 words]

## Dataset
- [max 5 bullets]

## Key Results
- [max 5 bullets]

## Limitations
- [max 5 bullets]

## Relevance to GNN-PCNA cryptic pocket prediction
- [max 5 bullets]

Rules:
- One claim per bullet
- Under 20 words per bullet
- No speculation — only what the paper states
- No paragraphs — bullets only
- Cite figure/table/section for any quantitative claim
```

---

## Extract PCNA Biology Facts

```
Extract all information about PCNA (Proliferating Cell Nuclear Antigen) from this source.

Format as bullet points organized by category:

## Structure
- ...

## Function
- ...

## AOH1996 binding site
- Binding residues: ...
- Binding pocket region: ...
- Pocket geometry: ...
- Affinity (Kd or IC50): ...

## Cancer relevance
- ...

## Published MD or dynamics studies
- ...

Only use information from the loaded source.
Mark anything not stated as "Not stated."
```
