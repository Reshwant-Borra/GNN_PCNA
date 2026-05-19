# data/raw/ — Raw PDB Files

All PDB files are **committed directly to this repo** and can be cloned without running any download script.

## What goes here

All PDB files used in this project (59 PCNA structures + 91 CryptoSite benchmark proteins, 149 total), named `{PDB_ID}.pdb`.

## How to reproduce

```bash
# Download all 59 structures + verify SHA256 checksums + build graph tensors
python scripts/download_data.py

# Download only (skip graph building)
python scripts/download_data.py --skip-graphs

# Verify checksums of already-downloaded files
python scripts/download_data.py --verify

# Re-download even if files exist (e.g., after a partial download)
python scripts/download_data.py --force
```

The script:
1. Downloads all PDB files from `https://files.rcsb.org/download/{PDB_ID}.pdb`
2. Verifies each file contains `ATOM` records
3. Computes SHA256 checksums and saves them to `data/manifests/pdb_checksums.json`
4. Builds PyG graph tensors and saves them to `data/graphs/`

## Source

All structures are from RCSB PDB (https://www.rcsb.org/). Download is free, no authentication required.

## Excluded structure

**1W61 is NOT included** — it is proline racemase (*Trypanosoma cruzi*), not PCNA.
It was incorrectly included in earlier versions of this project.
See `docs/vault/structures/1W61.md` for details.

## After downloading

```bash
python scripts/make_split.py              # create train/val/test split
python scripts/per_structure_analysis.py  # run per-structure analysis
python scripts/full_eval.py               # full evaluation + figures
```
