"""
Sequence homology check between CryptoSite train and val/test structures.
Flags pairs with sequence identity >= 30% (standard similarity threshold).
Output: data/results/homology_check.json
"""
import json, warnings
import numpy as np
from pathlib import Path
from Bio import SeqIO
from Bio.Align import PairwiseAligner

warnings.filterwarnings("ignore")

REPO    = Path(__file__).parent.parent
RAW     = REPO / "data" / "raw"
RESULTS = REPO / "data" / "results"
SPLIT   = json.loads((REPO / "data/splits/cryptosite_split.json").read_text())["splits"]

TRAIN = SPLIT["train"]
VAL   = SPLIT["val"]
TEST  = SPLIT["test"]

THRESHOLD = 30.0  # % identity flagged as potentially homologous

aligner = PairwiseAligner()
aligner.mode            = "global"
aligner.match_score     = 1
aligner.mismatch_score  = 0
aligner.open_gap_score  = -1
aligner.extend_gap_score = -0.5


# ── extract longest chain sequence from PDB ───────────────────────────────────

AA3 = {
    "ALA":"A","ARG":"R","ASN":"N","ASP":"D","CYS":"C","GLN":"Q","GLU":"E",
    "GLY":"G","HIS":"H","ILE":"I","LEU":"L","LYS":"K","MET":"M","PHE":"F",
    "PRO":"P","SER":"S","THR":"T","TRP":"W","TYR":"Y","VAL":"V",
    "MSE":"M","HSD":"H","HSE":"H","HSP":"H","SEC":"C","PYL":"K",
}

def extract_sequence(pdb_id: str) -> str | None:
    pdb_path = RAW / f"{pdb_id}.pdb"
    if not pdb_path.exists():
        return None
    chains: dict[str, list] = {}
    seen = set()
    for line in pdb_path.read_text(errors="ignore").splitlines():
        if not line.startswith("ATOM"):
            continue
        if line[12:16].strip() != "CA":
            continue
        chain  = line[21]
        resnum = line[22:27].strip()
        resnam = line[17:20].strip()
        key    = (chain, resnum)
        if key in seen:
            continue
        seen.add(key)
        aa = AA3.get(resnam)
        if aa:
            chains.setdefault(chain, []).append(aa)
    if not chains:
        return None
    return "".join(max(chains.values(), key=len))


def pct_identity(a: str, b: str) -> float:
    score  = aligner.score(a, b)
    max_id = min(len(a), len(b))
    return 100.0 * score / max_id if max_id > 0 else 0.0


# ── load sequences ─────────────────────────────────────────────────────────────

print("Extracting sequences...")
train_seqs, val_seqs, test_seqs = {}, {}, {}

for pdb in TRAIN:
    s = extract_sequence(pdb)
    if s:
        train_seqs[pdb] = s
    else:
        print(f"  MISSING: {pdb}")

for pdb in VAL:
    s = extract_sequence(pdb)
    if s:
        val_seqs[pdb] = s

for pdb in TEST:
    s = extract_sequence(pdb)
    if s:
        test_seqs[pdb] = s

print(f"  Train: {len(train_seqs)}/{len(TRAIN)} sequences extracted")
print(f"  Val:   {len(val_seqs)}/{len(VAL)}")
print(f"  Test:  {len(test_seqs)}/{len(TEST)}")

# ── pairwise comparison: train vs val+test ─────────────────────────────────────

print(f"\nRunning pairwise alignment ({len(train_seqs)} train x {len(val_seqs)+len(test_seqs)} val+test)...")

flagged = []
all_pairs = []

held_out = {**{k: (v,"val") for k,v in val_seqs.items()},
            **{k: (v,"test") for k,v in test_seqs.items()}}

for h_id, (h_seq, h_split) in held_out.items():
    best_pct, best_train = 0.0, None
    for t_id, t_seq in train_seqs.items():
        pct = pct_identity(h_seq, t_seq)
        all_pairs.append({"held": h_id, "train": t_id, "pct_identity": round(pct, 2)})
        if pct > best_pct:
            best_pct, best_train = pct, t_id

    status = "FLAGGED" if best_pct >= THRESHOLD else "OK"
    line   = f"  [{h_split.upper():4s}] {h_id:6s}  best match: {best_train} ({best_pct:.1f}%)  {status}"
    print(line)

    if best_pct >= THRESHOLD:
        flagged.append({
            "held_out": h_id, "split": h_split,
            "closest_train": best_train, "pct_identity": round(best_pct, 2)
        })

# ── summary ───────────────────────────────────────────────────────────────────

all_pcts = [p["pct_identity"] for p in all_pairs]

print(f"\n{'='*55}")
print(f"FLAGGED (>= {THRESHOLD}% identity with any training structure): {len(flagged)}")
if flagged:
    for f in flagged:
        print(f"  {f['held_out']} ({f['split']}) ~ {f['closest_train']}: {f['pct_identity']:.1f}%")
else:
    print("  NONE — no val/test structure is homologous to any training structure")
print(f"\nAll-pair identity: mean={np.mean(all_pcts):.1f}%  max={np.max(all_pcts):.1f}%  min={np.min(all_pcts):.1f}%")
print(f"{'='*55}")

result = {
    "threshold_pct": THRESHOLD,
    "n_train": len(train_seqs),
    "n_val":   len(val_seqs),
    "n_test":  len(test_seqs),
    "flagged_pairs": flagged,
    "leakage_detected": len(flagged) > 0,
    "all_pair_stats": {
        "mean": round(np.mean(all_pcts), 2),
        "max":  round(np.max(all_pcts),  2),
        "min":  round(np.min(all_pcts),  2),
    }
}

out = RESULTS / "homology_check.json"
out.write_text(json.dumps(result, indent=2))
print(f"\nSaved -> {out}")
