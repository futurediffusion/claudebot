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

from core.episodic_memory import EpisodicMemoryEngine
from core.self_model_engine import SelfModelEngine
from core.world_model import WorldModelEngine
from orchestrator.tools.worker_core_bridge import BrowserAutomationTool


def main() -> None:
    parser = argparse.ArgumentParser(description="Run browser automation via worker-core")
    parser.add_argument("task", nargs="+", help="Task description")
    parser.add_argument("--config", help="Optional path to tools/worker-core .env file")
    parser.add_argument("--agent", default="shared_cli", help="Agent identity for self-model tracking")
    args = parser.parse_args()

    tool = BrowserAutomationTool()
    task = " ".join(args.task)
    world_model = WorldModelEngine(agent_name=args.agent)
    world_model.record_task_start(
        task=task,
        task_type="browser_automation",
        route="browser",
        model_name="worker-core:browser",
    )
    result = tool.execute(task, config_path=args.config)
    SelfModelEngine(agent_name=args.agent).record_execution(
        task=task,
        task_type="browser_automation",
        model_name="worker-core:browser",
        success=result.get("success", False),
        execution_time_ms=0,
        error=result.get("error"),
        tools_used=["browser"],
        metadata={"source": "run_browser.py"},
    )
    EpisodicMemoryEngine(agent_name=args.agent).record_episode(
        task=task,
        task_type="browser_automation",
        success=result.get("success", False),
        execution_time_ms=0,
        episode_type="automation",
        model_name="worker-core:browser",
        tools_used=["browser"],
        steps=[
            {
                "stage": "tool:browser",
                "status": "completed" if result.get("success") else "failed",
                "detail": str(result.get("content") or result.get("response") or result.get("error") or "")[:220],
            }
        ],
        response=result.get("content") or result.get("response") or result.get("stdout"),
        error=result.get("error"),
        tool_results={"browser": result},
        metadata={"source": "run_browser.py", "automation_route": "browser"},
    )
    world_model.record_execution(
        task=task,
        task_type="browser_automation",
        success=result.get("success", False),
        model_name="worker-core:browser",
        route="browser",
        tools_used=["browser"],
        response=result.get("content") or result.get("response") or result.get("stdout"),
        error=result.get("error"),
        tool_results={"browser": result},
        metadata={"source": "run_browser.py", "automation_route": "browser"},
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
