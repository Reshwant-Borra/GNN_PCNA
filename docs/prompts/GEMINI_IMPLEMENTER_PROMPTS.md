# GEMINI_IMPLEMENTER_PROMPTS.md — Reusable Gemini Implementation Prompts

---

## Standard Implementation Prompt

```
You are a senior Python engineer implementing code for a GNN-based cryptic pocket prediction system.

Project: GNN-PCNA
Stack: Python 3.10+, PyTorch Geometric, MDAnalysis, BioPython, numpy, scipy, scikit-learn

Project context — read carefully:
[paste docs/knowledge/SYSTEM_OVERVIEW.md]

Relevant pipeline stage:
[paste relevant section of docs/knowledge/PIPELINE.md]

File to implement: src/{path/to/file.py}

Current stub — preserve ALL function signatures, docstrings, and type hints:
[paste full stub]

Implementation requirements:
- Python type hints on all public functions
- No placeholder TODOs or raise NotImplementedError — implement fully
- Handle PCNA homotrimer: chains A, B, C; ~261 residues per chain
- Document tensor shapes in docstrings (e.g., "Returns: (N,) float32")
- Do NOT change function signatures
- Do NOT add new public functions unless explicitly listed
- Follow existing import style and dataclass definitions
- Handle edge cases listed below

Edge cases to handle:
[paste risks from Claude plan]

Implementation steps (follow in order):
[paste implementation steps from Claude plan]

Return:
1. Complete implemented file (entire file, not just changes)
2. One-paragraph change summary
3. Any assumptions made that Claude should verify
```

---

## Debug / Fix Prompt

```
You are debugging a Python implementation for GNN-PCNA cryptic pocket prediction.

Error:
[paste full traceback]

File causing the error:
[paste full file content]

Known context:
- PCNA graph: ~800 nodes (trimer) or ~267 (monomer)
- Edge features: (E, 2) — distance + seq_separation (float32)
- Node features: (N, 26) — float32
- edge_index: (2, E) — long tensor
- All data is on the same device (CPU or CUDA)

Steps:
1. Identify the exact root cause (not just the symptom)
2. Provide the minimal targeted fix (not a rewrite)
3. Explain why the fix works

Do NOT redesign the function unless the current approach is fundamentally broken.
Return: fixed function + one-line explanation.
```

---

## Test Implementation Prompt

```
Write unit tests for the following Python file in the GNN-PCNA project.

File: src/{path/to/file.py}
[paste file content]

Test requirements:
- Use pytest
- No mocking of core computation (BioPython, MDAnalysis, PyTorch)
- Test each public function with at least 3 test cases:
  1. Happy path (normal input)
  2. Edge case (empty input, single residue, very large graph)
  3. Error case (invalid input should raise with clear message)
- Use synthetic/in-memory data where possible (no external file dependencies)
- Include a smoke test for the GNN forward pass with random tensors

Known failure modes from KNOWN_BUGS.md:
[paste KNOWN_BUGS.md]

Return: complete test file at tests/test_{filename}.py
```

---

## Multi-File Implementation Prompt

```
You are implementing multiple related files for GNN-PCNA.

Context:
[paste SYSTEM_OVERVIEW.md]

Files to implement (in order — later files depend on earlier ones):

File 1: src/{path/file1.py}
[paste stub 1]

File 2: src/{path/file2.py}
[paste stub 2]

Requirements (all files):
- Python 3.10+ type hints
- Fully implemented (no TODOs)
- Handle PCNA homotrimer (chains A, B, C)
- Shape-documented docstrings

Return:
- File 1: complete implementation
- File 2: complete implementation
- Change summary for both
```

---

## Related

[[AI_WORKFLOW_RULES]] · [[AGENTS]] · [[plan_template]] · [[KNOWN_BUGS]] · [[FILE_GUIDE]]
