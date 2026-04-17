#!/usr/bin/env python3
"""Entry point for the multi-model orchestrator."""

from __future__ import annotations

import argparse
import sys

sys.path.insert(0, "D:/IA/CODE/claudebot/orchestrator")

from core.task_decomposer import MultiModelOrchestrator


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-model orchestrator CLI")
    parser.add_argument("task", nargs="*", help="Task description")
    parser.add_argument(
        "--agent",
        default="claude_code",
        help="Agent identity used for the shared self-model",
    )
    args = parser.parse_args()

    if not args.task:
        print("Usage: python cli.py '<task description>' [--agent claude_code|gemini_cli|codex_cli]")
        print("\nExamples:")
        print('  python cli.py "Create a Python function to calculate factorial"')
        print('  python cli.py "Design an auth API and create the files and write tests"')
        print('  python cli.py "Refactor the entire codebase"')
        print('  python cli.py "Abre Chrome y ve a https://example.com"')
        print('  python cli.py "Abre Notepad y escribe hola mundo"')
        print('  python cli.py --agent codex_cli "Fix this broken project and validate the output"')
        sys.exit(1)

    task = " ".join(args.task)
    orchestrator = MultiModelOrchestrator(agent_name=args.agent)
    result = orchestrator.execute_complex_task(task, verbose=True)

    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print("Task: " + result["original_task"])
    print("Subtasks: " + str(len(result["subtasks"])))
    print("Successful: " + str(result["successful"]) + "/" + str(len(result["results"])))
    print("Time: " + str(result["total_time_ms"]) + "ms")

    print("\nModels used:")
    for item in result["results"]:
        status = "OK" if item["success"] else "FAIL"
        print(f"  [{status}] {item['model']} - {item['phase']}")


if __name__ == "__main__":
    main()
