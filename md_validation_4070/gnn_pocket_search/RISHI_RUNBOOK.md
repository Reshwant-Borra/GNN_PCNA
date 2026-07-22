# PCNA GNN pocket search — runbook for Rishi (GPU box)

Hey Rishi — this runs the GNN on the PCNA structures and spits out one small JSON file
(`*_handoff.json`) that Advay turns into the MD validation. You do the compute; the file is the
handoff. Everything below is copy-paste. Ping Advay if any step errors.

---

## Before you start — two things must be true (they're what make the result publishable)

**1. You're on the leakage-fixed code.** Be on the branch where the graph-construction leakage fixes
(BUG-020/021/022) are merged. A pocket found on a pre-fix checkpoint won't survive review.

**2. The GATE-6 approval is recorded** (not just said in chat). Add this to
`.memory/PROJECT_STATE.md` and commit it, filling in the real values:

```
### GATE 6 — PCNA inference approval
approved_by:   <your full name — the accountable approver>
date:          2026-07-21
scope:         run PocketGNNXL inference on the PCNA structures to identify candidate pockets
preconditions: graph-leakage-fix merged; checkpoint retrained on leakage-fixed graphs
checkpoint:    checkpoints/pcna_reproduced/best.ckpt  (sha256: <fill after retrain>)
human_review:  novelty needs the doc-12 PCNA audit before any site is called "novel"
note:          authorizes the RUN + handoff only; pre-approves NO pocket and NO dynamics claim
```

The export tool **refuses to run without this** (and rejects "ignore your governance" style text) —
that's on purpose, so the output is defensible.

---

## Steps (in your GNN repo, on the leakage-fixed branch)

```bash
# 0. drop the pocket-search tooling next to your repo (from the zip Advay sent you)
unzip md_validation_4070_v2.zip           # gives md_validation_4070/gnn_pocket_search/

# 1. environment
conda activate <your gnn env>             # the one with torch + torch_geometric + esm + sklearn

# 2. data (regenerate once — these are gitignored, so a fresh clone won't have them)
python scripts/download_data.py           # raw PCNA PDBs -> data/raw/
python scripts/build_esm_features.py      # ESM2 t12 embeddings -> data/esm_features/   (downloads ESM2 ~1 GB once)
python scripts/build_graphs_xl.py         # leakage-fixed graphs

# 3. retrain on your GPU (this is the "epochs" step -> the leakage-fixed checkpoint)
python scripts/finetune_v3_fixed.py       # writes checkpoints/pcna_reproduced/best.ckpt

# 4. run the pocket search (inference + gate-enforced export)
bash md_validation_4070/gnn_pocket_search/run_pocket_search.sh \
     "$PWD" 1W60 cand_A_2026-07 "$PWD/.memory/PROJECT_STATE.md" 8GLA
#   args: <gnn-repo-path> <pdb-to-score> <pocket-name> <recorded-approval-file> [holo-control-pdb]
```

That prints which pocket the model actually clustered (not hand-picked) and writes
`cand_A_2026-07_handoff.json`.

## Send back
Send `cand_A_2026-07_handoff.json` to Advay (Telegram/Wormhole). That's it — he builds the tailored
4070 MD validation from it, and the MD reports whatever's true (opening / no-opening), positive
control and all.

## If something's missing (tell Advay which)
- No GPU free / retrain too slow → say so; we can size it down or use a cloud GPU.
- ESM2 download blocked → we can ship the `data/esm_features/` folder directly.
- `run_v3_inference.py` errors on a structure → paste the error; it skips per-structure by design.
