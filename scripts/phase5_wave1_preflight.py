#!/usr/bin/env python3
"""Generate or verify the official Phase 5 Wave 1 prelaunch package.

This script does not run MD, minimization, equilibration, production, ligand
parameterization, or trajectory analysis.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from phase5_md.wave1 import main


if __name__ == "__main__":
    raise SystemExit(main())
