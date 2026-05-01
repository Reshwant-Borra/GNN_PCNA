# TESTING.md — Test Strategy

→ Links: [[VALIDATION]] | [[FILE_GUIDE]] | [[COMMANDS]]

---

## Testing Philosophy

- Tests verify code correctness, not scientific validity.
- Scientific validity is verified through experiments (see `docs/experiments/`).
- Use pytest. No mocking of core computation (MDAnalysis, BioPython).
- Test at function level, not class level — keep tests small and targeted.

---

## Test Layers

### Layer 1 — Unit Tests (per function)

| Test | Target | What to check |
|---|---|---|
| `test_parse_pdb` | `parse_pdb.parse_pdb()` | Correct residue count for 1W60 (expect ~261 per chain) |
| `test_strip_heteroatoms` | `parse_pdb.strip_heteroatoms()` | No HETATM in output except keep_resname |
| `test_standardize_chains` | `parse_pdb.standardize_chains()` | Chains renamed to A, B, C |
| `test_label_pocket_residues` | `parse_pdb.label_pocket_residues()` | Label fraction ~0.05–0.15 for 8GLA |
| `test_build_graph_shapes` | `graph_construction.build_graph()` | x=(N,26), edge_attr=(E,2), edge_index=(2,E) |
| `test_gnn_forward` | `CrypticGNN.forward()` | Output shape (N,), values in [0,1] |
| `test_focal_loss` | `loss.py` | Loss = 0 for perfect prediction, > 0 for wrong |

### Layer 2 — Integration Tests

| Test | What to check |
|---|---|
| Full pipeline on 1W60 (apo) | No exceptions; sensible output shapes |
| Full pipeline on 8GLA (holo, labeled) | Label fraction OK; training step runs |
| Forward pass on random PCNA-sized graph | Output range [0,1]; no NaN |

### Layer 3 — Scientific Validation (not automated)

| Test | How to validate |
|---|---|
| Positive control: recover 8GLA pocket | Run E002; check pocket rank ≤ 3 |
| RMSF threshold | Run E003; compare pocket vs. background RMSF |
| Data leakage check | Confirm split is protein-level (manual inspection) |

---

## Test File Locations (to create)

```
tests/
├── test_parse_pdb.py
├── test_graph_construction.py
├── test_cryptic_gnn.py
├── test_focal_loss.py
└── test_integration.py
```

---

## How to Run Tests (Needs verification)

```bash
# All tests
pytest tests/ -v

# Single test file
pytest tests/test_cryptic_gnn.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

---

## GNN Forward Pass Smoke Test (no data needed)

```python
import torch
from src.models.cryptic_gnn import CrypticGNN

def test_gnn_forward():
    model = CrypticGNN()
    N, E = 267, 2000
    x = torch.randn(N, 26)
    edge_index = torch.randint(0, N, (2, E))
    edge_attr = torch.randn(E, 2)
    scores = model(x, edge_index, edge_attr)
    assert scores.shape == (N,)
    assert scores.min() >= 0.0
    assert scores.max() <= 1.0
    assert not torch.isnan(scores).any()
```

---

## How Gemini Should Use This

When implementing any `src/` file, also implement the corresponding unit test stub.
Gemini should return: implementation + test file with at least 3 tests per function.

## How ChatGPT Should Use This

When reviewing, check:
1. Does the test cover the edge case (empty graph, single-residue chain, very long chain)?
2. Is the test actually testing the right thing (not just checking it runs without error)?
3. Is there risk of data leakage in the test fixtures?
