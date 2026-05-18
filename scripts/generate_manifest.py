"""
Generate SHA-256 manifest for all committed data files.

Writes data/MANIFEST.json  (machine-readable)
   and data/MANIFEST.md    (human-readable table)

Usage:
    python scripts/generate_manifest.py
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).parent.parent
MANIFEST_JSON = REPO / "data" / "MANIFEST.json"
MANIFEST_MD   = REPO / "data" / "MANIFEST.md"

# Directories to hash
SCAN_DIRS = [
    "data/raw",
    "data/pcna",
    "data/pcna_xl",
    "data/graphs",
    "data/graphs_xl",
    "data/processed",
    "data/cryptosite",
    "data/splits",
    "data/xl_splits",
    "data/esm_features",
    "checkpoints",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def is_tracked(path: Path) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(path)],
        cwd=str(REPO),
        capture_output=True,
    )
    return result.returncode == 0


def main():
    entries = []
    for dir_str in SCAN_DIRS:
        d = REPO / dir_str
        if not d.exists():
            continue
        for p in sorted(d.rglob("*")):
            if not p.is_file():
                continue
            if p.name in {".gitkeep", ".DS_Store"}:
                continue
            rel = p.relative_to(REPO).as_posix()
            tracked = is_tracked(p)
            size = p.stat().st_size
            checksum = sha256(p) if tracked else None
            entries.append({
                "path": rel,
                "size_bytes": size,
                "sha256": checksum,
                "tracked_in_git": tracked,
            })

    manifest = {
        "generated": datetime.utcnow().isoformat() + "Z",
        "repo": "GNN_PCNA",
        "total_files": len(entries),
        "files": entries,
    }
    MANIFEST_JSON.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {MANIFEST_JSON.relative_to(REPO)}")

    # Markdown table
    lines = [
        "# Data File Manifest",
        f"*Generated: {manifest['generated']}*",
        "",
        "| Path | Size | SHA-256 | In git? |",
        "|------|------|---------|---------|",
    ]
    for e in entries:
        sz = f"{e['size_bytes']:,}"
        chk = e["sha256"][:16] + "…" if e["sha256"] else "—"
        git = "yes" if e["tracked_in_git"] else "no"
        lines.append(f"| `{e['path']}` | {sz} | `{chk}` | {git} |")

    MANIFEST_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {MANIFEST_MD.relative_to(REPO)}")
    print(f"Total files inventoried: {len(entries)}")


if __name__ == "__main__":
    main()
