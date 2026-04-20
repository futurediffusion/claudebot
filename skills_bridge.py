#!/usr/bin/env python3
"""CLI for the shared local skill bridge."""

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

from core.skill_bridge import SkillBridge


def main() -> None:
    parser = argparse.ArgumentParser(description="Shared skill bridge CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List discoverable skills")
    list_parser.add_argument("query", nargs="?", help="Optional search query")
    list_parser.add_argument("--provider", help="Restrict to a single provider")
    list_parser.add_argument("--limit", type=int, default=20)
    list_parser.add_argument("--executable-only", action="store_true")

    show_parser = subparsers.add_parser("show", help="Show skill metadata")
    show_parser.add_argument("skill_id")
    show_parser.add_argument("--content", action="store_true", help="Include skill content/help")
    show_parser.add_argument("--max-chars", type=int, default=6000)

    suggest_parser = subparsers.add_parser("suggest", help="Suggest skills for a task")
    suggest_parser.add_argument("task")
    suggest_parser.add_argument("--limit", type=int, default=6)

    run_parser = subparsers.add_parser("run", help="Execute an executable skill")
    run_parser.add_argument("skill_id")
    run_parser.add_argument("--timeout-ms", type=int, default=30000)
    run_parser.add_argument("skill_args", nargs=argparse.REMAINDER)

    args = parser.parse_args()
    bridge = SkillBridge()

    if args.command == "list":
        payload = bridge.list_skills(
            query=args.query,
            provider=args.provider,
            executable_only=args.executable_only,
            limit=args.limit,
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if args.command == "show":
        payload = bridge.get_skill(
            args.skill_id,
            include_content=args.content,
            max_chars=args.max_chars,
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if args.command == "suggest":
        payload = bridge.build_context_brief(args.task, limit=args.limit)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if args.command == "run":
        skill_args = list(args.skill_args)
        if skill_args[:1] == ["--"]:
            skill_args = skill_args[1:]
        payload = bridge.execute(args.skill_id, skill_args=skill_args, timeout_ms=args.timeout_ms)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        raise SystemExit(0 if payload.get("success") else payload.get("returncode") or 1)


if __name__ == "__main__":
    main()
