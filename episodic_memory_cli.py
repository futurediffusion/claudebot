#!/usr/bin/env python3
"""Inspect shared episodic memory from the repo root."""

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

from core.episodic_memory import EpisodicMemoryEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="Shared episodic memory CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary_parser = subparsers.add_parser("summary", help="Show episodic memory summary")
    summary_parser.add_argument("--agent", default="shared_cli", help="Agent identity")

    find_parser = subparsers.add_parser("find", help="Find similar past episodes")
    find_parser.add_argument("task", nargs="+", help="Task description")
    find_parser.add_argument("--task-type", help="Optional task type hint")
    find_parser.add_argument("--limit", type=int, default=3, help="Maximum episodes to return")
    find_parser.add_argument("--agent", default="shared_cli", help="Agent identity")

    args = parser.parse_args()
    engine = EpisodicMemoryEngine(agent_name=args.agent)

    if args.command == "summary":
        print(json.dumps(engine.get_summary(), ensure_ascii=False, indent=2))
        return

    task = " ".join(args.task)
    print(
        json.dumps(
            engine.build_context_brief(task=task, task_type=args.task_type, limit=args.limit),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
