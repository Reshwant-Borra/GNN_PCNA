#!/usr/bin/env python3
"""Launch the ResearchOS monitoring dashboard.

Usage:
    python dashboard/start.py
    python dashboard/start.py --port 7765
    python dashboard/start.py --repo-root /path/to/repo --port 8080
    python -m dashboard.start   (from repo root)
"""
import argparse
import sys
from pathlib import Path

# Ensure the repo root (parent of this file's directory) is on sys.path so
# that `import dashboard.server` and `import research_os` both work regardless
# of how this script is invoked.
_repo_root_guess = Path(__file__).resolve().parent.parent
if str(_repo_root_guess) not in sys.path:
    sys.path.insert(0, str(_repo_root_guess))


def main() -> None:
    parser = argparse.ArgumentParser(description="ResearchOS Dashboard")
    parser.add_argument("--port", type=int, default=7765, help="Port to listen on (default: 7765)")
    parser.add_argument("--repo-root", default=".", help="ResearchOS repository root (default: cwd)")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if not (repo_root / "research_os").exists():
        print(f"[warn] {repo_root} does not look like a ResearchOS repo (no research_os/ dir)", file=sys.stderr)

    # Patch REPO_ROOT before uvicorn imports the app module.
    import dashboard.server as srv
    srv.REPO_ROOT = repo_root

    url = f"http://{args.host}:{args.port}"
    print(f"\nResearchOS Dashboard")
    print(f"  URL  : {url}")
    print(f"  Root : {repo_root}")
    print(f"  Events: {repo_root / 'data' / 'dashboard_events.ndjson'}")
    print()

    try:
        import uvicorn
    except ImportError:
        print("uvicorn is required.  Install with:  pip install uvicorn", file=sys.stderr)
        sys.exit(1)

    uvicorn.run(
        "dashboard.server:app",
        host=args.host,
        port=args.port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
