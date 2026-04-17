#!/usr/bin/env python3
"""
Test script to verify model switching works correctly.
"""

import sys
sys.path.insert(0, "D:/IA/CODE/claudebot/orchestrator")

from core.orchestrator import Orchestrator


def test_model(model_name: str, task: str):
    """Test a specific model with a task."""
    orchestrator = Orchestrator()

    print("\n" + "="*60)
    print("Testing: " + model_name)
    print("Task: " + task)
    print("="*60)

    result = orchestrator.execute(task)

    print("Model selected: " + str(result['model']))
    print("Task type: " + str(result['task_type']))
    print("Success: " + str(result['success']))
    print("Execution time: " + str(result['execution_time_ms']) + "ms")
    print("Response:")
    if result['response']:
        try:
            print(result['response'][:300])
        except UnicodeEncodeError:
            print("[Response contains Unicode characters - see log file]")
    else:
        print("No response")

    if result['error']:
        print("ERROR: " + str(result['error']))

    return result


def main():
    orchestrator = Orchestrator()

    # Health check first
    print("=== HEALTH CHECK ===")
    health = orchestrator.health_check()
    for model, status in health.items():
        marker = "[OK]" if status else "[FAIL]"
        print("  " + model + ": " + marker)

    print("\n")

    # Test 1: gemma4 - Lightweight
    test_model(
        "gemma4:latest",
        "List 3 programming languages"
    )

    # Test 2: Fast coding
    test_model(
        "qwen3-coder-next:cloud",
        "Write a Python function that adds two numbers"
    )

    # Test 3: Planning
    test_model(
        "minimax-m2.7:cloud",
        "What are 3 approaches to organize a Python project?"
    )


if __name__ == "__main__":
    main()