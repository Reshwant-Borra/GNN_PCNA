"""
Convert residue list into a PyTorch Geometric Data object.
Nodes: residues. Edges: Cα–Cα pairs within distance cutoff.
"""
from __future__ import annotations
import numpy as np
import torch
from torch_geometric.data import Data

from .parse_pdb import Residue

AA_ONE_HOT = {
    'ALA':0,'ARG':1,'ASN':2,'ASP':3,'CYS':4,'GLN':5,'GLU':6,'GLY':7,
    'HIS':8,'ILE':9,'LEU':10,'LYS':11,'MET':12,'PHE':13,'PRO':14,
    'SER':15,'THR':16,'TRP':17,'TYR':18,'VAL':19,
}
SS_MAP = {'H': 0, 'E': 1, 'C': 2}


def residue_to_node_features(res: Residue, seq_len: int, seq_idx: int) -> np.ndarray:
    """
    Build 26-dim feature vector for a single residue.
    [aa_onehot(20), sasa(1), ss_onehot(3), b_factor(1), rel_pos(1)]
    """
    raise NotImplementedError


def build_graph(
    residues: list[Residue],
    labels: np.ndarray | None = None,
    distance_cutoff: float = 8.0,
) -> Data:
    """
    Construct PyG Data from a residue list.

    Returns:
        data.x          : (N, 26)  node features
        data.edge_index : (2, E)   COO format
        data.edge_attr  : (E, 2)   [distance, seq_separation]
        data.y          : (N,)     pocket labels (if provided)
        data.pos        : (N, 3)   Cα coordinates
    """
    raise NotImplementedError


def save_graph(data: Data, path: str) -> None:
    torch.save(data, path)


def load_graph(path: str) -> Data:
    return torch.load(path)
