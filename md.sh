#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MD="$ROOT/md_validation_4070"
OUTDIR="$MD/outputs"
POCKET="${PCNA_MD_POCKET:-final_consensus_1w60_20260815}"
ENV_NAME="${PCNA_MD_CONDA_ENV:-pcna-md-4070}"

usage() {
  cat <<'EOF'
Usage:
  ./md.sh smoke       # 0.1 ns 8GLA control smoke in tmux
  ./md.sh control5    # 3 x 5 ns 8GLA control-first validation in tmux
  ./md.sh benchmark   # short real-system CUDA benchmark in tmux
  ./md.sh production  # gated 3 x 100 ns control + 3 x 100 ns apo/candidate
  ./md.sh analyze     # run frozen analyzer in tmux
  ./md.sh status      # summarize tmux sessions, runs, and gates
  ./md.sh attach      # attach latest pcna_* tmux session
EOF
}

q() {
  printf '%q' "$1"
}

cmd_join() {
  local out="" arg
  for arg in "$@"; do
    out+="$(q "$arg") "
  done
  printf '%s' "${out% }"
}

resolve_python() {
  if [[ -n "${PCNA_MD_PYTHON:-}" && -x "${PCNA_MD_PYTHON:-}" ]]; then
    printf '%s\n' "$PCNA_MD_PYTHON"; return
  fi
  if [[ -n "${CONDA_PREFIX:-}" && -x "$CONDA_PREFIX/bin/python" ]]; then
    printf '%s\n' "$CONDA_PREFIX/bin/python"; return
  fi
  if [[ -x "$ROOT/.venv_gnn_pcna/bin/python" ]]; then
    printf '%s\n' "$ROOT/.venv_gnn_pcna/bin/python"; return
  fi
  if command -v python >/dev/null 2>&1; then
    command -v python; return
  fi
  if command -v python3 >/dev/null 2>&1; then
    command -v python3; return
  fi
  echo "No Python found. Activate $ENV_NAME or set PCNA_MD_PYTHON=/path/to/python." >&2
  exit 1
}

PYTHON_BIN="$(resolve_python)"

require_deps() {
  "$PYTHON_BIN" - <<'PY'
import gemmi, mdtraj, openmm, pdbfixer  # noqa: F401
PY
}

require_cuda() {
  "$PYTHON_BIN" - <<'PY'
import openmm as mm
platforms = [mm.Platform.getPlatform(i).getName() for i in range(mm.Platform.getNumPlatforms())]
if "CUDA" not in platforms:
    raise SystemExit(f"OpenMM CUDA platform unavailable; available platforms={platforms}")
PY
}

require_tmux() {
  if ! command -v tmux >/dev/null 2>&1; then
    cat >&2 <<'EOF'
tmux is not installed. Refusing to run MD outside tmux.

Install tmux, then re-run the same command:
  Ubuntu/Debian: sudo apt-get update && sudo apt-get install -y tmux
  macOS:         brew install tmux
EOF
    exit 1
  fi
}

launch_tmux() {
  local session="$1"; shift
  local stage="$1"; shift
  local command_str="$1"; shift
  local next_action="$1"; shift

  require_tmux
  if tmux has-session -t "$session" 2>/dev/null; then
    echo "A tmux session named '$session' already exists; refusing duplicate launch."
    echo "Attach: ./md.sh attach $session"
    exit 1
  fi

  local log_dir="$MD/logs"
  mkdir -p "$log_dir"
  local stamp
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  local log="$log_dir/${stage}_${stamp}.log"
  local command_file="$log_dir/${stage}_${stamp}.command.txt"
  local runner="$log_dir/${stage}_${stamp}.runner.sh"

  printf '%s\n' "$command_str" > "$command_file"
cat > "$runner" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd $(q "$ROOT")
echo "=== [\$(date -u +%Y-%m-%dT%H:%M:%SZ)] START stage=$stage session=$session ==="
echo "command: $command_str"
$command_str
status=\$?
echo "=== [\$(date -u +%Y-%m-%dT%H:%M:%SZ)] EXIT \$status stage=$stage ==="
exit \$status
EOF
  chmod +x "$runner"

  local tmux_inner="cd $(q "$ROOT"); set -o pipefail; bash $(q "$runner") 2>&1 | tee -a $(q "$log")"
  tmux new-session -d -s "$session" "bash -lc $(q "$tmux_inner")"

  echo "Started tmux session: $session"
  echo "Log: $log"
  echo "Command: $command_file"
  echo "Detach from tmux: Ctrl-b then d"
  echo "Reattach: ./md.sh attach $session"
  echo "$next_action"
}

attach_session() {
  require_tmux
  local session="${1:-}"
  if [[ -z "$session" ]]; then
    session="$(tmux list-sessions -F '#{session_created} #{session_name}' 2>/dev/null \
      | awk '$2 ~ /^pcna_/ {print}' | sort -nr | head -1 | awk '{print $2}')"
  fi
  if [[ -z "$session" ]]; then
    echo "No pcna_* tmux session found."
    exit 1
  fi
  exec tmux attach -t "$session"
}

run_smoke() {
  require_tmux
  require_deps
  require_cuda
  local cmd
  cmd="$(cmd_join "$PYTHON_BIN" "$MD/run_md.py" --pocket "$POCKET" --run control \
      --replicates 1 --ns 0.1 --outdir "$OUTDIR" --platform CUDA --require-platform \
      --md-stage smoke) && "
  cmd+="$(cmd_join "$PYTHON_BIN" "$MD/analyze_md.py" --pocket "$POCKET" --outdir "$OUTDIR")"
  launch_tmux "pcna_smoke" "smoke" "$cmd" "Next after completion: ./md.sh status, then ./md.sh control5"
}

run_control5() {
  require_tmux
  require_deps
  require_cuda
  local cmd
  cmd="$(cmd_join "$PYTHON_BIN" "$MD/run_md.py" --pocket "$POCKET" --run control \
      --replicates 3 --ns 5 --outdir "$OUTDIR" --platform CUDA --require-platform \
      --md-stage control_validation) && "
  cmd+="$(cmd_join "$PYTHON_BIN" "$MD/analyze_md.py" --pocket "$POCKET" --outdir "$OUTDIR") && "
  cmd+="$(cmd_join "$PYTHON_BIN" "$MD/md_workflow.py" control-report --outdir "$OUTDIR")"
  launch_tmux "pcna_control5" "control5" "$cmd" \
    "Next after PASS: Gate-6 human review. Production remains blocked until approval is recorded."
}

run_benchmark() {
  require_tmux
  require_deps
  require_cuda
  local bench_out="$MD/benchmark_outputs"
  local bench_ns="${PCNA_MD_BENCHMARK_NS:-0.02}"
  local cmd
  cmd="$(cmd_join "$PYTHON_BIN" "$MD/run_md.py" --pocket "$POCKET" --run control \
      --replicates 1 --ns "$bench_ns" --equil-ns 0 --min-steps 0 \
      --outdir "$bench_out" --platform CUDA --require-platform --md-stage benchmark) && "
  cmd+="$(cmd_join "$PYTHON_BIN" "$MD/md_workflow.py" benchmark-report --outdir "$bench_out")"
  launch_tmux "pcna_benchmark" "benchmark" "$cmd" "Next after completion: ./md.sh status"
}

run_analyze() {
  require_tmux
  require_deps
  local cmd
  cmd="$(cmd_join "$PYTHON_BIN" "$MD/analyze_md.py" --pocket "$POCKET" --outdir "$OUTDIR")"
  launch_tmux "pcna_analyze" "analyze" "$cmd" "Next after completion: ./md.sh status"
}

run_production() {
  "$PYTHON_BIN" "$MD/md_workflow.py" production-gate --outdir "$OUTDIR" \
    --authorize-run --pocket "$POCKET" --replicates 3 --ns 100
  require_deps
  local auth="$OUTDIR/.production_authorization.json"
  local cmd
  cmd="$(cmd_join "$PYTHON_BIN" "$MD/run_md.py" --pocket "$POCKET" --run control \
      --replicates 3 --ns 100 --outdir "$OUTDIR" --platform CUDA --require-platform \
      --md-stage production --production-authorization "$auth") && "
  cmd+="$(cmd_join "$PYTHON_BIN" "$MD/run_md.py" --pocket "$POCKET" --run apo \
      --replicates 3 --ns 100 --outdir "$OUTDIR" --platform CUDA --require-platform \
      --md-stage production --production-authorization "$auth") && "
  cmd+="$(cmd_join "$PYTHON_BIN" "$MD/analyze_md.py" --pocket "$POCKET" --outdir "$OUTDIR")"
  launch_tmux "pcna_production" "production" "$cmd" "Next after completion: ./md.sh analyze"
}

case "${1:-}" in
  smoke) run_smoke ;;
  control5) run_control5 ;;
  benchmark) run_benchmark ;;
  production) run_production ;;
  analyze) run_analyze ;;
  status) "$PYTHON_BIN" "$MD/md_workflow.py" status --outdir "$OUTDIR" ;;
  attach) shift || true; attach_session "${1:-}" ;;
  ""|-h|--help|help) usage ;;
  *) usage; exit 2 ;;
esac
