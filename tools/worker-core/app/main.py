from __future__ import annotations

import sys
from pathlib import Path

# Añadir worker-core/ al path para que funcione tanto
# "python app/main.py" como "python -m app.main"
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import argparse
import uuid

import yaml

from app.config import Config
from app.logger import get_logger
from app.memory import Memory
from app.orchestrator import Orchestrator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PC-Worker v1 — Agente orquestador de tareas de automatización"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--task",
        type=str,
        help='Descripción de la tarea. Usa "demo" para la tarea de demostración.',
    )
    group.add_argument(
        "--task-file",
        type=Path,
        help="Ruta a un archivo YAML con la definición de la tarea (campo: task).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Ruta al archivo .env de configuración (por defecto: worker-core/.env).",
    )
    args = parser.parse_args()

    config = Config.load(args.config)
    logger = get_logger("main", config.logs_dir)
    memory = Memory(config.memory_file)

    if args.task:
        task_description = args.task.strip()
        # Atajo para la tarea demo
        if task_description.lower() == "demo":
            demo_file = config.tasks_dir / "demo.yaml"
            if not demo_file.exists():
                logger.error(f"Archivo demo no encontrado: {demo_file}")
                sys.exit(1)
            data = yaml.safe_load(demo_file.read_text(encoding="utf-8"))
            task_description = data["task"]
    else:
        task_file: Path = args.task_file
        if not task_file.exists():
            logger.error(f"Archivo de tarea no encontrado: {task_file}")
            sys.exit(1)
        data = yaml.safe_load(task_file.read_text(encoding="utf-8"))
        task_description = data["task"]

    task_id = uuid.uuid4().hex[:8]
    logger.info(f"Tarea {task_id}: {task_description[:100]}")

    orchestrator = Orchestrator(config, memory)
    success = orchestrator.run(task_id, task_description)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
