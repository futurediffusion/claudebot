#!/usr/bin/env python3
"""Inspect the shared self-model from the repo root."""

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

from core.automation_detection import detect_automation_route
from core.router import Router
from core.self_model_engine import SelfModelEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="Shared self-model CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary_parser = subparsers.add_parser("summary", help="Show self-model summary")
    summary_parser.add_argument("--agent", default="shared_cli", help="Agent identity")

    plan_parser = subparsers.add_parser("plan", help="Simulate a decision for a task")
    plan_parser.add_argument("task", nargs="+", help="Task description")
    plan_parser.add_argument("--agent", default="shared_cli", help="Agent identity")

    args = parser.parse_args()

    if args.command == "summary":
        engine = SelfModelEngine(agent_name=args.agent)
        print(json.dumps(engine.get_summary(), ensure_ascii=False, indent=2))
        return

    task = " ".join(args.task)
    engine = SelfModelEngine(agent_name=args.agent)
    route = detect_automation_route(task)
    if route:
        print(json.dumps(engine.plan_for_task(task), ensure_ascii=False, indent=2))
        return

    router = Router(agent_name=args.agent)
    model_type, task_type, reasoning = router.route(task)
    decision_meta = router.get_last_decision_meta()
    print(json.dumps({
        "task": task,
        "task_type": task_type.value,
        "selected_model": model_type.value,
        "reasoning": reasoning,
        "self_model": decision_meta.get("decision_simulation"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
