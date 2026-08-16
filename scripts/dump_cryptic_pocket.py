"""Dump the GNN-predicted AOH1996 cryptic pocket on PCNA.

Reports, per ground-truth AOH1996 residue, the model score on the HOLO structure
(8GLA, pocket open) vs the APO structure (1W60, pocket closed). A cryptic pocket
should score high in holo and lower in apo. Also lists the model's top residues.
"""
from __future__ import annotations
import sys, json
from pathlib import Path
REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))
import torch, numpy as np
from src.models import PocketGNNXL

AOH_GT_BY_CHAIN = {
    "A": {25,26,27,38,39,40,41,42,44,45,46,47,123,125,126,128,231,232,233,234,250,251,252,253},
    "B": {23,25,26,27,38,39,40,41,42,44,45,46,47,123,125,126,128,231,232,233,234,250,251,252},
}
CKPT = REPO / "checkpoints/pcna_reproduced/best.ckpt"

def score(pdb):
    p = REPO / "data" / "pcna_xl" / f"{pdb}.pt"
    data = torch.load(str(p), weights_only=False)
    m = PocketGNNXL(node_in_dim=data.x.shape[1]).eval()
    m.load_state_dict(torch.load(str(CKPT), map_location="cpu", weights_only=True))
    with torch.no_grad():
        s = m(data.x, data.edge_index, data.edge_attr,
              data.edge_index_seq, data.edge_attr_seq, data.chain_id).numpy()
    resid = data.resid.numpy()
    chain = [chr(65+int(c)) for c in data.chain_id.numpy()]
    return s, resid, chain

def main():
    hs, hr, hc = score("8GLA")
    aps, apr, apc = score("1W60")
    # apo lookup by (chain,resid)
    apo = {(c, int(r)): float(v) for v, r, c in zip(aps, apr, apc)}

    rows = []
    for v, r, c in zip(hs, hr, hc):
        r = int(r)
        if r in AOH_GT_BY_CHAIN.get(c, set()):
            rows.append((c, r, float(v), apo.get((c, r), float("nan"))))
    rows.sort(key=lambda x: -x[2])

    print("=== GNN-predicted AOH1996 cryptic pocket (8GLA holo vs 1W60 apo) ===")
    print(f"{'chain':5s} {'res':>4s} {'holo':>7s} {'apo':>7s} {'delta':>7s}")
    for c, r, h, a in rows:
        d = h - a if a == a else float('nan')
        print(f"{c:5s} {r:4d} {h:7.3f} {a:7.3f} {d:7.3f}")

    print("\n--- summary ---")
    print(f"pocket residues scored      : {len(rows)}")
    # Report holo/apo/delta over the SAME set of residues: those with a valid apo
    # (1W60) match. This keeps holo_mean - apo_mean == delta_mean exactly, instead
    # of mixing an all-rows holo mean with matched-only apo/delta means.
    paired = [(h, a) for _, _, h, a in rows if a == a]  # a == a drops NaN (unmatched apo)
    n_unpaired = len(rows) - len(paired)
    if not paired:
        print("no pocket residues had a valid apo (1W60) match -- "
              "holo/apo/delta means undefined "
              "(check chain mapping / AOH_GT_BY_CHAIN).")
    else:
        holo_mean  = float(np.mean([h for h, _ in paired]))
        apo_mean   = float(np.mean([a for _, a in paired]))
        delta_mean = float(np.mean([h - a for h, a in paired]))
        print(f"matched pocket residues (apo & holo): {len(paired)}"
              + (f"  ({n_unpaired} unmatched, excluded from means)" if n_unpaired else ""))
        print(f"holo (8GLA) mean matched-pocket score: {holo_mean:.4f}")
        print(f"apo  (1W60) mean matched-pocket score: {apo_mean:.4f}")
        print(f"mean holo-apo delta (cryptic)        : {delta_mean:+.4f}")

    # top-15 residues overall on holo
    order = np.argsort(hs)[::-1][:15]
    print("\n=== top-15 residues by score on 8GLA (whole trimer) ===")
    for i in order:
        print(f"  chain {hc[i]} res {int(hr[i]):4d}  score {hs[i]:.3f}  "
              f"{'[AOH pocket]' if int(hr[i]) in AOH_GT_BY_CHAIN.get(hc[i],set()) else ''}")

if __name__ == "__main__":
    main()
