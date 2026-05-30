#!/usr/bin/env bash
# One-shot RunPod workflow for budget-constrained Phase 5 1AXC MD.
#
# Runs:
#   GPU/OpenMM checks -> smoke test -> smoke analysis -> production -> production analysis
#   -> output packaging.
#
# This script intentionally does not install or upgrade OpenMM. Use the already-created
# `phase5-md` conda environment.

set -Eeuo pipefail

if git rev-parse --show-toplevel >/dev/null 2>&1; then
  REPO_ROOT="$(git rev-parse --show-toplevel)"
else
  REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi
cd "$REPO_ROOT"

RUN_ROOT="${RUN_ROOT:-outputs/phase5_md/time_crunch_1axc_25ns}"
LOG_ROOT="${LOG_ROOT:-outputs/phase5_md/logs}"
PACKAGE_ROOT="${PACKAGE_ROOT:-outputs/phase5_md/packages}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${LOG_ROOT}/one_shot_${TIMESTAMP}.log"

HOURLY_COST_USD="${HOURLY_COST_USD:-6}"
TOTAL_TARGET_COST_USD="${TOTAL_TARGET_COST_USD:-27}"
TOTAL_HARD_COST_USD="${TOTAL_HARD_COST_USD:-30}"
PRODUCTION_NS="${PRODUCTION_NS:-25}"
REPLICATES="${REPLICATES:-3}"
MAX_PRODUCTION_WALL_HOURS="${MAX_PRODUCTION_WALL_HOURS:-4.0}"

mkdir -p "$LOG_ROOT" "$PACKAGE_ROOT"
exec > >(tee -a "$LOG_FILE") 2>&1

START_EPOCH="$(date +%s)"
FINAL_STATUS=0

elapsed_hours() {
  python - "$START_EPOCH" <<'PY'
import sys, time
start = float(sys.argv[1])
print((time.time() - start) / 3600.0)
PY
}

projected_spend() {
  python - "$START_EPOCH" "$HOURLY_COST_USD" <<'PY'
import sys, time
start = float(sys.argv[1])
hourly = float(sys.argv[2])
print((time.time() - start) / 3600.0 * hourly)
PY
}

remaining_budget_value() {
  python - "$START_EPOCH" "$HOURLY_COST_USD" "$1" <<'PY'
import sys, time
start = float(sys.argv[1])
hourly = float(sys.argv[2])
limit = float(sys.argv[3])
spent = (time.time() - start) / 3600.0 * hourly
print(max(0.5, limit - spent))
PY
}

package_outputs() {
  local status="$1"
  set +e
  mkdir -p "$PACKAGE_ROOT"
  local package_path="${PACKAGE_ROOT}/phase5_time_crunch_1axc_25ns_${TIMESTAMP}_status${status}.tgz"
  local items=()
  [[ -d "$RUN_ROOT" ]] && items+=("time_crunch_1axc_25ns")
  [[ -d "$LOG_ROOT" ]] && items+=("logs")
  if [[ "${#items[@]}" -gt 0 ]]; then
    echo "=== PACKAGING OUTPUTS ==="
    tar -czf "$package_path" -C outputs/phase5_md "${items[@]}"
    echo "Package: $package_path"
    ls -lh "$package_path"
  else
    echo "No outputs/logs found to package."
  fi
  echo "=== END $(date) status=${status} projected_spend_usd=$(projected_spend) ==="
}

on_exit() {
  local status="$?"
  package_outputs "$status"
  exit "$status"
}
trap on_exit EXIT

run_step() {
  local title="$1"
  shift
  echo
  echo "=== ${title} $(date) ==="
  "$@"
}

activate_conda_env() {
  if [[ -n "${CONDA_PREFIX:-}" && "$(basename "$CONDA_PREFIX")" == "phase5-md" ]]; then
    echo "Conda environment already active: $CONDA_PREFIX"
    return
  fi

  local candidates=(
    "${CONDA_SH:-}"
    "$HOME/miniforge3/etc/profile.d/conda.sh"
    "$HOME/miniconda3/etc/profile.d/conda.sh"
    "$HOME/anaconda3/etc/profile.d/conda.sh"
    "/opt/conda/etc/profile.d/conda.sh"
  )
  for conda_sh in "${candidates[@]}"; do
    if [[ -n "$conda_sh" && -f "$conda_sh" ]]; then
      # shellcheck disable=SC1090
      source "$conda_sh"
      conda activate phase5-md
      echo "Activated conda environment: $CONDA_PREFIX"
      return
    fi
  done

  echo "ERROR: Could not find conda.sh. Set CONDA_SH=/path/to/conda.sh and rerun." >&2
  exit 2
}

echo "=== START $(date) ==="
echo "Repo root: $REPO_ROOT"
echo "Run root: $RUN_ROOT"
echo "Log file: $LOG_FILE"
echo "Budget: target=$TOTAL_TARGET_COST_USD hard=$TOTAL_HARD_COST_USD hourly=$HOURLY_COST_USD"
echo "Production: replicates=$REPLICATES production_ns=$PRODUCTION_NS"

activate_conda_env

run_step "GIT STATE" git status -sb
run_step "GPU CHECK" nvidia-smi
run_step "OPENMM CHECK" python -m openmm.testInstallation

run_step "SMOKE TEST" python scripts/phase5_run_1axc_openmm.py \
  --output-root "$RUN_ROOT" \
  --smoke-test \
  --max-wall-hours 0.5 \
  --hourly-cost-usd "$HOURLY_COST_USD" \
  --target-cost-usd 3 \
  --hard-cost-usd 5

run_step "SMOKE ANALYSIS" python scripts/phase5_analyze_1axc_md.py \
  --run-root "${RUN_ROOT}/smoke_test"

PROD_TARGET="$(remaining_budget_value "$TOTAL_TARGET_COST_USD")"
PROD_HARD="$(remaining_budget_value "$TOTAL_HARD_COST_USD")"
echo
echo "=== PRODUCTION BUDGET AFTER SMOKE ==="
echo "elapsed_hours=$(elapsed_hours)"
echo "projected_spend_usd=$(projected_spend)"
echo "production_target_cost_usd=${PROD_TARGET}"
echo "production_hard_cost_usd=${PROD_HARD}"

echo
echo "=== PRODUCTION RUN $(date) ==="
set +e
python scripts/phase5_run_1axc_openmm.py \
  --output-root "$RUN_ROOT" \
  --replicates "$REPLICATES" \
  --production-ns "$PRODUCTION_NS" \
  --seeds 2026052901 2026052902 2026052903 \
  --windows 239-243 28-32 206-210 134-138 \
  --reference-window 118-122 \
  --max-wall-hours "$MAX_PRODUCTION_WALL_HOURS" \
  --hourly-cost-usd "$HOURLY_COST_USD" \
  --target-cost-usd "$PROD_TARGET" \
  --hard-cost-usd "$PROD_HARD"
PRODUCTION_STATUS="$?"
set -e
echo "Production exit status: $PRODUCTION_STATUS"

if ls "$RUN_ROOT"/replicate_*/trajectory.dcd >/dev/null 2>&1; then
  echo
  echo "=== PRODUCTION ANALYSIS $(date) ==="
  set +e
  python scripts/phase5_analyze_1axc_md.py \
    --run-root "$RUN_ROOT" \
    --windows 239-243 28-32 206-210 134-138 \
    --reference-window 118-122
  ANALYSIS_STATUS="$?"
  set -e
  echo "Production analysis exit status: $ANALYSIS_STATUS"
else
  echo "No production trajectories found; skipping production analysis."
  ANALYSIS_STATUS=0
fi

echo
echo "=== OUTPUT SUMMARY ==="
find "$RUN_ROOT" -maxdepth 3 -type f | sort || true
du -sh "$RUN_ROOT" "$LOG_ROOT" 2>/dev/null || true

if [[ "$PRODUCTION_STATUS" -ne 0 ]]; then
  echo "Production did not complete cleanly; outputs will still be packaged for inspection."
  FINAL_STATUS="$PRODUCTION_STATUS"
  exit "$FINAL_STATUS"
fi

if [[ "$ANALYSIS_STATUS" -ne 0 ]]; then
  echo "Production analysis failed; outputs will still be packaged for inspection."
  FINAL_STATUS="$ANALYSIS_STATUS"
  exit "$FINAL_STATUS"
fi

echo "One-shot workflow completed successfully."
