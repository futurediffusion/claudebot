#!/usr/bin/env python3
"""Inspect the shared world model from the repo root."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ORCHESTRATOR_ROOT = ROOT / "orchestrator"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ORCHESTRATOR_ROOT) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR_ROOT))

from core.world_model import WorldModelEngine


def _matches_active_agent(entry: dict | None, active_agent_cli: str | None) -> bool:
    if not active_agent_cli:
        return True
    if not isinstance(entry, dict):
        return False
    return (entry.get("active_agent_cli") or "unknown") == active_agent_cli


def _filter_task_views(payload: dict, active_agent_cli: str | None) -> dict:
    if not active_agent_cli:
        return payload
    filtered = dict(payload)
    active_task = filtered.get("active_task")
    filtered["active_task"] = active_task if _matches_active_agent(active_task, active_agent_cli) else None
    if "recent_tasks" in filtered:
        filtered["recent_tasks"] = [
            item for item in filtered.get("recent_tasks", [])
            if _matches_active_agent(item, active_agent_cli)
        ]
    if "pending_objectives" in filtered:
        filtered["pending_objectives"] = [
            item for item in filtered.get("pending_objectives", [])
            if _matches_active_agent(item, active_agent_cli)
        ]
    return filtered


def main() -> None:
    parser = argparse.ArgumentParser(description="Shared world model CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary_parser = subparsers.add_parser("summary", help="Show world model summary")
    summary_parser.add_argument("--agent", default="shared_cli", help="Agent identity")
    summary_parser.add_argument("--refresh", action="store_true", help="Refresh desktop observation before reading")
    summary_parser.add_argument("--active-agent-cli", help="Filter task data by active agent CLI")

    observe_parser = subparsers.add_parser("observe", help="Refresh and print the full world state")
    observe_parser.add_argument("--agent", default="shared_cli", help="Agent identity")
    observe_parser.add_argument("--active-agent-cli", help="Filter task data by active agent CLI")

    focus_parser = subparsers.add_parser("focus", help="Show the task-relevant world-state slice")
    focus_parser.add_argument("task", nargs="+", help="Task description")
    focus_parser.add_argument("--task-type", help="Optional task type hint")
    focus_parser.add_argument("--agent", default="shared_cli", help="Agent identity")
    focus_parser.add_argument("--active-agent-cli", help="Filter task data by active agent CLI")

    args = parser.parse_args()
    engine = WorldModelEngine(agent_name=args.agent)

    if args.command == "summary":
        summary = engine.get_summary(refresh=args.refresh)
        print(json.dumps(_filter_task_views(summary, args.active_agent_cli), ensure_ascii=False, indent=2))
        return

    if args.command == "observe":
        observed = engine.observe_desktop()
        if "tasks" in observed:
            observed = dict(observed)
            observed["tasks"] = _filter_task_views(observed.get("tasks", {}), args.active_agent_cli)
        print(json.dumps(observed, ensure_ascii=False, indent=2))
        return

    task = " ".join(args.task)
    brief = engine.build_context_brief(task=task, task_type=args.task_type, refresh=True)
    print(
        json.dumps(
            _filter_task_views(brief, args.active_agent_cli),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
