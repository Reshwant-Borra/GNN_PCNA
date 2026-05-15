"""
Build PyTorch Geometric graphs from residue lists.

v2 changes vs v1:
  - Node features: 26 → 40 dims (physicochemical + pseudo-dihedrals + geometry)
  - Two graph views: contact graph (8 Å) + backbone sequential graph (|i–j| ≤ 2)
  - Edge features: 2 → 6 dims (adds inv_dist, same_chain, is_backbone, cross_chain)
  - build_graph_v2() returns the dual-graph Data object for PocketGNN v2
  - build_graph() (v1 API) still works unchanged for backward compat

Node feature layout (40 dims)
──────────────────────────────
 [0:20]   aa_onehot           — 20 standard amino acids
 [20]     sasa_norm           — SASA / 300, clamped to [0,1]
 [21:24]  ss_onehot           — helix / strand / coil
 [24]     b_factor_norm       — B-factor / 100, clamped to [0,1]
 [25]     rel_pos             — position / (len-1)
 [26]     hydrophobicity      — Kyte-Doolittle, normalized [0,1]
 [27]     charge              — formal charge at pH 7, in {-1, 0, +1}
 [28]     volume              — Van der Waals volume, normalized
 [29]     flexibility         — B-factor propensity, normalized
 [30]     sin_pseudo_phi      — sin of Cα pseudo-dihedral (i-1,i,i+1,i+2)
 [31]     cos_pseudo_phi
 [32]     sin_pseudo_psi      — sin of Cα pseudo-dihedral (i-2,i-1,i,i+1)
 [33]     cos_pseudo_psi
 [34]     local_density_5A    — neighbour count ≤ 5 Å / 10, clamped to [0,1]
 [35]     local_density_10A   — neighbour count ≤ 10 Å / 30, clamped to [0,1]
 [36]     is_interface        — 1 if any cross-chain neighbour within 8 Å
 [37:40]  chain_onehot        — A=100, B=010, C=001, other=000

Edge feature layout (6 dims)
─────────────────────────────
 [0]  dist_norm      — dist / cutoff
 [1]  inv_dist       — 1 / (1 + dist)
 [2]  seq_sep_norm   — |i-j|/20, clamped [0,1]; 1.0 for cross-chain
 [3]  same_chain     — 1 if same chain, 0 otherwise
 [4]  is_backbone    — 1 if |i-j|==1 and same chain
 [5]  cross_chain    — 1 if different chains (redundant with same_chain, kept for clarity)
"""

from __future__ import annotations

import numpy as np
import torch
from torch_geometric.data import Data

from .parse_pdb import Residue

# ── Amino acid lookup tables ─────────────────────────────────────────────────

AA_ONE_HOT = {
    'ALA': 0, 'ARG': 1,  'ASN': 2,  'ASP': 3,  'CYS': 4,
    'GLN': 5, 'GLU': 6,  'GLY': 7,  'HIS': 8,  'ILE': 9,
    'LEU': 10,'LYS': 11, 'MET': 12, 'PHE': 13, 'PRO': 14,
    'SER': 15,'THR': 16, 'TRP': 17, 'TYR': 18, 'VAL': 19,
}

SS_MAP = {'H': 0, 'E': 1, 'C': 2}

# Kyte-Doolittle hydrophobicity, rescaled to [0, 1] from original [-4.5, 4.5]
_KD_RAW = {
    'ILE': 4.5,  'VAL': 4.2,  'LEU': 3.8,  'PHE': 2.8,  'CYS': 2.5,
    'MET': 1.9,  'ALA': 1.8,  'GLY': -0.4, 'THR': -0.7, 'SER': -0.8,
    'TRP': -0.9, 'TYR': -1.3, 'PRO': -1.6, 'HIS': -3.2, 'GLU': -3.5,
    'GLN': -3.5, 'ASP': -3.5, 'ASN': -3.5, 'LYS': -3.9, 'ARG': -4.5,
}
_kd_min, _kd_max = -4.5, 4.5
HYDROPHOBICITY = {aa: (_KD_RAW.get(aa, 0) - _kd_min) / (_kd_max - _kd_min)
                  for aa in AA_ONE_HOT}

# Formal charge at pH 7 (mapped to -1, 0, +1 as float)
CHARGE = {aa: 0.0 for aa in AA_ONE_HOT}
CHARGE.update({'ARG': 1.0, 'LYS': 1.0, 'ASP': -1.0, 'GLU': -1.0, 'HIS': 0.1})

# Van der Waals volume (Å³), normalized by TRP=227
_VOL_RAW = {
    'GLY': 60.1, 'ALA': 88.6, 'SER': 89.0, 'PRO': 112.7, 'VAL': 140.0,
    'THR': 116.1,'CYS': 108.5,'ILE': 166.7,'LEU': 166.7,'ASN': 114.1,
    'ASP': 111.1,'GLN': 143.8,'LYS': 168.6,'GLU': 138.4,'MET': 162.9,
    'HIS': 153.2,'PHE': 189.9,'ARG': 173.4,'TYR': 193.6,'TRP': 227.8,
}
_vol_max = 227.8
VOLUME = {aa: _VOL_RAW.get(aa, 100) / _vol_max for aa in AA_ONE_HOT}

# B-factor propensity (Vihinen 1994), normalized to [0,1]
_FLEX_RAW = {
    'ALA': 0.357,'ARG': 0.529,'ASN': 0.463,'ASP': 0.511,'CYS': 0.346,
    'GLN': 0.493,'GLU': 0.497,'GLY': 0.544,'HIS': 0.323,'ILE': 0.462,
    'LEU': 0.365,'LYS': 0.562,'MET': 0.295,'PHE': 0.314,'PRO': 0.509,
    'SER': 0.508,'THR': 0.444,'TRP': 0.305,'TYR': 0.420,'VAL': 0.386,
}
_flex_min = min(_FLEX_RAW.values())
_flex_max = max(_FLEX_RAW.values())
FLEXIBILITY = {aa: (_FLEX_RAW.get(aa, 0.4) - _flex_min) / (_flex_max - _flex_min)
               for aa in AA_ONE_HOT}

NODE_DIM = 40
EDGE_DIM = 6


# ── Geometry helpers ─────────────────────────────────────────────────────────

def _pseudo_dihedral(p1: np.ndarray, p2: np.ndarray,
                     p3: np.ndarray, p4: np.ndarray) -> float:
    """Cα pseudo-dihedral angle in radians between 4 consecutive Cα atoms."""
    b1 = p2 - p1
    b2 = p3 - p2
    b3 = p4 - p3
    n1 = np.cross(b1, b2)
    n2 = np.cross(b2, b3)
    norm1 = np.linalg.norm(n1)
    norm2 = np.linalg.norm(n2)
    if norm1 < 1e-8 or norm2 < 1e-8:
        return 0.0
    n1 = n1 / norm1
    n2 = n2 / norm2
    b2_hat = b2 / (np.linalg.norm(b2) + 1e-8)
    cos_d = np.clip(np.dot(n1, n2), -1.0, 1.0)
    sin_d = np.dot(np.cross(n1, n2), b2_hat)
    return float(np.arctan2(sin_d, cos_d))


def _compute_pseudo_dihedrals(
    coords: np.ndarray,            # (N, 3)
    chain_ids: np.ndarray,         # (N,) str
) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute two pseudo-dihedrals per residue i:
      phi-like: (i-1, i, i+1, i+2)
      psi-like: (i-2, i-1, i, i+1)
    Residues at chain ends get 0.0.
    Returns (phi_arr, psi_arr) each shape (N,) in radians.
    """
    N = len(coords)
    phi_arr = np.zeros(N, dtype=np.float32)
    psi_arr = np.zeros(N, dtype=np.float32)

    for i in range(N):
        # phi: needs i-1, i, i+1, i+2 — all same chain
        if (1 <= i < N - 2
                and chain_ids[i-1] == chain_ids[i] == chain_ids[i+1] == chain_ids[i+2]):
            phi_arr[i] = _pseudo_dihedral(
                coords[i-1], coords[i], coords[i+1], coords[i+2])

        # psi: needs i-2, i-1, i, i+1 — all same chain
        if (2 <= i < N - 1
                and chain_ids[i-2] == chain_ids[i-1] == chain_ids[i] == chain_ids[i+1]):
            psi_arr[i] = _pseudo_dihedral(
                coords[i-2], coords[i-1], coords[i], coords[i+1])

    return phi_arr, psi_arr


# ── Node feature builders ────────────────────────────────────────────────────

def _node_features_v1(res: Residue, seq_len: int, seq_idx: int) -> np.ndarray:
    """Original 26-dim feature vector (v1 API preserved)."""
    aa_onehot = np.zeros(20, dtype=np.float32)
    idx = AA_ONE_HOT.get(res.resname, -1)
    if idx >= 0:
        aa_onehot[idx] = 1.0
    sasa_norm  = np.array([min(res.sasa / 300.0, 1.0)], dtype=np.float32)
    ss_onehot  = np.zeros(3, dtype=np.float32)
    ss_onehot[SS_MAP.get(res.secondary_structure, 2)] = 1.0
    bfactor    = np.array([min(res.b_factor / 100.0, 1.0)], dtype=np.float32)
    rel_pos    = np.array([seq_idx / max(seq_len - 1, 1)], dtype=np.float32)
    return np.concatenate([aa_onehot, sasa_norm, ss_onehot, bfactor, rel_pos])


def _build_node_matrix_v2(
    residues: list[Residue],
    coords: np.ndarray,     # (N, 3)
    chain_ids: np.ndarray,  # (N,) str
    dist_matrix: np.ndarray,  # (N, N)
) -> np.ndarray:
    """Build (N, 40) node feature matrix for PocketGNN v2."""
    N = len(residues)
    phi_arr, psi_arr = _compute_pseudo_dihedrals(coords, chain_ids)

    # Local density
    density_5  = (dist_matrix < 5.0).sum(axis=1) - 1   # subtract self
    density_10 = (dist_matrix < 10.0).sum(axis=1) - 1
    density_5_norm  = np.clip(density_5  / 10.0, 0, 1).astype(np.float32)
    density_10_norm = np.clip(density_10 / 30.0, 0, 1).astype(np.float32)

    # Interface flag: does this residue have a cross-chain neighbour within 8Å?
    is_interface = np.zeros(N, dtype=np.float32)
    for i in range(N):
        for j in range(N):
            if chain_ids[i] != chain_ids[j] and dist_matrix[i, j] < 8.0:
                is_interface[i] = 1.0
                break

    # Chain one-hot (for PCNA A/B/C; for other proteins all zeros)
    unique_chains = sorted(set(chain_ids))
    chain_to_idx  = {c: k for k, c in enumerate(unique_chains[:3])}

    rows = []
    for i, res in enumerate(residues):
        aa_onehot = np.zeros(20, dtype=np.float32)
        idx = AA_ONE_HOT.get(res.resname, -1)
        if idx >= 0:
            aa_onehot[idx] = 1.0

        sasa_norm  = min(res.sasa / 300.0, 1.0)
        ss_onehot  = np.zeros(3, dtype=np.float32)
        ss_onehot[SS_MAP.get(res.secondary_structure, 2)] = 1.0
        b_norm     = min(res.b_factor / 100.0, 1.0)
        rel_pos    = i / max(N - 1, 1)

        hydro = HYDROPHOBICITY.get(res.resname, 0.5)
        chg   = CHARGE.get(res.resname, 0.0)
        vol   = VOLUME.get(res.resname, 0.5)
        flex  = FLEXIBILITY.get(res.resname, 0.5)

        phi, psi = phi_arr[i], psi_arr[i]

        chain_oh = np.zeros(3, dtype=np.float32)
        cidx = chain_to_idx.get(res.chain, -1)
        if 0 <= cidx < 3:
            chain_oh[cidx] = 1.0

        row = np.array([
            *aa_onehot,                 # 20
            sasa_norm,                  # 1
            *ss_onehot,                 # 3
            b_norm,                     # 1
            rel_pos,                    # 1
            hydro, chg, vol, flex,      # 4
            np.sin(phi), np.cos(phi),   # 2
            np.sin(psi), np.cos(psi),   # 2
            density_5_norm[i],          # 1
            density_10_norm[i],         # 1
            is_interface[i],            # 1
            *chain_oh,                  # 3
        ], dtype=np.float32)            # total = 40

        rows.append(row)

    return np.stack(rows)              # (N, 40)


# ── Edge builders ─────────────────────────────────────────────────────────────

def _build_edge_attr(
    i_idx: np.ndarray,
    j_idx: np.ndarray,
    dist_matrix: np.ndarray,
    chain_ids: np.ndarray,
    resids: np.ndarray,
    cutoff: float,
) -> np.ndarray:
    """Build (E, 6) edge feature matrix."""
    dists      = dist_matrix[i_idx, j_idx]
    same_chain = (chain_ids[i_idx] == chain_ids[j_idx]).astype(np.float32)

    raw_sep   = np.abs(resids[i_idx] - resids[j_idx]).astype(np.float32)
    seq_sep   = np.where(same_chain.astype(bool),
                         np.minimum(raw_sep, 20.0) / 20.0, 1.0)

    is_backbone = (same_chain.astype(bool) & (raw_sep == 1)).astype(np.float32)
    cross_chain = 1.0 - same_chain

    return np.stack([
        dists / cutoff,          # dist_norm
        1.0 / (1.0 + dists),    # inv_dist
        seq_sep,                 # seq_sep_norm
        same_chain,              # same_chain
        is_backbone,             # is_backbone
        cross_chain,             # cross_chain
    ], axis=1).astype(np.float32)


def _build_backbone_edges(
    chain_ids: np.ndarray,
    resids: np.ndarray,
    dist_matrix: np.ndarray,
    max_sep: int = 2,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Build backbone sequential edges: residue pairs where |i−j| ≤ max_sep
    and same chain. Returns (i_idx, j_idx).
    """
    N = len(chain_ids)
    rows, cols = [], []
    for i in range(N):
        for j in range(N):
            if i == j:
                continue
            if chain_ids[i] == chain_ids[j]:
                sep = abs(int(resids[i]) - int(resids[j]))
                if 1 <= sep <= max_sep:
                    rows.append(i)
                    cols.append(j)
    if not rows:
        return np.empty((0,), dtype=np.int64), np.empty((0,), dtype=np.int64)
    return np.array(rows, dtype=np.int64), np.array(cols, dtype=np.int64)


# ── Public API ────────────────────────────────────────────────────────────────

def build_graph(
    residues: list[Residue],
    labels: np.ndarray | None = None,
    distance_cutoff: float = 8.0,
) -> Data:
    """
    v1 API: single contact graph with 26-dim nodes and 2-dim edges.
    Preserved for backward compatibility with CrypticGNN v1.
    """
    N = len(residues)
    if N == 0:
        raise ValueError("empty residue list")

    x      = np.stack([_node_features_v1(r, N, i) for i, r in enumerate(residues)])
    coords = np.stack([r.ca_coord for r in residues])
    chain_ids = np.array([r.chain  for r in residues])
    resids    = np.array([r.resid  for r in residues], dtype=np.int32)

    diff        = coords[:, None, :] - coords[None, :, :]
    dist_matrix = np.linalg.norm(diff, axis=-1)

    i_idx, j_idx = np.where((dist_matrix < distance_cutoff) & (dist_matrix > 0))
    if len(i_idx) == 0:
        raise ValueError(f"no edges within {distance_cutoff} Å")

    dists      = dist_matrix[i_idx, j_idx]
    same_chain = chain_ids[i_idx] == chain_ids[j_idx]
    raw_sep    = np.abs(resids[i_idx] - resids[j_idx]).astype(np.float32)
    seq_sep    = np.where(same_chain, np.minimum(raw_sep, 20.0) / 20.0, 1.0)
    edge_attr  = np.stack([dists / distance_cutoff, seq_sep], axis=1).astype(np.float32)

    data = Data(
        x          = torch.from_numpy(x),
        edge_index = torch.from_numpy(np.stack([i_idx, j_idx])).long(),
        edge_attr  = torch.from_numpy(edge_attr),
        pos        = torch.from_numpy(coords.astype(np.float32)),
    )
    if labels is not None:
        data.y = torch.from_numpy(labels.astype(np.float32))
    return data


def build_graph_v2(
    residues: list[Residue],
    labels: np.ndarray | None = None,
    distance_cutoff: float = 8.0,
    backbone_max_sep: int = 2,
) -> Data:
    """
    v2 API: dual-graph Data for PocketGNN v2.

    Returns Data with:
      .x                — (N, 40) node features
      .edge_index       — (2, E_contact) spatial contact graph
      .edge_attr        — (E_contact, 6)
      .edge_index_seq   — (2, E_seq) backbone sequential graph
      .edge_attr_seq    — (E_seq, 6)
      .pos              — (N, 3) Cα coordinates
      .chain_id         — (N,) long  0/1/2
      .resid            — (N,) long  residue sequence number
      .y                — (N,) if labels provided
    """
    N = len(residues)
    if N == 0:
        raise ValueError("empty residue list")

    coords    = np.stack([r.ca_coord for r in residues]).astype(np.float32)
    chain_ids = np.array([r.chain for r in residues])
    resids    = np.array([r.resid  for r in residues], dtype=np.int32)

    # Pairwise distances (shared by both graph builders)
    diff        = coords[:, None, :] - coords[None, :, :]   # (N, N, 3)
    dist_matrix = np.linalg.norm(diff, axis=-1)             # (N, N)

    # ── Node features (40-dim) ────────────────────────────────────────────
    x = _build_node_matrix_v2(residues, coords, chain_ids, dist_matrix)

    # ── Contact graph (spatial, 8 Å) ──────────────────────────────────────
    ci, cj = np.where((dist_matrix < distance_cutoff) & (dist_matrix > 0))
    if len(ci) == 0:
        raise ValueError(f"no spatial edges within {distance_cutoff} Å")
    contact_attr = _build_edge_attr(ci, cj, dist_matrix, chain_ids, resids, distance_cutoff)

    # ── Backbone graph (sequential, |i-j| ≤ 2, same chain) ───────────────
    bi, bj = _build_backbone_edges(chain_ids, resids, dist_matrix, backbone_max_sep)
    if len(bi) > 0:
        backbone_attr = _build_edge_attr(bi, bj, dist_matrix, chain_ids, resids, distance_cutoff)
    else:
        backbone_attr = np.empty((0, EDGE_DIM), dtype=np.float32)

    # ── Chain ID encoding ─────────────────────────────────────────────────
    unique_chains = sorted(set(chain_ids))
    chain_to_int  = {c: k for k, c in enumerate(unique_chains)}
    chain_id_int  = np.array([chain_to_int[c] for c in chain_ids], dtype=np.int64)

    data = Data(
        x              = torch.from_numpy(x),
        edge_index     = torch.from_numpy(np.stack([ci, cj])).long(),
        edge_attr      = torch.from_numpy(contact_attr),
        edge_index_seq = torch.from_numpy(np.stack([bi, bj]) if len(bi) > 0
                                          else np.zeros((2, 0), dtype=np.int64)).long(),
        edge_attr_seq  = torch.from_numpy(backbone_attr),
        pos            = torch.from_numpy(coords),
        chain_id       = torch.from_numpy(chain_id_int),
        resid          = torch.from_numpy(resids.astype(np.int64)),
    )
    if labels is not None:
        data.y = torch.from_numpy(labels.astype(np.float32))
    return data


def save_graph(data: Data, path: str) -> None:
    torch.save(data, path)


def load_graph(path: str) -> Data:
    return torch.load(path)
