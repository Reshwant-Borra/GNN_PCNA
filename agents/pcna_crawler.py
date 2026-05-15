"""
PCNA Training Data Web Crawler
================================
Recursive web crawler with verification layers to find and catalog
training data for the GNN-PCNA cryptic pocket detection project.

Sources searched:
  - RCSB PDB REST API  (all human PCNA structures)
  - UniProt API        (P12004 cross-refs → PDB IDs)
  - CryptoSite dataset (Cimermancic 2016 - cryptic pocket benchmark)
  - PocketMiner repo   (GitHub, supplementary data links)
  - PubMed/PMC API     (papers with downloadable structure data)
  - sc-PDB             (binding site database for pre-training)

Output:
  data/catalog/pcna_data_catalog.json   — full structured catalog
  data/catalog/download_queue.txt       — URLs ready to wget/curl
  data/catalog/crawl_report.md          — human-readable summary

Usage:
    python agents/pcna_crawler.py                    # full run
    python agents/pcna_crawler.py --sources rcsb     # single source
    python agents/pcna_crawler.py --download          # also fetch PDB files
"""

import argparse
import json
import re
import time
import urllib.parse
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

# ── paths ──────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent
CATALOG_DIR = REPO_ROOT / "data" / "catalog"
PDB_RAW_DIR = REPO_ROOT / "data" / "raw"

CATALOG_DIR.mkdir(parents=True, exist_ok=True)
PDB_RAW_DIR.mkdir(parents=True, exist_ok=True)

# ── constants ──────────────────────────────────────────────────────────────────
RCSB_SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
RCSB_ENTRY_URL  = "https://data.rcsb.org/rest/v1/core/entry/{}"
RCSB_DOWNLOAD   = "https://files.rcsb.org/download/{}.pdb"
UNIPROT_URL     = "https://rest.uniprot.org/uniprotkb/{}.json"
PUBMED_SEARCH   = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH    = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

PCNA_UNIPROT_ID = "P12004"          # human PCNA
KNOWN_STRUCTURES = ["1W60", "8GLA", "1AXC", "1W61"]  # always include these

POLITE_DELAY = 0.5   # seconds between requests

# ── verification layer ─────────────────────────────────────────────────────────

class VerificationResult:
    def __init__(self, passed: bool, reason: str, score: float = 0.0):
        self.passed = passed
        self.reason = reason
        self.score  = score   # 0.0–1.0 relevance score

    def __repr__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"[{status} {self.score:.2f}] {self.reason}"


def verify_pdb_entry(entry: dict) -> VerificationResult:
    """Check if a PDB entry is relevant for PCNA cryptic pocket training."""
    pdb_id    = entry.get("pdb_id", "").upper()
    title     = entry.get("title", "").lower()
    organisms = [o.lower() for o in entry.get("organisms", [])]
    polymers  = [p.lower() for p in entry.get("polymer_types", [])]
    resolution = entry.get("resolution_angstrom")

    score = 0.0
    reasons = []

    # Must be protein
    if not any("polypeptide" in p or "protein" in p for p in polymers):
        if polymers:
            return VerificationResult(False, f"Not a protein: {polymers}")

    # PCNA-specific hits get high score
    pcna_keywords = ["pcna", "proliferating cell nuclear antigen",
                     "sliding clamp", "clamp loader", "aoh1996",
                     "cryptic pocket", "idcl"]
    for kw in pcna_keywords:
        if kw in title:
            score += 0.4
            reasons.append(f"title contains '{kw}'")
            break

    # Human organism preferred
    if any("homo sapiens" in o or "human" in o for o in organisms):
        score += 0.2
        reasons.append("human organism")
    elif any(o for o in organisms):
        score += 0.05

    # Known ground-truth structures
    if pdb_id in KNOWN_STRUCTURES:
        score = 1.0
        reasons.append("known ground-truth structure")

    # Resolution filter (< 3.5 Å acceptable for graph construction)
    if resolution is not None:
        if resolution <= 2.5:
            score += 0.2
            reasons.append(f"high resolution {resolution}Å")
        elif resolution <= 3.5:
            score += 0.1
            reasons.append(f"acceptable resolution {resolution}Å")
        else:
            score -= 0.1
            reasons.append(f"low resolution {resolution}Å")

    # Cryptic pocket dataset markers
    cryptic_kw = ["cryptosite", "cryptic", "hidden pocket", "allosteric",
                  "conformational change", "pocket", "binding site"]
    for kw in cryptic_kw:
        if kw in title:
            score += 0.15
            reasons.append(f"cryptic/pocket keyword '{kw}'")
            break

    passed = score >= 0.2 or pdb_id in KNOWN_STRUCTURES
    reason = "; ".join(reasons) if reasons else "no matching keywords"
    return VerificationResult(passed, reason, min(score, 1.0))


def verify_dataset_url(url: str, description: str) -> VerificationResult:
    """Light verification for non-PDB dataset links."""
    score = 0.0
    kws = ["cryptosite", "pcna", "pocket", "cryptic", "cryptominer",
           "pocketminer", "sc-pdb", "training", "benchmark"]
    desc_lower = description.lower()
    for kw in kws:
        if kw in desc_lower or kw in url.lower():
            score += 0.3
    # Penalise obviously wrong file types
    if url.endswith((".png", ".jpg", ".css", ".js")):
        return VerificationResult(False, "non-data file type", 0.0)
    passed = score >= 0.3
    return VerificationResult(passed, f"url/desc match score {score:.1f}", score)


# ── data sources ───────────────────────────────────────────────────────────────

class RCSBSource:
    """Query RCSB PDB for PCNA-related structures via REST search API."""

    name = "rcsb"

    def fetch(self) -> list[dict]:
        results = []
        results += self._search_by_uniprot(PCNA_UNIPROT_ID)
        results += self._search_by_keyword("PCNA cryptic pocket")
        results += self._search_by_keyword("sliding clamp cryptic")
        results += self._fetch_known_structures()
        return self._deduplicate(results)

    def _search_by_uniprot(self, uniprot_id: str) -> list[dict]:
        query = {
            "query": {
                "type": "terminal",
                "service": "text",
                "parameters": {
                    "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                    "operator": "exact_match",
                    "value": uniprot_id,
                }
            },
            "return_type": "entry",
            "request_options": {"results_slice": {"start": 0, "limit": 200}}
        }
        return self._execute_query(query, f"UniProt:{uniprot_id}")

    def _search_by_keyword(self, keyword: str) -> list[dict]:
        query = {
            "query": {
                "type": "terminal",
                "service": "full_text",
                "parameters": {"value": keyword}
            },
            "return_type": "entry",
            "request_options": {"results_slice": {"start": 0, "limit": 50}}
        }
        return self._execute_query(query, f"keyword:{keyword}")

    def _fetch_known_structures(self) -> list[dict]:
        entries = []
        for pdb_id in KNOWN_STRUCTURES:
            entry = self._fetch_entry_metadata(pdb_id)
            if entry:
                entries.append(entry)
        return entries

    def _execute_query(self, query: dict, label: str) -> list[dict]:
        time.sleep(POLITE_DELAY)
        try:
            r = requests.post(RCSB_SEARCH_URL, json=query, timeout=15)
            r.raise_for_status()
            hits = r.json().get("result_set", [])
            print(f"  RCSB {label}: {len(hits)} hits")
            entries = []
            for hit in hits:
                pdb_id = hit.get("identifier", "").split("_")[0].upper()
                if pdb_id:
                    entry = self._fetch_entry_metadata(pdb_id)
                    if entry:
                        entries.append(entry)
                        time.sleep(POLITE_DELAY)
            return entries
        except Exception as e:
            print(f"  RCSB error ({label}): {e}")
            return []

    def _fetch_entry_metadata(self, pdb_id: str) -> Optional[dict]:
        try:
            r = requests.get(RCSB_ENTRY_URL.format(pdb_id), timeout=10)
            r.raise_for_status()
            data = r.json()
            struct = data.get("struct", {})
            exp    = data.get("exptl", [{}])[0]
            return {
                "pdb_id":               pdb_id,
                "title":                struct.get("title", ""),
                "resolution_angstrom":  data.get("refine", [{}])[0].get("ls_d_res_high"),
                "organisms":            [
                    s.get("pdbx_description", "")
                    for s in data.get("rcsb_entity_source_organism", [])
                ],
                "polymer_types":        [
                    p.get("rcsb_entity_polymer_type", "")
                    for p in data.get("entity_poly", [])
                ],
                "experimental_method":  exp.get("method", ""),
                "download_url":         RCSB_DOWNLOAD.format(pdb_id),
                "rcsb_url":             f"https://www.rcsb.org/structure/{pdb_id}",
                "source":               "rcsb",
            }
        except Exception as e:
            print(f"    metadata error {pdb_id}: {e}")
            return None

    def _deduplicate(self, entries: list[dict]) -> list[dict]:
        seen = set()
        out  = []
        for e in entries:
            pid = e.get("pdb_id", "")
            if pid and pid not in seen:
                seen.add(pid)
                out.append(e)
        return out


class UniProtSource:
    """Cross-reference UniProt P12004 to find additional PDB entries."""

    name = "uniprot"

    def fetch(self) -> list[dict]:
        time.sleep(POLITE_DELAY)
        try:
            r = requests.get(UNIPROT_URL.format(PCNA_UNIPROT_ID), timeout=15)
            r.raise_for_status()
            data = r.json()
            pdb_ids = []
            for xref in data.get("dbReferences", []):
                if xref.get("type") == "PDB":
                    pdb_ids.append(xref["id"])
            print(f"  UniProt P12004: {len(pdb_ids)} PDB cross-refs")
            return [{"pdb_id": pid, "source": "uniprot",
                     "download_url": RCSB_DOWNLOAD.format(pid),
                     "title": "", "organisms": ["Homo sapiens"],
                     "polymer_types": ["polypeptide(L)"],
                     "resolution_angstrom": None}
                    for pid in pdb_ids]
        except Exception as e:
            print(f"  UniProt error: {e}")
            return []


class RecursiveCrawler:
    """
    Generic recursive web crawler with depth limit and relevance filtering.
    Crawls HTML pages, extracts dataset/download links, verifies relevance.
    """

    RELEVANCE_KEYWORDS = [
        "cryptosite", "cryptic pocket", "pcna", "sliding clamp",
        "aoh1996", "pocketminer", "sc-pdb", "cryptic binding",
        "training data", "dataset", "benchmark", "apo", "holo",
        "molecular dynamics", "pocket detection",
    ]

    def __init__(self, seed_urls: list[str], max_depth: int = 2, max_pages: int = 40):
        self.seed_urls = seed_urls
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.visited:  set[str] = set()
        self.found_datasets: list[dict] = []

    def crawl(self) -> list[dict]:
        queue: deque[tuple[str, int]] = deque((url, 0) for url in self.seed_urls)

        while queue and len(self.visited) < self.max_pages:
            url, depth = queue.popleft()
            if url in self.visited:
                continue
            self.visited.add(url)

            print(f"  crawling [depth={depth}]: {url[:80]}")
            page_data = self._fetch_page(url)
            if not page_data:
                continue

            time.sleep(POLITE_DELAY)
            links, datasets = self._extract(url, page_data)

            for ds in datasets:
                result = verify_dataset_url(ds["url"], ds["description"])
                if result.passed:
                    ds["relevance_score"] = result.score
                    ds["verification"]    = result.reason
                    self.found_datasets.append(ds)

            if depth < self.max_depth:
                for link in links:
                    if link not in self.visited and self._is_relevant_url(link):
                        queue.append((link, depth + 1))

        return self.found_datasets

    def _fetch_page(self, url: str) -> Optional[str]:
        try:
            headers = {"User-Agent": "GNN-PCNA-research-crawler/1.0 (academic)"}
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            return r.text
        except Exception as e:
            print(f"    fetch error: {e}")
            return None

    def _extract(self, base_url: str, html: str) -> tuple[list[str], list[dict]]:
        soup = BeautifulSoup(html, "html.parser")
        links    = []
        datasets = []

        for tag in soup.find_all("a", href=True):
            href = urllib.parse.urljoin(base_url, tag["href"])
            text = tag.get_text(strip=True)

            # Candidate dataset links: direct file downloads
            if any(href.endswith(ext) for ext in
                   [".pdb", ".cif", ".gz", ".zip", ".tar", ".csv", ".json",
                    ".txt", ".tsv", ".npy", ".pt", ".h5"]):
                datasets.append({
                    "url":         href,
                    "description": text or Path(href).name,
                    "type":        "download",
                    "found_on":    base_url,
                    "source":      "crawler",
                })
            else:
                links.append(href)

        # Also scrape text for DOI/dataset mentions
        page_text = soup.get_text(" ", strip=True).lower()
        for kw in ["zenodo.org", "figshare", "osf.io", "github.com",
                   "drive.google", "dropbox.com", "supplementary"]:
            if kw in page_text:
                # find nearest URL mention
                idx = page_text.find(kw)
                snippet = page_text[max(0, idx-30):idx+80]
                datasets.append({
                    "url":         base_url,
                    "description": f"mentions '{kw}': ...{snippet}...",
                    "type":        "mention",
                    "found_on":    base_url,
                    "source":      "crawler",
                })

        return links, datasets

    def _is_relevant_url(self, url: str) -> bool:
        url_lower = url.lower()
        # Skip social, ads, CDN, etc.
        skip = ["twitter.com", "facebook.com", "linkedin.com", "youtube.com",
                "google.com/ads", "cdn.", "fonts.", "analytics", ".css", ".js",
                ".png", ".jpg", "#"]
        if any(s in url_lower for s in skip):
            return False
        # Prefer relevant domains
        good = ["rcsb.org", "uniprot.org", "ncbi.nlm.nih.gov", "ebi.ac.uk",
                "github.com", "zenodo.org", "figshare", "biorxiv.org",
                "nature.com", "science.org", "pnas.org", "acs.org",
                "sciencedirect", "pocketminer", "cryptosite", "durrantlab"]
        if any(g in url_lower for g in good):
            return True
        # Check keyword relevance
        return any(kw in url_lower for kw in self.RELEVANCE_KEYWORDS)


class CryptoSiteSource:
    """
    Targets the CryptoSite dataset (Cimermancic et al. 2016) and
    PocketMiner supplementary data — primary training set for the GNN.
    """

    name = "cryptosite"

    SEED_URLS = [
        "https://github.com/salilab/cryptosite",
        "https://github.com/durrantlab/pocketminer",
        "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4931009/",  # CryptoSite paper PMC
        "https://zenodo.org/search?q=cryptosite+cryptic+pocket",
        "https://zenodo.org/search?q=pocketminer",
    ]

    def fetch(self) -> list[dict]:
        crawler = RecursiveCrawler(self.SEED_URLS, max_depth=2, max_pages=30)
        results = crawler.crawl()
        for r in results:
            r["source"] = "cryptosite_crawler"
        print(f"  CryptoSite/PocketMiner crawler: {len(results)} dataset links")
        return results


class SCPDBSource:
    """
    sc-PDB: binding site database for pre-training the pocket scoring head.
    """

    name = "scpdb"

    SEED_URLS = [
        "http://bioinfo-pharma.u-strasbg.fr/scPDB/",
        "https://github.com/search?q=sc-pdb+binding+site",
        "https://zenodo.org/search?q=sc-pdb",
    ]

    def fetch(self) -> list[dict]:
        crawler = RecursiveCrawler(self.SEED_URLS, max_depth=1, max_pages=15)
        results = crawler.crawl()
        for r in results:
            r["source"] = "scpdb_crawler"
        print(f"  sc-PDB crawler: {len(results)} dataset links")
        return results


# ── catalog builder ────────────────────────────────────────────────────────────

class CatalogBuilder:
    def __init__(self):
        self.pdb_entries:   list[dict] = []
        self.dataset_links: list[dict] = []

    def add_pdb_entries(self, entries: list[dict]):
        for entry in entries:
            result = verify_pdb_entry(entry)
            entry["verification_passed"] = result.passed
            entry["verification_reason"] = result.reason
            entry["relevance_score"]     = result.score
            if result.passed:
                self.pdb_entries.append(entry)
            else:
                print(f"    FILTERED {entry.get('pdb_id')}: {result.reason}")

    def add_dataset_links(self, links: list[dict]):
        self.dataset_links.extend(links)

    def save(self) -> Path:
        catalog = {
            "generated_at":  datetime.utcnow().isoformat() + "Z",
            "pdb_entries":   sorted(self.pdb_entries,
                                    key=lambda x: x.get("relevance_score", 0),
                                    reverse=True),
            "dataset_links": sorted(self.dataset_links,
                                    key=lambda x: x.get("relevance_score", 0),
                                    reverse=True),
            "stats": {
                "pdb_count":     len(self.pdb_entries),
                "dataset_links": len(self.dataset_links),
                "top_pdb_ids":   [e["pdb_id"] for e in self.pdb_entries[:20]],
            }
        }
        catalog_path = CATALOG_DIR / "pcna_data_catalog.json"
        catalog_path.write_text(json.dumps(catalog, indent=2))

        # Download queue
        queue_lines = []
        for e in self.pdb_entries:
            queue_lines.append(e.get("download_url", ""))
        for d in self.dataset_links:
            if d.get("type") == "download":
                queue_lines.append(d.get("url", ""))
        queue_path = CATALOG_DIR / "download_queue.txt"
        queue_path.write_text("\n".join(filter(None, queue_lines)))

        # Human-readable report
        report = self._build_report(catalog)
        report_path = CATALOG_DIR / "crawl_report.md"
        report_path.write_text(report)

        return catalog_path

    def _build_report(self, catalog: dict) -> str:
        lines = [
            "# PCNA Data Crawl Report",
            f"Generated: {catalog['generated_at']}",
            "",
            f"## Summary",
            f"- PDB structures found (verified): {catalog['stats']['pdb_count']}",
            f"- External dataset links found: {catalog['stats']['dataset_links']}",
            "",
            "## Top PDB Structures",
            "| PDB ID | Score | Title | Resolution |",
            "|--------|-------|-------|------------|",
        ]
        for e in catalog["pdb_entries"][:30]:
            lines.append(
                f"| [{e['pdb_id']}](https://www.rcsb.org/structure/{e['pdb_id']}) "
                f"| {e.get('relevance_score', 0):.2f} "
                f"| {e.get('title', '')[:50]} "
                f"| {e.get('resolution_angstrom', 'N/A')} Å |"
            )
        lines += [
            "",
            "## External Dataset Links",
        ]
        for d in catalog["dataset_links"][:20]:
            lines.append(
                f"- [{d.get('description', '')[:60]}]({d.get('url', '')}) "
                f"(score: {d.get('relevance_score', 0):.2f}, source: {d.get('source', '')})"
            )
        lines += [
            "",
            "## Next Steps",
            "1. Run `python agents/pcna_crawler.py --download` to fetch top PDB files",
            "2. Check `data/catalog/download_queue.txt` for full download list",
            "3. Manually verify CryptoSite/PocketMiner links and download dataset",
            "4. Run `src/data_processing/parse_pdb.py` on downloaded structures",
        ]
        return "\n".join(lines)


def download_pdb_files(catalog_path: Path, limit: int = 10):
    """Download top-scored PDB files into data/raw/."""
    catalog = json.loads(catalog_path.read_text())
    entries = catalog["pdb_entries"][:limit]
    print(f"\nDownloading top {len(entries)} PDB files...")
    for e in entries:
        pdb_id = e["pdb_id"]
        url    = e.get("download_url") or RCSB_DOWNLOAD.format(pdb_id)
        dest   = PDB_RAW_DIR / f"{pdb_id}.pdb"
        if dest.exists():
            print(f"  {pdb_id} already exists, skipping")
            continue
        try:
            time.sleep(POLITE_DELAY)
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            dest.write_bytes(r.content)
            print(f"  downloaded {pdb_id} ({len(r.content)//1024} KB)")
        except Exception as ex:
            print(f"  failed {pdb_id}: {ex}")


# ── main ───────────────────────────────────────────────────────────────────────

ALL_SOURCES = {
    "rcsb":       RCSBSource,
    "uniprot":    UniProtSource,
    "cryptosite": CryptoSiteSource,
    "scpdb":      SCPDBSource,
}


def main():
    parser = argparse.ArgumentParser(description="PCNA training data crawler")
    parser.add_argument("--sources", nargs="+", default=list(ALL_SOURCES.keys()),
                        choices=list(ALL_SOURCES.keys()),
                        help="Which sources to query (default: all)")
    parser.add_argument("--download", action="store_true",
                        help="Also download top PDB files into data/raw/")
    parser.add_argument("--download-limit", type=int, default=10,
                        help="Max PDB files to download (default: 10)")
    args = parser.parse_args()

    print(f"=== PCNA Data Crawler — {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    print(f"Sources: {args.sources}\n")

    builder = CatalogBuilder()

    for source_name in args.sources:
        print(f"[{source_name.upper()}]")
        source = ALL_SOURCES[source_name]()
        results = source.fetch()

        if source_name in ("rcsb", "uniprot"):
            builder.add_pdb_entries(results)
        else:
            builder.add_dataset_links(results)
        print()

    print("Saving catalog...")
    catalog_path = builder.save()
    print(f"  → {catalog_path}")
    print(f"  → {CATALOG_DIR / 'download_queue.txt'}")
    print(f"  → {CATALOG_DIR / 'crawl_report.md'}")

    if args.download:
        download_pdb_files(catalog_path, limit=args.download_limit)

    stats = json.loads(catalog_path.read_text())["stats"]
    print(f"\nDone. {stats['pdb_count']} PDB structures, "
          f"{stats['dataset_links']} dataset links.")
    print(f"Top PDB IDs: {', '.join(stats['top_pdb_ids'][:10])}")


if __name__ == "__main__":
    main()
