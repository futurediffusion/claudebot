#!/usr/bin/env python3
"""
Test complex task execution with multiple models.
"""

import sys
sys.path.insert(0, "D:/IA/CODE/claudebot/orchestrator")

from core.task_decomposer import MultiModelOrchestrator


def main():
    orchestrator = MultiModelOrchestrator()

    # Tarea que SI requiere múltiples modelos
    result = orchestrator.execute_complex_task(
        "Design an API for user authentication and create the files and write tests",
        verbose=True
    )

    print("\n" + "="*60)
    print("RESUMEN EJECUCION")
    print("="*60)
    print("Tarea original: " + result['original_task'])
    print("Total sub-tareas: " + str(len(result['subtasks'])))
    print("Exitosas: " + str(result['successful']) + "/" + str(len(result['results'])))
    print("Tiempo total: " + str(result['total_time_ms']) + "ms")

    print("\nModelos utilizados:")
    for r in result['results']:
        status = "[OK]" if r['success'] else "[FAIL]"
        print("  " + status + " " + r['model'] + " - " + r['phase'])


if __name__ == "__main__":
    main()