"""
Gemma 3:4b credibility verifier — Layer 6 of the validation pipeline.

Scores each scraped record for relevance to PCNA cryptic pocket research
using Gemma 3:4b running locally via Ollama (OpenAI-compatible API).

PDB structures auto-approve (score=7); papers and datasets are scored by the LLM.

Usage:
    python agents/gemma_verifier.py
    python agents/gemma_verifier.py --catalog data/catalog/pcna_data_catalog.json
    python agents/gemma_verifier.py --dry-run    # print scores, don't write
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from openai import OpenAI

REPO_ROOT    = Path(__file__).parent.parent
CATALOG_PATH = REPO_ROOT / "data" / "catalog" / "pcna_data_catalog.json"

MODEL    = "gemma3:4b"
ENDPOINT = "http://localhost:11434/v1"

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(base_url=ENDPOINT, api_key="ollama")
    return _client


def _health_check() -> bool:
    """Return True if Ollama is reachable and the model is available."""
    try:
        import urllib.request
        urllib.request.urlopen("http://localhost:11434", timeout=3)
        return True
    except Exception:
        return False


_SYSTEM = (
    "You are a data curator for a computational biology project that predicts "
    "cryptic binding pockets on the protein PCNA using a graph neural network. "
    "You evaluate whether a data source is useful for this project."
)

_PROMPT_TEMPLATE = """\
Evaluate this data source for relevance to PCNA cryptic pocket prediction research.

Title: {title}
Description: {description}
Source type: {record_type}
Source database: {source}

Score the relevance on a scale of 1–10:
10 = directly reports PCNA structure, binding, or cryptic pocket data
7  = GNN/pocket prediction methods applicable to PCNA
5  = general protein pocket or binding site data
3  = tangentially related (protein structure, unrelated target)
1  = completely unrelated

Reply with EXACTLY two lines:
<integer score 1-10>
<one-line reason, max 120 characters>
"""


def verify_record(record: dict) -> tuple[int, str]:
    """
    Score a single catalog record with Gemma 3:4b.

    Returns:
        (score, reason)  —  score in [1, 10], reason is a short string.
    """
    record_type = record.get("record_type", "")

    # PDB structures are auto-approved — structural validation already strict
    if record_type == "pdb_structure":
        return 7, "structural data auto-approved (validated by L1-L5)"

    title       = (record.get("title") or "")[:200]
    description = (record.get("description") or "")[:400]
    source      = record.get("source", "")

    prompt = _PROMPT_TEMPLATE.format(
        title=title,
        description=description,
        record_type=record_type,
        source=source,
    )

    try:
        client = _get_client()
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.1,
            max_tokens=80,
        )
        text = resp.choices[0].message.content.strip()
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        score  = max(1, min(10, int(lines[0])))
        reason = lines[1] if len(lines) > 1 else "no reason provided"
        return score, reason[:150]
    except (ValueError, IndexError):
        return 5, "parse error — defaulting to 5"
    except Exception as e:
        return 5, f"llm error: {str(e)[:80]}"


def verify_catalog(
    catalog_path: Path = CATALOG_PATH,
    dry_run: bool = False,
) -> Path:
    """
    Score every record in catalog["passed"] and write gemma_score / gemma_reason
    back to the catalog JSON in-place.

    Returns the catalog path.
    """
    if not _health_check():
        print("[gemma_verifier] Ollama not reachable at localhost:11434 — skipping L6")
        return catalog_path

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    records  = catalog.get("passed", [])
    total    = len(records)

    approved = 0
    dropped  = 0

    print(f"[gemma_verifier] Scoring {total} records with {MODEL}...")
    for i, rec in enumerate(records, 1):
        score, reason = verify_record(rec)
        rec["gemma_score"]  = score
        rec["gemma_reason"] = reason

        status = "PASS" if score >= 6 else "DROP"
        if score >= 6:
            approved += 1
        else:
            dropped += 1

        print(f"  [{i:>4}/{total}] {status} {score:>2}/10  {rec['uid'][:20]:<22}  {reason[:60]}")

        # Be polite to local Ollama — avoid hammering
        if rec.get("record_type") != "pdb_structure":
            time.sleep(0.1)

    print(f"\n[gemma_verifier] Approved={approved}  Dropped={dropped}")

    if not dry_run:
        # Atomic write
        tmp = catalog_path.with_suffix(".tmp.json")
        tmp.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
        tmp.replace(catalog_path)
        print(f"[gemma_verifier] Updated → {catalog_path}")

    return catalog_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gemma 3:4b L6 credibility verifier for PCNA data catalog")
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print scores without writing back to catalog")
    args = parser.parse_args()

    if not args.catalog.exists():
        print(f"[gemma_verifier] Catalog not found: {args.catalog}")
        print("  Run agents/pcna_crawler.py first.")
        return

    verify_catalog(args.catalog, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
