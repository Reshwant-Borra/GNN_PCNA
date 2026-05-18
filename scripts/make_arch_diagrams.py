"""
Professional architecture diagrams for GNN-PCNA paper.
Uses matplotlib patheffects, section panels, and clean card design.
Outputs: results/figures/arch_model.png, results/figures/arch_pipeline.png
"""
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.patheffects as pe
import numpy as np
from pathlib import Path

OUT = Path(__file__).parent.parent / "results" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# ── Palette ───────────────────────────────────────────────────────────────────
NAVY   = "#1B2A4A"
BLUE   = "#2563EB"
LBLUE  = "#DBEAFE"
ORANGE = "#EA580C"
LORANGE= "#FEF3C7"
GREEN  = "#16A34A"
LGREEN = "#DCFCE7"
GRAY   = "#6B7280"
LGRAY  = "#F9FAFB"
WHITE  = "#FFFFFF"
PANEL  = "#F1F5F9"
DARK   = "#0F172A"
MID    = "#334155"


def shadow():
    return [pe.withSimplePatchShadow(offset=(2, -2), shadow_rgbFace="#cccccc", alpha=0.4)]


def card(ax, x, y, w, h, title, subtitle=None,
         fc=WHITE, ec=BLUE, tc=DARK, title_size=9.5,
         sub_size=7.5, bold=True, radius=0.008):
    r = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0,rounding_size={radius}",
                       linewidth=1.4, edgecolor=ec, facecolor=fc,
                       zorder=4)
    r.set_path_effects(shadow())
    ax.add_patch(r)
    ty = y + h / 2 + (h * 0.1 if subtitle else 0)
    ax.text(x + w / 2, ty, title,
            ha="center", va="center", fontsize=title_size,
            fontweight="bold" if bold else "normal",
            color=tc, zorder=5, clip_on=False,
            fontfamily="DejaVu Sans")
    if subtitle:
        ax.text(x + w / 2, y + h / 2 - h * 0.18, subtitle,
                ha="center", va="center", fontsize=sub_size,
                color=GRAY, zorder=5, style="italic",
                fontfamily="DejaVu Sans")


def panel_bg(ax, x, y, w, h, label, fc=PANEL, lc="#CBD5E1"):
    r = FancyBboxPatch((x, y), w, h,
                       boxstyle="round,pad=0,rounding_size=0.012",
                       linewidth=1, edgecolor=lc, facecolor=fc,
                       zorder=1, alpha=0.7)
    ax.add_patch(r)
    ax.text(x + w / 2, y + h - 0.018, label,
            ha="center", va="top", fontsize=7.5,
            color=MID, fontweight="bold", zorder=2,
            fontfamily="DejaVu Sans")


def arr(ax, x1, y1, x2, y2, col=MID, lw=1.4, style="-|>"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=col,
                                lw=lw, mutation_scale=11),
                zorder=3)


def hline(ax, x1, x2, y, col=MID, lw=1.4):
    ax.plot([x1, x2], [y, y], color=col, lw=lw, zorder=3)


def vline(ax, x, y1, y2, col=MID, lw=1.4):
    ax.plot([x, x], [y1, y2], color=col, lw=lw, zorder=3)


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 1 — Model Architecture
# ─────────────────────────────────────────────────────────────────────────────

def make_arch():
    W, H = 10, 15
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor(WHITE)

    # ── Title bar ─────────────────────────────────────────────────────────
    title_rect = FancyBboxPatch((0, 0.955), 1, 0.045,
                                boxstyle="square,pad=0",
                                facecolor=NAVY, edgecolor="none", zorder=0)
    ax.add_patch(title_rect)
    ax.text(0.5, 0.977, "PocketGNNXL  —  Dual-Branch Graph Attention Network",
            ha="center", va="center", fontsize=12, fontweight="bold",
            color=WHITE, zorder=1, fontfamily="DejaVu Sans")
    ax.text(0.5, 0.960, "13.4M parameters  ·  520-dim input  ·  per-residue cryptic pocket scoring",
            ha="center", va="center", fontsize=7.5, color="#93C5FD", zorder=1,
            fontfamily="DejaVu Sans")

    # ── INPUT SECTION ─────────────────────────────────────────────────────
    panel_bg(ax, 0.02, 0.835, 0.96, 0.11, "INPUT FEATURES", fc="#EFF6FF", lc=BLUE)

    # Hand-crafted
    card(ax, 0.06, 0.850, 0.30, 0.07,
         "Hand-crafted Features",
         "40-dim · AA identity, SASA, SS,\nB-factor, φ/ψ, density, charge",
         fc=LBLUE, ec=BLUE, tc=NAVY)

    # ESM2
    card(ax, 0.44, 0.850, 0.30, 0.07,
         "ESM2 Language Model",
         "480-dim · facebook/esm2_t12_35M\npre-cached per structure",
         fc=LORANGE, ec=ORANGE, tc="#7C2D12")

    # Edge features (right side)
    card(ax, 0.77, 0.850, 0.19, 0.07,
         "Edge Features",
         "6-dim\ndist, seq-sep, chain",
         fc=LGREEN, ec=GREEN, tc="#14532D")

    # Concat arrows
    arr(ax, 0.21, 0.850, 0.44, 0.807)
    arr(ax, 0.59, 0.850, 0.56, 0.807)

    # ── CONCAT + PRE-ENCODER ──────────────────────────────────────────────
    card(ax, 0.20, 0.768, 0.60, 0.055,
         "Concatenate  →  520-dim node features per residue",
         fc=WHITE, ec=NAVY, tc=NAVY, title_size=9)

    arr(ax, 0.50, 0.768, 0.50, 0.725)

    card(ax, 0.20, 0.678, 0.60, 0.050,
         "Pre-Encoder",
         "Linear(520 → 256 → 512 → 768)  +  LayerNorm",
         fc=LBLUE, ec=NAVY, tc=NAVY, title_size=9.5)

    # Edge features arrow to pre-encoder
    ax.annotate("", xy=(0.80, 0.703), xytext=(0.96, 0.885),
                arrowprops=dict(arrowstyle="-|>", color=GREEN,
                                lw=1.2, mutation_scale=10,
                                connectionstyle="arc3,rad=-0.25"), zorder=3)

    # ── SPLIT LINE ────────────────────────────────────────────────────────
    vline(ax, 0.50, 0.678, 0.645)
    hline(ax, 0.20, 0.80, 0.645)
    # down to branches
    ax.annotate("", xy=(0.26, 0.625), xytext=(0.20, 0.645),
                arrowprops=dict(arrowstyle="-|>", color=MID, lw=1.4, mutation_scale=11), zorder=3)
    ax.annotate("", xy=(0.74, 0.625), xytext=(0.80, 0.645),
                arrowprops=dict(arrowstyle="-|>", color=MID, lw=1.4, mutation_scale=11), zorder=3)

    # ── SPATIAL BRANCH ────────────────────────────────────────────────────
    panel_bg(ax, 0.03, 0.195, 0.44, 0.43, "SPATIAL BRANCH", fc="#EFF6FF", lc=BLUE)

    gat_h = 0.058
    gat_gap = 0.014
    y_start = 0.575
    for i in range(5):
        y = y_start - i * (gat_h + gat_gap)
        card(ax, 0.07, y, 0.36, gat_h,
             f"GATv2Conv  #{i+1}",
             "hidden=768 · heads=8 · BatchNorm · Dropout(0.1)",
             fc=LBLUE, ec=BLUE, tc=NAVY, title_size=9, sub_size=7)
        if i < 4:
            arr(ax, 0.25, y, 0.25, y - gat_gap, col=BLUE)

    # Virtual node
    vnode_y = 0.370
    card(ax, 0.05, vnode_y, 0.20, 0.052,
         "Virtual Node",
         "vnode_proj + gate",
         fc=LGREEN, ec=GREEN, tc="#14532D", title_size=8.5, sub_size=7)
    # bidirectional arrow to branch
    ax.annotate("", xy=(0.25, vnode_y + 0.026), xytext=(0.25 + 0.04, vnode_y + 0.026),
                arrowprops=dict(arrowstyle="<->", color=GREEN, lw=1.2, mutation_scale=10), zorder=3)

    # ── SEQUENTIAL BRANCH ─────────────────────────────────────────────────
    panel_bg(ax, 0.53, 0.195, 0.44, 0.43, "SEQUENTIAL BRANCH", fc="#FFF7ED", lc=ORANGE)

    y_start2 = 0.575
    for i in range(4):
        y = y_start2 - i * (gat_h + gat_gap)
        card(ax, 0.57, y, 0.36, gat_h,
             f"GATv2Conv  #{i+1}",
             "hidden=768 · heads=8 · BatchNorm · Dropout(0.1)",
             fc=LORANGE, ec=ORANGE, tc="#7C2D12", title_size=9, sub_size=7)
        if i < 3:
            arr(ax, 0.75, y, 0.75, y - gat_gap, col=ORANGE)

    # Branch labels
    ax.text(0.25, 0.632, "5×", ha="center", va="bottom",
            fontsize=9, fontweight="bold", color=BLUE, zorder=5)
    ax.text(0.75, 0.632, "4×", ha="center", va="bottom",
            fontsize=9, fontweight="bold", color=ORANGE, zorder=5)

    # ── FUSION ────────────────────────────────────────────────────────────
    y_fuse_top = 0.195
    # lines from branches down
    vline(ax, 0.25, y_fuse_top, 0.170)
    vline(ax, 0.75, y_fuse_top, 0.170)
    hline(ax, 0.25, 0.75, 0.170)
    arr(ax, 0.50, 0.170, 0.50, 0.148)

    panel_bg(ax, 0.10, 0.040, 0.80, 0.115, "FUSION & OUTPUT", fc="#F0FDF4", lc=GREEN)

    card(ax, 0.14, 0.090, 0.72, 0.050,
         "Concatenate branches  →  Linear(1536→768) → ReLU → Linear(768→1)",
         fc=WHITE, ec=NAVY, tc=NAVY, title_size=9)

    arr(ax, 0.50, 0.090, 0.50, 0.066)

    # Output card — dark filled
    out_rect = FancyBboxPatch((0.22, 0.044), 0.56, 0.044,
                              boxstyle="round,pad=0,rounding_size=0.008",
                              facecolor=NAVY, edgecolor=NAVY, zorder=4)
    out_rect.set_path_effects(shadow())
    ax.add_patch(out_rect)
    ax.text(0.50, 0.066, "Sigmoid  →  Per-residue cryptic pocket score  ∈  [0, 1]",
            ha="center", va="center", fontsize=9.5, fontweight="bold",
            color=WHITE, zorder=5, fontfamily="DejaVu Sans")

    # ── Legend ─────────────────────────────────────────────────────────────
    legend_items = [
        mpatches.Patch(fc=LBLUE,   ec=BLUE,   label="Spatial GATv2Conv"),
        mpatches.Patch(fc=LORANGE, ec=ORANGE, label="Sequential GATv2Conv"),
        mpatches.Patch(fc=LGREEN,  ec=GREEN,  label="Virtual node / edges"),
        mpatches.Patch(fc=NAVY,    ec=NAVY,   label="Output"),
    ]
    ax.legend(handles=legend_items, loc="lower right",
              fontsize=7.5, framealpha=0.95, edgecolor="#CBD5E1",
              fancybox=True, bbox_to_anchor=(0.99, 0.005))

    plt.tight_layout(pad=0)
    fig.savefig(str(OUT / "arch_model.png"), dpi=250, bbox_inches="tight",
                facecolor=WHITE)
    plt.close(fig)
    print("Saved arch_model.png")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 2 — Inference Pipeline
# ─────────────────────────────────────────────────────────────────────────────

def make_pipeline():
    W, H = 15, 6.5
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor(WHITE)

    # Title bar
    title_rect = FancyBboxPatch((0, 0.92), 1, 0.08,
                                boxstyle="square,pad=0",
                                facecolor=NAVY, edgecolor="none", zorder=0)
    ax.add_patch(title_rect)
    ax.text(0.5, 0.962, "GNN-PCNA  —  Inference Pipeline",
            ha="center", va="center", fontsize=13, fontweight="bold",
            color=WHITE, zorder=1, fontfamily="DejaVu Sans")
    ax.text(0.5, 0.932, "From PDB structure to ranked cryptic pocket candidates",
            ha="center", va="center", fontsize=8.5, color="#93C5FD", zorder=1,
            fontfamily="DejaVu Sans")

    # ── SECTION 1: Graph Construction ─────────────────────────────────────
    panel_bg(ax, 0.01, 0.52, 0.56, 0.36, "GRAPH CONSTRUCTION", fc="#EFF6FF", lc=BLUE)

    bw, bh = 0.118, 0.145
    by = 0.575
    boxes_top = [
        (0.025, "PDB File", ".pdb / RCSB fetch",         "#F8FAFC", GRAY),
        (0.155, "Structure\nParser", "BioPython\nCα extraction",       LBLUE,   BLUE),
        (0.285, "Graph\nBuilder",   "k-NN k=10, r=10Å\n6-dim edges",  LBLUE,   BLUE),
        (0.415, "Hand-crafted\nFeatures", "40-dim nodes\nSASA·SS·φψ·B", LBLUE, BLUE),
    ]
    for i, (bx, title, sub, fc, ec) in enumerate(boxes_top):
        card(ax, bx, by, bw, bh, title, sub, fc=fc, ec=ec, tc=NAVY,
             title_size=8.5, sub_size=7)
        if i < len(boxes_top) - 1:
            arr(ax, bx + bw, by + bh/2, bx + bw + 0.012, by + bh/2, col=BLUE)

    # ── SECTION 2: ESM2 Path ───────────────────────────────────────────────
    panel_bg(ax, 0.01, 0.10, 0.56, 0.38, "ESM2 LANGUAGE MODEL PATH", fc="#FFF7ED", lc=ORANGE)

    esm_boxes = [
        (0.155, "Sequence\nExtract", "FASTA from\nstructure",           LORANGE, ORANGE),
        (0.285, "ESM2\n35M Model",  "facebook/esm2\n480-dim embed.",   LORANGE, ORANGE),
        (0.415, "ESM2\nEmbeddings", "480-dim per residue\npre-cached", LORANGE, ORANGE),
    ]
    ey = 0.165
    for i, (bx, title, sub, fc, ec) in enumerate(esm_boxes):
        card(ax, bx, ey, bw, bh, title, sub, fc=fc, ec=ec, tc="#7C2D12",
             title_size=8.5, sub_size=7)
        if i < len(esm_boxes) - 1:
            arr(ax, bx + bw, ey + bh/2, bx + bw + 0.012, ey + bh/2, col=ORANGE)

    # Dashed drop from graph builder to ESM path
    ax.plot([0.345, 0.345], [by, ey + bh],
            color=ORANGE, lw=1.3, linestyle=(0, (4, 3)), zorder=3)
    ax.annotate("", xy=(0.345, ey + bh + 0.002), xytext=(0.345, ey + bh + 0.05),
                arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.3, mutation_scale=10), zorder=3)

    # Cache note
    ax.text(0.475, 0.305, "cached in\ndata/esm_features/",
            ha="center", va="center", fontsize=7, color=ORANGE, style="italic",
            bbox=dict(fc="white", ec=ORANGE, boxstyle="round,pad=0.2", lw=0.8, alpha=0.9))

    # ── CONCATENATE ───────────────────────────────────────────────────────
    cx, cy, cw, ch = 0.593, 0.38, 0.10, 0.195
    card(ax, cx, cy, cw, ch,
         "Concat\n520-dim",
         "hand-crafted\n+ ESM2",
         fc=WHITE, ec=NAVY, tc=NAVY, title_size=9, sub_size=7.5)

    # Arrows into concat
    arr(ax, 0.415 + bw, by + bh/2, cx, cy + ch * 0.72, col=BLUE)
    arr(ax, 0.415 + bw, ey + bh/2, cx, cy + ch * 0.28, col=ORANGE)

    # ── MODEL ─────────────────────────────────────────────────────────────
    mx, my, mw, mh = 0.722, 0.30, 0.12, 0.37
    model_rect = FancyBboxPatch((mx, my), mw, mh,
                                boxstyle="round,pad=0,rounding_size=0.012",
                                facecolor=NAVY, edgecolor=NAVY, zorder=4)
    model_rect.set_path_effects(shadow())
    ax.add_patch(model_rect)
    ax.text(mx + mw/2, my + mh*0.62, "PocketGNNXL", ha="center", va="center",
            fontsize=10, fontweight="bold", color=WHITE, zorder=5)
    ax.text(mx + mw/2, my + mh*0.42, "13.4M params", ha="center", va="center",
            fontsize=8, color="#93C5FD", zorder=5, style="italic")
    ax.text(mx + mw/2, my + mh*0.25, "Dual-branch\nGATv2Conv", ha="center", va="center",
            fontsize=7.5, color="#BFDBFE", zorder=5)
    ax.text(mx + mw/2, my + mh*0.08, "threshold > 0.40", ha="center", va="center",
            fontsize=7, color="#6EE7B7", zorder=5, style="italic")

    arr(ax, cx + cw, cy + ch/2, mx, my + mh/2, col=NAVY, lw=1.6)

    # ── POST-PROCESSING ───────────────────────────────────────────────────
    panel_bg(ax, 0.862, 0.10, 0.128, 0.82, "POST-PROCESSING", fc="#F0FDF4", lc=GREEN)

    post_boxes = [
        (0.235, "DBSCAN\nCluster", "eps=6Å\nmin_pts=3", LGREEN, GREEN),
        (0.09,  "Ranked\nPockets",  "by cluster\nmean score", "#BBF7D0", GREEN),
    ]
    for yoff, title, sub, fc, ec in post_boxes:
        card(ax, 0.872, yoff, 0.108, 0.135, title, sub,
             fc=fc, ec=ec, tc="#14532D", title_size=8.5, sub_size=7)

    arr(ax, mx + mw, my + mh*0.7, 0.872, 0.302, col=GREEN, lw=1.4)
    arr(ax, 0.926, 0.235, 0.926, 0.225, col=GREEN, lw=1.4)

    # ── Legend ─────────────────────────────────────────────────────────────
    legend_items = [
        mpatches.Patch(fc=LBLUE,   ec=BLUE,   label="Graph construction"),
        mpatches.Patch(fc=LORANGE, ec=ORANGE, label="ESM2 language model"),
        mpatches.Patch(fc=NAVY,    ec=NAVY,   label="PocketGNNXL"),
        mpatches.Patch(fc=LGREEN,  ec=GREEN,  label="Post-processing"),
    ]
    ax.legend(handles=legend_items, loc="lower right",
              fontsize=8, framealpha=0.95, edgecolor="#CBD5E1",
              fancybox=True, bbox_to_anchor=(0.998, 0.005))

    plt.tight_layout(pad=0)
    fig.savefig(str(OUT / "arch_pipeline.png"), dpi=250, bbox_inches="tight",
                facecolor=WHITE)
    plt.close(fig)
    print("Saved arch_pipeline.png")


if __name__ == "__main__":
    make_arch()
    make_pipeline()
