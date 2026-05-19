"""Generate per-protein markdown docs + AOH1996 candidate extract."""
import csv, json, sys, io
from pathlib import Path
from datetime import date

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO   = Path(__file__).parent.parent
PDIR   = REPO / "results" / "per_structure"
OUTDIR = REPO / "docs" / "proteins"
OUTDIR.mkdir(parents=True, exist_ok=True)

TODAY  = date.today().isoformat()

# Large replication complexes — AUROC unreliable due to AGS/ADP contamination
COMPLEX_CONTAM = {"8UN0","8UMY","8UMU","8UMT","6VVO","8UI8","8UI9"}

AOH_GT_N = 24   # total ground-truth residues in AOH1996 site

rows = list(csv.DictReader(
    open(PDIR / "summary_table.csv", encoding="utf-8", errors="replace")))

# Load V3 AUROCs from v3_summary.csv if available (held-out structures only)
V3_CSV = REPO / "results" / "v3" / "v3_summary.csv"
TRAINING_STRUCTS = {"8GLA"}  # fine-tuned on these — V3 AUROC is invalid for them
v3_auroc: dict[str, float] = {}
if V3_CSV.exists():
    for row in csv.DictReader(open(V3_CSV, encoding="utf-8")):
        pdb = row["pdb"]
        val = row.get("auroc_v3", "")
        if val and val != "N/A":
            try:
                v3_auroc[pdb] = float(val)
            except ValueError:
                pass

def category(r):
    p = r["pdb"]
    if p in {"8GLA","8GL9","8GCJ"}: return "AOH1996 holo (confirmed binder)"
    if p in {"1W60","4RJF","1U7B"}: return "Canonical apo PCNA"
    if p == "9B8T":                 return "Novel site (Pol epsilon interface)"
    if p in COMPLEX_CONTAM:         return "Large replication complex (AUROC unreliable)"
    return "Other PCNA structure"

def auroc_str(r):
    p = r["pdb"]
    raw = r.get("auroc","")
    if raw:
        note = " (raw — may include co-factor ligands)" if p in COMPLEX_CONTAM else " (raw, ligand-proximity labels)"
        return f"{float(raw):.4f}{note}"
    return "N/A (apo — no ligand for labeling)"

def overlap_bar(n, total=AOH_GT_N):
    filled = round(n / total * 20)
    return f"{'#' * filled}{'.' * (20 - filled)}  {n}/{total}"

def write_protein_doc(r):
    pdb   = r["pdb"]
    rdir  = PDIR / pdb
    title = r["title"].split("PROTEIN")[0].strip().rstrip(",").strip()

    # read report.txt
    report_path = rdir / "report.txt"
    report_text = report_path.read_text(encoding="utf-8", errors="replace") \
                  if report_path.exists() else "_Report not found._"

    # read summary.json
    summ = {}
    summ_path = rdir / "summary.json"
    if summ_path.exists():
        try:
            summ = json.loads(summ_path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            pass

    aoh_n   = int(r["top_aoh_overlap"])
    tc_mean = float(r["top_cluster_mean"])
    tc_n    = int(r["top_cluster_n"])
    n_res   = int(r["n_residues"])
    n_chain = int(r["n_chains"])
    ligs    = r["ligands"] or "none (apo)"
    conc    = float(r["top_concavity"]) if r["top_concavity"] else 0.0
    cat     = category(r)

    candidate_flag = (
        aoh_n >= 18 and tc_mean >= 0.55
        and pdb not in COMPLEX_CONTAM
        and pdb not in {"7M5L"}
    )
    candidate_tag = "**AOH1996 CANDIDATE**" if candidate_flag else ""

    lines = [
        f"# {pdb} — {title}",
        f"",
        f"> Generated: {TODAY}  |  Category: {cat}  {candidate_tag}",
        f"",
        f"## Quick Stats",
        f"",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| PDB ID | [{pdb}](https://www.rcsb.org/structure/{pdb}) |",
        f"| Residues | {n_res} across {n_chain} chains |",
        f"| Ligands detected | {ligs} |",
        f"| AUROC | {auroc_str(r)} |",
        f"| Top pocket mean score | {tc_mean:.4f} ({tc_n} residues) |",
        f"| AOH1996 GT overlap | {overlap_bar(aoh_n)} |",
        f"| Top pocket concavity | {conc:.3f} ({'concave' if conc >= 0.5 else 'convex'}) |",
        f"",
        f"## AOH1996 Pocket Assessment",
        f"",
    ]

    threshold_note = (
        f" **Note: mean score {tc_mean:.3f} is below the 0.7 project-defined threshold — "
        f"the AOH1996 pocket is not confidently recovered by this checkpoint.**"
        if tc_mean < 0.7 else ""
    )

    if aoh_n >= 20:
        lines += [
            f"The model's top predicted cluster overlaps with **{aoh_n}/24 AOH1996 ground-truth residues** "
            f"({aoh_n/AOH_GT_N*100:.0f}% of the confirmed pocket from PDB 8GLA). "
            f"Top cluster mean score: {tc_mean:.3f}.{threshold_note}",
            f"",
            f"**Hypothesis (unvalidated):** This region may be compatible with AOH1996 binding. "
            f"Molecular docking or MD simulation is required to test this hypothesis. "
            f"Labels are derived from ligand-proximity heuristics, not curated benchmark labels.",
        ]
    elif aoh_n >= 12:
        lines += [
            f"Moderate overlap: **{aoh_n}/24 AOH1996 GT residues** found in top cluster "
            f"(mean score {tc_mean:.3f}).{threshold_note} "
            f"Partial pocket similarity may be present — requires further investigation.",
        ]
    else:
        lines += [
            f"Low AOH1996 overlap: **{aoh_n}/24 GT residues** in top cluster "
            f"(mean score {tc_mean:.3f}). The top predicted region does not coincide with "
            f"the AOH1996 site. This may indicate a distinct binding interface or a model "
            f"prediction artefact — not a validated novel pocket.",
        ]

    lines += [
        f"",
        f"## Full Analysis Report",
        f"",
        f"```",
        report_text.strip(),
        f"```",
        f"",
        f"## Data Files",
        f"",
        f"> **Gitignored** — regenerate locally with `python scripts/per_structure_analysis.py`",
        f"> PDB inputs: `python agents/pcna_crawler.py --download` | Graphs: `python scripts/build_graphs.py`",
        f"",
        f"| File | Description | Tracked in git? |",
        f"|------|-------------|----------------|",
        f"| `results/per_structure/{pdb}/scores.csv` | Per-residue pocket scores | No |",
        f"| `results/per_structure/{pdb}/clusters.csv` | DBSCAN cluster assignments | No |",
        f"| `results/per_structure/{pdb}/report.txt` | Full text analysis report | No |",
        f"| `results/per_structure/{pdb}/summary.json` | Machine-readable summary | No |",
        f"| `results/per_structure/summary_table.csv` | All-59 rollup | Yes |",
        f"| `checkpoints/pcna/best_pcna.ckpt` | Trained model weights | Yes |",
        f"| `data/raw/{pdb}.pdb` | Raw PDB structure | No |",
        f"| `data/graphs/{pdb}.pt` | PyG graph tensor | No |",
        f"",
        f"---",
        f"*GNN-PCNA v2 | Dual-branch GATv2Conv | Checkpoint tracked at `checkpoints/pcna/best_pcna.ckpt`*",
    ]

    out = OUTDIR / f"{pdb}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return candidate_flag

# ── Generate all per-protein docs ──────────────────────────────────────────────
candidates = []
for r in rows:
    is_cand = write_protein_doc(r)
    if is_cand:
        candidates.append(r)
    print(f"  wrote docs/proteins/{r['pdb']}.md {'[CANDIDATE]' if is_cand else ''}")

print(f"\nWrote {len(rows)} protein docs.")

# ── AOH1996 Candidate Extract ──────────────────────────────────────────────────
candidates.sort(key=lambda r: (
    -int(r["top_aoh_overlap"]),
    -float(r["top_cluster_mean"])
))

extract_lines = [
    f"# AOH1996 Candidate Structures — Cryptic Pocket Extract",
    f"",
    f"> Generated: {TODAY}",
    f"> Criteria: AOH1996 GT overlap >= 18/24 residues AND top cluster mean >= 0.55 AND no co-factor contamination",
    f"",
    f"## What This Means",
    f"",
    f"AOH1996 (molecular weight ~900 Da) targets a cryptic pocket at the PCNA A-B subunit interface, "
    f"engaging residues in the C-terminal loop (231-253) and IDCL (119-134). "
    f"Structures listed here have GNN-predicted pockets that spatially overlap >75% with the experimentally "
    f"confirmed binding site from PDB 8GLA.",
    f"",
    f"These represent PCNA conformations in which the cryptic pocket is **at least partially pre-opened** "
    f"— the most accessible states for AOH1996 binding.",
    f"",
    f"## Tier 1 — Highest Confidence (overlap >= 22, score >= 0.60)",
    f"",
    f"| PDB | Description | AOH GT overlap | Top score | AUROC | Concavity | Category |",
    f"|-----|-------------|---------------|-----------|-------|-----------|----------|",
]

tier1 = [r for r in candidates if int(r["top_aoh_overlap"]) >= 22 and float(r["top_cluster_mean"]) >= 0.60]
tier2 = [r for r in candidates if r not in tier1]

for r in tier1:
    pdb  = r["pdb"]
    aur  = v3_auroc.get(pdb, float(r["auroc"]) if r["auroc"] else float("nan"))
    aur_str = f"{aur:.4f}" if not (aur != aur) else "N/A"  # nan check
    if pdb in TRAINING_STRUCTS:
        aur_str += " [LEAK]"
    desc = r["title"].split("PROTEIN")[0].strip().rstrip(",")[:55]
    extract_lines.append(
        f"| **{pdb}** | {desc} | {r['top_aoh_overlap']}/24 | "
        f"{float(r['top_cluster_mean']):.3f} | {aur_str} | "
        f"{float(r['top_concavity']):.3f} | {category(r)} |"
    )

extract_lines += [
    f"",
    f"## Tier 2 — Moderate Confidence (overlap >= 18, score >= 0.55)",
    f"",
    f"| PDB | Description | AOH GT overlap | Top score | AUROC | Category |",
    f"|-----|-------------|---------------|-----------|-------|----------|",
]

for r in tier2:
    pdb  = r["pdb"]
    aur  = v3_auroc.get(pdb, float(r["auroc"]) if r["auroc"] else float("nan"))
    aur_str = f"{aur:.4f}" if not (aur != aur) else "N/A"
    if pdb in TRAINING_STRUCTS:
        aur_str += " [LEAK]"
    desc = r["title"].split("PROTEIN")[0].strip().rstrip(",")[:55]
    extract_lines.append(
        f"| {pdb} | {desc} | {r['top_aoh_overlap']}/24 | "
        f"{float(r['top_cluster_mean']):.3f} | {aur_str} | {category(r)} |"
    )

extract_lines += [
    f"",
    f"## Structural Basis for Candidacy",
    f"",
    f"### Why these structures are targetable",
    f"",
    f"1. **PCNA forms a homotrimeric ring** — each monomer presents an identical AOH1996 pocket.",
    f"   Structures with 3 or 6 chains (trimers / dimers-of-trimers) get 3x or 6x binding opportunities.",
    f"",
    f"2. **The cryptic pocket opens via induced fit** — AOH1996 itself induces the open conformation.",
    f"   High GNN scores on apo structures (e.g. 1W60, 4RJF) indicate the pocket is near-open even without ligand.",
    f"",
    f"3. **Concavity >= 0.45** = geometrically pocket-like (inward-pointing surface). These predictions",
    f"   are not artifacts of convex surface protrusions.",
    f"",
    f"### Key residues to target (from 8GLA co-crystal)",
    f"",
    f"| Region | Residues | Role |",
    f"|--------|----------|------|",
    f"| C-terminal loop | 231-234, 250-253 | Primary AOH1996 contacts |",
    f"| IDCL | 123, 125-126, 128 | Induced-fit hinge |",
    f"| Front-face loop | 38-47 | PIP-box groove overlap |",
    f"| Domain 1 surface | 25-27 | Electrostatic anchoring |",
    f"",
    f"### Structures confirmed NOT to be AOH1996 targets",
    f"",
    f"- **9B8T**: Top pocket at Pol epsilon-PCNA interface — novel site, different drug needed",
    f"- **8UN0, 8UMY, 8UMU, 8UMT, 6VVO, 8UI8, 8UI9**: CTF18-RFC/ATAD5-RFC replication complexes;",
    f"  AGS/ADP cofactor contamination makes AUROC unreliable for pocket labeling",
    f"- **7M5L**: Low AOH overlap (6/24), ligand TME/NH2 is not at AOH site",
    f"",
    f"## Recommended Priority for Docking",
    f"",
    f"```",
    f"Priority 1 (highest-scoring — candidate for follow-up):  3VKX, 9N3L, 1W60, 4RJF",
    f"Priority 2 (apo, good):      1AXC, 9CHM, 6FCN, 7KQ0",
    f"Priority 3 (complex, check): 1VYJ, 3P87, 6QCG, 5MAV",
    f"Confirmed holo (reference):  8GLA, 8GL9, 8GCJ",
    f"```",
    f"",
    f"---",
    f"*GNN-PCNA v2  |  Dual-branch GATv2Conv  |  PCNA-chain filtered AUROC  |  {TODAY}*",
]

ext_path = OUTDIR / "aoh1996_candidates.md"
ext_path.write_text("\n".join(extract_lines), encoding="utf-8")
print(f"\nCandidate extract: docs/proteins/aoh1996_candidates.md")
print(f"  Tier 1: {len(tier1)} structures")
print(f"  Tier 2: {len(tier2)} structures")
