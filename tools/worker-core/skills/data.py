from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import anthropic

from app.config import Config
from app.logger import get_logger


class DataSkill:
    """Parseo, escritura de datos y resumen con LLM."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._root = config.worker_root
        self._logger = get_logger("skill.data", config.logs_dir)

    # ------------------------------------------------------------------
    # Métodos directos
    # ------------------------------------------------------------------

    def read_csv(self, path: str) -> list[dict]:
        p = self._resolve(path)
        with p.open(encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    def read_json(self, path: str) -> dict | list:
        p = self._resolve(path)
        return json.loads(p.read_text(encoding="utf-8"))

    def write_json(self, path: str, data: dict | list) -> None:
        p = self._resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        self._logger.info(f"JSON escrito: {p}")

    def write_summary(self, path: str, lines: list[str]) -> None:
        """Añade líneas con timestamp a un archivo de texto."""
        p = self._resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        with p.open("a", encoding="utf-8") as f:
            for line in lines:
                f.write(f"[{ts}] {line}\n")
        self._logger.info(f"Líneas escritas en: {p}")

    def summarize(self, src: str, dst: str, prompt: str | None = None) -> str:
        """Lee src, genera un resumen con LLM y lo escribe en dst."""
        content = self._resolve(src).read_text(encoding="utf-8")
        summary = self._llm_summarize(content, prompt)
        out = self._resolve(dst)
        out.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        out.write_text(f"[{ts}]\n{summary}\n", encoding="utf-8")
        self._logger.info(f"Resumen LLM escrito en: {out}")
        return summary

    # ------------------------------------------------------------------
    # Interfaz del orquestador
    # ------------------------------------------------------------------

    def run(self, description: str, params: dict[str, Any] | None = None) -> dict:
        if params and "op" in params:
            return self._dispatch(params)
        return self._parse_text(description)

    def _dispatch(self, params: dict) -> dict:
        op = params["op"]

        if op == "write_summary":
            lines = params.get("lines") or [params.get("content", "")]
            self.write_summary(params["path"], lines)
            return {"success": True, "content": f"Resumen escrito en: {params['path']}"}

        if op == "write_json":
            self.write_json(params["path"], params.get("data", {}))
            return {"success": True, "content": f"JSON escrito en: {params['path']}"}

        if op == "summarize":
            summary = self.summarize(
                params["src"],
                params["dst"],
                params.get("prompt"),
            )
            return {"success": True, "content": summary}

        raise ValueError(
            f"DataSkill: operación desconocida '{op}'. "
            "Usa write_summary | write_json | summarize."
        )

    def _parse_text(self, task: str) -> dict:
        t = task.lower().strip()
        if any(kw in t for kw in ("write summary", "escribir resumen", "summary", "resumen")):
            for sep in (" to ", " en ", " a "):
                if sep in task:
                    parts = task.rsplit(sep, 1)
                    path = parts[1].strip()
                    self.write_summary(path, [task])
                    return {"success": True, "content": f"Resumen escrito en {path}"}
        raise ValueError(
            f"DataSkill no puede parsear: '{task}'. "
            "Pasa params={{\"op\":\"summarize|write_summary|write_json\",...}}."
        )

    # ------------------------------------------------------------------
    # LLM interno
    # ------------------------------------------------------------------

    def _llm_summarize(self, content: str, prompt: str | None = None) -> str:
        system = (
            prompt
            or "Eres un asistente que resume textos de forma clara y concisa. "
               "Extrae los puntos clave en bullet points en español."
        )
        client_kwargs: dict = {"api_key": self._config.anthropic_api_key}
        if self._config.anthropic_base_url:
            client_kwargs["base_url"] = self._config.anthropic_base_url

        client = anthropic.Anthropic(**client_kwargs)
        response = client.messages.create(
            model=self._config.model_name,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": content}],
        )
        text_blocks = [b for b in response.content if getattr(b, "type", None) == "text"]
        if not text_blocks:
            raise ValueError("El LLM no devolvió texto en el resumen")
        return text_blocks[0].text.strip()

    # ------------------------------------------------------------------

    def _resolve(self, path: str) -> Path:
        p = Path(path)
        if not p.is_absolute():
            p = self._root / p
        p = p.resolve()
        try:
            p.relative_to(self._root.resolve())
        except ValueError as exc:
            raise PermissionError(
                f"Acceso denegado: '{p}' esta fuera de worker_root ({self._root}). "
                "Usa rutas relativas a worker-core/."
            ) from exc
        return p
