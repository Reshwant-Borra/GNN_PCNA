#!/usr/bin/env bash
# =============================================================================
# Launch the whole PCNA MD validation DETACHED in tmux.
#
# Why: a 3x100 ns run takes 1.5-2.5 days per structure. In tmux it keeps running
# after you close the SSH window / log out / your laptop sleeps, and you can
# reattach to watch it any time. If the box REBOOTS, just re-run this script -
# each replicate resumes from its last checkpoint (it never restarts from zero).
#
# Usage:
#   ./run_in_tmux.sh                 # pocket=aoh1996, 3 replicates, 100 ns
#   ./run_in_tmux.sh aoh1996 3 100   # pocket, replicates, ns
#
# Then:
#   tmux attach -t pcna-md           # watch live  (detach: Ctrl-b then d)
#   tail -f md_validation_4070/run_*.log   # or just tail the log from anywhere
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

SESSION="pcna-md"
POCKET="${1:-aoh1996}"
REPS="${2:-3}"
NS="${3:-100}"
ENV_NAME="pcna-md-4070"

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is not installed. Install it (Ubuntu/WSL: sudo apt install tmux) or run the"
  echo "commands in README_FRIEND.md directly. tmux just keeps the run alive when you log out."
  exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "A '$SESSION' session is already running - not starting a second one."
  echo "  Watch it:  tmux attach -t $SESSION"
  LATEST_LOG="$(ls -t run_*.log 2>/dev/null | head -1 || true)"
  [ -n "$LATEST_LOG" ] && echo "  Tail log:  tail -f $(pwd)/$LATEST_LOG"
  exit 0
fi

LOG="run_$(date +%Y%m%d_%H%M%S).log"

# Write the pipeline to a small runner script (avoids all inline-quoting pitfalls).
# Positive control (8GLA) runs FIRST; apo (1W60) only if it finished; analysis only if both did.
RUNNER=".pcna_pipeline.sh"
cat > "$RUNNER" <<EOF
#!/usr/bin/env bash
set -o pipefail
cd "\$(dirname "\$0")"
if command -v conda >/dev/null 2>&1; then
  source "\$(conda info --base)/etc/profile.d/conda.sh"
fi
conda activate ${ENV_NAME}
echo "=== [\$(date)] START pocket=${POCKET} reps=${REPS} ns=${NS} ==="
python run_md.py --pocket ${POCKET} --run control --replicates ${REPS} --ns ${NS} && \\
python run_md.py --pocket ${POCKET} --run apo     --replicates ${REPS} --ns ${NS} && \\
python analyze_md.py --pocket ${POCKET}
STATUS=\$?
echo "=== [\$(date)] PIPELINE EXIT \$STATUS - see outputs/analysis/REPORT.md ==="
EOF
chmod +x "$RUNNER"

# Run the runner inside tmux, teeing all output to $LOG so it is readable any time.
tmux new-session -d -s "$SESSION" "bash '$RUNNER' 2>&1 | tee '$LOG'"

echo "Started detached tmux session '${SESSION}'."
echo "  It resumes from checkpoints automatically if the machine reboots (just re-run this script)."
echo "  Watch live:   tmux attach -t ${SESSION}      (detach again with: Ctrl-b then d)"
echo "  Tail the log: tail -f $(pwd)/${LOG}"
echo "  Sessions:     tmux ls"
