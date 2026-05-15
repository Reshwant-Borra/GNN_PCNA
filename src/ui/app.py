"""
GNN-PCNA: Cryptic Pocket Predictor — Streamlit UI

Run:
    streamlit run src/ui/app.py

Features:
  - Upload PDB or fetch from RCSB by ID
  - Runs PocketGNN v2 (or v1 for comparison)
  - Sequence heatmap colored by pocket probability
  - Per-residue score table with chain breakdown
  - PCNA chain A/B/C symmetry comparison
  - Export: B-factor-replaced PDB (PyMOL-ready) + CSV
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
import requests
import streamlit as st
import torch

# ── repo root on path ─────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.models import PocketGNN, CrypticGNN
from src.data_processing.parse_pdb import parse_pdb
from src.data_processing.graph_construction import build_graph_v2, build_graph

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GNN-PCNA Pocket Predictor",
    page_icon="🔬",
    layout="wide",
)

# ── constants ─────────────────────────────────────────────────────────────────
RCSB_DL = "https://files.rcsb.org/download/{}.pdb"
RAW_DIR  = REPO_ROOT / "data" / "raw"

KNOWN_ANNOTATIONS = {
    "8GLA": "Ground truth — AOH1996 cryptic pocket OPEN",
    "1W60": "Apo baseline — cryptic pocket absent",
    "4RJF": "Highest-resolution apo (2.0 Å)",
    "1U7B": "Highest resolution overall (1.88 Å)",
    "1AXC": "PIP-box complex (p21)",
    "9N3L": "HSP90alpha inhibitor — investigate for second cryptic site",
}

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
        r = requests.get(RCSB_DL.format(pdb_id.upper()), timeout=20)
        r.raise_for_status()
        return r.content
    except Exception:
        return None


def run_inference(pdb_bytes: bytes, model: torch.nn.Module) -> dict | None:
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".pdb", delete=False) as tmp:
        tmp.write(pdb_bytes)
        tmp_path = Path(tmp.name)
    try:
        residues = parse_pdb(tmp_path)
        if not residues:
            return None
        labels = None

        if isinstance(model, PocketGNN):
            data = build_graph_v2(residues, labels)
            with torch.no_grad():
                scores = model(
                    data.x, data.edge_index, data.edge_attr,
                    data.edge_index_seq, data.edge_attr_seq,
                    data.chain_id,
                ).numpy()
        else:
            data = build_graph(residues, labels)
            with torch.no_grad():
                scores = model(data.x, data.edge_index, data.edge_attr).numpy()

        return {
            "residues": residues,
            "scores"  : scores,
            "pdb_bytes": pdb_bytes,
        }
    except Exception as e:
        st.error(f"Inference failed: {e}")
        return None
    finally:
        os.unlink(tmp_path)


def export_bfactor_pdb(pdb_bytes: bytes, residues, scores: np.ndarray) -> str:
    """Replace B-factors with pocket probability × 100 for PyMOL coloring."""
    score_map = {
        (r.chain, r.resid): float(s) * 100
        for r, s in zip(residues, scores)
    }
    lines_out = []
    for line in pdb_bytes.decode("utf-8", errors="ignore").splitlines():
        if line.startswith("ATOM"):
            try:
                chain = line[21]
                resid = int(line[22:26].strip())
                prob  = score_map.get((chain, resid), 0.0)
                line  = line[:60] + f"{prob:6.2f}" + line[66:]
            except (ValueError, IndexError):
                pass
        lines_out.append(line)
    return "\n".join(lines_out)


def score_color(p: float) -> str:
    r = int(255 * p)
    g = int(255 * (1 - p))
    return f"rgb({r},{g},0)"


# ── sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🔬 GNN-PCNA")
    st.caption("Cryptic Pocket Predictor")
    st.divider()

    input_mode = st.radio("Input", ["PDB ID", "Upload PDB"], horizontal=True)
    pdb_bytes  = None
    pdb_label  = ""

    if input_mode == "PDB ID":
        pdb_id = st.text_input("PDB ID", value="8GLA").strip().upper()
        if st.button("Fetch from RCSB", type="primary"):
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
        ["v2-large (~10.4M params)", "v2-medium (~3.2M params)",
         "v2-small (~850k params)", "v1-baseline"],
        index=0,
    )
    model_key = model_choice.split(" ")[0]  # "v2-large", "v2-medium", etc.

    threshold = st.slider("Pocket threshold", 0.0, 1.0, 0.4, 0.05,
                          help="Residues above this probability are flagged as pocket candidates")

    st.divider()
    run_btn = st.button("Run inference", type="primary", disabled=pdb_bytes is None)

# ── main area ─────────────────────────────────────────────────────────────────

st.title("Cryptic Pocket Predictor")
st.caption("GNN-PCNA · PocketGNN v2 · Dual-branch GATv2Conv")

if not run_btn or pdb_bytes is None:
    st.info("Load a PDB structure in the sidebar and click **Run inference**.")
    st.divider()

    with st.expander("About the model"):
        st.markdown("""
**PocketGNN v2** is a dual-branch Graph Attention Network that predicts per-residue
cryptic pocket probability from a static crystal structure.

| Component | Detail |
|---|---|
| Node features | 40 dims: aa_onehot, SASA, secondary structure, B-factor, hydrophobicity, charge, volume, flexibility, pseudo-dihedrals, local density, interface flag, chain |
| Edge features | 6 dims: distance, 1/distance, sequence separation, same-chain, backbone bond, cross-chain |
| Branch 1 | 4× GATv2Conv on spatial contact graph (8 Å cutoff) |
| Branch 2 | 3× GATv2Conv on backbone sequential graph (\\|i−j\\| ≤ 2) |
| Fusion | Learned gate per residue |
| Head | 4-layer MLP → Sigmoid |
| Parameters | ~10.4M (large config) |
| Loss | Focal + Ranking + Symmetry |

**Ground truth**: residues within 6 Å of AOH1996 in PDB `8GLA`.
""")
    st.stop()

# Run inference
model = load_model(model_key)
with st.spinner("Running PocketGNN..."):
    result = run_inference(pdb_bytes, model)

if result is None:
    st.error("Inference failed — check the PDB file is valid.")
    st.stop()

residues = result["residues"]
scores   = result["scores"]
N        = len(residues)

chains     = [r.chain  for r in residues]
resnames   = [r.resname for r in residues]
resids     = [r.resid   for r in residues]
unique_chains = sorted(set(chains))

# ── summary row ───────────────────────────────────────────────────────────────
pocket_mask = scores >= threshold
n_pocket    = int(pocket_mask.sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Residues", N)
c2.metric("Chains", len(unique_chains))
c3.metric(f"Pocket candidates (≥{threshold:.2f})", n_pocket)
c4.metric("Max score", f"{scores.max():.3f}")

st.divider()

# ── sequence heatmap ──────────────────────────────────────────────────────────
st.subheader("Sequence pocket probability heatmap")

try:
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors

    fig, axes = plt.subplots(len(unique_chains), 1,
                             figsize=(16, 2.2 * len(unique_chains)),
                             squeeze=False)
    cmap = plt.cm.RdYlGn_r

    for ax_row, chain in zip(axes, unique_chains):
        ax = ax_row[0]
        mask    = np.array([c == chain for c in chains])
        ch_scores  = scores[mask]
        ch_resids  = np.array(resids)[mask]
        ch_resnames = np.array(resnames)[mask]

        im = ax.imshow(ch_scores[np.newaxis, :], aspect="auto",
                       cmap=cmap, vmin=0, vmax=1,
                       extent=[0, len(ch_scores), 0, 1])
        ax.set_yticks([])
        ax.set_xlabel(f"Residue position (Chain {chain})", fontsize=8)
        ax.set_title(f"Chain {chain}  ({len(ch_scores)} residues)", fontsize=9, pad=4)

        # Mark threshold line
        above = np.where(ch_scores >= threshold)[0]
        for idx in above:
            ax.axvline(idx + 0.5, color="black", alpha=0.15, linewidth=0.5)

        # Tick labels at every 20 residues
        step = max(1, len(ch_scores) // 20)
        ax.set_xticks(range(0, len(ch_scores), step))
        ax.set_xticklabels(ch_resids[::step], fontsize=6, rotation=45)

    plt.tight_layout(rect=[0, 0, 0.97, 1])
    fig.colorbar(im, ax=axes[:, 0], label="Pocket probability", shrink=0.8)
    st.pyplot(fig)
    plt.close(fig)

except ImportError:
    st.warning("matplotlib not installed — install it for heatmap visualisation.")

st.divider()

# ── top residue table ─────────────────────────────────────────────────────────
col_table, col_chain = st.columns([2, 1])

with col_table:
    st.subheader(f"Top pocket candidates (score ≥ {threshold:.2f})")
    import pandas as pd

    df = pd.DataFrame({
        "Chain"  : chains,
        "ResID"  : resids,
        "AA"     : resnames,
        "Score"  : scores.round(4),
        "Pocket" : pocket_mask,
    })
    df_top = df[df["Pocket"]].sort_values("Score", ascending=False).reset_index(drop=True)
    df_top.index += 1

    if len(df_top):
        st.dataframe(
            df_top[["Chain", "ResID", "AA", "Score"]].style.background_gradient(
                subset=["Score"], cmap="RdYlGn_r", vmin=0, vmax=1),
            use_container_width=True,
            height=min(600, 40 + 35 * len(df_top)),
        )
    else:
        st.info(f"No residues above threshold {threshold:.2f}. Lower the threshold in the sidebar.")

with col_chain:
    st.subheader("Chain scores")
    chain_stats = []
    for ch in unique_chains:
        mask = np.array([c == ch for c in chains])
        chain_stats.append({
            "Chain": ch,
            "Residues": int(mask.sum()),
            "Mean score": float(scores[mask].mean().round(3)),
            "Max score": float(scores[mask].max().round(3)),
            "Pocket residues": int((scores[mask] >= threshold).sum()),
        })
    st.dataframe(pd.DataFrame(chain_stats).set_index("Chain"), use_container_width=True)

    if len(unique_chains) == 3:
        st.caption("3-chain structure detected — likely PCNA homotrimer (A/B/C).")
        chain_means = [scores[np.array([c == ch for c in chains])].mean()
                       for ch in unique_chains]
        variance = np.var(chain_means)
        if variance < 0.001:
            st.success(f"Chain symmetry consistent (var={variance:.5f})")
        else:
            st.warning(f"Chain score variance={variance:.4f} — asymmetric prediction")

st.divider()

# ── exports ───────────────────────────────────────────────────────────────────
st.subheader("Export")
exp1, exp2 = st.columns(2)

with exp1:
    bfactor_pdb = export_bfactor_pdb(pdb_bytes, residues, scores)
    st.download_button(
        "Download B-factor PDB (PyMOL coloring)",
        data=bfactor_pdb,
        file_name=f"{pdb_label}_pocket_scores.pdb",
        mime="chemical/x-pdb",
        help="In PyMOL: spectrum b, red_white_green — red = high pocket probability",
    )

with exp2:
    import pandas as pd
    csv_df = pd.DataFrame({
        "chain": chains, "resid": resids, "aa": resnames,
        "pocket_score": scores.round(4),
        "is_pocket_candidate": pocket_mask,
    })
    st.download_button(
        "Download scores CSV",
        data=csv_df.to_csv(index=False),
        file_name=f"{pdb_label}_pocket_scores.csv",
        mime="text/csv",
    )

st.caption(f"Model: PocketGNN {model_key} · {model.param_count() if hasattr(model, 'param_count') else '?'} parameters · Structure: {pdb_label}")
