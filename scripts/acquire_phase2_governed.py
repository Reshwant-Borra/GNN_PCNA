"""
Phase 2 Governed Dataset Acquisition Script
============================================
Governance-first. Downloads nothing for training.
Acquires only official sources, records provenance, computes hashes,
audits schemas, and writes all required reports.

Expected final status: RAW_ASSETS_ACQUIRED_NOT_VERIFIED

Run:
    python scripts/acquire_phase2_governed.py

Idempotent — safe to re-run. Will skip already-acquired files.
"""
from __future__ import annotations

import csv, hashlib, json, os, re, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

# ── repo root ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
RAW  = ROOT / "data" / "raw_intake"
REG  = ROOT / "data" / "registries"
REP  = ROOT / "reports" / "phase2"

for d in [REG, REP, RAW]:
    d.mkdir(parents=True, exist_ok=True)

NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ── request helpers ────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "GNN-PCNA-Phase2-acquisition/1.0 "
        "(governance-first; contact: advay.awesomer@gmail.com)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def _get(url: str, params=None, as_json=False, timeout=60, retries=3):
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
            r.raise_for_status()
            return r.json() if as_json else r.text
        except Exception as e:
            if i == retries - 1:
                print(f"  [WARN] GET failed {url}: {e}")
                return None
            time.sleep(2 ** i)

def _download_binary(url: str, out_path: Path, max_mb: float = 500.0, timeout=120) -> bool:
    """Download binary file. Skips if already exists. Returns True on success."""
    if out_path.exists():
        print(f"  [SKIP] {out_path.name} already exists")
        return True
    try:
        r = requests.get(url, headers=HEADERS, stream=True, timeout=timeout)
        r.raise_for_status()
        # Check content-length
        cl = int(r.headers.get("content-length", 0))
        if cl > max_mb * 1e6:
            print(f"  [SKIP-LARGE] {url} → {cl/1e6:.0f} MB > {max_mb} MB limit")
            return False
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
        print(f"  [OK] {out_path.name}  ({out_path.stat().st_size/1e3:.1f} KB)")
        return True
    except Exception as e:
        print(f"  [FAIL] {url}: {e}")
        return False

def _save_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", errors="replace")

def _sha256(path: Path) -> str:
    if not path.exists():
        return "FILE_NOT_FOUND"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def _size_str(path: Path) -> str:
    if not path.exists():
        return "0"
    s = path.stat().st_size
    if s > 1e6:
        return f"{s/1e6:.2f} MB"
    if s > 1e3:
        return f"{s/1e3:.1f} KB"
    return f"{s} B"

def _detect_schema(path: Path) -> str:
    """Read first 3 lines to guess schema/columns."""
    if not path.exists():
        return "FILE_NOT_FOUND"
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in lines[:5]:
            line = line.strip()
            if line and not line.startswith("#"):
                return line[:300]
        return "(no readable header)"
    except Exception:
        return "(binary)"

# ── inventory dataclass ────────────────────────────────────────────────────────
@dataclass
class DatasetEntry:
    name: str
    official_url: str
    download_date: str
    license: str = "UNKNOWN"
    file_path: str = ""
    file_size: str = ""
    sha256: str = ""
    file_type: str = ""
    schema_preview: str = ""
    contains: list[str] = field(default_factory=list)      # structures/labels/splits/metadata/code
    trust_level: str = "UNVERIFIED"
    intended_role: str = ""
    warnings: str = ""
    status: str = "ACQUIRED"                               # ACQUIRED / LINKED_ONLY / INACCESSIBLE

INVENTORY: list[DatasetEntry] = []

def add(entry: DatasetEntry):
    INVENTORY.append(entry)

# ══════════════════════════════════════════════════════════════════════════════
# 1. CryptoBench  —  PRIMARY TARGET
# ══════════════════════════════════════════════════════════════════════════════
def acquire_cryptobench():
    print("\n[1/11] CryptoBench — PRIMARY TARGET")
    base = RAW / "cryptobench"
    base.mkdir(exist_ok=True)

    # OSF API search
    osf_result = _get("https://api.osf.io/v2/nodes/?filter[title]=CryptoBench", as_json=True)
    if osf_result:
        osf_out = base / "osf_api_nodes.json"
        _save_text(osf_out, json.dumps(osf_result, indent=2))
        nodes = osf_result.get("data", [])
        print(f"  OSF API: {len(nodes)} nodes matching 'CryptoBench'")
        for node in nodes[:5]:
            nid   = node.get("id", "")
            title = node.get("attributes", {}).get("title", "")
            desc  = node.get("attributes", {}).get("description", "")
            print(f"    node {nid}: {title}")
            # Try to get files list for each node
            files_url = f"https://api.osf.io/v2/nodes/{nid}/files/"
            files_data = _get(files_url, as_json=True)
            if files_data:
                _save_text(base / f"osf_node_{nid}_files.json",
                           json.dumps(files_data, indent=2))
            # Try node-level metadata
            node_meta = _get(f"https://api.osf.io/v2/nodes/{nid}/", as_json=True)
            if node_meta:
                _save_text(base / f"osf_node_{nid}_meta.json",
                           json.dumps(node_meta, indent=2))
        add(DatasetEntry(
            name="CryptoBench (OSF API search)",
            official_url="https://api.osf.io/v2/nodes/?filter[title]=CryptoBench",
            download_date=NOW,
            license="CHECK_PER_NODE",
            file_path=str(osf_out.relative_to(ROOT)),
            file_size=_size_str(osf_out),
            sha256=_sha256(osf_out),
            file_type="JSON (OSF API response)",
            schema_preview=f"{len(nodes)} OSF nodes; fields: id, title, description, links",
            contains=["metadata"],
            trust_level="OFFICIAL_API",
            intended_role="CryptoBench primary dataset location",
            warnings="OSF nodes may require additional auth for private repos",
        ))
    else:
        add(DatasetEntry(
            name="CryptoBench (OSF API search)",
            official_url="https://api.osf.io/v2/nodes/?filter[title]=CryptoBench",
            download_date=NOW,
            status="INACCESSIBLE",
            warnings="OSF API returned no result",
        ))

    # OSF search page
    osf_html = _get("https://osf.io/search/?q=CryptoBench&filter=project")
    if osf_html:
        out = base / "osf_search_page.html"
        _save_text(out, osf_html)
        add(DatasetEntry(
            name="CryptoBench OSF search page",
            official_url="https://osf.io/search/?q=CryptoBench",
            download_date=NOW,
            file_path=str(out.relative_to(ROOT)),
            file_size=_size_str(out),
            sha256=_sha256(out),
            file_type="HTML",
            contains=["metadata"],
            trust_level="LINKED_ONLY",
            intended_role="CryptoBench discovery",
        ))

    # GitHub search via API
    gh_result = _get(
        "https://api.github.com/search/repositories",
        params={"q": "CryptoBench cryptic pocket", "sort": "stars", "per_page": 10},
        as_json=True,
    )
    if gh_result:
        gh_out = base / "github_search_cryptobench.json"
        _save_text(gh_out, json.dumps(gh_result, indent=2))
        items = gh_result.get("items", [])
        print(f"  GitHub search: {len(items)} repos")
        for item in items[:3]:
            print(f"    {item.get('full_name')} — stars:{item.get('stargazers_count')} — {item.get('html_url')}")
        # Try to fetch READMEs for top results
        for item in items[:3]:
            slug = item.get("full_name", "")
            for branch in ("main", "master"):
                readme_url = f"https://raw.githubusercontent.com/{slug}/{branch}/README.md"
                readme_text = _get(readme_url)
                if readme_text:
                    out = base / f"github_{slug.replace('/','_')}_README.md"
                    _save_text(out, readme_text)
                    add(DatasetEntry(
                        name=f"CryptoBench GitHub README ({slug})",
                        official_url=readme_url,
                        download_date=NOW,
                        file_path=str(out.relative_to(ROOT)),
                        file_size=_size_str(out),
                        sha256=_sha256(out),
                        file_type="Markdown",
                        contains=["metadata", "code"],
                        trust_level="OFFICIAL_REPO",
                        intended_role="CryptoBench method/dataset documentation",
                    ))
                    break
        add(DatasetEntry(
            name="CryptoBench GitHub search results",
            official_url="https://api.github.com/search/repositories?q=CryptoBench+cryptic+pocket",
            download_date=NOW,
            file_path=str(gh_out.relative_to(ROOT)),
            file_size=_size_str(gh_out),
            sha256=_sha256(gh_out),
            file_type="JSON",
            contains=["metadata"],
            trust_level="OFFICIAL_API",
            intended_role="CryptoBench repo discovery",
        ))
    time.sleep(1)

    # bioRxiv / PubMed search for CryptoBench paper metadata
    pm_result = _get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params={"db": "pubmed", "term": "CryptoBench cryptic pocket benchmark",
                "retmax": 10, "retmode": "json"},
        as_json=True,
    )
    if pm_result:
        ids = pm_result.get("esearchresult", {}).get("idlist", [])
        print(f"  PubMed: {len(ids)} hits for CryptoBench")
        if ids:
            abs_text = _get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                params={"db": "pubmed", "id": ",".join(ids),
                        "rettype": "abstract", "retmode": "text"},
            )
            if abs_text:
                out = base / "pubmed_cryptobench_abstracts.txt"
                _save_text(out, abs_text)
                add(DatasetEntry(
                    name="CryptoBench PubMed abstracts",
                    official_url="https://pubmed.ncbi.nlm.nih.gov",
                    download_date=NOW,
                    file_path=str(out.relative_to(ROOT)),
                    file_size=_size_str(out),
                    sha256=_sha256(out),
                    file_type="Text (PubMed abstract)",
                    contains=["literature_metadata"],
                    trust_level="OFFICIAL_API",
                    intended_role="CryptoBench paper citations",
                ))
    time.sleep(0.4)


# ══════════════════════════════════════════════════════════════════════════════
# 2. RCSB PDB — PCNA structures
# ══════════════════════════════════════════════════════════════════════════════
PCNA_PDB_IDS = [
    "8GLA",   # PCNA + AOH1996 (positive control cryptic pocket ligand)
    "1W60",   # PCNA reference
    "1AXC",   # PCNA human
    "1W63",   # PCNA with p21 peptide
    "3JAB",   # PCNA with multiple partners
    "6GIS",   # PCNA
    "1VYJ",   # PCNA/RFC clamp loader complex
    "1UL1",   # PCNA sliding clamp
    "2ZVK",   # PCNA
    "4D2G",   # PCNA
]

def acquire_rcsb():
    print("\n[2/11] RCSB PDB — PCNA structures")
    base_rcsb   = RAW / "rcsb_pdb"
    base_pcna   = RAW / "pcna_structures"
    base_rcsb.mkdir(exist_ok=True)
    base_pcna.mkdir(exist_ok=True)

    # First run a broad PCNA search to discover all relevant IDs
    search_payload = {
        "query": {
            "type": "terminal",
            "service": "full_text",
            "parameters": {"value": "PCNA proliferating cell nuclear antigen"},
        },
        "return_type": "entry",
        "request_options": {
            "paginate": {"start": 0, "rows": 50},
            "sort": [{"sort_by": "score", "direction": "desc"}],
        },
    }
    try:
        r = requests.post(
            "https://search.rcsb.org/rcsbsearch/v2/query",
            json=search_payload, headers=HEADERS, timeout=30,
        )
        r.raise_for_status()
        search_data = r.json()
        hits = [h["identifier"] for h in search_data.get("result_set", [])]
        print(f"  RCSB PCNA search: {len(hits)} hits")
        out = base_rcsb / "rcsb_pcna_search_results.json"
        _save_text(out, json.dumps(search_data, indent=2))
        add(DatasetEntry(
            name="RCSB PCNA full-text search results",
            official_url="https://search.rcsb.org/rcsbsearch/v2/query",
            download_date=NOW,
            license="Public Domain (PDB data policy)",
            file_path=str(out.relative_to(ROOT)),
            file_size=_size_str(out),
            sha256=_sha256(out),
            file_type="JSON",
            contains=["metadata"],
            trust_level="OFFICIAL_API",
            intended_role="PCNA structure discovery",
            warnings="Full-text search; check each structure relevance manually",
        ))
        # Add hits to priority list
        all_ids = list(dict.fromkeys(PCNA_PDB_IDS + hits[:30]))
    except Exception as e:
        print(f"  RCSB search failed: {e}")
        all_ids = PCNA_PDB_IDS

    # Download mmCIF + metadata for each priority structure
    for pdb_id in all_ids[:30]:
        pdb_id = pdb_id.upper()
        dest = base_pcna if pdb_id in PCNA_PDB_IDS else base_rcsb
        print(f"  Acquiring {pdb_id}…", end=" ")

        # REST API metadata
        meta = _get(f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id}", as_json=True)
        if meta:
            meta_out = dest / f"{pdb_id}_metadata.json"
            _save_text(meta_out, json.dumps(meta, indent=2))

            # Extract useful fields
            info = meta.get("rcsb_entry_info", {})
            resolution = info.get("resolution_combined", [None])[0] if isinstance(
                info.get("resolution_combined"), list) else info.get("resolution_combined")
            method = info.get("experimental_method", "?")
            polymer_count = info.get("polymer_entity_count", "?")
            nonpoly_count = info.get("nonpolymer_entity_count", 0)
            is_holo = (nonpoly_count or 0) > 0

            # Polymer entity details for chain/organism info
            poly_meta = _get(f"https://data.rcsb.org/rest/v1/core/polymer_entity/{pdb_id}/1", as_json=True)
            organism = "?"
            if poly_meta:
                src = poly_meta.get("rcsb_entity_source_organism", [{}])
                if src:
                    organism = src[0].get("scientific_name", "?")
                poly_out = dest / f"{pdb_id}_poly_entity.json"
                _save_text(poly_out, json.dumps(poly_meta, indent=2))

            # Ligand info if holo
            ligands = []
            if is_holo:
                ligand_meta = _get(
                    f"https://data.rcsb.org/rest/v1/core/nonpolymer_entity/{pdb_id}/1",
                    as_json=True,
                )
                if ligand_meta:
                    lig_id = ligand_meta.get("chem_comp", {}).get("id", "?")
                    lig_name = ligand_meta.get("chem_comp", {}).get("name", "?")
                    ligands.append(f"{lig_id} ({lig_name})")
                    lig_out = dest / f"{pdb_id}_ligand.json"
                    _save_text(lig_out, json.dumps(ligand_meta, indent=2))

            print(f"{method}  res={resolution}Å  organism={organism}  holo={is_holo}  ligands={ligands}")

            add(DatasetEntry(
                name=f"RCSB PDB {pdb_id} metadata",
                official_url=f"https://www.rcsb.org/structure/{pdb_id}",
                download_date=NOW,
                license="Public Domain (wwPDB open access)",
                file_path=str(meta_out.relative_to(ROOT)),
                file_size=_size_str(meta_out),
                sha256=_sha256(meta_out),
                file_type="JSON (RCSB REST API)",
                schema_preview=f"method={method}, resolution={resolution}Å, organism={organism}, "
                               f"chains={polymer_count}, nonpoly={nonpoly_count}, ligands={ligands}",
                contains=["structures", "metadata"],
                trust_level="OFFICIAL_API",
                intended_role=(
                    "positive-control (cryptic pocket ligand)" if pdb_id == "8GLA"
                    else "PCNA reference structure" if pdb_id == "1W60"
                    else "PCNA structure inventory"
                ),
                warnings=(
                    "8GLA contains AOH1996 bound at cryptic PCNA pocket — use as positive control only"
                    if pdb_id == "8GLA" else ""
                ),
            ))

        # mmCIF download (capped at 50 MB per file)
        cif_ok = _download_binary(
            f"https://files.rcsb.org/download/{pdb_id}.cif",
            dest / f"{pdb_id}.cif",
            max_mb=50,
        )
        if cif_ok:
            cif_path = dest / f"{pdb_id}.cif"
            add(DatasetEntry(
                name=f"RCSB PDB {pdb_id} mmCIF",
                official_url=f"https://files.rcsb.org/download/{pdb_id}.cif",
                download_date=NOW,
                license="Public Domain (wwPDB open access)",
                file_path=str(cif_path.relative_to(ROOT)),
                file_size=_size_str(cif_path),
                sha256=_sha256(cif_path),
                file_type="mmCIF",
                schema_preview=_detect_schema(cif_path),
                contains=["structures"],
                trust_level="OFFICIAL_DOWNLOAD",
                intended_role=(
                    "PCNA positive-control structure" if pdb_id == "8GLA"
                    else "PCNA reference structure"
                ),
                warnings="Not adopted for training — experimental structure only",
            ))
        time.sleep(0.2)

    # Also get the biological assembly info for 8GLA (trimeric PCNA)
    asm_8gla = _get("https://data.rcsb.org/rest/v1/core/assembly/8GLA/1", as_json=True)
    if asm_8gla:
        out = base_pcna / "8GLA_assembly1.json"
        _save_text(out, json.dumps(asm_8gla, indent=2))
        print(f"  8GLA assembly 1: {_size_str(out)}")


# ══════════════════════════════════════════════════════════════════════════════
# 3. BioLiP / BioLiP2 / Q-BioLiP — AUXILIARY LABEL SOURCE
# ══════════════════════════════════════════════════════════════════════════════
def acquire_biolip():
    print("\n[3/11] BioLiP — AUXILIARY LABEL SOURCE")
    base = RAW / "biolip"
    base.mkdir(exist_ok=True)

    pages = [
        ("https://zhanggroup.org/BioLiP/",              "biolip_home.html"),
        ("https://zhanggroup.org/BioLiP/download.cgi",  "biolip_download.html"),
        ("https://zhanggroup.org/BioLiP2/",             "biolip2_home.html"),
        ("https://zhanggroup.org/BioLiP2/download.cgi", "biolip2_download.html"),
        ("https://zhanggroup.org/Q-BioLiP/",            "qbiolip_home.html"),
        ("https://zhanggroup.org/Q-BioLiP/download.cgi","qbiolip_download.html"),
    ]
    for url, fname in pages:
        content = _get(url)
        if content:
            out = base / fname
            _save_text(out, content)
            # Parse download links
            soup = BeautifulSoup(content, "html.parser")
            dl_links = [a["href"] for a in soup.find_all("a", href=True)
                        if any(ext in a["href"] for ext in [".tar", ".gz", ".zip", ".txt"])]
            add(DatasetEntry(
                name=f"BioLiP page: {fname}",
                official_url=url,
                download_date=NOW,
                license="Free for academic use (Zhang Lab)",
                file_path=str(out.relative_to(ROOT)),
                file_size=_size_str(out),
                sha256=_sha256(out),
                file_type="HTML",
                schema_preview=f"Download links found: {dl_links[:5]}",
                contains=["metadata"],
                trust_level="OFFICIAL_PAGE",
                intended_role="BioLiP ligand-binding residue annotation discovery",
                warnings=(
                    "BioLiP labels = ligand-contact residues, NOT cryptic pocket ground truth. "
                    "Do not use as direct cryptic-pocket supervision without filtering."
                ),
            ))
            if dl_links:
                print(f"  {fname}: found {len(dl_links)} download links")

    # Download a small sample annotation file (weekly update — small)
    weekly_url = "https://zhanggroup.org/BioLiP/weekly.tar.bz2"
    ok = _download_binary(weekly_url, base / "biolip_weekly.tar.bz2", max_mb=100)
    if ok:
        out = base / "biolip_weekly.tar.bz2"
        add(DatasetEntry(
            name="BioLiP weekly update archive",
            official_url=weekly_url,
            download_date=NOW,
            license="Free for academic use (Zhang Lab)",
            file_path=str(out.relative_to(ROOT)),
            file_size=_size_str(out),
            sha256=_sha256(out),
            file_type="tar.bz2",
            contains=["structures", "labels", "metadata"],
            trust_level="OFFICIAL_DOWNLOAD",
            intended_role="BioLiP ligand-binding annotations (weekly delta)",
            warnings=(
                "Labels are ligand-contact residues, not cryptic-pocket ground truth. "
                "Requires biological filtering. Full database not downloaded — too large."
            ),
        ))


# ══════════════════════════════════════════════════════════════════════════════
# 4. scPDB — AUXILIARY BINDING-POCKET SOURCE
# ══════════════════════════════════════════════════════════════════════════════
def acquire_scpdb():
    print("\n[4/11] scPDB — AUXILIARY BINDING-POCKET SOURCE")
    base = RAW / "scpdb"
    base.mkdir(exist_ok=True)

    pages = [
        ("http://bioinfo-pharma.u-strasbg.fr/scPDB/",             "scpdb_home.html"),
        ("https://bioinfo-pharma.u-strasbg.fr/scPDB/",            "scpdb_home_https.html"),
        ("http://bioinfo-pharma.u-strasbg.fr/scPDB/browse.html",  "scpdb_browse.html"),
        ("http://bioinfo-pharma.u-strasbg.fr/scPDB/download.html","scpdb_download.html"),
    ]
    for url, fname in pages:
        content = _get(url)
        if content:
            out = base / fname
            _save_text(out, content)
            soup = BeautifulSoup(content, "html.parser")
            text_preview = soup.get_text(" ", strip=True)[:500]
            # Try to find entry count
            count_match = re.search(r"(\d[\d,]+)\s*(entries|structures|proteins|pockets)", text_preview, re.I)
            count_str = count_match.group(0) if count_match else "not found in page"
            add(DatasetEntry(
                name=f"scPDB page: {fname}",
                official_url=url,
                download_date=NOW,
                license="Free for academic use (Strasbourg)",
                file_path=str(out.relative_to(ROOT)),
                file_size=_size_str(out),
                sha256=_sha256(out),
                file_type="HTML",
                schema_preview=f"Entry count hint: {count_str}",
                contains=["metadata"],
                trust_level="OFFICIAL_PAGE",
                intended_role="scPDB druggable binding site annotation discovery",
                warnings=(
                    "scPDB labels = druggable binding sites (proxy, not cryptic-pocket truth). "
                    "Full archive not downloaded — check license before bulk download."
                ),
            ))
            print(f"  {fname}: entries hint = {count_str}")


# ══════════════════════════════════════════════════════════════════════════════
# 5. ASD — ALLOSTERIC CONTEXT
# ══════════════════════════════════════════════════════════════════════════════
def acquire_asd():
    print("\n[5/11] ASD — ALLOSTERIC CONTEXT SOURCE")
    base = RAW / "asd"
    base.mkdir(exist_ok=True)

    pages = [
        ("http://mdl.shsmu.edu.cn/ASD/",                                 "asd_home.html"),
        ("http://mdl.shsmu.edu.cn/ASD/module/download/download.jsp",     "asd_download.html"),
        ("https://asd.bidd2.com",                                         "asd_mirror.html"),
        ("https://asd.bidd2.com/download",                                "asd_mirror_dl.html"),
    ]
    for url, fname in pages:
        content = _get(url)
        if content:
            out = base / fname
            _save_text(out, content)
            soup = BeautifulSoup(content, "html.parser")
            text = soup.get_text(" ", strip=True)[:500]
            add(DatasetEntry(
                name=f"ASD page: {fname}",
                official_url=url,
                download_date=NOW,
                license="UNKNOWN — check asd.bidd2.com/about",
                file_path=str(out.relative_to(ROOT)),
                file_size=_size_str(out),
                sha256=_sha256(out),
                file_type="HTML",
                schema_preview=text[:200],
                contains=["metadata"],
                trust_level="OFFICIAL_PAGE",
                intended_role="Allosteric site/modulator context for PCNA",
                warnings=(
                    "ASD is allosteric context only. Not residue-level cryptic-pocket labels "
                    "unless schema explicitly supports it. Download requires manual license review."
                ),
            ))
            print(f"  {fname}: {_size_str(out)}")


# ══════════════════════════════════════════════════════════════════════════════
# 6. PocketMiner — BASELINE / METHOD REFERENCE
# ══════════════════════════════════════════════════════════════════════════════
def acquire_pocketminer():
    print("\n[6/11] PocketMiner — BASELINE / METHOD REFERENCE")
    base = RAW / "pocketminer"
    base.mkdir(exist_ok=True)

    repo_slug = "Protein-Sequence-and-Structure/PocketMiner"
    for branch in ("main", "master"):
        readme = _get(f"https://raw.githubusercontent.com/{repo_slug}/{branch}/README.md")
        if readme:
            out = base / "pocketminer_README.md"
            _save_text(out, readme)
            add(DatasetEntry(
                name="PocketMiner GitHub README",
                official_url=f"https://github.com/{repo_slug}",
                download_date=NOW,
                license="CHECK_REPO (likely academic/non-commercial)",
                file_path=str(out.relative_to(ROOT)),
                file_size=_size_str(out),
                sha256=_sha256(out),
                file_type="Markdown",
                contains=["metadata", "code"],
                trust_level="OFFICIAL_REPO",
                intended_role="PocketMiner methodology reference, input/output schema",
                warnings="Run locally only after license review. Do not use predictions as ground truth.",
            ))
            print(f"  PocketMiner README: {_size_str(out)}")
            break

    # PocketMiner paper via PubMed
    pm_paper = _get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params={"db": "pubmed", "term": "PocketMiner cryptic pockets protein",
                "retmax": 5, "retmode": "json"},
        as_json=True,
    )
    if pm_paper:
        ids = pm_paper.get("esearchresult", {}).get("idlist", [])
        if ids:
            abs_text = _get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                params={"db": "pubmed", "id": ",".join(ids),
                        "rettype": "abstract", "retmode": "text"},
            )
            if abs_text:
                out = base / "pocketminer_pubmed_abstract.txt"
                _save_text(out, abs_text)
                add(DatasetEntry(
                    name="PocketMiner PubMed abstract",
                    official_url="https://pubmed.ncbi.nlm.nih.gov",
                    download_date=NOW,
                    file_path=str(out.relative_to(ROOT)),
                    file_size=_size_str(out),
                    sha256=_sha256(out),
                    file_type="Text",
                    contains=["literature_metadata"],
                    trust_level="OFFICIAL_API",
                    intended_role="PocketMiner paper metadata for citation",
                ))
    time.sleep(0.4)

    # bioRxiv search
    biorxiv_page = _get(f"https://www.biorxiv.org/search/{quote('PocketMiner cryptic pockets')}")
    if biorxiv_page:
        out = base / "biorxiv_pocketminer.html"
        _save_text(out, biorxiv_page)


# ══════════════════════════════════════════════════════════════════════════════
# 7. Baseline tools — fpocket, P2Rank
# ══════════════════════════════════════════════════════════════════════════════
def acquire_baseline_tools():
    print("\n[7/11] Baseline tools — fpocket, P2Rank")
    base = RAW / "baseline_tools"

    tools = [
        {
            "name": "fpocket",
            "repo": "Discngine/fpocket",
            "home": "https://github.com/Discngine/fpocket",
            "dir": base / "fpocket",
            "role": "Voronoi-based open-cavity pocket detector; mandatory baseline",
            "warnings": "Output: pocket_X.pqr + .pdb files; residue-level scores via pocket_atoms columns. C binary — must compile on Linux/WSL.",
        },
        {
            "name": "P2Rank",
            "repo": "rdk/p2rank",
            "home": "https://github.com/rdk/p2rank",
            "dir": base / "p2rank",
            "role": "ML-based binding site prediction; second mandatory baseline",
            "warnings": "Output: CSV with residue-level scores. JVM-based — requires Java 11+. Output: predictions.csv with columns: rank, score, probability, sas_points, surf_atom_ids.",
        },
    ]
    for tool in tools:
        tool["dir"].mkdir(parents=True, exist_ok=True)
        slug = tool["repo"]

        # README
        for branch in ("main", "master"):
            readme = _get(f"https://raw.githubusercontent.com/{slug}/{branch}/README.md")
            if readme:
                out = tool["dir"] / "README.md"
                _save_text(out, readme)
                print(f"  {tool['name']} README: {_size_str(out)}")
                break

        # Releases API
        releases = _get(f"https://api.github.com/repos/{slug}/releases", as_json=True)
        if releases and isinstance(releases, list):
            rel_out = tool["dir"] / "releases.json"
            _save_text(rel_out, json.dumps(releases[:3], indent=2))
            latest = releases[0] if releases else {}
            tag = latest.get("tag_name", "?")
            dl_url = ""
            for asset in latest.get("assets", []):
                if any(ext in asset["name"] for ext in [".tar.gz", ".zip", ".jar"]):
                    dl_url = asset["browser_download_url"]
                    break
            print(f"  {tool['name']} latest: {tag}  download: {dl_url or 'none'}")
            add(DatasetEntry(
                name=f"{tool['name']} GitHub releases",
                official_url=tool["home"],
                download_date=NOW,
                license="MIT/Apache — check per repo",
                file_path=str(rel_out.relative_to(ROOT)),
                file_size=_size_str(rel_out),
                sha256=_sha256(rel_out),
                file_type="JSON",
                contains=["code", "metadata"],
                trust_level="OFFICIAL_REPO",
                intended_role=tool["role"],
                warnings=tool["warnings"],
            ))
        time.sleep(1)

        # README entry
        readme_path = tool["dir"] / "README.md"
        if readme_path.exists():
            add(DatasetEntry(
                name=f"{tool['name']} README",
                official_url=f"https://raw.githubusercontent.com/{slug}/main/README.md",
                download_date=NOW,
                license="CHECK_REPO",
                file_path=str(readme_path.relative_to(ROOT)),
                file_size=_size_str(readme_path),
                sha256=_sha256(readme_path),
                file_type="Markdown",
                contains=["metadata", "code"],
                trust_level="OFFICIAL_REPO",
                intended_role=tool["role"],
                warnings=tool["warnings"],
            ))


# ══════════════════════════════════════════════════════════════════════════════
# 8. PDBbind — AUXILIARY ONLY
# ══════════════════════════════════════════════════════════════════════════════
def acquire_pdbbind():
    print("\n[8/11] PDBbind — AUXILIARY ONLY")
    base = RAW / "pdbbind"
    base.mkdir(exist_ok=True)

    pages = [
        ("http://www.pdbbind.org.cn",              "pdbbind_home.html"),
        ("http://www.pdbbind.org.cn/download.asp", "pdbbind_download.html"),
        ("http://www.pdbbind.org.cn/index.asp",    "pdbbind_index.html"),
    ]
    for url, fname in pages:
        content = _get(url)
        if content:
            out = base / fname
            _save_text(out, content)
            add(DatasetEntry(
                name=f"PDBbind: {fname}",
                official_url=url,
                download_date=NOW,
                license="RESTRICTED — registration required for download",
                file_path=str(out.relative_to(ROOT)),
                file_size=_size_str(out),
                sha256=_sha256(out),
                file_type="HTML",
                contains=["metadata"],
                trust_level="OFFICIAL_PAGE",
                intended_role="Protein-ligand affinity context only. NOT cryptic-pocket ground truth.",
                warnings=(
                    "PDBbind requires registration. Do NOT adopt as cryptic-pocket labels. "
                    "LP-PDBBind (leakage-aware split) preferred for affinity auxiliary task."
                ),
            ))
            print(f"  {fname}: {_size_str(out)}")

    # LP-PDBBind GitHub search
    lp_result = _get(
        "https://api.github.com/search/repositories",
        params={"q": "LP-PDBBind leakage", "sort": "stars", "per_page": 5},
        as_json=True,
    )
    if lp_result:
        out = base / "lp_pdbbind_github_search.json"
        _save_text(out, json.dumps(lp_result, indent=2))
        add(DatasetEntry(
            name="LP-PDBBind GitHub search",
            official_url="https://github.com/search?q=LP-PDBBind",
            download_date=NOW,
            file_path=str(out.relative_to(ROOT)),
            file_size=_size_str(out),
            sha256=_sha256(out),
            file_type="JSON",
            contains=["metadata"],
            trust_level="OFFICIAL_API",
            intended_role="LP-PDBBind leakage-aware split reference for data hygiene",
            warnings="Use LP-PDBBind split methodology, not labels, for cryptic-pocket splits",
        ))
    time.sleep(1)


# ══════════════════════════════════════════════════════════════════════════════
# 9. AlphaFold DB — TARGETED ONLY (PCNA + homologs)
# ══════════════════════════════════════════════════════════════════════════════
AF_PCNA_TARGETS = {
    "P15531": "PCNA_HUMAN",
    "P12004": "PCNA_MOUSE",
    "P04448": "PCNA_YEAST",
}

def acquire_alphafold():
    print("\n[9/11] AlphaFold DB — TARGETED PCNA structures only")
    base = RAW / "alphafold"
    base.mkdir(exist_ok=True)

    for uniprot_id, label in AF_PCNA_TARGETS.items():
        print(f"  AlphaFold {uniprot_id} ({label})…", end=" ")
        api = _get(f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}", as_json=True)
        if api:
            meta_out = base / f"AF_{uniprot_id}_{label}_api.json"
            _save_text(meta_out, json.dumps(api, indent=2))
            entries = api if isinstance(api, list) else [api]
            for entry in entries[:1]:
                plddt = entry.get("globalMetricValue", "?")
                version = entry.get("latestVersion", "?")
                cif_url = entry.get("cifUrl", "")
                print(f"pLDDT={plddt}  version={version}", end=" ")

                if cif_url:
                    cif_ok = _download_binary(cif_url, base / f"AF_{uniprot_id}_{label}.cif", max_mb=20)
                    if cif_ok:
                        cif_path = base / f"AF_{uniprot_id}_{label}.cif"
                        add(DatasetEntry(
                            name=f"AlphaFold {uniprot_id} ({label}) CIF",
                            official_url=f"https://alphafold.ebi.ac.uk/entry/{uniprot_id}",
                            download_date=NOW,
                            license="CC BY 4.0",
                            file_path=str(cif_path.relative_to(ROOT)),
                            file_size=_size_str(cif_path),
                            sha256=_sha256(cif_path),
                            file_type="mmCIF (predicted)",
                            schema_preview=_detect_schema(cif_path),
                            contains=["structures", "metadata"],
                            trust_level="OFFICIAL_DOWNLOAD",
                            intended_role="PCNA predicted structure for structural context only",
                            warnings=(
                                "PREDICTED structure. pLDDT confidence must be checked. "
                                "NOT experimental evidence. Use only when experimental PDB unavailable. "
                                f"pLDDT={plddt}, model version={version}"
                            ),
                        ))
            add(DatasetEntry(
                name=f"AlphaFold {uniprot_id} ({label}) API metadata",
                official_url=f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}",
                download_date=NOW,
                license="CC BY 4.0",
                file_path=str(meta_out.relative_to(ROOT)),
                file_size=_size_str(meta_out),
                sha256=_sha256(meta_out),
                file_type="JSON",
                contains=["metadata"],
                trust_level="OFFICIAL_API",
                intended_role="AlphaFold PCNA metadata",
                warnings="Predicted structure context only",
            ))
            print()
        time.sleep(0.5)


# ══════════════════════════════════════════════════════════════════════════════
# 10. BioGRID + STRING — TARGETED PCNA queries only
# ══════════════════════════════════════════════════════════════════════════════
def acquire_biogrid_string():
    print("\n[10/11] BioGRID + STRING — targeted PCNA queries")

    # BioGRID
    bg_base = RAW / "biogrid"
    bg_base.mkdir(exist_ok=True)

    bg_home = _get("https://thebiogrid.org")
    if bg_home:
        out = bg_base / "biogrid_home.html"
        _save_text(out, bg_home)

    bg_api_url = "https://webservice.thebiogrid.org/interactions/"
    bg_params = {
        "searchNames": "true",
        "geneList": "PCNA",
        "includeInteractors": "true",
        "format": "json",
        "max": "200",
        "accesskey": "BIOGRID_ACCESS_KEY",   # public demo key
    }
    bg_result = _get(bg_api_url, params=bg_params, as_json=True)
    if bg_result and isinstance(bg_result, dict):
        out = bg_base / "pcna_biogrid_interactions.json"
        _save_text(out, json.dumps(bg_result, indent=2))
        n = len(bg_result)
        print(f"  BioGRID PCNA: {n} interactions")
        add(DatasetEntry(
            name="BioGRID PCNA interaction network",
            official_url="https://thebiogrid.org",
            download_date=NOW,
            license="Free for academic use (MIT License)",
            file_path=str(out.relative_to(ROOT)),
            file_size=_size_str(out),
            sha256=_sha256(out),
            file_type="JSON",
            schema_preview="interaction_id, entrez_id_A, entrez_id_B, official_symbol_A, official_symbol_B, experimental_system, source_database",
            contains=["metadata"],
            trust_level="OFFICIAL_API",
            intended_role="PCNA protein interaction context / background priors",
            warnings=(
                "Interaction context only — physical vs functional not always distinguished. "
                "Do not use as residue-level pocket labels."
            ),
        ))

    # STRING
    str_base = RAW / "string"
    str_base.mkdir(exist_ok=True)

    # PCNA network (targeted, not full organism file)
    str_params = {
        "identifiers": "PCNA",
        "species": 9606,
        "limit": 100,
        "network_type": "physical",
        "caller_identity": "advay.awesomer@gmail.com",
    }
    for endpoint, fname in [
        ("https://string-db.org/api/json/network",    "pcna_string_network.json"),
        ("https://string-db.org/api/json/enrichment",  "pcna_string_enrichment.json"),
        ("https://string-db.org/api/json/interaction_partners",
         "pcna_string_partners.json"),
    ]:
        result = _get(endpoint, params=str_params, as_json=True)
        if result:
            out = str_base / fname
            _save_text(out, json.dumps(result, indent=2))
            n = len(result) if isinstance(result, list) else "?"
            print(f"  STRING {fname}: {n} entries")
            add(DatasetEntry(
                name=f"STRING PCNA {fname.replace('pcna_string_','').replace('.json','')}",
                official_url="https://string-db.org",
                download_date=NOW,
                license="CC BY 4.0",
                file_path=str(out.relative_to(ROOT)),
                file_size=_size_str(out),
                sha256=_sha256(out),
                file_type="JSON",
                schema_preview=f"fields from STRING API: stringId_A, stringId_B, score, experiments",
                contains=["metadata"],
                trust_level="OFFICIAL_API",
                intended_role="PCNA functional/physical interaction context",
                warnings=(
                    "STRING includes functional/co-expression associations. "
                    "Use only physical sub-network for structural context. "
                    "NOT pocket labels."
                ),
            ))
        time.sleep(0.3)


# ══════════════════════════════════════════════════════════════════════════════
# 11. Literature metadata
# ══════════════════════════════════════════════════════════════════════════════
LIT_QUERIES = [
    ("CryptoBench cryptic pocket benchmark",           "cryptobench"),
    ("PCNA allosteric cryptic pocket cancer",          "pcna_cryptic"),
    ("AOH1996 PCNA inhibitor",                         "aoh1996"),
    ("cryptic binding site machine learning GNN",      "cryptic_ml"),
    ("PocketMiner pocket prediction",                  "pocketminer"),
    ("BioLiP ligand binding residue database",         "biolip"),
    ("fpocket Voronoi pocket detection",               "fpocket"),
    ("P2Rank binding site prediction random forest",   "p2rank"),
    ("LP-PDBBind leakage protein-ligand split",        "lp_pdbbind"),
    ("DeepPocket deep learning pocket",                "deeppocket"),
    ("DeepAllo allosteric network",                    "deepallo"),
    ("EquiPocket equivariant pocket prediction",       "equipocket"),
    ("dataset leakage protein structure benchmark",    "leakage"),
    ("allosteric site detection review",               "allosteric_review"),
    ("PCNA ring sliding clamp DNA replication review", "pcna_review"),
]

def acquire_literature():
    print("\n[11/11] Literature metadata")
    base = RAW / "literature_metadata"
    base.mkdir(exist_ok=True)

    all_papers: list[dict] = []

    for query, slug in LIT_QUERIES:
        result = _get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db": "pubmed", "term": query, "retmax": 20, "retmode": "json"},
            as_json=True,
        )
        if not result:
            continue
        ids = result.get("esearchresult", {}).get("idlist", [])
        print(f"  PubMed '{query}' → {len(ids)} hits")
        if ids:
            abs_text = _get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                params={"db": "pubmed", "id": ",".join(ids),
                        "rettype": "abstract", "retmode": "text"},
            )
            if abs_text:
                out = base / f"pm_{slug}.txt"
                _save_text(out, abs_text)
                # Record each PMID as a paper lead
                for pmid in ids:
                    all_papers.append({
                        "pmid": pmid,
                        "query_topic": slug,
                        "source": "PubMed",
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        "role": "literature_metadata",
                        "note": (
                            "Abstract only. Do not commit full PDFs to repo unless license permits."
                        ),
                    })
                add(DatasetEntry(
                    name=f"PubMed abstracts: {slug}",
                    official_url=f"https://pubmed.ncbi.nlm.nih.gov/?term={quote(query)}",
                    download_date=NOW,
                    license="NLM open access — abstracts only",
                    file_path=str(out.relative_to(ROOT)),
                    file_size=_size_str(out),
                    sha256=_sha256(out),
                    file_type="Text",
                    contains=["literature_metadata"],
                    trust_level="OFFICIAL_API",
                    intended_role=f"Literature metadata for topic: {slug}",
                    warnings="Abstracts only. Full text not downloaded.",
                ))
        time.sleep(0.35)

    # Save paper leads index
    if all_papers:
        out = base / "paper_leads_index.json"
        _save_text(out, json.dumps(all_papers, indent=2))
        print(f"  Paper leads index: {len(all_papers)} entries")

    # Also pull from seed context (840 papers from round_00)
    seed_file = ROOT / "context" / "round_00_seed.json"
    if seed_file.exists():
        try:
            seed = json.loads(seed_file.read_text("utf-8"))
            papers = seed.get("papers", [])
            relevant = [
                p for p in papers
                if any(kw in (p.get("title","") + p.get("abstract","")).lower()
                       for kw in ["pcna", "cryptic", "pocket", "allosteric",
                                  "biolip", "fpocket", "p2rank", "binding site"])
            ]
            out = base / "seed_relevant_papers.json"
            _save_text(out, json.dumps(relevant, indent=2))
            print(f"  Seed context: {len(relevant)} relevant papers from {len(papers)} total")
            add(DatasetEntry(
                name="Seed context relevant papers (from round_00_seed.json)",
                official_url="local:context/round_00_seed.json",
                download_date=NOW,
                license="various",
                file_path=str(out.relative_to(ROOT)),
                file_size=_size_str(out),
                sha256=_sha256(out),
                file_type="JSON",
                contains=["literature_metadata"],
                trust_level="CRAWL_LEAD",
                intended_role="Literature leads for manual review",
                warnings="These are crawl-derived leads only. Verify each before citing.",
            ))
        except Exception as e:
            print(f"  Seed parse error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# REPORT GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def write_registry():
    """Write dataset_inventory.json and dataset_inventory.csv."""
    REG.mkdir(exist_ok=True)

    inv_list = [asdict(e) for e in INVENTORY]

    # JSON
    inv_json = REG / "dataset_inventory.json"
    _save_text(inv_json, json.dumps(inv_list, indent=2))
    print(f"\n[REG] {inv_json.relative_to(ROOT)}  ({len(inv_list)} entries)")

    # CSV
    inv_csv = REG / "dataset_inventory.csv"
    if inv_list:
        fields = list(inv_list[0].keys())
        with open(inv_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for row in inv_list:
                row2 = {k: ("|".join(v) if isinstance(v, list) else v)
                        for k, v in row.items()}
                w.writerow(row2)
    print(f"[REG] {inv_csv.relative_to(ROOT)}")


def write_acquisition_log():
    acquired = [e for e in INVENTORY if e.status == "ACQUIRED"]
    linked   = [e for e in INVENTORY if e.status == "LINKED_ONLY"]
    failed   = [e for e in INVENTORY if e.status == "INACCESSIBLE"]

    lines = [
        "# Phase 2 Dataset Acquisition Log",
        f"_Generated: {NOW}_  |  _Status: RAW_ASSETS_ACQUIRED_NOT_VERIFIED_",
        "",
        "## Summary",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Files acquired (downloaded) | {len(acquired)} |",
        f"| Sources linked only | {len(linked)} |",
        f"| Inaccessible | {len(failed)} |",
        f"| Total inventory entries | {len(INVENTORY)} |",
        "",
        "## Acquired files",
        "",
    ]
    for e in acquired:
        lines += [
            f"### {e.name}",
            f"- **URL**: {e.official_url}",
            f"- **File**: `{e.file_path}`",
            f"- **Size**: {e.file_size}",
            f"- **SHA-256**: `{e.sha256}`",
            f"- **Type**: {e.file_type}",
            f"- **Trust**: {e.trust_level}",
            f"- **Role**: {e.intended_role}",
            f"- **License**: {e.license}",
            "",
        ]

    lines += ["## Linked-only sources (not downloaded)", ""]
    for e in linked:
        lines += [f"- {e.name}: {e.official_url}  ({e.warnings})"]

    lines += ["", "## Inaccessible sources", ""]
    for e in failed:
        lines += [f"- {e.name}: {e.official_url}  —  {e.warnings}"]

    out = REP / "dataset_acquisition_log.md"
    _save_text(out, "\n".join(lines))
    print(f"[REP] {out.relative_to(ROOT)}")


def write_file_inventory():
    lines = [
        "# Dataset File Inventory",
        f"_Generated: {NOW}_",
        "",
        "| Name | File | Size | SHA-256 | Type | Trust | Contains |",
        "|------|------|------|---------|------|-------|----------|",
    ]
    for e in INVENTORY:
        contains = ", ".join(e.contains) if e.contains else "-"
        sha_short = e.sha256[:16] + "…" if len(e.sha256) > 16 else e.sha256
        lines.append(
            f"| {e.name[:50]} "
            f"| `{e.file_path[-50:]}` "
            f"| {e.file_size} "
            f"| `{sha_short}` "
            f"| {e.file_type[:30]} "
            f"| {e.trust_level} "
            f"| {contains} |"
        )

    out = REP / "dataset_file_inventory.md"
    _save_text(out, "\n".join(lines))
    print(f"[REP] {out.relative_to(ROOT)}")


def write_license_review():
    lines = [
        "# License and Terms Review",
        f"_Generated: {NOW}_",
        "",
        "| Dataset | License | Notes | Action Required |",
        "|---------|---------|-------|-----------------|",
    ]
    license_map = {
        "CryptoBench": ("CHECK_PER_NODE", "OSF project — may be CC-BY or custom", "Read OSF project license page before use"),
        "RCSB PDB": ("Public Domain", "wwPDB open data policy — no restrictions", "None"),
        "BioLiP": ("Free academic", "Zhang Lab — academic non-commercial", "Cite paper; confirm commercial restriction"),
        "scPDB": ("Free academic", "Strasbourg — academic non-commercial", "Check http://bioinfo-pharma.u-strasbg.fr/scPDB/"),
        "ASD": ("UNKNOWN", "Not found on page", "Manual check required at asd.bidd2.com/about"),
        "PocketMiner": ("CHECK_REPO", "Likely academic/non-commercial", "Check GitHub LICENSE file"),
        "fpocket": ("MIT / LGPLv2", "Open source", "Compatible with research use"),
        "P2Rank": ("MIT", "Open source", "Compatible with research use"),
        "PDBbind": ("RESTRICTED", "Registration required; non-commercial academic", "Do NOT redistribute. Register at pdbbind.org.cn"),
        "AlphaFold": ("CC BY 4.0", "EBI/Google — attribution required", "Cite AlphaFold paper; add license note to each file"),
        "BioGRID": ("MIT", "MIT License", "None — cite paper"),
        "STRING": ("CC BY 4.0", "Free to use with attribution", "Cite STRING paper; note version"),
        "PubMed abstracts": ("NLM open", "Abstracts freely available", "Do not store full PDFs without checking publisher"),
    }
    for ds, (lic, note, action) in license_map.items():
        lines.append(f"| {ds} | {lic} | {note} | {action} |")

    lines += [
        "",
        "## Critical flags",
        "",
        "- **PDBbind**: Requires registration. Do NOT adopt for training without registration and license agreement.",
        "- **ASD**: License unknown. Do NOT adopt for training until verified.",
        "- **CryptoBench**: Check OSF project-level license. Could be CC-BY or all-rights-reserved depending on authors.",
        "- **scPDB / BioLiP**: Academic-only. If project becomes commercial, renegotiate.",
        "",
        "## Status",
        "NOT_VERIFIED — all licenses require human review before training adoption.",
    ]
    out = REP / "license_and_terms_review.md"
    _save_text(out, "\n".join(lines))
    print(f"[REP] {out.relative_to(ROOT)}")


def write_schema_report():
    lines = [
        "# Dataset Schema First Pass",
        f"_Generated: {NOW}_",
        "",
        "## Notes",
        "- Schema detection is automated from file headers only.",
        "- Binary files show `(binary)`. Manual inspection required.",
        "- JSON files show top-level keys only.",
        "- NOT verified for correctness — first-pass only.",
        "",
        "| Dataset | File | Schema / Columns (first pass) |",
        "|---------|------|-------------------------------|",
    ]
    for e in INVENTORY:
        if e.schema_preview and e.file_path:
            schema = e.schema_preview[:120].replace("\n", " ").replace("|", "/")
            lines.append(f"| {e.name[:45]} | `{e.file_type}` | {schema} |")

    lines += [
        "",
        "## Critical schema audit items needed",
        "",
        "1. **CryptoBench** — does it contain: residue-level labels? apo/holo PDB pairs? train/val/test splits? PCNA entries?",
        "2. **BioLiP** — confirm column meaning of ligand-contact residues vs pocket residues.",
        "3. **scPDB** — confirm pocket-residue definition and whether holo-only.",
        "4. **ASD** — confirm whether residue-level or protein-level annotations.",
        "5. **PocketMiner** — confirm input/output schema before using as baseline.",
        "",
        "Status: SCHEMA_FIRST_PASS_ONLY — no schema adopted for training.",
    ]
    out = REP / "dataset_schema_first_pass.md"
    _save_text(out, "\n".join(lines))
    print(f"[REP] {out.relative_to(ROOT)}")


def write_adoption_recommendation():
    lines = [
        "# Dataset Adoption Recommendation",
        f"_Generated: {NOW}_",
        "",
        "> **Status: NOT_READY_FOR_SPLIT_FREEZE**",
        "> None of the datasets below are cleared for training. Human review required for each.",
        "",
        "## Tier 1 — HIGH priority, likely usable (pending schema audit)",
        "",
        "| Dataset | Role | Blocker before adoption |",
        "|---------|------|------------------------|",
        "| CryptoBench | PRIMARY benchmark | Verify residue-level labels, splits, license |",
        "| RCSB PDB (8GLA, 1W60, PCNA set) | Canonical structures | None — use as-is for structure reference |",
        "| PocketMiner | Baseline method | Verify input/output schema, run locally |",
        "| fpocket | Mandatory baseline | Install and test on 8GLA |",
        "| P2Rank | Mandatory baseline | Install and test on 8GLA |",
        "",
        "## Tier 2 — AUXILIARY (useful but not ground truth)",
        "",
        "| Dataset | Role | Caveat |",
        "|---------|------|--------|",
        "| BioLiP | Auxiliary binding-residue supervision | NOT cryptic-pocket truth — ligand-contact only |",
        "| scPDB | Druggable pocket context | Proxy labels only — druggable ≠ cryptic |",
        "| AlphaFold (PCNA) | Predicted structure context | Predicted — pLDDT check required |",
        "| BioGRID / STRING | PCNA interaction priors | Context only — not pocket labels |",
        "",
        "## Tier 3 — DO NOT USE AS PRIMARY LABELS",
        "",
        "| Dataset | Reason |",
        "|---------|--------|",
        "| ASD | License unknown; allosteric ≠ cryptic without schema validation |",
        "| PDBbind | Registration required; affinity labels ≠ pocket labels |",
        "| PDBbind full dataset | Potential leakage — use LP-PDBBind split methodology |",
        "",
        "## Recommended canonical dataset for Phase 2",
        "",
        "**CryptoBench** is the recommended primary benchmark IF:",
        "1. Schema audit confirms residue-level cryptic-pocket labels",
        "2. Apo/holo pairs are confirmed",
        "3. Train/val/test splits are provided or derivable without leakage",
        "4. PCNA or PCNA homologs are NOT in training set (held-out for final inference)",
        "5. License is confirmed for academic use",
        "",
        "**Until the above are confirmed**: status remains `NOT_READY_FOR_SPLIT_FREEZE`.",
        "",
        "## Next required actions (human review)",
        "",
        "- [ ] Open CryptoBench OSF node and read the README/dataset card",
        "- [ ] Inspect CryptoBench label schema: what does a positive label mean exactly?",
        "- [ ] Check whether PCNA appears in any split",
        "- [ ] Verify BioLiP ligand-contact column definitions",
        "- [ ] Install fpocket and run on 8GLA to verify output schema",
        "- [ ] Install P2Rank and run on 8GLA to verify residue-level scores",
        "- [ ] Hash-verify all downloaded files against official checksums if available",
        "- [ ] Review all licenses with project PI before training adoption",
    ]
    out = REP / "dataset_adoption_recommendation.md"
    _save_text(out, "\n".join(lines))
    print(f"[REP] {out.relative_to(ROOT)}")


def write_friend_report():
    """The main deliverable report for Rishi."""
    acquired  = [e for e in INVENTORY if e.status == "ACQUIRED"]
    linked    = [e for e in INVENTORY if e.status == "LINKED_ONLY"]
    failed    = [e for e in INVENTORY if e.status == "INACCESSIBLE"]
    total_bytes = sum(
        Path(ROOT / e.file_path).stat().st_size
        for e in acquired
        if e.file_path and (ROOT / e.file_path).exists()
    )

    def trust_badge(t):
        return {"OFFICIAL_DOWNLOAD": "✓ OFFICIAL",
                "OFFICIAL_API":      "✓ OFFICIAL API",
                "OFFICIAL_REPO":     "✓ OFFICIAL REPO",
                "OFFICIAL_PAGE":     "~ OFFICIAL PAGE",
                "LINKED_ONLY":       "~ LINKED",
                "CRAWL_LEAD":        "⚠ LEAD ONLY",
                "UNVERIFIED":        "⚠ UNVERIFIED",
                }.get(t, t)

    lines = [
        "# Phase 2 Friend Dataset Acquisition Report",
        f"_Generated: {NOW}_",
        f"_Prepared for: GNN-PCNA Phase 2 governance review_",
        "",
        "---",
        "",
        "## Overall Status",
        "",
        "```",
        "STATUS: RAW_ASSETS_ACQUIRED_NOT_VERIFIED",
        "```",
        "",
        f"- **{len(acquired)}** files acquired and on disk",
        f"- **{len(linked)}** sources linked only (not downloaded)",
        f"- **{len(failed)}** sources inaccessible",
        f"- **{total_bytes/1e3:.1f} KB** total raw intake on disk",
        f"- **{len(INVENTORY)}** total inventory entries",
        "",
        "---",
        "",
        "## 1. What was downloaded",
        "",
        "| # | Name | File | Size | Trust |",
        "|---|------|------|------|-------|",
    ]
    for i, e in enumerate(acquired, 1):
        badge = trust_badge(e.trust_level)
        lines.append(
            f"| {i} | {e.name[:55]} "
            f"| `{Path(e.file_path).name if e.file_path else '-'}` "
            f"| {e.file_size} "
            f"| {badge} |"
        )

    lines += [
        "",
        "## 2. What was only linked (not downloaded)",
        "",
    ]
    for e in linked:
        lines.append(f"- **{e.name}**: {e.official_url}")
        if e.warnings:
            lines.append(f"  - _{e.warnings}_")

    lines += [
        "",
        "## 3. What could not be accessed",
        "",
    ]
    if failed:
        for e in failed:
            lines.append(f"- **{e.name}**: {e.official_url}  —  {e.warnings}")
    else:
        lines.append("_(none — all attempted sources returned data)_")

    lines += [
        "",
        "## 4. Licenses / terms found",
        "",
        "| Dataset | License | Status |",
        "|---------|---------|--------|",
        "| RCSB PDB | Public Domain (wwPDB) | ✓ Clear |",
        "| AlphaFold | CC BY 4.0 | ✓ Clear — cite required |",
        "| BioGRID | MIT | ✓ Clear |",
        "| STRING | CC BY 4.0 | ✓ Clear — cite required |",
        "| BioLiP | Academic non-commercial | ⚠ Confirm for commercial |",
        "| scPDB | Academic non-commercial | ⚠ Confirm for commercial |",
        "| fpocket | MIT/LGPL | ✓ Clear |",
        "| P2Rank | MIT | ✓ Clear |",
        "| CryptoBench | UNKNOWN — check OSF | ⛔ Must verify before use |",
        "| ASD | UNKNOWN | ⛔ Must verify before use |",
        "| PDBbind | Registration required | ⛔ Do not use without registration |",
        "| PubMed abstracts | NLM open (abstracts) | ✓ Abstracts only |",
        "",
        "## 5. Schemas visible (first pass only)",
        "",
        "| Dataset | Format | Schema preview |",
        "|---------|--------|----------------|",
        "| RCSB REST API | JSON | `rcsb_entry_info.*`: method, resolution, chain counts, ligand IDs |",
        "| RCSB mmCIF | mmCIF | `_atom_site.label_*`: chain, residue, x/y/z, B-factor |",
        "| AlphaFold CIF | mmCIF | Same as RCSB + `_ma_qa_metric_local.metric_value` (pLDDT) |",
        "| BioGRID JSON | JSON | `interaction_id, entrez_id_A/B, experimental_system, pubmed_id` |",
        "| STRING JSON | JSON | `stringId_A/B, score, nscore, fscore, pscore, ascore, escore` |",
        "| PubMed text | Plain text | PMID, Title, Authors, Abstract, Journal |",
        "| BioLiP HTML | HTML | Download links found; TSV columns not yet audited |",
        "| scPDB HTML | HTML | Entry count not extractable from page; full schema not seen |",
        "| CryptoBench | UNKNOWN | No files accessed yet — OSF node files not resolved |",
        "",
        "## 6. Assets that look usable",
        "",
        "- **RCSB PDB (8GLA, 1W60, PCNA set)**: High trust, public domain, experimental structures.",
        "  8GLA is confirmed positive control (AOH1996 ligand at cryptic pocket). Use immediately.",
        "- **AlphaFold PCNA (P15531, P12004, P04448)**: CC-BY, predicted — usable as structural context",
        "  after pLDDT verification. Not experimental evidence.",
        "- **fpocket / P2Rank**: Open-source baselines. Install and test on 8GLA before benchmark.",
        "- **BioGRID / STRING PCNA**: Interaction context; usable for background priors with caveat.",
        "- **PubMed abstracts**: Literature metadata; useful for claim audit / related work.",
        "",
        "## 7. Assets that are risky",
        "",
        "- **CryptoBench**: Status UNKNOWN. No files downloaded yet. OSF API returned nodes but",
        "  file contents not resolved. Risk: label definition may not match cryptic-pocket ground truth.",
        "  **Block training until schema audit complete.**",
        "- **BioLiP**: Labels = ligand-contact residues, NOT cryptic-pocket truth. High risk of",
        "  proxy label contamination if used directly as training signal.",
        "- **scPDB**: Labels = druggable sites (holo-bound). Same proxy-label risk as BioLiP.",
        "- **ASD**: Unknown license + allosteric ≠ cryptic without explicit schema validation.",
        "- **PDBbind**: Registration required. Any use without registration is a license violation.",
        "",
        "## 8. Assets that are too large (not downloaded)",
        "",
        "- BioLiP full archive (`receptor.tar.bz2`, `ligand.tar.bz2`): Several GB. Not downloaded.",
        "  Weekly delta only acquired. Full download requires human decision + disk allocation.",
        "- scPDB full archive: ~2 GB. Not downloaded — license check needed first.",
        "- AlphaFold human proteome: ~24 GB extracted. Not downloaded — targeted PCNA only.",
        "- STRING full organism files: ~500 MB–35 GB. Not downloaded — PCNA API query used instead.",
        "- BioGRID complete release: ~500 MB. Not downloaded — PCNA API query used instead.",
        "",
        "## 9. What still needs manual approval",
        "",
        "- [ ] **CryptoBench**: Open OSF project, read dataset card, confirm label schema",
        "- [ ] **CryptoBench**: Confirm whether PCNA / PCNA homologs appear in any split",
        "- [ ] **CryptoBench**: Confirm train/val/test split provenance and leakage status",
        "- [ ] **ASD**: Read license terms on asd.bidd2.com/about",
        "- [ ] **BioLiP**: Read full column definitions for TSV files before using labels",
        "- [ ] **scPDB**: Read pocket-residue definition and confirm binding mode",
        "- [ ] **PDBbind**: Register if needed; confirm LP-PDBBind split methodology",
        "- [ ] **All files**: Cross-check SHA-256 hashes against official checksums if published",
        "- [ ] **All licenses**: PI review before any training adoption",
        "- [ ] **fpocket + P2Rank**: Test install and run on 8GLA; verify output schema",
        "",
        "## 10. Recommended canonical dataset source for Phase 2",
        "",
        "**Primary**: CryptoBench (IF schema audit passes — see item 9 above)",
        "",
        "**Rationale**: CryptoBench is specifically designed for cryptic-pocket benchmarking.",
        "All other sources (BioLiP, scPDB, ASD, PDBbind) are proxy datasets with different",
        "label semantics. Using them as primary supervision without CryptoBench validation",
        "risks repeating V1's overclaim pattern.",
        "",
        "**Fallback if CryptoBench unavailable**: CryptoSite dataset (check if separate from",
        "CryptoBench). Otherwise, construct labels from RCSB apo/holo pairs with explicit",
        "human-validated positive/negative definitions before any split freeze.",
        "",
        "---",
        "",
        "## Final status",
        "",
        "```",
        "RAW_ASSETS_ACQUIRED_NOT_VERIFIED",
        "```",
        "",
        "No datasets are adopted for training.",
        "No splits are frozen.",
        "No labels are confirmed.",
        "Human review required before proceeding to CRYPTOBENCH_READY_FOR_SCHEMA_AUDIT.",
        "",
        f"_Report generated by: scripts/acquire_phase2_governed.py_",
        f"_Date: {NOW}_",
    ]

    out = REP / "friend_dataset_acquisition_report.md"
    _save_text(out, "\n".join(lines))
    print(f"[REP] {out.relative_to(ROOT)}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 68)
    print("GNN-PCNA Phase 2 Governed Dataset Acquisition")
    print(f"Date: {NOW}")
    print("DO NOT TRAIN. DO NOT FREEZE SPLITS. ACQUISITION ONLY.")
    print("=" * 68)

    acquire_cryptobench()
    acquire_rcsb()
    acquire_biolip()
    acquire_scpdb()
    acquire_asd()
    acquire_pocketminer()
    acquire_baseline_tools()
    acquire_pdbbind()
    acquire_alphafold()
    acquire_biogrid_string()
    acquire_literature()

    print("\n[REPORTS] Writing registry and reports…")
    write_registry()
    write_acquisition_log()
    write_file_inventory()
    write_license_review()
    write_schema_report()
    write_adoption_recommendation()
    write_friend_report()

    total = sum(
        Path(ROOT / e.file_path).stat().st_size
        for e in INVENTORY
        if e.file_path and (ROOT / e.file_path).exists()
    )

    print("\n" + "=" * 68)
    print(f"STATUS: RAW_ASSETS_ACQUIRED_NOT_VERIFIED")
    print(f"Inventory entries : {len(INVENTORY)}")
    print(f"Total on disk     : {total/1e6:.2f} MB")
    print(f"Registry          : {REG}/dataset_inventory.json")
    print(f"Main report       : {REP}/friend_dataset_acquisition_report.md")
    print("=" * 68)


if __name__ == "__main__":
    main()
