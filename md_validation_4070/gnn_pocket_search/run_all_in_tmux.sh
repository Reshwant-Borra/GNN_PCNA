#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cat >&2 <<'EOF'
run_all_in_tmux.sh is HISTORICAL_DISABLED.

This legacy script used to assemble its own 3 x 100 ns MD commands.
That production bypass has been removed. It no longer launches GNN inference,
MD production, or analysis.

Supported MD entry points are:
  ./md.sh smoke
  ./md.sh control5
  ./md.sh benchmark
  ./md.sh analyze
  ./md.sh status

The only supported production entry point is:
  ./md.sh production

Run from the repository root:
EOF
printf '  cd %q\n' "$ROOT" >&2
cat >&2 <<'EOF'
  ./md.sh smoke
EOF

exit 2
