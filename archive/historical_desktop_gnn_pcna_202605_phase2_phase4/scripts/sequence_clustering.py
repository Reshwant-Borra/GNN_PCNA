"""
Sequence clustering for CryptoBench cryptic-only candidate set + friend's crawl structures.

Approach: RCSB PDB pre-computed sequence clusters at 30% identity.
- Queries RCSB polymer_entity_instance to resolve chain -> entity, then fetches
  rcsb_cluster_membership at identity=30.
- Fallbacks: if specified chain 404s or yields DNA/RNA, tries chain A then entity 1 directly.
- PCNA cluster anchor: 5e0v chain A → cluster_id_30 = 1168.
- Flags 2xur/3bep: PCNA homologs only if in cluster 1168.
- Resolves 6 repeated-holo cross-fold pairs.
- Clusters friend's 72 PCNA-related structures.

Outputs:
  data/registries/sequence_cluster_assignments.json
  data/registries/cross_fold_cluster_risks.json
  reports/phase2/sequence_clustering_report.md

Governance: docs/scientific_governance/05_SPLIT_PROTOCOL.md
"""

import json
import time
import requests
from pathlib import Path
from collections import defaultdict
from datetime import datetime

ROOT = Path(__file__).parent.parent

DATASET_PATH = ROOT / "data/raw_intake/cryptobench/metadata_files/66c328c87352852f68dbeac4_dataset.json"
FOLDS_PATH   = ROOT / "data/raw_intake/cryptobench/metadata_files/66c328d97352852f68dbead5_folds.json"
FRIEND_REG   = ROOT / "data/registries/friend_crawl_registry.json"
OUT_CLUSTERS = ROOT / "data/registries/sequence_cluster_assignments.json"
OUT_RISKS    = ROOT / "data/registries/cross_fold_cluster_risks.json"
OUT_REPORT   = ROOT / "reports/phase2/sequence_clustering_report.md"
CACHE_PATH   = ROOT / "data/registries/.cluster_api_cache.json"

RCSB_INSTANCE = "https://data.rcsb.org/rest/v1/core/polymer_entity_instance/{pdb}/{chain}"
RCSB_ENTITY   = "https://data.rcsb.org/rest/v1/core/polymer_entity/{pdb}/{entity}"
RCSB_ENTRY    = "https://data.rcsb.org/rest/v1/core/entry/{pdb}"

IDENTITY_TARGET = 30
PCNA_UNIPROT    = "P12004"
PCNA_EXACT      = {"5e0v", "3vkx"}
SLIDING_CLAMP   = {"2xur", "3bep"}

REPEATED_HOLO_GROUPS = {
    "holo_2fzc_2fzg_4f04": {"apos": ["2air", "9atc"], "shared_holos": ["2fzc", "2fzg", "4f04"]},
    "holo_5qya_7fo6":       {"apos": ["3e9p", "4ilg"], "shared_holos": ["5qya", "7fo6"]},
    "holo_6a5y":            {"apos": ["4n5g", "6hl0"], "shared_holos": ["6a5y"]},
}

RATE_SLEEP  = 0.08
MAX_RETRIES = 3


# ── Cache ─────────────────────────────────────────────────────────────────────

def load_cache() -> dict:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict) -> None:
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f)


def rcsb_get(url: str, cache: dict) -> dict | None:
    if url in cache:
        return cache[url]
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 404:
                cache[url] = None
                return None
            if r.status_code == 200:
                data = r.json()
                cache[url] = data
                return data
            time.sleep(1.0 * (attempt + 1))
        except Exception:
            time.sleep(1.0 * (attempt + 1))
    cache[url] = None
    return None


# ── Cluster lookup ────────────────────────────────────────────────────────────

def get_cluster_30(pdb_id: str, chain_hint: str, cache: dict) -> dict:
    """
    Returns dict with entity_id, cluster_id_30, description, method.
    Tries chain_hint first; falls back to chain A, then entity '1' directly.
    """
    pdb = pdb_id.lower()

    def _from_entity(eid: str) -> dict | None:
        url = RCSB_ENTITY.format(pdb=pdb, entity=eid)
        d = rcsb_get(url, cache)
        time.sleep(RATE_SLEEP)
        if not d:
            return None
        memberships = d.get("rcsb_cluster_membership", [])
        if not memberships:
            return None
        c30 = next((m["cluster_id"] for m in memberships if m["identity"] == IDENTITY_TARGET), None)
        desc = d.get("rcsb_polymer_entity", {}).get("pdbx_description", "")
        return {"entity_id": eid, "cluster_id_30": c30, "description": desc}

    def _entity_from_chain(ch: str) -> str | None:
        url = RCSB_INSTANCE.format(pdb=pdb, chain=ch)
        d = rcsb_get(url, cache)
        time.sleep(RATE_SLEEP)
        if not d:
            return None
        return d.get("rcsb_polymer_entity_instance_container_identifiers", {}).get("entity_id")

    # Try specified chain
    for chain in [chain_hint, "A"]:
        if not chain:
            continue
        eid = _entity_from_chain(chain)
        if eid:
            result = _from_entity(eid)
            if result and result.get("cluster_id_30") is not None:
                result["method"] = f"chain_{chain}"
                return result
            if result:
                result["method"] = f"chain_{chain}_no_cluster"
                return result

    # Fallback: try entity 1 directly (most PDB entries have protein as entity 1)
    result = _from_entity("1")
    if result:
        result["method"] = "entity_1_direct"
        return result

    # Fallback: try entity 2
    result = _from_entity("2")
    if result:
        result["method"] = "entity_2_direct"
        return result

    return {"entity_id": None, "cluster_id_30": None, "description": "", "method": "all_failed"}


# ── Data loaders ──────────────────────────────────────────────────────────────

def load_cryptobench():
    with open(FOLDS_PATH, encoding="utf-8") as f:
        folds = json.load(f)
    with open(DATASET_PATH, encoding="utf-8") as f:
        dataset = json.load(f)

    apo_to_fold    = {apo.lower(): fold for fold, apos in folds.items() for apo in apos}
    apo_to_chain   = {}
    apo_to_uniprot = {}
    for apo_key, records in dataset.items():
        apo = apo_key.lower()
        if not isinstance(records, list):
            records = [records]
        if apo not in apo_to_chain:
            apo_to_chain[apo]   = records[0].get("apo_chain", "A")
            apo_to_uniprot[apo] = records[0].get("uniprot_id", "")
    return apo_to_fold, apo_to_chain, apo_to_uniprot


def load_friend():
    ids = []
    with open(FRIEND_REG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                ids.append(json.loads(line).get("id", "").upper())
    return [x for x in ids if x]


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    ts = lambda: f"[{datetime.now():%H:%M:%S}]"
    print(f"{ts()} Loading registries...")
    apo_to_fold, apo_to_chain, apo_to_uniprot = load_cryptobench()
    friend_ids = load_friend()
    cache = load_cache()
    print(f"  CryptoBench apos: {len(apo_to_fold)}  |  Friend structures: {len(friend_ids)}")

    # ── PCNA anchor ──────────────────────────────────────────────────────────
    print(f"\n{ts()} Anchoring PCNA cluster via 5e0v chain A...")
    anchor = get_cluster_30("5e0v", "A", cache)
    PCNA_CLUSTER_ID = anchor.get("cluster_id_30")
    print(f"  PCNA cluster_id_30 = {PCNA_CLUSTER_ID}  ({anchor.get('description','')[:60]})")
    save_cache(cache)

    # ── Sliding clamp candidates ──────────────────────────────────────────────
    print(f"\n{ts()} Checking sliding clamp candidates: 2xur, 3bep ...")
    sc_results = {}
    for pdb in ["2xur", "3bep"]:
        r = get_cluster_30(pdb, "A", cache)
        is_pcna = PCNA_CLUSTER_ID is not None and r.get("cluster_id_30") == PCNA_CLUSTER_ID
        r["pcna_homolog"] = is_pcna
        r["policy"] = (
            "EXCLUDE — confirmed PCNA homolog at 30% identity"
            if is_pcna else
            "RETAIN — not in PCNA cluster at 30% identity; still a sliding clamp but evolutionarily distinct"
        )
        sc_results[pdb] = r
        print(f"  {pdb}: cluster30={r.get('cluster_id_30')}  pcna_homolog={is_pcna}  {r.get('description','')[:55]}")
    save_cache(cache)

    # ── CryptoBench apos ─────────────────────────────────────────────────────
    total = len(apo_to_fold)
    print(f"\n{ts()} Clustering {total} CryptoBench apo structures (RCSB API ~{total*0.18:.0f}s) ...")
    apo_results = {}
    failures = []
    for i, (apo, fold) in enumerate(apo_to_fold.items(), 1):
        chain = apo_to_chain.get(apo, "A")
        r = get_cluster_30(apo, chain, cache)
        apo_results[apo] = {
            "fold": fold,
            "chain": chain,
            "uniprot_id": apo_to_uniprot.get(apo, ""),
            "entity_id": r.get("entity_id"),
            "cluster_id_30": r.get("cluster_id_30"),
            "description": r.get("description", ""),
            "method": r.get("method"),
            "pcna_cluster": (PCNA_CLUSTER_ID is not None and
                             r.get("cluster_id_30") == PCNA_CLUSTER_ID),
        }
        if r.get("cluster_id_30") is None:
            failures.append(apo)
        if i % 100 == 0:
            print(f"  {ts()} {i}/{total} ({100*i//total}%) — null clusters: {len(failures)}")
            save_cache(cache)
    save_cache(cache)
    print(f"  Done. Null cluster lookups: {len(failures)}")

    # ── Friend structures ─────────────────────────────────────────────────────
    print(f"\n{ts()} Clustering {len(friend_ids)} friend structures ...")
    friend_results = {}
    for pdb in friend_ids:
        r = get_cluster_30(pdb, "A", cache)
        is_pcna = PCNA_CLUSTER_ID is not None and r.get("cluster_id_30") == PCNA_CLUSTER_ID
        friend_results[pdb] = {
            "entity_id": r.get("entity_id"),
            "cluster_id_30": r.get("cluster_id_30"),
            "description": r.get("description", ""),
            "method": r.get("method"),
            "pcna_cluster": is_pcna,
        }
    save_cache(cache)

    # ── Cross-fold cluster analysis ───────────────────────────────────────────
    print(f"\n{ts()} Analysing cross-fold cluster risks ...")
    cluster_to_folds = defaultdict(lambda: {"train": [], "test": []})
    for apo, info in apo_results.items():
        cid = info["cluster_id_30"]
        if cid is None:
            continue
        fold = info["fold"]
        key = "test" if fold == "test" else "train"
        cluster_to_folds[cid][key].append(apo)

    cross_fold = {
        cid: {
            "cluster_id_30": cid,
            "train_apos": sorted(data["train"]),
            "test_apos": sorted(data["test"]),
            "risk": "TRAIN_TEST_SEQUENCE_LEAKAGE",
            "action": "assign_all_apos_in_cluster_to_same_split_group",
        }
        for cid, data in cluster_to_folds.items()
        if data["train"] and data["test"]
    }
    print(f"  Cross-fold cluster risks: {len(cross_fold)}")

    # ── Repeated holo resolution ──────────────────────────────────────────────
    print(f"\n{ts()} Resolving repeated holo PDB pairs ...")
    holo_resolution = {}
    for group_key, group in REPEATED_HOLO_GROUPS.items():
        apo_clusters = [apo_results.get(apo, {}).get("cluster_id_30") for apo in group["apos"]]
        non_null = [c for c in apo_clusters if c is not None]
        same_cluster = len(non_null) == len(apo_clusters) and len(set(non_null)) == 1
        holo_resolution[group_key] = {
            "apos": group["apos"],
            "shared_holos": group["shared_holos"],
            "apo_cluster_ids_30": apo_clusters,
            "same_cluster": same_cluster,
            "action": (
                "GROUP_IN_SAME_SPLIT — apo proteins are sequence homologs; group together"
                if same_cluster else
                "KEEP_SHARED_HOLO_IN_ONE_SPLIT — apos are NOT sequence homologs, but the shared "
                "holo PDB structure must belong to only one split group to prevent structural leakage"
            ),
        }
        print(f"  {group_key}: same_cluster={same_cluster} apo_clusters={apo_clusters}")

    # ── PCNA cluster summary ──────────────────────────────────────────────────
    cb_pcna = sorted(a for a, info in apo_results.items() if info["pcna_cluster"])
    fr_pcna = sorted(p for p, info in friend_results.items() if info["pcna_cluster"])
    print(f"\n  PCNA cluster members — CryptoBench: {cb_pcna}")
    print(f"  PCNA cluster members — friend crawl: {fr_pcna}")

    # ── Write outputs ─────────────────────────────────────────────────────────
    print(f"\n{ts()} Writing output registries ...")

    cluster_doc = {
        "generated_at": datetime.now().isoformat(),
        "method": "RCSB_precomputed_sequence_clusters",
        "identity_threshold": IDENTITY_TARGET,
        "pcna_cluster_id_30": PCNA_CLUSTER_ID,
        "anchor": {"pdb": "5e0v", "chain": "A", "uniprot": PCNA_UNIPROT,
                   "description": anchor.get("description", "")},
        "sliding_clamp_candidates": sc_results,
        "repeated_holo_resolution": holo_resolution,
        "cryptobench_apo_clusters": apo_results,
        "friend_structure_clusters": friend_results,
        "pcna_cluster_members_cryptobench": cb_pcna,
        "pcna_cluster_members_friend_crawl": fr_pcna,
        "cross_fold_cluster_count": len(cross_fold),
        "null_cluster_lookups": failures,
        "governance": "docs/scientific_governance/05_SPLIT_PROTOCOL.md",
        "status": "CLUSTERING_COMPLETE" if not cross_fold else "CLUSTERING_COMPLETE_SPLIT_REDESIGN_NEEDED",
    }
    with open(OUT_CLUSTERS, "w", encoding="utf-8") as f:
        json.dump(cluster_doc, f, indent=2)

    risks_doc = {
        "generated_at": datetime.now().isoformat(),
        "identity_threshold": IDENTITY_TARGET,
        "cross_fold_cluster_risks": cross_fold,
        "cross_fold_cluster_count": len(cross_fold),
        "repeated_holo_resolution": holo_resolution,
        "sliding_clamp_pcna_status": {
            p: v["pcna_homolog"] for p, v in sc_results.items()
        },
        "status": "NO_RISKS" if not cross_fold else "SPLIT_REDESIGN_REQUIRED",
    }
    with open(OUT_RISKS, "w", encoding="utf-8") as f:
        json.dump(risks_doc, f, indent=2)

    _write_report(cluster_doc, cross_fold, holo_resolution, sc_results,
                  cb_pcna, fr_pcna, failures, PCNA_CLUSTER_ID)

    print(f"{ts()} DONE.")
    print(f"  {OUT_CLUSTERS}")
    print(f"  {OUT_RISKS}")
    print(f"  {OUT_REPORT}")
    return cluster_doc, risks_doc


def _write_report(ca, cross_fold, holo_res, sc_results, cb_pcna, fr_pcna, failures, pcna_cid):
    sc = ca["sliding_clamp_candidates"]
    lines = [
        "---",
        "type: analysis-report",
        f"status: {'complete' if not failures else 'complete_with_lookup_gaps'}",
        f"created: {datetime.now().strftime('%Y-%m-%d')}",
        "blocker_addressed: 3",
        "method: RCSB_precomputed_sequence_clusters_30pct_identity",
        "---",
        "",
        "# Sequence Clustering Report — Phase 2",
        "",
        f"**Method:** RCSB pre-computed sequence clusters at {IDENTITY_TARGET}% identity  ",
        f"**PCNA anchor:** 5e0v/chain A → cluster_id_30 = **{pcna_cid}**  ",
        "**Governance:** `docs/scientific_governance/05_SPLIT_PROTOCOL.md`",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| CryptoBench apo structures clustered | {len(ca['cryptobench_apo_clusters'])} |",
        f"| Friend crawl structures clustered | {len(ca['friend_structure_clusters'])} |",
        f"| Null cluster lookups (API or no entity) | {len(failures)} |",
        f"| Cross-fold cluster risks (sequence leakage) | {len(cross_fold)} |",
        f"| PCNA cluster members in CryptoBench | {len(cb_pcna)} |",
        f"| PCNA cluster members in friend crawl | {len(fr_pcna)} |",
        "",
        "---",
        "",
        "## Sliding Clamp Candidates",
        "",
        f"PCNA (5e0v) cluster ID at 30%: **{pcna_cid}**",
        "",
        "| PDB | cluster_id_30 | PCNA Homolog? | Description | Policy |",
        "|---|---|---|---|---|",
    ]
    for pdb, info in sc.items():
        flag = "**YES → EXCLUDE**" if info["pcna_homolog"] else "No → Retain"
        lines.append(
            f"| {pdb} | {info.get('cluster_id_30','N/A')} | {flag} | {info.get('description','')[:45]} | {info['policy'].split(' — ')[0]} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Repeated Holo PDB Pair Resolution",
        "",
        "6 holo PDB IDs appear in multiple official folds. The apo structures they connect",
        "must be in the same split group — either because they are sequence homologs OR",
        "because splitting them would let the test set see the same holo structure twice.",
        "",
        "| Group | Apos | Shared Holos | Same Cluster? | Action |",
        "|---|---|---|---|---|",
    ]
    for gk, gr in holo_res.items():
        same = gr["same_cluster"]
        apos = " ".join(gr["apos"])
        holos = " ".join(gr["shared_holos"])
        cids = str(gr["apo_cluster_ids_30"])
        action = gr["action"].split(" — ")[0]
        lines.append(f"| {gk} | {apos} | {holos} | {'YES' if same else 'NO'} ({cids}) | {action} |")

    lines += [
        "",
        "---",
        "",
        "## Cross-Fold Sequence Leakage Risks",
        "",
    ]
    if cross_fold:
        lines += [
            f"**{len(cross_fold)} clusters** span both train and test folds at >={IDENTITY_TARGET}% identity.",
            "All apo structures within each cluster must be assigned to the same fold.",
            "",
            "| Cluster ID | Train apos (sample) | Test apos (sample) |",
            "|---|---|---|",
        ]
        for cid, data in sorted(cross_fold.items()):
            tr = ", ".join(data["train_apos"][:4]) + ("…" if len(data["train_apos"]) > 4 else "")
            te = ", ".join(data["test_apos"][:4]) + ("…" if len(data["test_apos"]) > 4 else "")
            lines.append(f"| {cid} | {tr} | {te} |")
    else:
        lines.append("**No cross-fold sequence leakage risks detected** at 30% identity threshold.")

    lines += [
        "",
        "---",
        "",
        "## PCNA Cluster Members",
        "",
        f"**Cluster ID:** {pcna_cid}",
        "",
        f"CryptoBench ({len(cb_pcna)}): " + (", ".join(sorted(cb_pcna)) if cb_pcna else "None beyond 5e0v (already excluded)"),
        f"Friend crawl ({len(fr_pcna)}): " + (", ".join(sorted(fr_pcna)) if fr_pcna else "None"),
        "",
        "All PCNA cluster members excluded from training/validation per decision 2 (2026-05-27).",
        "",
        "---",
        "",
        "## Provenance",
        "",
        "- RCSB REST API: `polymer_entity_instance` → entity_id; `polymer_entity` → `rcsb_cluster_membership`",
        "- Cluster IDs are RCSB's sequence-identity-based groupings recomputed each UniProt release",
        "- identity=30 corresponds to SCOP superfamily / conservative homolog level",
        "- Governance: `docs/scientific_governance/05_SPLIT_PROTOCOL.md`",
        "- Evidence status: verified (RCSB pre-computed, not ad-hoc)",
        f"- Generated: {datetime.now().isoformat()}",
    ]
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    run()
