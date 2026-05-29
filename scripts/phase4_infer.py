"""Phase 4 PCNA inference — GATE 6 authorized.

Runs per-residue scoring on all 103 mmCIF structures in
C:\\Users\\reshw\\phase4_pcna_crawl using the frozen
spatial_only_fold1_seed1_best.pt checkpoint on CUDA (RTX 4070).

Produces the 5 required governance artifacts in reports/phase4/.

Authorization: reports/phase4/gate6_authorization_20260529.md
Governance:   docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md
"""

from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CRAWL_DIR = Path(r"C:\Users\reshw\phase4_pcna_crawl")
MMCIF_DIR = CRAWL_DIR / "mmcif"
MANIFEST_PATH = CRAWL_DIR / "phase4_crawl_manifest.json"
CHECKPOINT_PATH = ROOT / "checkpoints/phase3/spatial_only_fold1_seed1_best.pt"
INTERFACE_MAP_PATH = ROOT / "data/registries/pcna_interface_map.json"
GATE6_PATH = ROOT / "reports/phase4/gate6_authorization_20260529.md"
OUTPUT_DIR = ROOT / "reports/phase4"

HUMAN_PARTS = {"1", "2A"}
TOP_K_INTERFACE = 20
DATE_STAMP = "20260529"


# ---------------------------------------------------------------------------
# Gate check
# ---------------------------------------------------------------------------

def _check_gate6() -> None:
    if not GATE6_PATH.exists():
        raise RuntimeError(
            f"GATE 6 authorization record not found: {GATE6_PATH}\n"
            "Phase 4 inference requires human authorization."
        )


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------

def _load_model(device: torch.device):
    from phase3_model.gnn import GraphSAGE3L
    ckpt = torch.load(str(CHECKPOINT_PATH), map_location=device, weights_only=False)
    config = ckpt["config"]
    model = GraphSAGE3L(
        hidden_dim=config["hidden_dim"],
        dropout=config.get("dropout", 0.1),
    )
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device)
    model.eval()
    return model, ckpt


# ---------------------------------------------------------------------------
# Per-structure inference
# ---------------------------------------------------------------------------

def _run_structure(
    entry: dict[str, Any],
    model: torch.nn.Module,
    device: torch.device,
) -> dict[str, Any]:
    from phase4_inference.chain_selector import select_inference_chains
    from phase4_inference.cif_utils import read_cif_text
    from phase4_inference.graph_builder import build_inference_graph

    pdb_id: str = entry["pdb_id"]
    part: str = entry["part"]
    flag: str = entry.get("flag", "")
    cif_path = MMCIF_DIR / f"{pdb_id}.cif.gz"

    if not cif_path.exists():
        return {
            "pdb_id": pdb_id,
            "part": part,
            "flag": flag,
            "status": "ERROR_FILE_NOT_FOUND",
            "error": str(cif_path),
            "per_residue_scores": [],
            "chain_audit": {},
        }

    try:
        cif_text = read_cif_text(cif_path)
        selected_chains, chain_method, chain_audit, residues = select_inference_chains(
            cif_path, part, cif_text
        )

        data, node_metadata = build_inference_graph(cif_path, selected_chains, residues)

        if data.x.shape[0] == 0:
            return {
                "pdb_id": pdb_id,
                "part": part,
                "flag": flag,
                "status": "SKIP_NO_NODES",
                "chain_method": chain_method,
                "chain_audit": chain_audit,
                "per_residue_scores": [],
            }

        data = data.to(device)
        with torch.no_grad():
            logits = model(data)
        scores = torch.sigmoid(logits).cpu().numpy()

        per_residue = []
        for i, meta in enumerate(node_metadata):
            per_residue.append({
                "chain_id": meta["chain_id"],
                "residue_number": meta["residue_number"],
                "insertion_code": meta.get("insertion_code"),
                "residue_name": meta["residue_name"],
                "score": float(scores[i]),
                "node_index": i,
            })

        return {
            "pdb_id": pdb_id,
            "part": part,
            "flag": flag,
            "rank_in_candidate_manifest": entry.get("rank_in_candidate_manifest"),
            "resolution_angstrom": entry.get("resolution_angstrom"),
            "has_ligand": entry.get("has_ligand_per_manifest"),
            "notes": entry.get("notes", ""),
            "status": "OK",
            "n_nodes": int(data.x.shape[0]),
            "n_edges": int(data.edge_index.shape[1]),
            "selected_chains": sorted(selected_chains),
            "chain_method": chain_method,
            "chain_audit": chain_audit,
            "per_residue_scores": per_residue,
        }

    except Exception as exc:
        return {
            "pdb_id": pdb_id,
            "part": part,
            "flag": flag,
            "status": "ERROR",
            "error": str(exc),
            "per_residue_scores": [],
            "chain_audit": {},
        }


# ---------------------------------------------------------------------------
# Canonical aggregation (human PCNA only)
# ---------------------------------------------------------------------------

def _aggregate_canonical_scores(
    all_results: list[dict[str, Any]],
) -> dict[int, dict[str, Any]]:
    """Aggregate per-residue scores across all human PCNA structures by max.

    Returns: canonical_resnum -> {max_score, mean_score, n_structures, per_structure}
    """
    human_results = [
        r for r in all_results
        if r["part"] in HUMAN_PARTS and r["status"] == "OK"
        and r.get("flag") != "VARIANT_NOT_APO"
    ]

    # resnum -> list of (pdb_id, score)
    score_lists: dict[int, list[tuple[str, float]]] = defaultdict(list)

    for result in human_results:
        for rec in result["per_residue_scores"]:
            try:
                rn = int(rec["residue_number"])
                score_lists[rn].append((result["pdb_id"], rec["score"]))
            except (ValueError, TypeError):
                pass

    aggregated: dict[int, dict[str, Any]] = {}
    for rn, entries in score_lists.items():
        scores_only = [s for _, s in entries]
        aggregated[rn] = {
            "canonical_residue": rn,
            "max_score": max(scores_only),
            "mean_score": float(np.mean(scores_only)),
            "n_structures": len(scores_only),
            "per_structure": {pdb: s for pdb, s in entries},
        }

    return aggregated


# ---------------------------------------------------------------------------
# Candidate region identification
# ---------------------------------------------------------------------------

def _find_candidate_regions(
    canonical_scores: dict[int, dict[str, Any]],
    window_size: int = 5,
    top_n: int = 30,
) -> list[dict[str, Any]]:
    """Identify candidate regions: contiguous stretches of high-scoring residues."""
    if not canonical_scores:
        return []

    rns = sorted(canonical_scores)
    rn_to_score = {rn: canonical_scores[rn]["max_score"] for rn in rns}

    # Sliding window — score by max in window
    windows: list[dict[str, Any]] = []
    for i, start_rn in enumerate(rns):
        window_rns = [rn for rn in rns if start_rn <= rn < start_rn + window_size]
        if len(window_rns) < max(1, window_size // 2):
            continue
        max_s = max(rn_to_score[rn] for rn in window_rns)
        mean_s = float(np.mean([rn_to_score[rn] for rn in window_rns]))
        windows.append({
            "start_residue": start_rn,
            "end_residue": window_rns[-1],
            "window_residues": window_rns,
            "max_score": max_s,
            "mean_score": mean_s,
            "n_residues": len(window_rns),
        })

    # Select non-overlapping top windows
    windows.sort(key=lambda w: -w["max_score"])
    covered: set[int] = set()
    selected: list[dict[str, Any]] = []
    for w in windows:
        w_set = set(w["window_residues"])
        if not w_set & covered:
            selected.append(w)
            covered.update(w_set)
        if len(selected) >= top_n:
            break

    return selected


# ---------------------------------------------------------------------------
# Interface overlap
# ---------------------------------------------------------------------------

def _compute_per_structure_overlaps(
    all_results: list[dict[str, Any]],
    interface_map: dict[str, set[int]],
) -> list[dict[str, Any]]:
    from phase4_inference.interface_audit import compute_interface_overlaps

    overlap_records = []
    for result in all_results:
        if result["part"] not in HUMAN_PARTS or result["status"] != "OK":
            continue
        overlap = compute_interface_overlaps(
            result["per_residue_scores"],
            interface_map,
            top_k=TOP_K_INTERFACE,
        )
        overlap_records.append({
            "pdb_id": result["pdb_id"],
            "part": result["part"],
            "flag": result.get("flag", ""),
            "rank": result.get("rank_in_candidate_manifest"),
            **overlap,
        })
    return overlap_records


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------

def _write_json_results(all_results: list[dict[str, Any]], path: Path) -> None:
    payload = {
        "schema": "phase4_inference_results_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "gate6_authorization": str(GATE6_PATH),
        "checkpoint": str(CHECKPOINT_PATH),
        "n_structures": len(all_results),
        "structures": all_results,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"  Written: {path}")


def _write_candidate_report(
    candidate_regions: list[dict[str, Any]],
    canonical_scores: dict[int, dict[str, Any]],
    interface_map: dict[str, set[int]],
    all_results: list[dict[str, Any]],
    path: Path,
) -> None:
    n_human = sum(
        1 for r in all_results
        if r["part"] in HUMAN_PARTS and r["status"] == "OK"
        and r.get("flag") != "VARIANT_NOT_APO"
    )
    lines = [
        "# Phase 4 Candidate Report — PCNA Cryptic Pocket Regions",
        "",
        f"**Date:** {DATE_STAMP}",
        f"**Checkpoint:** `spatial_only_fold1_seed1_best.pt`",
        f"**Structures scored (human PCNA, excluding VARIANT_NOT_APO):** {n_human}",
        "",
        "> **Claim language (governance doc 14):** All regions below are",
        "> 'computationally predicted PCNA surface regions' and 'hypothesis-generating",
        "> sites for follow-up.' No therapeutic, druggability, or novel-site claims.",
        "> Recovery of known interfaces (PIP-box, IDCL, AOH1996 region) is expected",
        "> and does NOT constitute a novel prediction.",
        "",
        "## Top Candidate Regions (aggregated across human PCNA structures)",
        "",
        "| Rank | Residues | Max Score | Mean Score | N Structs | Interface Overlap |",
        "|------|----------|-----------|------------|-----------|-------------------|",
    ]

    for rank, region in enumerate(candidate_regions, 1):
        w_rns = set(region["window_residues"])
        iface_hits = []
        for iface_name, iface_residues in interface_map.items():
            if iface_name == "aoh1996_contact_region":
                iface_hits_here = w_rns & iface_residues
                if iface_hits_here:
                    iface_hits.append(f"{iface_name}(POSITIVE_CONTROL)")
            elif w_rns & iface_residues:
                iface_hits.append(iface_name)

        iface_str = ", ".join(iface_hits) if iface_hits else "none"
        res_range = f"{region['start_residue']}-{region['end_residue']}"
        lines.append(
            f"| {rank} | {res_range} | {region['max_score']:.4f} | "
            f"{region['mean_score']:.4f} | "
            f"{canonical_scores.get(region['start_residue'], {}).get('n_structures', '?')} | "
            f"{iface_str} |"
        )

    lines += [
        "",
        "## Per-Residue Canonical Score Table (top 50 by max score)",
        "",
        "| Canonical Residue | Max Score | Mean Score | N Structs |",
        "|-------------------|-----------|------------|-----------|",
    ]

    top_residues = sorted(
        canonical_scores.values(),
        key=lambda r: -r["max_score"]
    )[:50]
    for rec in top_residues:
        lines.append(
            f"| {rec['canonical_residue']} | {rec['max_score']:.4f} | "
            f"{rec['mean_score']:.4f} | {rec['n_structures']} |"
        )

    lines += [
        "",
        "---",
        f"*Generated: {datetime.now(timezone.utc).isoformat()}*",
        f"*Authorization: `{GATE6_PATH}`*",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Written: {path}")


def _write_pcna_audit(all_results: list[dict[str, Any]], path: Path) -> None:
    ok = [r for r in all_results if r["status"] == "OK"]
    errors = [r for r in all_results if r["status"] not in {"OK", "SKIP_NO_NODES"}]
    skipped = [r for r in all_results if r["status"] == "SKIP_NO_NODES"]

    part_counts: dict[str, int] = defaultdict(int)
    method_counts: dict[str, int] = defaultdict(int)
    for r in ok:
        part_counts[r["part"]] += 1
        method_counts[r.get("chain_method", "unknown").split(":")[0]] += 1

    lines = [
        "# Phase 4 PCNA Audit — GATE 6",
        "",
        f"**Date:** {DATE_STAMP}",
        f"**Authorization:** `gate6_authorization_20260529.md`",
        f"**Total structures attempted:** {len(all_results)}",
        f"**OK:** {len(ok)}",
        f"**Skipped (no nodes):** {len(skipped)}",
        f"**Errors:** {len(errors)}",
        "",
        "## Part breakdown",
        "",
        "| Part | Count |",
        "|------|-------|",
    ]
    for p, c in sorted(part_counts.items()):
        lines.append(f"| {p} | {c} |")

    lines += [
        "",
        "## Chain selection method breakdown",
        "",
        "| Method | Count |",
        "|--------|-------|",
    ]
    for m, c in sorted(method_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {m} | {c} |")

    lines += [
        "",
        "## Governance flags",
        "",
        "- **8GLA**: Positive-control sanity check. Recovery of AOH1996/ZQZ contact region",
        "  expected. Does NOT validate novel-site predictions (governance doc 12).",
        "- **5E0V**: VARIANT_NOT_APO (S228I mutation + FEN1 peptide).",
        "  Results excluded from aggregated canonical scores.",
        "- **Part 2C**: Sliding clamp homologs. Secondary comparative analysis only.",
        "  Not part of primary claim path.",
        "",
        "## Per-structure summary",
        "",
        "| PDB | Part | Flag | Status | N Nodes | N Edges | Chain Method |",
        "|-----|------|------|--------|---------|---------|--------------|",
    ]
    for r in sorted(all_results, key=lambda x: (x["part"], x["pdb_id"])):
        method_short = r.get("chain_method", "").split(":")[0] if r.get("chain_method") else r.get("status", "")
        lines.append(
            f"| {r['pdb_id']} | {r['part']} | {r.get('flag', '')} | {r['status']} | "
            f"{r.get('n_nodes', 0)} | {r.get('n_edges', 0)} | {method_short} |"
        )

    if errors:
        lines += ["", "## Errors", ""]
        for r in errors:
            lines.append(f"- **{r['pdb_id']}**: {r.get('error', r['status'])}")

    lines += [
        "",
        "---",
        f"*Generated: {datetime.now(timezone.utc).isoformat()}*",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Written: {path}")


def _write_interface_overlap(
    overlap_records: list[dict[str, Any]],
    interface_map: dict[str, set[int]],
    path: Path,
) -> None:
    lines = [
        "# Phase 4 Interface Overlap Analysis",
        "",
        f"**Date:** {DATE_STAMP}",
        "> Overlapping predictions with known PCNA interfaces does NOT constitute",
        "> novel-site prediction. AOH1996 region recovery is a positive control.",
        "",
        f"**Top-K for overlap:** {TOP_K_INTERFACE} residues per structure",
        "",
    ]

    # Per-interface summary across all human structures
    lines += ["## Summary: overlap fraction per interface (human PCNA)", ""]
    iface_names = list(interface_map)
    for iface in iface_names:
        fractions = []
        for rec in overlap_records:
            iface_data = rec.get("interface_overlaps", {}).get(iface, {})
            f = iface_data.get("top_k_overlap_fraction", 0.0)
            fractions.append(f)
        if fractions:
            control_note = " **(POSITIVE CONTROL)**" if iface == "aoh1996_contact_region" else ""
            lines.append(
                f"- **{iface}**{control_note}: "
                f"mean={np.mean(fractions):.3f}, "
                f"max={max(fractions):.3f}, "
                f"n={len(fractions)}"
            )

    lines += [
        "",
        "## Per-structure interface overlap",
        "",
        "| PDB | Part | Rank | " + " | ".join(iface_names) + " |",
        "|-----|------|------|" + "|".join(["---"] * len(iface_names)) + "|",
    ]
    for rec in sorted(overlap_records, key=lambda r: (r["part"], r.get("rank") or 999)):
        fracs = []
        for iface in iface_names:
            idata = rec.get("interface_overlaps", {}).get(iface, {})
            fracs.append(f"{idata.get('top_k_overlap_fraction', 0.0):.2f}")
        rank_str = str(rec.get("rank", "")) if rec.get("rank") else ""
        flag_note = f" [{rec['flag']}]" if rec.get("flag") else ""
        lines.append(
            f"| {rec['pdb_id']}{flag_note} | {rec['part']} | {rank_str} | "
            + " | ".join(fracs) + " |"
        )

    lines += [
        "",
        "---",
        f"*Generated: {datetime.now(timezone.utc).isoformat()}*",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Written: {path}")


def _write_candidate_prioritization(
    candidate_regions: list[dict[str, Any]],
    canonical_scores: dict[int, dict[str, Any]],
    interface_map: dict[str, set[int]],
    path: Path,
) -> None:
    lines = [
        "# Phase 4 Candidate Prioritization — Phase 5 MD Candidates",
        "",
        f"**Date:** {DATE_STAMP}",
        "",
        "> **Scope:** These are hypothesis-generating candidate regions for Phase 5",
        "> molecular dynamics validation. They are NOT validated sites.",
        "> MD validation is required before any scientific claim (governance doc 13).",
        "",
        "## Priority tiers",
        "",
        "**Tier 1 (Primary MD targets):** High max-score regions that do NOT overlap",
        "known PIP-box / IDCL / AOH1996 contact region — potential novel surface regions.",
        "",
        "**Tier 2 (Interface-adjacent):** High max-score regions overlapping known",
        "interfaces — useful for positive-control MD validation.",
        "",
        "**Tier 3 (Positive control):** 8GLA-region recovery for model sanity check.",
        "",
    ]

    known_ifaces = {"pip_box_binding_site", "apim_site", "idcl", "aoh1996_contact_region"}
    positive_control_iface = "aoh1996_contact_region"

    tier1, tier2, tier3 = [], [], []

    for region in candidate_regions:
        w_rns = set(region["window_residues"])
        overlapped_ifaces = {
            name for name, res in interface_map.items()
            if w_rns & res
        }
        is_positive_ctrl = positive_control_iface in overlapped_ifaces
        is_known_iface = bool(overlapped_ifaces & known_ifaces)

        region_entry = {**region, "overlapped_interfaces": sorted(overlapped_ifaces)}
        if is_positive_ctrl:
            tier3.append(region_entry)
        elif is_known_iface:
            tier2.append(region_entry)
        else:
            tier1.append(region_entry)

    def _write_tier(tier_name: str, tier: list[dict[str, Any]]) -> None:
        lines.append(f"## {tier_name} ({len(tier)} regions)")
        lines.append("")
        if not tier:
            lines.append("*None.*")
            lines.append("")
            return
        lines.append("| Rank | Residues | Max Score | Mean Score | Interface Overlap |")
        lines.append("|------|----------|-----------|------------|-------------------|")
        for i, r in enumerate(tier, 1):
            res_range = f"{r['start_residue']}-{r['end_residue']}"
            ifaces = ", ".join(r.get("overlapped_interfaces", [])) or "none"
            lines.append(
                f"| {i} | {res_range} | {r['max_score']:.4f} | {r['mean_score']:.4f} | {ifaces} |"
            )
        lines.append("")

    _write_tier("Tier 1 — Potential novel surface regions", tier1)
    _write_tier("Tier 2 — Interface-adjacent regions", tier2)
    _write_tier("Tier 3 — Positive control", tier3)

    lines += [
        "## Next steps",
        "",
        "1. Select Tier 1 + Tier 2 regions for Phase 5 MD sampling.",
        "2. MD sampling must follow governance doc 13 (MD_VALIDATION_RULES).",
        "3. No structural or mechanistic claims until MD + human review.",
        "",
        "---",
        f"*Generated: {datetime.now(timezone.utc).isoformat()}*",
        f"*Authorization: `{GATE6_PATH}`*",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Written: {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    t0 = time.time()
    print("=" * 70)
    print("Phase 4 PCNA Inference — GATE 6")
    print("=" * 70)

    _check_gate6()
    print(f"  GATE 6: authorized ({GATE6_PATH.name})")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  Device: {device}")
    if device.type == "cuda":
        print(f"  GPU: {torch.cuda.get_device_name(0)}")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    structures = manifest["structures"]
    print(f"  Structures: {len(structures)}")

    from phase4_inference.interface_audit import load_interface_map_from_file
    interface_map = load_interface_map_from_file(INTERFACE_MAP_PATH)
    print(f"  Interface map loaded: {len(interface_map)} regions")

    model, ckpt = _load_model(device)
    print(f"  Model loaded: hidden_dim={ckpt['config']['hidden_dim']}, "
          f"fold={ckpt.get('val_fold')}, seed={ckpt.get('seed')}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Inference loop ---
    all_results: list[dict[str, Any]] = []
    n = len(structures)
    for idx, entry in enumerate(structures):
        pdb_id = entry["pdb_id"]
        t_struct = time.time()
        result = _run_structure(entry, model, device)
        elapsed = time.time() - t_struct
        status = result["status"]
        n_nodes = result.get("n_nodes", 0)
        flag = f" [{result.get('flag', '')}]" if result.get("flag") else ""
        print(f"  [{idx+1:>3}/{n}] {pdb_id} part={entry['part']}{flag} "
              f"status={status} nodes={n_nodes} ({elapsed:.1f}s)")
        all_results.append(result)

    # --- Report 1: JSON results ---
    json_path = OUTPUT_DIR / f"phase4_inference_results_{DATE_STAMP}.json"
    _write_json_results(all_results, json_path)

    # --- Canonical aggregation (human PCNA, excluding VARIANT_NOT_APO) ---
    canonical_scores = _aggregate_canonical_scores(all_results)
    print(f"\n  Canonical residues scored: {len(canonical_scores)}")

    # --- Candidate regions ---
    candidate_regions = _find_candidate_regions(canonical_scores, window_size=5, top_n=30)
    print(f"  Candidate regions identified: {len(candidate_regions)}")

    # --- Report 2: Candidate report ---
    cand_path = OUTPUT_DIR / f"phase4_candidate_report_{DATE_STAMP}.md"
    _write_candidate_report(candidate_regions, canonical_scores, interface_map, all_results, cand_path)

    # --- Report 3: PCNA audit ---
    audit_path = OUTPUT_DIR / f"phase4_pcna_audit_{DATE_STAMP}.md"
    _write_pcna_audit(all_results, audit_path)

    # --- Interface overlaps ---
    overlap_records = _compute_per_structure_overlaps(all_results, interface_map)

    # --- Report 4: Interface overlap ---
    iface_path = OUTPUT_DIR / f"phase4_interface_overlap_{DATE_STAMP}.md"
    _write_interface_overlap(overlap_records, interface_map, iface_path)

    # --- Report 5: Candidate prioritization ---
    prio_path = OUTPUT_DIR / f"phase4_candidate_prioritization_{DATE_STAMP}.md"
    _write_candidate_prioritization(candidate_regions, canonical_scores, interface_map, prio_path)

    elapsed_total = time.time() - t0
    n_ok = sum(1 for r in all_results if r["status"] == "OK")
    n_err = sum(1 for r in all_results if r["status"] == "ERROR")
    print(f"\n{'=' * 70}")
    print(f"  Done in {elapsed_total:.1f}s — {n_ok}/{n} OK, {n_err} errors")
    print(f"  Reports written to: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
