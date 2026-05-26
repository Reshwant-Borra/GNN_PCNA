"""External-web tools for autonomous agents — opt-in via RESEARCHOS_ENABLE_WEB=1.

These tools are stdlib-only (no requests, no aiohttp) so they don't add
dependencies. They wrap PubMed E-utilities, the arXiv export API, and a
generic ``web_fetch`` for grabbing a URL's text.

Falls-back-everywhere: if a request fails, the tool returns
``{"ok": False, "error": "..."}`` rather than raising. The autonomous loop
treats this as a step failure and either retries with a different query or
falls back to deterministic behavior.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional
from xml.etree import ElementTree as ET

from research_os.tools.registry import Tool, ToolRegistry


_WEB_ENV = "RESEARCHOS_ENABLE_WEB"
_USER_AGENT = "ResearchOS/0.1 (autonomous-agent)"
_DEFAULT_TIMEOUT = 15.0

_PUBMED_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
_PUBMED_ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
_PUBMED_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
_ARXIV_API = "http://export.arxiv.org/api/query"


def _fetch(url: str, *, timeout: float = _DEFAULT_TIMEOUT) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


# ---------------------------------------------------------------------------
# Generic fetch
# ---------------------------------------------------------------------------

def _web_fetch(*, url: str, max_bytes: int = 200_000, timeout: float = _DEFAULT_TIMEOUT) -> Dict[str, Any]:
    if not (url.startswith("http://") or url.startswith("https://")):
        return {"ok": False, "url": url, "error": "url must start with http:// or https://"}
    try:
        body = _fetch(url, timeout=timeout)
    except urllib.error.HTTPError as e:
        return {"ok": False, "url": url, "error": f"HTTP {e.code}: {e.reason}"}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"ok": False, "url": url, "error": f"{type(e).__name__}: {e}"}
    truncated = len(body) > max_bytes
    body = body[:max_bytes]
    try:
        text = body.decode("utf-8", errors="replace")
    except Exception:
        text = ""
    return {
        "ok": True,
        "url": url,
        "size_bytes": len(body),
        "truncated": truncated,
        "text": text,
    }


# ---------------------------------------------------------------------------
# PubMed
# ---------------------------------------------------------------------------

def _pubmed_search(*, query: str, retmax: int = 10) -> Dict[str, Any]:
    params = urllib.parse.urlencode({
        "db": "pubmed",
        "term": query,
        "retmax": retmax,
        "retmode": "json",
    })
    url = f"{_PUBMED_ESEARCH}?{params}"
    try:
        raw = _fetch(url)
        data = json.loads(raw)
        ids = data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        return {"ok": False, "source": "pubmed", "query": query, "error": str(e)}
    if not ids:
        return {"ok": True, "source": "pubmed", "query": query, "count": 0, "results": []}

    # Fetch summaries.
    sum_url = f"{_PUBMED_ESUMMARY}?" + urllib.parse.urlencode({
        "db": "pubmed", "id": ",".join(ids), "retmode": "json",
    })
    results: List[Dict[str, Any]] = []
    try:
        sraw = _fetch(sum_url)
        sdata = json.loads(sraw).get("result", {})
        for pmid in ids:
            entry = sdata.get(pmid)
            if not entry:
                continue
            authors = [a.get("name", "") for a in entry.get("authors", []) if isinstance(a, dict)]
            results.append({
                "id": pmid,
                "source": "pubmed",
                "title": entry.get("title", ""),
                "authors": authors[:8],
                "year": (entry.get("pubdate") or "")[:4],
                "journal": entry.get("fulljournalname") or entry.get("source", ""),
                "doi": next(
                    (a.get("value", "")
                     for a in entry.get("articleids", [])
                     if isinstance(a, dict) and a.get("idtype") == "doi"),
                    "",
                ),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            })
    except Exception as e:
        return {"ok": False, "source": "pubmed", "query": query,
                "error": f"summary fetch failed: {e}"}
    return {"ok": True, "source": "pubmed", "query": query,
            "count": len(results), "results": results}


def _pubmed_abstract(*, pmid: str) -> Dict[str, Any]:
    params = urllib.parse.urlencode({
        "db": "pubmed", "id": pmid, "rettype": "abstract", "retmode": "text",
    })
    url = f"{_PUBMED_EFETCH}?{params}"
    try:
        text = _fetch(url).decode("utf-8", errors="replace")
    except Exception as e:
        return {"ok": False, "id": pmid, "error": str(e)}
    return {"ok": True, "id": pmid, "abstract": text}


# ---------------------------------------------------------------------------
# arXiv
# ---------------------------------------------------------------------------

_ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}


def _arxiv_search(*, query: str, max_results: int = 10) -> Dict[str, Any]:
    params = urllib.parse.urlencode({
        "search_query": query,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    })
    url = f"{_ARXIV_API}?{params}"
    try:
        raw = _fetch(url)
        root = ET.fromstring(raw)
    except Exception as e:
        return {"ok": False, "source": "arxiv", "query": query, "error": str(e)}

    results: List[Dict[str, Any]] = []
    for entry in root.findall("a:entry", _ATOM_NS):
        def _text(tag: str) -> str:
            el = entry.find(f"a:{tag}", _ATOM_NS)
            return (el.text or "").strip() if el is not None else ""

        title = _text("title").replace("\n", " ").strip()
        summary = _text("summary").strip()
        published = _text("published")[:10]
        link_el = entry.find("a:id", _ATOM_NS)
        aid = (link_el.text or "").strip() if link_el is not None else ""
        # arxiv id like http://arxiv.org/abs/2403.12345v1 — strip version
        m = re.search(r"abs/([\w.\-/]+?)(v\d+)?$", aid)
        arxiv_id = m.group(1) if m else aid
        authors = []
        for a in entry.findall("a:author/a:name", _ATOM_NS):
            if a.text:
                authors.append(a.text.strip())
        results.append({
            "id": arxiv_id,
            "source": "arxiv",
            "title": title,
            "authors": authors[:8],
            "year": published[:4],
            "summary": summary[:2000],
            "url": f"https://arxiv.org/abs/{arxiv_id}",
        })
    return {"ok": True, "source": "arxiv", "query": query,
            "count": len(results), "results": results}


# ---------------------------------------------------------------------------
# Unified search
# ---------------------------------------------------------------------------

def _web_search(*, query: str, source: str = "pubmed", limit: int = 10) -> Dict[str, Any]:
    src = source.lower()
    if src == "pubmed":
        return _pubmed_search(query=query, retmax=limit)
    if src == "arxiv":
        return _arxiv_search(query=query, max_results=limit)
    return {"ok": False, "query": query, "source": source,
            "error": f"unknown source: {source} (use 'pubmed' or 'arxiv')"}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_web(registry: ToolRegistry) -> None:
    """Register web tools. All are gated by RESEARCHOS_ENABLE_WEB=1."""
    registry.register_many([
        Tool(
            name="web_fetch",
            description="Fetch a URL (HTTP/HTTPS). Returns text, truncated to max_bytes.",
            runner=_web_fetch,
            inputs_schema={"url": "str", "max_bytes": "int?", "timeout": "float?"},
            outputs_schema={"ok": "bool", "text": "str", "size_bytes": "int"},
            requires_env=_WEB_ENV,
            side_effect_class="external",
            category="web",
        ),
        Tool(
            name="web_search",
            description="Search PubMed or arXiv for a query. Returns title/authors/year/url per hit.",
            runner=_web_search,
            inputs_schema={"query": "str", "source": "str (pubmed|arxiv)", "limit": "int?"},
            outputs_schema={"ok": "bool", "count": "int", "results": "list[dict]"},
            requires_env=_WEB_ENV,
            side_effect_class="external",
            category="web",
        ),
        Tool(
            name="pubmed_abstract",
            description="Fetch the abstract text for a given PubMed ID.",
            runner=_pubmed_abstract,
            inputs_schema={"pmid": "str"},
            outputs_schema={"ok": "bool", "abstract": "str"},
            requires_env=_WEB_ENV,
            side_effect_class="external",
            category="web",
        ),
    ])


def web_enabled() -> bool:
    return os.environ.get(_WEB_ENV, "").strip() in ("1", "true", "True", "yes", "on")


__all__ = ["register_web", "web_enabled"]
