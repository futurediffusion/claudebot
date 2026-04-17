#!/usr/bin/env python3
"""Run a Windows desktop automation task through worker-core."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestrator.tools.worker_core_bridge import WindowsAutomationTool


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Windows automation via worker-core")
    parser.add_argument("task", nargs="+", help="Task description")
    parser.add_argument("--config", help="Optional path to tools/worker-core .env file")
    args = parser.parse_args()

    tool = WindowsAutomationTool()
    result = tool.execute(" ".join(args.task), config_path=args.config)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
