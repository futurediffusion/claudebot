#!/usr/bin/env python3
"""High-level single entrypoint for locked-agent CLI execution."""

from __future__ import annotations

import argparse
import subprocess
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

AGENT_CHOICES = ["gemini_cli", "claude_code", "codex_cli", "minimax_cli"]
TOOL_CHOICES = ["auto", "browser", "windows", "worker", "edit"]


def _task_type_for_tool(tool: str) -> str:
    return {
        "browser": "browser_automation",
        "windows": "windows_automation",
        "worker": "worker_automation",
        "edit": "file_edit",
        "auto": "agent_routing",
    }.get(tool, "agent_routing")


def _route_for_tool(tool: str) -> str | None:
    return {
        "browser": "browser",
        "windows": "windows",
        "worker": "worker",
        "auto": "worker",
        "edit": None,
    }.get(tool)


def _log_active_agent_cli(agent: str, tool: str, task: str) -> None:
    metadata = {
        "source": "run_agent.py",
        "active_agent_cli": agent,
        "selected_tool": tool,
        "decision_policy": "locked_agent",
    }
    task_type = _task_type_for_tool(tool)
    route = _route_for_tool(tool)

    WorldModelEngine(agent_name=agent).record_task_start(
        task=task,
        task_type=task_type,
        route=route,
        model_name=f"{agent}:entrypoint",
        metadata=metadata,
        refresh_desktop=False,
    )
    SelfModelEngine(agent_name=agent).record_execution(
        task=task,
        task_type=task_type,
        model_name=f"{agent}:entrypoint",
        success=True,
        execution_time_ms=0,
        tools_used=[tool],
        metadata=metadata,
    )
    EpisodicMemoryEngine(agent_name=agent).record_episode(
        task=task,
        task_type=task_type,
        success=True,
        execution_time_ms=0,
        episode_type="routing",
        model_name=f"{agent}:entrypoint",
        tools_used=[tool],
        steps=[
            {
                "stage": "entrypoint",
                "status": "completed",
                "detail": f"active_agent_cli={agent}, tool={tool}",
            }
        ],
        metadata=metadata,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one locked agent from a single high-level CLI")
    parser.add_argument("--agent", choices=AGENT_CHOICES, required=True)
    parser.add_argument("--tool", choices=TOOL_CHOICES, default="auto")
    parser.add_argument("task", help="Task description")
    args = parser.parse_args()

    _log_active_agent_cli(args.agent, args.tool, args.task)

    if args.agent == "gemini_cli":
        cmd = [sys.executable, str(ROOT / "gemini_bridge.py"), args.tool, args.task]
    else:
        task = args.task if args.tool == "auto" else f"[locked_tool:{args.tool}] {args.task}"
        cmd = [
            sys.executable,
            str(ROOT / "orchestrator" / "cli.py"),
            "--agent",
            args.agent,
            "--routing-mode",
            "locked_agent",
            task,
        ]

    completed = subprocess.run(cmd)
    sys.exit(completed.returncode)


if __name__ == "__main__":
    main()
