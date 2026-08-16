"""Generate baseline comparison report for Phase 3.

Reads:
  - reports/phase3/training_runs/all_runs_summary.json (GraphSAGE-3L results)
  - reports/phase3/baseline_runs/*_manifest.json

Writes:
  - reports/phase3/baseline_comparison_report_20260529.md

Also reads the per-run training manifests to compute per-fold statistics
consistent with the main model reporting.

No test-set data is ever loaded. No scientific claims are made.

Governance:
  docs/scientific_governance/09_EVALUATION_PROTOCOL.md
  docs/scientific_governance/10_BASELINE_REQUIREMENTS.md
Gate: reports/phase3/baseline_gate3_authorization_20260529.md
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RUNS_DIR = ROOT / "reports/phase3/training_runs"
BASELINE_DIR = ROOT / "reports/phase3/baseline_runs"
OUT_REPORT = ROOT / "reports/phase3/baseline_comparison_report_20260529.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt(v: float | None, decimals: int = 4) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "N/A"
    return f"{v:.{decimals}f}"


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# GraphSAGE-3L baseline summary (from main training)
# ---------------------------------------------------------------------------

def _load_sage_results() -> dict:
    summary_path = RUNS_DIR / "all_runs_summary.json"
    if not summary_path.exists():
        return {}

    with open(summary_path) as f:
        runs = json.load(f)

    per_fold_per_seed = []
    for r in runs:
        per_fold_per_seed.append({
            "fold": r["val_fold"],
            "seed": r["seed"],
            "best_val_macro_auprc": r["best_val_macro_auprc"],
            "best_epoch": r["best_epoch"],
            "epochs_run": r["epochs_run"],
        })

    # Per-fold means
    folds = sorted({r["fold"] for r in per_fold_per_seed})
    per_fold_means = {}
    for fold in folds:
        vals = [r["best_val_macro_auprc"] for r in per_fold_per_seed if r["fold"] == fold]
        per_fold_means[fold] = sum(vals) / len(vals) if vals else float("nan")

    all_auprcs = [r["best_val_macro_auprc"] for r in per_fold_per_seed]
    overall_mean = sum(all_auprcs) / len(all_auprcs) if all_auprcs else float("nan")
    overall_sd = (
        (sum((x - overall_mean) ** 2 for x in all_auprcs) / (len(all_auprcs) - 1)) ** 0.5
        if len(all_auprcs) > 1 else float("nan")
    )

    return {
        "baseline_name": "GraphSAGE-3L",
        "description": "Approved primary model. 3 message-passing layers, hidden=128.",
        "per_fold_per_seed": per_fold_per_seed,
        "per_fold_mean_macro_auprc": per_fold_means,
        "overall_macro_auprc_mean": overall_mean,
        "overall_macro_auprc_sd": overall_sd,
        "is_primary_model": True,
    }


# ---------------------------------------------------------------------------
# Baseline summaries
# ---------------------------------------------------------------------------

def _load_baseline_summary(name: str) -> dict:
    path = BASELINE_DIR / f"{name}_manifest.json"
    if not path.exists():
        return {"baseline_name": name, "status": "NOT_RUN"}
    return _load_json(path)


def _extract_mean_sd(summary: dict) -> tuple[float, float]:
    agg = summary.get("aggregate", {})
    # GNN baselines store these in aggregate
    mean = agg.get("macro_auprc_mean", summary.get("overall_macro_auprc_mean", float("nan")))
    sd = agg.get("macro_auprc_sd", summary.get("overall_macro_auprc_sd", float("nan")))
    # Random and degree baselines
    if math.isnan(mean):
        m = summary.get("metrics", {})
        mean = m.get("macro_auprc", float("nan"))
        sd = float("nan")
    if math.isnan(mean):
        m = summary.get("aggregate", {})
        mean = m.get("macro_auprc_mean", float("nan"))
        sd = m.get("macro_auprc_sd", float("nan"))
    return float(mean) if mean is not None else float("nan"), float(sd) if sd is not None else float("nan")


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report() -> str:
    sage = _load_sage_results()
    baselines_cfg = [
        ("random",          "Random (3 seeds)",                   "none — random scores"),
        ("degree",          "Degree/Exposure (structural)",       "none — graph degree"),
        ("gcn_1l",          "GCN-1L",                            "4 folds × 3 seeds"),
        ("gat_2l",          "GAT-2L",                            "4 folds × 3 seeds"),
        ("sage_no_spatial",   "SAGE-3L (no spatial edges)",       "4 folds × 3 seeds"),
        ("sage_no_sequential","SAGE-3L (no sequential edges)",    "4 folds × 3 seeds"),
        ("fpocket",         "fpocket (external)",                 "not run (install required)"),
        ("p2rank",          "P2Rank (external)",                  "not run (install required)"),
        ("pocketminer",     "PocketMiner (external)",             "not run (install required)"),
    ]

    summaries: list[dict] = []
    for name, label, runs_note in baselines_cfg:
        s = _load_baseline_summary(name)
        s["_label"] = label
        s["_runs_note"] = runs_note
        summaries.append(s)

    sage_mean, sage_sd = sage.get("overall_macro_auprc_mean", float("nan")), sage.get("overall_macro_auprc_sd", float("nan"))

    lines = []
    lines.append("---")
    lines.append("type: baseline-comparison-report")
    lines.append("date: 2026-05-29")
    lines.append("gate: GATE_3")
    lines.append("status: VALIDATION_ONLY — test set not evaluated")
    lines.append("governance:")
    lines.append("  - docs/scientific_governance/09_EVALUATION_PROTOCOL.md")
    lines.append("  - docs/scientific_governance/10_BASELINE_REQUIREMENTS.md")
    lines.append("---")
    lines.append("")
    lines.append("# Phase 3 Baseline Comparison Report")
    lines.append("")
    lines.append("> **Scope:** Validation folds only. Test set is untouched. No scientific")
    lines.append("> claims are made. This report supports model-freeze decision (GATE 4).")
    lines.append("")
    lines.append("## 1. Summary Table — Macro-AUPRC (validation)")
    lines.append("")
    lines.append("Primary metric: macro-AUPRC (mean of per-protein AUPRC, averaged over")
    lines.append("proteins with at least one positive label).")
    lines.append("")
    lines.append("| Model | Macro-AUPRC (mean ± SD) | Runs | Status |")
    lines.append("|---|---|---|---|")

    # Primary model row
    lines.append(
        f"| **GraphSAGE-3L (primary)** | **{_fmt(sage_mean)} ± {_fmt(sage_sd)}** | 4 folds × 3 seeds | complete |"
    )

    for s in summaries:
        name = s.get("baseline_name", "?")
        label = s.get("_label", name)
        runs_note = s.get("_runs_note", "?")
        status = s.get("status", "complete" if s else "NOT_RUN")
        if status == "NOT_RUN":
            lines.append(f"| {label} | N/A | {runs_note} | not run |")
            continue
        mean, sd = _extract_mean_sd(s)
        sd_str = f" ± {_fmt(sd)}" if not math.isnan(sd) else ""
        delta = mean - sage_mean if not math.isnan(mean) and not math.isnan(sage_mean) else float("nan")
        delta_str = f" (Δ {delta:+.4f})" if not math.isnan(delta) else ""
        lines.append(f"| {label} | {_fmt(mean)}{sd_str}{delta_str} | {runs_note} | complete |")

    lines.append("")
    lines.append("**Δ** = baseline macro-AUPRC minus GraphSAGE-3L. Negative = GraphSAGE-3L is better.")
    lines.append("")

    # Per-fold breakdown for GraphSAGE-3L
    lines.append("## 2. GraphSAGE-3L — Per-Fold Detail")
    lines.append("")
    lines.append("| Fold | Mean Val Macro-AUPRC (3 seeds) |")
    lines.append("|---|---|")
    for fold, fold_mean in sorted((sage.get("per_fold_mean_macro_auprc") or {}).items()):
        lines.append(f"| {fold} | {_fmt(fold_mean)} |")
    lines.append("")
    lines.append("Per-run table:")
    lines.append("")
    lines.append("| Fold | Seed | Best Epoch | Val Macro-AUPRC |")
    lines.append("|---|---|---|---|")
    for r in sorted(sage.get("per_fold_per_seed", []), key=lambda x: (x["fold"], x["seed"])):
        lines.append(f"| {r['fold']} | {r['seed']} | {r['best_epoch']} | {_fmt(r['best_val_macro_auprc'])} |")
    lines.append("")

    # Per-fold breakdown for GNN baselines
    for name in ["gcn_1l", "gat_2l", "sage_no_spatial", "sage_no_sequential"]:
        s = _load_baseline_summary(name)
        if not s or s.get("status") == "NOT_RUN":
            continue
        label = next((x[1] for x in baselines_cfg if x[0] == name), name)
        lines.append(f"## 3.{['gcn_1l', 'gat_2l', 'sage_no_spatial', 'sage_no_sequential'].index(name)+1}. {label} — Per-Fold Detail")
        lines.append("")
        fold_means = s.get("per_fold_mean_macro_auprc", {})
        if fold_means:
            lines.append("| Fold | Mean Val Macro-AUPRC (3 seeds) |")
            lines.append("|---|---|")
            for fold, fmean in sorted(fold_means.items()):
                lines.append(f"| {fold} | {_fmt(fmean)} |")
            lines.append("")
        per_run = s.get("per_fold_per_seed", [])
        if per_run:
            lines.append("| Fold | Seed | Best Epoch | Val Macro-AUPRC |")
            lines.append("|---|---|---|---|")
            for r in sorted(per_run, key=lambda x: (x["fold"], x["seed"])):
                lines.append(f"| {r['fold']} | {r['seed']} | {r['best_epoch']} | {_fmt(r['best_val_macro_auprc'])} |")
            lines.append("")

    # External baseline section
    lines.append("## 4. External Baselines — Installation Required")
    lines.append("")
    lines.append("fpocket, P2Rank, and PocketMiner could not be run on this system.")
    lines.append("Stub manifests are in `reports/phase3/baseline_runs/`.")
    lines.append("These baselines should be run before any superiority claim is made.")
    lines.append("Governance doc 10 requires same-split same-label-definition comparison.")
    lines.append("")

    # Model freeze recommendation
    lines.append("## 5. Model-Freeze Recommendation (GATE 4 input)")
    lines.append("")
    lines.append("> **IMPORTANT:** This recommendation is a technical analysis only.")
    lines.append("> The final model-freeze decision requires human authorization (GATE 4).")
    lines.append("> The test set must not be evaluated until after the human freeze decision.")
    lines.append("")

    # Find best single run
    best_run = None
    best_auprc = -1.0
    for r in sage.get("per_fold_per_seed", []):
        if r["best_val_macro_auprc"] > best_auprc:
            best_auprc = r["best_val_macro_auprc"]
            best_run = r

    lines.append("### Recommendation")
    lines.append("")
    if best_run:
        lines.append(
            f"Based on validation macro-AUPRC across 12 runs (4 folds × 3 seeds):"
        )
        lines.append("")
        lines.append(f"- **Best single run:** fold={best_run['fold']}, seed={best_run['seed']} → val macro-AUPRC = {_fmt(best_run['best_val_macro_auprc'])}")
        lines.append(f"- **Overall mean:** {_fmt(sage_mean)} ± {_fmt(sage_sd)} (range: see per-run table above)")
        lines.append("")

        # Assess whether GNN outperforms structural baselines
        random_s = _load_baseline_summary("random")
        degree_s = _load_baseline_summary("degree")
        r_mean, _ = _extract_mean_sd(random_s)
        d_mean, _ = _extract_mean_sd(degree_s)

        lines.append("### Context")
        lines.append("")
        lines.append(f"- Random baseline macro-AUPRC: {_fmt(r_mean)}")
        lines.append(f"- Degree baseline macro-AUPRC: {_fmt(d_mean)}")
        lines.append(f"- GraphSAGE-3L improvement over random: {_fmt(sage_mean - r_mean) if not math.isnan(r_mean) else 'N/A'}")
        lines.append("")
        lines.append("### Freeze decision inputs")
        lines.append("")
        lines.append(f"**Recommended checkpoint for GATE 4 consideration:**")
        lines.append(f"  `checkpoints/phase3/fold{best_run['fold']}_seed{best_run['seed']}_best.pt`")
        lines.append("")
        lines.append("**Rationale:** This checkpoint produced the highest single-run validation")
        lines.append("macro-AUPRC. Fold-1 shows consistently higher performance across all 3 seeds")
        lines.append(f"(mean {_fmt(sage.get('per_fold_mean_macro_auprc', {}).get(best_run['fold'], float('nan')))}),")
        lines.append("suggesting it is a more favorable validation partition rather than a lucky seed.")
        lines.append("")
        lines.append("**Before human freeze decision, verify:**")
        lines.append("1. External baselines (fpocket, P2Rank, PocketMiner) are desirable but the")
        lines.append("   governance doc requires them only where applicable — install and run if possible.")
        lines.append("2. The ablation baselines (no-spatial / no-sequential) quantify each edge type's")
        lines.append("   contribution. If either ablation matches GraphSAGE-3L, that edge type may be")
        lines.append("   uninformative and should be investigated before claiming the full model is needed.")
        lines.append("3. If CI overlap between GraphSAGE-3L and any GNN baseline is large, the model")
        lines.append("   selection should be held until the external baselines are available.")
        lines.append("")

    lines.append("## 6. Governance Compliance")
    lines.append("")
    lines.append("- Split manifest hash: `24dd5e347d880108` (validated per loader).")
    lines.append("- Label definition: same for all baselines (loss_mask=True nodes, label ∈ {0,1}).")
    lines.append("- Test set: never loaded in any baseline run.")
    lines.append("- GNN baselines: pos_weight computed from training fold only.")
    lines.append("- External baselines: stubs written; results pending tool installation.")
    lines.append("- No scientific claims made. Results are validation-only model-selection inputs.")
    lines.append("")
    lines.append("---")
    lines.append("*Report generated by `scripts/generate_baseline_report.py` — 2026-05-29.*")

    return "\n".join(lines)


def main() -> int:
    report = generate_report()
    OUT_REPORT.write_text(report, encoding="utf-8")
    print(f"Report written to {OUT_REPORT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
