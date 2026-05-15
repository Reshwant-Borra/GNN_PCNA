"""
Obsidian Vault Writer — pushes verified catalog records to docs/knowledge/.

Reads data/catalog/pcna_data_catalog.json (after gemma_verifier.py has run),
filters records with gemma_score >= min_gemma OR record_type == "pdb_structure",
and writes structured Obsidian-compatible Markdown notes.

Output directories:
    docs/knowledge/auto_indexed/structures/   — PDB structure notes
    docs/knowledge/auto_indexed/literature/   — paper notes
    docs/knowledge/auto_indexed/datasets/     — dataset/compound notes

Also appends new wikilinks to docs/knowledge/INDEX.md under ## Auto-Indexed.

Usage:
    python agents/obsidian_writer.py
    python agents/obsidian_writer.py --min-gemma 7 --catalog path/to/catalog.json
    python agents/obsidian_writer.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT    = Path(__file__).parent.parent
CATALOG_PATH = REPO_ROOT / "data" / "catalog" / "pcna_data_catalog.json"
VAULT_BASE   = REPO_ROOT / "docs" / "knowledge" / "auto_indexed"
INDEX_PATH   = REPO_ROOT / "docs" / "knowledge" / "INDEX.md"


def _slug(uid: str) -> str:
    """Make a filesystem-safe slug from a record uid."""
    return re.sub(r'[^A-Za-z0-9_\-]', '_', uid)[:60]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ── Note templates ────────────────────────────────────────────────────────────

def _structure_note(rec: dict) -> str:
    uid        = rec.get("uid", "")
    title      = rec.get("title", "")
    source     = rec.get("source", "")
    url        = rec.get("url", "")
    dl_url     = rec.get("download_url", "")
    relevance  = rec.get("relevance", 0.0)
    gemma      = rec.get("gemma_score", "N/A")
    g_reason   = rec.get("gemma_reason", "")
    fetched    = rec.get("fetched_at", "")
    meta       = rec.get("metadata", {})
    resolution = meta.get("resolution") or rec.get("validation", {}).get("l3", {}).get("resolution_angstrom", "?")
    organism   = meta.get("organism", "")
    uniprot_ok = "YES" if meta.get("uniprot_confirmed") else "—"
    chains     = rec.get("validation", {}).get("l3", {}).get("chains", [])
    ca_comp    = rec.get("validation", {}).get("l3", {}).get("ca_completeness", "?")

    return f"""\
---
type: pdb-structure
uid: {uid}
source: {source}
resolution: {resolution}
organism: {organism}
uniprot_confirmed: {uniprot_ok}
relevance_score: {relevance:.3f}
gemma_score: {gemma}
fetched: {fetched or _now()}
auto_indexed: {_now()}
---

# {uid} — {title}

| Field | Value |
|---|---|
| PDB ID | [{uid}]({url}) |
| Resolution | {resolution} Å |
| Organism | {organism} |
| UniProt P12004 | {uniprot_ok} |
| Chains | {', '.join(chains) if chains else '?'} |
| Cα completeness | {ca_comp} |
| Source | {source} |
| Relevance score | {relevance:.3f} |
| Gemma score | {gemma}/10 |
| Gemma reason | {g_reason} |

## Download

```
{dl_url or url}
```

## Links

[[INDEX]] · [[DATASETS]] · [[PIPELINE]]
"""


def _paper_note(rec: dict) -> str:
    uid      = rec.get("uid", "")
    title    = rec.get("title", "") or uid
    source   = rec.get("source", "")
    url      = rec.get("url", "")
    desc     = (rec.get("description") or "")[:500]
    relevance = rec.get("relevance", 0.0)
    gemma    = rec.get("gemma_score", "N/A")
    g_reason = rec.get("gemma_reason", "")
    meta     = rec.get("metadata", {})
    pmid     = meta.get("pmid", "")
    doi      = meta.get("doi", "")
    query    = meta.get("query", "")

    return f"""\
---
type: paper
uid: {uid}
source: {source}
pmid: {pmid}
doi: {doi}
relevance_score: {relevance:.3f}
gemma_score: {gemma}
auto_indexed: {_now()}
---

# {title}

| Field | Value |
|---|---|
| Source | {source} |
| PMID | {pmid} |
| DOI | {doi} |
| Found by query | `{query}` |
| Relevance | {relevance:.3f} |
| Gemma score | {gemma}/10 |
| Gemma verdict | {g_reason} |

## Abstract / Description

{desc}

## URL

[Open]({url})

## Action

- [ ] Read and assess for NotebookLM extraction
- [ ] If relevant: add to NotebookLM notebook → distill → merge into [[INDEX]]

## Links

[[INDEX]] · [[NOTEBOOKLM_WORKFLOW]] · [[RESEARCH_QUESTION]]
"""


def _dataset_note(rec: dict) -> str:
    uid      = rec.get("uid", "")
    title    = rec.get("title", "") or uid
    source   = rec.get("source", "")
    url      = rec.get("url", "")
    dl_url   = rec.get("download_url", "")
    desc     = (rec.get("description") or "")[:400]
    relevance = rec.get("relevance", 0.0)
    gemma    = rec.get("gemma_score", "N/A")
    g_reason = rec.get("gemma_reason", "")
    meta     = rec.get("metadata", {})
    doi      = meta.get("doi", "")

    return f"""\
---
type: dataset
uid: {uid}
source: {source}
doi: {doi}
relevance_score: {relevance:.3f}
gemma_score: {gemma}
auto_indexed: {_now()}
---

# {title}

| Field | Value |
|---|---|
| Source | {source} |
| DOI | {doi} |
| Relevance | {relevance:.3f} |
| Gemma score | {gemma}/10 |
| Gemma verdict | {g_reason} |

## Description

{desc}

## Download

[Page]({url})
{f'[Direct download]({dl_url})' if dl_url else ''}

## Links

[[INDEX]] · [[DATASETS]] · [[PIPELINE]]
"""


# ── Writer ────────────────────────────────────────────────────────────────────

def write_record(rec: dict, dry_run: bool = False) -> Path | None:
    """Write one Obsidian note for a catalog record. Returns output path or None."""
    rtype = rec.get("record_type", "")
    uid   = rec.get("uid", "unknown")

    if rtype == "pdb_structure":
        out_dir = VAULT_BASE / "structures"
        content = _structure_note(rec)
    elif rtype == "paper":
        out_dir = VAULT_BASE / "literature"
        content = _paper_note(rec)
    elif rtype in ("dataset", "compound"):
        out_dir = VAULT_BASE / "datasets"
        content = _dataset_note(rec)
    else:
        return None

    filename = f"{_slug(uid)}.md"
    out_path = out_dir / filename

    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        if not out_path.exists():
            out_path.write_text(content, encoding="utf-8")

    return out_path


def _update_index(new_paths: list[Path], dry_run: bool = False) -> None:
    """Append new wikilinks to INDEX.md under ## Auto-Indexed section."""
    if not new_paths:
        return

    section_header = "## Auto-Indexed"

    if INDEX_PATH.exists():
        existing = INDEX_PATH.read_text(encoding="utf-8")
    else:
        existing = "# INDEX\n\n"

    # Build relative wikilinks
    links: list[str] = []
    for p in new_paths:
        try:
            rel = p.relative_to(REPO_ROOT / "docs" / "knowledge")
            name = p.stem
            links.append(f"- [[{name}]]")
        except ValueError:
            links.append(f"- [[{p.stem}]]")

    if section_header not in existing:
        append_block = f"\n\n{section_header}\n\n" + "\n".join(links) + "\n"
        updated = existing + append_block
    else:
        # Find existing section and append non-duplicate links
        existing_links = set(existing.split(section_header)[-1].splitlines())
        new_links = [l for l in links if l not in existing_links]
        if not new_links:
            return
        insert = "\n".join(new_links) + "\n"
        updated = existing.replace(
            section_header,
            section_header + "\n" + insert,
            1,
        )

    if not dry_run:
        INDEX_PATH.write_text(updated, encoding="utf-8")


def write_catalog(
    catalog_path: Path = CATALOG_PATH,
    min_gemma: int = 6,
    dry_run: bool = False,
) -> None:
    """
    Write Obsidian notes for all verified, Gemma-approved records.

    A record is written if:
      - record_type == "pdb_structure"  (structural validation sufficient)
      - OR gemma_score >= min_gemma
    """
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    records  = catalog.get("passed", [])

    written:  list[Path] = []
    skipped = 0

    print(f"[obsidian_writer] Processing {len(records)} records "
          f"(min_gemma={min_gemma}) ...")

    for rec in records:
        rtype       = rec.get("record_type", "")
        gemma_score = rec.get("gemma_score", None)

        # Decide whether to write
        if rtype == "pdb_structure":
            pass   # always write
        elif gemma_score is None or gemma_score < min_gemma:
            skipped += 1
            continue

        path = write_record(rec, dry_run=dry_run)
        if path:
            action = "DRY" if dry_run else "WRITE"
            print(f"  [{action}] {path.relative_to(REPO_ROOT)}")
            written.append(path)

    _update_index(written, dry_run=dry_run)

    print(f"\n[obsidian_writer] Written={len(written)}  Skipped={skipped}")
    if dry_run:
        print("  (dry-run — no files modified)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Write verified catalog records as Obsidian notes")
    parser.add_argument("--catalog",   type=Path, default=CATALOG_PATH)
    parser.add_argument("--min-gemma", type=int,  default=6,
                        help="Min gemma_score to include non-structure records (default 6)")
    parser.add_argument("--dry-run",   action="store_true",
                        help="Print what would be written without writing files")
    args = parser.parse_args()

    if not args.catalog.exists():
        print(f"[obsidian_writer] Catalog not found: {args.catalog}")
        print("  Run agents/pcna_crawler.py then agents/gemma_verifier.py first.")
        return

    write_catalog(args.catalog, args.min_gemma, args.dry_run)


if __name__ == "__main__":
    main()
