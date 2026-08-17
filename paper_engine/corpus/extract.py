"""PDF text extraction (pdfplumber).

Lazily imports pdfplumber so the rest of paper_engine works without it. Extracts
plain text and a best-effort title/abstract for indexing.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def available() -> bool:
    try:
        import pdfplumber  # noqa: F401
        return True
    except Exception:
        return False


@dataclass
class ExtractedDoc:
    path: str
    n_pages: int
    text: str
    title: str = ""
    abstract: str = ""


def extract_text(pdf_path: Path, max_pages: Optional[int] = None) -> ExtractedDoc:
    """Extract text from a PDF. Raises ImportError if pdfplumber is missing."""
    import pdfplumber

    pages_text = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        pages = pdf.pages if max_pages is None else pdf.pages[:max_pages]
        for page in pages:
            pages_text.append(page.extract_text() or "")
        n_pages = len(pdf.pages)
    text = "\n".join(pages_text)

    # Best-effort title = first non-empty line; abstract = text after "Abstract".
    title = ""
    for line in text.splitlines():
        if line.strip():
            title = line.strip()[:300]
            break
    abstract = ""
    low = text.lower()
    if "abstract" in low:
        start = low.index("abstract") + len("abstract")
        abstract = text[start:start + 1500].strip()

    return ExtractedDoc(path=str(pdf_path), n_pages=n_pages, text=text,
                        title=title, abstract=abstract)
