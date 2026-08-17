"""
crawl_phase3_labels.py
======================
Targeted acquisition of labeled datasets needed for Phase 3 GNN training.
Fixes vs first run:
  - BioLiP2: tries Michigan URL (zhanglab.dcmb.med.umich.edu) + browser headers
  - ASD: tries new mirror URLs (bidd2.com is dead)
  - APOc/COACH: allow_redirects=True on HEAD
"""
from __future__ import annotations

import asyncio, hashlib, json, os, re, sys, time
from datetime import datetime, timezone
from pathlib import Path

import aiohttp

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT   = Path(__file__).resolve().parent.parent
INTAKE = ROOT / "data" / "raw_intake"
LABELS = ROOT / "data" / "phase3_labels"
LABELS.mkdir(parents=True, exist_ok=True)

LOG_FILE = ROOT / "logs" / "phase3_crawl.log"
LOG_FILE.parent.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/json,*/*;q=0.9",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}
TIMEOUT = aiohttp.ClientTimeout(total=600, connect=30)


def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


async def fetch_json(session, url):
    try:
        async with session.get(url, headers=HEADERS, allow_redirects=True) as r:
            if r.status == 200:
                return await r.json(content_type=None)
            log(f"  HTTP {r.status}: {url}")
    except Exception as e:
        log(f"  ERROR {url}: {e}")
    return None


async def fetch_text(session, url):
    try:
        async with session.get(url, headers=HEADERS, allow_redirects=True) as r:
            if r.status == 200:
                return await r.text(errors="replace")
            log(f"  HTTP {r.status}: {url}")
    except Exception as e:
        log(f"  ERROR {url}: {e}")
    return None


async def download_file(session, url: str, dest: Path, label: str = "") -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        log(f"  [skip] {dest.name} already exists")
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        async with session.get(url, headers=HEADERS, allow_redirects=True) as r:
            if r.status == 200:
                with open(dest, "wb") as f:
                    async for chunk in r.content.iter_chunked(65536):
                        f.write(chunk)
                size_mb = dest.stat().st_size / 1e6
                log(f"  [OK] {label or dest.name}  {size_mb:.1f} MB  sha256={sha256(dest)[:12]}...")
                return True
            log(f"  [FAIL] HTTP {r.status}: {url}")
    except Exception as e:
        log(f"  [FAIL] {url}: {e}")
    return False


# ── CryptoBench (already acquired — skip if present) ───────────────────────────

async def crawl_cryptobench(session):
    out = INTAKE / "cryptobench" / "pz4a9"
    if (out / "cryptobench" / "cryptobench-dataset" / "dataset.json").exists():
        log("\n=== CryptoBench: already acquired, skipping ===")
        return
    log("\n=== CryptoBench ===")
    out.mkdir(parents=True, exist_ok=True)

    async def _osf_folder(folder_url: str, dest_dir: Path):
        data = await fetch_json(session, folder_url)
        if not data or not data.get("data"):
            return
        dest_dir.mkdir(parents=True, exist_ok=True)
        for fi in data["data"]:
            fname = fi["attributes"].get("name", "unknown")
            fkind = fi["attributes"].get("kind", "file")
            fsize = fi["attributes"].get("size") or 0
            if fkind == "folder":
                sub = fi["relationships"]["files"]["links"]["related"]["href"]
                log(f"      folder: {fname}/")
                await _osf_folder(sub, dest_dir / fname)
            else:
                flink = fi["links"].get("download", "")
                log(f"      file: {fname}  {fsize/1e6:.1f} MB")
                if flink and fsize < 5e9:
                    await download_file(session, flink, dest_dir / fname, fname)

    await _osf_folder(
        "https://api.osf.io/v2/nodes/pz4a9/files/osfstorage/",
        out / "cryptobench")


# ── BioLiP2 — Zhang lab Michigan URL ──────────────────────────────────────────

async def crawl_biolip2(session):
    out = LABELS / "biolip2"
    out.mkdir(parents=True, exist_ok=True)
    log("\n=== BioLiP2 ===")

    # Try multiple base URLs — Michigan moved, org may be Cloudflare-blocked
    candidate_bases = [
        "https://zhanglab.dcmb.med.umich.edu/BioLiP/",
        "https://zhanglab.ccmb.med.umich.edu/BioLiP/",
        "https://zhanglab.dcmb.med.umich.edu/BioLiP2/",
        "https://zhanggroup.org/BioLiP2/",
        "https://zhanggroup.org/BioLiP/",
    ]

    found_base = None
    for base in candidate_bases:
        html = await fetch_text(session, base)
        if html:
            log(f"  Reachable: {base}")
            found_base = base
            (out / f"biolip_home_{base.split('/')[2]}.html").write_text(html, encoding="utf-8")
            # Find download links
            links = re.findall(
                r'href=["\']([^"\']*\.(?:tar\.bz2|tar\.gz|gz|zip|tsv|txt))["\']', html)
            for link in links:
                if not link.startswith("http"):
                    link = base + link.lstrip("/")
                fname = link.split("/")[-1]
                if any(kw in fname.lower() for kw in
                       ["annotation", "nr", "weekly", "readme", "biolip", "list"]):
                    try:
                        async with session.head(link, headers=HEADERS, allow_redirects=True) as r:
                            size = int(r.headers.get("Content-Length", 0))
                            log(f"    {fname}: {r.status}  {size/1e6:.0f} MB")
                            if r.status == 200 and 0 < size < 2e9:
                                await download_file(session, link, out / fname, fname)
                    except Exception as e:
                        log(f"    HEAD {fname}: {e}")
            break

    # Direct file tries regardless
    log("  Trying direct file downloads...")
    direct_files = []
    for base in candidate_bases[:3]:
        direct_files += [
            f"{base}weekly.tar.bz2",
            f"{base}readme.txt",
            f"{base}BioLiP_2024-1-1.txt.gz",
            f"{base}BioLiP_2023-1-1.txt.gz",
            f"{base}BioLiP2_nr.tar.bz2",
        ]

    for url in direct_files:
        fname = url.split("/")[-1]
        dest  = out / fname
        if dest.exists():
            continue
        try:
            async with session.head(url, headers=HEADERS, allow_redirects=True) as r:
                size = int(r.headers.get("Content-Length", 0))
                log(f"  {fname} @ {url.split('/')[2]}: {r.status}  {size/1e6:.0f} MB")
                if r.status == 200 and 0 < size < 2e9:
                    await download_file(session, url, dest, fname)
                    break  # got it from one base, don't re-download
        except Exception as e:
            log(f"  {fname}: {e}")


# ── scPDB (already acquired 187 MB — skip) ────────────────────────────────────

async def crawl_scpdb(session):
    dest = LABELS / "scpdb" / "scPDB.tar.gz"
    if dest.exists() and dest.stat().st_size > 100e6:
        log("\n=== scPDB: already acquired (187 MB), skipping ===")
        return
    log("\n=== scPDB ===")
    out = LABELS / "scpdb"
    out.mkdir(parents=True, exist_ok=True)
    url = "http://bioinfo-pharma.u-strasbg.fr/scPDB/ressources/2016/scPDB.tar.gz"
    await download_file(session, url, dest, "scPDB.tar.gz")


# ── ASD — new mirrors ─────────────────────────────────────────────────────────

async def crawl_asd(session):
    out = LABELS / "asd"
    out.mkdir(parents=True, exist_ok=True)
    log("\n=== ASD (Allosteric Site Database) ===")

    # bidd2.com is dead. Try known current mirrors.
    candidate_pages = [
        "https://mdl.shsmu.edu.cn/ASD/module/download/download.jsp",
        "http://mdl.shsmu.edu.cn/ASD/module/download/download.jsp",
        "https://www.allosite.org/download",
        "https://allosigma.bii.a-star.edu.sg/download/",
        # GitHub releases for ASD
        "https://api.github.com/repos/xiaobo-zhu/ASD/releases",
    ]

    for url in candidate_pages:
        if "github.com/repos" in url:
            data = await fetch_json(session, url)
            if data and isinstance(data, list):
                log(f"  GitHub ASD releases: {len(data)}")
                for rel in data[:3]:
                    for asset in rel.get("assets", []):
                        aurl  = asset["browser_download_url"]
                        aname = asset["name"]
                        asize = asset.get("size", 0)
                        log(f"    {aname}  {asize/1e6:.0f} MB")
                        if asize < 2e9:
                            await download_file(session, aurl, out / aname, aname)
        else:
            html = await fetch_text(session, url)
            if html:
                log(f"  Reachable: {url}")
                (out / f"asd_page_{url.split('/')[2]}.html").write_text(html, encoding="utf-8")
                links = re.findall(
                    r'href=["\']([^"\']*\.(?:zip|tar\.gz|tgz|csv|tsv|xlsx|json))["\']', html, re.I)
                log(f"    {len(links)} download links")
                for link in links:
                    if not link.startswith("http"):
                        link = "https://" + url.split("/")[2] + "/" + link.lstrip("/")
                    fname = link.split("/")[-1]
                    log(f"    -> {fname}")
                    try:
                        async with session.head(link, headers=HEADERS, allow_redirects=True) as r:
                            size = int(r.headers.get("Content-Length", 0))
                            if r.status == 200 and size < 2e9:
                                await download_file(session, link, out / fname, fname)
                    except Exception as e:
                        log(f"    {fname}: {e}")

    # Direct known ASD data URLs
    direct = [
        "https://mdl.shsmu.edu.cn/ASD/module/download/files/ASD_Release_201909_AS.zip",
        "https://mdl.shsmu.edu.cn/ASD/module/download/files/ASD_Release_201909_AS.tar.gz",
        "http://mdl.shsmu.edu.cn/ASD/module/download/files/ASD_Release_201909_AS.zip",
    ]
    for url in direct:
        fname = url.split("/")[-1]
        if (out / fname).exists():
            continue
        try:
            async with session.head(url, headers=HEADERS, allow_redirects=True) as r:
                size = int(r.headers.get("Content-Length", 0))
                log(f"  {fname}: {r.status}  {size/1e6:.0f} MB")
                if r.status == 200 and size < 2e9:
                    await download_file(session, url, out / fname, fname)
        except Exception as e:
            log(f"  {fname}: {e}")


# ── APOc / COACH — follow redirects ───────────────────────────────────────────

async def crawl_apoc_coach(session):
    out = LABELS / "extras"
    out.mkdir(parents=True, exist_ok=True)
    log("\n=== APOc / COACH / CryptoSite ===")

    targets = [
        # APOc apo/holo benchmark
        ("https://zhanglab.dcmb.med.umich.edu/APOc/data/APOc_benchmark.tar.gz", out / "APOc_benchmark.tar.gz"),
        ("https://zhanglab.ccmb.med.umich.edu/APOc/data/APOc_benchmark.tar.gz", out / "APOc_benchmark.tar.gz"),
        # COACH binding site benchmark
        ("https://zhanglab.dcmb.med.umich.edu/COACH/benchmark.tar.bz2", out / "COACH_benchmark.tar.bz2"),
        ("https://zhanglab.ccmb.med.umich.edu/COACH/benchmark.tar.bz2", out / "COACH_benchmark.tar.bz2"),
        # CryptoSite (Sali lab) — GitHub is the live source
        ("https://raw.githubusercontent.com/salilab/cryptosite/main/data/all_systems.txt",
         out / "cryptosite_all_systems.txt"),
        ("https://raw.githubusercontent.com/salilab/cryptosite/main/test/input/cp_all.txt",
         out / "cryptosite_cp_all.txt"),
        ("https://raw.githubusercontent.com/salilab/cryptosite/master/data/all_systems.txt",
         out / "cryptosite_all_systems.txt"),
        # PocketMiner (Tubiana 2022) — try various repo names
        ("https://api.github.com/repos/Tubiana/PocketMiner", None),
        ("https://api.github.com/repos/tubiana/PocketMiner", None),
    ]

    for url, dest in targets:
        if dest and dest.exists() and dest.stat().st_size > 0:
            log(f"  [skip] {dest.name}")
            continue
        if url.startswith("https://api.github.com/repos/"):
            info = await fetch_json(session, url)
            if info and info.get("id"):
                log(f"  Found PocketMiner repo: {info['full_name']}  stars={info.get('stargazers_count')}")
                # Get releases + data dir
                repo = info["full_name"]
                rels = await fetch_json(session, f"https://api.github.com/repos/{repo}/releases")
                if rels:
                    for rel in rels[:2]:
                        for asset in rel.get("assets", []):
                            asize = asset.get("size", 0)
                            if asize < 2e9:
                                await download_file(
                                    session, asset["browser_download_url"],
                                    out / asset["name"], asset["name"])
        elif dest:
            try:
                async with session.head(url, headers=HEADERS, allow_redirects=True) as r:
                    size = int(r.headers.get("Content-Length", 0))
                    log(f"  {dest.name} @ {url.split('/')[2]}: {r.status}  {size/1e6:.0f} MB")
                    if r.status == 200 and 0 < size < 2e9:
                        ok = await download_file(session, url, dest, dest.name)
                        if ok:
                            break
            except Exception as e:
                log(f"  {dest.name}: {e}")


# ── main ───────────────────────────────────────────────────────────────────────

async def main():
    log("=" * 60)
    log("GNN-PCNA Phase 3 Label Crawler (retry)")
    log(f"Started: {datetime.now(timezone.utc).isoformat()}")
    log("=" * 60)

    connector = aiohttp.TCPConnector(limit=16, ssl=False)
    async with aiohttp.ClientSession(connector=connector, timeout=TIMEOUT) as session:
        await crawl_cryptobench(session)
        await crawl_biolip2(session)
        await crawl_scpdb(session)
        await crawl_asd(session)
        await crawl_apoc_coach(session)

    log("\n" + "=" * 60)
    log("DONE. New files:")
    total = 0
    for d in [INTAKE / "cryptobench", LABELS]:
        for f in sorted(d.rglob("*")):
            if f.is_file():
                sz = f.stat().st_size
                total += sz
                log(f"  {f.relative_to(ROOT)}  ({sz/1e6:.2f} MB)")
    log(f"Total: {total/1e6:.1f} MB")
    log("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
