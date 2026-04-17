#!/usr/bin/env python3
"""Run a full worker-core task with browser/windows/files/data enabled."""

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
from orchestrator.tools.worker_core_bridge import WorkerOrchestratorTool


def main() -> None:
    parser = argparse.ArgumentParser(description="Run worker-core orchestration")
    parser.add_argument("task", nargs="+", help="Task description")
    parser.add_argument("--config", help="Optional path to tools/worker-core .env file")
    parser.add_argument("--agent", default="shared_cli", help="Agent identity for self-model tracking")
    args = parser.parse_args()

    tool = WorkerOrchestratorTool()
    task = " ".join(args.task)
    world_model = WorldModelEngine(agent_name=args.agent)
    world_model.record_task_start(
        task=task,
        task_type="worker_automation",
        route="worker",
        model_name="worker-core:orchestrator",
    )
    result = tool.execute(task, config_path=args.config)
    SelfModelEngine(agent_name=args.agent).record_execution(
        task=task,
        task_type="worker_automation",
        model_name="worker-core:orchestrator",
        success=result.get("success", False),
        execution_time_ms=0,
        error=result.get("error"),
        tools_used=["worker"],
        metadata={"source": "run_worker.py"},
    )
    EpisodicMemoryEngine(agent_name=args.agent).record_episode(
        task=task,
        task_type="worker_automation",
        success=result.get("success", False),
        execution_time_ms=0,
        episode_type="automation",
        model_name="worker-core:orchestrator",
        tools_used=["worker"],
        steps=[
            {
                "stage": "tool:worker",
                "status": "completed" if result.get("success") else "failed",
                "detail": str(result.get("content") or result.get("response") or result.get("error") or "")[:220],
            }
        ],
        response=result.get("content") or result.get("response") or result.get("stdout"),
        error=result.get("error"),
        tool_results={"worker": result},
        metadata={"source": "run_worker.py", "automation_route": "worker"},
    )
    world_model.record_execution(
        task=task,
        task_type="worker_automation",
        success=result.get("success", False),
        model_name="worker-core:orchestrator",
        route="worker",
        tools_used=["worker"],
        response=result.get("content") or result.get("response") or result.get("stdout"),
        error=result.get("error"),
        tool_results={"worker": result},
        playbook_path=result.get("playbook"),
        metadata={"source": "run_worker.py", "automation_route": "worker"},
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
