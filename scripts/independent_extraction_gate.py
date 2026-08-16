#!/usr/bin/env python3
"""Independent non-PCNA extraction-policy selection and frozen 1W60 gate.

This script is deliberately stdlib-only. It consumes already generated residue
score CSVs and PDB CA coordinates; it does not train, rescore, or start MD.

Two-step usage:

    python scripts/independent_extraction_gate.py select-policy
    python scripts/independent_extraction_gate.py apply-1w60

The first command never reads 1W60 score files. The second command refuses to run
without a frozen policy produced by the first command.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import subprocess
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Iterable


REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "artifacts" / "pre_md_independent_extraction_20260815"
REPORT_DIR = REPO / "reports" / "pre_md_independent_extraction_20260815"
CAL_DIR = REPO / "artifacts" / "diagnostics" / "threshold_calibration_independent_20260814"
PCNA_SCORE_DIR = REPO / "artifacts" / "go_prep" / "seed_stability_scores"
SEEDS = (42, 43, 44)
ELIGIBLE_IDS = ("1GQY", "2HNX", "2K1V", "2WER", "3FU8")
EXCLUDED_IDS = {
    "2CNN": "degenerate validation labels in canonical clean split: n_positive=4 < min_positive=5",
    "8GLA": "PCNA positive-control/fine-tuning/checkpoint-selection structure; forbidden for independent extraction selection",
    "1W60": "final PCNA target; forbidden for extraction-method selection",
}
EPS = 6.0
MIN_SAMPLES = 3
MIN_CLUSTER_SIZE = 3


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip()
    except Exception:
        return "UNVERIFIED"


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", errors="replace", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        if "pdb_id" in r:
            r["pdb_id"] = r["pdb_id"].upper()
        r["resid"] = int(r["resid"])
        r["score"] = float(r["score"])
        if "label" in r:
            r["label"] = int(float(r["label"]))
        if "cluster" in r and r["cluster"] != "":
            r["cluster"] = int(r["cluster"])
    return rows


def load_calibration_rows() -> dict[int, list[dict]]:
    by_seed = {}
    for seed in SEEDS:
        path = CAL_DIR / f"calibration_scores_seed_{seed}.csv"
        if not path.exists():
            raise SystemExit(f"missing independent calibration scores: {path}")
        rows = [r for r in read_csv(path) if r["pdb_id"] in ELIGIBLE_IDS]
        seen = sorted({r["pdb_id"] for r in rows})
        if tuple(seen) != tuple(ELIGIBLE_IDS):
            raise SystemExit(f"{path} does not cover eligible IDs: got {seen}")
        by_seed[seed] = rows
    return by_seed


def load_ca_coords(pdb_id: str) -> dict[tuple[str, int], tuple[float, float, float]]:
    path = REPO / "data" / "raw" / f"{pdb_id}.pdb"
    coords: dict[tuple[str, int], tuple[float, float, float]] = {}
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("ATOM") and line[12:16].strip() == "CA":
                chain = line[21].strip() or "_"
                try:
                    resid = int(line[22:26])
                    coords[(chain, resid)] = (
                        float(line[30:38]),
                        float(line[38:46]),
                        float(line[46:54]),
                    )
                except ValueError:
                    continue
    if not coords:
        raise SystemExit(f"no CA coordinates parsed from {path}")
    return coords


def mcc_from_counts(tp: int, fp: int, fn: int, tn: int) -> float:
    denom = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return ((tp * tn - fp * fn) / denom) if denom else 0.0


def binary_metrics(rows: list[dict], selected: set[tuple[str, int]]) -> dict:
    tp = fp = fn = tn = 0
    positives = {(r["chain"], r["resid"]) for r in rows if r.get("label") == 1}
    for r in rows:
        key = (r["chain"], r["resid"])
        pred = key in selected
        label = r.get("label") == 1
        if pred and label:
            tp += 1
        elif pred and not label:
            fp += 1
        elif not pred and label:
            fn += 1
        else:
            tn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    j = len(selected & positives) / len(selected | positives) if (selected or positives) else 1.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "mcc": mcc_from_counts(tp, fp, fn, tn),
        "label_jaccard": j,
        "selected_n": len(selected),
        "positive_n": len(positives),
    }


def select_mcc_threshold(rows: list[dict]) -> dict:
    candidates = sorted({r["score"] for r in rows} | {0.4, 0.5})
    best = None
    for thr in candidates:
        selected = {(r["chain"], r["resid"], i) for i, r in enumerate(rows) if r["score"] >= thr}
        tp = fp = fn = tn = 0
        for i, r in enumerate(rows):
            pred = (r["chain"], r["resid"], i) in selected
            label = r["label"] == 1
            if pred and label:
                tp += 1
            elif pred and not label:
                fp += 1
            elif not pred and label:
                fn += 1
            else:
                tn += 1
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        mcc = mcc_from_counts(tp, fp, fn, tn)
        key = (mcc, f1, recall, precision, -abs(thr - 0.5), thr)
        if best is None or key > best["key"]:
            best = {
                "key": key,
                "threshold": thr,
                "mcc": mcc,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "predicted_positive_residues": tp + fp,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": tn,
            }
    best.pop("key")
    best["rank_fraction"] = best["predicted_positive_residues"] / len(rows)
    best["rank_count_mean_per_structure"] = round(best["predicted_positive_residues"] / len(ELIGIBLE_IDS))
    return best


def distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def dbscan(rows: list[dict], coords: dict[tuple[str, int], tuple[float, float, float]]) -> list[int]:
    keys = [(r["chain"], r["resid"]) for r in rows]
    points = [coords[k] for k in keys]
    labels = [-99] * len(rows)
    cluster_id = 0

    neighbors: list[list[int]] = []
    for i, p in enumerate(points):
        neighbors.append([j for j, q in enumerate(points) if distance(p, q) <= EPS])

    for i in range(len(rows)):
        if labels[i] != -99:
            continue
        if len(neighbors[i]) < MIN_SAMPLES:
            labels[i] = -1
            continue
        labels[i] = cluster_id
        queue = deque(neighbors[i])
        while queue:
            j = queue.popleft()
            if labels[j] == -1:
                labels[j] = cluster_id
            if labels[j] != -99:
                continue
            labels[j] = cluster_id
            if len(neighbors[j]) >= MIN_SAMPLES:
                queue.extend(neighbors[j])
        cluster_id += 1
    return labels


def cluster_selected(
    rows: list[dict],
    selected: set[tuple[str, int]],
    coords: dict[tuple[str, int], tuple[float, float, float]],
    ranking: str,
) -> dict:
    selected_rows = [r for r in rows if (r["chain"], r["resid"]) in selected and (r["chain"], r["resid"]) in coords]
    if len(selected_rows) < MIN_CLUSTER_SIZE:
        return {
            "valid": False,
            "primary": set(),
            "clusters": [],
            "runner_up_margin": None,
            "primary_score": None,
        }
    labels = dbscan(selected_rows, coords)
    clusters: dict[int, list[dict]] = defaultdict(list)
    for row, label in zip(selected_rows, labels):
        if label >= 0:
            clusters[int(label)].append(row)
    summaries = []
    for cid, members in clusters.items():
        if len(members) < MIN_CLUSTER_SIZE:
            continue
        mean_score = statistics.mean(r["score"] for r in members)
        rank_score = mean_score if ranking == "mean_score" else mean_score * math.sqrt(len(members))
        summaries.append({
            "cluster_id": cid,
            "size": len(members),
            "mean_score": mean_score,
            "rank_score": rank_score,
            "residues": sorted((r["chain"], r["resid"]) for r in members),
        })
    if not summaries:
        return {
            "valid": False,
            "primary": set(),
            "clusters": [],
            "runner_up_margin": None,
            "primary_score": None,
        }
    summaries.sort(key=lambda c: (-c["rank_score"], -c["mean_score"], -c["size"], c["cluster_id"]))
    primary = set(map(tuple, summaries[0]["residues"]))
    margin = None
    if len(summaries) > 1:
        margin = summaries[0]["rank_score"] - summaries[1]["rank_score"]
    return {
        "valid": True,
        "primary": primary,
        "clusters": summaries,
        "runner_up_margin": margin,
        "primary_score": summaries[0]["rank_score"],
    }


def ranked(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=lambda r: (-r["score"], r["chain"], r["resid"], r.get("resname", "")))


def selected_for_policy(rows: list[dict], policy: dict, threshold_record: dict) -> set[tuple[str, int]]:
    mode = policy["selection"]
    if mode == "fixed_abs":
        return {(r["chain"], r["resid"]) for r in rows if r["score"] >= policy["threshold"]}
    if mode == "mcc_abs":
        return {(r["chain"], r["resid"]) for r in rows if r["score"] >= threshold_record["threshold"]}
    if mode == "rank_count_mean":
        k = min(len(rows), threshold_record["rank_count_mean_per_structure"])
        return {(r["chain"], r["resid"]) for r in ranked(rows)[:k]}
    if mode == "rank_fraction":
        k = min(len(rows), max(0, round(threshold_record["rank_fraction"] * len(rows))))
        return {(r["chain"], r["resid"]) for r in ranked(rows)[:k]}
    if mode == "rank_chain_fraction":
        out = set()
        for chain in sorted({r["chain"] for r in rows}):
            chain_rows = [r for r in rows if r["chain"] == chain]
            k = min(len(chain_rows), max(0, round(threshold_record["rank_fraction"] * len(chain_rows))))
            out.update((r["chain"], r["resid"]) for r in ranked(chain_rows)[:k])
        return out
    raise ValueError(mode)


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a or b) else 1.0


def spearman(xs: list[float], ys: list[float]) -> float:
    def ranks(vals: list[float]) -> list[float]:
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        out = [0.0] * len(vals)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            rank = (i + j + 2) / 2.0
            for k in range(i, j + 1):
                out[order[k]] = rank
            i = j + 1
        return out

    if len(xs) != len(ys) or len(xs) < 2:
        return float("nan")
    rx, ry = ranks(xs), ranks(ys)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    cov = sum((x - mx) * (y - my) for x, y in zip(rx, ry))
    sx = math.sqrt(sum((x - mx) ** 2 for x in rx))
    sy = math.sqrt(sum((y - my) ** 2 for y in ry))
    return cov / (sx * sy) if sx and sy else float("nan")


def source_hashes(paths: Iterable[Path]) -> dict[str, str]:
    return {str(p.relative_to(REPO)): sha256_path(p) for p in paths if p.exists()}


def predeclared_spec(threshold_records: dict[int, dict]) -> dict:
    return {
        "version": "independent_extraction_policy_selection_v1",
        "created_at": utc_now(),
        "git_commit": git_commit(),
        "forbidden_target_use": "No 1W60/PCNA score, stability, or geometry input may be read during select-policy.",
        "eligible_non_pcna_structures": list(ELIGIBLE_IDS),
        "excluded_structures": EXCLUDED_IDS,
        "candidate_policies": candidate_policies(),
        "fixed_clustering": {
            "algorithm": "DBSCAN over selected residue CA coordinates",
            "eps_angstrom": EPS,
            "min_samples": MIN_SAMPLES,
            "minimum_cluster_size": MIN_CLUSTER_SIZE,
            "primary_cluster_default_ranking": "mean_score",
        },
        "selection_metrics": [
            "mean primary-cluster F1 against non-PCNA labels",
            "mean primary-cluster label Jaccard",
            "mean primary-cluster recall and precision",
            "valid-cluster rate",
            "mean within-structure pairwise seed Jaccard",
            "scale robustness under monotonic score transformations",
        ],
        "deterministic_selection_rule": (
            "Exclude policies with valid_cluster_rate < 0.80 or mean_recall < 0.20. "
            "Maximize composite_score = mean_f1 + 0.50*mean_label_jaccard + "
            "0.25*mean_seed_jaccard + 0.10*scale_robustness - 0.25*invalid_cluster_rate. "
            "Tie-breakers: higher mean_recall, higher mean_precision, lower mean_selected_n, "
            "rank-based before absolute threshold, then lexical policy_id."
        ),
        "gate_for_final_1w60": {
            "pre_md_pass_requires": [
                "policy_id and parameters exactly match frozen_extraction_method.json",
                "valid primary cluster in all three seeds",
                "literal mean pairwise Jaccard >= 0.50",
                "consensus residues at >=2/3 seeds >= 8",
                "no seed has primary-vs-runner-up margin <= 0 when runner-up exists",
            ],
            "symmetry_normalized_jaccard": "supplementary only if chain mapping is justified; literal Jaccard remains primary",
        },
        "threshold_records_from_non_pcna": threshold_records,
    }


def candidate_policies() -> list[dict]:
    return [
        {"policy_id": "fixed_0p4_primary_cluster", "selection": "fixed_abs", "threshold": 0.4, "cluster": True, "ranking": "mean_score", "scale_invariant": False},
        {"policy_id": "independent_mcc_abs_primary_cluster", "selection": "mcc_abs", "cluster": True, "ranking": "mean_score", "scale_invariant": False},
        {"policy_id": "independent_mcc_rank_count_primary_cluster", "selection": "rank_count_mean", "cluster": True, "ranking": "mean_score", "scale_invariant": True},
        {"policy_id": "independent_mcc_rank_fraction_primary_cluster", "selection": "rank_fraction", "cluster": True, "ranking": "mean_score", "scale_invariant": True},
        {"policy_id": "independent_mcc_rank_chain_fraction_primary_cluster", "selection": "rank_chain_fraction", "cluster": True, "ranking": "mean_score", "scale_invariant": True},
        {"policy_id": "independent_mcc_rank_fraction_size_weighted_cluster", "selection": "rank_fraction", "cluster": True, "ranking": "mean_score_sqrt_size", "scale_invariant": True},
    ]


def evaluate_policy(policy: dict, rows_by_seed: dict[int, list[dict]], threshold_records: dict[int, dict]) -> dict:
    coords = {pdb_id: load_ca_coords(pdb_id) for pdb_id in ELIGIBLE_IDS}
    cases = []
    by_structure: dict[str, dict[int, set]] = defaultdict(dict)
    for seed, rows in rows_by_seed.items():
        for pdb_id in ELIGIBLE_IDS:
            struct_rows = [r for r in rows if r["pdb_id"] == pdb_id]
            selected = selected_for_policy(struct_rows, policy, threshold_records[seed])
            clustered = cluster_selected(struct_rows, selected, coords[pdb_id], policy["ranking"])
            primary = clustered["primary"]
            metrics = binary_metrics(struct_rows, primary)
            by_structure[pdb_id][seed] = primary
            cases.append({
                "seed": seed,
                "pdb_id": pdb_id,
                "valid_cluster": clustered["valid"],
                "selected_precluster_n": len(selected),
                "primary_cluster_n": len(primary),
                "cluster_count": len(clustered["clusters"]),
                "runner_up_margin": clustered["runner_up_margin"],
                **metrics,
            })

    seed_jaccards = []
    for pdb_id, seed_sets in by_structure.items():
        for a, b in combinations(SEEDS, 2):
            seed_jaccards.append(jaccard(seed_sets[a], seed_sets[b]))

    valid_rate = statistics.mean(1.0 if c["valid_cluster"] else 0.0 for c in cases)
    invalid_rate = 1.0 - valid_rate
    scale_robustness = 1.0 if policy["scale_invariant"] else 0.0
    mean_f1 = statistics.mean(c["f1"] for c in cases)
    mean_label_jaccard = statistics.mean(c["label_jaccard"] for c in cases)
    mean_recall = statistics.mean(c["recall"] for c in cases)
    mean_precision = statistics.mean(c["precision"] for c in cases)
    mean_seed_jaccard = statistics.mean(seed_jaccards) if seed_jaccards else 0.0
    composite = (
        mean_f1
        + 0.50 * mean_label_jaccard
        + 0.25 * mean_seed_jaccard
        + 0.10 * scale_robustness
        - 0.25 * invalid_rate
    )
    eligible = valid_rate >= 0.80 and mean_recall >= 0.20
    return {
        "policy_id": policy["policy_id"],
        "policy": policy,
        "eligible_by_selection_rule": eligible,
        "composite_score": composite,
        "mean_f1": mean_f1,
        "mean_label_jaccard": mean_label_jaccard,
        "mean_recall": mean_recall,
        "mean_precision": mean_precision,
        "valid_cluster_rate": valid_rate,
        "invalid_cluster_rate": invalid_rate,
        "mean_seed_jaccard": mean_seed_jaccard,
        "scale_robustness": scale_robustness,
        "mean_selected_precluster_n": statistics.mean(c["selected_precluster_n"] for c in cases),
        "mean_primary_cluster_n": statistics.mean(c["primary_cluster_n"] for c in cases),
        "cases": cases,
    }


def select_policy() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    rows_by_seed = load_calibration_rows()
    threshold_records = {seed: select_mcc_threshold(rows) for seed, rows in rows_by_seed.items()}

    spec = predeclared_spec(threshold_records)
    spec_path = OUT_DIR / "predeclared_extraction_selection_spec.json"
    write_json(spec_path, spec)
    spec_hash = sha256_path(spec_path)

    results = [evaluate_policy(p, rows_by_seed, threshold_records) for p in candidate_policies()]
    ranked_results = sorted(
        results,
        key=lambda r: (
            not r["eligible_by_selection_rule"],
            -r["composite_score"],
            -r["mean_recall"],
            -r["mean_precision"],
            r["mean_selected_precluster_n"],
            0 if r["policy"]["scale_invariant"] else 1,
            r["policy_id"],
        ),
    )
    winner = ranked_results[0]
    if not winner["eligible_by_selection_rule"]:
        raise SystemExit("no extraction policy passed the independent eligibility rule")

    source_paths = [
        *(CAL_DIR / f"calibration_scores_seed_{s}.csv" for s in SEEDS),
        CAL_DIR / "calibration_provenance_and_stability.json",
        REPO / "data" / "results" / "homology30_audit.json",
        REPO / "data" / "results" / "split_integrity_520.json",
    ]
    frozen = {
        "version": "frozen_extraction_method_v1",
        "created_at": utc_now(),
        "git_commit": git_commit(),
        "predeclared_spec": str(spec_path.relative_to(REPO)),
        "predeclared_spec_sha256": spec_hash,
        "selected_without_pcna": True,
        "pcna_inputs_read_during_selection": [],
        "excluded_from_selection": EXCLUDED_IDS,
        "independent_development_structures": list(ELIGIBLE_IDS),
        "policy_id": winner["policy_id"],
        "selection": winner["policy"]["selection"],
        "score_transformation": "rank order only" if winner["policy"]["scale_invariant"] else "absolute score",
        "scale_invariant": winner["policy"]["scale_invariant"],
        "cluster_algorithm": "DBSCAN",
        "dbscan_eps_angstrom": EPS,
        "dbscan_min_samples": MIN_SAMPLES,
        "minimum_cluster_size": MIN_CLUSTER_SIZE,
        "cluster_ranking_rule": winner["policy"]["ranking"],
        "threshold_records_by_seed": threshold_records,
        "selection_metrics": {k: winner[k] for k in (
            "composite_score", "mean_f1", "mean_label_jaccard", "mean_recall",
            "mean_precision", "valid_cluster_rate", "mean_seed_jaccard",
            "scale_robustness", "mean_selected_precluster_n", "mean_primary_cluster_n"
        )},
        "go_gate": spec["gate_for_final_1w60"],
        "source_hashes": source_hashes(source_paths),
        "rationale": (
            "Selected by the predeclared deterministic rule on independent non-PCNA "
            "calibration structures only. Prior PCNA/8GLA-derived extraction results are "
            "historical provenance and are not inputs to this selection."
        ),
    }
    frozen_path = OUT_DIR / "frozen_extraction_method.json"
    write_json(frozen_path, frozen)
    frozen_hash = sha256_path(frozen_path)

    selection = {
        "created_at": utc_now(),
        "predeclared_spec": str(spec_path.relative_to(REPO)),
        "predeclared_spec_sha256": spec_hash,
        "frozen_policy": str(frozen_path.relative_to(REPO)),
        "frozen_policy_sha256": frozen_hash,
        "eligible_structures": eligibility_table(rows_by_seed),
        "results_ranked": ranked_results,
        "selected_policy_id": winner["policy_id"],
        "pcna_used_for_selection": False,
    }
    write_json(OUT_DIR / "independent_extraction_selection_results.json", selection)
    write_selection_report(selection, REPORT_DIR / "INDEPENDENT_EXTRACTION_SELECTION_REPORT.md")
    print(f"wrote {spec_path}")
    print(f"wrote {frozen_path}")
    print(f"selected {winner['policy_id']} (policy hash {frozen_hash})")


def eligibility_table(rows_by_seed: dict[int, list[dict]]) -> list[dict]:
    first = rows_by_seed[SEEDS[0]]
    out = []
    for pdb_id in ELIGIBLE_IDS:
        rows = [r for r in first if r["pdb_id"] == pdb_id]
        out.append({
            "pdb_id": pdb_id,
            "eligible": True,
            "non_pcna": True,
            "not_8gla": True,
            "not_final_target_1w60": True,
            "not_checkpoint_selection_input": True,
            "homology_audit": "PASS per data/results/homology30_audit.json",
            "n_residues": len(rows),
            "n_positive": sum(r["label"] for r in rows),
        })
    for pdb_id, reason in EXCLUDED_IDS.items():
        out.append({"pdb_id": pdb_id, "eligible": False, "reason": reason})
    return out


def set_to_json(s: set[tuple[str, int]]) -> list[dict]:
    return [{"chain": c, "resid": r} for c, r in sorted(s)]


def symmetry_normalized(a: set[tuple[str, int]], b: set[tuple[str, int]]) -> float:
    # PCNA homotrimer symmetry can make the same biological interface appear on
    # another chain. This is supplementary; literal chain-aware Jaccard remains
    # the primary gate metric.
    chains = ("A", "B", "C")
    best = jaccard(a, b)
    for shift in (0, 1, 2):
        mapped = {(chains[(chains.index(c) + shift) % 3], r) if c in chains else (c, r) for c, r in b}
        best = max(best, jaccard(a, mapped))
    return best


def load_pcna_scores() -> dict[int, list[dict]]:
    out = {}
    for idx, seed in enumerate(SEEDS):
        path = PCNA_SCORE_DIR / f"run{idx}" / "1W60" / "scores.csv"
        if not path.exists():
            raise SystemExit(f"missing 1W60 score file for seed {seed}: {path}")
        rows = read_csv(path)
        for r in rows:
            r["pdb_id"] = "1W60"
        out[seed] = rows
    return out


def apply_1w60() -> None:
    frozen_path = OUT_DIR / "frozen_extraction_method.json"
    if not frozen_path.exists():
        raise SystemExit("run select-policy first; frozen_extraction_method.json is missing")
    policy = json.loads(frozen_path.read_text(encoding="utf-8"))
    policy_hash = sha256_path(frozen_path)
    rows_by_seed = load_pcna_scores()
    coords = load_ca_coords("1W60")

    seed_results = {}
    sets = []
    for seed in SEEDS:
        rows = rows_by_seed[seed]
        threshold = policy["threshold_records_by_seed"][str(seed)] if str(seed) in policy["threshold_records_by_seed"] else policy["threshold_records_by_seed"][seed]
        policy_stub = {
            "selection": policy["selection"],
            "threshold": 0.4,
            "ranking": policy["cluster_ranking_rule"],
        }
        selected = selected_for_policy(rows, policy_stub, threshold)
        clustered = cluster_selected(rows, selected, coords, policy["cluster_ranking_rule"])
        primary = clustered["primary"]
        sets.append(primary)
        ordered_rows = {((r["chain"], r["resid"])): r for r in rows}
        seed_results[str(seed)] = {
            "score_file": str((PCNA_SCORE_DIR / f"run{SEEDS.index(seed)}" / "1W60" / "scores.csv").relative_to(REPO)),
            "score_file_sha256": sha256_path(PCNA_SCORE_DIR / f"run{SEEDS.index(seed)}" / "1W60" / "scores.csv"),
            "selected_precluster_n": len(selected),
            "valid_primary_cluster": clustered["valid"],
            "primary_cluster_n": len(primary),
            "primary_cluster": set_to_json(primary),
            "cluster_count": len(clustered["clusters"]),
            "clusters": [
                {
                    **{k: v for k, v in c.items() if k != "residues"},
                    "residues": [{"chain": ch, "resid": rid} for ch, rid in c["residues"]],
                }
                for c in clustered["clusters"]
            ],
            "runner_up_margin": clustered["runner_up_margin"],
            "primary_mean_score": (
                statistics.mean(ordered_rows[k]["score"] for k in primary) if primary else None
            ),
            "score_distribution": {
                "mean": statistics.mean(r["score"] for r in rows),
                "max": max(r["score"] for r in rows),
                "min": min(r["score"] for r in rows),
            },
        }

    pairs = []
    sym_pairs = []
    for (i, a), (j, b) in combinations(enumerate(SEEDS), 2):
        pairs.append({"a": a, "b": b, "jaccard": jaccard(sets[i], sets[j])})
        sym_pairs.append({"a": a, "b": b, "jaccard": symmetry_normalized(sets[i], sets[j])})
    freq = Counter()
    for s in sets:
        freq.update(s)
    consensus = {k for k, n in freq.items() if n >= 2}

    rank_correlations = []
    for (i, a), (j, b) in combinations(enumerate(SEEDS), 2):
        rows_a = {(r["chain"], r["resid"]): r["score"] for r in rows_by_seed[a]}
        rows_b = {(r["chain"], r["resid"]): r["score"] for r in rows_by_seed[b]}
        keys = sorted(set(rows_a) & set(rows_b))
        rank_correlations.append({
            "a": a,
            "b": b,
            "spearman": spearman([rows_a[k] for k in keys], [rows_b[k] for k in keys]),
            "top50_jaccard": jaccard(
                set(sorted(keys, key=lambda k: rows_a[k], reverse=True)[:50]),
                set(sorted(keys, key=lambda k: rows_b[k], reverse=True)[:50]),
            ),
        })

    mean_j = statistics.mean(p["jaccard"] for p in pairs)
    valid_all = all(seed_results[str(s)]["valid_primary_cluster"] for s in SEEDS)
    positive_margins = all(
        (seed_results[str(s)]["runner_up_margin"] is None or seed_results[str(s)]["runner_up_margin"] > 0)
        for s in SEEDS
    )
    reasons = []
    if not valid_all:
        reasons.append("not every seed produced a valid primary cluster")
    if mean_j < 0.50:
        reasons.append(f"literal mean pairwise Jaccard {mean_j:.4f} < 0.50")
    if len(consensus) < 8:
        reasons.append(f"consensus residues {len(consensus)} < 8")
    if not positive_margins:
        reasons.append("a seed had a non-positive primary-vs-runner-up margin")
    verdict = "PASS" if not reasons else "FAIL"

    report = {
        "created_at": utc_now(),
        "git_commit": git_commit(),
        "production_md_started": False,
        "gate6_human_approval": "NOT_GRANTED_NOT_FABRICATED",
        "pdb": "1W60",
        "frozen_policy": str(frozen_path.relative_to(REPO)),
        "frozen_policy_sha256": policy_hash,
        "policy_id": policy["policy_id"],
        "predeclared_gate": policy["go_gate"],
        "seed_results": seed_results,
        "literal_pairwise_jaccard": pairs,
        "literal_mean_pairwise_jaccard": mean_j,
        "symmetry_normalized_pairwise_jaccard_supplementary": sym_pairs,
        "symmetry_mapping": "cyclic chain relabeling among A/B/C only; supplemental, not replacement for literal Jaccard",
        "consensus_n_residues": len(consensus),
        "consensus_residues": set_to_json(consensus),
        "residue_frequency": {f"{c}:{r}": n for (c, r), n in sorted(freq.items())},
        "rank_correlations": rank_correlations,
        "pre_md_stability": verdict,
        "reasons": reasons,
        "interpretation_limit": (
            "PASS permits a governed MD handoff only. It does not prove a binding site, "
            "druggability, ligand binding, or in-vivo pocket opening."
        ),
    }
    write_json(OUT_DIR / "final_1w60_three_seed_stability_report.json", report)
    write_json(OUT_DIR / "final_consensus_pocket_handoff.json", {
        "pdb": "1W60",
        "derived_from": "three-seed consensus under frozen independent extraction policy",
        "frozen_policy_sha256": policy_hash,
        "pocket_residues": report["consensus_residues"],
        "pocket_chains": sorted({r["chain"] for r in report["consensus_residues"]}),
        "pre_md_stability": verdict,
        "gate6_human_approval": "REQUIRED_BEFORE_MD",
    })
    write_final_report(report, REPORT_DIR / "FINAL_1W60_THREE_SEED_STABILITY_REPORT.md")
    print(f"PRE-MD STABILITY: {verdict}")
    print(f"literal mean Jaccard: {mean_j:.4f}; consensus residues: {len(consensus)}")


def write_selection_report(selection: dict, path: Path) -> None:
    lines = [
        "# Independent Extraction Selection Report",
        "",
        f"Created: {selection['created_at']}",
        f"Predeclared spec: `{selection['predeclared_spec']}`",
        f"Predeclared spec SHA-256: `{selection['predeclared_spec_sha256']}`",
        f"Frozen policy: `{selection['frozen_policy']}`",
        f"Frozen policy SHA-256: `{selection['frozen_policy_sha256']}`",
        "",
        "## Independence",
        "",
        "Selection used only non-PCNA calibration score/label rows for 1GQY, 2HNX, 2K1V, 2WER, and 3FU8. It did not read 1W60 score files.",
        "",
        "## Eligibility",
        "",
        "| PDB | Eligible | Rationale |",
        "| --- | --- | --- |",
    ]
    for row in selection["eligible_structures"]:
        rationale = row.get("reason") or f"non-PCNA, labels n={row.get('n_positive')}, homology audit PASS"
        lines.append(f"| {row['pdb_id']} | {row['eligible']} | {rationale} |")
    lines.extend([
        "",
        "## Results",
        "",
        "| Policy | Eligible | Composite | F1 | Recall | Precision | Label Jaccard | Seed Jaccard | Valid clusters |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for r in selection["results_ranked"]:
        lines.append(
            f"| {r['policy_id']} | {r['eligible_by_selection_rule']} | "
            f"{r['composite_score']:.4f} | {r['mean_f1']:.4f} | {r['mean_recall']:.4f} | "
            f"{r['mean_precision']:.4f} | {r['mean_label_jaccard']:.4f} | "
            f"{r['mean_seed_jaccard']:.4f} | {r['valid_cluster_rate']:.4f} |"
        )
    lines.extend([
        "",
        f"Selected policy: `{selection['selected_policy_id']}`.",
        "",
        "This report is not a PCNA stability result.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_final_report(report: dict, path: Path) -> None:
    lines = [
        "# Final 1W60 Three-Seed Stability Report",
        "",
        f"Created: {report['created_at']}",
        f"Frozen policy: `{report['frozen_policy']}`",
        f"Frozen policy SHA-256: `{report['frozen_policy_sha256']}`",
        f"Policy: `{report['policy_id']}`",
        "",
        "## Gate",
        "",
        "Predeclared PASS requires valid primary clusters in all three seeds, literal mean pairwise Jaccard >= 0.50, consensus >= 8 residues, and positive primary/runner-up margin where a runner-up exists.",
        "",
        "## Seed Results",
        "",
        "| Seed | Selected before clustering | Primary cluster | Cluster count | Runner-up margin | Mean score | Max score |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for seed, r in report["seed_results"].items():
        margin = "NA" if r["runner_up_margin"] is None else f"{r['runner_up_margin']:.6f}"
        lines.append(
            f"| {seed} | {r['selected_precluster_n']} | {r['primary_cluster_n']} | "
            f"{r['cluster_count']} | {margin} | {r['score_distribution']['mean']:.4f} | "
            f"{r['score_distribution']['max']:.4f} |"
        )
    lines.extend([
        "",
        "## Agreement",
        "",
        f"Literal mean pairwise Jaccard: `{report['literal_mean_pairwise_jaccard']:.4f}`.",
        "",
        "| Pair | Literal Jaccard | Symmetry-normalized supplementary Jaccard | Spearman | Top-50 Jaccard |",
        "| --- | ---: | ---: | ---: | ---: |",
    ])
    sym_lookup = {(p["a"], p["b"]): p["jaccard"] for p in report["symmetry_normalized_pairwise_jaccard_supplementary"]}
    corr_lookup = {(p["a"], p["b"]): p for p in report["rank_correlations"]}
    for p in report["literal_pairwise_jaccard"]:
        key = (p["a"], p["b"])
        corr = corr_lookup[key]
        lines.append(
            f"| {p['a']}-{p['b']} | {p['jaccard']:.4f} | {sym_lookup[key]:.4f} | "
            f"{corr['spearman']:.4f} | {corr['top50_jaccard']:.4f} |"
        )
    lines.extend([
        "",
        f"Consensus residues: `{report['consensus_n_residues']}`.",
        "",
        f"PRE-MD STABILITY: **{report['pre_md_stability']}**",
        "",
        "Interpretation: this gate only supports a governed MD handoff. It is not evidence of binding or druggability.",
    ])
    if report["reasons"]:
        lines.extend(["", "Failure reasons:", ""])
        lines.extend(f"- {r}" for r in report["reasons"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("select-policy")
    sub.add_parser("apply-1w60")
    args = ap.parse_args()
    if args.cmd == "select-policy":
        select_policy()
    elif args.cmd == "apply-1w60":
        apply_1w60()


if __name__ == "__main__":
    main()
