#!/usr/bin/env python
"""Multi-seed pocket stability: the gate between "the GNN found something" and MD.

WHY THIS EXISTS
---------------
The pre-MD audit (2026-08) established that the exported candidate pocket is not a
property of the data -- it is a property of *which retrain you happened to run*. Scoring
1W60 with the repo's checkpoints selected, variously: the AOH site, an 8-residue IDCL
fragment, a 5-residue C-terminal tail, and a 255-residue whole chain. On the committed
scores the top cluster beats the runner-up by 0.0016-0.0119 mean score.

Running MD on a single seed's pocket therefore measures the seed, not the protein. This
tool runs the SAME selection logic across N seeded retrains and reports what survives.

WHAT IT DOES
------------
1. For each checkpoint, score the target structure with scripts/run_v3_inference.py
   (the real inference path -- no reimplementation, so semantics cannot drift) into an
   isolated output dir.
2. Take each run's top cluster as a set of (chain, resid) pairs.
3. Report pairwise Jaccard, per-residue selection frequency, and the consensus set
   (residues chosen by >= --min-fraction of runs).
4. Emit a verdict: STABLE (consensus is usable) or UNSTABLE (do not spend MD compute).

USAGE
-----
    # after producing several seeded checkpoints:
    #   for s in 42 43 44; do
    #     python scripts/finetune_v3_fixed.py --seed $s --out checkpoints/seed_$s/best.ckpt
    #   done
    python seed_stability.py --worktree /path/to/gnn_xl_worktree --pdb 1W60 \
        --ckpt checkpoints/seed_42/best.ckpt \
        --ckpt checkpoints/seed_43/best.ckpt \
        --ckpt checkpoints/seed_44/best.ckpt \
        --out stability_1W60.json

Pass --consensus-out to write a handoff-shaped residue list built from the consensus
rather than from any single seed.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
import tempfile
from collections import Counter
from itertools import combinations
from pathlib import Path

from sklearn.cluster import DBSCAN


DEFAULT_AOH_POSITIVES = {
    25, 26, 27, 38, 39, 40, 41, 42, 44, 45, 46, 47,
    123, 125, 126, 128, 231, 232, 233, 234, 250, 251, 252, 253,
}

RANK_THRESHOLD_MODES = {
    "validation-mcc-rank-count",
    "validation-mcc-rank-fraction",
    "validation-mcc-rank-chain-fraction",
}


def score_with_checkpoint(worktree: Path, pdb: str, ckpt: Path, out_dir: Path,
                          threshold: float = 0.4) -> Path:
    """Run the real inference script for one checkpoint; return the scores.csv path."""
    cmd = [sys.executable, "scripts/run_v3_inference.py",
           "--ckpt", str(ckpt), "--out-dir", str(out_dir), "--only", pdb,
           "--threshold", f"{threshold:.8g}"]
    proc = subprocess.run(cmd, cwd=worktree, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = (proc.stdout + proc.stderr).strip().splitlines()[-12:]
        sys.exit(f"[stability] inference failed for {ckpt}:\n  " + "\n  ".join(tail))
    csv_path = out_dir / pdb / "scores.csv"
    if not csv_path.exists():
        sys.exit(f"[stability] no scores.csv produced for {ckpt} (looked at {csv_path})")
    return csv_path


def _mcc(y_true: list[int], y_pred: list[int]) -> float:
    tp = sum(1 for y, p in zip(y_true, y_pred) if y == 1 and p == 1)
    tn = sum(1 for y, p in zip(y_true, y_pred) if y == 0 and p == 0)
    fp = sum(1 for y, p in zip(y_true, y_pred) if y == 0 and p == 1)
    fn = sum(1 for y, p in zip(y_true, y_pred) if y == 1 and p == 0)
    denom = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return ((tp * tn - fp * fn) / denom) if denom else -1.0


def select_validation_mcc_threshold(scores_csv: Path, validation_chain: str,
                                    positive_resids: set[int]) -> dict:
    """Select a score threshold from validation residues only.

    The rule mirrors the clean-split evaluator's policy: choose the threshold that
    maximizes MCC on validation labels, then freeze it before target-structure scoring.
    Ties are deterministic and independent of the target PDB.
    """
    rows = list(csv.DictReader(scores_csv.open(encoding="utf-8", errors="replace")))
    val = [
        (int(r["resid"]) in positive_resids, float(r["score"]))
        for r in rows
        if r["chain"] == validation_chain
    ]
    if not val:
        sys.exit(f"[stability] no validation rows for chain {validation_chain} in {scores_csv}")
    y_true = [1 if y else 0 for y, _ in val]
    if sum(y_true) < 2 or (len(y_true) - sum(y_true)) < 2:
        sys.exit("[stability] validation labels are degenerate; cannot select threshold")

    candidates = sorted({s for _, s in val} | {0.4, 0.5})
    best = None
    for thr in candidates:
        y_pred = [1 if s >= thr else 0 for _, s in val]
        pred_pos = sum(y_pred)
        tp = sum(1 for y, p in zip(y_true, y_pred) if y == 1 and p == 1)
        precision = tp / pred_pos if pred_pos else 0.0
        recall = tp / sum(y_true)
        f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
        # MCC first; then F1/recall/precision; then prefer thresholds near 0.5 for
        # deterministic tie-breaking without target-PDB information.
        key = (_mcc(y_true, y_pred), f1, recall, precision, -abs(thr - 0.5), thr)
        if best is None or key > best["key"]:
            best = {
                "key": key,
                "threshold": float(thr),
                "mcc": float(key[0]),
                "f1": float(f1),
                "precision": float(precision),
                "recall": float(recall),
                "predicted_positive_residues": int(pred_pos),
                "validation_chain": validation_chain,
                "n_validation_residues": len(val),
                "n_validation_positives": int(sum(y_true)),
            }
    best.pop("key", None)
    return best


def top_cluster_residues(scores_csv: Path) -> tuple[set[tuple[str, int]], float, float]:
    """Top cluster by mean score -> {(chain, resid)}, its mean, and the runner-up margin.

    Mirrors export_handoff.load_cluster exactly so this tool measures the thing that
    would actually be exported.
    """
    rows = list(csv.DictReader(scores_csv.open(encoding="utf-8", errors="replace")))
    for r in rows:
        r["score"] = float(r["score"])
        r["cluster"] = int(r["cluster"])
    clustered = [r for r in rows if r["cluster"] >= 0]
    if not clustered:
        return set(), float("nan"), float("nan")
    ids = sorted({r["cluster"] for r in clustered})
    means = {c: sum(r["score"] for r in clustered if r["cluster"] == c)
                / max(1, sum(1 for r in clustered if r["cluster"] == c)) for c in ids}
    best = max(means, key=means.get)
    ordered = sorted(means.values(), reverse=True)
    margin = (ordered[0] - ordered[1]) if len(ordered) > 1 else float("inf")
    members = {(r["chain"], int(r["resid"])) for r in clustered if r["cluster"] == best}
    return members, means[best], margin


def load_score_rows(scores_csv: Path) -> list[dict]:
    rows = list(csv.DictReader(scores_csv.open(encoding="utf-8", errors="replace")))
    for r in rows:
        r["resid"] = int(r["resid"])
        r["score"] = float(r["score"])
        if "cluster" in r:
            r["cluster"] = int(r["cluster"])
    return rows


def load_ca_coords(pdb_path: Path) -> dict[tuple[str, int], tuple[float, float, float]]:
    coords: dict[tuple[str, int], tuple[float, float, float]] = {}
    with pdb_path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("ATOM") and line[12:16].strip() == "CA":
                chain = line[21].strip()
                resid = int(line[22:26])
                coords[(chain, resid)] = (
                    float(line[30:38]), float(line[38:46]), float(line[46:54])
                )
    if not coords:
        sys.exit(f"[stability] no CA coordinates parsed from {pdb_path}")
    return coords


def _ranked(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=lambda r: (-r["score"], r["chain"], r["resid"], r.get("resname", "")))


def select_rank_budget_residues(rows: list[dict], mode: str,
                                threshold_record: dict) -> tuple[set[tuple[str, int]], dict]:
    """Select target residues by validation-derived rank budget, not absolute score.

    validation-mcc-rank-count uses the validation-chain positive-call count directly.
    validation-mcc-rank-fraction applies the validation positive-call fraction to the
    target structure. validation-mcc-rank-chain-fraction applies that fraction per chain.
    All are insensitive to a seed's absolute score scale on the target PDB.
    """
    pred_pos = int(threshold_record["predicted_positive_residues"])
    n_val = int(threshold_record["n_validation_residues"])
    fraction = pred_pos / max(n_val, 1)
    selected: set[tuple[str, int]] = set()

    if mode == "validation-mcc-rank-count":
        k = min(len(rows), max(0, pred_pos))
        selected = {(r["chain"], r["resid"]) for r in _ranked(rows)[:k]}
        details = {"rank_budget": k, "rank_budget_basis": "validation predicted-positive count"}
    elif mode == "validation-mcc-rank-fraction":
        k = min(len(rows), max(0, round(fraction * len(rows))))
        selected = {(r["chain"], r["resid"]) for r in _ranked(rows)[:k]}
        details = {"rank_budget": k, "rank_budget_basis": "validation predicted-positive fraction"}
    elif mode == "validation-mcc-rank-chain-fraction":
        per_chain = {}
        for chain in sorted({r["chain"] for r in rows}):
            chain_rows = [r for r in rows if r["chain"] == chain]
            k = min(len(chain_rows), max(0, round(fraction * len(chain_rows))))
            per_chain[chain] = k
            selected.update((r["chain"], r["resid"]) for r in _ranked(chain_rows)[:k])
        details = {"rank_budget_by_chain": per_chain,
                   "rank_budget_basis": "validation predicted-positive fraction per chain"}
    else:
        raise ValueError(f"not a rank threshold mode: {mode}")

    details.update({
        "validation_rank_fraction": fraction,
        "selected_target_residues": len(selected),
        "scale_invariant": True,
    })
    return selected, details


def top_cluster_from_selected(rows: list[dict], selected: set[tuple[str, int]],
                              coords: dict[tuple[str, int], tuple[float, float, float]]
                              ) -> tuple[set[tuple[str, int]], float, float, dict[int, int]]:
    selected_rows = [r for r in rows if (r["chain"], r["resid"]) in selected]
    selected_rows = [r for r in selected_rows if (r["chain"], r["resid"]) in coords]
    if len(selected_rows) < 3:
        return set(), float("nan"), float("nan"), {}

    labels = DBSCAN(eps=6.0, min_samples=3).fit(
        [coords[(r["chain"], r["resid"])] for r in selected_rows]
    ).labels_
    clusters: dict[int, list[dict]] = {}
    for row, label in zip(selected_rows, labels):
        if label >= 0:
            clusters.setdefault(int(label), []).append(row)
    if not clusters:
        return set(), float("nan"), float("nan"), {}

    means = {
        c: sum(r["score"] for r in members) / len(members)
        for c, members in clusters.items()
    }
    best = max(means, key=means.get)
    ordered = sorted(means.values(), reverse=True)
    margin = (ordered[0] - ordered[1]) if len(ordered) > 1 else float("inf")
    members = {(r["chain"], r["resid"]) for r in clusters[best]}
    cluster_sizes = {c: len(members) for c, members in sorted(clusters.items())}
    return members, means[best], margin, cluster_sizes


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / max(len(a | b), 1)


def main() -> None:
    ap = argparse.ArgumentParser(description="Multi-seed pocket stability gate.")
    ap.add_argument("--worktree", type=Path, required=True)
    ap.add_argument("--pdb", required=True, help="structure to score, e.g. 1W60")
    ap.add_argument("--ckpt", type=Path, action="append", required=True,
                    help="repeatable; one per seed. Use >= 3.")
    ap.add_argument("--min-fraction", type=float, default=0.6,
                    help="a residue joins the consensus if chosen by >= this fraction of runs")
    ap.add_argument("--min-jaccard", type=float, default=0.5,
                    help="mean pairwise Jaccard below this => UNSTABLE")
    ap.add_argument("--min-consensus-residues", type=int, default=8)
    ap.add_argument("--threshold", type=float, default=0.4,
                    help="fixed score threshold when --threshold-mode=fixed")
    ap.add_argument("--threshold-mode",
                    choices=("fixed", "validation-mcc",
                             "validation-mcc-rank-count",
                             "validation-mcc-rank-fraction",
                             "validation-mcc-rank-chain-fraction"),
                    default="fixed",
                    help="fixed: use --threshold; validation-mcc: select each checkpoint's "
                         "absolute threshold on validation labels before scoring the target; "
                         "validation-mcc-rank-* modes derive a rank budget from validation "
                         "MCC and apply that budget to target scores before DBSCAN")
    ap.add_argument("--validation-pdb", default="8GLA")
    ap.add_argument("--validation-chain", default="B")
    ap.add_argument("--out", type=Path, default=None, help="write the full report as JSON")
    ap.add_argument("--consensus-out", type=Path, default=None,
                    help="write the consensus residue list (handoff-shaped) here")
    ap.add_argument("--scores-dir", type=Path, default=None,
                    help="reuse/keep per-checkpoint scores here instead of a temp dir")
    args = ap.parse_args()

    if len(args.ckpt) < 2:
        sys.exit("[stability] give at least 2 --ckpt (3+ strongly recommended); "
                 "a single seed cannot show stability by construction.")

    workroot = args.scores_dir or Path(tempfile.mkdtemp(prefix="seedstab_"))
    workroot.mkdir(parents=True, exist_ok=True)

    runs = []
    threshold_records = []
    for i, ck in enumerate(args.ckpt):
        if not ck.exists():
            sys.exit(f"[stability] checkpoint not found: {ck}")
        threshold = float(args.threshold)
        threshold_record = {
            "mode": args.threshold_mode,
            "threshold": threshold,
        }
        if args.threshold_mode == "validation-mcc" or args.threshold_mode in RANK_THRESHOLD_MODES:
            val_dir = workroot / f"run{i}_validation"
            print(f"[stability] [{i+1}/{len(args.ckpt)}] selecting threshold on "
                  f"{args.validation_pdb} chain {args.validation_chain} for {ck.name} ...")
            val_csv = score_with_checkpoint(args.worktree, args.validation_pdb, ck, val_dir,
                                            threshold=args.threshold)
            threshold_record = select_validation_mcc_threshold(
                val_csv, args.validation_chain, DEFAULT_AOH_POSITIVES)
            threshold_record.update({
                "mode": args.threshold_mode,
                "validation_pdb": args.validation_pdb,
                "validation_scores_csv": str(val_csv),
            })
            threshold = threshold_record["threshold"]
            print(f"    -> threshold {threshold:.6f}, MCC {threshold_record['mcc']:.4f}, "
                  f"F1 {threshold_record['f1']:.4f}")

        target_threshold_note = (f"rank-budget mode; inference threshold {args.threshold:.6f} "
                                 "is ignored for extraction"
                                 if args.threshold_mode in RANK_THRESHOLD_MODES
                                 else f"threshold {threshold:.6f}")
        print(f"[stability] [{i+1}/{len(args.ckpt)}] scoring {args.pdb} with {ck.name} "
              f"at {target_threshold_note} ...")
        csv_path = score_with_checkpoint(args.worktree, args.pdb, ck, workroot / f"run{i}",
                                         threshold=(args.threshold if args.threshold_mode in RANK_THRESHOLD_MODES
                                                    else threshold))
        rank_details = {}
        cluster_sizes = None
        if args.threshold_mode in RANK_THRESHOLD_MODES:
            target_rows = load_score_rows(csv_path)
            selected, rank_details = select_rank_budget_residues(
                target_rows, args.threshold_mode, threshold_record)
            coords = load_ca_coords(args.worktree / "data" / "raw" / f"{args.pdb}.pdb")
            residues, mean, margin, cluster_sizes = top_cluster_from_selected(
                target_rows, selected, coords)
            threshold_record.update(rank_details)
        else:
            residues, mean, margin = top_cluster_residues(csv_path)
        runs.append({"checkpoint": str(ck), "n_residues": len(residues),
                     "threshold": round(threshold, 6),
                     "extraction_method": args.threshold_mode,
                     "selected_target_residues": rank_details.get("selected_target_residues"),
                     "rank_budget": rank_details.get("rank_budget"),
                     "rank_budget_by_chain": rank_details.get("rank_budget_by_chain"),
                     "cluster_sizes": cluster_sizes,
                     "top_mean_score": None if mean != mean else round(mean, 5),
                     "runner_up_margin": (None if margin == float("inf") or margin != margin
                                          else round(margin, 5)),
                     "residues": sorted(residues)})
        threshold_records.append(threshold_record)
        print(f"    -> {len(residues)} residues, mean {mean:.4f}, margin "
              f"{'inf' if margin == float('inf') else f'{margin:.4f}'}")

    sets = [set(map(tuple, r["residues"])) for r in runs]
    pairs = [(i, j, jaccard(sets[i], sets[j])) for i, j in combinations(range(len(sets)), 2)]
    mean_j = sum(p[2] for p in pairs) / len(pairs) if pairs else 1.0

    freq = Counter()
    for s in sets:
        freq.update(s)
    need = args.min_fraction * len(sets)
    consensus = sorted({k for k, c in freq.items() if c >= need})

    unstable = []
    if mean_j < args.min_jaccard:
        unstable.append(f"mean pairwise Jaccard {mean_j:.3f} < {args.min_jaccard}: the seeds "
                        f"do not agree on which residues form the pocket")
    if len(consensus) < args.min_consensus_residues:
        unstable.append(f"only {len(consensus)} residues reach {args.min_fraction:.0%} agreement "
                        f"(< {args.min_consensus_residues}): no usable consensus pocket")
    margins = [r["runner_up_margin"] for r in runs if r["runner_up_margin"] is not None]
    if margins and max(margins) < 0.02:
        unstable.append(f"every run's top cluster beats its runner-up by < 0.02 "
                        f"(max {max(margins):.4f}): selection is within noise in all seeds")

    report = {
        "pdb": args.pdb,
        "n_runs": len(runs),
        "mean_pairwise_jaccard": round(mean_j, 4),
        "pairwise_jaccard": [{"a": i, "b": j, "jaccard": round(v, 4)} for i, j, v in pairs],
        "consensus_min_fraction": args.min_fraction,
        "consensus_n_residues": len(consensus),
        "consensus_residues": [{"chain": c, "resid": r} for c, r in consensus],
        "residue_frequency": {f"{c}:{r}": n for (c, r), n in sorted(freq.items())},
        "threshold_mode": args.threshold_mode,
        "threshold_records": threshold_records,
        "runs": runs,
        "verdict": "UNSTABLE" if unstable else "STABLE",
        "reasons": unstable,
    }

    print("\n=== stability report ===")
    print(f"  runs                  : {len(runs)}")
    print(f"  mean pairwise Jaccard : {mean_j:.3f}")
    print(f"  consensus residues    : {len(consensus)} at >= {args.min_fraction:.0%} agreement")
    if consensus:
        by_chain: dict[str, list[int]] = {}
        for c, r in consensus:
            by_chain.setdefault(c, []).append(r)
        for c in sorted(by_chain):
            print(f"      chain {c}: {sorted(by_chain[c])}")
    print(f"  VERDICT               : {report['verdict']}")
    for r in unstable:
        print(f"      - {r}")

    if args.out:
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"  report -> {args.out}")
    if args.consensus_out and consensus:
        args.consensus_out.write_text(json.dumps({
            "pocket_residues": [{"chain": c, "resid": r} for c, r in consensus],
            "pocket_residues_by_chain": {c: sorted(v) for c, v in
                                         ((c, [r for cc, r in consensus if cc == c])
                                          for c in sorted({c for c, _ in consensus}))},
            "pocket_chains": sorted({c for c, _ in consensus}),
            "derived_from": f"multi-seed consensus ({args.threshold_mode})", "n_runs": len(runs),
            "min_fraction": args.min_fraction,
            "mean_pairwise_jaccard": round(mean_j, 4),
        }, indent=2), encoding="utf-8")
        print(f"  consensus -> {args.consensus_out}")

    sys.exit(0 if not unstable else 2)


if __name__ == "__main__":
    main()
