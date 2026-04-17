#!/usr/bin/env python3
"""
Test the task decomposer and multi-model execution.
"""

import sys
sys.path.insert(0, "D:/IA/CODE/claudebot/orchestrator")

from core.task_decomposer import TaskDecomposer, MultiModelOrchestrator


def test_decomposition():
    """Prueba la descomposición de tareas."""
    decomposer = TaskDecomposer()

    test_tasks = [
        "Create a new Python file with a hello world function",
        "Design an API for user authentication and create the files",
        "Refactor the entire auth module across all files and write tests",
        "Add error handling to all API endpoints and create unit tests",
        "What is the best way to organize a Python project?",
        "Fix the login bug and verify it works"
    ]

    print("=== PRUEBA DE DESCOMPOSICION ===\n")

    for task in test_tasks:
        print("Tarea: " + task)
        print("-" * 50)
        subtasks = decomposer.decompose(task)

        for i, st in enumerate(subtasks, 1):
            dep = " -> depends on: " + str(st['depends_on']) if st['depends_on'] else ""
            model = st['model'] or "[auto]"
            print("  " + str(i) + ". [" + st['phase'] + "]")
            print("     Model: " + model)
            desc = st['description'][:60] + "..." if len(st['description']) > 60 else st['description']
            print("     " + desc + dep)
        print()


def test_execution():
    """Prueba la ejecucion de tarea compleja."""
    print("\n=== PRUEBA DE EJECUCION COMPLETA ===\n")

    orchestrator = MultiModelOrchestrator()

    result = orchestrator.execute_complex_task(
        "Create a simple Python function that adds two numbers",
        verbose=True
    )

    print("\nRESULTADO FINAL:")
    print("  Tarea original: " + result['original_task'])
    print("  Sub-tareas: " + str(len(result['subtasks'])))
    print("  Exitosas: " + str(result['successful']) + "/" + str(len(result['results'])))
    print("  Tiempo total: " + str(result['total_time_ms']) + "ms")


if __name__ == "__main__":
    test_decomposition()
    # test_execution()  # Descomentar para ejecutar realmente con modelos