"""
PCNA Training Data Crawler — Multi-Domain Edition
==================================================
Crawls 12 independent domain sources in parallel, funnels every result
through a 5-layer validation pipeline, and writes a verified catalog.

Domain sources
--------------
  Structural databases:
    RCSBSource      - RCSB PDB REST API (search + metadata)
    PDBESource      - EBI PDBe REST API (independent mirror)
    AlphaFoldSource - AlphaFold DB (predicted PCNA homologs)
    SIFTSSource     - SIFTS residue-level mapping (validates PDB-UniProt alignment)

  Sequence / annotation:
    UniProtSource   - UniProt P12004 cross-references
    NCBISource      - NCBI Entrez protein + PubMed records
    InterProSource  - InterPro domain annotations (P12004)

  Literature / preprints:
    PubMedSource    - PubMed full-text search for PCNA + cryptic pocket papers
    BioRxivSource   - bioRxiv preprints

  Dataset repositories:
    ZenodoSource    - Zenodo dataset search (CryptoSite, PocketMiner)
    GitHubSource    - GitHub repo crawl (salilab/cryptosite, durrantlab/pocketminer)

  Compound databases:
    PubChemSource   - AOH1996 compound record + assay cross-refs
    ChEMBLSource    - ChEMBL bioactivity for PCNA-targeted compounds

Validation pipeline (5 layers, every record must pass all)
-----------------------------------------------------------
  L1 Network      - HTTP 200, content-type, min file size, timeout
  L2 Format       - PDB/JSON/HTML schema check, ATOM records present
  L3 Structural   - resolution, Ca completeness, chain count, B-factor range
  L4 Biological   - UniProt cross-ref, organism filter, sequence keyword match
  L5 Provenance   - SHA256 checksum, deduplication, source chain audit trail

Usage
-----
  python agents/pcna_crawler.py                     # all sources, no download
  python agents/pcna_crawler.py --download          # fetch verified PDB files
  python agents/pcna_crawler.py --sources rcsb pdbe # specific sources
  python agents/pcna_crawler.py --workers 6         # parallel workers
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

# ── paths ───────────────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).parent.parent
CATALOG_DIR = REPO_ROOT / "data" / "catalog"
RAW_DIR     = REPO_ROOT / "data" / "raw"

CATALOG_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

# ── constants ───────────────────────────────────────────────────────────────────
PCNA_UNIPROT    = "P12004"
PCNA_GENE       = "PCNA"
AOH1996_NAME    = "AOH1996"
AOH1996_SMILES  = "CC1=CC2=C(C=C1)N(C(=O)C3=CC=CN=C3)C(=O)N2"

KNOWN_PCNA_IDS  = {"1W60", "8GLA", "1AXC", "1W61"}  # always accept
POLITE_DELAY    = 0.35    # seconds between calls per domain
MAX_RETRIES     = 3
BACKOFF_BASE    = 1.5     # exponential backoff multiplier

RCSB_SEARCH  = "https://search.rcsb.org/rcsbsearch/v2/query"
RCSB_ENTRY   = "https://data.rcsb.org/rest/v1/core/entry/{}"
RCSB_DL      = "https://files.rcsb.org/download/{}.pdb"
PDBE_ENTRY   = "https://www.ebi.ac.uk/pdbe/api/pdb/entry/summary/{}"
PDBE_SEARCH  = "https://www.ebi.ac.uk/pdbe/search/pdb/select"
ALPHAFOLD_DL = "https://alphafold.ebi.ac.uk/files/AF-{}-F1-model_v4.pdb"
UNIPROT_API  = "https://rest.uniprot.org/uniprotkb/{}.json"
NCBI_SEARCH  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_FETCH   = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
SIFTS_URL    = "https://www.ebi.ac.uk/pdbe/api/mappings/uniprot/{}"
INTERP_URL   = "https://www.ebi.ac.uk/interpro/api/protein/UniProt/{}"
ZENODO_API   = "https://zenodo.org/api/records"
PUBCHEM_CID  = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}/JSON"
CHEMBL_API   = "https://www.ebi.ac.uk/chembl/api/data/target/search.json"
BIORXIV_API  = "https://api.biorxiv.org/details/biorxiv/{}/{}/json"
PUBMED_SRCH  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


# ══════════════════════════════════════════════════════════════════════════════
# SHARED UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

class RateLimiter:
    """Per-domain simple rate limiter (min gap between calls)."""
    def __init__(self):
        self._last: dict[str, float] = defaultdict(float)

    def wait(self, domain: str, delay: float = POLITE_DELAY):
        elapsed = time.monotonic() - self._last[domain]
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self._last[domain] = time.monotonic()

_rate = RateLimiter()

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "GNN-PCNA-research/1.0 (academic; advay.awesomer@gmail.com)"})


def fetch(url: str, domain: str = "", *, method: str = "GET",
          json_body: Any = None, timeout: int = 20,
          rate_delay: float = POLITE_DELAY) -> Optional[requests.Response]:
    """HTTP fetch with rate limiting and exponential-backoff retry."""
    _rate.wait(domain or urllib.parse.urlparse(url).netloc, rate_delay)
    for attempt in range(MAX_RETRIES):
        try:
            if method == "POST":
                r = SESSION.post(url, json=json_body, timeout=timeout)
            else:
                r = SESSION.get(url, timeout=timeout)
            if r.status_code == 429:
                wait = int(r.headers.get("Retry-After", 5))
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                return None
            time.sleep(BACKOFF_BASE ** attempt)
    return None


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ══════════════════════════════════════════════════════════════════════════════
# DATA RECORDS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SourceRecord:
    """Universal record from any domain source."""
    uid:          str            # pdb_id, doi, url hash, etc.
    record_type:  str            # "pdb_structure" | "paper" | "dataset" | "compound"
    source:       str            # which source class produced this
    url:          str
    title:        str            = ""
    description:  str            = ""
    metadata:     dict           = field(default_factory=dict)
    download_url: str            = ""
    # Filled by validation pipeline
    validation:   dict           = field(default_factory=dict)
    passed:       bool           = False
    relevance:    float          = 0.0
    checksum:     str            = ""
    fetched_at:   str            = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


# ══════════════════════════════════════════════════════════════════════════════
# VALIDATION PIPELINE — 5 LAYERS
# ══════════════════════════════════════════════════════════════════════════════

class ValidationPipeline:
    """
    Every SourceRecord passes through all 5 layers.
    A failure at any layer sets passed=False and records the reason.
    Layers annotate record.validation with their findings.
    """

    PCNA_KEYWORDS = [
        "pcna", "proliferating cell nuclear antigen", "sliding clamp",
        "aoh1996", "cryptic pocket", "idcl", "interdomain connecting loop",
        "clamp loader", "dna polymerase", "pcna inhibitor", "atx-101",
        "pocketminer", "cryptosite", "cryptic binding",
    ]
    RELEVANT_ORGANISMS = {
        "homo sapiens", "human", "mus musculus", "saccharomyces cerevisiae",
        "xenopus laevis", "arabidopsis thaliana",  # PCNA homologs studied
    }

    # ── Layer 1: Network ─────────────────────────────────────────────────────
    def l1_network(self, record: SourceRecord, content: bytes,
                   content_type: str, status: int) -> bool:
        result = {}
        result["status_code"] = status
        result["content_type"] = content_type
        result["size_bytes"]   = len(content)

        if status != 200:
            result["fail"] = f"HTTP {status}"
            record.validation["l1"] = result
            return False
        if len(content) < 500:
            result["fail"] = f"response too small ({len(content)} bytes)"
            record.validation["l1"] = result
            return False
        # Content-type should not be error pages
        if "text/html" in content_type and record.record_type == "pdb_structure":
            snippet = content[:200].decode("utf-8", errors="ignore").lower()
            if "error" in snippet or "not found" in snippet:
                result["fail"] = "HTML error page returned instead of PDB"
                record.validation["l1"] = result
                return False

        result["ok"] = True
        record.validation["l1"] = result
        return True

    # ── Layer 2: Format ──────────────────────────────────────────────────────
    def l2_format(self, record: SourceRecord, content: bytes) -> bool:
        result = {}

        if record.record_type == "pdb_structure":
            text  = content.decode("utf-8", errors="ignore")
            lines = text.splitlines()
            atom_lines = [l for l in lines if l.startswith("ATOM")]
            hetatm     = [l for l in lines if l.startswith("HETATM")]
            result["atom_record_count"]   = len(atom_lines)
            result["hetatm_record_count"] = len(hetatm)
            if not atom_lines:
                result["fail"] = "no ATOM records — not a valid PDB"
                record.validation["l2"] = result
                return False
            # Check ATOM line width (PDB fixed-width format)
            malformed = sum(1 for l in atom_lines[:20] if len(l) < 54)
            if malformed > 5:
                result["fail"] = f"{malformed}/20 ATOM lines too short — corrupt PDB"
                record.validation["l2"] = result
                return False

        elif record.record_type == "paper":
            text = content.decode("utf-8", errors="ignore")
            result["char_count"] = len(text)
            if len(text) < 200:
                result["fail"] = "paper content too short"
                record.validation["l2"] = result
                return False

        elif record.record_type == "dataset":
            # For JSON datasets
            if record.url.endswith(".json"):
                try:
                    json.loads(content)
                except json.JSONDecodeError as e:
                    result["fail"] = f"invalid JSON: {e}"
                    record.validation["l2"] = result
                    return False

        result["ok"] = True
        record.validation["l2"] = result
        return True

    # ── Layer 3: Structural (PDB-specific) ───────────────────────────────────
    def l3_structural(self, record: SourceRecord, content: bytes) -> bool:
        result = {}

        if record.record_type != "pdb_structure":
            result["skipped"] = "not a PDB structure"
            record.validation["l3"] = result
            return True  # non-structure records pass this layer

        pdb_id = record.uid.upper()
        text   = content.decode("utf-8", errors="ignore")
        lines  = text.splitlines()

        # Chain count
        atom_lines = [l for l in lines if l.startswith("ATOM") and len(l) > 21]
        chains     = {l[21] for l in atom_lines}
        result["chains"]      = sorted(chains)
        result["chain_count"] = len(chains)

        # Resolution
        resolution = None
        for l in lines:
            if l.startswith("REMARK   2 RESOLUTION"):
                m = re.search(r"(\d+\.\d+)", l)
                if m:
                    resolution = float(m.group(1))
                    break
        result["resolution_angstrom"] = resolution

        # Resolution filter — bypass for known PCNA core structures
        if resolution is not None and resolution > 3.5 and pdb_id not in KNOWN_PCNA_IDS:
            result["fail"] = f"resolution {resolution}A > 3.5A"
            record.validation["l3"] = result
            return False

        # Ca completeness
        residue_ids = {(l[21], l[22:26].strip()) for l in atom_lines}
        ca_lines    = [l for l in atom_lines if l[12:16].strip() == "CA"]
        ca_res      = {(l[21], l[22:26].strip()) for l in ca_lines}
        completeness = len(ca_res) / max(len(residue_ids), 1)
        result["ca_completeness"]  = round(completeness, 3)
        result["residue_count"]    = len(residue_ids)

        if completeness < 0.88:
            result["fail"] = f"Ca completeness {completeness:.1%} < 88%"
            record.validation["l3"] = result
            return False

        # B-factor outlier check (extreme values indicate modeled/problematic regions)
        b_factors = []
        for l in atom_lines[:200]:
            try:
                b = float(l[60:66].strip())
                b_factors.append(b)
            except (ValueError, IndexError):
                pass
        if b_factors:
            mean_b = sum(b_factors) / len(b_factors)
            result["mean_b_factor"] = round(mean_b, 2)
            if mean_b > 150:
                result["warn"] = f"very high mean B-factor {mean_b:.1f} — low quality"
                # warn but don't fail

        result["ok"] = True
        record.validation["l3"] = result
        return True

    # ── Layer 4: Biological relevance ────────────────────────────────────────
    def l4_biological(self, record: SourceRecord) -> float:
        """Returns relevance score 0.0-1.0; sets record.relevance."""
        result  = {}
        score   = 0.0
        reasons = []

        # Known ground-truth structures always score 1.0
        if record.uid.upper() in KNOWN_PCNA_IDS:
            record.relevance          = 1.0
            result["score"]           = 1.0
            result["reason"]          = "known ground-truth structure"
            record.validation["l4"]   = result
            return 1.0

        # Keyword match in title + description
        text = (record.title + " " + record.description).lower()
        kw_hits = [kw for kw in self.PCNA_KEYWORDS if kw in text]
        if kw_hits:
            score += min(0.5, len(kw_hits) * 0.12)
            reasons.append(f"keywords: {kw_hits[:3]}")

        # Organism relevance
        organism = record.metadata.get("organism", "").lower()
        if any(org in organism for org in self.RELEVANT_ORGANISMS):
            score += 0.2
            reasons.append(f"relevant organism: {organism}")

        # Resolution bonus for structures
        if record.record_type == "pdb_structure":
            res = record.validation.get("l3", {}).get("resolution_angstrom")
            if res is not None:
                if res <= 2.0:
                    score += 0.2
                    reasons.append(f"high res {res}A")
                elif res <= 2.5:
                    score += 0.12
                elif res <= 3.5:
                    score += 0.05

        # UniProt cross-reference confirmed
        if record.metadata.get("uniprot_confirmed"):
            score += 0.15
            reasons.append("UniProt P12004 confirmed")

        # Source quality weighting
        source_weights = {
            "rcsb": 0.05, "pdbe": 0.05, "alphafold": 0.03,
            "uniprot": 0.05, "sifts": 0.04, "pubmed": 0.03,
            "zenodo": 0.04, "github": 0.04,
        }
        score += source_weights.get(record.source.split(":")[0], 0.0)

        score = min(score, 1.0)
        result["score"]  = round(score, 3)
        result["reason"] = "; ".join(reasons) if reasons else "no keyword match"
        record.validation["l4"] = result
        record.relevance         = score
        return score

    # ── Layer 5: Provenance & integrity ──────────────────────────────────────
    def l5_provenance(self, record: SourceRecord, content: bytes,
                      seen_checksums: set[str]) -> bool:
        result  = {}
        chk     = sha256(content)
        result["sha256"]     = chk
        result["fetched_at"] = datetime.now(timezone.utc).isoformat()

        if chk in seen_checksums:
            result["fail"] = "duplicate content (same checksum as prior record)"
            record.validation["l5"] = result
            return False

        seen_checksums.add(chk)
        record.checksum    = chk
        record.fetched_at  = result["fetched_at"]

        # Source audit trail
        result["source_chain"] = [record.source, record.url]
        result["ok"]           = True
        record.validation["l5"] = result
        return True

    # ── Full pipeline ─────────────────────────────────────────────────────────
    def run(self, record: SourceRecord, content: bytes,
            content_type: str, status: int,
            seen_checksums: set[str],
            min_relevance: float = 0.15) -> bool:
        """Run all 5 layers. Returns True iff record passes every layer."""
        if not self.l1_network(record, content, content_type, status):
            return False
        if not self.l2_format(record, content):
            return False
        if not self.l3_structural(record, content):
            return False
        relevance = self.l4_biological(record)
        if relevance < min_relevance and record.uid.upper() not in KNOWN_PCNA_IDS:
            record.validation["l4"]["fail"] = f"relevance {relevance:.2f} < {min_relevance}"
            return False
        if not self.l5_provenance(record, content, seen_checksums):
            return False
        record.passed = True
        return True


# ══════════════════════════════════════════════════════════════════════════════
# DOMAIN SOURCES
# ══════════════════════════════════════════════════════════════════════════════

class BaseSource:
    name = "base"
    rate_delay = POLITE_DELAY

    def fetch_all(self) -> list[SourceRecord]:
        raise NotImplementedError

    def _get(self, url: str, **kw) -> Optional[requests.Response]:
        return fetch(url, self.name, rate_delay=self.rate_delay, **kw)

    def _post(self, url: str, body: Any, **kw) -> Optional[requests.Response]:
        return fetch(url, self.name, method="POST", json_body=body,
                     rate_delay=self.rate_delay, **kw)

    def _record(self, uid: str, rtype: str, url: str, **kw) -> SourceRecord:
        return SourceRecord(uid=uid, record_type=rtype, source=self.name,
                            url=url, **kw)


# ── RCSB PDB ─────────────────────────────────────────────────────────────────
class RCSBSource(BaseSource):
    name = "rcsb"

    QUERIES = [
        ("uniprot", {
            "query": {
                "type": "terminal", "service": "text",
                "parameters": {
                    "attribute": "rcsb_polymer_entity_container_identifiers"
                                 ".reference_sequence_identifiers.database_accession",
                    "operator": "exact_match", "negation": False,
                    "value": PCNA_UNIPROT,
                }
            },
            "return_type": "entry",
            "request_options": {"paginate": {"start": 0, "rows": 250}},
        }),
        ("keyword_pcna_cryptic", {
            "query": {
                "type": "group", "logical_operator": "and",
                "nodes": [
                    {"type": "terminal", "service": "full_text",
                     "parameters": {"value": "PCNA"}},
                    {"type": "terminal", "service": "full_text",
                     "parameters": {"value": "cryptic pocket"}},
                ]
            },
            "return_type": "entry",
            "request_options": {"paginate": {"start": 0, "rows": 50}},
        }),
        ("keyword_sliding_clamp", {
            "query": {"type": "terminal", "service": "full_text",
                      "parameters": {"value": "sliding clamp cryptic allosteric"}},
            "return_type": "entry",
            "request_options": {"paginate": {"start": 0, "rows": 50}},
        }),
    ]

    def fetch_all(self) -> list[SourceRecord]:
        seen_ids: set[str] = set()
        records: list[SourceRecord] = []

        for label, query in self.QUERIES:
            r = self._post(RCSB_SEARCH, query)
            if not r:
                print(f"  [{self.name}] {label}: request failed")
                continue
            hits = r.json().get("result_set", [])
            print(f"  [{self.name}] {label}: {len(hits)} hits")
            for hit in hits:
                pdb_id = hit.get("identifier", "").split("_")[0].upper()
                if pdb_id and pdb_id not in seen_ids:
                    seen_ids.add(pdb_id)
                    meta = self._fetch_meta(pdb_id)
                    rec  = self._record(
                        pdb_id, "pdb_structure",
                        f"https://www.rcsb.org/structure/{pdb_id}",
                        title        = meta.get("title", ""),
                        download_url = RCSB_DL.format(pdb_id),
                        metadata     = meta,
                    )
                    records.append(rec)

        # Always include known structures
        for pid in KNOWN_PCNA_IDS - seen_ids:
            meta = self._fetch_meta(pid)
            records.append(self._record(
                pid, "pdb_structure",
                f"https://www.rcsb.org/structure/{pid}",
                title=meta.get("title", ""), download_url=RCSB_DL.format(pid),
                metadata=meta,
            ))

        return records

    def _fetch_meta(self, pdb_id: str) -> dict:
        r = self._get(RCSB_ENTRY.format(pdb_id))
        if not r:
            return {}
        try:
            d = r.json()
            return {
                "title":       d.get("struct", {}).get("title", ""),
                "resolution":  (d.get("refine") or [{}])[0].get("ls_d_res_high"),
                "organism":    " ".join(
                    s.get("pdbx_description", "")
                    for s in d.get("rcsb_entity_source_organism", [])
                ),
                "method":      (d.get("exptl") or [{}])[0].get("method", ""),
                "source":      "rcsb_meta",
            }
        except Exception:
            return {}


# ── EBI PDBe ─────────────────────────────────────────────────────────────────
class PDBESource(BaseSource):
    name = "pdbe"

    def fetch_all(self) -> list[SourceRecord]:
        records: list[SourceRecord] = []

        # Search PDBe for PCNA (Solr-based)
        params = {
            "q": "molecule_name:PCNA OR molecule_name:proliferating",
            "fl": "pdb_id,title,resolution,organism_scientific_name",
            "rows": 200, "wt": "json",
        }
        r = self._get(PDBE_SEARCH, timeout=20)
        if r:
            try:
                docs = r.json().get("response", {}).get("docs", [])
                print(f"  [{self.name}] Solr search: {len(docs)} hits")
                seen: set[str] = set()
                for doc in docs:
                    pid = doc.get("pdb_id", "").upper()
                    if pid and pid not in seen:
                        seen.add(pid)
                        records.append(self._record(
                            pid, "pdb_structure",
                            f"https://www.ebi.ac.uk/pdbe/entry/pdb/{pid}",
                            title        = doc.get("title", ""),
                            download_url = RCSB_DL.format(pid),
                            metadata     = {
                                "resolution": doc.get("resolution"),
                                "organism":   doc.get("organism_scientific_name", ""),
                                "source":     "pdbe_solr",
                            },
                        ))
            except Exception:
                pass

        # Also fetch summary for known structures from PDBe (independent validation)
        for pid in KNOWN_PCNA_IDS:
            r2 = self._get(PDBE_ENTRY.format(pid.lower()))
            if r2:
                try:
                    data = r2.json().get(pid.lower(), {})
                    entry = (list(data.values()) or [{}])[0]
                    rec = self._record(
                        pid, "pdb_structure",
                        f"https://www.ebi.ac.uk/pdbe/entry/pdb/{pid}",
                        title        = entry.get("title", ""),
                        download_url = RCSB_DL.format(pid),
                        metadata     = {
                            "resolution": entry.get("resolution"),
                            "organism":   entry.get("organism_scientific_name", ""),
                            "source":     "pdbe_api",
                            "pdbe_confirmed": True,
                        },
                    )
                    records.append(rec)
                except Exception:
                    pass

        print(f"  [{self.name}] total: {len(records)}")
        return records


# ── AlphaFold DB ──────────────────────────────────────────────────────────────
class AlphaFoldSource(BaseSource):
    """Fetch AlphaFold predicted structures for PCNA homologs."""
    name = "alphafold"

    # Human PCNA + select homologs (UniProt accessions)
    TARGETS = [
        ("P12004", "Human PCNA"),
        ("P15873", "Mouse PCNA"),
        ("P04448", "S. cerevisiae PCNA (POL30)"),
        ("P15252", "X. laevis PCNA"),
        ("O15146", "Human PCNA2-like"),
    ]

    def fetch_all(self) -> list[SourceRecord]:
        records = []
        for acc, desc in self.TARGETS:
            url = ALPHAFOLD_DL.format(acc)
            r   = self._get(url)
            if r and r.status_code == 200:
                rec = self._record(
                    f"AF-{acc}", "pdb_structure", url,
                    title        = f"AlphaFold {desc}",
                    description  = f"Predicted structure for UniProt {acc}",
                    download_url = url,
                    metadata     = {"uniprot": acc, "source": "alphafold_db",
                                    "organism": desc, "is_predicted": True},
                )
                records.append(rec)
        print(f"  [{self.name}] {len(records)} AlphaFold structures found")
        return records


# ── SIFTS ─────────────────────────────────────────────────────────────────────
class SIFTSSource(BaseSource):
    """SIFTS: Structure Integration with Function, Taxonomy and Sequence.
    Provides authoritative PDB->UniProt residue-level mappings.
    Used as cross-validation that PDB entries are truly PCNA."""
    name = "sifts"

    def fetch_all(self) -> list[SourceRecord]:
        r = self._get(SIFTS_URL.format(PCNA_UNIPROT))
        if not r:
            print(f"  [{self.name}] request failed")
            return []
        try:
            data    = r.json()
            pdb_ids = list(data.get(PCNA_UNIPROT, {}).get("PDB", {}).keys())
            print(f"  [{self.name}] {len(pdb_ids)} PDB entries map to P12004")
            records = []
            for pid in pdb_ids:
                pid = pid.upper()
                records.append(self._record(
                    pid, "pdb_structure",
                    f"https://www.ebi.ac.uk/pdbe/entry/pdb/{pid}",
                    title        = f"SIFTS-verified PCNA structure",
                    download_url = RCSB_DL.format(pid),
                    metadata     = {"uniprot_confirmed": True,
                                    "uniprot": PCNA_UNIPROT,
                                    "source": "sifts"},
                ))
            return records
        except Exception as e:
            print(f"  [{self.name}] parse error: {e}")
            return []


# ── UniProt ───────────────────────────────────────────────────────────────────
class UniProtSource(BaseSource):
    name = "uniprot"

    def fetch_all(self) -> list[SourceRecord]:
        r = self._get(UNIPROT_API.format(PCNA_UNIPROT))
        if not r:
            return []
        try:
            data    = r.json()
            pdb_ids = []
            for xref in data.get("uniProtKBCrossReferences", []):
                if xref.get("database") == "PDB":
                    pdb_ids.append(xref["id"].upper())
            # Fallback key
            if not pdb_ids:
                for xref in data.get("dbReferences", []):
                    if xref.get("type") == "PDB":
                        pdb_ids.append(xref["id"].upper())
            print(f"  [{self.name}] {len(pdb_ids)} PDB cross-refs for P12004")
            records = []
            for pid in set(pdb_ids):
                records.append(self._record(
                    pid, "pdb_structure",
                    f"https://www.rcsb.org/structure/{pid}",
                    download_url = RCSB_DL.format(pid),
                    metadata     = {"uniprot_confirmed": True,
                                    "uniprot": PCNA_UNIPROT, "source": "uniprot"},
                ))
            return records
        except Exception as e:
            print(f"  [{self.name}] error: {e}")
            return []


# ── NCBI ─────────────────────────────────────────────────────────────────────
class NCBISource(BaseSource):
    """Search NCBI Protein + PubMed for PCNA structures and related papers."""
    name = "ncbi"
    rate_delay = 0.4   # NCBI allows 3 req/s unauthenticated

    def fetch_all(self) -> list[SourceRecord]:
        records = []
        records += self._search_protein()
        records += self._search_pubmed()
        return records

    def _search_protein(self) -> list[SourceRecord]:
        r = self._get(NCBI_SEARCH, timeout=15)
        params = {
            "db": "protein", "term": "PCNA[Gene Name] AND Homo sapiens[Organism]",
            "retmax": 50, "retmode": "json",
        }
        r = self._get(NCBI_SEARCH + "?" + urllib.parse.urlencode(params))
        if not r:
            return []
        try:
            ids   = r.json()["esearchresult"]["idlist"]
            print(f"  [{self.name}] protein: {len(ids)} NCBI protein IDs")
            return [self._record(
                f"NCBI:{nid}", "paper",
                f"https://www.ncbi.nlm.nih.gov/protein/{nid}",
                description = "NCBI protein record for PCNA",
                metadata    = {"ncbi_id": nid, "db": "protein"},
            ) for nid in ids[:20]]
        except Exception:
            return []

    def _search_pubmed(self) -> list[SourceRecord]:
        queries = [
            "PCNA cryptic pocket GNN",
            "PCNA AOH1996 binding site molecular dynamics",
            "PCNA PocketMiner graph neural network",
            "sliding clamp allosteric pocket",
        ]
        records = []
        for q in queries:
            params = {"db": "pubmed", "term": q, "retmax": 10, "retmode": "json"}
            r = self._get(PUBMED_SRCH + "?" + urllib.parse.urlencode(params))
            if not r:
                continue
            try:
                pmids = r.json()["esearchresult"]["idlist"]
                for pmid in pmids:
                    records.append(self._record(
                        f"PMID:{pmid}", "paper",
                        f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        description = f"PubMed: {q}",
                        metadata    = {"pmid": pmid, "query": q},
                    ))
            except Exception:
                continue
        print(f"  [{self.name}] pubmed: {len(records)} records")
        return records


# ── InterPro ──────────────────────────────────────────────────────────────────
class InterProSource(BaseSource):
    """InterPro domain annotations for P12004 — confirms protein family."""
    name = "interpro"

    def fetch_all(self) -> list[SourceRecord]:
        r = self._get(INTERP_URL.format(PCNA_UNIPROT))
        if not r:
            return []
        try:
            data    = r.json()
            entries = data.get("results", [])
            records = []
            for e in entries[:10]:
                meta   = e.get("metadata", {})
                rec_id = meta.get("accession", "")
                if rec_id:
                    records.append(self._record(
                        f"IPR:{rec_id}", "dataset",
                        f"https://www.ebi.ac.uk/interpro/entry/{rec_id}",
                        title       = meta.get("name", {}).get("name", ""),
                        description = f"InterPro family for PCNA (P12004)",
                        metadata    = {"interpro_id": rec_id, "type": meta.get("type")},
                    ))
            print(f"  [{self.name}] {len(records)} InterPro entries for P12004")
            return records
        except Exception as e:
            print(f"  [{self.name}] error: {e}")
            return []


# ── Zenodo ────────────────────────────────────────────────────────────────────
class ZenodoSource(BaseSource):
    name = "zenodo"

    QUERIES = [
        "cryptosite cryptic pocket protein",
        "pocketminer graph neural network protein",
        "PCNA training dataset",
        "sc-pdb binding site",
        "molecular dynamics PCNA",
    ]

    def fetch_all(self) -> list[SourceRecord]:
        records = []
        seen:  set[str] = set()
        for q in self.QUERIES:
            r = self._get(ZENODO_API + f"?q={urllib.parse.quote(q)}&size=10&sort=mostrecent")
            if not r:
                continue
            try:
                hits = r.json().get("hits", {}).get("hits", [])
                for hit in hits:
                    doi = hit.get("doi", str(hit.get("id", "")))
                    if doi in seen:
                        continue
                    seen.add(doi)
                    files = hit.get("files", [])
                    dl    = files[0].get("links", {}).get("self", "") if files else ""
                    records.append(self._record(
                        doi, "dataset",
                        hit.get("links", {}).get("html", ""),
                        title       = hit.get("metadata", {}).get("title", ""),
                        description = hit.get("metadata", {}).get("description", "")[:200],
                        download_url = dl,
                        metadata    = {
                            "doi": doi, "query": q,
                            "keywords": hit.get("metadata", {}).get("keywords", []),
                            "source": "zenodo",
                        },
                    ))
            except Exception:
                continue
        print(f"  [{self.name}] {len(records)} dataset records")
        return records


# ── GitHub ────────────────────────────────────────────────────────────────────
class GitHubSource(BaseSource):
    """Crawl key GitHub repos for dataset download links and supplementary files."""
    name = "github"

    REPOS = [
        ("salilab", "cryptosite",   "CryptoSite benchmark dataset"),
        ("durrantlab", "pocketminer", "PocketMiner GNN training data"),
        ("rcsb",       "rcsb-api-tools", "RCSB API tooling"),
    ]

    def fetch_all(self) -> list[SourceRecord]:
        records = []
        for org, repo, desc in self.REPOS:
            records += self._crawl_repo(org, repo, desc)
        return records

    def _crawl_repo(self, org: str, repo: str, desc: str) -> list[SourceRecord]:
        api_url  = f"https://api.github.com/repos/{org}/{repo}"
        html_url = f"https://github.com/{org}/{repo}"

        # Repo metadata
        r = self._get(api_url)
        repo_meta: dict = {}
        if r:
            try:
                repo_meta = r.json()
            except Exception:
                pass

        # Releases (dataset downloads)
        r2 = self._get(f"{api_url}/releases")
        releases = []
        if r2:
            try:
                for rel in r2.json()[:5]:
                    for asset in rel.get("assets", []):
                        releases.append(self._record(
                            f"gh:{org}/{repo}/{asset['name']}", "dataset",
                            asset["browser_download_url"],
                            title        = f"{repo} release asset: {asset['name']}",
                            description  = desc,
                            download_url = asset["browser_download_url"],
                            metadata     = {"repo": f"{org}/{repo}", "release": rel.get("tag_name"), "source": "github_release"},
                        ))
            except Exception:
                pass

        # README links
        r3 = self._get(f"{api_url}/readme",
                       **{"headers": {"Accept": "application/vnd.github.raw"}})
        readme_records = []
        if r3:
            readme_text = r3.text
            urls = re.findall(r'https?://\S+', readme_text)
            for url in urls:
                url = url.rstrip(")")
                if any(url.endswith(ext) for ext in [".zip", ".tar.gz", ".gz", ".pdb", ".csv", ".json"]):
                    readme_records.append(self._record(
                        f"gh_readme:{sha256(url.encode())[:8]}", "dataset", url,
                        title       = f"Dataset link from {org}/{repo} README",
                        description = desc,
                        download_url = url,
                        metadata    = {"repo": f"{org}/{repo}", "source": "github_readme"},
                    ))

        all_recs = releases + readme_records
        print(f"  [{self.name}] {org}/{repo}: {len(all_recs)} records")
        return all_recs


# ── PubMed / PMC ──────────────────────────────────────────────────────────────
class PubMedSource(BaseSource):
    """Search PubMed for PCNA / cryptic pocket papers with open data."""
    name  = "pubmed"
    TERMS = [
        "PCNA cryptic pocket GNN graph neural network",
        "PCNA AOH1996 molecular dynamics simulation",
        "PocketMiner cryptic binding site prediction",
        "sliding clamp inhibitor allosteric",
        "PCNA structure AlphaFold dynamics",
    ]

    def fetch_all(self) -> list[SourceRecord]:
        records: list[SourceRecord] = []
        seen: set[str] = set()
        for term in self.TERMS:
            params = {"db": "pubmed", "term": term, "retmax": 8,
                      "retmode": "json", "usehistory": "n"}
            r = self._get(PUBMED_SRCH + "?" + urllib.parse.urlencode(params))
            if not r:
                continue
            try:
                pmids = r.json()["esearchresult"]["idlist"]
                for pmid in pmids:
                    if pmid in seen:
                        continue
                    seen.add(pmid)
                    records.append(self._record(
                        f"PMID:{pmid}", "paper",
                        f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        description = term,
                        download_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/pmid/{pmid}/",
                        metadata    = {"pmid": pmid, "query": term, "source": "pubmed"},
                    ))
            except Exception:
                continue
        print(f"  [{self.name}] {len(records)} papers")
        return records


# ── bioRxiv ───────────────────────────────────────────────────────────────────
class BioRxivSource(BaseSource):
    name = "biorxiv"

    QUERIES = [
        "PCNA cryptic pocket",
        "graph neural network protein pocket",
        "PocketMiner",
        "molecular dynamics cryptic",
    ]

    def fetch_all(self) -> list[SourceRecord]:
        records: list[SourceRecord] = []
        seen: set[str] = set()
        start = "2020-01-01"
        end   = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        for q in self.QUERIES:
            url = f"https://api.biorxiv.org/details/biorxiv/{start}/{end}/0/json"
            r   = self._get(url)
            if not r:
                continue
            try:
                for paper in r.json().get("collection", []):
                    abstract = paper.get("abstract", "").lower()
                    title    = paper.get("title", "").lower()
                    if not any(kw in abstract or kw in title
                               for kw in ["pcna", "cryptic pocket", "pocketminer", "sliding clamp"]):
                        continue
                    doi = paper.get("doi", "")
                    if doi in seen:
                        continue
                    seen.add(doi)
                    records.append(self._record(
                        doi, "paper",
                        f"https://www.biorxiv.org/content/{doi}",
                        title       = paper.get("title", ""),
                        description = paper.get("abstract", "")[:200],
                        metadata    = {"doi": doi, "authors": paper.get("authors"),
                                       "date": paper.get("date"), "source": "biorxiv"},
                    ))
            except Exception:
                continue

        print(f"  [{self.name}] {len(records)} preprints")
        return records


# ── PubChem ───────────────────────────────────────────────────────────────────
class PubChemSource(BaseSource):
    """Fetch AOH1996 compound data and PCNA bioactivity records."""
    name = "pubchem"

    def fetch_all(self) -> list[SourceRecord]:
        records = []

        # AOH1996 compound
        r = self._get(PUBCHEM_CID.format(urllib.parse.quote(AOH1996_NAME)))
        if r:
            try:
                compounds = r.json().get("PC_Compounds", [])
                for c in compounds[:1]:
                    cid = c.get("id", {}).get("id", {}).get("cid", "")
                    records.append(self._record(
                        f"CID:{cid}", "dataset",
                        f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
                        title       = f"AOH1996 (CID {cid})",
                        description = "PCNA inhibitor compound used as ground truth for pocket labeling",
                        metadata    = {"cid": cid, "smiles": AOH1996_SMILES,
                                       "source": "pubchem"},
                    ))
            except Exception:
                pass

        # Bioassay search for PCNA
        params = {"q": f"target_chembl_id&target_component__accession={PCNA_UNIPROT}",
                  "format": "json", "limit": 20}
        r2 = self._get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/target/ProteinGI/json?q=PCNA")
        # Use a simplified lookup instead
        records.append(self._record(
            "PCNA:bioassay", "dataset",
            f"https://pubchem.ncbi.nlm.nih.gov/protein/{PCNA_UNIPROT}/bioactivities",
            title       = "PCNA bioactivity data (PubChem)",
            description = "All bioassay records for human PCNA from PubChem",
            metadata    = {"uniprot": PCNA_UNIPROT, "source": "pubchem_bioassay"},
        ))

        print(f"  [{self.name}] {len(records)} compound/assay records")
        return records


# ── ChEMBL ────────────────────────────────────────────────────────────────────
class ChEMBLSource(BaseSource):
    """ChEMBL bioactivity data for PCNA-targeted compounds."""
    name = "chembl"

    def fetch_all(self) -> list[SourceRecord]:
        r = self._get(f"{CHEMBL_API}?q=PCNA&format=json&limit=10")
        if not r:
            return []
        records = []
        try:
            targets = r.json().get("targets", [])
            for t in targets:
                chembl_id = t.get("target_chembl_id", "")
                if chembl_id:
                    records.append(self._record(
                        f"CHEMBL:{chembl_id}", "dataset",
                        f"https://www.ebi.ac.uk/chembl/target_report_card/{chembl_id}/",
                        title       = t.get("pref_name", ""),
                        description = f"ChEMBL target record for PCNA",
                        metadata    = {"chembl_id": chembl_id,
                                       "organism": t.get("organism", ""),
                                       "target_type": t.get("target_type", ""),
                                       "source": "chembl"},
                    ))
        except Exception as e:
            print(f"  [{self.name}] error: {e}")
        print(f"  [{self.name}] {len(records)} target records")
        return records


# ══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════

ALL_SOURCES: dict[str, type[BaseSource]] = {
    "rcsb":       RCSBSource,
    "pdbe":       PDBESource,
    "alphafold":  AlphaFoldSource,
    "sifts":      SIFTSSource,
    "uniprot":    UniProtSource,
    "ncbi":       NCBISource,
    "interpro":   InterProSource,
    "zenodo":     ZenodoSource,
    "github":     GitHubSource,
    "pubmed":     PubMedSource,
    "biorxiv":    BioRxivSource,
    "pubchem":    PubChemSource,
    "chembl":     ChEMBLSource,
}


class CrawlerOrchestrator:
    def __init__(self, sources: list[str], workers: int = 6,
                 min_relevance: float = 0.15):
        self.sources       = sources
        self.workers       = workers
        self.min_relevance = min_relevance
        self.pipeline      = ValidationPipeline()
        self.seen_checksums: set[str] = set()
        self.seen_uids:     set[str] = set()

    def run(self) -> tuple[list[SourceRecord], list[SourceRecord]]:
        """Run all sources in parallel. Returns (passed, failed) lists."""
        all_records: list[SourceRecord] = []

        # Parallel source fetching
        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            futures = {
                ex.submit(ALL_SOURCES[name]().fetch_all): name
                for name in self.sources
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    recs = future.result()
                    all_records.extend(recs)
                except Exception as e:
                    print(f"  [!] {name} source error: {e}")

        print(f"\nTotal records collected: {len(all_records)}")
        print("Running 5-layer validation pipeline...")

        # Deduplicate by UID before validation
        deduped: list[SourceRecord] = []
        for rec in all_records:
            if rec.uid not in self.seen_uids:
                self.seen_uids.add(rec.uid)
                deduped.append(rec)

        print(f"After UID dedup: {len(deduped)} unique records")

        passed: list[SourceRecord] = []
        failed: list[SourceRecord] = []

        for i, rec in enumerate(deduped, 1):
            dl_url = rec.download_url or rec.url
            r = fetch(dl_url, rec.source, timeout=25)

            if r is None:
                rec.validation["l1"] = {"fail": "request failed/timeout"}
                failed.append(rec)
                if i % 20 == 0:
                    print(f"  validated {i}/{len(deduped)} ...")
                continue

            ok = self.pipeline.run(
                rec, r.content,
                r.headers.get("Content-Type", ""),
                r.status_code,
                self.seen_checksums,
                min_relevance=self.min_relevance,
            )
            (passed if ok else failed).append(rec)

            if i % 20 == 0:
                print(f"  validated {i}/{len(deduped)} — pass={len(passed)} fail={len(failed)}")

        return passed, failed

    def save(self, passed: list[SourceRecord],
             failed: list[SourceRecord]) -> Path:
        """Write catalog JSON, download queue, and Markdown report."""
        now = datetime.now(timezone.utc).isoformat()

        # Group by type and source
        by_type: dict[str, list] = defaultdict(list)
        for r in passed:
            by_type[r.record_type].append(r.to_dict())

        catalog = {
            "generated_at": now,
            "crawler_version": "2.0-multidomain",
            "sources_queried": self.sources,
            "stats": {
                "total_collected": len(passed) + len(failed),
                "passed_validation": len(passed),
                "failed_validation": len(failed),
                "by_type": {k: len(v) for k, v in by_type.items()},
                "by_source": dict(
                    sorted(
                        ((s, sum(1 for r in passed if r.source == s))
                         for s in set(r.source for r in passed)),
                        key=lambda x: -x[1]
                    )
                ),
            },
            "passed": sorted(
                [r.to_dict() for r in passed],
                key=lambda x: -x.get("relevance", 0),
            ),
            "failed_summary": [
                {"uid": r.uid, "source": r.source,
                 "fail_layer": next(
                     (k for k, v in r.validation.items() if "fail" in v), "?"),
                 "reason": next(
                     (v["fail"] for v in r.validation.values()
                      if isinstance(v, dict) and "fail" in v), "unknown")}
                for r in failed
            ],
        }

        cat_path = CATALOG_DIR / "pcna_data_catalog.json"
        cat_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")

        # Download queue — only PDB structures that passed
        dl_lines = [
            r.download_url for r in passed
            if r.record_type == "pdb_structure" and r.download_url
        ]
        (CATALOG_DIR / "download_queue.txt").write_text(
            "\n".join(dl_lines), encoding="utf-8")

        # Report
        report = self._report(catalog, passed, failed)
        (CATALOG_DIR / "crawl_report.md").write_text(report, encoding="utf-8")

        print(f"\nCatalog  -> {cat_path}")
        print(f"Queue    -> {CATALOG_DIR / 'download_queue.txt'} ({len(dl_lines)} PDB files)")
        print(f"Report   -> {CATALOG_DIR / 'crawl_report.md'}")
        return cat_path

    @staticmethod
    def _report(catalog: dict, passed: list[SourceRecord],
                failed: list[SourceRecord]) -> str:
        stats = catalog["stats"]
        lines = [
            "# PCNA Multi-Domain Crawl Report",
            f"Generated: {catalog['generated_at']}",
            f"Crawler version: {catalog['crawler_version']}",
            "",
            "## Validation Summary",
            f"| | Count |",
            f"|---|---|",
            f"| Total collected | {stats['total_collected']} |",
            f"| Passed all 5 layers | {stats['passed_validation']} |",
            f"| Failed validation | {stats['failed_validation']} |",
            "",
            "## Records by Source",
            "| Source | Passed |",
            "|---|---|",
        ]
        for src, cnt in stats["by_source"].items():
            lines.append(f"| {src} | {cnt} |")

        lines += [
            "",
            "## Records by Type",
            "| Type | Count |",
            "|---|---|",
        ]
        for t, cnt in stats["by_type"].items():
            lines.append(f"| {t} | {cnt} |")

        # Top PDB structures
        structs = [r for r in passed if r.record_type == "pdb_structure"]
        lines += [
            "",
            f"## Top PDB Structures ({len(structs)} total)",
            "| PDB ID | Score | Source | Resolution | UniProt | Notes |",
            "|---|---|---|---|---|---|",
        ]
        for r in sorted(structs, key=lambda x: -x.relevance)[:30]:
            res  = r.validation.get("l3", {}).get("resolution_angstrom", "?")
            unip = "YES" if r.metadata.get("uniprot_confirmed") else "-"
            pred = " (predicted)" if r.metadata.get("is_predicted") else ""
            lines.append(
                f"| [{r.uid}](https://www.rcsb.org/structure/{r.uid}) "
                f"| {r.relevance:.2f} | {r.source} | {res} A | {unip} | {r.title[:40]}{pred} |"
            )

        # Papers
        papers = [r for r in passed if r.record_type == "paper"]
        if papers:
            lines += ["", f"## Papers Found ({len(papers)})", ""]
            for p in papers[:15]:
                lines.append(f"- [{p.title or p.uid}]({p.url})  ({p.source})")

        # Datasets
        datasets = [r for r in passed if r.record_type == "dataset"]
        if datasets:
            lines += ["", f"## Datasets Found ({len(datasets)})", ""]
            for d in datasets[:15]:
                lines.append(f"- [{d.title or d.uid}]({d.url})  (score={d.relevance:.2f})")

        # Failure breakdown
        fail_layers: dict[str, int] = defaultdict(int)
        for r in failed:
            layer = next(
                (k for k, v in r.validation.items()
                 if isinstance(v, dict) and "fail" in v), "unknown")
            fail_layers[layer] += 1

        lines += [
            "",
            "## Validation Failures by Layer",
            "| Layer | Failed |",
            "|---|---|",
        ]
        for layer, cnt in sorted(fail_layers.items()):
            lines.append(f"| {layer} | {cnt} |")

        lines += [
            "",
            "## Next Steps",
            "1. `python -m src.data_processing.fetch_structures --catalog data/catalog/pcna_data_catalog.json --download`",
            "2. Review `data/catalog/download_queue.txt` for all verified PDB download URLs",
            "3. Manually check GitHub/Zenodo dataset links for CryptoSite download",
            "4. Implement `src/data_processing/parse_pdb.py` — 90 stripped structures waiting",
        ]
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# DOWNLOAD
# ══════════════════════════════════════════════════════════════════════════════

def download_verified(catalog_path: Path, limit: int = 50,
                      min_relevance: float = 0.3):
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    structs = [r for r in catalog["passed"]
               if r["record_type"] == "pdb_structure"
               and r.get("relevance", 0) >= min_relevance][:limit]
    print(f"\nDownloading {len(structs)} verified PDB structures...")
    for r in structs:
        uid  = r["uid"].split("_")[0].upper()[:4]  # handle AF- prefixes
        dest = RAW_DIR / f"{uid}.pdb"
        if dest.exists():
            print(f"  -- {uid} exists")
            continue
        url = r.get("download_url") or RCSB_DL.format(uid)
        resp = fetch(url, "download", timeout=30)
        if resp:
            dest.write_bytes(resp.content)
            print(f"  OK {uid}  ({len(resp.content)//1024} KB)")
        else:
            print(f"  FAIL {uid}")
        time.sleep(0.3)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="PCNA multi-domain crawler with 5-layer validation")
    parser.add_argument("--sources", nargs="+",
                        default=list(ALL_SOURCES.keys()),
                        choices=list(ALL_SOURCES.keys()),
                        help="Domain sources to query (default: all 13)")
    parser.add_argument("--workers", type=int, default=6,
                        help="Parallel source workers (default: 6)")
    parser.add_argument("--min-relevance", type=float, default=0.15,
                        help="Minimum L4 relevance score to pass (default: 0.15)")
    parser.add_argument("--download", action="store_true",
                        help="Also download verified PDB files")
    parser.add_argument("--download-limit", type=int, default=50)
    args = parser.parse_args()

    print(f"=== PCNA Multi-Domain Crawler v2.0 ===")
    print(f"Sources ({len(args.sources)}): {', '.join(args.sources)}")
    print(f"Workers: {args.workers}  |  Min relevance: {args.min_relevance}\n")

    orch = CrawlerOrchestrator(args.sources, args.workers, args.min_relevance)
    passed, failed = orch.run()

    print(f"\nValidation complete: {len(passed)} passed / {len(failed)} failed")
    catalog_path = orch.save(passed, failed)

    if args.download:
        download_verified(catalog_path, args.download_limit, args.min_relevance)

    stats = json.loads(catalog_path.read_text(encoding="utf-8"))["stats"]
    print(f"\nDone. Passed={stats['passed_validation']}  "
          f"Failed={stats['failed_validation']}")
    print(f"By source: {stats['by_source']}")


if __name__ == "__main__":
    main()
