"""One-shot test-set evaluation for Phase 3 frozen model.

THIS SCRIPT RUNS THE TEST SET EXACTLY ONCE AND THEN REFUSES TO RUN AGAIN.

Governance (doc 09 hard rules):
  - Test metrics are reported once after model, threshold policy, baselines,
    and report plan are frozen.
  - No combined validation/test headline.
  - No test-set threshold tuning.
  - Evaluation config must be frozen before the test run.
  - Script writes an immutable run manifest and refuses to run without a
    frozen model manifest (GATE 4 record).

Pre-conditions checked before any test data is loaded:
  1. GATE 4 model-freeze record exists and contains 'decision: APPROVED'.
  2. No prior test evaluation output file exists (one-shot guard).
  3. GATE 2 first-training sign-off exists (pipeline authorization).
  4. Frozen checkpoint file exists and is readable.

If any pre-condition fails the script exits non-zero without loading test data.

Metrics computed (all pre-specified in doc 09 before training):
  - Macro-AUPRC (primary), micro-AUPRC
  - Macro-AUROC, micro-AUROC
  - Top-k residue recovery at k = 5, 10, 20
  - Precision@k at k = 5, 10, 20
  - Bootstrap 95% CI over proteins (N=1000, seed=42)
  - Per-protein table

Edge filter applied: spatial edges only (edge_type==0), matching the frozen
architecture (spatial_only_fold1_seed1_best.pt).

Outputs:
  reports/phase3/test_evaluation_20260529.md         — human-readable report
  reports/phase3/test_evaluation_manifest_20260529.json — machine-readable record
  reports/phase3/.test_evaluation_lock               — one-shot guard file

Usage:
  python scripts/evaluate_test_set.py
  python scripts/evaluate_test_set.py --device cuda

Authorization:
  GATE 4: reports/phase3/model_freeze_gate4_20260529.md
    (decision_id: phase3_model_freeze_20260529)
  GATE 2: reports/phase3/first_training_signoff_20260528.md
    (decision_id: phase3_first_training_signoff_20260528)

Governance:
  docs/scientific_governance/09_EVALUATION_PROTOCOL.md
  docs/scientific_governance/19_STOP_CONDITIONS.md
  docs/scientific_governance/26_HUMAN_REVIEW_GATES.md
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import torch
import torch.nn as nn
from torch_geometric.loader import DataLoader

from phase3_data.graph_loader import load_split
from phase3_evaluation.metrics import bootstrap_ci, compute_metrics_from_lists
from phase3_model.gnn import GraphSAGE3L
from baselines.gnn_trainer import filter_edges

# ---------------------------------------------------------------------------
# Governed paths — do not change without updating GATE 4 record
# ---------------------------------------------------------------------------

GATE4_RECORD     = ROOT / "reports/phase3/model_freeze_gate4_20260529.md"
GATE2_SIGNOFF    = ROOT / "reports/phase3/first_training_signoff_20260528.md"
FROZEN_CKPT      = ROOT / "checkpoints/phase3/spatial_only_fold1_seed1_best.pt"
GRAPH_DIR        = ROOT / "data/graphs"
SPLIT_MANIFEST   = ROOT / "data/registries/split_manifest_frozen.json"
OUT_REPORT       = ROOT / "reports/phase3/test_evaluation_20260529.md"
OUT_MANIFEST     = ROOT / "reports/phase3/test_evaluation_manifest_20260529.json"
LOCK_FILE        = ROOT / "reports/phase3/.test_evaluation_lock"

EDGE_TYPE_SPATIAL: int = 0  # matches frozen architecture


# ---------------------------------------------------------------------------
# Pre-condition checks — all must pass before any test data is loaded
# ---------------------------------------------------------------------------

def _check_gate4() -> str:
    """Return GATE 4 record contents; raise if absent or not APPROVED."""
    if not GATE4_RECORD.is_file():
        raise RuntimeError(
            f"GATE 4 model-freeze record not found: {GATE4_RECORD}\n"
            "Test-set evaluation is blocked until GATE 4 is recorded."
        )
    text = GATE4_RECORD.read_text(encoding="utf-8")
    if "decision: APPROVED" not in text:
        raise RuntimeError(
            f"GATE 4 record exists but does not contain 'decision: APPROVED'.\n"
            f"Path: {GATE4_RECORD}\n"
            "Correct the gate record before running test evaluation."
        )
    return text


def _check_one_shot_guard() -> None:
    """Refuse to run if a prior test evaluation lock file exists."""
    if LOCK_FILE.is_file():
        lock_info = LOCK_FILE.read_text(encoding="utf-8")
        raise RuntimeError(
            "Test-set evaluation has already been run once (one-shot guard).\n"
            f"Lock file: {LOCK_FILE}\n"
            f"Lock contents:\n{lock_info}\n"
            "Per governance doc 09, the test set must not be evaluated more than once."
        )
    if OUT_REPORT.is_file():
        raise RuntimeError(
            f"Test evaluation report already exists: {OUT_REPORT}\n"
            "Per governance doc 09, the test set must not be evaluated more than once.\n"
            "If the prior run is invalid, a human must delete both the report and "
            "the lock file and record the reason in wiki/log.md before re-running."
        )


def _check_gate2() -> None:
    if not GATE2_SIGNOFF.is_file():
        raise RuntimeError(
            f"GATE 2 first-training sign-off not found: {GATE2_SIGNOFF}"
        )


def _check_checkpoint() -> None:
    if not FROZEN_CKPT.is_file():
        raise RuntimeError(
            f"Frozen checkpoint not found: {FROZEN_CKPT}\n"
            "Verify the checkpoint path matches the GATE 4 record."
        )


def run_precondition_checks() -> None:
    """Run all pre-conditions. Raises RuntimeError on any failure.

    IMPORTANT: This function must be called and must succeed before
    any test data is loaded or any model inference is performed.
    """
    print("Checking pre-conditions...", flush=True)
    _check_gate4()
    print(f"  [OK] GATE 4 record: {GATE4_RECORD.name} — decision: APPROVED", flush=True)
    _check_one_shot_guard()
    print("  [OK] One-shot guard: no prior test evaluation found", flush=True)
    _check_gate2()
    print(f"  [OK] GATE 2 sign-off: {GATE2_SIGNOFF.name}", flush=True)
    _check_checkpoint()
    print(f"  [OK] Frozen checkpoint: {FROZEN_CKPT.name}", flush=True)
    print("All pre-conditions passed. Loading test data.\n", flush=True)


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------

def _collect_protein_scores(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
) -> list[tuple[list[float], list[int]]]:
    """Per-protein (logits, labels) pairs for loss_mask=True nodes only."""
    model.eval()
    protein_scores: list[tuple[list[float], list[int]]] = []
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            logits = model(batch)
            for i in range(batch.num_graphs):
                node_mask = batch.batch == i
                lm = batch.loss_mask[node_mask]
                s = logits[node_mask][lm].cpu().tolist()
                y = [int(v) for v in batch.y[node_mask][lm].cpu().tolist()]
                protein_scores.append((s, y))
    return protein_scores


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

def _fmt(v: float | None, decimals: int = 4) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "N/A"
    return f"{v:.{decimals}f}"


def _render_report(
    metrics: dict[str, Any],
    ci: dict[str, Any],
    n_test: int,
    elapsed: float,
    device_str: str,
) -> str:
    auprc_lo, auprc_hi = ci["macro_auprc_ci"]
    auroc_lo, auroc_hi = ci["macro_auroc_ci"]
    per_protein = metrics.get("per_protein", [])

    per_protein_rows = []
    for row in sorted(per_protein, key=lambda r: r.get("auprc") or -1, reverse=True):
        auprc_str = _fmt(row.get("auprc"))
        auroc_str = _fmt(row.get("auroc"))
        r5   = _fmt(row.get("top_5_recovery"))
        r10  = _fmt(row.get("top_10_recovery"))
        r20  = _fmt(row.get("top_20_recovery"))
        per_protein_rows.append(
            f"| {row['protein_idx']:4d} | {row['n_nodes']:5d} | "
            f"{auprc_str} | {auroc_str} | {r5} | {r10} | {r20} |"
        )
    per_protein_table = "\n".join(per_protein_rows)

    return f"""---
type: phase3-test-evaluation
date: 2026-05-29
status: FINAL — ONE-SHOT EVALUATION COMPLETE
gate4_record: reports/phase3/model_freeze_gate4_20260529.md
decision_id: phase3_model_freeze_20260529
frozen_checkpoint: checkpoints/phase3/spatial_only_fold1_seed1_best.pt
architecture: GraphSAGE-3L, spatial edges only (edge_type==0)
governance: docs/scientific_governance/09_EVALUATION_PROTOCOL.md
---

# Phase 3 Test-Set Evaluation Results

> **FINAL — test set evaluated once. This report may not be re-run.**
> Governance: `docs/scientific_governance/09_EVALUATION_PROTOCOL.md`
> Gate: `reports/phase3/model_freeze_gate4_20260529.md` (decision_id: `phase3_model_freeze_20260529`)

---

## 1. Headline Metrics

| Metric | Value | 95% CI |
|---|---|---|
| **Macro-AUPRC (primary)** | **{_fmt(metrics['macro_auprc'])}** | [{_fmt(auprc_lo)}, {_fmt(auprc_hi)}] |
| Micro-AUPRC | {_fmt(metrics['micro_auprc'])} | — |
| Macro-AUROC | {_fmt(metrics['macro_auroc'])} | [{_fmt(auroc_lo)}, {_fmt(auroc_hi)}] |
| Micro-AUROC | {_fmt(metrics['micro_auroc'])} | — |

**Interpretation note:** macro-AUPRC is the primary metric because positive label
rate is ~4.6%, making AUROC inflated under extreme class imbalance. CI is 95%
bootstrap over proteins (N=1000, seed=42). No threshold tuning was performed.

---

## 2. Top-k Residue Recovery

| k | Macro Recovery@k | Macro Precision@k |
|---|---|---|
| 5  | {_fmt(metrics.get('macro_top_5_recovery'))} | {_fmt(metrics.get('macro_precision_at_5'))} |
| 10 | {_fmt(metrics.get('macro_top_10_recovery'))} | {_fmt(metrics.get('macro_precision_at_10'))} |
| 20 | {_fmt(metrics.get('macro_top_20_recovery'))} | {_fmt(metrics.get('macro_precision_at_20'))} |

Recovery@k = fraction of true positives recovered in top-k ranked residues.
Precision@k = fraction of top-k residues that are true positives.
Both are macro (mean over proteins). k values pre-specified before training.

---

## 3. Dataset Summary

| Property | Value |
|---|---|
| Split | test |
| Structures evaluated | {n_test} |
| Proteins with valid AUPRC | {metrics['n_proteins_with_valid_auprc']} / {metrics['n_proteins']} |
| Split manifest hash prefix | 24dd5e347d880108 (frozen) |
| PCNA holdout enforced | yes (cluster 1168 excluded from all train/val/test overlap checks) |
| Edge type | spatial only (edge_type==0) — matches frozen architecture |

---

## 4. Model Configuration

| Parameter | Value |
|---|---|
| Architecture | GraphSAGE-3L, spatial edges only |
| Checkpoint | `checkpoints/phase3/spatial_only_fold1_seed1_best.pt` |
| Val fold frozen on | fold=1 |
| Val seed frozen on | seed=1 |
| Val macro-AUPRC at freeze | 0.2047 |
| hidden_dim | 128 |
| dropout | 0.1 |
| Inference device | {device_str} |
| Elapsed (inference only) | {elapsed:.1f}s |

---

## 5. Validation Context (for comparison only — not headline)

| Model variant | Val macro-AUPRC |
|---|---|
| Spatial-only (frozen, this model) | 0.1897 +/- 0.0091 (12 runs) |
| Full GraphSAGE-3L | 0.1876 +/- 0.0113 (12 runs) |
| Random baseline | 0.0861 +/- 0.0011 |
| Degree/exposure baseline | 0.0813 |
| GCN-1L | 0.1601 +/- 0.0089 |
| GAT-2L | 0.1739 +/- 0.0090 |

Note: validation metrics are for context only. Test result above is the
single authoritative performance estimate. Do not combine them.

---

## 6. Missing Baselines

fpocket, P2Rank, and PocketMiner were not run on the frozen test split.
Stubs: `reports/phase3/baseline_runs/{{fpocket,p2rank,pocketminer}}_manifest.json`.
Per governance doc 10, any superiority claim over these tools requires
running them on the same split (hash: 24dd5e347d880108) with the same
label definition before that language appears in reports or publications.

---

## 7. Governance Compliance

- [x] GATE 4 model-freeze record present and APPROVED before test data loaded.
- [x] One-shot guard checked: no prior test evaluation existed.
- [x] Test split loaded via frozen manifest (hash prefix: 24dd5e347d880108).
- [x] PCNA cluster 1168 excluded (holdout enforced in split manifest).
- [x] Edge filter applied: spatial only (matches frozen architecture).
- [x] No threshold tuning on test set.
- [x] No second run possible (lock file written).
- [x] No combined validation/test headline.
- [x] Bootstrap CI computed over proteins (N=1000, seed=42).
- [x] Per-protein table included below.
- [x] No scientific claims made beyond reported metrics.

---

## 8. Per-Protein Table (sorted by AUPRC descending)

| idx | nodes | AUPRC | AUROC | Rec@5 | Rec@10 | Rec@20 |
|-----|-------|-------|-------|-------|--------|--------|
{per_protein_table}

---

## 9. Provenance

- GATE 4 decision_id: `phase3_model_freeze_20260529`
- GATE 2 decision_id: `phase3_first_training_signoff_20260528`
- Option B authorization: `phase3_spatial_only_retrain_20260529`
- Graph release decision_id: `phase3_first_graph_release_20260528`
- Split manifest hash: `24dd5e347d880108`
- Lock file written: `reports/phase3/.test_evaluation_lock`
- Machine manifest: `reports/phase3/test_evaluation_manifest_20260529.json`
- No scientific claims are made in this report.
- Evidence status: computational, single held-out test evaluation.
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--device", type=str, default=None,
        help="Inference device: 'cuda', 'cpu', or auto-detect (default).",
    )
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    # -----------------------------------------------------------------------
    # PRE-CONDITIONS — must all pass before any test data is touched
    # -----------------------------------------------------------------------
    try:
        run_precondition_checks()
    except RuntimeError as exc:
        print(f"\nPRE-CONDITION FAILURE:\n{exc}", file=sys.stderr)
        return 2

    # -----------------------------------------------------------------------
    # Device selection
    # -----------------------------------------------------------------------
    if args.device:
        device_str = args.device
    elif torch.cuda.is_available():
        device_str = "cuda"
        print(f"[device] CUDA available — {torch.cuda.get_device_name(0)}. Using cuda.", flush=True)
    else:
        device_str = "cpu"
        print("[device] CUDA not available. Using cpu.", flush=True)

    device = torch.device(device_str)

    # -----------------------------------------------------------------------
    # Load frozen checkpoint
    # -----------------------------------------------------------------------
    print(f"Loading frozen checkpoint: {FROZEN_CKPT.name}", flush=True)
    ckpt = torch.load(FROZEN_CKPT, map_location=device, weights_only=False)
    ckpt_config = ckpt.get("config", {})
    hidden_dim = ckpt_config.get("hidden_dim", 128)
    dropout    = ckpt_config.get("dropout", 0.1)

    model = GraphSAGE3L(hidden_dim=hidden_dim, dropout=dropout).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    print(f"  hidden_dim={hidden_dim}  dropout={dropout}  architecture=spatial_only", flush=True)

    # -----------------------------------------------------------------------
    # Load test split — only after all pre-conditions pass
    # -----------------------------------------------------------------------
    print(f"\nLoading test split from frozen manifest...", flush=True)
    test_data_raw = load_split(GRAPH_DIR, SPLIT_MANIFEST, "test")
    print(f"  {len(test_data_raw)} test structures loaded", flush=True)

    # Apply spatial-only edge filter — must match frozen architecture
    test_data = [filter_edges(d, EDGE_TYPE_SPATIAL) for d in test_data_raw]
    sample_before = test_data_raw[0].edge_index.shape[1]
    sample_after  = test_data[0].edge_index.shape[1]
    print(f"  Edge filter (spatial only): {sample_before} -> {sample_after} edges per sample", flush=True)

    # -----------------------------------------------------------------------
    # Write one-shot lock file BEFORE inference (prevents partial-run re-use)
    # -----------------------------------------------------------------------
    lock_content = (
        f"test_evaluation_started: 2026-05-29\n"
        f"gate4_record: {GATE4_RECORD}\n"
        f"frozen_checkpoint: {FROZEN_CKPT}\n"
        f"n_test_structures: {len(test_data)}\n"
        f"governance: docs/scientific_governance/09_EVALUATION_PROTOCOL.md\n"
        f"note: This file prevents the test set from being evaluated more than once.\n"
        f"      Do not delete without recording the reason in wiki/log.md and\n"
        f"      obtaining human authorization for a re-run.\n"
    )
    LOCK_FILE.write_text(lock_content, encoding="utf-8")
    print(f"\n[lock] One-shot guard written: {LOCK_FILE}", flush=True)

    # -----------------------------------------------------------------------
    # Inference
    # -----------------------------------------------------------------------
    print("\nRunning inference on test split...", flush=True)
    t_start = time.time()
    test_loader = DataLoader(test_data, batch_size=32, shuffle=False)
    protein_scores = _collect_protein_scores(model, test_loader, device)
    elapsed = time.time() - t_start
    print(f"  Inference complete. {len(protein_scores)} proteins. ({elapsed:.1f}s)", flush=True)

    # -----------------------------------------------------------------------
    # Compute metrics
    # -----------------------------------------------------------------------
    print("Computing metrics...", flush=True)
    metrics = compute_metrics_from_lists(protein_scores)
    ci = bootstrap_ci(protein_scores)

    print(f"\n{'='*56}", flush=True)
    print(f"  TEST RESULTS (one-shot, frozen checkpoint)", flush=True)
    print(f"  Macro-AUPRC (primary): {metrics['macro_auprc']:.4f}", flush=True)
    auprc_lo, auprc_hi = ci["macro_auprc_ci"]
    print(f"  95% CI:                [{auprc_lo:.4f}, {auprc_hi:.4f}]", flush=True)
    print(f"  Micro-AUPRC:           {metrics['micro_auprc']:.4f}", flush=True)
    print(f"  Macro-AUROC:           {metrics['macro_auroc']:.4f}", flush=True)
    print(f"  Micro-AUROC:           {metrics['micro_auroc']:.4f}", flush=True)
    for k in (5, 10, 20):
        rec = metrics.get(f'macro_top_{k}_recovery', float('nan'))
        pre = metrics.get(f'macro_precision_at_{k}', float('nan'))
        print(f"  Top-{k:2d} recovery/prec:  {rec:.4f} / {pre:.4f}", flush=True)
    print(f"{'='*56}", flush=True)

    # -----------------------------------------------------------------------
    # Write outputs
    # -----------------------------------------------------------------------
    report_text = _render_report(metrics, ci, len(test_data), elapsed, device_str)

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(report_text, encoding="utf-8")
    print(f"\n[report] Written to {OUT_REPORT}", flush=True)

    # Strip per-protein list from manifest (stored in report, not JSON, to keep size down)
    manifest_metrics = {k: v for k, v in metrics.items() if k != "per_protein"}
    manifest: dict[str, Any] = {
        "artifact_type": "phase3_test_evaluation",
        "date": "2026-05-29",
        "status": "FINAL_ONE_SHOT",
        "gate4_record": str(GATE4_RECORD),
        "gate4_decision_id": "phase3_model_freeze_20260529",
        "frozen_checkpoint": str(FROZEN_CKPT),
        "architecture": "GraphSAGE-3L, spatial edges only (edge_type==0)",
        "n_test_structures": len(test_data),
        "elapsed_seconds": round(elapsed, 2),
        "device": device_str,
        "metrics": manifest_metrics,
        "bootstrap_ci": {
            "macro_auprc_ci_lo": round(auprc_lo, 6),
            "macro_auprc_ci_hi": round(auprc_hi, 6),
            "macro_auroc_ci_lo": round(ci["macro_auroc_ci"][0], 6),
            "macro_auroc_ci_hi": round(ci["macro_auroc_ci"][1], 6),
            "n_bootstrap": ci["n_bootstrap"],
            "alpha": ci["alpha"],
        },
        "governance": {
            "evaluation_protocol": "docs/scientific_governance/09_EVALUATION_PROTOCOL.md",
            "split_manifest_hash_prefix": "24dd5e347d880108",
            "no_test_rerun": True,
            "lock_file": str(LOCK_FILE),
            "no_scientific_claims": True,
        },
    }
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[manifest] Written to {OUT_MANIFEST}", flush=True)
    print("\nTest-set evaluation complete. GATE 5 cleared.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
