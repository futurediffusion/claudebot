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


def _episode_matches_active_agent(episode: dict, active_agent_cli: str | None) -> bool:
    if not active_agent_cli:
        return True
    return (episode.get("active_agent_cli") or "unknown") == active_agent_cli


def _filter_brief(payload: dict, active_agent_cli: str | None) -> dict:
    if not active_agent_cli:
        return payload
    filtered = dict(payload)
    matches = filtered.get("matches", [])
    filtered["matches"] = [item for item in matches if _episode_matches_active_agent(item, active_agent_cli)]
    filtered["match_count"] = len(filtered["matches"])
    return filtered


def main() -> None:
    parser = argparse.ArgumentParser(description="Shared episodic memory CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary_parser = subparsers.add_parser("summary", help="Show episodic memory summary")
    summary_parser.add_argument("--agent", default="shared_cli", help="Agent identity")
    summary_parser.add_argument("--active-agent-cli", help="Filter episodes by active agent CLI")

    find_parser = subparsers.add_parser("find", help="Find similar past episodes")
    find_parser.add_argument("task", nargs="+", help="Task description")
    find_parser.add_argument("--task-type", help="Optional task type hint")
    find_parser.add_argument("--limit", type=int, default=3, help="Maximum episodes to return")
    find_parser.add_argument("--agent", default="shared_cli", help="Agent identity")
    find_parser.add_argument("--active-agent-cli", help="Filter episodes by active agent CLI")

    args = parser.parse_args()
    engine = EpisodicMemoryEngine(agent_name=args.agent)

    if args.command == "summary":
        summary = engine.get_summary()
        summary["recent"] = [
            item for item in summary.get("recent", [])
            if _episode_matches_active_agent(item, args.active_agent_cli)
        ]
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    task = " ".join(args.task)
    brief = engine.build_context_brief(task=task, task_type=args.task_type, limit=args.limit)
    print(
        json.dumps(
            _filter_brief(brief, args.active_agent_cli),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
