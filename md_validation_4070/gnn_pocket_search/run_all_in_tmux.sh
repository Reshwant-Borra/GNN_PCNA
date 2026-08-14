#!/usr/bin/env bash
# =============================================================================
# FULL pipeline, detached in tmux: GNN pocket search  ->  handoff  ->  MD validation.
# One command; survives SSH drops / reboots; MD stage resumes from checkpoints.
#
# Stage 1 (GNN env): run_pocket_search.sh  -> <name>_handoff.json  (GATE-6 enforced)
# Stage 2:           handoff_to_pocket.py  -> ../pockets/<name>.json
# Stage 3 (MD env):  run_md.py control -> run_md.py apo -> analyze_md.py
#
# Usage:
#   ./run_all_in_tmux.sh <gnn-worktree> <pdb> <pocket-name> <approval-file> <gnn-env> \
#                        <checkpoint> [control-pdb] [md-env]
# e.g.
#   ./run_all_in_tmux.sh ~/gnn_xl_worktree 1W60 cand_A_2026-07 \
#       ~/gnn_xl_worktree/.memory/PROJECT_STATE.md gnnenv \
#       ~/gnn_xl_worktree/checkpoints/pcna_reproduced/best.ckpt 8GLA
#
# NOTE: <checkpoint> is REQUIRED and must be the file runbook step 3 wrote. This path does
# NOT run the retrain for you -- run step 3 first. run_v3_inference.py refuses a checkpoint
# older than the virtual-node fix (84c6aaa), so a skipped retrain now fails loudly instead
# of silently producing a pocket from a pre-fix model.
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"
GPS="$(pwd)"                 # gnn_pocket_search/
MDPKG="$(dirname "$GPS")"    # md_validation_4070/

WORKTREE="${1:?usage: run_all_in_tmux.sh <worktree> <pdb> <name> <approval-file> <gnn-env> <checkpoint> [control-pdb] [md-env]}"
PDB="${2:?need pdb}"; NAME="${3:?need pocket name}"; APPROVAL="${4:?need recorded GATE-6 approval file}"
GNN_ENV="${5:?need the conda env name for the GNN (torch_geometric+esm)}"
CKPT="${6:?need the checkpoint path finetune_v3_fixed.py --out wrote (runbook step 3)}"
CONTROL="${7:-}"; MD_ENV="${8:-pcna-md-4070}"
[ -f "$CKPT" ] || { echo "checkpoint not found: $CKPT (run runbook step 3 first)"; exit 1; }
SESSION="pcna-full"

command -v tmux >/dev/null 2>&1 || { echo "install tmux first (sudo apt install tmux)"; exit 1; }
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "'$SESSION' already running. Watch: tmux attach -t $SESSION"; exit 0
fi
[ -d "$WORKTREE" ] || { echo "worktree not found: $WORKTREE"; exit 1; }
LOG="$GPS/full_$(date +%Y%m%d_%H%M%S).log"

RUNNER="$GPS/.full_pipeline.sh"
cat > "$RUNNER" <<EOF
#!/usr/bin/env bash
set -o pipefail
if command -v conda >/dev/null 2>&1; then source "\$(conda info --base)/etc/profile.d/conda.sh"; fi

echo "=== [\$(date)] STAGE 1/3 — GNN pocket search (gate-enforced) ==="
conda activate "${GNN_ENV}"
bash "${GPS}/run_pocket_search.sh" "${WORKTREE}" "${PDB}" "${NAME}" "${APPROVAL}" "${CKPT}" ${CONTROL:+"${CONTROL}"} \
  || { echo "[stop] pocket search stage failed (exit \$?). Causes, in order of likelihood:"; \
       echo "       - stale checkpoint (predates the virtual-node fix) -> rerun runbook step 3"; \
       echo "       - missing/invalid recorded GATE-6 approval in ${APPROVAL}"; \
       echo "       - a code error in run_v3_inference.py -> read the traceback above"; \
       echo "       Nothing else runs."; exit 1; }

echo "=== [\$(date)] STAGE 2/3 — handoff -> MD pocket definition ==="
python "${GPS}/handoff_to_pocket.py" --handoff "${GPS}/${NAME}_handoff.json" --out "${MDPKG}/pockets/${NAME}.json" || exit 1

echo "=== [\$(date)] STAGE 3/3 — MD validation (control -> apo -> analyze) ==="
conda activate "${MD_ENV}"
cd "${MDPKG}"
if [ -n "${CONTROL}" ]; then
  python run_md.py --pocket "${NAME}" --run control --replicates 3 --ns 100 || exit 1
else
  echo "[note] no control structure -> the positive-control gate will report 'inconclusive', not a negative."
fi
python run_md.py --pocket "${NAME}" --run apo --replicates 3 --ns 100 || exit 1
python analyze_md.py --pocket "${NAME}"
echo "=== [\$(date)] ALL DONE — GNN candidate + MD report at ${MDPKG}/outputs/analysis/REPORT.md ==="
EOF
chmod +x "$RUNNER"

tmux new-session -d -s "$SESSION" "bash '$RUNNER' 2>&1 | tee '$LOG'"
echo "Started detached tmux session '$SESSION' (GNN pocket search -> MD validation)."
echo "  It resumes the MD stage from checkpoints if the box reboots (re-run this script)."
echo "  Watch live:   tmux attach -t $SESSION        (detach: Ctrl-b then d)"
echo "  Tail the log: tail -f $LOG"
