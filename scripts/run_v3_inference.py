"""Run PocketGNNXL (v3) on all 59 PCNA structures using ESM2 features."""
import sys, io, csv, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import torch
from sklearn.metrics import roc_auc_score
from sklearn.cluster import DBSCAN
from src.models import PocketGNNXL
from src.data_processing.parse_pdb import parse_pdb, get_ligand_coords, label_pocket_residues
from src.data_processing.graph_construction import build_graph_v2

REPO     = Path(__file__).parent.parent
RAW      = REPO / "data" / "raw"
ESM_DIR  = REPO / "data" / "esm_features"
PDIR     = REPO / "results" / "per_structure"
CKPT     = REPO / "checkpoints" / "pcna" / "best_pcna_v3.ckpt"
OUT_DIR  = REPO / "results" / "v3"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SKIP = {
    'HOH','WAT','SO4','EDO','PEG','GOL','DMS','PO4','MPD','FMT','ACT',
    'MES','HED','BME','DTT','EPE','NHE','IMD','CIT','TRS','FLC','SCN',
    'AZI','NO3','PGE','PE5','PE7','NH4','ACE','MSE','SEP','TPO','PTR',
    'MG','CA','ZN','MN','FE','CU','NA','K','CD','AU','PT','CO','NI',
    'HG','SE','BR','CL','IOD',
    'AGS','ADP','ATP','GTP','GDP','TTP','TMP','DTP','SF4','FES','F3S',
    'DOC','APC','ANP','AMP','CTP','UTP','NAD','FAD','FMN',
}
AOH_GT = {25,26,27,38,39,40,41,42,44,45,46,47,123,125,126,128,231,232,233,234,250,251,252,253}

model = PocketGNNXL().eval()
model.load_state_dict(torch.load(CKPT, map_location="cpu", weights_only=True))
print(f"Loaded PocketGNNXL: {sum(p.numel() for p in model.parameters()):,} params")

rows = list(csv.DictReader(open(PDIR / "summary_table.csv", encoding="utf-8", errors="replace")))
pcna_pdbs = [r["pdb"] for r in rows]
print(f"Running v3 on {len(pcna_pdbs)} PCNA structures...\n")

summary_rows = []

for pdb in pcna_pdbs:
    pdb_path = RAW / f"{pdb}.pdb"
    esm_path = ESM_DIR / f"{pdb}.npy"
    if not pdb_path.exists():
        print(f"  {pdb}: SKIP (no PDB)")
        continue
    if not esm_path.exists():
        print(f"  {pdb}: SKIP (no ESM2 features — run build_esm_features.py)")
        continue

    try:
        residues = parse_pdb(pdb_path)
        data     = build_graph_v2(residues)
        esm_feats = torch.from_numpy(np.load(esm_path)).float()

        if esm_feats.shape[0] != data.x.shape[0]:
            print(f"  {pdb}: SKIP (ESM shape {esm_feats.shape[0]} != graph {data.x.shape[0]})")
            continue

        # Concat ESM2 to hand-crafted features -> 520-dim
        x_xl = torch.cat([data.x, esm_feats], dim=1)

        with torch.no_grad():
            scores = model(x_xl, data.edge_index, data.edge_attr,
                           data.edge_index_seq, data.edge_attr_seq,
                           data.chain_id).numpy()

        # Cluster above threshold
        threshold = 0.4
        high_mask = scores > threshold
        high_idx  = np.where(high_mask)[0]
        coords_all = np.array([r.ca_coord for r in residues])

        clusters = [-1] * len(residues)
        if len(high_idx) >= 3:
            db = DBSCAN(eps=6.0, min_samples=3).fit(coords_all[high_idx])
            for i, idx in enumerate(high_idx):
                clusters[idx] = db.labels_[i]

        # Top cluster
        cluster_ids = [c for c in set(clusters) if c >= 0]
        top_mean, top_n, top_aoh = 0.0, 0, 0
        if cluster_ids:
            best = max(cluster_ids, key=lambda c: scores[[i for i,cl in enumerate(clusters) if cl==c]].mean())
            best_idx = [i for i,cl in enumerate(clusters) if cl==best]
            top_mean = float(scores[best_idx].mean())
            top_n    = len(best_idx)
            top_aoh  = sum(1 for i in best_idx
                           if residues[i].resid in AOH_GT
                           and residues[i].chain in {"A","B","C"})

        # AUROC if ligand available
        auroc = None
        found_ligs = set()
        for line in pdb_path.read_text(errors="ignore").splitlines():
            if line.startswith("HETATM"):
                rn = line[17:20].strip()
                if rn not in SKIP:
                    found_ligs.add(rn)

        chain_sizes = {}
        for r in residues:
            chain_sizes[r.chain] = chain_sizes.get(r.chain, 0) + 1
        pcna_chains = {c for c,n in chain_sizes.items() if 200 <= n <= 300}
        if not pcna_chains:
            pcna_chains = set(chain_sizes.keys())
        mask = np.array([r.chain in pcna_chains for r in residues])

        if found_ligs:
            all_lig = []
            for lig in found_ligs:
                c = get_ligand_coords(pdb_path, resname=lig)
                if c is not None:
                    all_lig.append(c)
            if all_lig:
                lig_coords = np.vstack(all_lig)
                labels = label_pocket_residues(residues, lig_coords, cutoff_angstrom=6.0)
                y = labels[mask]; s = scores[mask]
                if y.sum() >= 2 and (1-y).sum() >= 2:
                    auroc = float(roc_auc_score(y, s))

        # Save per-structure scores
        struct_dir = OUT_DIR / pdb
        struct_dir.mkdir(exist_ok=True)
        with open(struct_dir / "scores.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["chain","resid","resname","score","cluster"])
            for i, (r, sc, cl) in enumerate(zip(residues, scores, clusters)):
                w.writerow([r.chain, r.resid, r.resname, f"{sc:.4f}", cl])

        auroc_str = f"{auroc:.4f}" if auroc else "N/A"
        print(f"  {pdb:6s}: top_score={top_mean:.3f} top_n={top_n:3d} "
              f"aoh={top_aoh:2d}/24 AUROC={auroc_str}")

        summary_rows.append({
            "pdb": pdb,
            "top_cluster_mean": f"{top_mean:.4f}",
            "top_cluster_n": top_n,
            "top_aoh_overlap": top_aoh,
            "auroc_v3": auroc_str,
            "n_residues": len(residues),
            "score_max": f"{scores.max():.4f}",
            "score_mean": f"{scores.mean():.4f}",
        })

    except Exception as e:
        print(f"  {pdb}: ERROR {e}")

# Write summary
with open(OUT_DIR / "v3_summary.csv", "w", newline="", encoding="utf-8") as f:
    if summary_rows:
        w = csv.DictWriter(f, fieldnames=summary_rows[0].keys())
        w.writeheader()
        w.writerows(summary_rows)

# Compare v1 vs v3
print(f"\n{'='*60}")
print("V1 vs V3 AUROC Comparison (structures with drug-like ligands)")
print(f"{'='*60}")
v1_aurocs = {r["pdb"]: float(r["auroc"]) for r in rows if r["auroc"]}
for row in summary_rows:
    pdb = row["pdb"]
    v3a = row["auroc_v3"]
    if v3a != "N/A" and pdb in v1_aurocs:
        delta = float(v3a) - v1_aurocs[pdb]
        arrow = "+" if delta >= 0 else ""
        print(f"  {pdb:6s}: v1={v1_aurocs[pdb]:.4f}  v3={v3a}  delta={arrow}{delta:.4f}")

print(f"\nResults -> {OUT_DIR}")
print(f"Processed: {len(summary_rows)}/{len(pcna_pdbs)} structures")
