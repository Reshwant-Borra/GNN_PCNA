"""
catalog_to_obsidian.py — Convert crawler catalog to linked Obsidian vault notes.

Reads data/catalog/raw_catalog.json (all records) and creates:
  docs/vault/structures/PDB_XXXX.md    — one note per PDB structure
  docs/vault/papers/paper_XXXX.md      — one note per paper/preprint
  docs/vault/datasets/dataset_XXXX.md  — one note per dataset
  docs/vault/compounds/XXXX.md         — one note per compound/target
  docs/vault/_HUB_STRUCTURES.md        — hub linking all structure notes
  docs/vault/_HUB_PAPERS.md
  docs/vault/_HUB_DATASETS.md
  docs/vault/_HUB_COMPOUNDS.md
  docs/vault/KNOWLEDGE_GRAPH.md        — master hub (top-level node)

All notes use YAML frontmatter (Dataview-compatible) and wikilinks.

Usage:
    python agents/catalog_to_obsidian.py
    python agents/catalog_to_obsidian.py --catalog data/catalog/raw_catalog.json
    python agents/catalog_to_obsidian.py --min-relevance 0.0   # include everything
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT    = Path(__file__).parent.parent
CATALOG_DIR  = REPO_ROOT / "data" / "catalog"
VAULT_DIR    = REPO_ROOT / "docs" / "vault"

# Sub-directories
STRUCT_DIR   = VAULT_DIR / "structures"
PAPER_DIR    = VAULT_DIR / "papers"
DATA_DIR     = VAULT_DIR / "datasets"
CMPD_DIR     = VAULT_DIR / "compounds"

for d in (STRUCT_DIR, PAPER_DIR, DATA_DIR, CMPD_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ── Known PDB ground-truth structures ───────────────────────────────────────
KNOWN_PCNA_IDS = {"1W60", "8GLA", "1AXC"}  # 1W61 removed — proline racemase (T. cruzi), not PCNA

KNOWN_ANNOTATIONS = {
    "1W60": {"role": "apo-baseline", "note": "Apo PCNA — cryptic pocket absent. Primary negative training example."},
    "8GLA": {"role": "ground-truth-holo", "note": "PCNA + AOH1996 — cryptic pocket OPEN. Primary positive training example. Ground truth for pocket labeling."},
    "1AXC": {"role": "pip-box-complex", "note": "PCNA + p21 PIP-box. Interface-bound; not the cryptic AOH1996 site."},
    # 1W61 REMOVED — it is proline racemase (Trypanosoma cruzi), NOT PCNA. See docs/vault/structures/1W61.md
    "4RJF": {"role": "high-res-apo", "note": "Highest-resolution apo structure (2.0 A). Better node features than 1W60."},
    "1U7B": {"role": "high-res-overall", "note": "1.88 A resolution overall — highest resolution in the PCNA set."},
    "9N3L": {"role": "novel-inhibitor", "note": "HSP90alpha inhibitor bound to PCNA — potential second cryptic pocket. Investigate."},
    "8F5Q": {"role": "pip-box-high-res", "note": "PCNA + PIP box at 1.9 A."},
}

# ── Helpers ──────────────────────────────────────────────────────────────────

def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^\w\s-]", "", s).strip()
    s = re.sub(r"[\s_]+", "_", s)
    return s[:80]


def safe_str(v: Any, default: str = "") -> str:
    if v is None:
        return default
    return str(v).strip()


def yaml_str(v: Any) -> str:
    s = safe_str(v)
    if any(c in s for c in ':#{}[]|>&*!,"'):
        s = s.replace('"', '\\"')
        return f'"{s}"'
    return s or '""'


def tags_for(record: dict) -> list[str]:
    tags = ["pcna", record.get("record_type", "unknown").replace("_", "-")]
    if record.get("passed"):
        tags.append("validated")
    src = record.get("source", "")
    if src:
        tags.append(f"source-{src.split(':')[0]}")
    meta = record.get("metadata", {})
    if meta.get("uniprot_confirmed"):
        tags.append("uniprot-confirmed")
    uid = record.get("uid", "").upper()
    if uid in KNOWN_PCNA_IDS:
        tags.append("ground-truth")
    return tags


def relevance_label(r: float) -> str:
    if r >= 0.8:  return "high"
    if r >= 0.5:  return "medium"
    if r >= 0.2:  return "low"
    return "minimal"


# ── Structure note ────────────────────────────────────────────────────────────

def write_structure_note(record: dict) -> Path:
    uid   = record["uid"].upper()
    meta  = record.get("metadata", {})
    val   = record.get("validation", {})
    l3    = val.get("l3", {})
    ann   = KNOWN_ANNOTATIONS.get(uid, {})
    res   = l3.get("resolution_angstrom") or meta.get("resolution")
    chains = l3.get("chains", [])
    org   = safe_str(meta.get("organism") or record.get("description"))
    title = safe_str(record.get("title")) or f"PCNA Structure {uid}"
    passed = record.get("passed", False)
    rel   = record.get("relevance", 0.0)

    # Infer category
    if uid in KNOWN_PCNA_IDS:
        category = "core"
    elif rel >= 0.5:
        category = "primary"
    elif rel >= 0.2:
        category = "secondary"
    else:
        category = "peripheral"

    lines = [
        "---",
        f"type: pdb_structure",
        f"pdb_id: {uid}",
        f"title: {yaml_str(title)}",
        f"resolution_angstrom: {res if res else 'null'}",
        f"chains: {json.dumps(chains)}",
        f"organism: {yaml_str(org)}",
        f"source: {yaml_str(record.get('source', ''))}",
        f"relevance: {round(rel, 3)}",
        f"relevance_label: {relevance_label(rel)}",
        f"validated: {str(passed).lower()}",
        f"category: {category}",
        f"ca_completeness: {l3.get('ca_completeness', 'null')}",
        f"residue_count: {l3.get('residue_count', 'null')}",
        f"mean_b_factor: {l3.get('mean_b_factor', 'null')}",
        f"tags: [{', '.join(tags_for(record))}]",
        f"rcsb_url: https://www.rcsb.org/structure/{uid}",
        f"download_url: {yaml_str(record.get('download_url', ''))}",
        "---",
        "",
        f"# {uid} — {title}",
        "",
    ]

    if ann:
        lines += [
            f"> **Role**: `{ann['role']}`",
            f">",
            f"> {ann['note']}",
            "",
        ]

    lines += [
        "## Summary",
        "",
        f"| Field | Value |",
        f"|---|---|",
        f"| PDB ID | `{uid}` |",
        f"| Resolution | {f'{res} Å' if res else 'N/A'} |",
        f"| Chains | {', '.join(chains) if chains else 'unknown'} |",
        f"| Organism | {org or 'unknown'} |",
        f"| Ca completeness | {'{:.1%}'.format(l3.get('ca_completeness', 0)) if l3.get('ca_completeness') else 'N/A'} |",
        f"| Residues | {l3.get('residue_count', 'N/A')} |",
        f"| Validation | {'PASSED' if passed else 'flagged'} |",
        f"| Relevance | {rel:.2f} ({relevance_label(rel)}) |",
        "",
    ]

    # Validation detail
    fail_reasons = [
        v.get("fail") for v in record.get("validation", {}).values()
        if isinstance(v, dict) and "fail" in v
    ]
    if not passed and fail_reasons:
        lines += [
            "## Validation Flags",
            "",
        ]
        for reason in fail_reasons:
            lines.append(f"- {reason}")
        lines.append("")

    # ML usage note
    lines += [
        "## ML Usage",
        "",
    ]
    if uid == "8GLA":
        lines += [
            "- **Positive training example** — AOH1996 cryptic pocket is open",
            "- Ground truth: residues within 6 Å of AOH1996 ligand labeled `1`",
            "- Required for: pocket labeling, validation gate",
        ]
    elif uid == "1W60":
        lines += [
            "- **Negative training example** — apo PCNA, no cryptic pocket",
            "- Cryptic pocket residues labeled `0` in this structure",
        ]
    elif category in ("core", "primary"):
        lines += [
            "- Candidate training structure — high confidence PCNA",
            "- Suitable for data augmentation (3 chains × structure)",
        ]
    else:
        lines += [
            "- Low-confidence structure — use with caution",
            "- May serve as augmentation data after manual review",
        ]
    lines.append("")

    # Wikilinks
    related = [pid for pid in KNOWN_PCNA_IDS if pid != uid]
    lines += [
        "## Connections",
        "",
        f"- **RCSB entry**: [PDB {uid}](https://www.rcsb.org/structure/{uid})",
        f"- **Download**: [{uid}.pdb]({record.get('download_url', '')})",
        "",
        "**Related structures**: " + " · ".join(f"[[{p}]]" for p in related),
        "",
        "**Pipeline**: [[PIPELINE]] · [[DATASETS]] · [[parse_pdb]] · [[graph_construction]]",
        "",
        "**Hub**: [[_HUB_STRUCTURES]] · [[KNOWLEDGE_GRAPH]]",
        "",
    ]

    dest = STRUCT_DIR / f"{uid}.md"
    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest


# ── Paper note ───────────────────────────────────────────────────────────────

def write_paper_note(record: dict, idx: int) -> Path:
    uid   = record.get("uid", f"paper_{idx}")
    title = safe_str(record.get("title")) or "Untitled paper"
    desc  = safe_str(record.get("description"))
    src   = record.get("source", "")
    url   = record.get("url", "")
    rel   = record.get("relevance", 0.0)
    meta  = record.get("metadata", {})
    slug  = slugify(uid)

    lines = [
        "---",
        f"type: paper",
        f"uid: {yaml_str(uid)}",
        f"title: {yaml_str(title)}",
        f"source: {yaml_str(src)}",
        f"url: {yaml_str(url)}",
        f"relevance: {round(rel, 3)}",
        f"relevance_label: {relevance_label(rel)}",
        f"validated: {str(record.get('passed', False)).lower()}",
        f"tags: [{', '.join(tags_for(record))}]",
        "---",
        "",
        f"# {title}",
        "",
        "## Abstract / Description",
        "",
        desc if desc else "_No description crawled — fetch manually from URL below._",
        "",
        "## Source",
        "",
        f"- **Source database**: {src}",
        f"- **URL**: {url}",
        f"- **Relevance score**: {rel:.2f} ({relevance_label(rel)})",
        "",
        "## Relevance to GNN-PCNA",
        "",
        "_Review and annotate: does this paper contain methods, datasets, or findings relevant to cryptic pocket prediction on PCNA?_",
        "",
        "- [ ] Relevant methods",
        "- [ ] Contains dataset",
        "- [ ] Contains PCNA-specific findings",
        "- [ ] Contains CryptoSite benchmark results",
        "",
        "## Key Findings",
        "",
        "_Extract from paper:_",
        "",
        "## Connections",
        "",
        "**Hub**: [[_HUB_PAPERS]] · [[KNOWLEDGE_GRAPH]]",
        "",
        "**Related**: [[paper_notes]] · [[RESEARCH_NOTES_LOG]] · [[DATASETS]]",
        "",
    ]

    dest = PAPER_DIR / f"{slug}.md"
    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest


# ── Dataset note ─────────────────────────────────────────────────────────────

def write_dataset_note(record: dict, idx: int) -> Path:
    uid   = record.get("uid", f"dataset_{idx}")
    title = safe_str(record.get("title")) or "Unnamed dataset"
    desc  = safe_str(record.get("description"))
    src   = record.get("source", "")
    url   = record.get("url", "")
    dl    = record.get("download_url", "")
    rel   = record.get("relevance", 0.0)
    meta  = record.get("metadata", {})
    slug  = slugify(uid)

    lines = [
        "---",
        f"type: dataset",
        f"uid: {yaml_str(uid)}",
        f"title: {yaml_str(title)}",
        f"source: {yaml_str(src)}",
        f"url: {yaml_str(url)}",
        f"download_url: {yaml_str(dl)}",
        f"relevance: {round(rel, 3)}",
        f"relevance_label: {relevance_label(rel)}",
        f"validated: {str(record.get('passed', False)).lower()}",
        f"tags: [{', '.join(tags_for(record))}]",
        "---",
        "",
        f"# {title}",
        "",
        "## Description",
        "",
        desc if desc else "_No description — check URL._",
        "",
        "## Source",
        "",
        f"| Field | Value |",
        f"|---|---|",
        f"| Source | {src} |",
        f"| URL | [{uid}]({url}) |",
    ]

    if dl:
        lines.append(f"| Download | [{dl[:60]}...]({dl}) |" if len(dl) > 60 else f"| Download | [{dl}]({dl}) |")

    meta_entries = {k: v for k, v in meta.items() if k not in ("source",) and v}
    if meta_entries:
        lines += ["", "## Metadata", ""]
        for k, v in meta_entries.items():
            lines.append(f"- **{k}**: {v}")

    lines += [
        "",
        "## Usage in Pipeline",
        "",
        "_Annotate: how does this dataset fit into the GNN-PCNA pipeline?_",
        "",
        "- [ ] Pre-training (CryptoSite-style)",
        "- [ ] Fine-tuning",
        "- [ ] Evaluation / benchmark",
        "- [ ] Negative controls",
        "",
        "## Connections",
        "",
        "**Hub**: [[_HUB_DATASETS]] · [[KNOWLEDGE_GRAPH]]",
        "",
        "**Pipeline**: [[PIPELINE]] · [[DATASETS]] · [[fetch_structures]]",
        "",
    ]

    dest = DATA_DIR / f"{slug}.md"
    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest


# ── Compound note ─────────────────────────────────────────────────────────────

def write_compound_note(record: dict, idx: int) -> Path:
    uid   = record.get("uid", f"compound_{idx}")
    title = safe_str(record.get("title")) or uid
    desc  = safe_str(record.get("description"))
    src   = record.get("source", "")
    url   = record.get("url", "")
    rel   = record.get("relevance", 0.0)
    meta  = record.get("metadata", {})
    slug  = slugify(uid)

    lines = [
        "---",
        f"type: compound",
        f"uid: {yaml_str(uid)}",
        f"title: {yaml_str(title)}",
        f"source: {yaml_str(src)}",
        f"url: {yaml_str(url)}",
        f"relevance: {round(rel, 3)}",
        f"relevance_label: {relevance_label(rel)}",
        f"validated: {str(record.get('passed', False)).lower()}",
    ]

    if meta.get("smiles"):
        lines.append(f"smiles: {yaml_str(meta['smiles'])}")
    if meta.get("cid"):
        lines.append(f"pubchem_cid: {meta['cid']}")
    if meta.get("chembl_id"):
        lines.append(f"chembl_id: {meta['chembl_id']}")
    if meta.get("organism"):
        lines.append(f"organism: {yaml_str(meta['organism'])}")
    if meta.get("target_type"):
        lines.append(f"target_type: {yaml_str(meta['target_type'])}")

    lines += [
        f"tags: [{', '.join(tags_for(record))}]",
        "---",
        "",
        f"# {title}",
        "",
        "## Description",
        "",
        desc if desc else "_No description._",
        "",
    ]

    if meta.get("smiles"):
        lines += [
            "## Structure",
            "",
            f"```",
            f"SMILES: {meta['smiles']}",
            f"```",
            "",
        ]

    lines += [
        "## Source",
        "",
        f"- **Database**: {src}",
        f"- **URL**: [{uid}]({url})",
        "",
        "## Relevance to PCNA Research",
        "",
    ]

    if "AOH1996" in title or "AOH" in uid.upper():
        lines += [
            "**AOH1996 is the ground-truth PCNA inhibitor.**",
            "",
            "- Binds the cryptic pocket visible in PDB [[8GLA]]",
            "- Pocket is ABSENT in apo structure [[1W60]]",
            "- Used to label pocket residues (within 6 Å = positive label)",
            "- Ground truth for the entire GNN-PCNA project",
            "",
        ]
    else:
        lines += [
            "_Annotate: what is this compound's relevance to PCNA cryptic pocket research?_",
            "",
        ]

    meta_entries = {k: v for k, v in meta.items() if k not in ("source", "smiles") and v}
    if meta_entries:
        lines += ["## Metadata", ""]
        for k, v in meta_entries.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")

    lines += [
        "## Connections",
        "",
        "**Hub**: [[_HUB_COMPOUNDS]] · [[KNOWLEDGE_GRAPH]]",
        "",
        "**Related**: [[8GLA]] · [[BIOLOGY_PCNA]] · [[DATASETS]]",
        "",
    ]

    dest = CMPD_DIR / f"{slug}.md"
    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest


# ── Hub notes ─────────────────────────────────────────────────────────────────

def write_hub(hub_type: str, notes: list[tuple[str, str, float]],
              description: str) -> Path:
    """Write a hub note linking all notes of a given type.
    notes = [(uid, title, relevance), ...]
    """
    now   = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    fname = f"_HUB_{hub_type.upper()}.md"
    dest  = VAULT_DIR / fname
    slug  = hub_type.lower()

    # Sort by relevance descending
    notes_sorted = sorted(notes, key=lambda x: -x[2])

    high   = [(u, t, r) for u, t, r in notes_sorted if r >= 0.5]
    medium = [(u, t, r) for u, t, r in notes_sorted if 0.2 <= r < 0.5]
    low    = [(u, t, r) for u, t, r in notes_sorted if r < 0.2]

    lines = [
        "---",
        f"type: hub",
        f"hub_for: {slug}",
        f"generated: {now}",
        f"total_nodes: {len(notes)}",
        f"tags: [hub, pcna, {slug}]",
        "---",
        "",
        f"# {hub_type.title()} Hub",
        "",
        description,
        "",
        f"**{len(notes)} nodes** | Updated: {now}",
        "",
        "**Navigation**: [[KNOWLEDGE_GRAPH]] · [[PIPELINE]] · [[DATASETS]]",
        "",
    ]

    def section(label: str, items: list):
        if not items:
            return
        lines.append(f"## {label} ({len(items)})")
        lines.append("")
        lines.append("| Node | Title | Relevance |")
        lines.append("|---|---|---|")
        for uid, title, rel in items:
            lines.append(f"| [[{uid}]] | {title[:60]} | {rel:.2f} |")
        lines.append("")

    section("High Relevance", high)
    section("Medium Relevance", medium)
    section("Low / Peripheral", low)

    lines += [
        "## All Nodes (wikilinks)",
        "",
        " · ".join(f"[[{u}]]" for u, _, _ in notes_sorted),
        "",
    ]

    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest


# ── Master knowledge graph ────────────────────────────────────────────────────

def write_knowledge_graph(stats: dict) -> Path:
    now  = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dest = VAULT_DIR / "KNOWLEDGE_GRAPH.md"

    lines = [
        "---",
        "type: knowledge-graph-root",
        f"generated: {now}",
        f"total_nodes: {stats.get('total', 0)}",
        "tags: [hub, pcna, knowledge-graph, mcp-ready]",
        "---",
        "",
        "# GNN-PCNA Knowledge Graph",
        "",
        "> Root node for the PCNA cryptic pocket prediction knowledge base.",
        "> All data is crawled, validated, and linked. MCP-connectable.",
        "",
        f"**Generated**: {now}  ",
        f"**Total nodes**: {stats.get('total', 0)}  ",
        f"**Structures**: {stats.get('structures', 0)} PDB entries  ",
        f"**Papers**: {stats.get('papers', 0)} literature nodes  ",
        f"**Datasets**: {stats.get('datasets', 0)} dataset nodes  ",
        f"**Compounds**: {stats.get('compounds', 0)} compound nodes  ",
        "",
        "---",
        "",
        "## Hub Index",
        "",
        "| Hub | Nodes | Description |",
        "|---|---|---|",
        f"| [[_HUB_STRUCTURES]] | {stats.get('structures', 0)} | PDB crystal structures + metadata |",
        f"| [[_HUB_PAPERS]] | {stats.get('papers', 0)} | Literature: PubMed, bioRxiv papers |",
        f"| [[_HUB_DATASETS]] | {stats.get('datasets', 0)} | Training datasets (Zenodo, GitHub) |",
        f"| [[_HUB_COMPOUNDS]] | {stats.get('compounds', 0)} | Inhibitors, bioactivity (ChEMBL, PubChem) |",
        "",
        "---",
        "",
        "## Ground Truth Structures",
        "",
        "| Structure | Role | Resolution |",
        "|---|---|---|",
        "| [[8GLA]] | **Holo — positive label** | 3.77 Å |",
        "| [[1W60]] | Apo — negative label | 3.15 Å |",
        "| [[4RJF]] | High-res apo (best features) | 2.0 Å |",
        "| [[1U7B]] | Highest resolution | 1.88 Å |",
        "| [[1AXC]] | PIP-box complex | 2.6 Å |",
        "| [[1W61]] | **EXCLUDED** — proline racemase, not PCNA | 2.1 Å |",
        "| [[9N3L]] | Novel inhibitor — investigate | 1.9 Å |",
        "",
        "---",
        "",
        "## Pipeline Links",
        "",
        "| Stage | File | Status |",
        "|---|---|---|",
        "| Data acquisition | [[fetch_structures]] | Done |",
        "| PDB parsing | [[parse_pdb]] | Stub |",
        "| Graph construction | [[graph_construction]] | Stub |",
        "| Model | [[MODELS]] (CrypticGNN) | Implemented |",
        "| Training | [[train]] | Stub |",
        "| Validation | [[VALIDATION]] | Design |",
        "",
        "---",
        "",
        "## MCP Integration",
        "",
        "This vault is MCP-connectable. To wire a knowledge-graph MCP to the ML model:",
        "",
        "```",
        "Obsidian vault root: C:/Users/advay/GNN_PNCA/",
        "KNOWLEDGE_GRAPH.md:  docs/vault/KNOWLEDGE_GRAPH.md",
        "Catalog JSON:        data/catalog/pcna_data_catalog.json",
        "Raw catalog:         data/catalog/raw_catalog.json",
        "```",
        "",
        "**Query pattern**: ask the MCP for structures with `relevance >= 0.5` and `validated: true`",
        "to get the curated training set. Use `type: paper` nodes for literature context.",
        "",
        "---",
        "",
        "## Biology Context",
        "",
        "[[BIOLOGY_PCNA]] · [[RESEARCH_QUESTION]] · [[paper_notes]] · [[KNOWN_LIMITATIONS]]",
        "",
        "## Experiments",
        "",
        "[[EXPERIMENT_INDEX]] · [[RESEARCH_NOTES_LOG]]",
        "",
        "## Workflow",
        "",
        "[[PIPELINE]] · [[AGENTS]] · [[AI_WORKFLOW_RULES]] · [[SYSTEM_OVERVIEW]]",
        "",
    ]

    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Export crawler catalog to linked Obsidian vault notes")
    parser.add_argument("--catalog", type=Path,
                        default=CATALOG_DIR / "raw_catalog.json",
                        help="Path to raw_catalog.json (default: data/catalog/raw_catalog.json)")
    parser.add_argument("--min-relevance", type=float, default=0.0,
                        help="Min relevance score to include a record (default: 0.0 = all)")
    parser.add_argument("--validated-only", action="store_true",
                        help="Only export records that passed 5-layer validation")
    args = parser.parse_args()

    if not args.catalog.exists():
        # Fall back to pcna_data_catalog.json
        fallback = CATALOG_DIR / "pcna_data_catalog.json"
        if fallback.exists():
            args.catalog = fallback
            print(f"Using fallback catalog: {fallback}")
        else:
            print(f"No catalog found at {args.catalog}. Run pcna_crawler.py first.")
            return

    raw = json.loads(args.catalog.read_text(encoding="utf-8"))

    # Support both raw_catalog.json (all_records) and pcna_data_catalog.json (passed)
    if "all_records" in raw:
        records = raw["all_records"]
    elif "passed" in raw:
        records = raw["passed"]
        # Also include failed records for Obsidian (with metadata for context)
        for r in raw.get("failed_summary", []):
            r["passed"] = False
            r.setdefault("record_type", "unknown")
            r.setdefault("relevance", 0.0)
        # Note: failed_summary only has uid/source/fail, not full record — skip
    else:
        print("Unrecognised catalog format.")
        return

    # Filter
    filtered = [r for r in records
                if r.get("relevance", 0.0) >= args.min_relevance
                and (not args.validated_only or r.get("passed", False))]

    print(f"Catalog: {len(records)} total records → {len(filtered)} after filter")

    struct_notes, paper_notes, dataset_notes, compound_notes = [], [], [], []

    for i, rec in enumerate(filtered):
        rtype = rec.get("record_type", "")
        uid   = rec.get("uid", f"rec_{i}")
        title = safe_str(rec.get("title")) or uid
        rel   = rec.get("relevance", 0.0)

        try:
            if rtype == "pdb_structure":
                write_structure_note(rec)
                struct_notes.append((uid, title, rel))

            elif rtype in ("paper", "pubmed_record", "preprint"):
                p = write_paper_note(rec, i)
                paper_notes.append((p.stem, title, rel))

            elif rtype in ("dataset", "github_dataset", "zenodo_dataset",
                           "protein_record", "domain_annotation"):
                p = write_dataset_note(rec, i)
                dataset_notes.append((p.stem, title, rel))

            elif rtype in ("compound", "chembl_target", "pubchem_compound"):
                p = write_compound_note(rec, i)
                compound_notes.append((p.stem, title, rel))

            elif rtype == "unknown":
                # best-guess routing by source
                src = rec.get("source", "")
                if src in ("pubmed", "biorxiv"):
                    p = write_paper_note(rec, i)
                    paper_notes.append((p.stem, title, rel))
                elif src in ("zenodo", "github"):
                    p = write_dataset_note(rec, i)
                    dataset_notes.append((p.stem, title, rel))
                elif src in ("chembl", "pubchem"):
                    p = write_compound_note(rec, i)
                    compound_notes.append((p.stem, title, rel))

        except Exception as e:
            print(f"  [!] failed to write note for {uid}: {e}")

    # Force known PCNA structures even if not in catalog
    for pid in ("1W60", "8GLA", "1AXC", "4RJF", "1U7B", "9N3L", "8F5Q"):  # 1W61 excluded — proline racemase
        if not any(u == pid for u, _, _ in struct_notes):
            stub = {
                "uid": pid, "record_type": "pdb_structure",
                "title": KNOWN_ANNOTATIONS.get(pid, {}).get("note", f"PCNA {pid}"),
                "source": "known", "relevance": 0.9 if pid in KNOWN_PCNA_IDS else 0.6,
                "passed": pid in KNOWN_PCNA_IDS,
                "metadata": {}, "validation": {},
                "download_url": f"https://files.rcsb.org/download/{pid}.pdb",
            }
            try:
                write_structure_note(stub)
                struct_notes.append((pid, stub["title"][:60], stub["relevance"]))
            except Exception as e:
                print(f"  [!] stub note failed for {pid}: {e}")

    # Write hubs
    write_hub("STRUCTURES", struct_notes,
              "All PDB structures found for PCNA (human, P12004) — X-ray and cryo-EM. "
              "Core set: [[8GLA]] (ground truth), [[1W60]] (apo baseline).")
    write_hub("PAPERS", paper_notes,
              "Literature: PubMed and bioRxiv papers relevant to PCNA cryptic pockets, "
              "GNN pocket prediction, and molecular dynamics.")
    write_hub("DATASETS", dataset_notes,
              "Training datasets: CryptoSite benchmark, Zenodo repositories, "
              "GitHub supplementary data.")
    write_hub("COMPOUNDS", compound_notes,
              "Small molecules: AOH1996 (ground-truth PCNA inhibitor), "
              "ChEMBL bioactivity records, PubChem compound data.")

    stats = {
        "total": len(struct_notes) + len(paper_notes) + len(dataset_notes) + len(compound_notes),
        "structures": len(struct_notes),
        "papers": len(paper_notes),
        "datasets": len(dataset_notes),
        "compounds": len(compound_notes),
    }
    write_knowledge_graph(stats)

    print(f"\nVault export complete -> {VAULT_DIR}")
    print(f"  Structures : {stats['structures']:>4} notes  ({STRUCT_DIR})")
    print(f"  Papers     : {stats['papers']:>4} notes  ({PAPER_DIR})")
    print(f"  Datasets   : {stats['datasets']:>4} notes  ({DATA_DIR})")
    print(f"  Compounds  : {stats['compounds']:>4} notes  ({CMPD_DIR})")
    print(f"  Total      : {stats['total']:>4} nodes in graph")
    print(f"\n  KNOWLEDGE_GRAPH.md -> {VAULT_DIR / 'KNOWLEDGE_GRAPH.md'}")


if __name__ == "__main__":
    main()
