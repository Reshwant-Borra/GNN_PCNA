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

from src.models import PocketGNN, CrypticGNN, PocketGNNXL
from src.data_processing.parse_pdb import parse_pdb
from src.data_processing.graph_construction import build_graph_v2, build_graph

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GNN-PCNA Pocket Predictor",
    page_icon="",
    layout="wide",
)

RAW_DIR     = REPO_ROOT / "data" / "raw"
ESM_DIR     = REPO_ROOT / "data" / "esm_features"
V3_DIR      = REPO_ROOT / "results" / "v3"
V1_DIR      = REPO_ROOT / "results" / "per_structure"
RCSB_DL     = "https://files.rcsb.org/download/{}.pdb"

CKPT_V2 = REPO_ROOT / "checkpoints" / "pcna" / "best_pcna.ckpt"
CKPT_V3 = REPO_ROOT / "checkpoints" / "pcna_reproduced" / "best.ckpt"

# Residues within 6 A of AOH1996 (ZQZ) in 8GLA
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
def load_model(config: str) -> tuple[torch.nn.Module, bool, str]:
    """Returns (model, checkpoint_loaded, checkpoint_path_str)."""
    if config == "v3-xl":
        m = PocketGNNXL().eval()
        ckpt = CKPT_V3
    elif config == "v2-small":
        m = PocketGNN.small().eval()
        ckpt = CKPT_V2
    else:
        return CrypticGNN().eval(), False, ""

    if ckpt.exists():
        m.load_state_dict(torch.load(str(ckpt), map_location="cpu", weights_only=True))
        return m, True, str(ckpt)
    return m, False, str(ckpt)


@st.cache_resource
def load_esm_model():
    """Load ESM2 t12 (480-dim) for on-the-fly feature generation."""
    from transformers import EsmModel, EsmTokenizer
    name = "facebook/esm2_t12_35M_UR50D"
    tokenizer = EsmTokenizer.from_pretrained(name)
    model = EsmModel.from_pretrained(name).eval()
    return tokenizer, model


_THREE_TO_ONE = {
    'ALA':'A','ARG':'R','ASN':'N','ASP':'D','CYS':'C','GLN':'Q','GLU':'E',
    'GLY':'G','HIS':'H','ILE':'I','LEU':'L','LYS':'K','MET':'M','PHE':'F',
    'PRO':'P','SER':'S','THR':'T','TRP':'W','TYR':'Y','VAL':'V',
}

MAX_LEN = 1022


@torch.no_grad()
def _embed_sequence(seq: str, tokenizer, esm_model, esm_dim=480) -> np.ndarray:
    L = len(seq)
    if L == 0:
        return np.zeros((0, esm_dim), dtype=np.float32)
    if L <= MAX_LEN:
        inputs = tokenizer(seq, return_tensors="pt", add_special_tokens=True)
        out = esm_model(**inputs)
        return out.last_hidden_state[0, 1:-1].numpy().astype(np.float32)
    stride = 512
    emb_sum = np.zeros((L, esm_dim), dtype=np.float64)
    counts = np.zeros(L, dtype=np.float64)
    start = 0
    while start < L:
        end = min(start + MAX_LEN, L)
        inputs = tokenizer(seq[start:end], return_tensors="pt", add_special_tokens=True)
        out = esm_model(**inputs)
        chunk = out.last_hidden_state[0, 1:-1].numpy()
        emb_sum[start:end] += chunk
        counts[start:end] += 1
        if end == L:
            break
        start += stride
    return (emb_sum / np.maximum(counts[:, None], 1)).astype(np.float32)


def get_esm_features(pdb_id: str, residues, esm_dim=480) -> np.ndarray | None:
    """Return (N, 480) ESM2 features. Tries cache first, then on-the-fly."""
    cached = ESM_DIR / f"{pdb_id.upper()}.npy"
    if cached.exists():
        feats = np.load(str(cached))
        if feats.shape[0] == len(residues):
            return feats
    # On-the-fly: generate features using ESM2
    try:
        tokenizer, esm_model = load_esm_model()
        chains: dict[str, list] = {}
        for i, r in enumerate(residues):
            chains.setdefault(r.chain, []).append((i, r))
        all_embs = np.zeros((len(residues), esm_dim), dtype=np.float32)
        for chain_id, res_list in chains.items():
            seq = "".join(_THREE_TO_ONE.get(r.resname, "X") for _, r in res_list)
            emb = _embed_sequence(seq, tokenizer, esm_model, esm_dim)
            target = len(res_list)
            if emb.shape[0] < target:
                pad = np.zeros((target - emb.shape[0], esm_dim), dtype=np.float32)
                emb = np.concatenate([emb, pad], axis=0)
            else:
                emb = emb[:target]
            for k, (idx, _) in enumerate(res_list):
                all_embs[idx] = emb[k]
        return all_embs
    except Exception as e:
        st.warning(f"ESM2 feature generation failed: {e}")
        return None


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
                  pdb_id: str = "", progress=None) -> dict | None:
    with tempfile.NamedTemporaryFile(suffix=".pdb", delete=False) as tmp:
        tmp.write(pdb_bytes)
        tmp_path = Path(tmp.name)
    try:
        if progress:
            progress.progress(0.10, "Parsing PDB structure...")
        residues = parse_pdb(tmp_path)
        if not residues:
            return None

        if progress:
            progress.progress(0.30, "Building graph...")
        data = build_graph_v2(residues, labels=None)

        if isinstance(model, PocketGNNXL):
            if progress:
                progress.progress(0.50, "Loading ESM2 features...")
            esm_feats = get_esm_features(pdb_id, residues)
            if esm_feats is None:
                st.error("ESM2 features unavailable for this structure and on-the-fly "
                         "generation failed. Try a known PCNA structure.")
                return None
            if esm_feats.shape[0] != data.x.shape[0]:
                st.error(f"ESM2 shape mismatch ({esm_feats.shape[0]} vs {data.x.shape[0]}). "
                         "Re-run build_esm_features.py for this structure.")
                return None
            x_in = torch.cat([data.x, torch.from_numpy(esm_feats).float()], dim=1)
            if progress:
                progress.progress(0.70, "Running PocketGNNXL v3 forward pass...")
            with torch.no_grad():
                scores = model(x_in, data.edge_index, data.edge_attr,
                               data.edge_index_seq, data.edge_attr_seq,
                               data.chain_id).numpy()
        elif isinstance(model, PocketGNN):
            if progress:
                progress.progress(0.60, "Running PocketGNN forward pass...")
            with torch.no_grad():
                scores = model(
                    data.x, data.edge_index, data.edge_attr,
                    data.edge_index_seq, data.edge_attr_seq,
                    data.chain_id,
                ).numpy()
        else:
            data_v1 = build_graph(residues, labels=None)
            if progress:
                progress.progress(0.60, "Running CrypticGNN forward pass...")
            with torch.no_grad():
                scores = model(data_v1.x, data_v1.edge_index, data_v1.edge_attr).numpy()

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
    from src.models.cryptic_gnn import focal_loss
    N, E = 24, 50
    E_seq = 2 * (N - 1)
    is_xl = isinstance(model, PocketGNNXL)
    feat_dim = 520 if is_xl else 40
    x             = torch.randn(N, feat_dim)
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
        if isinstance(model, (PocketGNN, PocketGNNXL)):
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
                score = score_map.get((chain, resid), 0.0)
                line  = line[:60] + f"{score:6.2f}" + (line[66:] if len(line) > 66 else "")
            except (ValueError, IndexError):
                pass
        lines_out.append(line)
    return "\n".join(lines_out)


@st.cache_data
def load_v3_summary() -> "pd.DataFrame | None":
    csv = V3_DIR / "v3_summary.csv"
    if not csv.exists():
        return None
    import pandas as pd
    return pd.read_csv(csv)


@st.cache_data
def load_v1_summary() -> "pd.DataFrame | None":
    csv = V1_DIR / "summary_table.csv"
    if not csv.exists():
        return None
    import pandas as pd
    return pd.read_csv(csv, encoding="utf-8", errors="replace")


# ── sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("GNN-PCNA")
    st.caption("Cryptic Pocket Predictor")
    st.caption("Inference: 100% local — no API calls")
    st.divider()

    tab_mode = st.radio("Mode", ["Inference", "Results Browser"], horizontal=True)

    if tab_mode == "Inference":
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
            pdb_id = pdb_label

        st.divider()
        model_choice = st.selectbox(
            "Model",
            [
                "v3-xl (13.4M params, ESM2) [BEST]",
                "v2-small (~907k params)",
                "v1-baseline",
            ],
            index=0,
            help="v3-xl uses ESM2 protein language model features; requires pre-computed or on-the-fly ESM2 embeddings",
        )
        model_key = model_choice.split(" ")[0]

        ckpt_file = st.file_uploader("Load checkpoint (.ckpt)", type=["ckpt", "pt"],
                                     help="Optional — overrides default checkpoint")

        threshold = st.slider("Pocket threshold", 0.0, 1.0, 0.40, 0.05,
                              help="Residues above this score flagged as pocket candidates")

        st.divider()
        sanity_btn = st.button("Run sanity test")
        run_btn    = st.button("Run inference", type="primary", disabled=pdb_bytes is None)
    else:
        pdb_bytes = None
        pdb_label = ""
        pdb_id    = ""
        model_key = "v3-xl"
        threshold = 0.40
        run_btn   = False
        sanity_btn = False
        ckpt_file  = None


# ── main area ─────────────────────────────────────────────────────────────────

if tab_mode == "Results Browser":
    st.title("V3 Results Browser")
    st.caption("Pre-computed PocketGNNXL (v3) scores across PCNA structures")

    import pandas as pd

    v3_df = load_v3_summary()
    v1_df = load_v1_summary()

    if v3_df is None:
        st.error("results/v3/v3_summary.csv not found — run scripts/run_v3_inference.py first.")
        st.stop()

    # Merge v1 AUROC for comparison
    if v1_df is not None and "auroc" in v1_df.columns:
        v1_map = v1_df.set_index("pdb")["auroc"].to_dict()
        v3_df["auroc_v1"] = v3_df["pdb"].map(v1_map)
        v3_df["auroc_v1"] = pd.to_numeric(v3_df["auroc_v1"], errors="coerce")

    v3_df["auroc_v3_num"] = pd.to_numeric(v3_df["auroc_v3"].replace("N/A", float("nan")), errors="coerce")
    v3_df["top_cluster_mean"] = pd.to_numeric(v3_df["top_cluster_mean"], errors="coerce")
    v3_df["score_max"] = pd.to_numeric(v3_df["score_max"], errors="coerce")

    # Summary metrics
    has_auroc = v3_df["auroc_v3_num"].notna()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Structures processed", len(v3_df))
    c2.metric("With AUROC (drug-like ligand)", int(has_auroc.sum()))
    mean_v3 = v3_df.loc[has_auroc, "auroc_v3_num"].mean()
    c3.metric("Mean AUROC (v3)", f"{mean_v3:.4f}")
    if "auroc_v1" in v3_df.columns:
        mean_v1 = v3_df.loc[has_auroc & v3_df["auroc_v1"].notna(), "auroc_v1"].mean()
        c4.metric("Mean AUROC (v1 baseline)", f"{mean_v1:.4f}", delta=f"+{mean_v3 - mean_v1:.4f}")

    st.divider()

    # AUROC comparison chart
    if "auroc_v1" in v3_df.columns:
        st.subheader("V1 vs V3 AUROC — structures with drug-like ligands")
        cmp = v3_df[has_auroc & v3_df["auroc_v1"].notna()].copy()
        cmp["delta"] = cmp["auroc_v3_num"] - cmp["auroc_v1"]
        cmp = cmp.sort_values("auroc_v3_num", ascending=False)

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(10, 4))
            x_pos = np.arange(len(cmp))
            width = 0.35
            ax.bar(x_pos - width/2, cmp["auroc_v1"], width, label="V1 (~907k)", color="#4472C4", alpha=0.85)
            ax.bar(x_pos + width/2, cmp["auroc_v3_num"], width, label="V3 (13.4M+ESM2)", color="#ED7D31", alpha=0.85)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(cmp["pdb"], rotation=30, ha="right", fontsize=9)
            ax.set_ylim(0, 1.05)
            ax.axhline(0.5, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
            ax.set_ylabel("AUROC")
            ax.set_title("PocketGNN V1 vs PocketGNNXL V3 — AUROC on drug-like ligand structures")
            ax.legend(fontsize=9)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
        except ImportError:
            pass

        st.subheader("AUROC comparison table")
        disp = cmp[["pdb", "auroc_v1", "auroc_v3_num", "delta",
                     "top_cluster_n", "top_aoh_overlap", "top_cluster_mean"]].copy()
        disp.columns = ["PDB", "V1 AUROC", "V3 AUROC", "Delta",
                        "Top cluster N", "AOH overlap /24", "Top cluster mean"]
        disp = disp.reset_index(drop=True)
        st.dataframe(
            disp.style
                .format({"V1 AUROC": "{:.4f}", "V3 AUROC": "{:.4f}",
                         "Delta": "{:+.4f}", "Top cluster mean": "{:.4f}"})
                .background_gradient(subset=["V3 AUROC"], cmap="RdYlGn", vmin=0.5, vmax=1.0)
                .background_gradient(subset=["Delta"], cmap="RdYlGn", vmin=-0.2, vmax=0.6),
            use_container_width=True,
        )

    st.divider()
    st.subheader("All 59 PCNA structures — V3 scores")

    display_v3 = v3_df[[
        "pdb", "top_cluster_mean", "top_cluster_n", "top_aoh_overlap",
        "auroc_v3", "score_max", "score_mean", "n_residues"
    ]].copy()
    display_v3.columns = [
        "PDB", "Top cluster score", "Top cluster N", "AOH overlap /24",
        "AUROC (v3)", "Max score", "Mean score", "Residues"
    ]
    st.dataframe(
        display_v3.style.background_gradient(
            subset=["Top cluster score", "Max score"], cmap="RdYlGn", vmin=0.5, vmax=1.0),
        use_container_width=True,
        height=600,
    )

    st.divider()
    st.subheader("Per-structure score browser")
    sel_pdb = st.selectbox("Select structure", sorted(v3_df["pdb"].tolist()), index=0)
    scores_csv = V3_DIR / sel_pdb / "scores.csv"
    if scores_csv.exists():
        sel_df = pd.read_csv(scores_csv)
        sel_df["score"] = pd.to_numeric(sel_df["score"], errors="coerce")
        col_hm, col_top = st.columns([3, 1])
        with col_hm:
            try:
                import matplotlib
                matplotlib.use("Agg")
                import matplotlib.pyplot as plt
                unique_chains = sel_df["chain"].unique().tolist()
                fig, axes = plt.subplots(len(unique_chains), 1,
                                         figsize=(16, 2.2 * len(unique_chains)), squeeze=False)
                cmap = plt.cm.RdYlGn_r
                for ax_row, ch in zip(axes, unique_chains):
                    ax = ax_row[0]
                    ch_df = sel_df[sel_df["chain"] == ch]
                    sc = ch_df["score"].values
                    ri = ch_df["resid"].values
                    im = ax.imshow(sc[np.newaxis, :], aspect="auto",
                                   cmap=cmap, vmin=0, vmax=1,
                                   extent=[0, len(sc), 0, 1])
                    ax.set_yticks([])
                    step = max(1, len(sc) // 25)
                    ax.set_xticks(range(0, len(sc), step))
                    ax.set_xticklabels(ri[::step], fontsize=6, rotation=45)
                    ax.set_title(f"Chain {ch} | {len(sc)} residues | "
                                 f"{int((sc >= threshold).sum())} above {threshold:.2f}",
                                 fontsize=9)
                plt.tight_layout(rect=[0, 0, 0.96, 1])
                fig.colorbar(im, ax=axes[:, 0], label="V3 prioritization score", shrink=0.8)
                st.pyplot(fig)
                plt.close(fig)
            except ImportError:
                pass
        with col_top:
            top20 = sel_df.nlargest(20, "score")[["chain", "resid", "resname", "score"]]
            st.caption("Top 20 residues")
            st.dataframe(top20.reset_index(drop=True), use_container_width=True, height=500)

        st.download_button(
            f"Download {sel_pdb} V3 scores CSV",
            data=scores_csv.read_text(encoding="utf-8"),
            file_name=f"{sel_pdb}_v3_scores.csv",
            mime="text/csv",
        )
    else:
        st.warning(f"No v3 scores found for {sel_pdb}")

    st.stop()


# ── inference mode ────────────────────────────────────────────────────────────

st.title("Cryptic Pocket Predictor")

v3_note = " · **v3 (ESM2)**" if model_key == "v3-xl" else ""
st.caption(f"GNN-PCNA{v3_note}  *  PocketGNN v2 + XL  *  Dual-branch GATv2Conv  *  Local inference only")

model, ckpt_loaded, ckpt_path = load_model(model_key)
if ckpt_file is not None:
    try:
        state = torch.load(io.BytesIO(ckpt_file.read()), map_location="cpu", weights_only=True)
        model.load_state_dict(state)
        model.eval()
        st.sidebar.success("Checkpoint loaded from upload")
    except Exception as e:
        st.sidebar.error(f"Checkpoint error: {e}")
elif ckpt_loaded:
    st.sidebar.success(f"Checkpoint loaded: {Path(ckpt_path).name}")
else:
    st.sidebar.warning(
        f"No checkpoint found at `{ckpt_path}`. "
        "Model weights are random — scores are meaningless. "
        "Train first with `python src/training/train.py` or upload a checkpoint above."
    )

n_params = sum(p.numel() for p in model.parameters())

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
        if model_key == "v3-xl":
            st.markdown(f"""
**PocketGNNXL** — `v3-xl` — **{n_params:,} parameters**

| Component | Detail |
|---|---|
| Node features | 520 dims = 40 hand-crafted + 480 ESM2 (facebook/esm2_t12_35M_UR50D) |
| Edge features | 6 dims — distance_norm, 1/(1+d), seq_sep_norm, same_chain, is_backbone, cross_chain |
| Pre-encoder | Linear(520 → 384) + ReLU + LayerNorm → Linear(384 → 768) + ReLU + LayerNorm |
| Spatial branch | 5x GATv2Conv on contact graph (8 A cutoff), residual + LayerNorm |
| Sequential branch | 4x GATv2Conv on backbone graph, residual + LayerNorm |
| Virtual node | Global context node gated into all residue representations |
| Fusion | Learned gate per residue |
| Head | MLP -> sigmoid per residue |
| Checkpoint | pcna_reproduced/best.ckpt — fully reproduced XL, seed=42 end-to-end (primary checkpoint) |
| Held-out AUROC | **0.8913** mean over 6 held-out structures (8GLA excluded — training leak) |
""")
        else:
            st.markdown(f"""
**{model.__class__.__name__}** — `{model_key}` — **{n_params:,} parameters**

| Component | Detail |
|---|---|
| Node features | 40 dims — aa_onehot (20), SASA, secondary structure (3), B-factor, rel_pos, hydrophobicity, charge, VdW volume, flexibility, pseudo-dihedrals (4), local density 5A/10A, interface flag, chain_onehot (3) |
| Edge features | 6 dims — distance_norm, 1/(1+d), seq_sep_norm, same_chain, is_backbone, cross_chain |
| Spatial branch | 4x GATv2Conv (3x for small) on contact graph (8 A cutoff), residual + LayerNorm |
| Sequential branch | 3x GATv2Conv (2x for small) on backbone graph |
| Fusion | Learned gate per residue |
| Head | MLP -> sigmoid per residue |
| Checkpoint | best_pcna.ckpt — all results produced with small (~907k) |
| AUROC on 8GLA | **0.8661** |
""")

    with st.expander("V3 vs V1 headline results (pre-computed on 59 PCNA structures)"):
        v3_df = load_v3_summary()
        v1_df = load_v1_summary()
        if v3_df is not None and v1_df is not None and "auroc" in v1_df.columns:
            import pandas as pd
            v1_map = v1_df.set_index("pdb")["auroc"].to_dict()
            rows = []
            for _, row in v3_df.iterrows():
                v3a = row["auroc_v3"]
                if v3a == "N/A":
                    continue
                v1a = v1_map.get(row["pdb"])
                if not v1a:
                    continue
                try:
                    rows.append({"PDB": row["pdb"], "V1 AUROC": float(v1a),
                                 "V3 AUROC": float(v3a),
                                 "Delta": float(v3a) - float(v1a)})
                except Exception:
                    pass
            if rows:
                cmp = pd.DataFrame(rows).sort_values("V3 AUROC", ascending=False)
                st.dataframe(
                    cmp.style.format({"V1 AUROC": "{:.4f}", "V3 AUROC": "{:.4f}", "Delta": "{:+.4f}"})
                       .background_gradient(subset=["V3 AUROC"], cmap="RdYlGn", vmin=0.5, vmax=1.0),
                    use_container_width=True,
                )
                st.caption(f"V3 mean AUROC: {cmp['V3 AUROC'].mean():.4f}  |  "
                           f"V1 mean AUROC: {cmp['V1 AUROC'].mean():.4f}")

    st.stop()

# ── run inference ─────────────────────────────────────────────────────────────
progress_bar = st.progress(0, "Starting inference...")
result = run_inference(pdb_bytes, model, pdb_id=pdb_label, progress=progress_bar)
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

# ── model tag ─────────────────────────────────────────────────────────────────
model_tag = f"{model.__class__.__name__} ({model_key}, {n_params:,} params)"
if model_key == "v3-xl":
    esm_cached = (ESM_DIR / f"{pdb_label}.npy").exists()
    st.success(f"V3 inference complete — ESM2 features {'from cache' if esm_cached else 'generated on-the-fly'}")

# ── summary row ───────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Residues",   N)
c2.metric("Chains",     len(unique_chains))
c3.metric(f"Pocket candidates (>={threshold:.2f})", n_pocket)
c4.metric("Max score",  f"{scores.max():.3f}")
c5.metric("Mean score", f"{scores.mean():.3f}")

# Show pre-computed AUROC for this structure if available
if model_key == "v3-xl":
    v3_df = load_v3_summary()
    if v3_df is not None:
        row = v3_df[v3_df["pdb"] == pdb_label]
        if not row.empty:
            r = row.iloc[0]
            v1_df = load_v1_summary()
            v1_auroc = None
            if v1_df is not None and "auroc" in v1_df.columns:
                v1_row = v1_df[v1_df["pdb"] == pdb_label]
                if not v1_row.empty:
                    try:
                        v1_auroc = float(v1_row.iloc[0]["auroc"])
                    except Exception:
                        pass
            parts = [f"**V3 AUROC:** {r['auroc_v3']}",
                     f"AOH overlap: {r['top_aoh_overlap']}/24",
                     f"Top cluster score: {float(r['top_cluster_mean']):.4f}"]
            if v1_auroc is not None and r["auroc_v3"] != "N/A":
                delta = float(r["auroc_v3"]) - v1_auroc
                parts.append(f"V1 AUROC: {v1_auroc:.4f} (delta: {delta:+.4f})")
            st.info("  |  ".join(parts))

st.divider()

# ── sequence heatmap ──────────────────────────────────────────────────────────
st.subheader("Per-chain prioritization score heatmap")

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
    fig.colorbar(im, ax=axes[:, 0], label="prioritization score", shrink=0.8)
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
        ch_cols = st.columns(len(unique_chains))
        for col, ch in zip(ch_cols, unique_chains):
            ch_mask = df["Chain"] == ch
            ch_gt   = int(df[ch_mask]["GT_pocket"].sum())
            ch_pred = int(df[ch_mask]["Pocket"].sum())
            ch_tp   = int(df[ch_mask]["TP"].sum())
            ch_prec = ch_tp / ch_pred if ch_pred else 0.0
            ch_rec  = ch_tp / ch_gt   if ch_gt   else 0.0
            col.metric(f"Chain {ch}",
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

    if len(unique_chains) >= 3:
        st.caption("3+ chain structure — likely PCNA homotrimer (A/B/C)")
        pcna_ch = [ch for ch in unique_chains
                   if sum(1 for c in chains if c == ch) >= 200]
        if pcna_ch:
            chain_means = [scores[np.array([c == ch for c in chains])].mean()
                           for ch in pcna_ch]
            variance = float(np.var(chain_means))
            if variance < 0.001:
                st.success(f"Chain symmetry consistent (var={variance:.5f})")
            else:
                st.warning(f"Chain asymmetry detected (var={variance:.4f})")

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

with st.expander("Score distribution"):
    try:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.hist(scores, bins=50, color="#4472C4", alpha=0.8, edgecolor="none")
        ax.axvline(threshold, color="red", linewidth=1.5, linestyle="--",
                   label=f"Threshold ({threshold:.2f})")
        ax.set_xlabel("prioritization score")
        ax.set_ylabel("Residue count")
        ax.set_title(f"Score distribution — {model_tag}")
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
        file_name=f"{pdb_label}_{model_key}_pocket_scores.pdb",
        mime="chemical/x-pdb",
        help="In PyMOL: spectrum b, red_white_green — red = high prioritization score",
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
        file_name=f"{pdb_label}_{model_key}_pocket_scores.csv",
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
            file_name=f"{pdb_label}_{model_key}_pocket_clusters.json",
            mime="application/json",
        )
    else:
        st.caption("No clusters to export.")

st.caption(
    f"Model: {model_tag}  |  Structure: {pdb_label}  |  "
    f"Threshold: {threshold:.2f}  |  Local inference (no API)"
)
