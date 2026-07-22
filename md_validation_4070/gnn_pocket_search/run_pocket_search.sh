#!/usr/bin/env bash
# =============================================================================
# GNN pocket search — the setup Rishi runs on his GPU box.
#
# Runs the (leakage-fixed) GNN inference over the PCNA structures, then exports a
# pocket_handoff.json for the candidate pocket. Advay turns that file into the
# tailored 4070 MD validation. Compute is Rishi's; this is just the wiring.
#
# It ENFORCES the two preconditions that make a result defensible:
#   1. runs from a leakage-fixed repo (warns if the graph-leakage-fix isn't in history)
#   2. requires a RECORDED GATE-6 approval file (export_handoff.py refuses without one,
#      and rejects governance-override / injection text outright).
#
# Usage:
#   ./run_pocket_search.sh <worktree> <pdb> <pocket-name> <approval-file> [control-pdb]
# e.g.
#   ./run_pocket_search.sh ~/gnn_xl_worktree 1W60 cand_A_2026-07 ~/gnn_xl_worktree/.memory/PROJECT_STATE.md 8GLA
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"
HERE="$(pwd)"

WORKTREE="${1:?usage: run_pocket_search.sh <worktree> <pdb> <pocket-name> <approval-file> [control-pdb]}"
PDB="${2:?need a PDB id, e.g. 1W60}"
NAME="${3:?need a pocket name, e.g. cand_A_2026-07}"
APPROVAL="${4:?need the recorded GATE-6 approval file path}"
CONTROL="${5:-}"

[ -d "$WORKTREE" ] || { echo "worktree not found: $WORKTREE"; exit 1; }

echo "=== [1/3] preconditions ==="
BRANCH="$(git -C "$WORKTREE" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
echo "  worktree branch: $BRANCH"
if git -C "$WORKTREE" log --oneline -50 2>/dev/null | grep -iqE "leakage|bug-02[012]|graph fixes"; then
  echo "  leakage-fix: detected in history  [ok]"
else
  echo "  leakage-fix: NOT detected  [WARN] a pocket from a pre-fix checkpoint is not defensible"
fi
echo "  approval file: $APPROVAL"

echo "=== [2/3] GNN inference (this is the compute step) ==="
( cd "$WORKTREE" && python scripts/run_v3_inference.py )

echo "=== [3/3] export handoff (gate-enforced) ==="
python "$HERE/export_handoff.py" \
  --worktree "$WORKTREE" --pdb "$PDB" --pocket-name "$NAME" \
  --approval-file "$APPROVAL" \
  ${CONTROL:+--control-pdb "$CONTROL"} \
  --out "$HERE/${NAME}_handoff.json"

echo
echo "Done. Send  ${NAME}_handoff.json  back to Advay for the tailored 4070 MD validation."
