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

## Easiest path — current status
The old one-command `run_all_in_tmux.sh` path is disabled. It used to assemble
its own MD production commands and is no longer a supported launcher.

Run GNN handoff generation separately, then run MD only through the repository
root `./md.sh` launcher:

```bash
cd <repo-root>
./md.sh smoke
```

> **CHANGED 2026-08-11 (pre-MD audit).** `<checkpoint>` is now a REQUIRED argument, and this
> one-command path does **not** run the retrain — do step 3 first. Previously this path silently
> skipped step 3 and scored PCNA with the pre-virtual-node-fix checkpoint; the resulting candidate
> moved from chain A / 23 residues to chain B / 35 residues (Jaccard 0.000) purely on which
> checkpoint was loaded. `run_v3_inference.py` now refuses a checkpoint older than the fix commit.

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
#    --seed is now REQUIRED in practice: without it this script was unseeded, and two identical
#    invocations produced two different checkpoints AND two different candidate pockets
#    (chain B/35 residues vs chain A/4 residues). Run >=3 seeds and only trust a candidate that
#    is stable across them. A best.ckpt_meta.json sidecar now records seed/epoch/sha256.
python scripts/finetune_v3_fixed.py --seed 42 --out checkpoints/pcna_reproduced/best.ckpt
#    optional but recommended — refuse epochs with a high apo false-positive rate:
#    python scripts/finetune_v3_fixed.py --seed 42 --max_apo_fp 5 --out checkpoints/pcna_reproduced/best.ckpt

# 4. run the pocket search (inference + gate-enforced export)
#    The checkpoint is now an EXPLICIT argument, passed to BOTH inference and the provenance
#    record, so the model that produced the pocket and the model named in the handoff cannot
#    diverge. Inference hard-fails on a checkpoint older than the virtual-node fix (84c6aaa).
bash md_validation_4070/gnn_pocket_search/run_pocket_search.sh \
     "$PWD" 1W60 cand_A_2026-07 "$PWD/.memory/PROJECT_STATE.md" \
     "$PWD/checkpoints/pcna_reproduced/best.ckpt" 8GLA
#   args: <gnn-repo-path> <pdb-to-score> <pocket-name> <recorded-approval-file> <checkpoint> [holo-control-pdb]

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
