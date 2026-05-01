# Prompts

## Claude — Planning & Architecture

### System Context Injection
```
You are a computational biology engineer working on GNN-based cryptic pocket detection for PCNA.

Context:
- Target: PCNA (PDB 1W60 apo, 8GLA holo with AOH1996)
- Ground truth pocket: residues within 6 Å of AOH1996 in 8GLA
- Stack: PyTorch Geometric, MDAnalysis, BioPython
- Goal: per-residue cryptic pocket probability

Pipeline stages:
1. PDB → residue graph (nodes: residues, edges: Cα–Cα < 8 Å)
2. GATv2Conv GNN (4 layers, 256 hidden, 4 heads)
3. MLP scoring head → sigmoid → P(pocket)
4. MD validation: RMSF + DCCM + volume tracking

Read docs/knowledge/ for full context before proceeding.
```

### Architecture Decision Prompt
```
Given the pipeline in PIPELINE.md and constraints in KNOWN_LIMITATIONS.md,
propose the [specific component] design. Consider:
- Input/output tensor shapes
- Edge cases in PCNA's homotrimeric structure
- How this component connects to upstream/downstream stages
Return: design decision + rationale + 3 alternatives considered.
```

---

## Gemini — Implementation

### Full File Generation
```
Implement the following Python file for the GNN-PCNA project.

Project context:
[paste SYSTEM_OVERVIEW.md]
[paste PIPELINE.md relevant stage]

File to implement: src/[path/to/file.py]
Stub (preserve function signatures):
[paste stub]

Requirements:
- PyTorch Geometric compatible
- Type hints on all functions
- No placeholder TODOs — implement fully
- Handle PCNA homotrimer (chains A, B, C) correctly
- Return shapes documented in docstrings
```

### Debug Prompt
```
Debug this error in the GNN-PCNA project:

Error:
[paste traceback]

File:
[paste file]

Known context:
- PCNA graph has ~800 nodes (trimer) or ~267 (monomer)
- Edge features: [distance, seq_separation] shape (E, 2)
- Node features: shape (N, 26)
Identify the root cause and provide a minimal fix.
```

---

## ChatGPT — Review

### Code Review
```
Review this Python implementation for a GNN-based protein pocket detector.

Focus on:
1. Off-by-one errors in graph construction
2. Data leakage (are train/val/test splits protein-level, not residue-level?)
3. Label imbalance handling (focal loss or weighted BCE correct?)
4. PyTorch Geometric API misuse
5. MD analysis assumptions (RMSF normalization, DCCM symmetry)

Code:
[paste implementation]

Known issues to check: [paste KNOWN_BUGS.md]
```

### Hypothesis Review
```
Evaluate this experimental hypothesis for PCNA cryptic pocket detection:

Hypothesis: [state hypothesis]

Critique from the perspective of:
1. Structural biology (is this physically plausible?)
2. ML validity (does the training setup support testing this?)
3. Statistical power (is the validation set sufficient?)
4. Alternative explanations

Be concise. Flag the single most critical flaw if one exists.
```
