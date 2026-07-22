# Pocket handoff protocol — GNN run (Rishi, GPU) → MD validation (Advay)

Clean division of labor: **Rishi's GPU does the compute**, the pocket comes out of a **real run**,
and Advay builds the **tailored 4070 MD validation** for whatever that run identifies. This file is
the interface so nothing is guessed and nothing bypasses the project's own controls.

## Two preconditions (do these first — they're what make the result defensible)
1. **Leakage fix landed.** Run only from code on/after the merged `graph-leakage-fix`
   (BUG-020/021/022). A pocket found on a pre-fix / leaky checkpoint can't be defended under review.
2. **GATE 6 approval recorded.** Per `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`, PCNA
   inference is gated. Record the approval in `.memory/PROJECT_STATE.md` (approver + date + scope)
   *before* the run — a verbal OK is not a recorded approval. (Advay can draft this entry for the
   approver to confirm and commit.)

## Step 1 — Rishi runs, on the 4070
From the leakage-fixed worktree, on the GPU box:
```bash
# (retrain if the checkpoint isn't already the leakage-fixed one, then infer)
python scripts/run_v3_inference.py            # scores all PCNA structures, DBSCAN-clusters pockets
python scripts/check_prediction_overlap.py <top residues>   # honesty check vs known interfaces
```
This produces per-structure scores + clustered candidate pockets.

## Step 2 — Rishi fills the handoff file
For the candidate to validate, fill `pockets/pocket_handoff.schema.json` (one JSON object):
the clustered residues (model output, not hand-picked), the structure they're on, the checkpoint
+ commit + split-file provenance (with `leakage_fixed: true`), the overlap classification, and the
recorded GATE-6 approval ref. Send that JSON back to Advay.

## Step 3 — Advay builds the tailored 4070 MD validation
Advay converts the handoff JSON into `pockets/<name>.json` (a one-file drop — the harness is already
parameterized) and hands back the run package. Rishi (or the friend) runs:
```bash
./run_in_tmux.sh <name>          # control first, then apo, then analysis — detached, resumable
```
`analyze_md.py` writes `outputs/analysis/REPORT.md` with the per-replicate trajectory metrics and the
positive-control gate. **The gate reports whatever is true** — `Interpretable: True/False`,
opening/no-opening. It is not tuned to a desired answer; that's the point.

## What this protocol deliberately does NOT do
- It does not pre-declare the pocket, or that it "has the best dynamics." That is decided by the MD,
  after the run, honestly.
- It does not skip the leakage fix or the gate. Those are what make a positive result publishable.
