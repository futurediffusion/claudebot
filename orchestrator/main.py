#!/usr/bin/env python3
"""
Example usage of the Multi-Model Orchestrator.
"""

from orchestrator import Orchestrator


def main():
    orchestrator = Orchestrator()

    # Example 1: Health check
    print("=== Health Check ===")
    health = orchestrator.health_check()
    for model, status in health.items():
        print(f"  {model}: {'✓' if status else '✗'}")

    # Example 2: Fast coding task
    print("\n=== Fast Coding Task ===")
    result = orchestrator.execute(
        task="Create a Python function that calculates fibonacci numbers"
    )
    print(f"Model: {result['model']}")
    print(f"Task Type: {result['task_type']}")
    print(f"Success: {result['success']}")

    # Example 3: Planning task
    print("\n=== Planning Task ===")
    result = orchestrator.execute(
        task="Design an architecture for a web API with auth and database"
    )
    print(f"Model: {result['model']}")
    print(f"Task Type: {result['task_type']}")

    # Example 4: Vision task (would need actual screenshot)
    print("\n=== Vision Task ===")
    result = orchestrator.execute(
        task="Analyze the UI in this screenshot for issues"
    )
    print(f"Model: {result['model']}")
    print(f"Task Type: {result['task_type']}")


if __name__ == "__main__":
    main()