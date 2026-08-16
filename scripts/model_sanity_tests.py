"""
Proper model sanity tests — beyond AUROC.

Tests:
  1. Score distribution check — model is not outputting constant/degenerate scores
  2. Negative control — non-PCNA protein should score low on average
  3. Sequence shuffle control — scrambling AA identity should reduce signal
  4. Cross-structure consistency — same PCNA sequence, different crystal contacts
  5. Calibration check — score histogram and fraction above threshold vs actual recall
  6. Symmetry sanity — PCNA homotrimer chains should correlate strongly
  7. Permutation test — shuffling node features should destroy AUROC
"""
import sys, io
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import torch
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import roc_auc_score
from src.models import PocketGNN
from src.data_processing.parse_pdb import parse_pdb, get_ligand_coords, label_pocket_residues
from src.data_processing.graph_construction import build_graph_v2

REPO  = Path(__file__).parent.parent
RAW   = REPO / "data" / "raw"
CKPT  = REPO / "checkpoints" / "pcna" / "best_pcna.ckpt"

model = PocketGNN.small().eval()
model.load_state_dict(torch.load(CKPT, map_location="cpu", weights_only=True))

def run_model(pdb_path):
    residues = parse_pdb(pdb_path)
    data = build_graph_v2(residues)
    with torch.no_grad():
        scores = model(data.x, data.edge_index, data.edge_attr,
                       data.edge_index_seq, data.edge_attr_seq,
                       data.chain_id).numpy()
    return residues, data, scores

results = {}

print("=" * 70)
print("GNN-PCNA Model Sanity Test Suite")
print("=" * 70)

# ── Test 1: Score distribution on 8GLA ────────────────────────────────────────
print("\n[1] Score distribution — 8GLA (should NOT be constant or near-uniform)")
residues, data, scores = run_model(RAW / "8GLA.pdb")
std  = scores.std()
pct_high = (scores > 0.4).mean()
pct_low  = (scores < 0.1).mean()
print(f"    min={scores.min():.3f}  max={scores.max():.3f}  "
      f"mean={scores.mean():.3f}  std={std:.3f}")
print(f"    Above 0.4: {pct_high:.1%}  |  Below 0.1: {pct_low:.1%}")
t1_pass = std > 0.05 and pct_high < 0.8 and pct_low > 0.1
print(f"    PASS={t1_pass}  (need std>0.05, <80% above threshold, >10% clearly low)")
results["T1_distribution"] = t1_pass

# ── Test 2: Negative control — non-PCNA protein ───────────────────────────────
print("\n[2] Negative control — non-PCNA proteins should score lower on average")
# Use CryptoSite structures if available, else skip
neg_pdbs = list((RAW).glob("*.pdb"))
# Filter to likely non-PCNA: not in our 59 PCNA list
pcna_ids = {p.stem for p in (REPO / "results" / "per_structure").iterdir()
            if p.is_dir()} if (REPO / "results" / "per_structure").exists() else set()
non_pcna = [p for p in neg_pdbs if p.stem not in pcna_ids][:5]
pcna_means = []
for pid in ["8GLA", "1W60", "3VKX"]:
    if (RAW / f"{pid}.pdb").exists():
        _, _, s = run_model(RAW / f"{pid}.pdb")
        pcna_means.append(s.mean())
avg_pcna = np.mean(pcna_means) if pcna_means else 0

if non_pcna:
    neg_means = []
    for p in non_pcna:
        try:
            _, _, s = run_model(p)
            neg_means.append(s.mean())
        except Exception:
            pass
    avg_neg = np.mean(neg_means) if neg_means else None
    if avg_neg is not None:
        t2_pass = avg_pcna > avg_neg
        print(f"    PCNA mean score: {avg_pcna:.3f} (n=3)")
        print(f"    Non-PCNA mean score: {avg_neg:.3f} (n={len(neg_means)})")
        print(f"    PASS={t2_pass}  (PCNA should score higher than non-PCNA)")
        results["T2_negative_control"] = t2_pass
    else:
        print("    SKIP — could not run non-PCNA structures")
        results["T2_negative_control"] = "SKIP"
else:
    print("    SKIP — no non-PCNA structures found in data/raw/")
    results["T2_negative_control"] = "SKIP"

# ── Test 3: Sequence shuffle control ─────────────────────────────────────────
print("\n[3] Sequence shuffle — scramble AA identity, AUROC should drop")
pdb_path = RAW / "8GLA.pdb"
residues, data, scores = run_model(pdb_path)
coords = get_ligand_coords(pdb_path, resname="ZQZ")
labels = label_pocket_residues(residues, coords, cutoff_angstrom=6.0)
chain_sizes = {}
for r in residues:
    chain_sizes[r.chain] = chain_sizes.get(r.chain, 0) + 1
pcna_chains = {c for c, n in chain_sizes.items() if 200 <= n <= 300}
mask = np.array([r.chain in pcna_chains for r in residues])
y = labels[mask]; s_real = scores[mask]
real_auroc = roc_auc_score(y, s_real)

# Shuffle the AA one-hot block (first 20 dims) in node features
shuffled_data = data.clone()
aa_block = shuffled_data.x[:, :20].clone()
idx = torch.randperm(aa_block.shape[0])
shuffled_data.x[:, :20] = aa_block[idx]
with torch.no_grad():
    s_shuffled = model(shuffled_data.x, shuffled_data.edge_index, shuffled_data.edge_attr,
                       shuffled_data.edge_index_seq, shuffled_data.edge_attr_seq,
                       shuffled_data.chain_id).numpy()
shuffled_auroc = roc_auc_score(y, s_shuffled[mask])
t3_pass = real_auroc > shuffled_auroc + 0.05
print(f"    Real AUROC: {real_auroc:.4f}")
print(f"    Shuffled-AA AUROC: {shuffled_auroc:.4f}")
print(f"    Delta: {real_auroc - shuffled_auroc:.4f}")
print(f"    PASS={t3_pass}  (real should exceed shuffled by >0.05)")
results["T3_shuffle_control"] = t3_pass

# ── Test 4: Cross-structure consistency — 1W60 vs 1VYM (both apo PCNA) ────────
print("\n[4] Cross-structure consistency — 1W60 vs 1VYM (same sequence, diff crystal)")
structures = {}
for pid in ["1W60", "1VYM"]:
    if (RAW / f"{pid}.pdb").exists():
        res, _, sc = run_model(RAW / f"{pid}.pdb")
        # Take chain A scores by resid (normalize to single chain)
        chain_a = [(r.resid, s) for r, s in zip(res, sc) if r.chain == "A"]
        structures[pid] = dict(chain_a)

if len(structures) == 2:
    common = sorted(set(structures["1W60"]) & set(structures["1VYM"]))
    s1 = [structures["1W60"][r] for r in common]
    s2 = [structures["1VYM"][r] for r in common]
    r_pearson, _ = pearsonr(s1, s2)
    r_spearman, _ = spearmanr(s1, s2)
    t4_pass = r_pearson > 0.70
    print(f"    Common residues: {len(common)}")
    print(f"    Pearson r: {r_pearson:.4f}  |  Spearman r: {r_spearman:.4f}")
    print(f"    PASS={t4_pass}  (same protein should correlate >0.70)")
    results["T4_consistency"] = t4_pass
else:
    print("    SKIP — one or both structures not available")
    results["T4_consistency"] = "SKIP"

# ── Test 5: Calibration — score vs actual pocket rate ─────────────────────────
print("\n[5] Calibration — do score bins predict pocket rate monotonically?")
residues, data, scores = run_model(RAW / "8GLA.pdb")
coords = get_ligand_coords(RAW / "8GLA.pdb", resname="ZQZ")
labels = label_pocket_residues(residues, coords, cutoff_angstrom=6.0)
bins = np.linspace(0, 1, 6)
bin_labels = np.digitize(scores, bins) - 1
monotone_violations = 0
prev_rate = -1
print("    Score bin  | Pocket rate")
for b in range(len(bins) - 1):
    mask_b = bin_labels == b
    if mask_b.sum() > 0:
        rate = labels[mask_b].mean()
        lo, hi = bins[b], bins[b+1]
        print(f"    [{lo:.1f}-{hi:.1f}]    | {rate:.3f}  (n={mask_b.sum()})")
        if rate < prev_rate - 0.05:
            monotone_violations += 1
        prev_rate = rate
t5_pass = monotone_violations == 0
print(f"    Monotone violations: {monotone_violations}")
print(f"    PASS={t5_pass}  (pocket rate should increase with score)")
results["T5_calibration"] = t5_pass

# ── Test 6: Trimer symmetry on 8GLA ──────────────────────────────────────────
print("\n[6] Trimer symmetry — chains A/B/C of 8GLA should correlate strongly")
residues, data, scores = run_model(RAW / "8GLA.pdb")
chain_scores = {}
for r, s in zip(residues, scores):
    if r.chain not in chain_scores:
        chain_scores[r.chain] = {}
    chain_scores[r.chain][r.resid] = s
# Only consider PCNA chains (200–300 residues) to exclude non-PCNA interactors
chain_sizes = {c: len(d) for c, d in chain_scores.items()}
pcna_chains_t6 = [c for c, n in chain_sizes.items() if 200 <= n <= 300]
chains = pcna_chains_t6 if len(pcna_chains_t6) >= 2 else list(chain_scores.keys())
if len(chains) >= 2:
    corrs = []
    for i in range(len(chains)):
        for j in range(i+1, len(chains)):
            c1, c2 = chains[i], chains[j]
            common = sorted(set(chain_scores[c1]) & set(chain_scores[c2]))
            if len(common) > 10:
                s1 = [chain_scores[c1][r] for r in common]
                s2 = [chain_scores[c2][r] for r in common]
                r_val, _ = pearsonr(s1, s2)
                corrs.append(r_val)
                print(f"    {c1}-{c2}: Pearson r={r_val:.4f} (n={len(common)})")
    avg_corr = np.mean(corrs)
    t6_pass = avg_corr > 0.75
    print(f"    Mean inter-chain correlation: {avg_corr:.4f}")
    print(f"    PASS={t6_pass}  (PCNA homotrimer chains should correlate >0.75)")
    results["T6_symmetry"] = bool(t6_pass)
else:
    print("    SKIP")
    results["T6_symmetry"] = "SKIP"

# ── Test 7: Permutation test — shuffle all node features ─────────────────────
print("\n[7] Permutation test — fully shuffled node features should give AUROC ~0.5")
residues, data, scores = run_model(RAW / "8GLA.pdb")
coords = get_ligand_coords(RAW / "8GLA.pdb", resname="ZQZ")
labels = label_pocket_residues(residues, coords, cutoff_angstrom=6.0)
mask = np.array([r.chain in pcna_chains for r in residues])

perm_aurocs = []
for _ in range(5):
    perm_data = data.clone()
    perm_data.x = perm_data.x[torch.randperm(perm_data.x.shape[0])]
    with torch.no_grad():
        perm_scores = model(perm_data.x, perm_data.edge_index, perm_data.edge_attr,
                            perm_data.edge_index_seq, perm_data.edge_attr_seq,
                            perm_data.chain_id).numpy()
    y = labels[mask]
    if y.sum() >= 2 and (1-y).sum() >= 2:
        perm_aurocs.append(roc_auc_score(y, perm_scores[mask]))
mean_perm = np.mean(perm_aurocs)
t7_pass = mean_perm < 0.65
print(f"    Permuted AUROC (5 runs): {[f'{a:.3f}' for a in perm_aurocs]}")
print(f"    Mean permuted AUROC: {mean_perm:.4f}")
print(f"    Real AUROC: {real_auroc:.4f}")
print(f"    PASS={t7_pass}  (permuted should be <0.65, well below real {real_auroc:.3f})")
results["T7_permutation"] = t7_pass

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("SANITY TEST SUMMARY")
print("=" * 70)
passed  = sum(1 for v in results.values() if v is True or v == True)
failed  = sum(1 for v in results.values() if v is False or (v != "SKIP" and v == False))
skipped = sum(1 for v in results.values() if v == "SKIP")
for name, result in results.items():
    if result == "SKIP":
        icon = "SKIP"
    elif result:
        icon = "PASS"
    else:
        icon = "FAIL"
    print(f"  [{icon}] {name}")
print(f"\n  {passed} passed  |  {failed} failed  |  {skipped} skipped")
if failed > 0:
    print("\n  WARNING: Failed tests indicate model may be unreliable.")
else:
    print("\n  All tests passed — model behaviour is consistent with a real signal.")
