#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cat >&2 <<'EOF'
run_in_tmux.sh is deprecated and no longer launches production directly.

Use the canonical gated launcher instead:
  ./md.sh smoke
  ./md.sh control5
  ./md.sh benchmark
  ./md.sh production
  ./md.sh analyze
  ./md.sh status
  ./md.sh attach
EOF

if [[ $# -eq 0 ]]; then
  exit 2
fi

exec "$ROOT/md.sh" "$@"
