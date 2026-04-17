from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from app.config import Config
from app.logger import get_logger


class FilesSkill:
    """Operaciones de sistema de archivos locales. Sin LLM."""

    def __init__(self, config: Config) -> None:
        self._root = config.worker_root
        self._logger = get_logger("skill.files", config.logs_dir)

    def read(self, path: str) -> str:
        p = self._validate(path)
        return p.read_text(encoding="utf-8")

    def write(self, path: str, content: str) -> None:
        p = self._validate(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        self._logger.info(f"Archivo escrito: {p}")

    def move(self, src: str, dst: str) -> None:
        s = self._validate(src)
        d = self._validate(dst)
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(s), str(d))
        self._logger.info(f"Movido: {s} → {d}")

    def copy(self, src: str, dst: str) -> None:
        s = self._validate(src)
        d = self._validate(dst)
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(s), str(d))
        self._logger.info(f"Copiado: {s} → {d}")

    def exists(self, path: str) -> bool:
        return self._validate(path).exists()

    def list_dir(self, path: str) -> list[str]:
        return [str(c) for c in self._validate(path).iterdir()]

    def run(self, description: str, params: dict[str, Any] | None = None) -> dict:
        """Interfaz uniforme para el orquestador.

        Si params contiene "op", despacha de forma estructurada.
        Si no, intenta parsear la descripción en texto (fallback legacy).
        """
        if params and "op" in params:
            return self._dispatch(params)
        return self._parse_text(description)

    # ------------------------------------------------------------------
    # Despacho estructurado (camino principal)
    # ------------------------------------------------------------------

    def _dispatch(self, params: dict) -> dict:
        op = params["op"]

        if op == "write":
            self.write(params["path"], params.get("content", ""))
            return {"success": True, "content": f"Escrito: {params['path']}"}

        if op == "move":
            self.move(params["src"], params["dst"])
            return {"success": True, "content": f"Movido: {params['src']} → {params['dst']}"}

        if op == "copy":
            self.copy(params["src"], params["dst"])
            return {"success": True, "content": f"Copiado: {params['src']} → {params['dst']}"}

        if op == "read":
            content = self.read(params["path"])
            return {"success": True, "content": content}

        raise ValueError(f"FilesSkill: operación desconocida '{op}'. Usa write|move|copy|read.")

    # ------------------------------------------------------------------
    # Fallback: parseo de texto libre
    # ------------------------------------------------------------------

    def _parse_text(self, task: str) -> dict:
        t = task.lower().strip()

        if t.startswith("move ") and " to " in t:
            parts = task[5:].split(" to ", 1)
            self.move(parts[0].strip(), parts[1].strip())
            return {"success": True, "content": f"Movido {parts[0].strip()} → {parts[1].strip()}"}

        if t.startswith("copy ") and " to " in t:
            parts = task[5:].split(" to ", 1)
            self.copy(parts[0].strip(), parts[1].strip())
            return {"success": True, "content": f"Copiado {parts[0].strip()} → {parts[1].strip()}"}

        if t.startswith("read "):
            content = self.read(task[5:].strip())
            return {"success": True, "content": content}

        raise ValueError(
            f"FilesSkill no puede parsear la instrucción: '{task}'. "
            "Pasa params={{\"op\":\"write|move|copy|read\",...}} o usa "
            "'move <src> to <dst>' / 'read <path>'."
        )

    # ------------------------------------------------------------------

    def _validate(self, path: str) -> Path:
        p = Path(path)
        if not p.is_absolute():
            p = self._root / p
        p = p.resolve()
        try:
            p.relative_to(self._root.resolve())
        except ValueError:
            raise PermissionError(
                f"Acceso denegado: '{p}' está fuera de worker_root ({self._root}). "
                "Usa rutas relativas a worker-core/."
            )
        return p
