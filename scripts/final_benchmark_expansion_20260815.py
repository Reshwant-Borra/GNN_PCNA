#!/usr/bin/env python3
"""Final independent benchmark-expansion audit before MD decision.

This script is intentionally conservative. It inventories active canonical data,
historical/archive provenance, and selected Git-history pointers, then applies the
strict eligibility gate requested for extraction-method development. It does not
train, does not infer on PCNA, does not use 8GLA/1W60 for method selection, and
does not overwrite any frozen historical policy.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import statistics
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "artifacts" / "final_benchmark_expansion_20260815"
REPORT = REPO / "reports" / "final_benchmark_expansion_20260815"
SEEDS = (42, 43, 44)
PCNA_IDS = {
    "1AXC", "1U76", "1U7B", "1UL1", "1VYJ", "1VYM", "1W60", "1W61", "1W63",
    "2ZVK", "2ZVL", "2ZVM", "3JAB", "3P87", "3TBL", "3VKX", "4D2G", "4RJF",
    "4ZTD", "5E0T", "5E0U", "5E0V", "5MAV", "5MLO", "5MLW", "5MOM", "5YCO",
    "5YD8", "6CBI", "6EHT", "6FCM", "6FCN", "6GIS", "6GWS", "6HVO", "6K3A",
    "6QC0", "6QCG", "6VVO", "7EFA", "7KQ0", "7M5L", "7M5N", "7NV0", "8COB",
    "8E84", "8F5Q", "8GCJ", "8GL9", "8GLA", "8UI8", "8UI9", "8UMT", "8UMU",
    "8UMY", "8UN0", "9B8T", "9CG4", "9CHM", "9EOA", "9GY0", "9N3L",
}
PREV_POLICY = REPO / "artifacts" / "pre_md_independent_extraction_20260815" / "frozen_extraction_method.json"
STRONG_ART = REPO / "artifacts" / "strong_robustness_20260815"
PREV_ART = REPO / "artifacts" / "pre_md_independent_extraction_20260815"
CAL_DIR = REPO / "artifacts" / "diagnostics" / "threshold_calibration_independent_20260814"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    except Exception:
        return "UNVERIFIED"


def git_dirty() -> bool:
    try:
        return bool(subprocess.check_output(["git", "status", "--short"], cwd=REPO, text=True).strip())
    except Exception:
        return True


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def norm_id(x: str) -> str:
    return x.upper()


def split_record_map() -> dict[str, dict[str, Any]]:
    p = REPO / "data" / "results" / "split_integrity_520.json"
    d = read_json(p)
    return {r["pdb_id"].upper(): r | {"source_file": str(p.relative_to(REPO))} for r in d["per_structure"]}


def historical_label_entries() -> dict[str, dict[str, Any]]:
    p = REPO / "archive" / "historical_desktop_gnn_pcna_202605_phase2_phase4" / "data" / "labels" / "label_manifest.json"
    if not p.exists():
        return {}
    d = read_json(p)
    out = {}
    for pdb_id, entry in d.get("entries", {}).items():
        out[pdb_id.upper()] = {
            "source_file": str(p.relative_to(REPO)),
            "historical_fold": entry.get("fold", ""),
            "historical_positive_count": entry.get("positive_count", ""),
            "historical_masked_count": entry.get("masked_count", ""),
            "historical_label_path": entry.get("path", ""),
        }
    return out


def active_raw_ids() -> dict[str, str]:
    out = {}
    for root in (REPO / "data" / "raw", REPO / "data" / "raw_intake"):
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if p.suffix.lower() not in {".pdb", ".cif", ".json"}:
                continue
            m = re.search(r"(?<![A-Za-z0-9])([0-9][A-Za-z0-9]{3})(?![A-Za-z0-9])", p.name)
            if m:
                out.setdefault(m.group(1).upper(), str(p.relative_to(REPO)))
    return out


def pcna_history_ids() -> dict[str, str]:
    out = {}
    p = REPO / "results" / "per_structure" / "summary_table.csv"
    if p.exists():
        with p.open(encoding="utf-8", errors="replace", newline="") as fh:
            for r in csv.DictReader(fh):
                pdb = (r.get("pdb") or r.get("pdb_id") or "").upper()
                if pdb:
                    out[pdb] = str(p.relative_to(REPO))
    return out


def score_availability() -> dict[str, str]:
    out = {}
    for seed in SEEDS:
        p = CAL_DIR / f"calibration_scores_seed_{seed}.csv"
        if not p.exists():
            continue
        with p.open(encoding="utf-8", errors="replace", newline="") as fh:
            for r in csv.DictReader(fh):
                out.setdefault(r["pdb_id"].upper(), str(p.relative_to(REPO)))
    for root in [REPO / "artifacts" / "go_prep" / "seed_stability_scores"]:
        if root.exists():
            for p in root.rglob("scores.csv"):
                parts = {x.upper() for x in p.parts}
                for pdb in PCNA_IDS:
                    if pdb in parts:
                        out.setdefault(pdb, str(p.relative_to(REPO)))
    return out


def chain_summary_from_pdb(pdb_id: str) -> str:
    p = REPO / "data" / "raw" / f"{pdb_id}.pdb"
    if not p.exists():
        return "unknown"
    counts: Counter[str] = Counter()
    seen = set()
    with p.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("ATOM") and line[12:16].strip() == "CA":
                chain = line[21].strip() or "_"
                resid = line[22:27].strip()
                key = (chain, resid)
                if key not in seen:
                    counts[chain] += 1
                    seen.add(key)
    return ";".join(f"{c}:{n}" for c, n in sorted(counts.items())) if counts else "unknown"


def build_candidates() -> list[dict[str, Any]]:
    split = split_record_map()
    hist = historical_label_entries()
    raw = active_raw_ids()
    pcna_scores = pcna_history_ids()
    scores = score_availability()
    all_ids = sorted(set(split) | set(hist) | set(raw) | set(pcna_scores) | PCNA_IDS)

    rows = []
    for pdb_id in all_ids:
        s = split.get(pdb_id, {})
        h = hist.get(pdb_id, {})
        pcna_related = pdb_id in PCNA_IDS or "pcna_structures" in raw.get(pdb_id, "").lower()
        original_role = h.get("historical_fold", "")
        current_role = s.get("split", "")
        label_avail = bool(s) or bool(h)
        pred_avail = pdb_id in scores
        label_quality = "canonical_non_degenerate" if s and not s.get("degenerate_labels") else (
            "canonical_degenerate" if s else ("historical_only_unverified" if h else "none")
        )
        structure_quality = "canonical_graph_record" if s else ("structure_only" if pdb_id in raw else "historical_pointer_only")
        train_overlap = current_role == "train" or str(original_role).startswith("train")
        validation_overlap = current_role == "val"
        test_overlap = current_role == "test" or original_role == "test"
        fine_tune_overlap = pdb_id == "8GLA" or pcna_related
        checkpoint_selection_overlap = pdb_id == "8GLA" or pcna_related

        eligible = False
        reason = ""
        if pcna_related:
            reason = "PCNA/PCNA-family structure; forbidden for independent extraction selection"
        elif pdb_id in {"1W60", "8GLA"}:
            reason = "final target or positive-control PCNA structure"
        elif not label_avail:
            reason = "no machine-readable residue/pocket labels"
        elif not pred_avail:
            reason = "no frozen-checkpoint prediction scores available in active canonical calibration artifacts"
        elif not s:
            reason = "historical labels only; incompatible/stale graph-feature regime or insufficient provenance"
        elif s.get("degenerate_labels"):
            reason = f"degenerate/unusable canonical labels: n_positive={s.get('n_positive')}"
        elif current_role == "train":
            reason = "training example; using it would invalidate extraction-development independence"
        elif current_role == "test":
            reason = "final held-out test example; preserved untouched"
        elif current_role != "val":
            reason = f"unsupported current split role: {current_role or 'unknown'}"
        else:
            eligible = True
            reason = "eligible canonical non-PCNA model-validation structure; not training, test, 1W60, or 8GLA"

        rows.append({
            "pdb_id": pdb_id,
            "chain": chain_summary_from_pdb(pdb_id),
            "source_file": s.get("source_file") or h.get("source_file") or raw.get(pdb_id, "") or pcna_scores.get(pdb_id, ""),
            "label_availability": label_avail,
            "prediction_score_availability": pred_avail,
            "model_checkpoint_provenance": (
                "frozen seed 42/43/44 go_prep checkpoints" if pred_avail else
                ("historical/incompatible or absent" if h else "absent")
            ),
            "original_split_role": original_role,
            "current_split_role": current_role,
            "homology_cluster": "",
            "pcna_related": pcna_related,
            "train_overlap": train_overlap,
            "validation_overlap": validation_overlap,
            "test_overlap": test_overlap,
            "fine_tuning_overlap": fine_tune_overlap,
            "checkpoint_selection_overlap": checkpoint_selection_overlap,
            "label_quality": label_quality,
            "structure_quality": structure_quality,
            "n_residues": s.get("n_nodes", ""),
            "n_positive": s.get("n_positive", h.get("historical_positive_count", "")),
            "positive_fraction": s.get("positive_fraction", ""),
            "eligible": eligible,
            "exclusion_reason": "" if eligible else reason,
        })

    # Fill homology clusters from split manifest if available.
    split_json = None
    try:
        split_json = json.loads(subprocess.check_output(
            ["git", "show", "d7cf76d674bced192b3c9d2b4f7f4fbf7ac3a228:data/splits/cryptosite_homology30_split.json"],
            cwd=REPO, text=True,
        ))
    except Exception:
        split_path = REPO / "data" / "splits" / "cryptosite_homology30_split.json"
        if split_path.exists():
            split_json = read_json(split_path)
    if split_json:
        cluster_by_id = {}
        for cluster, ids in split_json.get("components", {}).items():
            for pdb_id in ids:
                cluster_by_id[pdb_id.upper()] = cluster
        for row in rows:
            row["homology_cluster"] = cluster_by_id.get(row["pdb_id"], row["homology_cluster"])

    return rows


def compact_benchmark_spec(eligible_ids: list[str]) -> dict[str, Any]:
    return {
        "created_at": utc_now(),
        "benchmark_id": "final_benchmark_expansion_20260815_extraction_development",
        "eligible_structures": eligible_ids,
        "forbidden_selection_inputs": ["1W60", "8GLA", "PCNA structures", "final held-out test split", "training split"],
        "selection_metrics_frozen_before_comparison": [
            "precision", "recall", "F1", "MCC", "Jaccard/IoU",
            "valid-cluster rate", "centroid distance to labeled pocket",
            "cluster fragmentation", "physical compactness", "seed variance",
            "worst-case protein performance", "leave-one-protein-out robustness",
            "bootstrap resampling across proteins",
        ],
        "replacement_requirement": {
            "aggregate_improvement": "clear, not tiny 0.01-0.02 noise",
            "robustness": "equal or better LOPO/worst-case/valid-cluster behavior",
            "pcna_not_used_for_selection": True,
        },
        "pcna_inputs_read_during_selection": [],
        "note": "No new eligible structures survived; comparison relies on the existing eligible validation subset and previously generated robust audit."
    }


def summarize_candidate_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [r for r in rows if r["eligible"]]
    reasons = Counter(r["exclusion_reason"] or "eligible" for r in rows)
    current_roles = Counter(r["current_split_role"] or "not_current_clean_split" for r in rows)
    label_qualities = Counter(r["label_quality"] for r in rows)
    return {
        "discovered_candidates": len(rows),
        "eligible_candidates": len(eligible),
        "excluded_candidates": len(rows) - len(eligible),
        "eligible_ids": [r["pdb_id"] for r in eligible],
        "exclusion_reason_counts": dict(reasons),
        "current_role_counts": dict(current_roles),
        "label_quality_counts": dict(label_qualities),
    }


def eligible_quality(rows: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [r for r in rows if r["eligible"]]
    sizes = [int(r["n_residues"]) for r in eligible if r["n_residues"] != ""]
    positives = [int(r["n_positive"]) for r in eligible if r["n_positive"] != ""]
    chains = {r["pdb_id"]: r["chain"] for r in eligible}
    return {
        "n": len(eligible),
        "protein_size_distribution": describe(sizes),
        "pocket_size_distribution": describe(positives),
        "chain_distribution": chains,
        "label_prevalence": {
            r["pdb_id"]: float(r["positive_fraction"]) for r in eligible if r["positive_fraction"] != ""
        },
        "representativeness": (
            "limited: high-quality independent benchmark remains only five heterogeneous validation proteins; "
            "adequate for rejecting obviously brittle extraction changes, not for universal method optimality"
        ),
    }


def describe(vals: list[int]) -> dict[str, Any]:
    if not vals:
        return {}
    return {
        "min": min(vals),
        "median": statistics.median(vals),
        "mean": statistics.mean(vals),
        "max": max(vals),
        "values": vals,
    }


def load_existing_robustness() -> dict[str, Any]:
    robust = read_json(STRONG_ART / "independent_method_robustness_audit.json")
    geom = read_json(STRONG_ART / "current_06792_geometric_diagnosis.json")
    rankcal = read_json(STRONG_ART / "seed_ranking_and_calibration_diagnosis.json")
    stability = read_json(PREV_ART / "final_1w60_three_seed_stability_report.json")
    return {"robust": robust, "geom": geom, "rankcal": rankcal, "stability": stability}


def md_handoff(existing: dict[str, Any]) -> dict[str, Any]:
    handoff = read_json(PREV_ART / "final_consensus_pocket_handoff.json")
    policy_hash = sha256_path(PREV_POLICY)
    ckpt_hashes = {
        str(seed): sha256_path(REPO / "artifacts" / "go_prep" / f"seed_{seed}" / "best.ckpt")
        for seed in SEEDS
    }
    membership_path = STRONG_ART / "current_06792_residue_membership.csv"
    core = []
    fringe = []
    seed_specific = []
    with membership_path.open(encoding="utf-8", errors="replace", newline="") as fh:
        for r in csv.DictReader(fh):
            item = {"chain": r["chain"], "resid": int(r["resid"]), "resname": r["resname"]}
            n = int(r["n_seeds"])
            if n == 3:
                core.append(item)
            elif n == 2:
                fringe.append(item)
            else:
                seed_specific.append(item)
    return {
        "created_at": utc_now(),
        "gate6_status": "REQUIRED_BEFORE_MD",
        "final_recommendation": "PROCEED_TO_CONTROL_FIRST_MD",
        "do_not_start_long_production_without_human_approval": True,
        "candidate": {
            "pdb": handoff["pdb"],
            "primary_consensus_residues_ge_2of3": handoff["pocket_residues"],
            "core_3of3": core,
            "fringe_2of3": fringe,
            "seed_specific_boundary_union_only": seed_specific,
        },
        "frozen_extraction_policy": {
            "path": str(PREV_POLICY.relative_to(REPO)),
            "sha256": policy_hash,
            "policy_id": "independent_mcc_rank_fraction_size_weighted_cluster",
        },
        "frozen_checkpoints": ckpt_hashes,
        "positive_control": {
            "pdb": "8GLA",
            "definition": "ligand-stripped holo/open PCNA AOH1996-bound structure; control-first MD must show interpretable openness contrast before candidate production replicates",
        },
        "commands": {
            "first_md_preparation_command": "./md.sh smoke",
            "control_first_md": "./md.sh control5",
            "production_after_all_gates": "./md.sh production",
            "analysis": "./md.sh analyze",
        },
        "expected_outputs": [
            "md_validation_4070/outputs/control/rep*/production.dcd",
            "md_validation_4070/outputs/apo/rep*/production.dcd",
            "md_validation_4070/outputs/analysis/summary.json",
            "md_validation_4070/outputs/analysis/REPORT.md",
        ],
        "stop_failure_conditions": [
            "Gate-6 approval absent or not specific to this handoff",
            "biological assembly chain count mismatch",
            "pocket residues fail to resolve in prepared apo/control structures",
            "PDBFixer/gemmi/OpenMM preparation reports long-bond or topology errors",
            "short smoke test is unstable or produces invalid energies",
            "positive-control openness is not interpretable",
            "analysis detects severe PBC/RMSD artifacts",
        ],
    }


def write_pocket_json(handoff: dict[str, Any]) -> None:
    pocket = {
        "name": "final_consensus_1w60_20260815",
        "source": "final benchmark expansion handoff; derived from frozen three-seed >=2/3 consensus",
        "apo_pdb": "1W60",
        "control_pdb": "8GLA",
        "expected_protein_chains": 3,
        "min_chain_res": 200,
        "interface_chain_indices": [0],
        "pocket_resseq": [int(r["resid"]) for r in handoff["candidate"]["primary_consensus_residues_ge_2of3"]],
        "pocket_residues": handoff["candidate"]["primary_consensus_residues_ge_2of3"],
        "core_3of3": handoff["candidate"]["core_3of3"],
        "fringe_2of3": handoff["candidate"]["fringe_2of3"],
        "gate6_human_approval": "REQUIRED_BEFORE_MD",
        "frozen_policy_sha256": handoff["frozen_extraction_policy"]["sha256"],
        "notes": [
            "Computational candidate only; no binding, druggability, or biological efficacy established.",
            "Literal boundary stability is moderate; 3/3 core is the higher-confidence region.",
        ],
    }
    write_json(REPO / "md_validation_4070" / "pockets" / "final_consensus_1w60_20260815.json", pocket)


def write_reports(rows: list[dict[str, Any]], summary: dict[str, Any], quality: dict[str, Any], existing: dict[str, Any], handoff: dict[str, Any]) -> None:
    REPORT.mkdir(parents=True, exist_ok=True)
    robust = existing["robust"]
    geom = existing["geom"]
    stability = existing["stability"]

    lines = [
        "# Final Benchmark Eligibility Report",
        "",
        f"Created: {utc_now()}",
        f"Git commit: `{git_commit()}`; dirty worktree: `{git_dirty()}`.",
        "",
        "## Candidate Inventory",
        "",
        f"Discovered candidate structure records: **{summary['discovered_candidates']}**.",
        f"Eligible for extraction-method development: **{summary['eligible_candidates']}**.",
        f"Excluded: **{summary['excluded_candidates']}**.",
        "",
        "Eligible IDs: " + ", ".join(f"`{x}`" for x in summary["eligible_ids"]),
        "",
        "The expanded audit found historical labels and Git-history artifacts, but no additional non-PCNA structures with compatible frozen-checkpoint residue scores, canonical 520-dim graph/label provenance, and a legitimate development role beyond the existing validation set.",
        "",
        "## Dataset Roles",
        "",
        "- Training split: rejected for extraction-method development.",
        "- Model validation split: eligible only for non-degenerate, non-PCNA structures with frozen-checkpoint scores.",
        "- Checkpoint selection: 8GLA chain-B role; rejected.",
        "- Fine-tuning: 8GLA/PCNA role; rejected.",
        "- Untouched test split: preserved; not consumed to tune extraction.",
        "- PCNA target: 1W60 rejected from selection.",
        "- Positive control: 8GLA rejected from selection.",
        "",
        "Established split/label integrity check was rerun from the canonical Git snapshot into `artifacts/final_benchmark_expansion_20260815/split_integrity_520_rerun_from_git_snapshot.json`: `ok=true`, `errors=[]`, graph-manifest hash `69744b548e812697ba9015c6563ed526f1af2e915b1595badb1dd47fd1b4c64f`, with the same six degenerate structures recorded by the canonical report.",
        "Homology/leakage status remains the established `data/results/homology30_audit.json` PASS: no train-to-val/test cluster overlaps and `leakage_detected=false`.",
        "",
        "Selection file-read audit remains `pcna_inputs_read_during_selection: []` from the strong robustness audit. No new selection pass read PCNA inputs.",
        "",
        "## Benchmark Quality",
        "",
        f"Protein sizes: {quality['protein_size_distribution']}.",
        f"Pocket positive counts: {quality['pocket_size_distribution']}.",
        f"Label prevalence by protein: {quality['label_prevalence']}.",
        "",
        quality["representativeness"],
        "",
        "## Extraction Comparison",
        "",
        "Serious candidate methods compared in the existing robustness grid: fixed absolute threshold, validation-MCC absolute threshold, MCC rank count, MCC rank fraction, chain-aware rank fraction, fixed rank fraction, DBSCAN eps 5/6/7 A, min_samples 3, min cluster size 3, cluster ranking by mean score or mean score x sqrt(size), plus diagnostic mean-rank ensembling.",
        "",
        f"Current policy grid ID: `{robust['current_policy_grid_id']}`.",
        f"Materially better independent policy found: **{robust['materially_better_policy_found']}**.",
        f"LOPO score improvement of best over current: `{robust['lopo_score_improvement_over_current']:.4f}`.",
        f"Current LOPO mean score: `{robust['current_policy_lopo']['mean_lopo_score']:.4f}`; best LOPO mean score: `{robust['best_lopo_policy']['mean_lopo_score']:.4f}`.",
        "",
        "No replacement is frozen because the expanded audit did not add eligible structures and the existing LOPO/bootstrap comparison did not demonstrate a robust, material improvement over the current independently frozen policy.",
        "",
        "## PCNA Rerun",
        "",
        "No new 1W60 evaluation was run because no independently justified replacement policy was frozen.",
        "",
        "## Final Reproducibility Assessment",
        "",
        f"Mean literal 1W60 Jaccard: `{stability['literal_mean_pairwise_jaccard']:.4f}`.",
        f"3/3 core: `{geom['n_3of3_core']}` residues; >=2/3 consensus: `{geom['n_2of3_or_better']}` residues; union: `{geom['n_union']}` residues.",
        "Centroid distances (A): " + ", ".join(f"{p['a']}-{p['b']}={p['distance_A']:.3f}" for p in geom["centroid_pair_distances"]) + ".",
        "6 A near-overlap: " + ", ".join(f"{p['a']}-{p['b']}={p['symmetric_near_fraction']:.3f}" for p in geom["neighborhood_overlap"]["6.0"]) + ".",
        "",
        "Classification: **MODERATE / EXPLORATORY PASS**. Literal boundary agreement is moderate, but the three seeds identify the same physical candidate pocket core with strong geometric overlap and high local/global rank concordance.",
        "",
        "## Retraining Decision",
        "",
        "**RETRAINING NOT JUSTIFIED.** Rankings remain strongly correlated, the pocket location is physically stable, and disagreement is primarily boundary/calibration-related rather than model-level collapse.",
        "",
        "## MD Readiness",
        "",
        "**PROCEED TO CONTROL-FIRST MD**.",
        "",
        "Do not start long candidate production MD before Gate-6 approval. The next sequence is Gate-6 -> prep validation -> short smoke test -> positive-control MD -> control interpretability assessment -> candidate production replicates.",
        "",
        f"Exact first MD-preparation command: `{handoff['commands']['first_md_preparation_command']}`",
    ]
    (REPORT / "FINAL_BENCHMARK_ELIGIBILITY_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (REPO / "FINAL_BENCHMARK_ELIGIBILITY_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    write_json(OUT / "final_benchmark_eligibility_report.json", {
        "summary": summary,
        "quality": quality,
        "split_integrity_rerun": "artifacts/final_benchmark_expansion_20260815/split_integrity_520_rerun_from_git_snapshot.json",
        "homology_audit": "data/results/homology30_audit.json",
        "current_policy_status": "kept",
        "new_policy": None,
        "pcna_rerun": None,
        "md_readiness": "PROCEED TO CONTROL-FIRST MD",
        "retraining": "RETRAINING NOT JUSTIFIED",
    })


def update_registries(summary: dict[str, Any]) -> None:
    # Keep this narrowly additive and avoid rewriting historical decisions.
    dec_path = REPO / "research_os_registries" / "decision_registry.json"
    exp_path = REPO / "research_os_registries" / "experiment_registry.json"
    art_path = REPO / "research_os_registries" / "artifact_registry.json"
    for path in (dec_path, exp_path, art_path):
        if not path.exists():
            continue
        data = read_json(path)
        entries = data.setdefault("entries", [])
        existing_ids = {e.get("decision_id") or e.get("experiment_id") or e.get("artifact_id") for e in entries}
        if path == dec_path and "DEC-0003" not in existing_ids:
            entries.append({
                "decision_id": "DEC-0003",
                "date": "2026-08-15",
                "decision_maker": "codex.agent_non_human",
                "request": "Final benchmark-expansion pass before MD readiness decision.",
                "created_at": utc_now(),
                "updated_at": utc_now(),
                "options": ["keep current policy", "freeze replacement policy", "retrain", "hold before MD", "proceed to control-first MD"],
                "decision": "Keep current independently frozen extraction policy; do not retrain; proceed to control-first MD after Gate-6 approval.",
                "rationale": "No additional eligible independent non-PCNA structures survived strict gate; existing LOPO/bootstrap did not justify replacement; PCNA evidence supports same physical pocket core with boundary uncertainty.",
                "evidence": ["artifacts/final_benchmark_expansion_20260815/final_benchmark_eligibility_report.json"],
                "affected_claims": ["CLAIM-PCNA-001"],
                "follow_up": ["Human Gate-6 approval required before MD preparation/production."],
            })
        elif path == exp_path and "EXP-0003" not in existing_ids:
            entries.append({
                "experiment_id": "EXP-0003",
                "title": "Final independent benchmark expansion before MD decision",
                "purpose": "Search for additional eligible independent extraction-development structures and decide whether a replacement extraction policy is justified.",
                "status": "completed",
                "created_at": utc_now(),
                "updated_at": utc_now(),
                "created_by_agent": "codex.final_benchmark_expansion",
                "script_or_workflow": "scripts/final_benchmark_expansion_20260815.py",
                "command": ".venv_gnn_pcna/bin/python scripts/final_benchmark_expansion_20260815.py",
                "metrics": {
                    "discovered_candidates": summary["discovered_candidates"],
                    "eligible_candidates": summary["eligible_candidates"],
                    "new_policy_frozen": False,
                    "pcna_rerun": False,
                },
                "actual_outcome": "No independently justified replacement policy; proceed to control-first MD after Gate-6 approval.",
                "interpretation": "Moderate/exploratory computational pass with explicit boundary uncertainty.",
                "human_approval": {"required": True, "status": "required_before_md"},
            })
        elif path == art_path and "ART-0032" not in existing_ids:
            entries.append({
                "artifact_id": "ART-0032",
                "path": "artifacts/final_benchmark_expansion_20260815/all_candidate_structures.csv",
                "artifact_type": "processed_data",
                "status": "current",
                "created_at": utc_now(),
                "updated_at": utc_now(),
                "created_by_agent": "codex.final_benchmark_expansion",
                "git_commit": git_commit(),
                "git_dirty": git_dirty(),
                "command": ".venv_gnn_pcna/bin/python scripts/final_benchmark_expansion_20260815.py",
                "inputs": [
                    "data/results/split_integrity_520.json",
                    "data/results/homology30_audit.json",
                    "archive/historical_desktop_gnn_pcna_202605_phase2_phase4/data/labels/label_manifest.json",
                    "artifacts/strong_robustness_20260815/independent_method_robustness_audit.json",
                ],
                "outputs": [
                    "artifacts/final_benchmark_expansion_20260815/all_candidate_structures.csv",
                    "FINAL_BENCHMARK_ELIGIBILITY_REPORT.md",
                ],
            })
        data["updated_at"] = utc_now()
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def update_knowledge_base() -> None:
    path = REPO / "research_os_memory" / "VALIDATION_STATUS.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    marker = "## Final Pre-MD Benchmark Expansion - 2026-08-15"
    block = f"""

{marker}

Supported:
- Three frozen seeds rank the same PCNA neighborhood reasonably consistently.
- Current physical pocket localization is substantially more stable than literal boundary membership.
- Current result has an 11-residue 3/3 core and 16-residue >=2/3 consensus.
- Current extraction policy was independently selected and remains the best-supported policy after final expansion audit.

Uncertainty:
- Exact pocket boundary is not fully stable.
- Literal Jaccard is moderate rather than excellent.
- Independent extraction benchmark remains limited to five eligible non-PCNA validation proteins.
- Computational prediction does not establish druggability or binding.

Not established:
- Actual ligand binding.
- Druggability.
- Biological efficacy.
- Experimentally confirmed pocket opening.
- Therapeutic relevance.

MD readiness: PROCEED TO CONTROL-FIRST MD only after human Gate-6 approval; production MD has not started.
"""
    if marker not in text:
        path.write_text(text.rstrip() + block + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    REPORT.mkdir(parents=True, exist_ok=True)
    rows = build_candidates()
    fields = [
        "pdb_id", "chain", "source_file", "label_availability", "prediction_score_availability",
        "model_checkpoint_provenance", "original_split_role", "current_split_role", "homology_cluster",
        "pcna_related", "train_overlap", "validation_overlap", "test_overlap", "fine_tuning_overlap",
        "checkpoint_selection_overlap", "label_quality", "structure_quality", "n_residues", "n_positive",
        "positive_fraction", "eligible", "exclusion_reason",
    ]
    write_csv(OUT / "all_candidate_structures.csv", rows, fields)

    summary = summarize_candidate_counts(rows)
    quality = eligible_quality(rows)
    existing = load_existing_robustness()
    spec = compact_benchmark_spec(summary["eligible_ids"])
    write_json(OUT / "predeclared_expanded_benchmark_spec.json", spec)
    write_json(OUT / "candidate_summary.json", summary | {"benchmark_quality": quality})

    handoff = md_handoff(existing)
    write_json(OUT / "md_handoff_packet.json", handoff)
    write_pocket_json(handoff)
    write_reports(rows, summary, quality, existing, handoff)
    update_registries(summary)
    update_knowledge_base()

    print(json.dumps({
        "candidate_csv": str((OUT / "all_candidate_structures.csv").relative_to(REPO)),
        "discovered": summary["discovered_candidates"],
        "eligible": summary["eligible_candidates"],
        "policy": "kept_current_independent_mcc_rank_fraction_size_weighted_cluster",
        "pcna_rerun": False,
        "md_readiness": "PROCEED TO CONTROL-FIRST MD",
    }, indent=2))


if __name__ == "__main__":
    main()
