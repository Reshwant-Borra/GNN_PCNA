---
type: parallel-track-handoff
date: 2026-05-28
author: Reshwant-Borra
status: authorized
---

# Friend Parallel Track — What You Can Build While Phase 3 Runs

Reshwant is handling Phase 3 training, baselines execution, model freeze, and test
evaluation himself. This document defines everything you can build **in parallel**
that will slot directly into the project when Phase 3 completes.

**Everything listed here is implementable from the GitHub repo alone.**
No graph tensors, no CIF files, no checkpoints are needed. All tasks are pure code
with synthetic/mock data tests.

---

## What Is and Is Not on the Repo

| Artifact | On GitHub? | Notes |
|---|---|---|
| All `src/` code | YES | Full Phase 3 pipeline |
| All `docs/scientific_governance/` | YES | Binding rules — read before touching anything |
| `.memory/PROJECT_STATE.md` | YES | Start here every session |
| `data/registries/*.json` | YES | Split manifest, label manifest, dataset index |
| `reports/phase3/training_runs/*.json` | YES | 12 training manifests with results |
| `tests/phase3/` | YES | Existing test suite (93 passing) |
| `data/graphs/*.npz` | **NO** | Gitignored (176 MB); Reshwant has locally |
| `data/raw_intake/` | **NO** | Gitignored; CIF files for structural tools |
| `checkpoints/phase3/*.pt` | **NO** | Gitignored; model weights |

---

## Startup Sequence (every session)

```
1. Read .memory/PROJECT_STATE.md
2. Read docs/scientific_governance/16_CODING_AGENT_RULES.md   ← always first
3. Read docs/scientific_governance/00_COMPACT_INDEX.md
4. Run existing tests to confirm nothing is broken:
   PYTHONPATH=src python -m pytest tests/ -v
```

---

## Dependencies to Install

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install torch_geometric
pip install scikit-learn numpy scipy matplotlib seaborn
pip install biopython        # for solvent-accessibility baseline
```

If on GPU: install the CUDA-compatible torch and torch_geometric versions instead.
Verify with: `python -c "import torch_geometric; print(torch_geometric.__version__)"`.

---

## Track A — Alternative GNN Architectures (highest priority)

Reshwant will run these on the frozen split once implemented. Your job is to write
the code and tests; do not run training.

**Governance:** `docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md`,
`docs/scientific_governance/16_CODING_AGENT_RULES.md`

### A1 — GCN-1L (`src/phase3_model/gcn.py`)

Single-layer GCN (GCNConv). Must satisfy the same `ModelInterface` as `GraphSAGE3L`:
- Input: 25-dim node features, edge_index
- Output: (N,) raw logits — **no sigmoid**
- `hidden_dim` locked to {64, 128}; raise ValueError otherwise
- `ModelOutputContract` field set to same contract as GNN (see `src/phase3_model/interfaces.py`)
- Batch-isolated: no global pooling across proteins in a batch

```python
# Target signature
class GCN1L(nn.Module):
    def __init__(self, hidden_dim: int = 128, dropout: float = 0.1): ...
    def forward(self, data) -> torch.Tensor: ...  # (N,) logits, no sigmoid
```

**Tests:** `tests/phase3/test_gcn_gat.py`
- hidden_dim validation (64 ok, 128 ok, 32 raises ValueError)
- forward shape: output is (N,), no extra dims
- batch isolation: same tolerance as existing test (atol=1e-5) with dropout=0.0
- no NaN in output on random input

### A2 — GAT-2L (`src/phase3_model/gat.py`)

Two-layer GAT (GATConv, 4 attention heads). Same interface contract as above.

```python
class GAT2L(nn.Module):
    def __init__(self, hidden_dim: int = 128, dropout: float = 0.1, heads: int = 4): ...
    def forward(self, data) -> torch.Tensor: ...  # (N,) logits, no sigmoid
```

Note: with multi-head attention, manage the feature dimension carefully so the final
head still maps to 1 output logit. `hidden_dim` refers to per-head dim; total
intermediate dim = hidden_dim * heads.

**Tests:** same file `tests/phase3/test_gcn_gat.py` — same four checks.

### A3 — No-Edge-Type Ablation (`src/phase3_model/gnn_no_edge_type.py`)

GraphSAGE-3L but treating all edges identically (ignoring `edge_type`). Identical
architecture to `GraphSAGE3L` in `src/phase3_model/gnn.py` except `edge_type` is
not used. The purpose is to measure how much sequential vs. spatial edge typing
contributes to performance.

**Tests:** same file, check that output is identical shape and contract.

---

## Track B — Baseline Method Wrappers

Write the wrapper code and parsing logic. Do NOT run the tools (no CIF files on disk).
Each wrapper must implement the interface in `src/baselines/interfaces.py` and return
per-residue scores in the same format as `compute_metrics_from_lists()`.

**Governance:** `docs/scientific_governance/10_BASELINE_REQUIREMENTS.md`

Output format for all baselines: `list[tuple[list[float], list[int]]]` — one entry
per protein, each entry is (scores, labels) matching the `loss_mask=True` residues.

### B1 — Random Baseline (`src/baselines/random_baseline.py`)

Uniform random score in [0, 1] per residue. Seeded for reproducibility.

```python
def random_baseline(protein_data_list, seed=42) -> list[tuple[list[float], list[int]]]:
    ...
```

Tests: output shape matches input, same seed = same output, different seed = different.

### B2 — Solvent Accessibility Baseline (`src/baselines/solvent_exposure.py`)

Use BioPython's `HSExposureCB` or DSSP wrapper to compute relative solvent
accessibility (RSA) per residue from a CIF/PDB file. Higher RSA = more exposed =
higher baseline score.

The wrapper should accept a path to a CIF file and return a dict mapping
`(chain_id, residue_seq_id)` → RSA float, matching the same residue keying used in
`src/phase3_data/graph_loader.py`.

Write with mock CIF data for tests. Actual execution will happen on Reshwant's machine.

### B3 — fpocket Wrapper (`src/baselines/fpocket_wrapper.py`)

Parse fpocket's `*_info.txt` and `*_pockets.pqr` output to extract per-residue
pocket membership scores. fpocket assigns residues to pockets with a druggability score.

The wrapper should:
1. Accept a path to fpocket output directory
2. Parse all pocket files
3. Return per-residue scores (max pocket score across all pockets a residue belongs to)
4. Return 0.0 for residues not in any pocket

Tests: write a mock fpocket output directory with synthetic data, parse it, verify
correct residue scores.

### B4 — P2Rank Wrapper (`src/baselines/p2rank_wrapper.py`)

Parse P2Rank's `*.csv` prediction output. P2Rank assigns each residue a pocket
probability score.

Tests: same pattern — mock CSV, parse, verify.

### B5 — PocketMiner Wrapper (`src/baselines/pocketminer_wrapper.py`)

PocketMiner outputs per-residue cryptic pocket probabilities in a JSON or CSV.
Parse the output and map to our residue keying.

Tests: mock output, parse, verify.

---

## Track C — Visualization and Analysis Scripts

These use the training manifests **already on GitHub** in
`reports/phase3/training_runs/`. No graph tensors needed.

**Governance:** `docs/scientific_governance/09_EVALUATION_PROTOCOL.md`

### C1 — Training Curve Plotter (`scripts/plot_training_curves.py`)

Load all 12 `fold*_seed*_manifest.json` files. For each run, plot val_macro_auprc
vs. epoch from the `history` list. Output: one figure per fold showing all 3 seeds.

```
python scripts/plot_training_curves.py --out-dir reports/phase3/figures/
```

Dependencies: matplotlib, seaborn.

### C2 — Cross-Fold Summary Plot (`scripts/plot_fold_summary.py`)

Box-and-whisker across folds. Scatter of all 12 run AUPRCs. Output one summary figure.

### C3 — Training Results Analysis (`scripts/analyze_training_results.py`)

Statistical summary from manifests:
- Mean ± SD per fold (already in the summarize script; extend it)
- Seed variance vs. fold variance (is most variance within-fold or between-fold?)
- Correlation between best_epoch and val_macro_auprc
- Print to stdout and optionally write to `reports/phase3/training_analysis.md`

No governance doc required for this — it's descriptive analysis of committed results.

---

## Track D — Phase 4 Inference Pipeline Scaffold

Build the inference entry point for when Phase 3 completes and the model is frozen.
This is a scaffold; it must run in **dry-run mode** (no real checkpoint needed for
tests) but be immediately usable once Reshwant provides the frozen checkpoint path.

**Governance:** `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`,
`docs/scientific_governance/14_CLAIM_POLICY.md`

### D1 — Inference Runner (`src/phase4_inference/runner.py`)

```python
def run_inference(
    checkpoint_path: Path,
    graph_dir: Path,
    pdb_ids: list[str],
    output_dir: Path,
    dry_run: bool = True,
) -> dict:
    """Load frozen model, run predictions on given pdb_ids, write per-residue scores.

    dry_run=True: validates paths and config but does not load weights or run forward.
    dry_run=False: requires Phase 3 model freeze human gate before running.
    """
```

Output format: one JSON per protein with residue-level prediction scores and provenance
(checkpoint path, pdb_id, model config, date, no_scientific_claims=True).

### D2 — PCNA Inference Gate (`src/phase4_inference/pcna_gate.py`)

A gate that refuses to produce PCNA inference output until a human-signed PCNA gate
record exists at `reports/phase4/pcna_inference_gate_YYYYMMDD.md`. Mirror the pattern
in `src/phase3_training/gates.py`.

```python
class PCNAGateError(RuntimeError): ...

def pcna_gate_status(human_pcna_signoff: Path | None) -> dict: ...
```

Tests: raises without signoff file, passes with a mock signoff file.

---

## Hard Rules — Apply to Everything You Write

These are binding regardless of what seems reasonable:

1. **No training.** Do not call `train_one_run()` or any optimizer. Write tests with
   `model.eval()` and random tensors only.

2. **No test-set evaluation.** Never call `load_split(..., "test", ...)`.

3. **No scientific claims.** Do not write strings like "GCN outperforms" or
   "baseline fails" in code, comments, or reports.

4. **No sigmoid in model forward.** BCEWithLogitsLoss handles it.
   `ModelOutputContract` must reflect this.

5. **Mock data for tests.** Construct synthetic `torch_geometric.data.Data` objects
   in tests — do not load from `data/graphs/` (not on your machine).

6. **Run full test suite before any commit:**
   ```
   PYTHONPATH=src python -m pytest tests/ -v
   ```
   All 93 existing tests must still pass. Add new tests for every new module.

7. **Do not touch:** `CLAUDE.md`, `AGENTS.md`, `.memory/INDEX.md`,
   `.memory/MEMORY_RULES.md`, `docs/scientific_governance/`, `wiki/index.md`

---

## What to Commit

- New `src/` files under `phase3_model/`, `baselines/`, `phase4_inference/`
- New `scripts/plot_*.py` and `scripts/analyze_*.py`
- New `tests/phase3/test_gcn_gat.py` and `tests/baselines/`
- Update `wiki/log.md` with a dated entry for each durable decision
- Update `.memory/PROJECT_STATE.md` under "What Is Done" at session end

Do **not** commit: anything in `data/graphs/`, `data/raw_intake/`, `checkpoints/`.

---

## How This Slots Into Phase 3 When Reshwant Is Ready

| Your artifact | How Reshwant uses it |
|---|---|
| `src/phase3_model/gcn.py` | Drops into `run_all_training.py` with `--model gcn` |
| `src/phase3_model/gat.py` | Same |
| `src/phase3_model/gnn_no_edge_type.py` | Same |
| `src/baselines/` wrappers | Reshwant runs external tools, feeds output to wrappers |
| `scripts/plot_training_curves.py` | Reshwant runs once to generate figures |
| `src/phase4_inference/runner.py` | Used immediately after model freeze |
| `src/phase4_inference/pcna_gate.py` | Blocks PCNA inference until Reshwant signs |
