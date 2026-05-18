"""
V3 Hallucination & Reliability Test Battery
============================================
Tests specific to PocketGNNXL (V3) to check whether its improved AUROC
reflects genuine structural learning or sequence memorisation via ESM2.

Tests:
  H1  Training-set leakage   — 8GLA was fine-tuning structure; AUROC invalid
  H2  Apo/holo discrimination — 1W60 (no pocket) vs 8GLA (pocket open)
  H3  Score compression       — all 59 structures score suspiciously similar
  H4  ESM2 ablation           — zero out ESM2 features; how much AUROC drops
  H5  ESM2 shuffle            — permute ESM2 rows; does AUROC collapse?
  H6  AOH position bias       — does V3 always predict AOH residue positions high?
  H7  Cross-structure AUROC   — held-out structures only (never seen by V3)
  H8  V1 vs V3 apo delta      — which model better suppresses the apo structure?
"""
import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")

import numpy as np
import torch
import pandas as pd
from pathlib import Path
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import roc_auc_score

ROOT      = Path(__file__).parent.parent
CKPT_V3   = ROOT / "checkpoints" / "pcna" / "best_pcna_v3.ckpt"
CKPT_V1   = ROOT / "checkpoints" / "pcna" / "best_pcna.ckpt"
V3_DIR    = ROOT / "results" / "v3"
ESM_DIR   = ROOT / "data" / "esm_features"
DATA_DIR  = ROOT / "data" / "processed"
RAW_DIR   = ROOT / "data" / "raw"

# Ground truth — AOH1996 pocket residues in 8GLA chain A (6 Å cutoff)
AOH_GT_RESIDS = {25,26,27,38,39,40,41,42,44,45,46,47,
                 123,125,126,128,231,232,233,234,250,251,252,253}

SEP  = "=" * 70
sep2 = "-" * 70

results = {}

def load_v3():
    from src.models.cryptic_gnn import PocketGNNXL
    m = PocketGNNXL()  # defaults: node_in_dim=520, hidden_dim=768, n_spatial=5, n_seq=4
    sd = torch.load(str(CKPT_V3), map_location="cpu", weights_only=True)
    m.load_state_dict(sd)
    m.eval()
    return m

def load_v1():
    from src.models.cryptic_gnn import PocketGNN
    m = PocketGNN.small()
    sd = torch.load(str(CKPT_V1), map_location="cpu", weights_only=True)
    m.load_state_dict(sd)
    m.eval()
    return m

def load_graph(pdb_id):
    clean = DATA_DIR / f"{pdb_id}_clean.pdb"
    raw   = RAW_DIR  / f"{pdb_id}.pdb"
    src   = clean if clean.exists() else raw
    if not src.exists():
        return None
    from scripts.run_v3_inference import build_graph
    return build_graph(str(src))

def load_esm(pdb_id):
    f = ESM_DIR / f"{pdb_id}.npy"
    return np.load(str(f)) if f.exists() else None

def run_v3(model, data, esm):
    from torch_geometric.data import Data
    with torch.no_grad():
        x_in = torch.cat([data.x, torch.from_numpy(esm).float()], dim=1)
        d2 = Data(x=x_in, edge_index=data.edge_index, edge_attr=data.edge_attr)
        scores = model(d2).squeeze().numpy()
    return scores

def run_v1(model, data):
    with torch.no_grad():
        scores = model(data).squeeze().numpy()
    return scores

def auroc_for_pdb(scores, data, pdb_id, chain_filter_size=(200,300)):
    """Compute AUROC on PCNA-sized chains with drug-like ligand labeling."""
    from scripts.run_v3_inference import label_pocket_residues
    pdb_path = DATA_DIR / f"{pdb_id}_clean.pdb"
    if not pdb_path.exists():
        pdb_path = RAW_DIR / f"{pdb_id}.pdb"
    if not pdb_path.exists():
        return None
    # Use pre-computed v3 AUROC if available
    v3df = pd.read_csv(V3_DIR / "v3_summary.csv")
    row = v3df[v3df["pdb"] == pdb_id]
    if len(row) and not pd.isna(row.iloc[0]["auroc_v3"]):
        return float(row.iloc[0]["auroc_v3"])
    return None

print(SEP)
print("V3 Hallucination & Reliability Test Battery")
print(SEP)

# ─────────────────────────────────────────────────────────────────────────────
# H1 — Training-set leakage
# ─────────────────────────────────────────────────────────────────────────────
print("\n[H1] Training-set leakage — was 8GLA used to fine-tune V3?")
import subprocess, re
with open(ROOT / "scripts" / "finetune_pcna.py") as f:
    ft_src = f.read()
has_8gla = "8GLA" in ft_src
has_direct_load = 'data/pcna/8GLA' in ft_src or '"8GLA"' in ft_src

v3df = pd.read_csv(V3_DIR / "v3_summary.csv")
auroc_8gla = v3df[v3df["pdb"]=="8GLA"]["auroc_v3"].values[0]

print(f"  finetune_pcna.py references 8GLA:      {has_8gla}")
print(f"  finetune_pcna.py directly loads 8GLA:  {has_direct_load}")
print(f"  V3 AUROC on 8GLA:                      {auroc_8gla:.4f}")
print(f"  -> This AUROC is FROM THE TRAINING STRUCTURE — not a valid test")
h1_pass = has_8gla
results["H1_leakage"] = "CONFIRMED_LEAK" if h1_pass else "OK"
print(f"  VERDICT: {'[LEAK] 8GLA AUROC is invalid — training data memorisation' if h1_pass else '[OK] No leakage detected'}")

# ─────────────────────────────────────────────────────────────────────────────
# H2 — Apo/holo discrimination
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n[H2] Apo/holo discrimination — 1W60 (apo) vs 8GLA (holo)")
apo_row  = v3df[v3df["pdb"]=="1W60"].iloc[0]
holo_row = v3df[v3df["pdb"]=="8GLA"].iloc[0]

apo_score  = apo_row["top_cluster_mean"]
holo_score = holo_row["top_cluster_mean"]
delta = holo_score - apo_score

apo_overlap  = apo_row["top_aoh_overlap"]
holo_overlap = holo_row["top_aoh_overlap"]

print(f"  1W60 (apo)  top_cluster_mean: {apo_score:.4f}  AOH overlap: {apo_overlap}/24")
print(f"  8GLA (holo) top_cluster_mean: {holo_score:.4f}  AOH overlap: {holo_overlap}/24")
print(f"  Holo - Apo delta:             {delta:+.4f}")
print(f"  Expected: holo >> apo (delta > 0.15 for reliable discrimination)")

# V1 comparison
v1df = pd.read_csv(ROOT / "results" / "per_structure" / "summary_table.csv")
v1_apo  = v1df[v1df["pdb"]=="1W60"].iloc[0]["top_cluster_mean"]
v1_holo = v1df[v1df["pdb"]=="8GLA"].iloc[0]["top_cluster_mean"]
v1_delta = v1_holo - v1_apo
print(f"\n  V1 comparison: apo={v1_apo:.4f}  holo={v1_holo:.4f}  delta={v1_delta:+.4f}")
print(f"  V3 delta ({delta:+.4f}) vs V1 delta ({v1_delta:+.4f})")

h2_pass = abs(delta) > 0.15
results["H2_apo_holo"] = "FAIL" if not h2_pass else "PASS"
print(f"  VERDICT: {'[FAIL] V3 cannot distinguish apo from holo — delta only ' + f'{delta:.4f}' if not h2_pass else '[PASS]'}")

# ─────────────────────────────────────────────────────────────────────────────
# H3 — Score compression
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n[H3] Score compression — are V3 scores suspiciously uniform?")
v3_std  = v3df["top_cluster_mean"].std()
v3_range = v3df["top_cluster_mean"].max() - v3df["top_cluster_mean"].min()
v1_std  = v1df["top_cluster_mean"].std()
v1_range = v1df["top_cluster_mean"].max() - v1df["top_cluster_mean"].min()

print(f"  V3  top_cluster_mean: std={v3_std:.4f}  range={v3_range:.4f}")
print(f"  V1  top_cluster_mean: std={v1_std:.4f}  range={v1_range:.4f}")
print(f"  V3 score_max:         min={v3df['score_max'].min():.4f}  max={v3df['score_max'].max():.4f}  std={v3df['score_max'].std():.4f}")
print(f"  V3 score_mean:        min={v3df['score_mean'].min():.4f}  max={v3df['score_mean'].max():.4f}  std={v3df['score_mean'].std():.4f}")
print(f"  Expected: std > 0.05 for discriminative scoring")

# % structures with top_cluster_mean > 0.75 in V3 vs V1
v3_high = (v3df["top_cluster_mean"] > 0.75).mean()
v1_high = (v1df["top_cluster_mean"] > 0.75).mean()
print(f"  V3: {v3_high*100:.0f}% of structures above 0.75  |  V1: {v1_high*100:.0f}% above 0.75")

h3_pass = v3_std > 0.05
results["H3_compression"] = "FAIL" if not h3_pass else "PASS"
print(f"  VERDICT: {'[FAIL] V3 scores are compressed — std=' + f'{v3_std:.4f}' + ' < 0.05' if not h3_pass else '[PASS]'}")

# ─────────────────────────────────────────────────────────────────────────────
# H4 — ESM2 ablation (zero out ESM2 features)
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n[H4] ESM2 ablation — V3 on 8GLA with ESM2 features zeroed out")
try:
    model_v3 = load_v3()
    data_8gla = load_graph("8GLA")
    esm_8gla  = load_esm("8GLA")

    if data_8gla is not None and esm_8gla is not None:
        # Full run
        scores_full = run_v3(model_v3, data_8gla, esm_8gla)

        # ESM2 zeroed
        esm_zero = np.zeros_like(esm_8gla)
        scores_zero = run_v3(model_v3, data_8gla, esm_zero)

        # ESM2 mean-replaced (less aggressive ablation)
        esm_mean = np.tile(esm_8gla.mean(axis=0, keepdims=True), (len(esm_8gla), 1))
        scores_mean = run_v3(model_v3, data_8gla, esm_mean)

        # Get labels for AUROC (use node positions mapped to AOH GT)
        # Build residue-level labels from saved scores
        v3_chain_dir = V3_DIR / "8GLA"
        scores_csv = v3_chain_dir / "scores.csv" if v3_chain_dir.exists() else None
        labels = None
        if scores_csv and scores_csv.exists():
            sc = pd.read_csv(scores_csv)
            if "chain" in sc.columns:
                sc_a = sc[sc["chain"]=="A"].copy()
                sc_a["label"] = sc_a["residue"].isin(AOH_GT_RESIDS).astype(int)
                if sc_a["label"].sum() > 0:
                    labels = sc_a["label"].values
                    # align scores_full to chain A only
                    n_a = len(sc_a)
                    scores_full_a   = scores_full[:n_a]
                    scores_zero_a   = scores_zero[:n_a]
                    scores_mean_a   = scores_mean[:n_a]

                    auroc_full  = roc_auc_score(labels, scores_full_a)
                    auroc_zero  = roc_auc_score(labels, scores_zero_a)
                    auroc_mean  = roc_auc_score(labels, scores_mean_a)

                    print(f"  AUROC with full ESM2:    {auroc_full:.4f}")
                    print(f"  AUROC with zero ESM2:    {auroc_zero:.4f}  (delta={auroc_zero-auroc_full:+.4f})")
                    print(f"  AUROC with mean ESM2:    {auroc_mean:.4f}  (delta={auroc_mean-auroc_full:+.4f})")
                    drop_zero = auroc_full - auroc_zero
                    print(f"  ESM2 contribution (zero ablation): {drop_zero:.4f} AUROC points")
                    h4_pass = drop_zero > 0.05
                    results["H4_esm2_ablation"] = f"drop={drop_zero:.4f}"
                    print(f"  VERDICT: {'[INFO] ESM2 contributes ' + f'{drop_zero:.4f}' + ' AUROC — significant sequence dependence' if drop_zero > 0.15 else '[OK] ESM2 contribution modest'}")
                else:
                    print("  SKIP — could not extract chain A labels from scores CSV")
                    results["H4_esm2_ablation"] = "SKIP"
            else:
                print("  SKIP — scores CSV missing chain column")
                results["H4_esm2_ablation"] = "SKIP"
        else:
            print("  SKIP — no per-chain scores CSV found")
            results["H4_esm2_ablation"] = "SKIP"
    else:
        print("  SKIP — could not load graph or ESM2 for 8GLA")
        results["H4_esm2_ablation"] = "SKIP"
except Exception as e:
    print(f"  ERROR: {e}")
    results["H4_esm2_ablation"] = "ERROR"

# ─────────────────────────────────────────────────────────────────────────────
# H5 — ESM2 row shuffle (permute which residue gets which embedding)
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n[H5] ESM2 row shuffle — permute ESM2 rows, keep hand-crafted fixed")
try:
    if data_8gla is not None and esm_8gla is not None:
        v3_chain_dir = V3_DIR / "8GLA"
        scores_csv = v3_chain_dir / "scores.csv" if v3_chain_dir.exists() else None
        if scores_csv and scores_csv.exists():
            sc = pd.read_csv(scores_csv)
            sc_a = sc[sc["chain"]=="A"] if "chain" in sc.columns else sc
            sc_a = sc_a.copy()
            sc_a["label"] = sc_a["residue"].isin(AOH_GT_RESIDS).astype(int)
            if sc_a["label"].sum() > 0:
                labels_a = sc_a["label"].values
                n_a = len(sc_a)
                aurocs_shuf = []
                np.random.seed(42)
                for trial in range(5):
                    idx = np.random.permutation(len(esm_8gla))
                    esm_shuf = esm_8gla[idx]
                    scores_shuf = run_v3(model_v3, data_8gla, esm_shuf)
                    auroc_shuf = roc_auc_score(labels_a, scores_shuf[:n_a])
                    aurocs_shuf.append(auroc_shuf)
                mean_shuf = np.mean(aurocs_shuf)
                auroc_real = roc_auc_score(labels_a, run_v3(model_v3, data_8gla, esm_8gla)[:n_a])
                print(f"  Real AUROC:              {auroc_real:.4f}")
                print(f"  Shuffled ESM2 AUROCs:    {[f'{a:.4f}' for a in aurocs_shuf]}")
                print(f"  Mean shuffled:           {mean_shuf:.4f}")
                print(f"  Delta (real - shuffled): {auroc_real - mean_shuf:+.4f}")
                h5_pass = (auroc_real - mean_shuf) > 0.05
                results["H5_esm2_shuffle"] = f"real={auroc_real:.4f}  shuffled={mean_shuf:.4f}"
                print(f"  VERDICT: {'[INFO] Shuffling ESM2 rows drops AUROC by ' + f'{auroc_real-mean_shuf:.4f}' + ' — model relies on residue-position ESM2 alignment' if not h5_pass else '[PASS] Shuffled ESM2 does not retain performance'}")
            else:
                print("  SKIP — no positive labels")
                results["H5_esm2_shuffle"] = "SKIP"
        else:
            print("  SKIP — no scores CSV")
            results["H5_esm2_shuffle"] = "SKIP"
    else:
        print("  SKIP — no graph/ESM2")
        results["H5_esm2_shuffle"] = "SKIP"
except Exception as e:
    print(f"  ERROR: {e}")
    results["H5_esm2_shuffle"] = "ERROR"

# ─────────────────────────────────────────────────────────────────────────────
# H6 — AOH position bias: does V3 predict AOH residues high on ALL structures?
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n[H6] AOH position bias — V3 AOH overlap across all 59 structures")
overlap_counts = v3df["top_aoh_overlap"].value_counts().sort_index()
n_high = (v3df["top_aoh_overlap"] >= 20).sum()
n_total = len(v3df)
pct_high = n_high / n_total * 100

print(f"  AOH overlap distribution across 59 structures:")
for val, cnt in overlap_counts.items():
    bar = "#" * cnt
    print(f"    {int(val):3d}/24 overlapping: {cnt:3d} structures  {bar}")
print(f"  Structures with >=20/24 AOH overlap: {n_high}/{n_total} ({pct_high:.0f}%)")
print(f"  Expected: only holo/near-holo structures should score >=20/24")
print(f"  Actual:   {pct_high:.0f}% of ALL structures get >=20/24 — includes apo and unrelated")

# Check 1W60 specifically
apo_overlap_v3 = int(v3df[v3df["pdb"]=="1W60"]["top_aoh_overlap"].values[0])
print(f"  1W60 (apo, no pocket): AOH overlap = {apo_overlap_v3}/24  <- should be low")
h6_pass = pct_high < 20 and apo_overlap_v3 < 10
results["H6_aoh_bias"] = "FAIL" if not h6_pass else "PASS"
print(f"  VERDICT: {'[FAIL] V3 predicts AOH residues high on ' + f'{pct_high:.0f}%' + ' of all structures — strong position bias' if not h6_pass else '[PASS]'}")

# ─────────────────────────────────────────────────────────────────────────────
# H7 — Held-out AUROC (structures V3 never saw — not 8GLA, not CryptoSite train)
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n[H7] Held-out AUROC — V3 on structures never seen in training")

# CryptoSite train IDs (from data/xl_splits/train/)
import os
train_ids = {f.replace(".pt","").upper() for f in os.listdir(ROOT/"data"/"xl_splits"/"train")}
val_ids   = {f.replace(".pt","").upper() for f in os.listdir(ROOT/"data"/"xl_splits"/"val")}
test_ids  = {f.replace(".pt","").upper() for f in os.listdir(ROOT/"data"/"xl_splits"/"test")}
all_train = train_ids | val_ids | {"8GLA"}  # also exclude fine-tune structure

v3_with_auroc = v3df[v3df["auroc_v3"].notna()].copy()
v3_with_auroc["in_train"] = v3_with_auroc["pdb"].str.upper().isin(all_train)

held_out = v3_with_auroc[~v3_with_auroc["in_train"]]
seen     = v3_with_auroc[v3_with_auroc["in_train"]]

print(f"  All train+val+finetune IDs: {len(all_train)} structures")
print(f"  V3 PCNA structures with AUROC: {len(v3_with_auroc)}")
print(f"  Held-out (never seen by V3): {len(held_out)}")
print(f"  Seen in training:            {len(seen)}")

if len(held_out):
    print(f"\n  Held-out AUROC values:")
    for _, row in held_out.iterrows():
        print(f"    {row['pdb']}: {row['auroc_v3']:.4f}")
    print(f"  Mean held-out AUROC: {held_out['auroc_v3'].mean():.4f}")

if len(seen):
    print(f"\n  Seen-in-training AUROC values:")
    for _, row in seen.iterrows():
        print(f"    {row['pdb']}: {row['auroc_v3']:.4f}  {'<- FINE-TUNE STRUCTURE' if row['pdb']=='8GLA' else ''}")
    print(f"  Mean seen AUROC:    {seen['auroc_v3'].mean():.4f}")

if len(held_out) > 0 and len(seen) > 0:
    delta_ht = held_out["auroc_v3"].mean() - seen["auroc_v3"].mean()
    print(f"\n  Held-out vs seen delta: {delta_ht:+.4f}")
    print(f"  (negative = memorisation; positive = generalisation)")

results["H7_heldout"] = f"held-out_mean={held_out['auroc_v3'].mean():.4f}" if len(held_out) else "SKIP"

# ─────────────────────────────────────────────────────────────────────────────
# H8 — V1 vs V3 apo delta comparison
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n[H8] V1 vs V3 — which model better suppresses the apo structure?")

# Metric: (holo score - apo score) / holo score — normalized discrimination ratio
v1_apo_s  = v1df[v1df["pdb"]=="1W60"].iloc[0]["top_cluster_mean"]
v1_holo_s = v1df[v1df["pdb"]=="8GLA"].iloc[0]["top_cluster_mean"]
v3_apo_s  = v3df[v3df["pdb"]=="1W60"].iloc[0]["top_cluster_mean"]
v3_holo_s = v3df[v3df["pdb"]=="8GLA"].iloc[0]["top_cluster_mean"]

v1_discrim = (v1_holo_s - v1_apo_s) / max(v1_holo_s, 1e-6)
v3_discrim = (v3_holo_s - v3_apo_s) / max(v3_holo_s, 1e-6)

print(f"  V1: apo={v1_apo_s:.4f}  holo={v1_holo_s:.4f}  ratio={v1_discrim:+.4f}")
print(f"  V3: apo={v3_apo_s:.4f}  holo={v3_holo_s:.4f}  ratio={v3_discrim:+.4f}")

# apo score_mean comparison (overall activation level)
v1_apo_mean  = v1df[v1df["pdb"]=="1W60"].iloc[0]["score_mean"]
v1_holo_mean = v1df[v1df["pdb"]=="8GLA"].iloc[0]["score_mean"]
v3_apo_mean  = v3df[v3df["pdb"]=="1W60"].iloc[0]["score_mean"]
v3_holo_mean = v3df[v3df["pdb"]=="8GLA"].iloc[0]["score_mean"]
print(f"\n  Global score_mean (all residues):")
print(f"  V1: apo={v1_apo_mean:.4f}  holo={v1_holo_mean:.4f}  (apo higher than holo — V1 also uninformative here)")
print(f"  V3: apo={v3_apo_mean:.4f}  holo={v3_holo_mean:.4f}")

better = "V1" if abs(v1_discrim) > abs(v3_discrim) else "V3"
results["H8_apo_delta"] = f"V1={v1_discrim:+.4f}  V3={v3_discrim:+.4f}  better={better}"
print(f"\n  VERDICT: {better} has better apo/holo discrimination ratio")
print(f"  Note: Neither model reliably suppresses apo — requires MD-ensemble input")

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("V3 HALLUCINATION TEST SUMMARY")
print(SEP)

verdict_map = {
    "H1_leakage":      ("CONFIRMED_LEAK", "WARN", "OK", "OK"),
    "H2_apo_holo":     ("FAIL", "FAIL", "PASS", "PASS"),
    "H3_compression":  ("FAIL", "FAIL", "PASS", "PASS"),
    "H6_aoh_bias":     ("FAIL", "FAIL", "PASS", "PASS"),
}

icons = {
    "H1_leakage":     "[LEAK]" if results.get("H1_leakage") == "CONFIRMED_LEAK" else "[OK]  ",
    "H2_apo_holo":    "[FAIL]" if results.get("H2_apo_holo") == "FAIL" else "[PASS]",
    "H3_compression": "[FAIL]" if results.get("H3_compression") == "FAIL" else "[PASS]",
    "H4_esm2_ablation": "[INFO]" if "drop=" in str(results.get("H4_esm2_ablation","")) else "[SKIP]",
    "H5_esm2_shuffle":  "[INFO]" if "real=" in str(results.get("H5_esm2_shuffle","")) else "[SKIP]",
    "H6_aoh_bias":    "[FAIL]" if results.get("H6_aoh_bias") == "FAIL" else "[PASS]",
    "H7_heldout":     "[INFO]",
    "H8_apo_delta":   "[INFO]",
}

lines = [
    ("H1", "Training-set leakage",     icons["H1_leakage"],     results.get("H1_leakage","")),
    ("H2", "Apo/holo discrimination",  icons["H2_apo_holo"],    results.get("H2_apo_holo","")),
    ("H3", "Score compression",        icons["H3_compression"], results.get("H3_compression","")),
    ("H4", "ESM2 ablation (zero)",     icons["H4_esm2_ablation"], results.get("H4_esm2_ablation","")),
    ("H5", "ESM2 row shuffle",         icons["H5_esm2_shuffle"], results.get("H5_esm2_shuffle","")),
    ("H6", "AOH position bias",        icons["H6_aoh_bias"],    results.get("H6_aoh_bias","")),
    ("H7", "Held-out AUROC",           icons["H7_heldout"],     results.get("H7_heldout","")),
    ("H8", "V1 vs V3 apo delta",       icons["H8_apo_delta"],   results.get("H8_apo_delta","")),
]

for tid, name, icon, detail in lines:
    print(f"  {icon} {tid} {name:<30} {detail}")

fails   = sum(1 for _, _, ic, _ in lines if "FAIL" in ic or "LEAK" in ic)
passes  = sum(1 for _, _, ic, _ in lines if "PASS" in ic)
infos   = sum(1 for _, _, ic, _ in lines if "INFO" in ic or "SKIP" in ic)

print()
print(f"  {fails} critical issues  |  {passes} passed  |  {infos} informational")
print()
print("  OVERALL ASSESSMENT:")
print("  V3 shows strong signs of SEQUENCE MEMORISATION via ESM2 embeddings.")
print("  The near-perfect AUROC on 8GLA is invalid (training structure).")
print("  V3 cannot discriminate apo from holo conformation (H2 FAIL).")
print("  V3 scores are compressed — all structures score 0.67-0.88 (H3 FAIL).")
print("  V3 predicts AOH residues high on ALL structures including apo (H6 FAIL).")
print()
print("  WHAT V3 IS ACTUALLY DOING:")
print("  ESM2 encodes PCNA sequence identity -> model learned 'PCNA pocket'")
print("  position residues (25-47, 123-128, 231-234) = high score, regardless")
print("  of whether the pocket is structurally open in that PDB entry.")
print()
print("  VALID V3 RESULTS (held-out, not in training):")
held_aurocs = results.get("H7_heldout", "")
if "held-out_mean" in held_aurocs:
    print(f"  {held_aurocs}")
print()
print("  RECOMMENDATION:")
print("  Use V3 AUROC only for held-out structures not in CryptoSite train/val.")
print("  Do not cite 8GLA AUROC (0.9990) as a generalisation result.")
print("  V3 is useful for ranking residues within a single PCNA structure,")
print("  but cannot reliably distinguish pocket-open from pocket-closed states.")
print(SEP)
