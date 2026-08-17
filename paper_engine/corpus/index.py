"""Hybrid retrieval index over the downloaded corpus.

BM25 (rank_bm25) for sparse lexical retrieval plus an optional dense layer using
local Ollama embeddings (nomic-embed-text). Metadata + extracted text live in a
SQLite database so the 30 GB of PDFs are indexed once and queried cheaply during
manuscript drafting (RAG citation grounding).

Heavy deps (rank_bm25, pdfplumber) are optional; build() reports clearly if they
are missing rather than failing obscurely.
"""
from __future__ import annotations

import json
import pickle
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from paper_engine import config
from paper_engine.corpus import extract as extract_mod

_DB = "corpus.sqlite"
_BM25 = "bm25.pkl"


def _db_path() -> Path:
    return config.CORPUS_INDEX_DIR / _DB


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


@dataclass
class Hit:
    doc_id: int
    score: float
    title: str
    doi: str
    snippet: str


def _ensure_db() -> sqlite3.Connection:
    config.CORPUS_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_db_path()))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS docs ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT UNIQUE, doi TEXT, "
        "title TEXT, year INTEGER, path TEXT, n_pages INTEGER, text TEXT)")
    return conn


def _extract_one(args):
    """Module-level worker for parallel extraction (must be picklable on Windows).

    Returns (key, title, n_pages, text) or None on failure.
    """
    key, abspath, fallback_title = args
    try:
        from paper_engine.corpus import extract as _extract
        doc = _extract.extract_text(Path(abspath))
        return (key, doc.title or fallback_title, doc.n_pages, doc.text)
    except Exception:
        return None


def build(max_docs: Optional[int] = None, verbose: bool = True) -> dict:
    """Extract text from downloaded PDFs and build the SQLite + BM25 index."""
    if not extract_mod.available():
        raise RuntimeError(
            "pdfplumber is required to index PDFs. Install with: pip install -e \".[paper]\"")
    try:
        from rank_bm25 import BM25Okapi
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "rank_bm25 is required for the index. Install with: pip install -e \".[paper]\"") from exc

    manifest_path = config.CORPUS_DIR / "corpus_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError("No corpus_manifest.json — run the crawl first (paper-corpus).")
    items = json.loads(manifest_path.read_text(encoding="utf-8")).get("items", [])
    if max_docs:
        items = items[:max_docs]

    conn = _ensure_db()
    corpus_tokens: List[List[str]] = []
    doc_ids: List[int] = []
    indexed = 0

    # Partition into already-indexed (reuse) and to-extract (parallel).
    to_extract = []
    for it in items:
        pdf_path = (config.REPO_ROOT / it["path"]) if not Path(it["path"]).is_absolute() else Path(it["path"])
        if not pdf_path.exists():
            continue
        row = conn.execute("SELECT id, text FROM docs WHERE key=?", (it["key"],)).fetchone()
        if row:
            doc_id, text = row
            corpus_tokens.append(_tokenize(text))
            doc_ids.append(doc_id)
            indexed += 1
        else:
            to_extract.append((it["key"], str(pdf_path), it.get("title", ""),
                               it.get("doi", ""), it.get("year"), it["path"]))

    # Parallel extraction across all cores (pdfplumber is CPU-bound).
    if to_extract:
        from concurrent.futures import ProcessPoolExecutor

        meta = {t[0]: t for t in to_extract}
        work = [(t[0], t[1], t[2]) for t in to_extract]
        results = []
        try:
            with ProcessPoolExecutor(max_workers=config.WORKER_PROCESSES) as ex:
                results = list(ex.map(_extract_one, work))
        except Exception as exc:  # fall back to sequential if pool fails
            if verbose:
                print(f"[index] parallel pool failed ({exc}); extracting sequentially")
            results = [_extract_one(w) for w in work]
        for res in results:
            if not res:
                continue
            key, title, n_pages, text = res
            _, _, _, doi, year, relpath = meta[key]
            cur = conn.execute(
                "INSERT OR IGNORE INTO docs(key,doi,title,year,path,n_pages,text) "
                "VALUES(?,?,?,?,?,?,?)", (key, doi, title, year, relpath, n_pages, text))
            row = conn.execute("SELECT id FROM docs WHERE key=?", (key,)).fetchone()
            if row:
                corpus_tokens.append(_tokenize(text))
                doc_ids.append(row[0])
                indexed += 1
        conn.commit()
        if verbose:
            print(f"[index] extracted {len(to_extract)} PDFs across {config.WORKER_PROCESSES} workers")

    if corpus_tokens:
        bm25 = BM25Okapi(corpus_tokens)
        with open(config.CORPUS_INDEX_DIR / _BM25, "wb") as fh:
            pickle.dump({"bm25": bm25, "doc_ids": doc_ids}, fh)
    conn.close()
    return {"indexed": indexed, "db": str(_db_path())}


def search(query: str, k: int = 5) -> List[Hit]:
    """Lexical BM25 search over the indexed corpus."""
    bm_path = config.CORPUS_INDEX_DIR / _BM25
    if not bm_path.exists():
        return []
    with open(bm_path, "rb") as fh:
        payload = pickle.load(fh)
    bm25, doc_ids = payload["bm25"], payload["doc_ids"]
    scores = bm25.get_scores(_tokenize(query))
    ranked = sorted(zip(doc_ids, scores), key=lambda x: x[1], reverse=True)[:k]
    conn = _ensure_db()
    hits: List[Hit] = []
    for doc_id, score in ranked:
        row = conn.execute("SELECT title, doi, text FROM docs WHERE id=?", (doc_id,)).fetchone()
        if not row:
            continue
        title, doi, text = row
        hits.append(Hit(doc_id=doc_id, score=float(score), title=title or "",
                        doi=doi or "", snippet=(text or "")[:300]))
    conn.close()
    return hits
