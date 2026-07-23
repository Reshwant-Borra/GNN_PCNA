# PCNA GNN pocket search — runbook for Rishi (GPU box)

Hey Rishi — this runs the GNN on the PCNA structures and spits out one small JSON file
(`*_handoff.json`) that Advay turns into the MD validation. You do the compute; the file is the
handoff. Everything below is copy-paste. Ping Advay if any step errors.

**Your review is applied** (thank you): the virtual-node batch-mixing fix, the batch-vector wiring in
training, the checkpoint-path override, and chain-qualified residue export are all in. See the
"Status" box below for what's OK to run now vs. what's needed before a headline result.

---

## Status — what this run is / isn't (per your review)
- ✅ **OK now:** running this to test the pipeline end-to-end and generate an **experimental** candidate.
- ⛔ **Not yet a publishable / competition-headline result** until: (1) retrain *after* the virtual-node
  fix (the old checkpoint predates it), (2) checkpoint paths consistent (handled below), (3) residue/
  chain mapping spot-checked (handled — see step 5).
- ⚠️ **Do NOT describe the score as a pristine untouched final test.** The old test set has already
  influenced development decisions, so its number is a development estimate, not an untouched holdout.

---

## Before you start — two things must be true

**1. You're on `graph-leakage-fix` — NOT `advay-parallel-track`.** `advay-parallel-track` only has the
MD-handoff tools; the runnable XL pipeline (model, training, inference, data) lives on
`graph-leakage-fix` (BUG-020/021/022). `git branch --show-current` should print `graph-leakage-fix`.

**2. The GATE-6 approval is recorded** (not just said in chat). Add this to `.memory/PROJECT_STATE.md`
and commit it, filling in the real values:

```
### GATE 6 — PCNA inference approval
approved_by:   <your full name — the accountable approver>
date:          2026-07-22
scope:         run PocketGNNXL inference on the PCNA structures to identify candidate pockets
preconditions: graph-leakage-fix merged; checkpoint RETRAINED after the virtual-node fix
checkpoint:    <path>  (sha256: <fill after retrain>)
human_review:  novelty needs the doc-12 PCNA audit before any site is called "novel"
note:          authorizes the RUN + handoff only; pre-approves NO pocket and NO dynamics claim
```

The export tool **refuses to run without this** (and rejects "ignore your governance" style text) —
that's on purpose, so the output is defensible.

---

## Easiest path — ONE command, both stages, in tmux
After setup (steps 0–2 below, once), this runs **GNN pocket search → MD validation** end to end,
detached in tmux, resuming the MD stage from checkpoints if the box reboots:
```bash
cd md_validation_4070/gnn_pocket_search
./run_all_in_tmux.sh <gnn-worktree> 1W60 cand_A_2026-07 <recorded-GATE6-approval-file> <gnn-env> 8GLA
#   -> Stage 1 GNN pocket search (gated) -> Stage 2 handoff->pocket -> Stage 3 MD (control,apo,analyze)
tmux attach -t pcna-full          # watch (detach: Ctrl-b then d);  tail -f full_*.log
```
It **won't start the MD stage** unless Stage 1 produced a handoff, which requires the recorded GATE-6
approval — so the gate still holds across the whole pipeline. Steps below are the same thing by hand.

## Steps (in the GNN repo, on `graph-leakage-fix`)

```bash
# 0. drop the pocket-search tooling next to your repo (from the zip Advay sent you)
unzip md_validation_4070_v2.zip           # gives md_validation_4070/gnn_pocket_search/
#    (MD stage needs the pcna-md-4070 env too: conda env create -f ../environment.yml)

# 1. environment
conda activate <your gnn env>             # torch + torch_geometric + esm + sklearn

# 2. data (regenerate once — these are gitignored, so a fresh clone won't have them)
python scripts/download_data.py           # raw PCNA PDBs -> data/raw/
python scripts/build_esm_features.py      # ESM2 t12 embeddings -> data/esm_features/  (downloads ESM2 ~1 GB once)
python scripts/build_graphs_xl.py         # leakage-fixed graphs

# 3. RETRAIN on your GPU (required — the virtual-node fix changed training).
#    Pin the output path so inference finds it (this resolves the checkpoint-path conflict:
#    finetune's default --out is checkpoints/pcna/best_pcna_v3_fixed.ckpt, but inference's default
#    is checkpoints/pcna_reproduced/best.ckpt — so make them match explicitly):
python scripts/finetune_v3_fixed.py --out checkpoints/pcna_reproduced/best.ckpt

# 4. run the pocket search (inference + gate-enforced export)
#    If you kept finetune's default --out instead, pass the SAME path here via CKPT (see run_pocket_search.sh),
#    or run inference directly with:  python scripts/run_v3_inference.py --ckpt <that path>
bash md_validation_4070/gnn_pocket_search/run_pocket_search.sh \
     "$PWD" 1W60 cand_A_2026-07 "$PWD/.memory/PROJECT_STATE.md" 8GLA
#   args: <gnn-repo-path> <pdb-to-score> <pocket-name> <recorded-approval-file> [holo-control-pdb]

# 5. sanity-check the residue mapping before sending: open cand_A_2026-07_handoff.json and confirm
#    pocket_residues is a list of {chain, resid} PAIRS (not bare numbers) and the chains/resids look
#    right for the structure. The AOH site spans two chains, so chain identity matters.
```

That prints which pocket the model actually clustered (not hand-picked) and writes
`cand_A_2026-07_handoff.json`.

## Send back
Send `cand_A_2026-07_handoff.json` to Advay (Telegram/Wormhole). He builds the tailored 4070 MD
validation from it, and the MD reports whatever's true (opening / no-opening), positive control and all.

## If something's missing (tell Advay which)
- No GPU free / retrain too slow → say so; we can size it down or use a cloud GPU.
- ESM2 download blocked → we can ship the `data/esm_features/` folder directly.
- `run_v3_inference.py` errors on a structure → paste the error; it skips per-structure by design.
- Checkpoint path mismatch (`FileNotFoundError` on the `.ckpt`) → you and inference used different
  paths; re-run inference with `--ckpt <the path finetune wrote>`.
