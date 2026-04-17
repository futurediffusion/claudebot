#!/usr/bin/env python3
"""
Entry point - todas las tareas pasan por descomposición y multi-modelo.
"""

import sys
sys.path.insert(0, "D:/IA/CODE/claudebot/orchestrator")

from core.task_decomposer import MultiModelOrchestrator


def main():
    if len(sys.argv) < 2:
        print("Usage: python cli.py '<task description>'")
        print("\nExamples:")
        print('  python cli.py "Create a Python function to calculate factorial"')
        print('  python cli.py "Design an auth API and create the files and write tests"')
        print('  python cli.py "Refactor the entire codebase"')
        print('  python cli.py "Abre Chrome y ve a https://example.com"')
        print('  python cli.py "Abre Notepad y escribe hola mundo"')
        sys.exit(1)

    task = " ".join(sys.argv[1:])

    orchestrator = MultiModelOrchestrator()
    result = orchestrator.execute_complex_task(task, verbose=True)

    print("\n" + "="*60)
    print("RESUMEN FINAL")
    print("="*60)
    print("Tarea: " + result['original_task'])
    print("Sub-tareas: " + str(len(result['subtasks'])))
    print("Exitosas: " + str(result['successful']) + "/" + str(len(result['results'])))
    print("Tiempo: " + str(result['total_time_ms']) + "ms")

    print("\nModelos utilizados:")
    for r in result['results']:
        status = "OK" if r['success'] else "FAIL"
        print(f"  [{status}] {r['model']} - {r['phase']}")


if __name__ == "__main__":
    main()
