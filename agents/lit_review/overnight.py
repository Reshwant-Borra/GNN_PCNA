#!/usr/bin/env python3
"""
GNN-PCNA Overnight Literature Review Loop
Runs 4 rounds of expanded queries, saves to context/, pushes to NotebookLM,
commits to git. Runs indefinitely until Ctrl+C.

Usage:
  PYTHONIOENCODING=utf-8 python agents/lit_review/overnight.py
  PYTHONIOENCODING=utf-8 python agents/lit_review/overnight.py --no-git
  PYTHONIOENCODING=utf-8 python agents/lit_review/overnight.py --sleep 1800
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
HERE    = Path(__file__).parent
ROOT    = HERE.parent.parent          # GNN_PNCA/
CONTEXT = ROOT / "context"
CONTEXT.mkdir(exist_ok=True)

# ── Import agent tools ────────────────────────────────────────────────────────
sys.path.insert(0, str(HERE))
import agent

# Point agent's session dir at context/
agent._init_sess(CONTEXT)

# ── Args ──────────────────────────────────────────────────────────────────────
AUTO_GIT  = "--no-git" not in sys.argv
SLEEP_SEC = int(next((sys.argv[i+1] for i, a in enumerate(sys.argv)
                      if a == "--sleep" and i+1 < len(sys.argv)), 1200))
NLM_SCRIPT = Path.home() / "tools" / "notebooklm" / "notebooklm_skill.py"

# ── Extra query rounds (beyond the 50 in DRY_RUN_QUERIES) ────────────────────
ROUND_QUERIES = {

    1: [  # Structural biology deep-dive
        ("search_pubmed",            {"query": "PCNA sliding DNA clamp replication fork structure crystal", "max_results": 40}),
        ("search_openalex",          {"query": "PCNA sliding clamp replication repair checkpoint", "max_results": 50}),
        ("search_pubmed",            {"query": "PCNA ubiquitination monoubiquitylation SUMOylation DDT pathway", "max_results": 30}),
        ("search_europe_pmc",        {"query": "PCNA p21 interaction PIP box PCNA-interacting protein", "max_results": 40}),
        ("search_pubmed",            {"query": "PCNA inhibitor peptide small molecule anticancer activity", "max_results": 40}),
        ("search_crossref",          {"query": "PCNA cancer biomarker triple negative breast colorectal prognosis", "max_results": 40}),
        ("search_openalex",          {"query": "protein-protein interface drug design hot spots inhibitor", "max_results": 50}),
        ("search_pubmed",            {"query": "undruggable cancer target protein-protein interaction small molecule", "max_results": 30}),
        ("search_openalex",          {"query": "protein pocket flexibility induced fit conformational selection", "max_results": 50}),
        ("search_crossref",          {"query": "structure-based drug design fragment screening cryptic", "max_results": 40}),
        ("search_pubmed",            {"query": "virtual screening docking binding pocket druggability", "max_results": 40}),
        ("search_europe_pmc",        {"query": "FBDD fragment-based drug discovery cryptic allosteric site", "max_results": 30}),
        ("search_biorxiv_preprints", {"query": "PCNA structure biology cancer drug new", "max_results": 25}),
        ("search_biorxiv_preprints", {"query": "cryptic pocket discovery machine learning 2024 2025", "max_results": 25}),
    ],

    2: [  # Advanced ML architectures
        ("search_arxiv",             {"query": "SchNet DimeNet PaiNN equivariant neural network molecular property", "max_results": 40}),
        ("search_openalex",          {"query": "SchNet DimeNet molecular graph neural network atomic interactions", "max_results": 40}),
        ("search_arxiv",             {"query": "EquiformerV2 SE3 equivariant transformer protein structure", "max_results": 40}),
        ("search_arxiv",             {"query": "AlphaFold protein structure prediction binding site pocket", "max_results": 40}),
        ("search_openalex",          {"query": "AlphaFold2 predicted structure drug binding site discovery", "max_results": 50}),
        ("search_arxiv",             {"query": "graph transformer protein function drug discovery attention", "max_results": 40}),
        ("search_openalex",          {"query": "graph transformer molecular property prediction binding affinity", "max_results": 40}),
        ("search_arxiv",             {"query": "contrastive learning self-supervised protein representation", "max_results": 40}),
        ("search_crossref",          {"query": "deep learning protein 3D structure pocket binding site comparison", "max_results": 40}),
        ("search_openalex",          {"query": "graph convolutional network drug target interaction prediction", "max_results": 50}),
        ("search_arxiv",             {"query": "TorchMD-NET NequIP SEGNN equivariant protein energy", "max_results": 40}),
        ("search_openalex",          {"query": "virtual node global pooling graph neural network molecular", "max_results": 40}),
        ("search_crossref",          {"query": "focal loss imbalanced dataset binding site prediction", "max_results": 30}),
        ("search_biorxiv_preprints", {"query": "graph neural network protein pocket 2024 2025 deep learning", "max_results": 25}),
    ],

    3: [  # Pocket detection and MD methods
        ("search_pubmed",            {"query": "fpocket DoGSiteScorer P2Rank SiteMap binding site prediction comparison", "max_results": 40}),
        ("search_openalex",          {"query": "fpocket Volsurf binding site prediction druggability score", "max_results": 50}),
        ("search_crossref",          {"query": "SiteMap Glide Schrodinger docking pocket detection", "max_results": 40}),
        ("search_pubmed",            {"query": "machine learning druggability prediction binding pocket scoring", "max_results": 40}),
        ("search_openalex",          {"query": "neural network protein surface pocket geometry detection 3D", "max_results": 50}),
        ("search_pubmed",            {"query": "GROMACS NAMD AMBER OpenMM molecular dynamics protein", "max_results": 30}),
        ("search_openalex",          {"query": "CHARMM36m force field protein MD simulation NPT ensemble", "max_results": 40}),
        ("search_pubmed",            {"query": "umbrella sampling free energy perturbation protein pocket", "max_results": 30}),
        ("search_crossref",          {"query": "accelerated molecular dynamics protein conformational change pocket", "max_results": 30}),
        ("search_pubmed",            {"query": "Markov state model protein conformational dynamics pocket", "max_results": 30}),
        ("search_openalex",          {"query": "protein fluctuation B-factor flexibility drug binding site", "max_results": 40}),
        ("search_crossref",          {"query": "protein conformation ensemble pocket volume POVME EPOCK", "max_results": 30}),
        ("search_europe_pmc",        {"query": "molecular dynamics simulation PCNA protein flexibility binding", "max_results": 40}),
        ("search_biorxiv_preprints", {"query": "molecular dynamics protein pocket opening simulation 2024", "max_results": 25}),
    ],

    4: [  # Cancer drug discovery + benchmarks + related proteins
        ("search_pubmed",            {"query": "BRCA1 BRCA2 CDK2 MDM2 p53 cryptic pocket inhibitor", "max_results": 30}),
        ("search_openalex",          {"query": "cancer target allosteric inhibitor clinical trial drug", "max_results": 50}),
        ("search_pubmed",            {"query": "RAS KRAS allosteric inhibitor switch II pocket covalent", "max_results": 30}),
        ("search_crossref",          {"query": "PD-L1 immune checkpoint cryptic pocket small molecule", "max_results": 30}),
        ("search_openalex",          {"query": "benchmark protein pocket prediction DUD-E CASF evaluation metric", "max_results": 40}),
        ("search_pubmed",            {"query": "AUROC AUPRC enrichment factor binding site evaluation", "max_results": 30}),
        ("search_crossref",          {"query": "benchmark dataset protein cryptic pocket evaluation comparison", "max_results": 40}),
        ("search_openalex",          {"query": "Shrake Rupley SASA solvent accessible surface protein pocket", "max_results": 40}),
        ("search_pubmed",            {"query": "ESM1b ESM1v evolutionary scale modeling protein variant", "max_results": 30}),
        ("search_arxiv",             {"query": "protein language model zero shot mutation fitness prediction", "max_results": 40}),
        ("search_openalex",          {"query": "ProteinMPNN protein design language model structure", "max_results": 40}),
        ("search_arxiv",             {"query": "RoseTTAFold OpenFold protein structure ab initio", "max_results": 40}),
        ("search_openalex",          {"query": "DSSP secondary structure assignment protein feature engineering", "max_results": 30}),
        ("search_biorxiv_preprints", {"query": "cancer drug discovery AI machine learning 2025 clinical", "max_results": 25}),
    ],
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_context() -> int:
    """Load all previously saved papers from context/ into agent.PAPERS."""
    loaded = 0
    for f in sorted(CONTEXT.glob("**/*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            for p in data.get("papers", []):
                src = p.get("source", "ctx")
                if agent._add(p, src):
                    loaded += 1
        except Exception:
            continue
    return loaded


def save_round(round_n: int, new_papers: int) -> Path:
    """Save current PAPERS to a round-specific JSON in context/."""
    out = CONTEXT / f"round_{round_n:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    lst = sorted(agent.PAPERS.values(), key=lambda p: -(p.get("citations", 0)))
    urls = [p.get("pdf_url") or p.get("url") or "" for p in lst]
    urls = [u for u in urls if u.startswith("http")]
    urls = list(dict.fromkeys(urls))

    out.write_text(
        json.dumps({"round": round_n, "timestamp": datetime.now().isoformat(),
                    "new_papers": new_papers, "total": len(lst),
                    "papers": lst},
                   indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    urls_file = CONTEXT / f"round_{round_n:02d}_urls.txt"
    urls_file.write_text("\n".join(urls[:300]), encoding="utf-8")

    print(f"[SAVE]  {out.name}  ({len(lst)} total, {new_papers} new, {len(urls)} URLs)")
    return urls_file


def push_notebooklm(urls_file: Path, notebook_id: str = None) -> str:
    """Add URLs to NotebookLM. Creates notebook on first call, reuses after."""
    if not NLM_SCRIPT.exists():
        print("[NLM]  notebooklm_skill.py not found — skipping")
        return notebook_id or ""

    try:
        if not notebook_id:
            r = subprocess.run(
                [sys.executable, str(NLM_SCRIPT), "create",
                 "--name", "GNN-PCNA LitReview (Live)"],
                capture_output=True, text=True, timeout=90,
            )
            notebook_id = r.stdout.strip().split()[-1] if r.returncode == 0 else ""
            print(f"[NLM]  Created notebook: {notebook_id}")

        if notebook_id:
            r2 = subprocess.run(
                [sys.executable, str(NLM_SCRIPT), "add-sources",
                 "--id", notebook_id, "--sources-file", str(urls_file)],
                capture_output=True, text=True, timeout=180,
            )
            if r2.returncode == 0:
                print(f"[NLM]  Sources added to {notebook_id}")
            else:
                print(f"[NLM]  add-sources error: {r2.stderr[:200]}")
    except Exception as e:
        print(f"[NLM]  Error: {e}")

    return notebook_id or ""


def git_commit(round_n: int, new_papers: int) -> None:
    if not AUTO_GIT:
        return
    try:
        subprocess.run(["git", "-C", str(ROOT), "add", "context/", "agents/lit_review/"],
                       check=True, capture_output=True)
        msg = f"lit-review: round {round_n} — {new_papers} new papers ({len(agent.PAPERS)} total)"
        subprocess.run(["git", "-C", str(ROOT), "commit", "-m", msg],
                       check=True, capture_output=True)
        print(f"[GIT]  Committed: {msg}")
    except subprocess.CalledProcessError as e:
        print(f"[GIT]  Nothing to commit or error: {e.stderr[:100] if e.stderr else 'no changes'}")


def run_round(round_n: int) -> int:
    """Execute one round of queries. Returns number of new papers added."""
    queries = ROUND_QUERIES.get(round_n, [])
    if not queries:
        print(f"[WARN] No queries for round {round_n}")
        return 0

    before = len(agent.PAPERS)
    print(f"\n{'='*60}")
    print(f"[ROUND {round_n}]  {len(queries)} queries  |  {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")

    for name, args in queries:
        fn = agent.TOOL_MAP.get(name)
        if not fn:
            continue
        result = fn(**args)
        count  = result.get("count", 0)
        total  = len(agent.PAPERS)
        print(f"  {name:<30} +{count:<4} | total={total}  [{args['query'][:45]}]")
        time.sleep(0.4)

    # Citation chain on high-impact discoveries this round
    top = sorted(
        [p for p in agent.PAPERS.values()
         if p.get("s2_id") and p.get("citations", 0) > 200],
        key=lambda p: -p.get("citations", 0),
    )[:5]
    for p in top:
        print(f"  cite-chain: {p['title'][:55]}  ({p.get('citations',0)} cites)")
        agent.get_s2_citations(p["s2_id"], 25)
        agent.get_s2_references(p["s2_id"], 30)

    new = len(agent.PAPERS) - before
    print(f"\n[ROUND {round_n}]  done  +{new} new  |  total={len(agent.PAPERS)}")
    return new


# ── Main loop ─────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"[OVERNIGHT] GNN-PCNA Literature Review Loop")
    print(f"[OVERNIGHT] Context dir : {CONTEXT}")
    print(f"[OVERNIGHT] Auto-git    : {AUTO_GIT}")
    print(f"[OVERNIGHT] Sleep (s)   : {SLEEP_SEC}")
    print(f"[OVERNIGHT] NotebookLM  : {'yes' if NLM_SCRIPT.exists() else 'not found'}")

    # Load any papers already on disk
    loaded = load_context()
    print(f"[OVERNIGHT] Loaded {loaded} existing papers from context/ (dedup seed)\n")

    notebook_id = ""
    round_n = 1

    try:
        while True:
            new = run_round(round_n)
            urls_file = save_round(round_n, new)

            if NLM_SCRIPT.exists() and new > 0:
                notebook_id = push_notebooklm(urls_file, notebook_id)

            git_commit(round_n, new)

            # Cycle rounds 1-4 indefinitely
            round_n = (round_n % 4) + 1

            stats = agent.get_paper_stats()
            print(f"[SLEEP]  cumulative={stats['total']} papers | "
                  f"sleeping {SLEEP_SEC//60} min...")
            time.sleep(SLEEP_SEC)

    except KeyboardInterrupt:
        print(f"\n[OVERNIGHT] Interrupted. Total papers: {len(agent.PAPERS)}")
        save_round(0, 0)
        git_commit(0, 0)


if __name__ == "__main__":
    main()
