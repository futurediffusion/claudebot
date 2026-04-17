from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.windows_adapter import WindowsAdapter
from app.config import Config


def main() -> None:
    parser = argparse.ArgumentParser(description="Ejecuta una tarea directa con WindowsAdapter")
    parser.add_argument("--task", required=True, help="Tarea a ejecutar en el escritorio Windows")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Ruta al archivo .env (por defecto: worker-core/.env)",
    )
    args = parser.parse_args()

    try:
        config = Config.load(args.config)
        adapter = WindowsAdapter(config)
        result = adapter.run(args.task)
    except Exception as exc:
        result = {
            "success": False,
            "content": None,
            "error": str(exc),
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
