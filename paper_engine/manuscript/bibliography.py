"""Reference handling — real citations only.

Loads the project's curated literature metadata (313 real papers with DOIs),
selects a domain-relevant shortlist, and exposes it to the writer as a numbered
list the writer may cite as ``[n]`` — and ONLY from this list (no invented
citations). After drafting, :func:`finalize_citations` keeps only the references
actually cited and renumbers them sequentially.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from paper_engine import config

_SEED_CANDIDATES = (
    "data/raw_intake/literature_metadata/seed_relevant_papers.json",
)

_RELEVANCE_TERMS = [
    "pcna", "cryptic pocket", "cryptic site", "graph neural", "gnn", "esm",
    "molecular dynamics", "allosteric", "binding site", "druggab", "cancer",
    "residue", "proliferating cell nuclear", "protein language model",
    "pocket prediction", "structure-based",
]


@dataclass
class Reference:
    idx: int
    title: str
    authors: List[str]
    year: Optional[int]
    doi: str = ""
    url: str = ""
    citations: int = 0

    def author_str(self) -> str:
        if not self.authors:
            return "Anonymous"
        if len(self.authors) == 1:
            return self.authors[0]
        if len(self.authors) <= 3:
            return ", ".join(self.authors)
        return f"{self.authors[0]} et al."

    def formatted(self) -> str:
        year = f"({self.year})" if self.year else ""
        doi = f" doi:{self.doi}" if self.doi else ""
        title = self.title.rstrip(".")
        return f"{self.author_str()} {year}. {title}.{doi}".strip()


def _clean_title(title: str) -> str:
    """Strip HTML markup (e.g. <i>) and collapse whitespace from a title."""
    title = re.sub(r"<[^>]+>", "", title)
    return re.sub(r"\s+", " ", title).strip()


def _load_raw() -> List[dict]:
    path = config.find_data_file(*_SEED_CANDIDATES)
    if path is None:
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(data, dict):
        for key in ("papers", "entries", "seed_papers"):
            if key in data and isinstance(data[key], list):
                data = data[key]
                break
    return data if isinstance(data, list) else []


def _score(item: dict) -> float:
    text = (str(item.get("title", "")) + " " + str(item.get("abstract", ""))).lower()
    hits = sum(1 for t in _RELEVANCE_TERMS if t in text)
    cites = item.get("citations") or 0
    try:
        cites = int(cites)
    except Exception:
        cites = 0
    return hits * 3.0 + math.log10(cites + 1)


def load_references(limit: int = 22) -> List[Reference]:
    """Domain-relevant shortlist of real references, ranked by relevance+impact."""
    raw = _load_raw()
    scored = sorted(raw, key=_score, reverse=True)
    refs: List[Reference] = []
    seen_titles = set()
    for item in scored:
        title = _clean_title(str(item.get("title", "")))
        if not title or title.lower() in seen_titles:
            continue
        seen_titles.add(title.lower())
        authors = item.get("authors") or []
        if isinstance(authors, str):
            authors = [authors]
        year = item.get("year")
        try:
            year = int(year) if year else None
        except Exception:
            year = None
        refs.append(Reference(
            idx=len(refs) + 1, title=title, authors=list(authors), year=year,
            doi=str(item.get("doi", "") or ""), url=str(item.get("url", "") or ""),
            citations=int(item.get("citations") or 0),
        ))
        if len(refs) >= limit:
            break
    return refs


def to_prompt_block(refs: List[Reference]) -> str:
    if not refs:
        return "(No reference list available — do not cite anything.)"
    lines = ["Cite ONLY these, by [n]. Do not invent any other citation:"]
    for r in refs:
        lines.append(f"[{r.idx}] {r.author_str()} ({r.year or 'n.d.'}). {r.title}")
    return "\n".join(lines)


def finalize_citations(full_text: str, refs: List[Reference]) -> Tuple[Dict[int, int], List[Reference]]:
    """Find which [n] are actually used, renumber them 1..k in first-use order.

    Returns (old_idx -> new_idx map, ordered list of used references renumbered).
    """
    used_order: List[int] = []
    for m in re.finditer(r"\[(\d+)\]", full_text):
        n = int(m.group(1))
        if n not in used_order and any(r.idx == n for r in refs):
            used_order.append(n)
    remap = {old: new for new, old in enumerate(used_order, start=1)}
    by_idx = {r.idx: r for r in refs}
    used_refs = []
    for old in used_order:
        r = by_idx[old]
        used_refs.append(Reference(
            idx=remap[old], title=r.title, authors=r.authors, year=r.year,
            doi=r.doi, url=r.url, citations=r.citations))
    return remap, used_refs


def apply_remap(text: str, remap: Dict[int, int]) -> str:
    """Rewrite [old] citation markers to [new]; drop markers with no mapping."""
    def _sub(m):
        n = int(m.group(1))
        return f"[{remap[n]}]" if n in remap else ""
    return re.sub(r"\[(\d+)\]", _sub, text)
