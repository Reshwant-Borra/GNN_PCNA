"""
Extract ESM2 per-residue embeddings for all processed PDB structures.

Uses facebook/esm2_t12_35M_UR50D (480-dim, 35M params) from HuggingFace.
Falls back to esm2_t6_8M_UR50D (320-dim) if t12 isn't cached yet.

Output: data/esm_features/{PDB_ID}.npy  — shape (N_residues, 480)

ESM2 handles up to 1022 residues per call. Long chains are split into
overlapping windows and averaged at overlaps.

Usage:
    python scripts/build_esm_features.py
    python scripts/build_esm_features.py --model t6     # 320-dim, faster
    python scripts/build_esm_features.py --ids 8GLA 1W60
    python scripts/build_esm_features.py --force        # re-run all
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import torch
from tqdm import tqdm

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.data_processing.parse_pdb import parse_pdb

RAW_DIR     = REPO_ROOT / "data" / "raw"
PROC_DIR    = REPO_ROOT / "data" / "processed"
ESM_DIR     = REPO_ROOT / "data" / "esm_features"
ESM_DIR.mkdir(parents=True, exist_ok=True)

# ESM2 amino acid alphabet (single-letter codes)
_THREE_TO_ONE = {
    'ALA':'A','ARG':'R','ASN':'N','ASP':'D','CYS':'C','GLN':'Q','GLU':'E',
    'GLY':'G','HIS':'H','ILE':'I','LEU':'L','LYS':'K','MET':'M','PHE':'F',
    'PRO':'P','SER':'S','THR':'T','TRP':'W','TYR':'Y','VAL':'V',
}
_ESM_MODELS = {
    't6':  'facebook/esm2_t6_8M_UR50D',    # 320-dim
    't12': 'facebook/esm2_t12_35M_UR50D',  # 480-dim
    't30': 'facebook/esm2_t30_150M_UR50D', # 640-dim
}
_ESM_DIMS = {'t6': 320, 't12': 480, 't30': 640}

MAX_LEN = 1022  # ESM2 max without special tokens


def _load_esm(model_key: str):
    from transformers import EsmModel, EsmTokenizer
    name = _ESM_MODELS[model_key]
    print(f"Loading {name} ...")
    tokenizer = EsmTokenizer.from_pretrained(name)
    model     = EsmModel.from_pretrained(name)
    model.eval()
    return tokenizer, model


@torch.no_grad()
def _embed_sequence(seq: str, tokenizer, model, esm_dim: int) -> np.ndarray:
    """
    Return (L, esm_dim) embeddings for a single amino-acid sequence.
    Handles sequences longer than MAX_LEN via overlapping windows (stride=512).
    """
    L = len(seq)
    if L == 0:
        return np.zeros((0, esm_dim), dtype=np.float32)

    if L <= MAX_LEN:
        inputs = tokenizer(seq, return_tensors='pt', add_special_tokens=True)
        out    = model(**inputs)
        # [0] = batch, [1:-1] = strip <cls> and <eos> tokens
        return out.last_hidden_state[0, 1:-1].numpy().astype(np.float32)

    # Long chain: sliding window with stride=512, average overlaps
    stride  = 512
    emb_sum = np.zeros((L, esm_dim), dtype=np.float64)
    counts  = np.zeros(L, dtype=np.float64)

    start = 0
    while start < L:
        end   = min(start + MAX_LEN, L)
        chunk = seq[start:end]
        inputs = tokenizer(chunk, return_tensors='pt', add_special_tokens=True)
        out    = model(**inputs)
        chunk_emb = out.last_hidden_state[0, 1:-1].numpy()
        emb_sum[start:end] += chunk_emb
        counts[start:end]  += 1
        if end == L:
            break
        start += stride

    return (emb_sum / np.maximum(counts[:, None], 1)).astype(np.float32)


def embed_pdb(pdb_path: Path, tokenizer, model, esm_dim: int) -> np.ndarray | None:
    """
    Parse a PDB, extract per-chain sequences, embed with ESM2, reassemble
    into (N_residues, esm_dim) in the same order as parse_pdb() returns them.
    """
    try:
        residues = parse_pdb(pdb_path)
    except Exception as e:
        print(f"    parse_pdb failed: {e}")
        return None

    if not residues:
        return None

    # Group residues by chain (preserving order)
    chains: dict[str, list] = {}
    for i, r in enumerate(residues):
        chains.setdefault(r.chain, []).append((i, r))

    all_embs = np.zeros((len(residues), esm_dim), dtype=np.float32)

    for chain_id, res_list in chains.items():
        seq = ''.join(_THREE_TO_ONE.get(r.resname, 'X') for _, r in res_list)
        emb = _embed_sequence(seq, tokenizer, model, esm_dim)
        if emb.shape[0] != len(res_list):
            # Length mismatch — pad or truncate to match
            target = len(res_list)
            if emb.shape[0] < target:
                pad = np.zeros((target - emb.shape[0], esm_dim), dtype=np.float32)
                emb = np.concatenate([emb, pad], axis=0)
            else:
                emb = emb[:target]
        for k, (idx, _) in enumerate(res_list):
            all_embs[idx] = emb[k]

    return all_embs


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract ESM2 protein embeddings for all PDB structures")
    parser.add_argument('--model',  default='t12', choices=['t6', 't12', 't30'],
                        help='ESM2 variant (t6=320d fast, t12=480d, t30=640d)')
    parser.add_argument('--ids',    nargs='+', metavar='PDB_ID',
                        help='Only process specific IDs')
    parser.add_argument('--force',  action='store_true',
                        help='Overwrite existing .npy files')
    args = parser.parse_args()

    esm_dim = _ESM_DIMS[args.model]
    tokenizer, model = _load_esm(args.model)
    print(f"ESM2 dim={esm_dim}  |  output -> {ESM_DIR}\n")

    # Collect PDB files: prefer processed (_clean.pdb), fall back to raw/
    if args.ids:
        id_set = {i.upper() for i in args.ids}
        proc_files = []
        for pid in id_set:
            clean = PROC_DIR / f"{pid}_clean.pdb"
            raw   = RAW_DIR  / f"{pid}.pdb"
            if clean.exists():
                proc_files.append(clean)
            elif raw.exists():
                proc_files.append(raw)
        proc_files = sorted(proc_files)
    else:
        proc_files = sorted(PROC_DIR.glob("*_clean.pdb"))

    ok = failed = skipped = 0
    for pdb_path in tqdm(proc_files, desc="ESM2", unit="struct"):
        stem   = pdb_path.stem
        pdb_id = stem.replace('_clean', '').upper()
        out_path = ESM_DIR / f"{pdb_id}.npy"

        if out_path.exists() and not args.force:
            skipped += 1
            continue

        emb = embed_pdb(pdb_path, tokenizer, model, esm_dim)
        if emb is None:
            tqdm.write(f"  FAIL {pdb_id}")
            failed += 1
            continue

        np.save(str(out_path), emb)
        tqdm.write(f"  OK   {pdb_id:<8}  shape={emb.shape}")
        ok += 1

    print(f"\nDone.  OK={ok}  failed={failed}  skipped={skipped}")
    print(f"ESM2 dim={esm_dim}  |  files in {ESM_DIR}")
    print("\nNext: python scripts/build_graphs_xl.py")


if __name__ == '__main__':
    main()
