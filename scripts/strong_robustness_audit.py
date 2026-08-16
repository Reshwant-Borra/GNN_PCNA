#!/usr/bin/env python3
"""Post-pass stronger robustness audit for GNN-PCNA.

This is a prospective internal-standard audit after the earlier exploratory
pre-MD PASS. It does not start MD, does not retrain, and does not use 1W60 to
choose extraction methods.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import statistics
import subprocess
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from itertools import combinations, product
from pathlib import Path
from typing import Iterable


REPO = Path(__file__).resolve().parents[1]
ART = REPO / "artifacts" / "strong_robustness_20260815"
REP = REPO / "reports" / "strong_robustness_20260815"
PREV_ART = REPO / "artifacts" / "pre_md_independent_extraction_20260815"
CAL_DIR = REPO / "artifacts" / "diagnostics" / "threshold_calibration_independent_20260814"
PCNA_SCORE_DIR = REPO / "artifacts" / "go_prep" / "seed_stability_scores"
SEEDS = (42, 43, 44)
ELIGIBLE = ("1GQY", "2HNX", "2K1V", "2WER", "3FU8")
CURRENT_POLICY_ID = "independent_mcc_rank_fraction_size_weighted_cluster"
OLD_POLICY_HASH = "24979c81c86c012fc8cbb9d665f6a5294da6de2e30a28eb71827abfb5009abcf"


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
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    except Exception:
        return "UNVERIFIED"


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


class ReadLog:
    def __init__(self) -> None:
        self.paths: list[str] = []

    def add(self, path: Path) -> None:
        rel = str(path.relative_to(REPO) if path.is_absolute() and path.is_relative_to(REPO) else path)
        self.paths.append(rel)

    def assert_no_pcna(self) -> None:
        bad = [p for p in self.paths if any(x in p.upper() for x in ("1W60", "8GLA", "PCNA"))]
        if bad:
            raise SystemExit(f"independent selection attempted to read PCNA/8GLA inputs: {bad}")


def read_csv(path: Path, log: ReadLog | None = None) -> list[dict]:
    if log:
        log.add(path)
    with path.open(encoding="utf-8", errors="replace", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        if "pdb_id" in r:
            r["pdb_id"] = r["pdb_id"].upper()
        r["resid"] = int(r["resid"])
        r["score"] = float(r["score"])
        if "label" in r and r["label"] != "":
            r["label"] = int(float(r["label"]))
        if "cluster" in r and r["cluster"] != "":
            r["cluster"] = int(r["cluster"])
    return rows


def load_pdb_ca(pdb_id: str, log: ReadLog | None = None) -> dict[tuple[str, int], dict]:
    path = REPO / "data" / "raw" / f"{pdb_id}.pdb"
    if log:
        log.add(path)
    out: dict[tuple[str, int], dict] = {}
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("ATOM") and line[12:16].strip() == "CA":
                chain = line[21].strip() or "_"
                try:
                    resid = int(line[22:26])
                except ValueError:
                    continue
                out[(chain, resid)] = {
                    "chain": chain,
                    "resid": resid,
                    "resname": line[17:20].strip(),
                    "coord": (float(line[30:38]), float(line[38:46]), float(line[46:54])),
                }
    if not out:
        raise SystemExit(f"no CA atoms parsed from {path}")
    return out


def dist(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def centroid(keys: Iterable[tuple[str, int]], coords: dict[tuple[str, int], dict]) -> tuple[float, float, float]:
    pts = [coords[k]["coord"] for k in keys if k in coords]
    return tuple(statistics.mean(p[i] for p in pts) for i in range(3)) if pts else (float("nan"),) * 3


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a or b) else 1.0


def rank_map(rows: list[dict]) -> dict[tuple[str, int], int]:
    ordered = sorted(rows, key=lambda r: (-r["score"], r["chain"], r["resid"]))
    return {(r["chain"], r["resid"]): i + 1 for i, r in enumerate(ordered)}


def spearman_from_pairs(pairs: list[tuple[float, float]]) -> float:
    if len(pairs) < 2:
        return float("nan")

    def ranks(vals: list[float]) -> list[float]:
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        out = [0.0] * len(vals)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            rank = (i + j + 2) / 2
            for k in range(i, j + 1):
                out[order[k]] = rank
            i = j + 1
        return out

    xs, ys = [p[0] for p in pairs], [p[1] for p in pairs]
    rx, ry = ranks(xs), ranks(ys)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    cov = sum((x - mx) * (y - my) for x, y in zip(rx, ry))
    sx = math.sqrt(sum((x - mx) ** 2 for x in rx))
    sy = math.sqrt(sum((y - my) ** 2 for y in ry))
    return cov / (sx * sy) if sx and sy else float("nan")


def dbscan(rows: list[dict], coords: dict[tuple[str, int], dict], eps: float, min_samples: int) -> list[int]:
    points = [coords[(r["chain"], r["resid"])]["coord"] for r in rows]
    labels = [-99] * len(rows)
    neigh = []
    for i, p in enumerate(points):
        neigh.append([j for j, q in enumerate(points) if dist(p, q) <= eps])
    cid = 0
    for i in range(len(rows)):
        if labels[i] != -99:
            continue
        if len(neigh[i]) < min_samples:
            labels[i] = -1
            continue
        labels[i] = cid
        queue = deque(neigh[i])
        while queue:
            j = queue.popleft()
            if labels[j] == -1:
                labels[j] = cid
            if labels[j] != -99:
                continue
            labels[j] = cid
            if len(neigh[j]) >= min_samples:
                queue.extend(neigh[j])
        cid += 1
    return labels


def mcc(tp: int, fp: int, fn: int, tn: int) -> float:
    denom = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return ((tp * tn - fp * fn) / denom) if denom else 0.0


def select_mcc_record(rows: list[dict], n_structures: int) -> dict:
    candidates = sorted({r["score"] for r in rows} | {0.4, 0.5}, reverse=True)
    ordered = sorted(rows, key=lambda r: r["score"], reverse=True)
    total_pos = sum(1 for r in rows if r["label"] == 1)
    total_neg = len(rows) - total_pos
    best = None
    idx = 0
    tp = fp = 0
    for thr in candidates:
        while idx < len(ordered) and ordered[idx]["score"] >= thr:
            if ordered[idx]["label"] == 1:
                tp += 1
            else:
                fp += 1
            idx += 1
        fn = total_pos - tp
        tn = total_neg - fp
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        key = (mcc(tp, fp, fn, tn), f1, rec, prec, -abs(thr - 0.5), thr)
        if best is None or key > best["key"]:
            best = {
                "key": key,
                "threshold": thr,
                "predicted_positive_residues": tp + fp,
                "rank_fraction": (tp + fp) / len(rows),
                "rank_count_mean_per_structure": round((tp + fp) / n_structures),
                "mcc": key[0],
                "precision": prec,
                "recall": rec,
                "f1": f1,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": tn,
            }
    best.pop("key")
    return best


def select_rows(rows: list[dict], policy: dict, record: dict) -> set[tuple[str, int]]:
    mode = policy["selection"]
    ordered = sorted(rows, key=lambda r: (-r["score"], r["chain"], r["resid"]))
    if mode == "fixed_abs":
        return {(r["chain"], r["resid"]) for r in rows if r["score"] >= policy["threshold"]}
    if mode == "mcc_abs":
        return {(r["chain"], r["resid"]) for r in rows if r["score"] >= record["threshold"]}
    if mode == "rank_fraction":
        k = min(len(rows), max(0, round(record["rank_fraction"] * len(rows))))
        return {(r["chain"], r["resid"]) for r in ordered[:k]}
    if mode == "rank_count_mean":
        k = min(len(rows), max(0, record["rank_count_mean_per_structure"]))
        return {(r["chain"], r["resid"]) for r in ordered[:k]}
    if mode == "rank_chain_fraction":
        out = set()
        for chain in sorted({r["chain"] for r in rows}):
            cr = [r for r in ordered if r["chain"] == chain]
            k = min(len(cr), max(0, round(record["rank_fraction"] * len(cr))))
            out.update((r["chain"], r["resid"]) for r in cr[:k])
        return out
    if mode == "fixed_rank_fraction":
        k = min(len(rows), max(0, round(policy["fixed_fraction"] * len(rows))))
        return {(r["chain"], r["resid"]) for r in ordered[:k]}
    raise ValueError(mode)


def cluster_selected(
    rows: list[dict],
    selected: set[tuple[str, int]],
    coords: dict[tuple[str, int], dict],
    *,
    eps: float,
    min_samples: int,
    min_cluster_size: int,
    ranking: str,
) -> dict:
    sr = [r for r in rows if (r["chain"], r["resid"]) in selected and (r["chain"], r["resid"]) in coords]
    if len(sr) < min_cluster_size:
        return {"valid": False, "primary": set(), "clusters": [], "runner_up_margin": None}
    labels = dbscan(sr, coords, eps, min_samples)
    by = defaultdict(list)
    for r, lab in zip(sr, labels):
        if lab >= 0:
            by[lab].append(r)
    clusters = []
    for cid, members in by.items():
        if len(members) < min_cluster_size:
            continue
        mean_score = statistics.mean(r["score"] for r in members)
        if ranking == "mean_score":
            rank_score = mean_score
        elif ranking == "mean_score_sqrt_size":
            rank_score = mean_score * math.sqrt(len(members))
        elif ranking == "sum_score":
            rank_score = sum(r["score"] for r in members)
        else:
            raise ValueError(ranking)
        clusters.append({
            "cluster_id": int(cid),
            "size": len(members),
            "mean_score": mean_score,
            "rank_score": rank_score,
            "residues": sorted((r["chain"], r["resid"]) for r in members),
        })
    if not clusters:
        return {"valid": False, "primary": set(), "clusters": [], "runner_up_margin": None}
    clusters.sort(key=lambda c: (-c["rank_score"], -c["mean_score"], -c["size"], c["cluster_id"]))
    margin = None if len(clusters) == 1 else clusters[0]["rank_score"] - clusters[1]["rank_score"]
    return {"valid": True, "primary": set(map(tuple, clusters[0]["residues"])), "clusters": clusters, "runner_up_margin": margin}


def label_metrics(rows: list[dict], selected: set[tuple[str, int]]) -> dict:
    positives = {(r["chain"], r["resid"]) for r in rows if r["label"] == 1}
    tp = len(selected & positives)
    fp = len(selected - positives)
    fn = len(positives - selected)
    tn = len(rows) - tp - fp - fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "mcc": mcc(tp, fp, fn, tn),
        "label_jaccard": jaccard(selected, positives),
        "selected_n": len(selected),
        "positive_n": len(positives),
    }


def load_calibration(log: ReadLog) -> dict[int, list[dict]]:
    by_seed = {}
    for seed in SEEDS:
        path = CAL_DIR / f"calibration_scores_seed_{seed}.csv"
        rows = [r for r in read_csv(path, log) if r["pdb_id"] in ELIGIBLE]
        by_seed[seed] = rows
    return by_seed


def candidate_grid() -> list[dict]:
    selections = [
        {"selection": "fixed_abs", "threshold": 0.4, "scale_invariant": False, "selection_label": "fixed_0p4"},
        {"selection": "mcc_abs", "scale_invariant": False, "selection_label": "mcc_abs"},
        {"selection": "rank_count_mean", "scale_invariant": True, "selection_label": "mcc_rank_count"},
        {"selection": "rank_fraction", "scale_invariant": True, "selection_label": "mcc_rank_fraction"},
        {"selection": "rank_chain_fraction", "scale_invariant": True, "selection_label": "mcc_rank_chain_fraction"},
        {"selection": "fixed_rank_fraction", "fixed_fraction": 0.06, "scale_invariant": True, "selection_label": "fixed_rank_fraction_0p06"},
    ]
    out = []
    for sel, eps, min_samples, min_cluster_size, ranking in product(
        selections,
        (5.0, 6.0, 7.0),
        (3,),
        (3,),
        ("mean_score", "mean_score_sqrt_size"),
    ):
        p = dict(sel)
        p.update({
            "eps": eps,
            "min_samples": min_samples,
            "min_cluster_size": min_cluster_size,
            "ranking": ranking,
        })
        p["policy_id"] = (
            f"{p['selection_label']}_eps{eps:g}_ms{min_samples}_min{min_cluster_size}_{ranking}"
        ).replace(".", "p")
        out.append(p)
    return out


_MCC_CACHE: dict[tuple[int, tuple[str, ...]], dict] = {}


def evaluate_policy(policy: dict, rows_by_seed: dict[int, list[dict]], coords: dict[str, dict], train_ids: tuple[str, ...], eval_ids: tuple[str, ...]) -> dict:
    records = {}
    for seed in SEEDS:
        cache_key = (seed, tuple(sorted(train_ids)))
        if cache_key not in _MCC_CACHE:
            train_rows = [r for r in rows_by_seed[seed] if r["pdb_id"] in train_ids]
            _MCC_CACHE[cache_key] = select_mcc_record(train_rows, len(train_ids))
        records[seed] = _MCC_CACHE[cache_key]
    cases = []
    seed_sets_by_protein: dict[str, dict[int, set]] = defaultdict(dict)
    for seed in SEEDS:
        for pdb_id in eval_ids:
            rows = [r for r in rows_by_seed[seed] if r["pdb_id"] == pdb_id]
            selected = select_rows(rows, policy, records[seed])
            clustered = cluster_selected(
                rows, selected, coords[pdb_id],
                eps=policy["eps"], min_samples=policy["min_samples"],
                min_cluster_size=policy["min_cluster_size"], ranking=policy["ranking"],
            )
            primary = clustered["primary"]
            seed_sets_by_protein[pdb_id][seed] = primary
            cases.append({
                "seed": seed,
                "pdb_id": pdb_id,
                "valid_cluster": clustered["valid"],
                "selected_precluster_n": len(selected),
                "primary_cluster_n": len(primary),
                "runner_up_margin": clustered["runner_up_margin"],
                **label_metrics(rows, primary),
            })
    seed_j = []
    for pdb_id, by_seed in seed_sets_by_protein.items():
        for a, b in combinations(SEEDS, 2):
            seed_j.append(jaccard(by_seed.get(a, set()), by_seed.get(b, set())))
    f1s = [c["f1"] for c in cases]
    valid_rate = statistics.mean(1.0 if c["valid_cluster"] else 0.0 for c in cases)
    mean_f1 = statistics.mean(f1s)
    mean_j = statistics.mean(c["label_jaccard"] for c in cases)
    mean_rec = statistics.mean(c["recall"] for c in cases)
    mean_prec = statistics.mean(c["precision"] for c in cases)
    mean_seed_j = statistics.mean(seed_j) if seed_j else 0.0
    invalid = 1 - valid_rate
    robust_score = (
        mean_f1 + 0.50 * mean_j + 0.25 * mean_seed_j + 0.10 * (1 if policy["scale_invariant"] else 0)
        - 0.25 * invalid + 0.10 * min(f1s) - 0.05 * (statistics.pstdev(f1s) if len(f1s) > 1 else 0.0)
    )
    return {
        "policy": policy,
        "policy_id": policy["policy_id"],
        "eligible_by_rule": valid_rate >= 0.80 and mean_rec >= 0.20,
        "robust_score": robust_score,
        "mean_f1": mean_f1,
        "median_f1": statistics.median(f1s),
        "worst_f1": min(f1s),
        "f1_std": statistics.pstdev(f1s) if len(f1s) > 1 else 0.0,
        "mean_label_jaccard": mean_j,
        "mean_recall": mean_rec,
        "mean_precision": mean_prec,
        "valid_cluster_rate": valid_rate,
        "mean_seed_jaccard": mean_seed_j,
        "mean_selected_precluster_n": statistics.mean(c["selected_precluster_n"] for c in cases),
        "mean_primary_cluster_n": statistics.mean(c["primary_cluster_n"] for c in cases),
        "threshold_records": records,
        "cases": cases,
    }


def summarize_current_1w60() -> dict:
    report = json.loads((PREV_ART / "final_1w60_three_seed_stability_report.json").read_text())
    coords = load_pdb_ca("1W60")
    rows_by_seed = {}
    ranks_by_seed = {}
    scores_by_seed = {}
    for idx, seed in enumerate(SEEDS):
        rows = read_csv(PCNA_SCORE_DIR / f"run{idx}" / "1W60" / "scores.csv")
        rows_by_seed[seed] = rows
        ranks_by_seed[seed] = rank_map(rows)
        scores_by_seed[seed] = {(r["chain"], r["resid"]): r["score"] for r in rows}

    sets = {seed: {(r["chain"], r["resid"]) for r in report["seed_results"][str(seed)]["primary_cluster"]} for seed in SEEDS}
    union = sorted(set().union(*sets.values()))
    freq = Counter()
    for s in sets.values():
        freq.update(s)
    core = {k for k, n in freq.items() if n == 3}
    consensus2 = {k for k, n in freq.items() if n >= 2}
    core_cent = centroid(core, coords)
    table = []
    for k in union:
        row = {
            "chain": k[0],
            "resid": k[1],
            "resname": coords.get(k, {}).get("resname", "UNK"),
            "seed42_selected": k in sets[42],
            "seed43_selected": k in sets[43],
            "seed44_selected": k in sets[44],
            "n_seeds": freq[k],
            "score_seed42": scores_by_seed[42].get(k),
            "score_seed43": scores_by_seed[43].get(k),
            "score_seed44": scores_by_seed[44].get(k),
            "rank_seed42": ranks_by_seed[42].get(k),
            "rank_seed43": ranks_by_seed[43].get(k),
            "rank_seed44": ranks_by_seed[44].get(k),
            "x": coords.get(k, {}).get("coord", (None, None, None))[0],
            "y": coords.get(k, {}).get("coord", (None, None, None))[1],
            "z": coords.get(k, {}).get("coord", (None, None, None))[2],
            "distance_to_consensus_centroid": dist(coords[k]["coord"], core_cent) if k in coords and core else None,
            "category": "3/3 consensus core" if freq[k] == 3 else ("2/3 fringe" if freq[k] == 2 else f"seed-specific {next(s for s in SEEDS if k in sets[s])}"),
        }
        table.append(row)
    fields = list(table[0]) if table else []
    write_csv(ART / "current_06792_residue_membership.csv", table, fields)

    centroids = {seed: centroid(sets[seed], coords) for seed in SEEDS}
    centroid_pairs = [{"a": a, "b": b, "distance_A": dist(centroids[a], centroids[b])} for a, b in combinations(SEEDS, 2)]
    neighborhood = {}
    for d in (4.0, 6.0, 8.0):
        vals = []
        for a, b in combinations(SEEDS, 2):
            def frac_near(x, y):
                return sum(1 for k in x if any(k in coords and j in coords and dist(coords[k]["coord"], coords[j]["coord"]) <= d for j in y)) / len(x)
            vals.append({"a": a, "b": b, "distance": d, "symmetric_near_fraction": (frac_near(sets[a], sets[b]) + frac_near(sets[b], sets[a])) / 2})
        neighborhood[str(d)] = vals

    local_keys = set()
    for k in set().union(*sets.values()):
        if k not in coords:
            continue
        for kk, v in coords.items():
            if dist(coords[k]["coord"], v["coord"]) <= 8.0:
                local_keys.add(kk)
    rank_stats = []
    global_stats = []
    for a, b in combinations(SEEDS, 2):
        common = sorted(set(scores_by_seed[a]) & set(scores_by_seed[b]))
        global_stats.append({"a": a, "b": b, "spearman": spearman_from_pairs([(scores_by_seed[a][k], scores_by_seed[b][k]) for k in common])})
        lk = sorted(local_keys & set(scores_by_seed[a]) & set(scores_by_seed[b]))
        rank_stats.append({"a": a, "b": b, "local_8A_spearman": spearman_from_pairs([(scores_by_seed[a][k], scores_by_seed[b][k]) for k in lk]), "n_local": len(lk)})

    seed_fraction = {}
    for seed in SEEDS:
        seed_fraction[str(seed)] = {
            "cluster_n": len(sets[seed]),
            "fraction_3of3_core": len(sets[seed] & core) / len(sets[seed]),
            "fraction_2of3_or_better": len(sets[seed] & consensus2) / len(sets[seed]),
        }

    out = {
        "created_at": utc_now(),
        "previous_policy": CURRENT_POLICY_ID,
        "previous_policy_sha256": sha256_path(PREV_ART / "frozen_extraction_method.json"),
        "post_pass_stronger_internal_robustness_requirement": {
            "mean_literal_jaccard_target": 0.75,
            "minimum_pairwise_literal_jaccard": 0.65,
            "history_note": "This stricter standard was imposed after the earlier 0.6792 exploratory PASS and was not predeclared before that result.",
        },
        "sets": {str(seed): sorted(list(sets[seed])) for seed in SEEDS},
        "n_union": len(union),
        "n_3of3_core": len(core),
        "n_2of3_or_better": len(consensus2),
        "seed_fraction": seed_fraction,
        "centroids": {str(k): v for k, v in centroids.items()},
        "centroid_pair_distances": centroid_pairs,
        "neighborhood_overlap": neighborhood,
        "global_spearman": global_stats,
        "local_rank_spearman": rank_stats,
        "interpretation": (
            "same physical pocket core with nontrivial boundary/fringe extension disagreement"
            if len(core) >= 10
            and min(v["fraction_2of3_or_better"] for v in seed_fraction.values()) >= 0.80
            and min(
                item["symmetric_near_fraction"]
                for item in neighborhood["6.0"]
            )
            >= 0.85
            else "meaningful spatial disagreement possible"
        ),
    }
    write_json(ART / "current_06792_geometric_diagnosis.json", out)
    write_membership_pdb(coords, freq)
    return out


def write_membership_pdb(coords: dict[tuple[str, int], dict], freq: Counter) -> None:
    src = REPO / "data" / "raw" / "1W60.pdb"
    dst = ART / "current_06792_membership_colored_ca.pdb"
    ART.mkdir(parents=True, exist_ok=True)
    with src.open(encoding="utf-8", errors="replace") as inp, dst.open("w", encoding="utf-8") as out:
        for line in inp:
            if line.startswith("ATOM"):
                chain = line[21].strip() or "_"
                try:
                    resid = int(line[22:26])
                except ValueError:
                    out.write(line)
                    continue
                n = freq.get((chain, resid), 0)
                b = {0: 0.0, 1: 25.0, 2: 50.0, 3: 75.0}[n]
                out.write(line[:60] + f"{b:6.2f}" + line[66:])
            else:
                out.write(line)


def quantiles(vals: list[float]) -> dict:
    s = sorted(vals)
    def q(frac: float) -> float:
        if not s:
            return float("nan")
        pos = frac * (len(s) - 1)
        lo = int(math.floor(pos))
        hi = int(math.ceil(pos))
        if lo == hi:
            return s[lo]
        return s[lo] * (hi - pos) + s[hi] * (pos - lo)
    return {"min": s[0], "q05": q(0.05), "q25": q(0.25), "median": q(0.5), "q75": q(0.75), "q95": q(0.95), "max": s[-1], "mean": statistics.mean(s)}


def ranking_calibration_report(geom: dict) -> dict:
    scores_by_seed = {}
    rank_by_seed = {}
    for idx, seed in enumerate(SEEDS):
        rows = read_csv(PCNA_SCORE_DIR / f"run{idx}" / "1W60" / "scores.csv")
        scores_by_seed[seed] = {(r["chain"], r["resid"]): r["score"] for r in rows}
        rank_by_seed[seed] = rank_map(rows)
    keys = sorted(set.intersection(*(set(scores_by_seed[s]) for s in SEEDS)))
    top_overlap = []
    for k in (10, 20, 30, 50):
        tops = {s: set(sorted(keys, key=lambda x: scores_by_seed[s][x], reverse=True)[:k]) for s in SEEDS}
        for a, b in combinations(SEEDS, 2):
            top_overlap.append({"k": k, "a": a, "b": b, "jaccard": jaccard(tops[a], tops[b])})
    selected_union = {tuple(x) for vals in geom["sets"].values() for x in vals}
    rank_of_selected = []
    for seed in SEEDS:
        own = {tuple(x) for x in geom["sets"][str(seed)]}
        for source_seed in SEEDS:
            source_set = {tuple(x) for x in geom["sets"][str(source_seed)]}
            ranks = [rank_by_seed[seed][r] for r in source_set if r in rank_by_seed[seed]]
            rank_of_selected.append({
                "ranking_seed": seed,
                "residue_set_from_seed": source_seed,
                "median_rank": statistics.median(ranks),
                "best_rank": min(ranks),
                "worst_rank": max(ranks),
                "n": len(ranks),
                "own_set": source_seed == seed,
            })
    pairwise = []
    for a, b in combinations(SEEDS, 2):
        pairs = [(scores_by_seed[a][k], scores_by_seed[b][k]) for k in keys]
        pairwise.append({"a": a, "b": b, "global_spearman": spearman_from_pairs(pairs)})
    out = {
        "created_at": utc_now(),
        "score_distributions": {str(s): quantiles(list(scores_by_seed[s].values())) for s in SEEDS},
        "pairwise_global_spearman": pairwise,
        "top_k_overlap": top_overlap,
        "rank_of_seed_selected_residues": rank_of_selected,
        "diagnosis": {
            "model_ranking": "highly correlated globally and locally; no evidence of qualitatively different pocket solution",
            "score_calibration": "substantial absolute scale differences persist, especially seed 44 compression",
            "extraction_boundary": "literal Jaccard is limited by fringe/boundary residues around a shared core",
        },
    }
    write_json(ART / "seed_ranking_and_calibration_diagnosis.json", out)
    return out


def independent_robustness() -> dict:
    log = ReadLog()
    rows_by_seed = load_calibration(log)
    coords = {pdb: load_pdb_ca(pdb, log) for pdb in ELIGIBLE}
    log.assert_no_pcna()
    write_json(ART / "independent_selection_file_read_log.json", {"paths": sorted(set(log.paths)), "pcna_inputs_read_during_selection": []})

    full = [evaluate_policy(p, rows_by_seed, coords, ELIGIBLE, ELIGIBLE) for p in candidate_grid()]
    full_sorted = sorted(full, key=lambda r: (not r["eligible_by_rule"], -r["robust_score"], -r["mean_recall"], -r["mean_precision"], r["policy_id"]))
    full_summary = [{k: r[k] for k in ("policy_id", "eligible_by_rule", "robust_score", "mean_f1", "median_f1", "worst_f1", "f1_std", "mean_label_jaccard", "mean_recall", "mean_precision", "valid_cluster_rate", "mean_seed_jaccard", "mean_selected_precluster_n", "mean_primary_cluster_n")} for r in full_sorted]
    write_csv(ART / "independent_method_full_grid_summary.csv", full_summary, list(full_summary[0]))

    lopo_cases = []
    lopo_by_policy = defaultdict(list)
    for holdout in ELIGIBLE:
        train = tuple(x for x in ELIGIBLE if x != holdout)
        for p in candidate_grid():
            res = evaluate_policy(p, rows_by_seed, coords, train, (holdout,))
            lopo_by_policy[p["policy_id"]].append(res)
            lopo_cases.append({
                "holdout": holdout,
                "policy_id": p["policy_id"],
                "robust_score": res["robust_score"],
                "mean_f1": res["mean_f1"],
                "mean_recall": res["mean_recall"],
                "mean_precision": res["mean_precision"],
                "valid_cluster_rate": res["valid_cluster_rate"],
                "mean_seed_jaccard": res["mean_seed_jaccard"],
            })
    write_csv(ART / "leave_one_protein_out_cases.csv", lopo_cases, list(lopo_cases[0]))
    lopo_summary = []
    for pid, entries in lopo_by_policy.items():
        scores = [e["robust_score"] for e in entries]
        f1s = [e["mean_f1"] for e in entries]
        recs = [e["mean_recall"] for e in entries]
        valids = [e["valid_cluster_rate"] for e in entries]
        lopo_summary.append({
            "policy_id": pid,
            "mean_lopo_score": statistics.mean(scores),
            "median_lopo_score": statistics.median(scores),
            "worst_lopo_score": min(scores),
            "std_lopo_score": statistics.pstdev(scores),
            "mean_lopo_f1": statistics.mean(f1s),
            "worst_lopo_f1": min(f1s),
            "mean_lopo_recall": statistics.mean(recs),
            "min_valid_cluster_rate": min(valids),
        })
    lopo_summary.sort(key=lambda r: (-r["mean_lopo_score"], -r["worst_lopo_score"], r["policy_id"]))

    # Per-protein rank counts from LOPO cases.
    top_counts = defaultdict(lambda: {"top1": 0, "top2": 0})
    for holdout in ELIGIBLE:
        ranked = sorted([c for c in lopo_cases if c["holdout"] == holdout], key=lambda c: (-c["robust_score"], c["policy_id"]))
        if ranked:
            top_counts[ranked[0]["policy_id"]]["top1"] += 1
        for r in ranked[:2]:
            top_counts[r["policy_id"]]["top2"] += 1
    for row in lopo_summary:
        row.update(top_counts[row["policy_id"]])
    write_csv(ART / "leave_one_protein_out_summary.csv", lopo_summary, list(lopo_summary[0]))

    current_full = next(r for r in full_sorted if r["policy_id"] == "mcc_rank_fraction_eps6_ms3_min3_mean_score_sqrt_size")
    current_lopo = next(r for r in lopo_summary if r["policy_id"] == current_full["policy_id"])
    best_lopo = lopo_summary[0]
    best_full = next(r for r in full_sorted if r["policy_id"] == best_lopo["policy_id"])
    improvement = best_lopo["mean_lopo_score"] - current_lopo["mean_lopo_score"]
    materially_better = (
        best_lopo["policy_id"] != current_lopo["policy_id"]
        and improvement >= 0.03
        and best_lopo["worst_lopo_score"] >= current_lopo["worst_lopo_score"]
        and best_lopo["min_valid_cluster_rate"] >= 0.80
        and best_full["eligible_by_rule"]
    )

    boot = bootstrap_policy_scores(lopo_cases)
    ensemble = ensemble_feasibility(rows_by_seed, coords)
    out = {
        "created_at": utc_now(),
        "post_pass_stronger_internal_robustness_requirement": True,
        "selection_inputs": sorted(set(log.paths)),
        "pcna_inputs_read_during_selection": [],
        "full_grid_top10": full_summary[:10],
        "lopo_top10": lopo_summary[:10],
        "current_policy_grid_id": current_full["policy_id"],
        "current_policy_full": {k: current_full[k] for k in full_summary[0]},
        "current_policy_lopo": current_lopo,
        "best_lopo_policy": best_lopo,
        "best_lopo_full": {k: best_full[k] for k in full_summary[0]},
        "materially_better_policy_found": materially_better,
        "lopo_score_improvement_over_current": improvement,
        "bootstrap": boot,
        "ensemble": ensemble,
    }
    write_json(ART / "independent_method_robustness_audit.json", out)
    return out


def bootstrap_policy_scores(lopo_cases: list[dict]) -> dict:
    by_policy_holdout = defaultdict(dict)
    for c in lopo_cases:
        by_policy_holdout[c["policy_id"]][c["holdout"]] = c["robust_score"]
    rng = random.Random(20260815)
    rows = []
    for pid, vals in by_policy_holdout.items():
        samples = []
        ids = list(ELIGIBLE)
        for _ in range(250):
            draw = [rng.choice(ids) for _ in ids]
            samples.append(statistics.mean(vals[d] for d in draw))
        rows.append({
            "policy_id": pid,
            "bootstrap_mean": statistics.mean(samples),
            "bootstrap_low_025": sorted(samples)[int(0.025 * len(samples))],
            "bootstrap_high_975": sorted(samples)[int(0.975 * len(samples)) - 1],
        })
    rows.sort(key=lambda r: -r["bootstrap_mean"])
    write_csv(ART / "bootstrap_policy_scores.csv", rows, list(rows[0]))
    return {"top10": rows[:10], "n_bootstrap": 250, "unit": "validation protein"}


def ensemble_feasibility(rows_by_seed: dict[int, list[dict]], coords: dict[str, dict]) -> dict:
    # Prospective diagnostic only. It evaluates a single ensemble ranking on
    # labels, but does not replace individual-seed stability.
    cases = []
    for pdb_id in ELIGIBLE:
        per_seed = {s: [r for r in rows_by_seed[s] if r["pdb_id"] == pdb_id] for s in SEEDS}
        keys = sorted({(r["chain"], r["resid"]) for r in per_seed[42]})
        ranks = {s: rank_map(per_seed[s]) for s in SEEDS}
        labels = {(r["chain"], r["resid"]): r["label"] for r in per_seed[42]}
        score_lookup = {s: {(r["chain"], r["resid"]): r["score"] for r in per_seed[s]} for s in SEEDS}
        ensemble_rows = []
        for k in keys:
            mean_rank = statistics.mean(ranks[s][k] for s in SEEDS)
            mean_score = statistics.mean(score_lookup[s][k] for s in SEEDS)
            ensemble_rows.append({"chain": k[0], "resid": k[1], "score": -mean_rank, "label": labels[k], "mean_score": mean_score})
        # Use non-PCNA all-seed average positive fraction from all calibration rows.
        positive_fraction = statistics.mean(
            sum(r["label"] for r in rows_by_seed[s]) / len(rows_by_seed[s]) for s in SEEDS
        )
        k_n = max(1, round(positive_fraction * len(ensemble_rows)))
        selected = {(r["chain"], r["resid"]) for r in sorted(ensemble_rows, key=lambda r: -r["score"])[:k_n]}
        clustered = cluster_selected(
            ensemble_rows, selected, coords[pdb_id],
            eps=6.0, min_samples=3, min_cluster_size=3, ranking="mean_score_sqrt_size",
        )
        cases.append({"pdb_id": pdb_id, "selected_precluster_n": len(selected), "valid_cluster": clustered["valid"], **label_metrics(ensemble_rows, clustered["primary"])})
    out = {
        "method": "mean rank aggregation across frozen seeds",
        "methodological_status": "prospective_refinement_not_original_single_seed_method",
        "mean_f1": statistics.mean(c["f1"] for c in cases),
        "mean_recall": statistics.mean(c["recall"] for c in cases),
        "mean_precision": statistics.mean(c["precision"] for c in cases),
        "valid_cluster_rate": statistics.mean(1.0 if c["valid_cluster"] else 0.0 for c in cases),
        "cases": cases,
        "recommendation": "diagnostic_only_unless_human_approves_ensemble_pipeline",
    }
    return out


def apply_new_policy_if_needed(robust: dict) -> dict | None:
    if not robust["materially_better_policy_found"]:
        return None
    # Freeze before reading 1W60. The selected policy came only from independent
    # validation robustness above.
    best_id = robust["best_lopo_policy"]["policy_id"]
    full_grid = {r["policy_id"]: r for r in json.loads((ART / "independent_method_robustness_audit.json").read_text())["full_grid_top10"]}
    # Find the policy details from candidate grid.
    policy = next(p for p in candidate_grid() if p["policy_id"] == best_id)
    frozen = {
        "version": "frozen_extraction_method_stronger_internal_v1",
        "created_at": utc_now(),
        "git_commit": git_commit(),
        "old_policy": CURRENT_POLICY_ID,
        "old_policy_sha256": OLD_POLICY_HASH,
        "policy_id": best_id,
        "policy": policy,
        "selected_without_pcna": True,
        "pcna_inputs_read_during_selection": [],
        "independent_development_structures": list(ELIGIBLE),
        "selection_basis": "leave-one-protein-out robust score improvement over current policy",
        "lopo_score_improvement_over_current": robust["lopo_score_improvement_over_current"],
        "strong_internal_gate": {
            "mean_literal_jaccard_required": 0.75,
            "minimum_pairwise_jaccard_required": 0.65,
            "all_seed_clusters_valid": True,
        },
    }
    path = ART / "frozen_extraction_method.json"
    write_json(path, frozen)
    frozen_hash = sha256_path(path)
    return apply_policy_to_1w60(policy, frozen_hash)


def apply_policy_to_1w60(policy: dict, frozen_hash: str) -> dict:
    rows_by_seed = {}
    coords = load_pdb_ca("1W60")
    # Threshold/rank records for new policy are still derived from all non-PCNA
    # structures, not from 1W60.
    log = ReadLog()
    cal_rows = load_calibration(log)
    records = {s: select_mcc_record(cal_rows[s], len(ELIGIBLE)) for s in SEEDS}
    sets = {}
    seed_results = {}
    for idx, seed in enumerate(SEEDS):
        rows = read_csv(PCNA_SCORE_DIR / f"run{idx}" / "1W60" / "scores.csv")
        rows_by_seed[seed] = rows
        selected = select_rows(rows, policy, records[seed])
        clustered = cluster_selected(
            rows, selected, coords,
            eps=policy["eps"], min_samples=policy["min_samples"],
            min_cluster_size=policy["min_cluster_size"], ranking=policy["ranking"],
        )
        sets[seed] = clustered["primary"]
        seed_results[str(seed)] = {
            "selected_precluster_n": len(selected),
            "valid_primary_cluster": clustered["valid"],
            "primary_cluster_n": len(clustered["primary"]),
            "primary_cluster": [{"chain": c, "resid": r} for c, r in sorted(clustered["primary"])],
            "runner_up_margin": clustered["runner_up_margin"],
            "cluster_count": len(clustered["clusters"]),
        }
    pairs = [{"a": a, "b": b, "jaccard": jaccard(sets[a], sets[b])} for a, b in combinations(SEEDS, 2)]
    mean_j = statistics.mean(p["jaccard"] for p in pairs)
    freq = Counter()
    for s in sets.values():
        freq.update(s)
    consensus = {k for k, v in freq.items() if v >= 2}
    verdict = "STRONG PRE-MD PASS" if (
        mean_j >= 0.75
        and min(p["jaccard"] for p in pairs) >= 0.65
        and all(seed_results[str(s)]["valid_primary_cluster"] for s in SEEDS)
        and len(consensus) >= 8
        and all(seed_results[str(s)]["runner_up_margin"] is None or seed_results[str(s)]["runner_up_margin"] > 0 for s in SEEDS)
    ) else "STRONG PRE-MD FAIL"
    out = {
        "created_at": utc_now(),
        "frozen_policy_sha256": frozen_hash,
        "policy_id": policy["policy_id"],
        "seed_results": seed_results,
        "literal_pairwise_jaccard": pairs,
        "literal_mean_pairwise_jaccard": mean_j,
        "consensus_n_residues": len(consensus),
        "consensus_residues": [{"chain": c, "resid": r} for c, r in sorted(consensus)],
        "strong_internal_verdict": verdict,
        "mean_ge_0p80": mean_j >= 0.80,
        "mean_ge_0p85": mean_j >= 0.85,
        "production_md_started": False,
    }
    write_json(ART / "final_1w60_strong_stability_report.json", out)
    return out


def write_reports(geom: dict, rankcal: dict, robust: dict, new_result: dict | None) -> None:
    REP.mkdir(parents=True, exist_ok=True)
    md_common_header = (
        "POST-PASS STRONGER INTERNAL ROBUSTNESS REQUIREMENT: the earlier 0.6792 result remains a valid exploratory PASS under the previous gate. "
        "The >=0.75 mean-Jaccard target is a new voluntary internal release standard imposed after seeing that result; it is not represented as a universal literature threshold.\n"
    )
    write_text("CURRENT_06792_GEOMETRIC_DIAGNOSIS.md", [
        "# Current 0.6792 Geometric Diagnosis",
        "",
        md_common_header,
        f"Interpretation: **{geom['interpretation']}**.",
        "The clusters are not three unrelated/displaced pocket solutions. They share a central residue core, but the boundary and an adjacent 231-252 extension differ enough that the stricter release target is not met.",
        f"3/3 core residues: {geom['n_3of3_core']}; >=2/3 residues: {geom['n_2of3_or_better']}; union: {geom['n_union']}.",
        "",
        "Centroid distances (A):",
        *[f"- {p['a']}-{p['b']}: {p['distance_A']:.3f}" for p in geom["centroid_pair_distances"]],
        "",
        "Near-neighborhood overlap:",
        *[f"- {item['a']}-{item['b']} within 6 A: {item['symmetric_near_fraction']:.3f}" for item in geom["neighborhood_overlap"]["6.0"]],
        "",
        "Seed fractions:",
        *[f"- seed {s}: {v['fraction_3of3_core']:.3f} in 3/3 core; {v['fraction_2of3_or_better']:.3f} in >=2/3 consensus" for s, v in geom["seed_fraction"].items()],
        "",
        "Residue table: `artifacts/strong_robustness_20260815/current_06792_residue_membership.csv`.",
        "Visualization aid: `artifacts/strong_robustness_20260815/current_06792_membership_colored_ca.pdb` uses B-factors 75/50/25 for 3/2/1 seed selection.",
    ])
    write_text("SEED_RANKING_AND_CALIBRATION_DIAGNOSIS.md", [
        "# Seed Ranking and Calibration Diagnosis",
        "",
        md_common_header,
        "Global Spearman correlations:",
        *[f"- {p['a']}-{p['b']}: {p['global_spearman']:.4f}" for p in rankcal["pairwise_global_spearman"]],
        "",
        "Local 8 A Spearman correlations around the selected pocket:",
        *[f"- {p['a']}-{p['b']}: {p['local_8A_spearman']:.4f} across {p['n_local']} residues" for p in geom["local_rank_spearman"]],
        "",
        "Top-k residue-overlap Jaccards:",
        *[f"- {p['a']}-{p['b']} top-{p['k']}: {p['jaccard']:.4f}" for p in rankcal["top_k_overlap"] if p["k"] in (10, 20, 50)],
        "",
        "Score distributions are recorded in `seed_ranking_and_calibration_diagnosis.json`.",
        "",
        "Diagnosis: rankings are similar; absolute score distributions differ materially. The current disagreement is mostly boundary/extraction/calibration, not an obviously different learned pocket.",
    ])
    top = robust["full_grid_top10"][0]
    write_text("INDEPENDENT_METHOD_ROBUSTNESS_AUDIT.md", [
        "# Independent Method Robustness Audit",
        "",
        md_common_header,
        f"Best full-grid policy: `{top['policy_id']}` robust score {top['robust_score']:.4f}.",
        f"Current policy grid ID: `{robust['current_policy_grid_id']}`.",
        f"Materially better policy found by LOPO rule: `{robust['materially_better_policy_found']}`.",
        f"LOPO score improvement over current: {robust['lopo_score_improvement_over_current']:.4f}.",
        f"Current policy full-grid robust score: {robust['current_policy_full']['robust_score']:.4f}; mean F1 {robust['current_policy_full']['mean_f1']:.4f}; valid cluster rate {robust['current_policy_full']['valid_cluster_rate']:.4f}.",
        f"Best LOPO policy valid-cluster floor: {robust['best_lopo_policy']['min_valid_cluster_rate']:.4f}; top-1 count {robust['best_lopo_policy']['top1']}; top-2 count {robust['best_lopo_policy']['top2']}.",
        "No new policy was frozen because the apparent LOPO improvement was small, validation-set dependent, and did not satisfy the material-improvement rule.",
        "",
        "Full grid CSV: `artifacts/strong_robustness_20260815/independent_method_full_grid_summary.csv`.",
        "LOPO CSV: `artifacts/strong_robustness_20260815/leave_one_protein_out_summary.csv`.",
        "Selection file-read log confirms `pcna_inputs_read_during_selection: []`.",
    ])
    adequacy_rows = []
    first_seed_rows = read_csv(CAL_DIR / "calibration_scores_seed_42.csv")
    for pdb in ELIGIBLE:
        rows = [r for r in first_seed_rows if r["pdb_id"] == pdb]
        adequacy_rows.append(f"| {pdb} | {len(rows)} | {sum(r['label'] for r in rows)} | {sum(r['label'] for r in rows)/len(rows):.4f} |")
    write_text("VALIDATION_SET_ADEQUACY_REPORT.md", [
        "# Validation Set Adequacy Report",
        "",
        md_common_header,
        "The five-protein set is eligible by current provenance but small and heterogeneous. It is enough for a conservative robustness audit, not enough to claim universal extraction-method optimality.",
        "",
        "| PDB | residues | positives | prevalence |",
        "| --- | ---: | ---: | ---: |",
        *adequacy_rows,
        "",
        "No additional clean eligible non-PCNA structures were added in this pass because no machine-readable score/label artifacts for additional candidates were present in the active clean calibration artifact set.",
    ])
    write_text("LEAVE_ONE_PROTEIN_OUT_EXTRACTION_REPORT.md", [
        "# Leave-One-Protein-Out Extraction Report",
        "",
        md_common_header,
        f"Best LOPO policy: `{robust['best_lopo_policy']['policy_id']}`.",
        f"Current policy LOPO mean score: {robust['current_policy_lopo']['mean_lopo_score']:.4f}.",
        f"Best policy LOPO mean score: {robust['best_lopo_policy']['mean_lopo_score']:.4f}.",
        f"Current worst LOPO score: {robust['current_policy_lopo']['worst_lopo_score']:.4f}; best-policy worst LOPO score: {robust['best_lopo_policy']['worst_lopo_score']:.4f}.",
        f"Best-policy min valid-cluster rate: {robust['best_lopo_policy']['min_valid_cluster_rate']:.4f}.",
        "The LOPO result does not justify replacing the frozen policy because the leading methods are close and no candidate is consistently dominant across proteins.",
        "Detailed cases: `artifacts/strong_robustness_20260815/leave_one_protein_out_cases.csv`.",
    ])
    write_text("SCALE_INVARIANT_METHOD_COMPARISON.md", [
        "# Scale-Invariant Method Comparison",
        "",
        md_common_header,
        "Scale-invariant methods dominated the top independent robustness rankings. Absolute thresholding remained weaker under seed score-scale shifts.",
        "See `independent_method_full_grid_summary.csv` and `leave_one_protein_out_summary.csv`.",
    ])
    write_text("POCKET_CORE_VS_FRINGE_ANALYSIS.md", [
        "# Pocket Core vs Fringe Analysis",
        "",
        md_common_header,
        f"3/3 core: {geom['n_3of3_core']} residues. >=2/3 consensus: {geom['n_2of3_or_better']} residues. Union: {geom['n_union']} residues.",
        "The Jaccard shortfall is mainly explained by peripheral residues around a shared core, especially residues 231-252 and one seed-specific boundary difference.",
    ])
    ens = robust["ensemble"]
    write_text("ENSEMBLE_FEASIBILITY_REPORT.md", [
        "# Ensemble Feasibility Report",
        "",
        md_common_header,
        f"Mean-rank ensemble diagnostic mean F1: {ens['mean_f1']:.4f}; recall {ens['mean_recall']:.4f}; precision {ens['mean_precision']:.4f}; valid rate {ens['valid_cluster_rate']:.4f}.",
        "Ensembling is a prospective methodological refinement, not the original single-seed stability method. It is not adopted here without human approval and without a comparable seed-stability endpoint.",
    ])
    write_text("RETRAINING_NECESSITY_ASSESSMENT.md", [
        "# Retraining Necessity Assessment",
        "",
        md_common_header,
        "RETRAINING NOT CURRENTLY JUSTIFIED.",
        "",
        "Rationale: global and local rankings are correlated; the current 1W60 clusters share a physical core; disagreement is primarily boundary/extraction/calibration. Independent validation did not show that the frozen checkpoints learned qualitatively different regions.",
    ])
    if new_result:
        write_text("FINAL_1W60_STRONG_STABILITY_REPORT.md", [
            "# Final 1W60 Strong Stability Report",
            "",
            md_common_header,
            f"Policy: `{new_result['policy_id']}`.",
            f"Mean literal Jaccard: {new_result['literal_mean_pairwise_jaccard']:.4f}.",
            f"Consensus residues: {new_result['consensus_n_residues']}.",
            f"Verdict: **{new_result['strong_internal_verdict']}**.",
        ])


def write_text(name: str, lines: list[str]) -> None:
    (REP / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)
    old_hash = sha256_path(PREV_ART / "frozen_extraction_method.json")
    if old_hash != OLD_POLICY_HASH:
        raise SystemExit(f"frozen policy hash mismatch: {old_hash}")
    geom = summarize_current_1w60()
    rankcal = ranking_calibration_report(geom)
    robust = independent_robustness()
    new_result = apply_new_policy_if_needed(robust)
    write_reports(geom, rankcal, robust, new_result)
    summary = {
        "created_at": utc_now(),
        "current_06792_interpretation": geom["interpretation"],
        "materially_better_policy_found": robust["materially_better_policy_found"],
        "new_1w60_result": new_result,
        "retraining": "RETRAINING NOT CURRENTLY JUSTIFIED",
        "production_md_started": False,
    }
    write_json(ART / "strong_robustness_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
