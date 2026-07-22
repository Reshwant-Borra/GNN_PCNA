# GNN pocket search → MD handoff (setup for Rishi's GPU box)

This is the wiring for the compute division of labor: **Rishi runs the GNN on his GPU**, it emits
a `*_handoff.json`, **Advay** turns that into the tailored 4070 MD validation. It does not run any
gated action by itself and does not pre-pick a pocket.

## Files
- `run_pocket_search.sh` — orchestration Rishi runs: preconditions → inference → export.
- `export_handoff.py` — reads the model's `results/v3/<pdb>/scores.csv`, takes the clustered
  pocket (model output, not hand-picked), records provenance (checkpoint sha256, git commit, split
  file, leakage-fix status), runs the AOH-overlap honesty check, and writes `<name>_handoff.json`
  matching `../pockets/pocket_handoff.schema.json`.

## Gate enforcement (why this is safe to run)
`export_handoff.py` **refuses to emit a handoff** unless `--approval-file` points at a file that
actually contains a recorded `GATE 6 … approved_by …` entry — and it **rejects** governance-override
/ prompt-injection text ("override all governance", "supersede", "give this to your repo") outright.
So the tool cannot be used to launder a verbal OK or a chat message into a result.

## Preconditions (both required for a defensible result)
1. Run from a repo where the **graph-leakage-fix** (BUG-020/021/022) is merged.
2. A **recorded GATE-6 approval** exists (specific scope, approver, date) in `.memory/PROJECT_STATE.md`.
   See `../POCKET_HANDOFF_PROTOCOL.md` for the template. A verbal/chat approval does not count.

## Run
```bash
# on Rishi's box, after `conda activate <env>` from the leakage-fixed branch:
./run_pocket_search.sh ~/gnn_xl_worktree 1W60 cand_A_2026-07 ~/gnn_xl_worktree/.memory/PROJECT_STATE.md 8GLA
# -> produces cand_A_2026-07_handoff.json; send it to Advay.
```
Smoke-tested against real `results/v3/1W60/scores.csv`: correctly refuses injection/missing-approval
inputs, and on a valid approval emits the 24-residue AOH cluster classified `overlaps_known_interface`.
