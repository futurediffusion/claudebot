from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import Config
from app.memory import Memory
from app.orchestrator import Orchestrator


def main() -> None:
    parser = argparse.ArgumentParser(description="Ejecuta una tarea completa con worker-core")
    parser.add_argument("--task", required=True, help="Tarea a ejecutar")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Ruta al archivo .env (por defecto: worker-core/.env)",
    )
    args = parser.parse_args()

    task_id = uuid.uuid4().hex[:8]

    try:
        config = Config.load(args.config)
        memory = Memory(config.memory_file)
        orchestrator = Orchestrator(config, memory)
        success = orchestrator.run(task_id, args.task)
        playbook_path = config.playbooks_dir / f"{task_id}.json"

        result = {
            "success": success,
            "content": (
                f"Worker task {task_id} completed"
                if success
                else None
            ),
            "error": None if success else f"Worker task {task_id} failed",
            "task_id": task_id,
            "playbook": str(playbook_path) if playbook_path.exists() else None,
        }
    except Exception as exc:
        result = {
            "success": False,
            "content": None,
            "error": str(exc),
            "task_id": task_id,
            "playbook": None,
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
