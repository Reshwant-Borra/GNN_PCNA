"""
Document and Knowledge Ingestion Agent (Agent 21)

Ingests PDFs, Markdown, TXT, JSON (arxiv/crawler metadata), HTML, and
Claude/chat transcripts into:
  - research_os_registries/source_registry.json  (machine-readable)
  - Obsidian/GNN_PNCA/docs/sources/SRC-XXXX_slug.md  (human-readable note)
  - Obsidian/GNN_PNCA/docs/sources/_SOURCE_INDEX.md  (index table row)
  - data/artifacts/<task_id>/ingest_report.json  (full report)

Usage:
    python agents/ingest.py --path paper.pdf
    python agents/ingest.py --path note.md --path transcript.md
    python agents/ingest.py --dir research/rmsf_md_research/data/arxiv/
    python agents/ingest.py --transcript "Obsidian/Claude/Chat History/session.md"
    python agents/ingest.py --list-sources
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT      = Path(__file__).parent.parent
REGISTRY_DIR   = REPO_ROOT / "research_os_registries"
SOURCE_REG     = REGISTRY_DIR / "source_registry.json"
ARTIFACT_ROOT  = REPO_ROOT / "data" / "artifacts"
OBSIDIAN_ROOT  = Path("C:/Users/advay/Obsidian/GNN_PNCA")
SOURCES_DIR    = OBSIDIAN_ROOT / "docs" / "sources"
SOURCE_INDEX   = SOURCES_DIR / "_SOURCE_INDEX.md"

SUPPORTED_EXTENSIONS = {".pdf", ".md", ".txt", ".json", ".html", ".htm"}


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class ExtractedSource:
    path: str
    title: str
    source_type: str
    text: str
    sections: list[dict[str, str]]  # [{heading, content}]
    metadata: dict[str, Any]        # authors, date, doi, url, etc.


@dataclass
class SourceEntry:
    id: str
    created: str
    updated: str
    status: str = "current"
    created_by: str = "agent-21"
    title: str = ""
    source_type: str = ""
    original_path: str = ""
    path_hash: str = ""
    doi: str | None = None
    url: str | None = None
    authors: list[str] = field(default_factory=list)
    date_published: str | None = None
    topics: list[str] = field(default_factory=list)
    relevance_score: float = 0.5
    short_summary: str = ""
    abstract_summary: str = ""
    extracted_claims: list[dict] = field(default_factory=list)
    linked_claims: list[str] = field(default_factory=list)
    linked_experiments: list[str] = field(default_factory=list)
    linked_artifacts: list[str] = field(default_factory=list)
    obsidian_note: str = ""
    notes: str = ""


# ── Registry I/O ─────────────────────────────────────────────────────────────

def _load_registry() -> dict:
    if SOURCE_REG.exists():
        return json.loads(SOURCE_REG.read_text(encoding="utf-8"))
    return {"_schema_version": "1.0", "_id_prefix": "SRC", "sources": []}


def _save_registry(reg: dict) -> None:
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    tmp = SOURCE_REG.with_suffix(".tmp")
    tmp.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(SOURCE_REG)


def _next_src_id(reg: dict) -> str:
    existing = [s["id"] for s in reg.get("sources", [])]
    nums = [int(s.split("-")[1]) for s in existing if re.match(r"SRC-\d+", s)]
    return f"SRC-{(max(nums) + 1 if nums else 1):04d}"


def _path_hash(path: str) -> str:
    return hashlib.sha256(path.encode()).hexdigest()[:16]


def _already_ingested(reg: dict, path: str) -> SourceEntry | None:
    ph = _path_hash(path)
    for s in reg.get("sources", []):
        if s.get("path_hash") == ph:
            return s
    return None


# ── Type detection ────────────────────────────────────────────────────────────

def _detect_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return "pdf"
    if ext == ".md":
        # Distinguish transcript from note
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")[:500]
            if "**user**" in text.lower() or "**assistant**" in text.lower() or "## user" in text.lower():
                return "transcript"
        except Exception:
            pass
        return "markdown"
    if ext == ".txt":
        return "text"
    if ext == ".json":
        return "json_metadata"
    if ext in {".html", ".htm"}:
        return "html"
    return "unknown"


# ── Parsers ───────────────────────────────────────────────────────────────────

def _parse_pdf(path: Path) -> ExtractedSource:
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
        text = "\n".join(text_parts)
    except ImportError:
        text = f"[pdfplumber not installed — install with: pip install pdfplumber]\nPath: {path}"
    except Exception as exc:
        text = f"[PDF extraction failed: {exc}]"

    title = path.stem.replace("_", " ").replace("-", " ").title()
    sections = _chunk_paragraphs(text)
    return ExtractedSource(path=str(path), title=title, source_type="pdf",
                           text=text, sections=sections, metadata={})


def _parse_markdown(path: Path) -> ExtractedSource:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    # Extract YAML frontmatter
    meta: dict[str, Any] = {}
    body = raw
    if raw.startswith("---"):
        end = raw.find("---", 3)
        if end != -1:
            fm = raw[3:end].strip()
            for line in fm.splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    meta[k.strip()] = v.strip().strip('"')
            body = raw[end + 3:].strip()

    title = meta.get("title", path.stem.replace("_", " ").replace("-", " ").title())
    sections = _chunk_by_headings(body)
    return ExtractedSource(path=str(path), title=title, source_type="markdown",
                           text=body, sections=sections, metadata=meta)


def _parse_transcript(path: Path) -> ExtractedSource:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    title = path.stem.replace("_", " ").replace("-", " ").title() + " (transcript)"
    # Extract key decisions and facts from assistant messages
    assistant_blocks = re.findall(r"(?:##\s*assistant|assistant\s*\n)(.*?)(?=##\s*user|user\s*\n|$)",
                                  raw, re.IGNORECASE | re.DOTALL)
    if not assistant_blocks:
        assistant_blocks = [raw]
    text = "\n\n".join(b.strip() for b in assistant_blocks if b.strip())
    sections = _chunk_by_headings(text) or _chunk_paragraphs(text)
    return ExtractedSource(path=str(path), title=title, source_type="transcript",
                           text=text, sections=sections, metadata={"session_file": str(path)})


def _parse_json_metadata(path: Path) -> ExtractedSource:
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        data = {}
    # Handle arxiv/PMC crawler JSON format
    title = (data.get("title") or data.get("paper_title") or
             path.stem.replace("_", " ").title())
    abstract = data.get("abstract") or data.get("summary") or ""
    authors = data.get("authors") or []
    if isinstance(authors, str):
        authors = [authors]
    date = data.get("published") or data.get("date") or None
    doi = data.get("doi") or None
    url = data.get("link") or data.get("url") or None
    text = f"{title}\n\n{abstract}"
    sections = [{"heading": "Abstract", "content": abstract}] if abstract else []
    return ExtractedSource(
        path=str(path), title=title, source_type="json_metadata",
        text=text, sections=sections,
        metadata={"authors": authors, "date": date, "doi": doi, "url": url,
                  "raw_keys": list(data.keys())[:10]},
    )


def _parse_html(path: Path) -> ExtractedSource:
    try:
        from bs4 import BeautifulSoup
        raw = path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(raw, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else path.stem
        text = soup.get_text(separator="\n", strip=True)
        sections = _chunk_paragraphs(text)
    except ImportError:
        title = path.stem
        text = f"[beautifulsoup4 not installed]\nPath: {path}"
        sections = []
    return ExtractedSource(path=str(path), title=title, source_type="html",
                           text=text, sections=sections, metadata={})


def _chunk_by_headings(text: str) -> list[dict[str, str]]:
    sections = []
    current_heading = "Introduction"
    current_lines: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^(#{1,4})\s+(.+)$", line)
        if m:
            if current_lines:
                sections.append({"heading": current_heading,
                                  "content": "\n".join(current_lines).strip()})
            current_heading = m.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections.append({"heading": current_heading,
                          "content": "\n".join(current_lines).strip()})
    return [s for s in sections if s["content"]]


def _chunk_paragraphs(text: str, max_chars: int = 800) -> list[dict[str, str]]:
    paras = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    return [{"heading": f"Paragraph {i+1}", "content": p}
            for i, p in enumerate(paras) if len(p) > 30]


def extract_source(path: Path, source_type_override: str | None = None) -> ExtractedSource:
    stype = source_type_override or _detect_type(path)
    if stype == "pdf":
        return _parse_pdf(path)
    if stype == "transcript":
        return _parse_transcript(path)
    if stype in {"markdown", "md"}:
        return _parse_markdown(path)
    if stype == "text":
        raw = path.read_text(encoding="utf-8", errors="ignore")
        return ExtractedSource(path=str(path), title=path.stem, source_type="text",
                               text=raw, sections=_chunk_paragraphs(raw), metadata={})
    if stype == "json_metadata":
        return _parse_json_metadata(path)
    if stype in {"html", "htm"}:
        return _parse_html(path)
    raw = path.read_text(encoding="utf-8", errors="ignore")
    return ExtractedSource(path=str(path), title=path.stem, source_type="unknown",
                           text=raw, sections=[], metadata={})


# ── Summarization + tagging ───────────────────────────────────────────────────

_GNN_PCNA_TOPICS = [
    "pcna", "cryptic pocket", "gnn", "graph neural network", "esm2", "md simulation",
    "molecular dynamics", "rmsf", "dccm", "pocket detection", "binding site", "aoh1996",
    "cryptosite", "pocketminer", "auroc", "auprc", "benchmarking", "protein flexibility",
    "allostery", "gatv2", "focal loss", "protein language model", "gatvconv",
]

def _auto_tag(src: ExtractedSource) -> list[str]:
    text_lower = src.text.lower()
    return [t for t in _GNN_PCNA_TOPICS if t in text_lower]


def _relevance_score(topics: list[str]) -> float:
    core = {"pcna", "cryptic pocket", "gnn", "pocket detection", "aoh1996", "cryptosite"}
    hits = len(set(topics) & core)
    return min(1.0, round(0.3 + hits * 0.12, 2))


def _short_summary(src: ExtractedSource) -> str:
    # Use first non-empty section content, truncated
    for sec in src.sections:
        content = sec["content"].strip()
        if content:
            first_sentence = re.split(r"(?<=[.!?])\s+", content)[0]
            return first_sentence[:200]
    return src.title


def _abstract_summary(src: ExtractedSource) -> str:
    # Use abstract section if present, else first 2 sections
    for sec in src.sections:
        if "abstract" in sec["heading"].lower():
            return sec["content"][:600]
    chunks = [s["content"] for s in src.sections[:2]]
    return " ".join(chunks)[:600]


def _extract_claims(src: ExtractedSource) -> list[dict]:
    """Heuristic claim extraction: look for metric-like sentences."""
    claims = []
    metric_pattern = re.compile(
        r"(AUROC|AUPRC|accuracy|precision|recall|F1|AUC|sensitivity|specificity|"
        r"fold.change|RMSF|DCCM|pocket volume|IC50|binding affinity)[^.]{0,120}\.",
        re.IGNORECASE,
    )
    for sec in src.sections:
        for m in metric_pattern.finditer(sec["content"]):
            claims.append({
                "claim_text": m.group(0).strip(),
                "evidence_type": "computational" if src.source_type != "pdf" else "from_paper",
                "section": sec["heading"],
                "strength": "suggestive",
            })
            if len(claims) >= 8:
                break
        if len(claims) >= 8:
            break
    return claims


# ── Link proposal ─────────────────────────────────────────────────────────────

def _propose_links(src: ExtractedSource, topics: list[str]) -> dict[str, list[str]]:
    """Heuristic link proposals based on topic overlap with known claim/exp IDs."""
    proposed: dict[str, list[str]] = {"claims": [], "experiments": [], "artifacts": []}
    text_lower = src.text.lower()
    if any(t in text_lower for t in ("auroc", "auprc", "cryptosite", "held-out")):
        proposed["claims"].append("CLAIM-0001")
        proposed["experiments"].append("EXP-0001")
    if any(t in text_lower for t in ("aoh1996", "8gla", "binding site", "pocket recovery")):
        proposed["claims"].append("CLAIM-0002")
    if any(t in text_lower for t in ("anm", "normal mode", "fold-change", "dccm")):
        proposed["claims"].append("CLAIM-0003")
        proposed["experiments"].append("EXP-0002")
    if any(t in text_lower for t in ("molecular dynamics", "rmsf", "pocket volume", "trajectory")):
        proposed["claims"].append("CLAIM-0005")
        proposed["experiments"].append("EXP-0003")
    if any(t in text_lower for t in ("esm2", "language model", "plm", "embedding")):
        proposed["claims"].append("CLAIM-0004")
    # Deduplicate
    return {k: list(dict.fromkeys(v)) for k, v in proposed.items()}


# ── Obsidian note writer ──────────────────────────────────────────────────────

def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", title.lower())[:40].strip("_")


def _write_obsidian_note(entry: SourceEntry, src: ExtractedSource,
                          proposals: dict[str, list[str]]) -> Path:
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    slug = _slug(entry.title)
    note_path = SOURCES_DIR / f"{entry.id}_{slug}.md"

    topics_str = ", ".join(entry.topics) if entry.topics else "—"
    authors_str = ", ".join(entry.authors) if entry.authors else "—"
    doi_str = entry.doi or "—"
    url_str = entry.url or "—"

    claim_rows = "\n".join(
        f"| {c['claim_text'][:80]} | {c['evidence_type']} | {c['section']} |"
        for c in entry.extracted_claims[:6]
    ) or "| _(none extracted)_ | | |"

    link_rows = []
    for claim_id in proposals.get("claims", []):
        link_rows.append(f"| claim | {claim_id} | topic overlap |")
    for exp_id in proposals.get("experiments", []):
        link_rows.append(f"| experiment | {exp_id} | topic overlap |")
    links_str = "\n".join(link_rows) or "| _(no proposals)_ | | |"

    abstract = entry.abstract_summary[:500] or "_(no abstract extracted)_"

    content = f"""---
src_id: {entry.id}
title: "{entry.title}"
source_type: {entry.source_type}
topics: [{topics_str}]
relevance: {entry.relevance_score}
date_ingested: {entry.created[:10]}
original_path: "{entry.original_path}"
---

# {entry.title}

**SRC-ID:** {entry.id}
**Type:** {entry.source_type}
**Authors:** {authors_str}
**Published:** {entry.date_published or '—'}
**DOI:** {doi_str}
**URL:** {url_str}
**Topics:** {topics_str}
**Relevance:** {entry.relevance_score}

→ Links: [[_SOURCE_INDEX]] | [[INDEX]]

---

## Summary

{entry.short_summary}

---

## Abstract / Overview

{abstract}

---

## Extracted Claims

| Claim | Evidence type | Section |
|---|---|---|
{claim_rows}

---

## Proposed Links to Project

| Type | ID | Rationale |
|---|---|---|
{links_str}

---

## Notes

{entry.notes or '_(none)_'}
"""
    note_path.write_text(content, encoding="utf-8")
    return note_path


def _update_source_index(entry: SourceEntry) -> None:
    if not SOURCE_INDEX.exists():
        return
    raw = SOURCE_INDEX.read_text(encoding="utf-8")
    # Find the table and append a row before the empty sentinel
    table_sentinel = "| _(empty — run ingest to populate)_ | | | | | |"
    slug = _slug(entry.title)
    topics_short = ", ".join(entry.topics[:3]) if entry.topics else "—"
    claims_short = ", ".join(entry.linked_claims[:2]) if entry.linked_claims else "—"
    new_row = (f"| {entry.id} | [[{entry.id}_{slug}\\|{entry.title[:40]}]] "
               f"| {entry.source_type} | {topics_short} | {claims_short} "
               f"| {entry.created[:10]} |")

    if table_sentinel in raw:
        raw = raw.replace(table_sentinel, new_row)
    else:
        # Append row after last table row
        lines = raw.splitlines()
        last_table_line = max(
            (i for i, l in enumerate(lines) if l.startswith("|")), default=None
        )
        if last_table_line is not None:
            lines.insert(last_table_line + 1, new_row)
            raw = "\n".join(lines)
        else:
            raw += f"\n{new_row}\n"

    SOURCE_INDEX.write_text(raw, encoding="utf-8")


# ── Main ingest logic ─────────────────────────────────────────────────────────

def ingest_file(path: Path, reg: dict,
                source_type_override: str | None = None) -> tuple[SourceEntry, dict]:
    """Ingest one file. Returns (entry, link_proposals). Does NOT save registry."""
    path_str = str(path.resolve())

    existing = _already_ingested(reg, path_str)
    if existing:
        print(f"  [skip] {path.name} — already ingested as {existing['id']}")
        return None, {}

    print(f"  [parse] {path.name}")
    src = extract_source(path, source_type_override)

    topics = _auto_tag(src)
    relevance = _relevance_score(topics)
    claims = _extract_claims(src)
    proposals = _propose_links(src, topics)

    now = datetime.now(timezone.utc).isoformat()
    src_id = _next_src_id(reg)

    entry = SourceEntry(
        id=src_id,
        created=now,
        updated=now,
        title=src.title,
        source_type=src.source_type,
        original_path=path_str,
        path_hash=_path_hash(path_str),
        doi=src.metadata.get("doi"),
        url=src.metadata.get("url"),
        authors=src.metadata.get("authors", []),
        date_published=src.metadata.get("date"),
        topics=topics,
        relevance_score=relevance,
        short_summary=_short_summary(src),
        abstract_summary=_abstract_summary(src),
        extracted_claims=claims,
        linked_claims=proposals.get("claims", []),
        linked_experiments=proposals.get("experiments", []),
        linked_artifacts=proposals.get("artifacts", []),
    )

    # Write Obsidian note
    note_path = _write_obsidian_note(entry, src, proposals)
    entry.obsidian_note = str(note_path)
    print(f"  [note] {note_path.name}")

    # Update SOURCE_INDEX
    _update_source_index(entry)

    # Stage for registry write
    reg.setdefault("sources", []).append(asdict(entry))

    return entry, proposals


def collect_paths(args) -> list[Path]:
    paths: list[Path] = []
    for p in getattr(args, "path", []) or []:
        fp = Path(p)
        if fp.is_file():
            paths.append(fp)
        else:
            print(f"[warn] Not a file: {fp}")
    if getattr(args, "dir", None):
        d = Path(args.dir)
        if d.is_dir():
            paths.extend(f for f in d.rglob("*") if f.suffix.lower() in SUPPORTED_EXTENSIONS)
        else:
            print(f"[warn] Not a directory: {d}")
    if getattr(args, "transcript", None):
        tp = Path(args.transcript)
        if tp.is_file():
            paths.append(tp)
        else:
            print(f"[warn] Transcript not found: {tp}")
    return paths


def run_ingest(args) -> None:
    paths = collect_paths(args)
    if not paths:
        print("No files to ingest.")
        return

    reg = _load_registry()
    task_id = str(uuid.uuid4())[:8]
    artifact_dir = ARTIFACT_ROOT / task_id
    artifact_dir.mkdir(parents=True, exist_ok=True)

    ingested: list[dict] = []
    skipped: list[str] = []

    print(f"\nIngesting {len(paths)} file(s) — task {task_id}\n")
    for path in paths:
        entry, proposals = ingest_file(path, reg, getattr(args, "source_type", None))
        if entry is None:
            skipped.append(str(path))
        else:
            ingested.append({"id": entry.id, "title": entry.title,
                             "obsidian_note": entry.obsidian_note,
                             "topics": entry.topics,
                             "linked_claims": entry.linked_claims,
                             "link_proposals": proposals})

    _save_registry(reg)

    report = {
        "task_id": task_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ingested": len(ingested),
        "skipped": len(skipped),
        "sources": ingested,
        "skipped_paths": skipped,
    }
    report_path = artifact_dir / "ingest_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"Ingested: {len(ingested)} | Skipped: {len(skipped)}")
    print(f"Source registry: {SOURCE_REG}")
    print(f"Ingest report:   {report_path}")
    print(f"Obsidian sources: {SOURCES_DIR}")
    if ingested:
        print("\nNew sources:")
        for s in ingested:
            topics_str = ", ".join(s["topics"][:3]) or "—"
            print(f"  {s['id']} — {s['title'][:50]}  [{topics_str}]")
            if s["linked_claims"]:
                print(f"         -> proposed links: {', '.join(s['linked_claims'])}")


def list_sources() -> None:
    reg = _load_registry()
    sources = reg.get("sources", [])
    if not sources:
        print("Source registry is empty. Run: python agents/ingest.py --path <file>")
        return
    print(f"\n{'SRC-ID':<10} {'Title':<45} {'Type':<15} {'Relevance':<10}")
    print("-" * 85)
    for s in sources:
        title = s.get("title", "")[:44]
        stype = s.get("source_type", "")[:14]
        rel = s.get("relevance_score", 0)
        print(f"{s['id']:<10} {title:<45} {stype:<15} {rel:.2f}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Agent 21: Document and Knowledge Ingestion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd")

    ingest_p = sub.add_parser("ingest", help="Ingest files (default command)")
    ingest_p.add_argument("--path", action="append", metavar="FILE",
                          help="File to ingest (can repeat)")
    ingest_p.add_argument("--dir", metavar="DIR",
                          help="Directory to batch-ingest")
    ingest_p.add_argument("--transcript", metavar="FILE",
                          help="Claude/chat transcript to ingest")
    ingest_p.add_argument("--source-type", dest="source_type", metavar="TYPE",
                          help="Override type detection")

    sub.add_parser("list", help="List all ingested sources")

    # Allow bare --path / --dir without subcommand for convenience
    parser.add_argument("--path", action="append", metavar="FILE")
    parser.add_argument("--dir", metavar="DIR")
    parser.add_argument("--transcript", metavar="FILE")
    parser.add_argument("--source-type", dest="source_type", metavar="TYPE")
    parser.add_argument("--list-sources", action="store_true")

    args = parser.parse_args()

    if args.cmd == "list" or getattr(args, "list_sources", False):
        list_sources()
        return

    if args.cmd == "ingest" or args.cmd is None:
        run_ingest(args)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
