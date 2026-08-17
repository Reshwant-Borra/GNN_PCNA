"""Legal open-access discovery.

OpenAlex is the primary source: free, no key, ~250M works, and it exposes the
best open-access PDF location per work. We query the project's domain, keep only
works with an OA full-text location, and yield normalized records. Unpaywall is
used to resolve OA PDFs for DOIs that OpenAlex did not already resolve.

Politeness: requests join OpenAlex's "polite pool" via a mailto, and a per-host
rate limiter (in download_manager) governs the actual file fetches.
"""
from __future__ import annotations

import time
import urllib.parse
import urllib.request
import json
from dataclasses import dataclass, field
from typing import Iterator, List, Optional

from paper_engine import config

OPENALEX = "https://api.openalex.org/works"
UNPAYWALL = "https://api.unpaywall.org/v2/"

# Domain queries that define the corpus scope. Each becomes an OpenAlex search.
DEFAULT_TOPIC_QUERIES: List[str] = [
    "PCNA proliferating cell nuclear antigen",
    "cryptic pocket protein cryptic site",
    "graph neural network protein structure",
    "protein language model ESM residue embedding",
    "molecular dynamics cryptic pocket opening",
    "allosteric site prediction protein",
    "ligand binding site prediction structure",
    "cancer protein-protein interaction inhibitor undruggable",
    "AlphaFold protein structure prediction",
    "drug discovery structure-based virtual screening",
]


@dataclass
class WorkRecord:
    source: str
    work_id: str
    title: str
    doi: str = ""
    year: Optional[int] = None
    authors: List[str] = field(default_factory=list)
    oa_pdf_url: str = ""
    oa_status: str = ""
    host: str = ""
    license: str = ""

    def dedup_key(self) -> str:
        if self.doi:
            return f"doi:{self.doi.lower()}"
        return f"title:{self.title.strip().lower()[:120]}"


def _get_json(url: str, timeout: int = 30, retries: int = 3) -> Optional[dict]:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "paper_engine/0.1 (mailto:%s)" % _mailto()})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return None


def _mailto() -> str:
    import os
    return os.environ.get("PAPER_ENGINE_MAILTO", "advay.awesomer@gmail.com")


def _host_of(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc
    except Exception:
        return ""


# Hosts that reliably allow direct PDF download (vs publisher domains that 403).
RELIABLE_HOSTS = (
    "arxiv.org", "biorxiv.org", "medrxiv.org", "ncbi.nlm.nih.gov", "europepmc.org",
    "ebi.ac.uk", "mdpi.com", "plos.org", "frontiersin.org", "preprints.org",
    "researchsquare.com", "chemrxiv.org", "pmc.ncbi.nlm.nih.gov", "ssrn.com",
)
# Publisher hosts that commonly block hot-linked PDF fetches.
BLOCKED_HOSTS = (
    "wiley.com", "sciencedirect.com", "springer.com", "pnas.org", "cell.com",
    "tandfonline.com", "sagepub.com", "oup.com", "acs.org",
)


def _host_score(url: str) -> int:
    host = _host_of(url).lower()
    if any(h in host for h in RELIABLE_HOSTS):
        return 2
    if any(h in host for h in BLOCKED_HOSTS):
        return 0
    return 1


def _pdf_candidates(work: dict) -> List[str]:
    """All OA PDF URLs across locations, plus a constructed arXiv URL if present."""
    urls: List[str] = []
    for loc in ([work.get("best_oa_location"), work.get("primary_location")]
                + list(work.get("locations", []) or [])):
        if loc and loc.get("is_oa") is not False:
            pdf = (loc or {}).get("pdf_url")
            if pdf:
                urls.append(pdf)
    oa = work.get("open_access", {}) or {}
    if (oa.get("oa_url") or "").endswith(".pdf"):
        urls.append(oa["oa_url"])
    # Construct a direct arXiv PDF URL from the arXiv id if available.
    ids = work.get("ids", {}) or {}
    for loc in list(work.get("locations", []) or []):
        landing = (loc or {}).get("landing_page_url", "") or ""
        if "arxiv.org/abs/" in landing:
            arxiv_id = landing.split("arxiv.org/abs/")[-1].split("v")[0]
            urls.append(f"https://arxiv.org/pdf/{arxiv_id}")
    # Dedup preserving order, then sort by host reliability (stable).
    seen, uniq = set(), []
    for u in urls:
        if u and u not in seen:
            seen.add(u)
            uniq.append(u)
    return sorted(uniq, key=_host_score, reverse=True)


def _normalize_openalex(work: dict) -> Optional[WorkRecord]:
    candidates = _pdf_candidates(work)
    if not candidates:
        return None  # keep only works with a direct OA PDF
    pdf = candidates[0]
    best = work.get("best_oa_location") or work.get("primary_location") or {}
    oa = work.get("open_access", {}) or {}
    authors = []
    for a in work.get("authorships", [])[:12]:
        name = (a.get("author") or {}).get("display_name")
        if name:
            authors.append(name)
    doi = (work.get("doi") or "").replace("https://doi.org/", "")
    return WorkRecord(
        source="openalex",
        work_id=work.get("id", "").rsplit("/", 1)[-1],
        title=work.get("title") or work.get("display_name") or "",
        doi=doi, year=work.get("publication_year"), authors=authors,
        oa_pdf_url=pdf, oa_status=oa.get("oa_status", ""),
        host=_host_of(pdf), license=(best or {}).get("license", "") or "",
    )


def openalex_search(query: str, *, max_records: int = 500, per_page: int = 200,
                    from_year: Optional[int] = 1990) -> Iterator[WorkRecord]:
    """Yield OA WorkRecords for a query via cursor pagination."""
    cursor = "*"
    fetched = 0
    while cursor and fetched < max_records:
        params = {
            "search": query,
            "filter": "is_oa:true" + (f",from_publication_date:{from_year}-01-01" if from_year else ""),
            "per-page": str(min(per_page, max_records - fetched)),
            "cursor": cursor,
            "mailto": _mailto(),
            "select": "id,title,display_name,doi,publication_year,authorships,"
                      "open_access,best_oa_location,primary_location,locations,ids",
        }
        url = OPENALEX + "?" + urllib.parse.urlencode(params)
        data = _get_json(url)
        if not data:
            break
        results = data.get("results", [])
        if not results:
            break
        for work in results:
            rec = _normalize_openalex(work)
            if rec and rec.oa_pdf_url:
                yield rec
        fetched += len(results)
        cursor = (data.get("meta") or {}).get("next_cursor")
        time.sleep(0.2)  # be polite


def discover(queries: Optional[List[str]] = None, *, per_query: int = 300) -> List[WorkRecord]:
    """Run all topic queries and return a deduplicated list of OA works."""
    queries = queries or DEFAULT_TOPIC_QUERIES
    seen = set()
    out: List[WorkRecord] = []
    for q in queries:
        for rec in openalex_search(q, max_records=per_query):
            key = rec.dedup_key()
            if key in seen:
                continue
            seen.add(key)
            out.append(rec)
    return out


def unpaywall_pdf(doi: str) -> Optional[str]:
    """Resolve an OA PDF URL for a DOI via Unpaywall (legal OA only)."""
    if not doi:
        return None
    url = f"{UNPAYWALL}{urllib.parse.quote(doi)}?email={_mailto()}"
    data = _get_json(url)
    if not data:
        return None
    loc = data.get("best_oa_location") or {}
    return loc.get("url_for_pdf") or None
