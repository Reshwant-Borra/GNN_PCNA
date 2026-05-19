"""
GNN-PCNA MCP Server — exposes the Obsidian vault and model inference to Claude.

Register in Claude Code settings (Settings > MCP Servers):
  Name:    pcna
  Command: python
  Args:    C:/Users/advay/GNN_PNCA/agents/mcp_server.py

Or add to .claude/mcp.json in the repo root.

Tools exposed
─────────────
  list_structures()            — all validated PDB structures from catalog
  get_structure(pdb_id)        — full metadata for one structure
  search_vault(query)          — keyword search across all vault notes
  list_papers()                — literature nodes from vault
  list_datasets()              — dataset nodes from vault
  get_knowledge_graph()        — summary of the full knowledge graph
  run_inference(pdb_id, model) — run PocketGNN on a structure, return scores
  get_pipeline_status()        — what's implemented vs stub
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# ── repo root ─────────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).parent.parent
CATALOG_DIR = REPO_ROOT / "data" / "catalog"
VAULT_DIR   = REPO_ROOT / "docs" / "vault"
RAW_DIR     = REPO_ROOT / "data" / "raw"
sys.path.insert(0, str(REPO_ROOT))

# ── MCP import ────────────────────────────────────────────────────────────────
try:
    from mcp.server.fastmcp import FastMCP
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False
    print("WARNING: mcp package not installed. Run: pip install mcp", file=sys.stderr)

# ── data helpers ──────────────────────────────────────────────────────────────

def _load_catalog() -> dict:
    path = CATALOG_DIR / "raw_catalog.json"
    if not path.exists():
        path = CATALOG_DIR / "pcna_data_catalog.json"
    if not path.exists():
        return {"all_records": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_validated() -> list[dict]:
    path = CATALOG_DIR / "pcna_data_catalog.json"
    if not path.exists():
        return []
    cat = json.loads(path.read_text(encoding="utf-8"))
    return cat.get("passed", [])


def _read_frontmatter(md_path: Path) -> dict:
    """Extract YAML frontmatter from a vault note."""
    text = md_path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {"file": md_path.stem}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"')
    fm["file"] = md_path.stem
    fm["content_preview"] = text[m.end():m.end() + 300].strip()
    return fm


def _search_notes(query: str, subdir: str | None = None) -> list[dict]:
    base = VAULT_DIR / subdir if subdir else VAULT_DIR
    results = []
    query_lower = query.lower()
    for path in base.rglob("*.md"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if query_lower in text.lower():
            fm = _read_frontmatter(path)
            fm["match_file"] = str(path.relative_to(REPO_ROOT))
            results.append(fm)
    return results


# ── MCP server setup ──────────────────────────────────────────────────────────

if _MCP_AVAILABLE:
    mcp = FastMCP("pcna-vault")

    @mcp.tool()
    def list_structures(validated_only: bool = True, limit: int = 50) -> list[dict]:
        """
        List PCNA structures from the knowledge vault.
        Returns metadata: pdb_id, resolution, chains, relevance, validated.
        """
        if validated_only:
            records = _load_validated()
        else:
            cat     = _load_catalog()
            records = cat.get("all_records", [])

        structs = [r for r in records if r.get("record_type") == "pdb_structure"]
        structs = sorted(structs, key=lambda r: -r.get("relevance", 0))[:limit]

        return [
            {
                "pdb_id"    : r.get("uid", ""),
                "title"     : r.get("title", ""),
                "resolution": r.get("validation", {}).get("l3", {}).get("resolution_angstrom"),
                "chains"    : r.get("validation", {}).get("l3", {}).get("chains", []),
                "relevance" : round(r.get("relevance", 0), 3),
                "validated" : r.get("passed", False),
                "source"    : r.get("source", ""),
                "rcsb_url"  : f"https://www.rcsb.org/structure/{r.get('uid', '')}",
            }
            for r in structs
        ]

    @mcp.tool()
    def get_structure(pdb_id: str) -> dict:
        """
        Get full metadata for a specific PDB structure.
        Includes validation layers, vault note content, download status.
        """
        pdb_id = pdb_id.upper().strip()
        cat    = _load_catalog()
        record = next(
            (r for r in cat.get("all_records", []) if r.get("uid", "").upper() == pdb_id),
            None
        )

        # Vault note
        note_path = VAULT_DIR / "structures" / f"{pdb_id}.md"
        note_content = ""
        if note_path.exists():
            note_content = note_path.read_text(encoding="utf-8")

        # Local file status
        local_pdb = RAW_DIR / f"{pdb_id}.pdb"

        return {
            "pdb_id"         : pdb_id,
            "in_catalog"     : record is not None,
            "catalog_record" : record or {},
            "vault_note"     : note_content[:2000] if note_content else "No vault note found.",
            "local_pdb"      : str(local_pdb) if local_pdb.exists() else None,
            "download_url"   : f"https://files.rcsb.org/download/{pdb_id}.pdb",
        }

    @mcp.tool()
    def search_vault(query: str, category: str = "all") -> list[dict]:
        """
        Search the Obsidian vault knowledge graph by keyword.
        category: 'all' | 'structures' | 'papers' | 'datasets' | 'compounds'
        Returns matching notes with frontmatter metadata and content preview.
        """
        subdir_map = {
            "structures": "structures",
            "papers"    : "papers",
            "datasets"  : "datasets",
            "compounds" : "compounds",
        }
        subdir = subdir_map.get(category)
        results = _search_notes(query, subdir)
        return results[:20]

    @mcp.tool()
    def list_papers(limit: int = 20) -> list[dict]:
        """
        List literature nodes (PubMed, NCBI) from the vault.
        Returns title, source, relevance, URL.
        """
        notes = []
        paper_dir = VAULT_DIR / "papers"
        if not paper_dir.exists():
            return []
        for path in sorted(paper_dir.glob("*.md"))[:limit]:
            fm = _read_frontmatter(path)
            notes.append({
                "title"    : fm.get("title", path.stem),
                "uid"      : fm.get("uid", path.stem),
                "source"   : fm.get("source", ""),
                "relevance": fm.get("relevance", ""),
                "url"      : fm.get("url", ""),
                "file"     : str(path.relative_to(REPO_ROOT)),
            })
        return notes

    @mcp.tool()
    def list_datasets(limit: int = 30) -> list[dict]:
        """
        List dataset nodes (Zenodo, GitHub, ChEMBL) from the vault.
        Returns title, source, download_url, relevance.
        """
        notes = []
        ds_dir = VAULT_DIR / "datasets"
        if not ds_dir.exists():
            return []
        for path in sorted(ds_dir.glob("*.md"))[:limit]:
            fm = _read_frontmatter(path)
            notes.append({
                "title"       : fm.get("title", path.stem),
                "uid"         : fm.get("uid", path.stem),
                "source"      : fm.get("source", ""),
                "relevance"   : fm.get("relevance", ""),
                "download_url": fm.get("download_url", ""),
                "file"        : str(path.relative_to(REPO_ROOT)),
            })
        return notes

    @mcp.tool()
    def get_knowledge_graph() -> dict:
        """
        Return a summary of the full PCNA knowledge graph.
        Includes node counts, validated structures, pipeline status, and key notes.
        """
        struct_count  = len(list((VAULT_DIR / "structures").glob("*.md"))) if (VAULT_DIR / "structures").exists() else 0
        paper_count   = len(list((VAULT_DIR / "papers").glob("*.md")))   if (VAULT_DIR / "papers").exists()   else 0
        dataset_count = len(list((VAULT_DIR / "datasets").glob("*.md"))) if (VAULT_DIR / "datasets").exists() else 0
        compound_count= len(list((VAULT_DIR / "compounds").glob("*.md")))if (VAULT_DIR / "compounds").exists() else 0

        validated = _load_validated()

        kg_note = VAULT_DIR / "KNOWLEDGE_GRAPH.md"
        kg_content = kg_note.read_text(encoding="utf-8") if kg_note.exists() else ""

        return {
            "vault_root"        : str(VAULT_DIR),
            "total_nodes"       : struct_count + paper_count + dataset_count + compound_count,
            "by_type"           : {
                "structures": struct_count,
                "papers"    : paper_count,
                "datasets"  : dataset_count,
                "compounds" : compound_count,
            },
            "validated_pdb_count": len(validated),
            "ground_truth"      : {
                "positive": "8GLA — AOH1996 cryptic pocket OPEN",
                "negative": "1W60 — apo PCNA, pocket absent",
            },
            "knowledge_graph_note": kg_content[:3000],
            "catalog_path"      : str(CATALOG_DIR / "pcna_data_catalog.json"),
        }

    @mcp.tool()
    def run_inference(pdb_id: str, model_size: str = "small") -> dict:
        """
        Run PocketGNN on a local PDB structure and return per-residue scores.
        model_size: 'small' (~907k), 'medium' (~3.6M), 'large' (~10.4M)
        pdb_id must be present in data/raw/ (fetch first with fetch_structures.py).
        Returns top-20 pocket candidates and summary statistics.
        """
        import torch
        from src.models import PocketGNN
        from src.data_processing.parse_pdb import parse_pdb
        from src.data_processing.graph_construction import build_graph_v2

        pdb_path = RAW_DIR / f"{pdb_id.upper()}.pdb"
        if not pdb_path.exists():
            return {"error": f"{pdb_id}.pdb not in data/raw/ — run fetch_structures.py first"}

        try:
            if model_size == "large":
                model = PocketGNN().eval()
                ckpt_path = REPO_ROOT / "checkpoints" / "pcna" / "best_pcna.ckpt"
            elif model_size == "medium":
                model = PocketGNN.medium().eval()
                ckpt_path = REPO_ROOT / "checkpoints" / "pcna" / "best_pcna.ckpt"
            else:
                model = PocketGNN.small().eval()
                ckpt_path = REPO_ROOT / "checkpoints" / "pcna" / "best_pcna.ckpt"

            checkpoint_loaded = False
            if ckpt_path.exists():
                model.load_state_dict(
                    torch.load(str(ckpt_path), map_location="cpu", weights_only=True)
                )
                checkpoint_loaded = True

            residues = parse_pdb(pdb_path)
            data     = build_graph_v2(residues)
            with torch.no_grad():
                scores = model(
                    data.x, data.edge_index, data.edge_attr,
                    data.edge_index_seq, data.edge_attr_seq,
                    data.chain_id,
                ).numpy()

            top_idx = scores.argsort()[::-1][:20]
            top_residues = [
                {
                    "chain": residues[i].chain,
                    "resid": residues[i].resid,
                    "aa"   : residues[i].resname,
                    "score": round(float(scores[i]), 4),
                }
                for i in top_idx
            ]

            note = (
                f"Checkpoint loaded: {ckpt_path.name}. Scores are from a trained prototype model "
                f"using ligand-proximity labels. Treat as preliminary hypotheses, not validated results."
                if checkpoint_loaded else
                f"WARNING: checkpoint not found at {ckpt_path}. Scores are random — train first "
                f"with src/training/train.py."
            )

            return {
                "pdb_id"         : pdb_id.upper(),
                "n_residues"     : len(residues),
                "model_size"     : model_size,
                "model_params"   : model.param_count(),
                "checkpoint_loaded": checkpoint_loaded,
                "mean_score"     : round(float(scores.mean()), 4),
                "max_score"      : round(float(scores.max()), 4),
                "pocket_candidates_above_0.4": int((scores >= 0.4).sum()),
                "top_20_residues": top_residues,
                "note": note,
            }
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def get_pipeline_status() -> dict:
        """
        Return the current implementation status of every pipeline stage.
        """
        def check(path: str) -> str:
            p = REPO_ROOT / path
            if not p.exists():
                return "missing"
            text = p.read_text(encoding="utf-8", errors="ignore")
            if "raise NotImplementedError" in text or "pass\n" == text.strip():
                return "stub"
            if len(text) < 200:
                return "stub"
            return "implemented"

        return {
            "Stage 1 — fetch_structures" : check("src/data_processing/fetch_structures.py"),
            "Stage 2 — parse_pdb"        : check("src/data_processing/parse_pdb.py"),
            "Stage 3 — graph_construction": check("src/data_processing/graph_construction.py"),
            "Model   — PocketGNN v2"     : check("src/models/cryptic_gnn.py"),
            "Training — train.py"        : check("src/training/train.py"),
            "Loss    — focal+rank+sym"   : check("src/training/loss.py"),
            "Dataset — PocketDataset"    : check("src/training/dataset.py"),
            "UI      — Streamlit app"    : check("src/ui/app.py"),
            "MCP     — this server"      : "running",
            "Eval    — score_pockets"    : check("src/evaluation/score_pockets.py"),
            "MD      — parse_trajectory" : check("src/md/parse_trajectory.py"),
            "Crawler — pcna_crawler"     : check("agents/pcna_crawler.py"),
            "Vault   — catalog_to_obsidian": check("agents/catalog_to_obsidian.py"),
        }


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not _MCP_AVAILABLE:
        print("Install mcp first: pip install mcp")
        sys.exit(1)
    mcp.run()
