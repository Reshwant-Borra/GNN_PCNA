"""
GNN-PCNA: Cryptic Pocket Predictor — Streamlit UI

Run:
    streamlit run src/ui/app.py

All inference runs 100% locally (PyTorch). No model API calls.
RCSB fetch is only used to download the input PDB file (optional — upload instead).
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import streamlit as st
import torch

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.models import PocketGNN, CrypticGNN
from src.data_processing.parse_pdb import parse_pdb
from src.data_processing.graph_construction import build_graph_v2, build_graph

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GNN-PCNA Pocket Predictor",
    page_icon="",
    layout="wide",
)

RAW_DIR = REPO_ROOT / "data" / "raw"
RCSB_DL = "https://files.rcsb.org/download/{}.pdb"

# Residues within 6 A of AOH1996 (ZQZ) in 8GLA — extracted from 8GLA.pt labels
# Chain C is unlabeled (ligand is at A-B interface only)
_8GLA_GT: dict[str, set[int]] = {
    "A": {25, 26, 27, 38, 39, 40, 41, 42, 44, 45, 46, 47,
          123, 125, 126, 128, 231, 232, 233, 234, 250, 251, 252, 253},
    "B": {23, 25, 26, 27, 38, 39, 40, 41, 42, 44, 45, 46, 47,
          123, 125, 126, 128, 231, 232, 233, 234, 250, 251, 252},
    "C": set(),
    "D": set(),
}

KNOWN_ANNOTATIONS = {
    "8GLA": "Ground truth — AOH1996 cryptic pocket OPEN (ZQZ ligand)",
    "1W60": "Apo baseline — cryptic pocket absent",
    "4RJF": "Highest-resolution apo (2.0 A)",
    "1U7B": "Highest resolution overall (1.88 A)",
    "1AXC": "PIP-box complex (p21)",
    "9N3L": "HSP90alpha inhibitor — investigate for second cryptic site",
}

SS_LABELS = {"H": "Helix", "E": "Sheet", "C": "Coil", "": "Unknown"}


# ── helpers ───────────────────────────────────────────────────────────────────

@st.cache_resource
def load_model(config: str) -> torch.nn.Module:
    if config == "v2-large":
        return PocketGNN().eval()
    elif config == "v2-medium":
        return PocketGNN.medium().eval()
    elif config == "v2-small":
        return PocketGNN.small().eval()
    else:
        return CrypticGNN().eval()


@st.cache_data(show_spinner=False)
def fetch_pdb_bytes(pdb_id: str) -> bytes | None:
    local = RAW_DIR / f"{pdb_id.upper()}.pdb"
    if local.exists():
        return local.read_bytes()
    try:
        import requests
        r = requests.get(RCSB_DL.format(pdb_id.upper()), timeout=20)
        r.raise_for_status()
        return r.content
    except Exception:
        return None


def run_inference(pdb_bytes: bytes, model: torch.nn.Module,
                  progress=None) -> dict | None:
    with tempfile.NamedTemporaryFile(suffix=".pdb", delete=False) as tmp:
        tmp.write(pdb_bytes)
        tmp_path = Path(tmp.name)
    try:
        if progress:
            progress.progress(0.15, "Parsing PDB structure...")
        residues = parse_pdb(tmp_path)
        if not residues:
            return None

        if progress:
            progress.progress(0.40, "Building graph...")
        if isinstance(model, PocketGNN):
            data = build_graph_v2(residues, labels=None)
            if progress:
                progress.progress(0.65, "Running PocketGNN forward pass...")
            with torch.no_grad():
                scores = model(
                    data.x, data.edge_index, data.edge_attr,
                    data.edge_index_seq, data.edge_attr_seq,
                    data.chain_id,
                ).numpy()
        else:
            data = build_graph(residues, labels=None)
            if progress:
                progress.progress(0.65, "Running CrypticGNN forward pass...")
            with torch.no_grad():
                scores = model(data.x, data.edge_index, data.edge_attr).numpy()

        if progress:
            progress.progress(1.0, "Done.")

        return {"residues": residues, "scores": scores,
                "pdb_bytes": pdb_bytes, "data": data}
    except Exception as e:
        st.error(f"Inference failed: {e}")
        return None
    finally:
        os.unlink(tmp_path)


def run_sanity_test(model: torch.nn.Module) -> tuple[bool, str]:
    """Forward + backward on synthetic data. Returns (passed, message)."""
    import torch
    from src.models.cryptic_gnn import focal_loss
    from torch_geometric.data import Data

    N, E = 24, 50
    E_seq = 2 * (N - 1)
    x             = torch.randn(N, 40)
    edge_index    = torch.randint(0, N, (2, E))
    edge_attr     = torch.randn(E, 6)
    src_s = torch.arange(N - 1)
    dst_s = torch.arange(1, N)
    edge_index_seq = torch.stack([
        torch.cat([src_s, dst_s]),
        torch.cat([dst_s, src_s]),
    ])
    edge_attr_seq = torch.randn(E_seq, 6)
    y = torch.randint(0, 2, (N,)).float()

    try:
        model.train()
        if isinstance(model, PocketGNN):
            scores = model(x, edge_index, edge_attr,
                           edge_index_seq, edge_attr_seq)
        else:
            scores = model(x, edge_index, edge_attr)

        assert scores.shape == (N,)
        assert 0.0 <= float(scores.min()) and float(scores.max()) <= 1.0

        loss = focal_loss(scores, y)
        loss.backward()
        model.zero_grad()
        model.eval()

        n = sum(p.numel() for p in model.parameters())
        return True, (f"PASSED  |  N={N} synthetic nodes  |  "
                      f"scores=[{scores.min():.3f}, {scores.max():.3f}]  |  "
                      f"loss={loss.item():.4f}  |  params={n:,}")
    except Exception as e:
        model.eval()
        return False, f"FAILED: {e}"


def cluster_pockets(residues, scores: np.ndarray, threshold: float):
    """DBSCAN pocket clustering on high-scoring Cα coordinates."""
    from sklearn.cluster import DBSCAN
    high_idx = np.where(scores >= threshold)[0]
    if len(high_idx) < 3:
        return []

    coords = np.array([residues[i].ca_coord for i in high_idx])
    db = DBSCAN(eps=6.0, min_samples=3, metric="euclidean").fit(coords)
    labels = db.labels_

    pockets = []
    for cid in sorted(set(labels)):
        if cid == -1:
            continue
        idx_in_cluster = high_idx[labels == cid]
        cluster_scores = scores[idx_in_cluster]
        cluster_coords = np.array([residues[i].ca_coord for i in idx_in_cluster])
        center = cluster_coords.mean(axis=0)
        pockets.append({
            "pocket_id"    : len(pockets) + 1,
            "n_residues"   : len(idx_in_cluster),
            "mean_score"   : float(cluster_scores.mean()),
            "max_score"    : float(cluster_scores.max()),
            "center_A"     : center,
            "residue_idxs" : idx_in_cluster,
        })

    pockets.sort(key=lambda p: p["mean_score"] * (p["n_residues"] ** 0.5), reverse=True)
    for i, p in enumerate(pockets):
        p["rank"] = i + 1
    return pockets


def export_bfactor_pdb(pdb_bytes: bytes, residues, scores: np.ndarray) -> str:
    score_map = {(r.chain, r.resid): float(s) * 100
                 for r, s in zip(residues, scores)}
    lines_out = []
    for line in pdb_bytes.decode("utf-8", errors="ignore").splitlines():
        if line.startswith("ATOM"):
            try:
                chain = line[21]
                resid = int(line[22:26].strip())
                prob  = score_map.get((chain, resid), 0.0)
                line  = line[:60] + f"{prob:6.2f}" + (line[66:] if len(line) > 66 else "")
            except (ValueError, IndexError):
                pass
        lines_out.append(line)
    return "\n".join(lines_out)


# ── sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("GNN-PCNA")
    st.caption("Cryptic Pocket Predictor")
    st.caption("Inference: 100% local — no API calls")
    st.divider()

    input_mode = st.radio("Input", ["PDB ID", "Upload PDB"], horizontal=True)
    pdb_bytes  = None
    pdb_label  = ""

    if input_mode == "PDB ID":
        pdb_id = st.text_input("PDB ID", value="8GLA").strip().upper()
        col_fetch, col_local = st.columns(2)
        with col_fetch:
            fetch_btn = st.button("Fetch RCSB", type="primary")
        with col_local:
            local_path = RAW_DIR / f"{pdb_id}.pdb"
            local_exists = local_path.exists()
            if st.button("Load local", disabled=not local_exists,
                         help=str(local_path) if local_exists else "Not cached locally"):
                pdb_bytes = local_path.read_bytes()
                pdb_label = pdb_id
                st.success(f"Loaded {pdb_id} from disk")

        if fetch_btn:
            with st.spinner(f"Fetching {pdb_id}..."):
                pdb_bytes = fetch_pdb_bytes(pdb_id)
            if pdb_bytes:
                st.success(f"Loaded {pdb_id} ({len(pdb_bytes)//1024} KB)")
                pdb_label = pdb_id
                if pdb_id in KNOWN_ANNOTATIONS:
                    st.info(KNOWN_ANNOTATIONS[pdb_id])
            else:
                st.error(f"Could not fetch {pdb_id}")
    else:
        uploaded = st.file_uploader("Upload .pdb", type=["pdb"])
        if uploaded:
            pdb_bytes = uploaded.read()
            pdb_label = uploaded.name.replace(".pdb", "").upper()
            st.success(f"Loaded {pdb_label}")

    st.divider()
    model_choice = st.selectbox(
        "Model",
        ["v2-small (~850k params)", "v2-medium (~3.2M params)",
         "v2-large (~10.4M params)", "v1-baseline"],
        index=0,
        help="small recommended for inference; large for fine-tuned checkpoints",
    )
    model_key = model_choice.split(" ")[0]

    ckpt_file = st.file_uploader("Load checkpoint (.ckpt)", type=["ckpt", "pt"],
                                 help="Optional trained weights file")

    threshold = st.slider("Pocket threshold", 0.0, 1.0, 0.35, 0.05,
                          help="Residues above this score flagged as pocket candidates")

    st.divider()
    sanity_btn = st.button("Run sanity test", help="Validate model on synthetic data before loading real PDB")
    run_btn    = st.button("Run inference", type="primary", disabled=pdb_bytes is None)


# ── main area ─────────────────────────────────────────────────────────────────

st.title("Cryptic Pocket Predictor")
st.caption("GNN-PCNA  *  PocketGNN v2  *  Dual-branch GATv2Conv  *  Local inference only")

# ── load model ────────────────────────────────────────────────────────────────
model = load_model(model_key)
if ckpt_file is not None:
    try:
        state = torch.load(io.BytesIO(ckpt_file.read()), map_location="cpu", weights_only=True)
        model.load_state_dict(state)
        model.eval()
        st.sidebar.success("Checkpoint loaded")
    except Exception as e:
        st.sidebar.error(f"Checkpoint error: {e}")

n_params = model.param_count() if hasattr(model, "param_count") else sum(p.numel() for p in model.parameters())

# ── sanity test ───────────────────────────────────────────────────────────────
if sanity_btn:
    with st.spinner("Running sanity test on synthetic data..."):
        passed, msg = run_sanity_test(model)
    if passed:
        st.success(f"Sanity test {msg}")
    else:
        st.error(f"Sanity test {msg}")

if not run_btn or pdb_bytes is None:
    st.info("Load a PDB in the sidebar and click **Run inference**.")

    with st.expander("Model architecture"):
        st.markdown(f"""
**{model.__class__.__name__}** — `{model_key}` — **{n_params:,} parameters**

| Component | Detail |
|---|---|
| Node features | 40 dims — aa_onehot (20), SASA, secondary structure (3), B-factor, rel_pos, hydrophobicity, charge, VdW volume, flexibility, pseudo-dihedrals (4), local density 5A/10A, interface flag, chain_onehot (3) |
| Edge features | 6 dims — distance_norm, 1/(1+d), seq_sep_norm, same_chain, is_backbone, cross_chain |
| Spatial branch | 4x GATv2Conv on contact graph (8 A cutoff), residual + LayerNorm |
| Sequential branch | 3x GATv2Conv on backbone graph (|i-j|<=2), residual + LayerNorm |
| Fusion | Learned gate per residue: g = sigmoid(W[h_s||h_b]), h = g*h_s + (1-g)*h_b |
| Head | 4-layer MLP: 768->384->192->96->1 -> sigmoid |
| Loss | Focal (gamma=2, alpha=1-pos_frac auto) + Ranking (margin=0.3, w=0.3) |
| Ground truth | Residues within 6 A of AOH1996 (ZQZ) in PDB 8GLA |
""")

    with st.expander("Pipeline info"):
        st.markdown("""
**No external API is used for inference.** The model is a local PyTorch GATv2Conv network.

- RCSB fetch is only needed to download the input PDB file (or upload directly)
- Graph construction, model forward pass, and scoring all run on your machine
- Export (B-factor PDB, CSV) is also fully local

**Training**: `python -m src.training.train --train_dir data/cryptosite/train --val_dir data/cryptosite/val --model_size small`
""")
    st.stop()

# ── run inference ─────────────────────────────────────────────────────────────
progress_bar = st.progress(0, "Starting inference...")
result = run_inference(pdb_bytes, model, progress=progress_bar)
progress_bar.empty()

if result is None:
    st.error("Inference failed — check that the PDB file is valid.")
    st.stop()

residues = result["residues"]
scores   = result["scores"]
N        = len(residues)

chains        = [r.chain    for r in residues]
resnames      = [r.resname  for r in residues]
resids        = [r.resid    for r in residues]
sasas         = [r.sasa     for r in residues]
bfactors      = [r.b_factor for r in residues]
ss_list       = [r.secondary_structure for r in residues]
unique_chains = sorted(set(chains))
pocket_mask   = scores >= threshold
n_pocket      = int(pocket_mask.sum())

# ── summary row ───────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Residues",   N)
c2.metric("Chains",     len(unique_chains))
c3.metric(f"Pocket candidates (>={threshold:.2f})", n_pocket)
c4.metric("Max score",  f"{scores.max():.3f}")
c5.metric("Mean score", f"{scores.mean():.3f}")

st.divider()

# ── sequence heatmap ──────────────────────────────────────────────────────────
st.subheader("Per-chain pocket probability heatmap")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(len(unique_chains), 1,
                             figsize=(18, 2.4 * len(unique_chains)),
                             squeeze=False)
    cmap = plt.cm.RdYlGn_r

    for ax_row, chain in zip(axes, unique_chains):
        ax = ax_row[0]
        mask       = np.array([c == chain for c in chains])
        ch_scores  = scores[mask]
        ch_resids  = np.array(resids)[mask]
        ch_ss      = np.array(ss_list)[mask]

        im = ax.imshow(ch_scores[np.newaxis, :], aspect="auto",
                       cmap=cmap, vmin=0, vmax=1,
                       extent=[0, len(ch_scores), 0, 1])
        ax.set_yticks([])

        # Color residue type marks by secondary structure
        for i, (sc, ss) in enumerate(zip(ch_scores, ch_ss)):
            if sc >= threshold:
                marker = "^" if ss == "H" else "s" if ss == "E" else "o"
                ax.plot(i + 0.5, 0.85, marker=marker, color="black",
                        markersize=3, alpha=0.7)

        ax.axhline(0.0, color="gray", linewidth=0.3)
        ax.set_xlabel(f"Residue index (Chain {chain})", fontsize=8)
        ax.set_title(f"Chain {chain}  |  {len(ch_scores)} residues  |  "
                     f"{int((ch_scores >= threshold).sum())} pocket candidates",
                     fontsize=9, pad=3)
        step = max(1, len(ch_scores) // 25)
        ax.set_xticks(range(0, len(ch_scores), step))
        ax.set_xticklabels(ch_resids[::step], fontsize=6, rotation=45)

    plt.tight_layout(rect=[0, 0, 0.96, 1])
    fig.colorbar(im, ax=axes[:, 0], label="Pocket probability", shrink=0.8)
    st.pyplot(fig)
    plt.close(fig)
except ImportError:
    st.warning("matplotlib not installed — pip install matplotlib")

st.divider()

# ── pocket clusters ───────────────────────────────────────────────────────────
st.subheader("Pocket cluster analysis (DBSCAN, eps=6A)")
try:
    pockets = cluster_pockets(residues, scores, threshold)
except ImportError:
    pockets = []
    st.warning("scikit-learn not installed — pip install scikit-learn")

if pockets:
    import pandas as pd
    pocket_rows = []
    for p in pockets:
        cx, cy, cz = p["center_A"]
        pocket_rows.append({
            "Rank"       : p["rank"],
            "Residues"   : p["n_residues"],
            "Mean score" : round(p["mean_score"], 4),
            "Max score"  : round(p["max_score"],  4),
            "Center X"   : round(float(cx), 1),
            "Center Y"   : round(float(cy), 1),
            "Center Z"   : round(float(cz), 1),
        })
    pocket_df = pd.DataFrame(pocket_rows).set_index("Rank")
    st.dataframe(pocket_df, use_container_width=True)

    # Residue list per pocket
    with st.expander(f"Residue membership ({len(pockets)} clusters)"):
        for p in pockets:
            res_list = [
                f"{residues[i].chain}{residues[i].resid}({residues[i].resname})"
                for i in p["residue_idxs"]
            ]
            st.markdown(f"**Pocket #{p['rank']}** ({p['n_residues']} residues, "
                        f"mean={p['mean_score']:.3f})")
            st.code(", ".join(res_list), language=None)
else:
    st.info(f"No DBSCAN clusters found above threshold {threshold:.2f}. "
            f"Lower the threshold or check the PDB file.")

st.divider()

# ── residue table + chain breakdown ──────────────────────────────────────────
col_table, col_chain = st.columns([3, 1])

with col_table:
    st.subheader(f"Top pocket residues (score >= {threshold:.2f})")
    import pandas as pd

    df = pd.DataFrame({
        "Chain"  : chains,
        "ResID"  : resids,
        "AA"     : resnames,
        "Score"  : scores.round(4),
        "SASA"   : np.round(sasas, 1),
        "B-factor": np.round(bfactors, 1),
        "SecStr" : [SS_LABELS.get(s, s) for s in ss_list],
        "Pocket" : pocket_mask,
    })

    # Ground truth comparison for 8GLA
    if pdb_label == "8GLA":
        df["GT_pocket"] = [
            rid in _8GLA_GT.get(ch, set())
            for ch, rid in zip(df["Chain"], df["ResID"])
        ]
        df["TP"] = df["Pocket"] & df["GT_pocket"]
        n_tp   = int(df["TP"].sum())
        n_gt   = int(df["GT_pocket"].sum())
        n_pred = int(df["Pocket"].sum())
        prec   = n_tp / n_pred if n_pred else 0.0
        rec    = n_tp / n_gt   if n_gt   else 0.0
        st.info(
            f"8GLA ground truth  |  GT={n_gt} labeled residues (chains A+B)  "
            f"Pred={n_pred}  TP={n_tp}  Precision={prec:.2f}  Recall={rec:.2f}"
        )
        # Per-chain breakdown
        ch_cols = st.columns(len(unique_chains))
        for col, ch in zip(ch_cols, unique_chains):
            ch_mask = df["Chain"] == ch
            ch_gt   = int(df[ch_mask]["GT_pocket"].sum())
            ch_pred = int(df[ch_mask]["Pocket"].sum())
            ch_tp   = int(df[ch_mask]["TP"].sum())
            ch_prec = ch_tp / ch_pred if ch_pred else 0.0
            ch_rec  = ch_tp / ch_gt   if ch_gt   else 0.0
            label   = "train" if ch == "A" else ("val (held-out)" if ch == "B" else "FP monitor")
            col.metric(f"Chain {ch} ({label})",
                       f"Rec {ch_rec:.2f}  Prec {ch_prec:.2f}",
                       f"{ch_tp}/{ch_gt} TP")

    df_top = df[df["Pocket"]].sort_values("Score", ascending=False).reset_index(drop=True)
    df_top.index += 1

    display_cols = ["Chain", "ResID", "AA", "Score", "SASA", "B-factor", "SecStr"]
    if "GT_pocket" in df.columns:
        display_cols += ["GT_pocket", "TP"]

    if len(df_top):
        st.dataframe(
            df_top[display_cols].style.background_gradient(
                subset=["Score"], cmap="RdYlGn_r", vmin=0, vmax=1),
            use_container_width=True,
            height=min(600, 40 + 35 * len(df_top)),
        )
    else:
        st.info(f"No residues above threshold {threshold:.2f}.")

with col_chain:
    st.subheader("Chain breakdown")
    chain_stats = []
    for ch in unique_chains:
        m = np.array([c == ch for c in chains])
        chain_stats.append({
            "Chain"    : ch,
            "Residues" : int(m.sum()),
            "Mean score": round(float(scores[m].mean()), 3),
            "Max score" : round(float(scores[m].max()),  3),
            "Pocket N"  : int((scores[m] >= threshold).sum()),
        })
    import pandas as pd
    st.dataframe(pd.DataFrame(chain_stats).set_index("Chain"), use_container_width=True)

    if len(unique_chains) == 3:
        st.caption("3-chain structure — likely PCNA homotrimer (A/B/C)")
        chain_means = [scores[np.array([c == ch for c in chains])].mean()
                       for ch in unique_chains]
        variance = float(np.var(chain_means))
        if variance < 0.001:
            st.success(f"Chain symmetry consistent (var={variance:.5f})")
        else:
            st.warning(f"Chain asymmetry detected (var={variance:.4f})")

    # Secondary structure breakdown of pocket residues
    st.subheader("SS of pocket residues")
    if n_pocket > 0:
        pocket_ss = [ss_list[i] for i, m in enumerate(pocket_mask) if m]
        ss_counts = {k: pocket_ss.count(k) for k in ["H", "E", "C", ""]}
        import pandas as pd
        ss_df = pd.DataFrame([
            {"SecStr": SS_LABELS.get(k, k), "Count": v}
            for k, v in ss_counts.items() if v > 0
        ]).set_index("SecStr")
        st.dataframe(ss_df, use_container_width=True)
    else:
        st.caption("No pocket residues to summarize.")

st.divider()

# ── score distribution ────────────────────────────────────────────────────────
with st.expander("Score distribution"):
    try:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.hist(scores, bins=50, color="#4472C4", alpha=0.8, edgecolor="none")
        ax.axvline(threshold, color="red", linewidth=1.5, linestyle="--",
                   label=f"Threshold ({threshold:.2f})")
        ax.set_xlabel("Pocket probability")
        ax.set_ylabel("Residue count")
        ax.set_title("Score distribution")
        ax.legend(fontsize=8)
        st.pyplot(fig)
        plt.close(fig)
    except ImportError:
        st.caption("matplotlib needed for distribution plot.")

# ── exports ───────────────────────────────────────────────────────────────────
st.subheader("Export")
exp1, exp2, exp3 = st.columns(3)

with exp1:
    bfactor_pdb = export_bfactor_pdb(pdb_bytes, residues, scores)
    st.download_button(
        "B-factor PDB (PyMOL coloring)",
        data=bfactor_pdb,
        file_name=f"{pdb_label}_pocket_scores.pdb",
        mime="chemical/x-pdb",
        help="In PyMOL: spectrum b, red_white_green — red = high pocket probability",
    )

with exp2:
    import pandas as pd
    csv_df = pd.DataFrame({
        "chain": chains, "resid": resids, "aa": resnames,
        "pocket_score"       : scores.round(4),
        "sasa"               : np.round(sasas, 2),
        "b_factor"           : np.round(bfactors, 2),
        "secondary_structure": ss_list,
        "is_pocket_candidate": pocket_mask,
    })
    st.download_button(
        "Scores CSV",
        data=csv_df.to_csv(index=False),
        file_name=f"{pdb_label}_pocket_scores.csv",
        mime="text/csv",
    )

with exp3:
    if pockets:
        import json
        pocket_export = [
            {
                "rank": p["rank"], "n_residues": p["n_residues"],
                "mean_score": round(p["mean_score"], 4),
                "max_score" : round(p["max_score"], 4),
                "center"    : [round(float(v), 2) for v in p["center_A"]],
                "residues"  : [
                    {"chain": residues[i].chain, "resid": residues[i].resid,
                     "aa": residues[i].resname, "score": round(float(scores[i]), 4)}
                    for i in p["residue_idxs"]
                ],
            }
            for p in pockets
        ]
        st.download_button(
            "Pocket clusters JSON",
            data=json.dumps(pocket_export, indent=2),
            file_name=f"{pdb_label}_pocket_clusters.json",
            mime="application/json",
        )
    else:
        st.caption("No clusters to export.")

st.caption(
    f"Model: {model.__class__.__name__} {model_key}  |  "
    f"{n_params:,} params  |  Structure: {pdb_label}  |  "
    f"Threshold: {threshold:.2f}  |  Local inference (no API)"
)
