#!/usr/bin/env python3
"""Run a browser automation task through worker-core."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ORCHESTRATOR_ROOT = ROOT / "orchestrator"
if str(ORCHESTRATOR_ROOT) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR_ROOT))

from core.self_model_engine import SelfModelEngine
from orchestrator.tools.worker_core_bridge import BrowserAutomationTool


def main() -> None:
    parser = argparse.ArgumentParser(description="Run browser automation via worker-core")
    parser.add_argument("task", nargs="+", help="Task description")
    parser.add_argument("--config", help="Optional path to tools/worker-core .env file")
    parser.add_argument("--agent", default="shared_cli", help="Agent identity for self-model tracking")
    args = parser.parse_args()

    tool = BrowserAutomationTool()
    result = tool.execute(" ".join(args.task), config_path=args.config)
    SelfModelEngine(agent_name=args.agent).record_execution(
        task=" ".join(args.task),
        task_type="browser_automation",
        model_name="worker-core:browser",
        success=result.get("success", False),
        execution_time_ms=0,
        error=result.get("error"),
        tools_used=["browser"],
        metadata={"source": "run_browser.py"},
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
