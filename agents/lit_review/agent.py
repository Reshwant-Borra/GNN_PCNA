#!/usr/bin/env python3
"""
GNN-PCNA Literature Review Agent — Hermes-3 (or any Ollama model) + 8 Academic Databases
Run: python lit_review/agent.py
     python lit_review/agent.py --dry-run          # skip Ollama, use hardcoded queries
     python lit_review/agent.py --model gemma3:4b  # use a specific model
     python lit_review/agent.py --model gpt-oss:20b
"""

import hashlib
import json
import re
import subprocess
import sys
import time

# Force line-buffered stdout so output appears live when piped
sys.stdout.reconfigure(line_buffering=True)
import xml.etree.ElementTree as ET
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import quote_plus

import requests

# ── Config ───────────────────────────────────────────────────────────────────
EMAIL   = "advay.awesomer@gmail.com"
DRY_RUN = "--dry-run" in sys.argv

# Model: --model <name> overrides, else auto-detect best available
_MODEL_FLAG = next((sys.argv[i+1] for i, a in enumerate(sys.argv) if a == "--model" and i+1 < len(sys.argv)), None)

PREFERRED_MODELS = ["hermes3", "gpt-oss:20b", "llama3:latest", "gemma3:4b", "llama3.2:latest"]

def _pick_model() -> str:
    if _MODEL_FLAG:
        return _MODEL_FLAG
    try:
        import ollama as _ol
        resp = _ol.list()
        # SDK returns either list of Model objects or a dict; handle both
        if hasattr(resp, "models"):
            available = {m.model for m in resp.models}
        else:
            available = {m.get("name", m.get("model", "")) for m in (resp or [])}
        for pref in PREFERRED_MODELS:
            if pref in available:
                return pref
        if available:
            picked = next(iter(available))
            return picked
    except Exception:
        pass
    return "hermes3"

MODEL = _pick_model()

SESS: Path = None          # set by _init_sess() — delayed so overnight.py can override
PAPERS: dict[str, dict] = {}   # stable key → paper dict

def _init_sess(base_dir: Path = None) -> Path:
    """Create and return the session directory. Idempotent."""
    global SESS
    if SESS is None:
        base = base_dir or (Path(__file__).parent / "papers")
        SESS = base / f"s_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        SESS.mkdir(parents=True, exist_ok=True)
    return SESS

# ── Deduplication ─────────────────────────────────────────────────────────────
def _key(paper: dict) -> str:
    doi = paper.get("doi", "").strip().lower().replace("https://doi.org/", "")
    if doi:
        return f"doi:{doi}"
    t = paper.get("title", "").lower().strip()
    return f"title:{hashlib.md5(t.encode()).hexdigest()}"

def _add(paper: dict, source: str) -> bool:
    """Return True if paper was new and added."""
    if not paper.get("title"):
        return False
    key = _key(paper)
    if key in PAPERS:
        return False
    # Fuzzy title match — catch same paper with different DOI/no-DOI
    title = paper.get("title", "").lower()
    for ex in PAPERS.values():
        if SequenceMatcher(None, title, ex.get("title","").lower()).ratio() > 0.88:
            return False
    paper["source"] = source
    PAPERS[key] = paper
    return True

def _clean_jats(text: str) -> str:
    """Strip JATS XML tags from CrossRef abstracts."""
    return re.sub(r"<[^>]+>", " ", text or "").strip()

# ── Search tools ─────────────────────────────────────────────────────────────

def search_pubmed(query: str, max_results: int = 40) -> dict:
    """PubMed / NCBI biomedical literature (E-utilities, free)."""
    try:
        r = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db": "pubmed", "term": query, "retmax": max_results,
                    "retmode": "json", "email": EMAIL},
            timeout=15,
        )
        ids = r.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return {"papers": [], "count": 0, "source": "PubMed", "query": query}

        time.sleep(0.35)  # NCBI rate limit: 3 req/s

        r2 = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={"db": "pubmed", "id": ",".join(ids), "rettype": "abstract",
                    "retmode": "xml", "email": EMAIL},
            timeout=30,
        )
        papers, root = [], ET.fromstring(r2.content)
        for art in root.findall(".//PubmedArticle"):
            try:
                pmid  = art.findtext(".//PMID", "")
                doi_el = art.find(".//ArticleId[@IdType='doi']")
                doi   = doi_el.text if doi_el is not None else ""
                title = art.findtext(".//ArticleTitle", "").strip()
                abstract = " ".join(
                    (el.text or "") for el in art.findall(".//AbstractText")
                ).strip()
                year_el = art.find(".//PubDate/Year")
                if year_el is None:
                    year_el = art.find(".//PubDate/MedlineDate")
                year = (year_el.text or "")[:4] if year_el is not None else ""
                authors = [
                    f"{a.findtext('LastName','')} {a.findtext('Initials','')}".strip()
                    for a in art.findall(".//Author")[:6]
                ]
                p = dict(title=title, abstract=abstract, year=year, doi=doi,
                         pmid=pmid, authors=authors,
                         url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
                if _add(p, "PubMed"):
                    papers.append(p)
            except Exception:
                continue
        return {"papers": papers, "count": len(papers), "source": "PubMed", "query": query}
    except Exception as e:
        return {"error": str(e), "papers": [], "count": 0, "source": "PubMed"}


def search_semantic_scholar(query: str, max_results: int = 50) -> dict:
    """Semantic Scholar — AI/ML + bio, returns citationCount and S2 paper IDs."""
    try:
        # Free tier: ~1 req/s; retry with backoff on 429
        for attempt in range(4):
            r = requests.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={
                    "query": query, "limit": min(max_results, 100),
                    "fields": "title,authors,year,abstract,externalIds,"
                              "openAccessPdf,url,citationCount,paperId",
                },
                headers={"User-Agent": f"GNN-PCNA-LitReview/1.0 ({EMAIL})"},
                timeout=20,
            )
            if r.status_code != 429:
                break
            time.sleep(2 ** (attempt + 1))
        else:
            return {"error": "S2 rate limit", "papers": [], "count": 0, "source": "S2"}
        papers = []
        for p in r.json().get("data", []):
            doi = p.get("externalIds", {}).get("DOI", "")
            pmid = p.get("externalIds", {}).get("PubMed", "")
            pdf  = (p.get("openAccessPdf") or {}).get("url", "")
            paper = dict(
                title=p.get("title", ""),
                abstract=p.get("abstract", ""),
                year=str(p.get("year", "")),
                doi=doi, pmid=pmid,
                authors=[a["name"] for a in p.get("authors", [])[:6]],
                url=p.get("url", ""),
                pdf_url=pdf,
                citations=p.get("citationCount", 0),
                s2_id=p.get("paperId", ""),
            )
            if _add(paper, "S2"):
                papers.append(paper)
        time.sleep(1.1)  # S2 free tier: stay under 1 req/s
        return {"papers": papers, "count": len(papers), "source": "S2", "query": query}
    except Exception as e:
        return {"error": str(e), "papers": [], "count": 0, "source": "S2"}


def search_arxiv(query: str, max_results: int = 50) -> dict:
    """arXiv — preprints in cs.LG, q-bio, cs.AI, physics.bio-ph."""
    try:
        r = requests.get(
            "http://export.arxiv.org/api/query",
            params={"search_query": f"all:{query}", "max_results": max_results,
                    "sortBy": "relevance"},
            timeout=20,
        )
        ns   = {"a": "http://www.w3.org/2005/Atom", "ax": "http://arxiv.org/schemas/atom"}
        root = ET.fromstring(r.content)
        papers = []
        for entry in root.findall("a:entry", ns):
            raw_id  = entry.findtext("a:id", "", ns)
            arxiv_id = raw_id.split("/abs/")[-1]
            title   = (entry.findtext("a:title", "", ns) or "").replace("\n", " ").strip()
            abstract= (entry.findtext("a:summary", "", ns) or "").replace("\n", " ").strip()
            year    = (entry.findtext("a:published", "", ns) or "")[:4]
            doi_el  = entry.find("ax:doi", ns)
            doi     = doi_el.text.strip() if doi_el is not None else ""
            authors = [e.findtext("a:name", "", ns) for e in entry.findall("a:author", ns)[:6]]
            p = dict(
                title=title, abstract=abstract, year=year, doi=doi,
                authors=authors,
                url=f"https://arxiv.org/abs/{arxiv_id}",
                pdf_url=f"https://arxiv.org/pdf/{arxiv_id}",
                arxiv_id=arxiv_id,
            )
            if _add(p, "arXiv"):
                papers.append(p)
        return {"papers": papers, "count": len(papers), "source": "arXiv", "query": query}
    except Exception as e:
        return {"error": str(e), "papers": [], "count": 0, "source": "arXiv"}


def search_openalex(query: str, max_results: int = 50) -> dict:
    """OpenAlex — 250 M+ works, best coverage, reconstructs abstracts from inverted index."""
    try:
        r = requests.get(
            "https://api.openalex.org/works",
            params={
                "search": query, "per-page": min(max_results, 200),
                "sort": "relevance_score:desc",
                "select": "id,title,authorships,publication_year,"
                          "abstract_inverted_index,doi,primary_location,"
                          "cited_by_count,open_access",
                "mailto": EMAIL,
            },
            timeout=20,
        )
        papers = []
        for p in r.json().get("results", []):
            title = p.get("title", "") or ""
            doi   = (p.get("doi") or "").replace("https://doi.org/", "")
            year  = str(p.get("publication_year", ""))
            inv   = p.get("abstract_inverted_index") or {}
            if inv:
                try:
                    size  = max(max(v) for v in inv.values()) + 1
                    words = [""] * size
                    for w, pos in inv.items():
                        for i in pos:
                            if i < size:
                                words[i] = w
                    abstract = " ".join(words)
                except Exception:
                    abstract = ""
            else:
                abstract = ""
            authors = [
                a.get("author", {}).get("display_name", "")
                for a in p.get("authorships", [])[:6]
            ]
            loc     = p.get("primary_location") or {}
            url     = loc.get("landing_page_url") or (f"https://doi.org/{doi}" if doi else "")
            pdf_url = (p.get("open_access") or {}).get("oa_url", "") or ""
            paper   = dict(
                title=title, abstract=abstract[:600], year=year, doi=doi,
                authors=[a for a in authors if a],
                url=url, pdf_url=pdf_url,
                citations=p.get("cited_by_count", 0),
            )
            if title and _add(paper, "OpenAlex"):
                papers.append(paper)
        return {"papers": papers, "count": len(papers), "source": "OpenAlex", "query": query}
    except Exception as e:
        return {"error": str(e), "papers": [], "count": 0, "source": "OpenAlex"}


def search_europe_pmc(query: str, max_results: int = 40) -> dict:
    """Europe PMC — European biomedical literature archive."""
    try:
        r = requests.get(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            params={"query": query, "format": "json", "pageSize": max_results,
                    "resultType": "core", "sort": "RELEVANCE"},
            timeout=20,
        )
        papers = []
        for p in r.json().get("resultList", {}).get("result", []):
            doi  = p.get("doi", "")
            pmid = p.get("pmid", "")
            als  = p.get("authorList", {}).get("author", [])
            url  = (f"https://europepmc.org/article/MED/{pmid}" if pmid
                    else f"https://doi.org/{doi}" if doi else "")
            paper = dict(
                title=p.get("title", ""),
                abstract=p.get("abstractText", ""),
                year=str(p.get("pubYear", "")),
                doi=doi, pmid=pmid,
                authors=[f"{a.get('lastName','')} {a.get('initials','')}".strip() for a in als[:6]],
                url=url,
            )
            if _add(paper, "EuropePMC"):
                papers.append(paper)
        return {"papers": papers, "count": len(papers), "source": "EuropePMC", "query": query}
    except Exception as e:
        return {"error": str(e), "papers": [], "count": 0, "source": "EuropePMC"}


def search_biorxiv_preprints(query: str, max_results: int = 30) -> dict:
    """bioRxiv / medRxiv preprints via CrossRef posted-content filter."""
    try:
        r = requests.get(
            "https://api.crossref.org/works",
            params={
                "query": query, "filter": "type:posted-content",
                "rows": max_results, "sort": "relevance",
                "select": "DOI,title,author,published,abstract,URL",
                "mailto": EMAIL,
            },
            timeout=20,
        )
        papers = []
        for p in r.json().get("message", {}).get("items", []):
            doi   = p.get("DOI", "")
            titles = p.get("title", [""])
            title  = titles[0] if titles else ""
            abstract = _clean_jats(p.get("abstract", ""))
            parts  = p.get("published", {}).get("date-parts", [[""]])[0]
            year   = str(parts[0]) if parts else ""
            authors = [f"{a.get('given','')} {a.get('family','')}".strip()
                       for a in p.get("author", [])[:6]]
            pdf = f"https://www.biorxiv.org/content/{doi}.full.pdf" if "10.1101" in doi else ""
            paper = dict(title=title, abstract=abstract, year=year, doi=doi,
                         authors=authors, url=p.get("URL",""), pdf_url=pdf)
            if _add(paper, "bioRxiv"):
                papers.append(paper)
        return {"papers": papers, "count": len(papers), "source": "bioRxiv", "query": query}
    except Exception as e:
        return {"error": str(e), "papers": [], "count": 0, "source": "bioRxiv"}


def search_crossref(query: str, max_results: int = 50) -> dict:
    """CrossRef — comprehensive DOI registry, all publication types."""
    try:
        r = requests.get(
            "https://api.crossref.org/works",
            params={
                "query": query, "rows": max_results, "sort": "relevance",
                "select": "DOI,title,author,published,abstract,URL,"
                          "container-title,is-referenced-by-count",
                "mailto": EMAIL,
            },
            timeout=20,
        )
        papers = []
        for p in r.json().get("message", {}).get("items", []):
            doi    = p.get("DOI", "")
            titles = p.get("title", [""])
            title  = titles[0] if titles else ""
            abstract = _clean_jats(p.get("abstract", ""))
            parts  = p.get("published", {}).get("date-parts", [[""]])[0]
            year   = str(parts[0]) if parts else ""
            authors = [f"{a.get('given','')} {a.get('family','')}".strip()
                       for a in p.get("author", [])[:6]]
            journal = (p.get("container-title") or [""])[0]
            paper   = dict(
                title=title, abstract=abstract, year=year, doi=doi,
                authors=authors, url=p.get("URL",""),
                journal=journal, citations=p.get("is-referenced-by-count", 0),
            )
            if title and _add(paper, "CrossRef"):
                papers.append(paper)
        return {"papers": papers, "count": len(papers), "source": "CrossRef", "query": query}
    except Exception as e:
        return {"error": str(e), "papers": [], "count": 0, "source": "CrossRef"}


def _s2_get(url: str, params: dict) -> requests.Response:
    """GET with S2 rate-limit retry."""
    for attempt in range(4):
        r = requests.get(url, params=params,
                         headers={"User-Agent": f"GNN-PCNA-LitReview/1.0 ({EMAIL})"},
                         timeout=15)
        if r.status_code != 429:
            return r
        time.sleep(2 ** (attempt + 1))
    return r  # return last response (may still be 429)


def get_s2_citations(s2_paper_id: str, max_results: int = 25) -> dict:
    """Follow citation chain — papers that CITE a key Semantic Scholar paper."""
    try:
        r = _s2_get(
            f"https://api.semanticscholar.org/graph/v1/paper/{s2_paper_id}/citations",
            {"fields": "title,authors,year,abstract,externalIds,url,citationCount",
             "limit": max_results},
        )
        papers = []
        for item in r.json().get("data", []):
            p   = item.get("citingPaper", {})
            doi = p.get("externalIds", {}).get("DOI", "")
            paper = dict(
                title=p.get("title", ""),
                abstract=p.get("abstract", ""),
                year=str(p.get("year", "")),
                doi=doi,
                authors=[a["name"] for a in p.get("authors", [])[:6]],
                url=p.get("url", ""),
                citations=p.get("citationCount", 0),
            )
            if _add(paper, "S2-Citing"):
                papers.append(paper)
        time.sleep(1.1)
        return {"papers": papers, "count": len(papers), "source": "S2-Citing"}
    except Exception as e:
        return {"error": str(e), "papers": [], "count": 0}


def get_s2_references(s2_paper_id: str, max_results: int = 30) -> dict:
    """Follow citation chain — papers that a key S2 paper REFERENCES."""
    try:
        r = _s2_get(
            f"https://api.semanticscholar.org/graph/v1/paper/{s2_paper_id}/references",
            {"fields": "title,authors,year,abstract,externalIds,url,citationCount",
             "limit": max_results},
        )
        papers = []
        for item in r.json().get("data", []):
            p   = item.get("citedPaper", {})
            doi = p.get("externalIds", {}).get("DOI", "")
            paper = dict(
                title=p.get("title", ""),
                abstract=p.get("abstract", ""),
                year=str(p.get("year", "")),
                doi=doi,
                authors=[a["name"] for a in p.get("authors", [])[:6]],
                url=p.get("url", ""),
                citations=p.get("citationCount", 0),
            )
            if _add(paper, "S2-Refs"):
                papers.append(paper)
        time.sleep(1.1)
        return {"papers": papers, "count": len(papers), "source": "S2-Refs"}
    except Exception as e:
        return {"error": str(e), "papers": [], "count": 0}


def get_open_access_pdf(doi: str) -> dict:
    """Unpaywall — resolve a DOI to its best open-access PDF URL."""
    try:
        r = requests.get(
            f"https://api.unpaywall.org/v2/{doi}",
            params={"email": EMAIL}, timeout=10,
        )
        d   = r.json()
        loc = d.get("best_oa_location") or {}
        return {
            "doi": doi,
            "is_oa": d.get("is_oa", False),
            "pdf_url": loc.get("url_for_pdf", ""),
            "landing": loc.get("url", ""),
            "host": loc.get("host_type", ""),
        }
    except Exception as e:
        return {"error": str(e), "doi": doi}


def get_paper_stats() -> dict:
    """Return current collection stats — total, by source, year range, coverage."""
    by_src: dict[str, int] = {}
    for p in PAPERS.values():
        by_src[p.get("source", "?")] = by_src.get(p.get("source", "?"), 0) + 1
    years  = [int(p["year"]) for p in PAPERS.values() if str(p.get("year","")).isdigit()]
    return {
        "total": len(PAPERS),
        "by_source": by_src,
        "year_range": [min(years), max(years)] if years else [],
        "with_abstract": sum(1 for p in PAPERS.values() if p.get("abstract")),
        "with_pdf": sum(1 for p in PAPERS.values() if p.get("pdf_url")),
        "with_doi": sum(1 for p in PAPERS.values() if p.get("doi")),
    }


def save_papers() -> dict:
    """Persist all papers to JSON + URL list for NotebookLM."""
    _init_sess()
    lst = sorted(PAPERS.values(), key=lambda p: -(p.get("citations", 0)))

    # Full JSON
    papers_file = SESS / "papers.json"
    papers_file.write_text(
        json.dumps({"session": datetime.now().isoformat(), "total": len(lst), "papers": lst},
                   indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # URL list for NotebookLM (prefer PDF → landing → pub URL)
    urls = []
    for p in lst:
        u = p.get("pdf_url") or p.get("url") or ""
        if u and u.startswith("http"):
            urls.append(u)
    urls = list(dict.fromkeys(urls))  # preserve order, deduplicate

    urls_file = SESS / "urls.txt"
    urls_file.write_text("\n".join(urls[:300]), encoding="utf-8")

    print(f"\n[SAVED] {len(lst)} papers → {papers_file}")
    print(f"[SAVED] {len(urls)} URLs  → {urls_file}")
    return {"papers_file": str(papers_file), "urls_file": str(urls_file),
            "total": len(lst), "urls": len(urls)}


def send_to_notebooklm(notebook_name: str = "") -> dict:
    """Create a NotebookLM notebook, add all paper URLs, request a lit-review report."""
    _init_sess()
    name = notebook_name or f"GNN-PCNA LitReview {datetime.now().strftime('%Y-%m-%d')}"

    lst  = sorted(PAPERS.values(), key=lambda p: -(p.get("citations", 0)))
    urls = []
    for p in lst:
        u = p.get("pdf_url") or p.get("url") or ""
        if u and u.startswith("http"):
            urls.append(u)
    urls = list(dict.fromkeys(urls))[:250]

    tmp = SESS / "nlm_urls.txt"
    tmp.write_text("\n".join(urls), encoding="utf-8")

    nlm = Path.home() / "tools" / "notebooklm" / "notebooklm_skill.py"
    if not nlm.exists():
        return {"success": False, "msg": f"notebooklm script not found at {nlm}",
                "urls_ready": str(tmp), "count": len(urls)}

    try:
        r1 = subprocess.run(
            [sys.executable, str(nlm), "create", "--name", name],
            capture_output=True, text=True, timeout=90,
        )
        nb_id = r1.stdout.strip().split()[-1] if r1.returncode == 0 else None

        if nb_id:
            subprocess.run(
                [sys.executable, str(nlm), "add-sources", "--id", nb_id,
                 "--sources-file", str(tmp)],
                capture_output=True, text=True, timeout=180,
            )
            report_prompt = (
                "Generate a comprehensive structured literature review for the GNN-PCNA project. "
                "This project predicts cryptic binding pockets on PCNA using dual-branch GNN + ESM2 "
                "protein language model embeddings. Structure the review as: "
                "1) PCNA biology and cancer relevance "
                "2) Cryptic binding pockets — discovery and computational prediction "
                "3) Graph neural networks for protein pocket prediction "
                "4) Protein language models for structure/function "
                "5) AOH1996 and PCNA drug discovery "
                "6) Molecular dynamics of cryptic pockets "
                "7) Benchmark datasets and evaluation metrics "
                "8) Key research gaps and future directions. "
                "For each section cite specific papers and highlight key quantitative findings."
            )
            r3 = subprocess.run(
                [sys.executable, str(nlm), "artifact", "--id", nb_id,
                 "--type", "report", "--prompt", report_prompt],
                capture_output=True, text=True, timeout=300,
            )
            return {
                "success": True, "notebook": name, "id": nb_id,
                "sources": len(urls),
                "report_preview": (r3.stdout or "")[:800],
            }
    except Exception as e:
        pass

    return {"success": False, "msg": "NotebookLM call failed — run manually",
            "urls_ready": str(tmp), "count": len(urls)}


# ── Hermes-3 tool schema ──────────────────────────────────────────────────────
TOOLS = [
    {"type": "function", "function": {
        "name": "search_pubmed",
        "description": "Search PubMed biomedical literature database",
        "parameters": {"type": "object", "required": ["query"], "properties": {
            "query":       {"type": "string"},
            "max_results": {"type": "integer", "default": 40},
        }},
    }},
    {"type": "function", "function": {
        "name": "search_semantic_scholar",
        "description": "Search Semantic Scholar — AI/ML + bio, returns citation counts and S2 paper IDs for citation chaining",
        "parameters": {"type": "object", "required": ["query"], "properties": {
            "query":       {"type": "string"},
            "max_results": {"type": "integer", "default": 50},
        }},
    }},
    {"type": "function", "function": {
        "name": "search_arxiv",
        "description": "Search arXiv preprints (cs.LG, q-bio, cs.AI, physics.bio-ph)",
        "parameters": {"type": "object", "required": ["query"], "properties": {
            "query":       {"type": "string"},
            "max_results": {"type": "integer", "default": 50},
        }},
    }},
    {"type": "function", "function": {
        "name": "search_openalex",
        "description": "Search OpenAlex — 250M+ works, best breadth coverage across all fields",
        "parameters": {"type": "object", "required": ["query"], "properties": {
            "query":       {"type": "string"},
            "max_results": {"type": "integer", "default": 50},
        }},
    }},
    {"type": "function", "function": {
        "name": "search_europe_pmc",
        "description": "Search Europe PMC — European biomedical archive",
        "parameters": {"type": "object", "required": ["query"], "properties": {
            "query":       {"type": "string"},
            "max_results": {"type": "integer", "default": 40},
        }},
    }},
    {"type": "function", "function": {
        "name": "search_biorxiv_preprints",
        "description": "Search bioRxiv and medRxiv preprints for cutting-edge unpublished biology",
        "parameters": {"type": "object", "required": ["query"], "properties": {
            "query":       {"type": "string"},
            "max_results": {"type": "integer", "default": 30},
        }},
    }},
    {"type": "function", "function": {
        "name": "search_crossref",
        "description": "Search CrossRef — comprehensive DOI registry, all publication types",
        "parameters": {"type": "object", "required": ["query"], "properties": {
            "query":       {"type": "string"},
            "max_results": {"type": "integer", "default": 50},
        }},
    }},
    {"type": "function", "function": {
        "name": "get_s2_citations",
        "description": "Follow citation chain forward — get papers that CITE a key paper. Use s2_id from search_semantic_scholar results. Best for expanding coverage after finding a foundational paper.",
        "parameters": {"type": "object", "required": ["s2_paper_id"], "properties": {
            "s2_paper_id": {"type": "string", "description": "Semantic Scholar paper ID"},
            "max_results": {"type": "integer", "default": 25},
        }},
    }},
    {"type": "function", "function": {
        "name": "get_s2_references",
        "description": "Follow citation chain backward — get papers referenced BY a key paper. Surfaces the foundational literature.",
        "parameters": {"type": "object", "required": ["s2_paper_id"], "properties": {
            "s2_paper_id": {"type": "string", "description": "Semantic Scholar paper ID"},
            "max_results": {"type": "integer", "default": 30},
        }},
    }},
    {"type": "function", "function": {
        "name": "get_open_access_pdf",
        "description": "Resolve a DOI to its open-access PDF URL via Unpaywall",
        "parameters": {"type": "object", "required": ["doi"], "properties": {
            "doi": {"type": "string"},
        }},
    }},
    {"type": "function", "function": {
        "name": "get_paper_stats",
        "description": "Get statistics on papers collected so far (total, by source, year range)",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "save_papers",
        "description": "Save all collected papers to JSON and generate URL list for NotebookLM. Call when done searching.",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "send_to_notebooklm",
        "description": "Create a NotebookLM notebook with all papers and generate a literature review report. Call LAST after save_papers.",
        "parameters": {"type": "object", "properties": {
            "notebook_name": {"type": "string", "description": "Optional notebook name"},
        }},
    }},
]

TOOL_MAP = {
    "search_pubmed":            search_pubmed,
    "search_semantic_scholar":  search_semantic_scholar,
    "search_arxiv":             search_arxiv,
    "search_openalex":          search_openalex,
    "search_europe_pmc":        search_europe_pmc,
    "search_biorxiv_preprints": search_biorxiv_preprints,
    "search_crossref":          search_crossref,
    "get_s2_citations":         get_s2_citations,
    "get_s2_references":        get_s2_references,
    "get_open_access_pdf":      get_open_access_pdf,
    "get_paper_stats":          get_paper_stats,
    "save_papers":              save_papers,
    "send_to_notebooklm":       send_to_notebooklm,
}

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM = """You are a world-class computational biology literature review agent with deep expertise in structural bioinformatics, machine learning, and drug discovery. Your mission: perform an EXHAUSTIVE literature review for the GNN-PCNA cryptic pocket prediction project.

PROJECT CONTEXT:
- Goal: Predict cryptic binding pockets on PCNA (Proliferating Cell Nuclear Antigen) using dual-branch GNN + ESM2 protein language model embeddings
- Architecture: GATv2Conv graph attention + ESM2 (facebook/esm2_t12_35M_UR50D), 40 hand-crafted + 480 ESM2 per-residue features, virtual node, ~13.4M params (V3)
- Drug target: AOH1996 bound at PCNA A-B subunit interface (PDB: 8GLA, 24 ground-truth residues within 6Å of ZQZ)
- Apo baseline: PDB 1W60. Training on 59 PCNA structures, CryptoSite 87-protein benchmark
- Performance: held-out AUROC 0.8081, AUPRC 0.3441, 6.2x lift over trivial baseline
- ANM: apo fold-change 0.857, holo 1.157, delta +0.300; holo DCCM 0.2093 vs apo 0.0995
- MD: 100ns NPT, CHARMM36m+TIP3P, OpenMM 8.1, NVIDIA L4 GPU

RESEARCH STRATEGY — MANDATORY EXECUTION ORDER:

Phase 1 — Core biology (run ALL of these):
1. "PCNA proliferating cell nuclear antigen structure function"
2. "PCNA overexpression cancer breast colorectal lung"
3. "PCNA inhibitor anticancer drug discovery"
4. "AOH1996 PCNA cancer drug"
5. "PCNA trimer interface allosteric pocket"

Phase 2 — Cryptic pockets (run ALL):
6. "cryptic binding pocket drug discovery hidden site"
7. "cryptic pocket computational prediction machine learning"
8. "cryptic pocket molecular dynamics simulation transient"
9. "CryptoSite benchmark cryptic pocket dataset"
10. "allosteric pocket cancer target structure-based"

Phase 3 — GNNs for proteins (run ALL):
11. "graph neural network protein pocket prediction binding site"
12. "GATv2 graph attention network molecular structure"
13. "GNN drug discovery binding site prediction"
14. "message passing neural network protein structure"
15. "geometric deep learning protein function"

Phase 4 — Protein language models (run ALL):
16. "ESM2 protein language model structure prediction"
17. "ProtTrans protein embeddings drug target prediction"
18. "protein language model binding site pocket"
19. "transfer learning protein structure function"

Phase 5 — MD and flexibility (run ALL):
20. "normal mode analysis ANM protein flexibility"
21. "molecular dynamics cryptic pocket conformational change"
22. "RMSF protein flexibility pocket opening"
23. "metadynamics enhanced sampling cryptic pocket"
24. "DCCM dynamic cross-correlation protein allosteric"

Phase 6 — Pocket detection methods (run ALL):
25. "fpocket sitemap volsurf protein cavity detection"
26. "DBSCAN clustering protein pocket residues"
27. "deep learning protein binding site geometry"

CITATION CHAINING: When search_semantic_scholar returns a paper with >300 citations, immediately call get_s2_citations() and get_s2_references() on its s2_id. This is how you uncover the field's most important work.

TOOL SELECTION PER QUERY: For each query above, use at least 2 different databases. Distribute across: pubmed, semantic_scholar, arxiv, openalex, europe_pmc, biorxiv_preprints, crossref.

TERMINATION: After completing all 27 queries + citation chaining on top papers, call get_paper_stats() to verify >200 unique papers, then save_papers(), then send_to_notebooklm().

Be systematic. Be exhaustive. The paper depends on this."""

# ── Exhaustive query list (no LLM needed — all 27 topics × 2 databases) ──────
DRY_RUN_QUERIES = [
    # ── Phase 1: PCNA biology ────────────────────────────────────────────────
    ("search_pubmed",            {"query": "PCNA proliferating cell nuclear antigen structure function", "max_results": 40}),
    ("search_openalex",          {"query": "PCNA proliferating cell nuclear antigen structure function", "max_results": 40}),
    ("search_pubmed",            {"query": "PCNA overexpression cancer breast colorectal lung prognosis", "max_results": 40}),
    ("search_europe_pmc",        {"query": "PCNA cancer biomarker overexpression tumor", "max_results": 40}),
    ("search_pubmed",            {"query": "PCNA inhibitor anticancer drug discovery small molecule", "max_results": 40}),
    ("search_crossref",          {"query": "PCNA inhibitor small molecule cancer therapy", "max_results": 40}),
    ("search_pubmed",            {"query": "AOH1996 PCNA cancer drug compound", "max_results": 30}),
    ("search_openalex",          {"query": "AOH1996 PCNA anticancer trimer interface", "max_results": 30}),
    ("search_pubmed",            {"query": "PCNA trimer interface allosteric regulation DNA replication", "max_results": 30}),
    ("search_europe_pmc",        {"query": "PCNA interdomain connecting loop allosteric pocket", "max_results": 30}),
    # ── Phase 2: Cryptic pockets ─────────────────────────────────────────────
    ("search_openalex",          {"query": "cryptic binding pocket hidden site drug discovery", "max_results": 50}),
    ("search_pubmed",            {"query": "cryptic pocket protein drug discovery hidden binding site", "max_results": 40}),
    ("search_openalex",          {"query": "cryptic pocket computational prediction machine learning", "max_results": 50}),
    ("search_crossref",          {"query": "cryptic pocket computational prediction deep learning", "max_results": 40}),
    ("search_pubmed",            {"query": "cryptic pocket molecular dynamics simulation transient", "max_results": 40}),
    ("search_openalex",          {"query": "cryptic pocket molecular dynamics conformational sampling", "max_results": 40}),
    ("search_pubmed",            {"query": "CryptoSite benchmark cryptic pocket dataset evaluation", "max_results": 30}),
    ("search_crossref",          {"query": "CryptoSite allosteric pocket benchmark protein", "max_results": 30}),
    ("search_openalex",          {"query": "allosteric pocket cancer target structure-based drug design", "max_results": 40}),
    ("search_europe_pmc",        {"query": "allosteric binding site protein conformational change", "max_results": 40}),
    # ── Phase 3: GNNs for proteins ───────────────────────────────────────────
    ("search_openalex",          {"query": "graph neural network protein binding site pocket prediction", "max_results": 50}),
    ("search_crossref",          {"query": "graph neural network binding site prediction drug discovery", "max_results": 40}),
    ("search_arxiv",             {"query": "GATv2 graph attention network protein structure", "max_results": 40}),
    ("search_openalex",          {"query": "GATv2 graph attention network molecular property prediction", "max_results": 40}),
    ("search_arxiv",             {"query": "GNN drug discovery binding site prediction molecular graph", "max_results": 40}),
    ("search_crossref",          {"query": "message passing neural network protein pocket", "max_results": 40}),
    ("search_arxiv",             {"query": "geometric deep learning protein structure function", "max_results": 40}),
    ("search_openalex",          {"query": "geometric deep learning equivariant protein structure", "max_results": 40}),
    # ── Phase 4: Protein language models ─────────────────────────────────────
    ("search_arxiv",             {"query": "ESM2 protein language model structure prediction embeddings", "max_results": 40}),
    ("search_openalex",          {"query": "ESM2 protein language model pocket drug target", "max_results": 40}),
    ("search_arxiv",             {"query": "ProtTrans protein language model binding site function", "max_results": 40}),
    ("search_crossref",          {"query": "protein language model transfer learning drug target prediction", "max_results": 40}),
    ("search_biorxiv_preprints", {"query": "protein language model binding site pocket prediction", "max_results": 30}),
    ("search_arxiv",             {"query": "protein transformer embeddings structure representation", "max_results": 40}),
    # ── Phase 5: MD and flexibility ──────────────────────────────────────────
    ("search_pubmed",            {"query": "normal mode analysis ANM protein flexibility pocket", "max_results": 40}),
    ("search_openalex",          {"query": "anisotropic network model protein dynamics flexibility", "max_results": 40}),
    ("search_pubmed",            {"query": "molecular dynamics cryptic pocket conformational change cancer", "max_results": 40}),
    ("search_europe_pmc",        {"query": "molecular dynamics protein pocket opening transient cavity", "max_results": 40}),
    ("search_pubmed",            {"query": "RMSF protein flexibility binding site dynamic", "max_results": 30}),
    ("search_crossref",          {"query": "metadynamics enhanced sampling cryptic pocket", "max_results": 30}),
    ("search_openalex",          {"query": "dynamic cross-correlation DCCM protein allosteric signal", "max_results": 30}),
    # ── Phase 6: Pocket detection algorithms ─────────────────────────────────
    ("search_openalex",          {"query": "fpocket sitemap volsurf protein cavity detection algorithm", "max_results": 40}),
    ("search_crossref",          {"query": "deep learning protein binding site geometry detection", "max_results": 40}),
    ("search_openalex",          {"query": "DBSCAN clustering protein pocket residue detection", "max_results": 30}),
    ("search_europe_pmc",        {"query": "protein pocket detection geometry deep learning druggability", "max_results": 30}),
    # ── Phase 7: preprints sweep ─────────────────────────────────────────────
    ("search_biorxiv_preprints", {"query": "PCNA inhibitor anticancer AOH1996 pocket drug", "max_results": 30}),
    ("search_biorxiv_preprints", {"query": "graph neural network protein pocket cryptic binding", "max_results": 30}),
    ("search_biorxiv_preprints", {"query": "ESM2 protein language model drug target binding site", "max_results": 30}),
    ("search_biorxiv_preprints", {"query": "molecular dynamics cryptic pocket cancer target", "max_results": 30}),
]

# ── Agent loop ────────────────────────────────────────────────────────────────

def run_dry_run() -> None:
    _init_sess()
    print("[DRY-RUN] Executing hardcoded queries without Ollama...\n")
    for name, args in DRY_RUN_QUERIES:
        print(f"  -> {name}({args['query'][:60]}...)")
        result = TOOL_MAP[name](**args)
        print(f"    found {result.get('count', 0)} new papers "
              f"(total: {len(PAPERS)})")
        time.sleep(0.5)

    # Citation chain on high-citation S2 results
    top = sorted(
        [p for p in PAPERS.values() if p.get("s2_id") and p.get("citations", 0) > 100],
        key=lambda p: -p.get("citations", 0),
    )[:3]
    for p in top:
        print(f"  -> citation chain: {p['title'][:60]}  ({p['citations']} cites)")
        get_s2_citations(p["s2_id"], 20)
        get_s2_references(p["s2_id"], 20)
        time.sleep(0.3)

    stats = get_paper_stats()
    print(f"\n[STATS] {stats}")
    save_result = save_papers()
    print(f"\n[DONE] Saved {save_result['total']} papers")
    print(f"       URLs → {save_result['urls_file']}")
    print("\nRun NotebookLM manually:")
    print(f"  python ~/tools/notebooklm/notebooklm_skill.py pipeline "
          f"--sources-file {save_result['urls_file']} --name 'GNN-PCNA LitReview'")


def run_hermes_agent() -> None:
    try:
        import ollama as _ollama
    except ImportError:
        print("[ERROR] pip install ollama")
        sys.exit(1)

    _init_sess()
    print(f"[AGENT] GNN-PCNA Literature Review Agent")
    print(f"[AGENT] Model: {MODEL}  |  Session: {SESS}")
    if MODEL != "hermes3":
        print(f"[NOTE]  hermes3 not found — using {MODEL}. Pull hermes3 for best tool-use quality.")
    print()

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user",   "content":
            "Begin the literature review. Execute the complete search strategy from the system prompt. "
            "Search all 27 query clusters, perform citation chaining on high-impact papers, "
            "then save and push to NotebookLM. Report your progress after each phase."},
    ]

    max_iterations = 80
    for i in range(max_iterations):
        try:
            response = _ollama.chat(model=MODEL, messages=messages, tools=TOOLS)
        except Exception as e:
            print(f"[ERROR] Ollama call failed: {e}")
            print("       Is Ollama running? Try: ollama serve")
            print(f"       Is hermes3 pulled? Try: ollama pull hermes3")
            sys.exit(1)

        msg = response.message

        if not msg.tool_calls:
            # Agent is done or stuck
            print(f"\n[AGENT] Final response:\n{msg.content}\n")
            if len(PAPERS) < 50:
                print("[WARN] < 50 papers found — agent may have stopped early")
            break

        messages.append(msg)

        for tc in msg.tool_calls:
            fn   = tc.function.name
            args = tc.function.arguments if isinstance(tc.function.arguments, dict) else {}

            print(f"[{i+1:02d}] {fn}({', '.join(f'{k}={repr(v)[:40]}' for k,v in args.items())})")

            if fn not in TOOL_MAP:
                result = {"error": f"unknown tool: {fn}"}
            else:
                result = TOOL_MAP[fn](**args)

            count = result.get("count", "")
            total = len(PAPERS)
            suffix = f"  +{count} new | total={total}" if isinstance(count, int) else ""
            print(f"      {suffix}")

            messages.append({"role": "tool", "content": json.dumps(result, ensure_ascii=False)})

    else:
        print(f"[WARN] Hit iteration limit ({max_iterations}). Saving what we have.")
        save_papers()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if DRY_RUN:
        run_dry_run()
    else:
        run_hermes_agent()
