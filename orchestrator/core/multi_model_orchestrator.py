"""
Single-agent CLI-first orchestrator (legacy multi-model test harness).
"""

from core.task_decomposer import TaskDecomposer, MultiModelOrchestrator as MMOrchestrator
from core.orchestrator import Orchestrator


def test_decomposition():
    """Prueba la descomposición de tareas."""
    decomposer = TaskDecomposer()

    test_tasks = [
        "Design an API for user authentication and create the files",
        "Refactor the entire auth module across all files and write tests",
        "Create a new Python module with a calculator class",
        "What is the best way to organize a Python project?",
        "Add error handling to all API endpoints and create unit tests",
        "Fix the login bug and verify it works"
    ]

    print("=== PRUEBA DE DESCOMPOSICIÓN ===\n")

    for task in test_tasks:
        print(f"Tarea: {task}")
        print("-" * 50)
        subtasks = decomposer.decompose(task)

        for i, st in enumerate(subtasks, 1):
            dep = f" -> depends on: {st['depends_on']}" if st['depends_on'] else ""
            model = st['model'] or "[auto]"
            print(f"  {i}. [{st['phase']}]")
            print(f"     Model: {model}")
            print(f"     {st['description'][:60]}{dep}")
        print()


def test_complex_execution():
    """Prueba la ejecución de tarea compleja."""
    print("\n=== PRUEBA DE EJECUCIÓN COMPLETA ===\n")

    orchestrator = MMOrchestrator()

    # Tarea de prueba
    result = orchestrator.execute_complex_task(
        "Create a simple Python function that adds two numbers and write a test for it",
        verbose=True
    )

    print("\nRESULTADO FINAL:")
    print(f"  Tarea original: {result['original_task']}")
    print(f"  Sub-tareas: {len(result['subtasks'])}")
    print(f"  Exitosas: {result['successful']}/{len(result['results'])}")
    print(f"  Tiempo total: {result['total_time_ms']}ms")


if __name__ == "__main__":
    test_decomposition()
    # test_complex_execution()  # Descomentar para ejecutar realmente