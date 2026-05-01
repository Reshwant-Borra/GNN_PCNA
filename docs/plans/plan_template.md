# Plan: {Task Name}

**Date:** YYYY-MM-DD
**Status:** draft | approved | in_progress | done
**Experiment:** E{NNN} (if applicable)

---

## Goal

_One sentence: what will be built and what it enables._

---

## Brain Files Read

_List the docs/knowledge/ files Claude read to create this plan._

- `docs/knowledge/PIPELINE.md` — Stage {N}
- `docs/knowledge/MODELS.md`
- `docs/knowledge/DATASETS.md`

---

## Code Files to Inspect

_Files Gemini should read before implementing._

| File | Why |
|---|---|
| `src/path/to/stub.py` | Contains function signatures to implement |
| `src/models/cryptic_gnn.py` | Upstream dependency |

---

## Inputs

| Input | Type | Shape / Format | Source |
|---|---|---|---|
| PDB file path | `pathlib.Path` | — | `data/raw/` |
| Residue list | `list[Residue]` | — | `parse_pdb()` |

---

## Outputs

| Output | Type | Shape / Format | Destination |
|---|---|---|---|
| PyG Data object | `torch_geometric.data.Data` | x=(N,26), edge_index=(2,E) | `data/graphs/` |
| Labels | `np.ndarray` | (N,) float32 | `data/labels/` |

---

## Implementation Steps

1. **Step 1** — description
   - Detail a
   - Detail b

2. **Step 2** — description
   - Detail a

3. **Step 3** — description

---

## Risks / Edge Cases

| Risk | Mitigation |
|---|---|
| Missing Cα atoms (non-standard residues) | Skip residue; log warning |
| Empty chain | Raise ValueError with clear message |
| Distance cutoff produces disconnected graph | Check edge count > 0 before returning |
| PCNA chains not named A/B/C | Remap via `standardize_chains()` |

---

## Tests / Validation

| Test | Expected result |
|---|---|
| `test_parse_pdb` on 1W60 | ~261 residues per chain |
| Graph node shape | (N, 26) |
| Graph edge shape | (E, 2) |
| Label fraction on 8GLA | 0.05–0.15 |
| GNN forward pass on graph | (N,) scores in [0, 1] |

---

## === GEMINI TASK ===

```
Project: GNN-PCNA cryptic pocket prediction
Stack: PyTorch Geometric, MDAnalysis, BioPython, Python 3.10+

Context (read before implementing):
[paste SYSTEM_OVERVIEW.md]
[paste relevant PIPELINE.md stage]
[paste MODELS.md if relevant]

File to implement: src/{path/to/file.py}

Current stub (preserve ALL function signatures and docstrings):
[paste full stub content]

Requirements:
- Full Python type hints on all public functions
- No placeholder TODOs — implement completely
- Handle PCNA homotrimer (chains A, B, C)
- Document return shapes in docstrings
- Do NOT change function signatures
- Follow existing import style

Implementation steps to follow:
[paste numbered steps from above]

Edge cases to handle:
[paste risks from above]

Return: complete implemented file + one-paragraph change summary.
```

---

## === CHATGPT REVIEW TASK ===

```
Project: GNN-PCNA cryptic pocket prediction (Python, PyTorch Geometric)
Changed file: src/{path/to/file.py}

[paste complete changed file here]

Known bugs to check (from KNOWN_BUGS.md):
[paste KNOWN_BUGS.md]

Review checklist:
1. Off-by-one errors in residue/graph indexing
2. Data leakage — is train/val/test split at protein level, not residue level?
3. Label imbalance — is focal loss or weighted BCE applied correctly?
4. PyTorch Geometric API misuse (edge_index long dtype, edge_attr float)
5. BioPython / MDAnalysis API correctness
6. Scientific correctness — PCNA homotrimer assumptions (chains A/B/C, ~261 residues each)
7. Edge cases — empty chains, non-standard residues, disconnected graph

For each issue found:
- Severity: critical | warning | suggestion
- Location: line number or function name
- Description: what's wrong
- Fix: minimal correction

Return: numbered list of issues only. No redesign suggestions.
```
