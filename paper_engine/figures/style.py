"""Publication-grade matplotlib styling.

A single source of truth for the journal/competition look: serif type, generous
sizes, honest spines, 300+ DPI export, and a colorblind-safe palette (Okabe-Ito).
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Dict

import matplotlib

matplotlib.use("Agg")  # headless render; safe on CPU-only / no-display machines
import matplotlib.pyplot as plt  # noqa: E402

# Okabe-Ito colorblind-safe qualitative palette.
OKABE_ITO = {
    "black": "#000000",
    "orange": "#E69F00",
    "sky_blue": "#56B4E9",
    "bluish_green": "#009E73",
    "yellow": "#F0E442",
    "blue": "#0072B2",
    "vermillion": "#D55E00",
    "reddish_purple": "#CC79A7",
    "grey": "#999999",
}

# Semantic colors used across figures.
PRIMARY_COLOR = OKABE_ITO["blue"]          # the GraphSAGE-3L primary model
BASELINE_COLOR = OKABE_ITO["sky_blue"]     # GNN baselines
NAIVE_COLOR = OKABE_ITO["grey"]            # random / degree references
ACCENT_COLOR = OKABE_ITO["vermillion"]     # callouts / ablations
POSITIVE_COLOR = OKABE_ITO["bluish_green"]
NEGATIVE_COLOR = OKABE_ITO["orange"]

DPI = 300

RCPARAMS: Dict[str, object] = {
    "figure.dpi": 110,
    "savefig.dpi": DPI,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.04,
    "font.family": "serif",
    "font.serif": ["DejaVu Serif", "Times New Roman", "Times", "Georgia"],
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "axes.linewidth": 0.8,
    "axes.edgecolor": "#333333",
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": "#DDDDDD",
    "grid.linewidth": 0.6,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "legend.fontsize": 9.5,
    "legend.frameon": False,
    "lines.linewidth": 1.8,
    "lines.markersize": 5,
    "figure.titlesize": 13,
    "figure.titleweight": "bold",
}


def set_style() -> None:
    """Apply the publication rcParams globally."""
    plt.rcParams.update(RCPARAMS)


@contextmanager
def publication_style():
    """Context manager that applies the style and restores prior rcParams."""
    prior = dict(plt.rcParams)
    try:
        plt.rcParams.update(RCPARAMS)
        yield
    finally:
        plt.rcParams.update(prior)


def despine(ax, *, top: bool = True, right: bool = True) -> None:
    """Remove chartjunk spines for a cleaner look."""
    if top:
        ax.spines["top"].set_visible(False)
    if right:
        ax.spines["right"].set_visible(False)
