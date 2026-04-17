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


def main() -> None:
    parser = argparse.ArgumentParser(description="Shared world model CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary_parser = subparsers.add_parser("summary", help="Show world model summary")
    summary_parser.add_argument("--agent", default="shared_cli", help="Agent identity")
    summary_parser.add_argument("--refresh", action="store_true", help="Refresh desktop observation before reading")

    observe_parser = subparsers.add_parser("observe", help="Refresh and print the full world state")
    observe_parser.add_argument("--agent", default="shared_cli", help="Agent identity")

    focus_parser = subparsers.add_parser("focus", help="Show the task-relevant world-state slice")
    focus_parser.add_argument("task", nargs="+", help="Task description")
    focus_parser.add_argument("--task-type", help="Optional task type hint")
    focus_parser.add_argument("--agent", default="shared_cli", help="Agent identity")

    args = parser.parse_args()
    engine = WorldModelEngine(agent_name=args.agent)

    if args.command == "summary":
        print(json.dumps(engine.get_summary(refresh=args.refresh), ensure_ascii=False, indent=2))
        return

    if args.command == "observe":
        print(json.dumps(engine.observe_desktop(), ensure_ascii=False, indent=2))
        return

    task = " ".join(args.task)
    print(
        json.dumps(
            engine.build_context_brief(task=task, task_type=args.task_type, refresh=True),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
