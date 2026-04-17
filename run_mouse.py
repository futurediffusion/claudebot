#!/usr/bin/env python3
"""Run calibrated mouse automation through the shared backend."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ORCHESTRATOR_ROOT = ROOT / "orchestrator"
if str(ORCHESTRATOR_ROOT) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR_ROOT))

from orchestrator.tools.mouse_calibration import main as mouse_main


if __name__ == "__main__":
    raise SystemExit(mouse_main(default_agent="shared_cli"))
