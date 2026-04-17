from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

import anthropic

from app.config import Config
from app.logger import get_logger
from app.memory import Memory
from app.task_queue import Subtask, TaskQueue
from adapters.browser_adapter import BrowserAdapter
from adapters.windows_adapter import WindowsAdapter
from skills.browser import BrowserSkill
from skills.data import DataSkill
from skills.files import FilesSkill
from skills.windows import WindowsSkill

_DECOMPOSE_SYSTEM = """\
Eres un planificador de tareas. Traduces instrucciones en espanol a subtareas JSON.
Adaptadores disponibles en esta sesion: {allowlist}

TABLA DE INTENCIONES
- "resume X en Y" / "haz un resumen de X y guardalo en Y" -> data, op:summarize
- "copia X a Y" / "guarda una copia de X en Y" -> files, op:copy
- "mueve X a Y" / "renombra X como Y" -> files, op:move
- "lee X" / "abre X" / "muestrame X" -> files, op:read
- "escribe [texto] en X" / "crea X con [texto]" -> files, op:write
- "escribe estas lineas en X" -> data, op:write_summary
- "abre [URL]" / "navega a [URL]" / "busca en [sitio]" -> browser, params:{}
- "abre [app]" / "haz click en [elemento]" -> windows, params:{}

EJEMPLOS COMPLETOS
Input: "lee tasks/info.txt y resumelo en tasks/output/resumen.txt"
Output: [{"index":0,"description":"Resumir archivo con IA","adapter":"data","params":{"op":"summarize","src":"tasks/info.txt","dst":"tasks/output/resumen.txt"}}]

Input: "copia tasks/tests/doc.txt a tasks/output/doc_backup.txt"
Output: [{"index":0,"description":"Copiar archivo","adapter":"files","params":{"op":"copy","src":"tasks/tests/doc.txt","dst":"tasks/output/doc_backup.txt"}}]

Input: "mueve tasks/output/doc.txt a tasks/archive/doc.txt"
Output: [{"index":0,"description":"Mover archivo","adapter":"files","params":{"op":"move","src":"tasks/output/doc.txt","dst":"tasks/archive/doc.txt"}}]

Input: "escribe 'hola mundo' en tasks/output/test.txt"
Output: [{"index":0,"description":"Escribir archivo","adapter":"files","params":{"op":"write","path":"tasks/output/test.txt","content":"hola mundo"}}]

Input: "copia tasks/report.txt a tasks/backup/report.txt y luego resumelo en tasks/output/summary.txt"
Output: [{"index":0,"description":"Copiar archivo","adapter":"files","params":{"op":"copy","src":"tasks/report.txt","dst":"tasks/backup/report.txt"}},{"index":1,"description":"Resumir con IA","adapter":"data","params":{"op":"summarize","src":"tasks/report.txt","dst":"tasks/output/summary.txt"}}]

Input: "abre https://example.com y guarda el titulo de la pagina en tasks/output/titulo.txt"
Output: [{"index":0,"description":"Abrir URL y extraer titulo","adapter":"browser","params":{}},{"index":1,"description":"Guardar titulo extraido","adapter":"files","params":{"op":"write","path":"tasks/output/titulo.txt","content":"[titulo extraido por browser]"}}]

REGLAS
- Usa solo adaptadores presentes en la allowlist.
- Para files y data, params es obligatorio con op y sus campos.
- Para browser y windows, params puede ser {}.
- No inventes rutas, contenido ni resultados que no esten en la instruccion.
- Rutas siempre relativas a worker-core/ (ej: tasks/output/archivo.txt).
- Responde unicamente JSON valido. Sin markdown. Sin texto extra.
"""

_ADAPTER_ALIASES = {
    "file": "files",
    "files": "files",
    "filesystem": "files",
    "archivo": "files",
    "archivos": "files",
    "data": "data",
    "datos": "data",
    "browser": "browser",
    "web": "browser",
    "windows": "windows",
    "desktop": "windows",
}

_OPERATION_ALIASES = {
    "files": {
        "read": {"read", "leer", "lee", "open", "abrir", "abre", "mostrar", "muestra"},
        "write": {"write", "escribir", "escribe", "create", "crear", "crea"},
        "copy": {"copy", "copiar", "copia"},
        "move": {"move", "mover", "mueve", "rename", "renombrar", "renombra"},
    },
    "data": {
        "summarize": {"summarize", "summary", "summarize_text", "resumir", "resume", "resumen"},
        "write_summary": {"write_summary", "summary_lines", "escribir_resumen", "append_summary"},
        "write_json": {"write_json", "json", "guardar_json"},
    },
}


def _strip_wrapping_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1].strip()
    return value


class Orchestrator:
    def __init__(self, config: Config, memory: Memory) -> None:
        self._config = config
        self._memory = memory
        self._logger = get_logger("orchestrator", config.logs_dir)
        client_kwargs: dict[str, Any] = {"api_key": config.anthropic_api_key}
        if config.anthropic_base_url:
            client_kwargs["base_url"] = config.anthropic_base_url
        self._client = anthropic.Anthropic(**client_kwargs)

        win_adapter = WindowsAdapter(config)
        br_adapter = BrowserAdapter(config)
        files_skill = FilesSkill(config)
        data_skill = DataSkill(config)

        self._skills: dict[str, Any] = {
            "windows": WindowsSkill(win_adapter),
            "browser": BrowserSkill(br_adapter),
            "files": files_skill,
            "data": data_skill,
        }

    def run(self, task_id: str, task_description: str) -> bool:
        """Ciclo de vida completo de una tarea."""
        self._logger.info(
            f"Iniciando tarea: {task_description[:80]}",
            extra={"task_id": task_id},
        )

        try:
            subtasks = self._decompose(task_description)
        except Exception as exc:
            self._logger.error(
                f"Error al descomponer la tarea: {exc}",
                extra={"task_id": task_id},
            )
            return False

        queue = TaskQueue(subtasks)

        while not queue.all_done():
            subtask = queue.next_pending()
            if subtask is None:
                break
            self._run_subtask(task_id, queue, subtask)

        if not queue.any_failed():
            self._save_playbook(task_id, task_description, queue)
            self._logger.info("Tarea completada con exito", extra={"task_id": task_id})
            return True

        failed = [s for s in queue.to_dict() if s["status"] == "failed"]
        self._logger.error(
            f"Tarea fallida. Subtareas fallidas: {[s['index'] for s in failed]}",
            extra={"task_id": task_id},
        )
        return False

    def _decompose(self, task_description: str) -> list[Subtask]:
        """Descompone una tarea en subtareas estructuradas."""
        simple_plan = self._try_rule_based_decompose(task_description)
        if simple_plan is not None:
            return self._normalize_subtasks(simple_plan)

        allowlist_str = ", ".join(self._config.action_allowlist)
        system = _DECOMPOSE_SYSTEM.replace("{allowlist}", allowlist_str)

        response = self._client.messages.create(
            model=self._config.orchestrator_model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": task_description}],
        )
        text_blocks = [b for b in response.content if getattr(b, "type", None) == "text"]
        if not text_blocks:
            raise ValueError(
                "El modelo no devolvio ningun bloque de texto. "
                f"Tipos recibidos: {[getattr(b, 'type', '?') for b in response.content]}"
            )
        raw = text_blocks[0].text.strip()

        if raw.startswith("```"):
            lines = raw.splitlines()
            raw = "\n".join(lines[1:-1] if lines and lines[-1].strip() == "```" else lines[1:])

        return self._normalize_subtasks(json.loads(raw))

    def _try_rule_based_decompose(
        self, task_description: str
    ) -> list[dict[str, Any]] | None:
        task = " ".join(task_description.strip().split())

        match = re.fullmatch(
            r"(?:lee|leer|abre|abrir|muestra|mostrar|muestrame)\s+(?P<src>.+?)\s+y\s+resumelo\s+(?:en|a)\s+(?P<dst>.+)",
            task,
            flags=re.IGNORECASE,
        )
        if match:
            return [
                {
                    "index": 0,
                    "description": "Resumir archivo con IA",
                    "adapter": "data",
                    "params": {
                        "op": "summarize",
                        "src": _strip_wrapping_quotes(match.group("src")),
                        "dst": _strip_wrapping_quotes(match.group("dst")),
                    },
                }
            ]

        match = re.fullmatch(
            r"(?:resume|resumir)\s+(?P<src>.+?)\s+(?:en|a)\s+(?P<dst>.+)",
            task,
            flags=re.IGNORECASE,
        )
        if match:
            return [
                {
                    "index": 0,
                    "description": "Resumir archivo con IA",
                    "adapter": "data",
                    "params": {
                        "op": "summarize",
                        "src": _strip_wrapping_quotes(match.group("src")),
                        "dst": _strip_wrapping_quotes(match.group("dst")),
                    },
                }
            ]

        match = re.fullmatch(
            r"(?:haz un resumen de|resumen de)\s+(?P<src>.+?)\s+y\s+(?:guardalo|guarda el resumen|guarda)\s+(?:en|a)\s+(?P<dst>.+)",
            task,
            flags=re.IGNORECASE,
        )
        if match:
            return [
                {
                    "index": 0,
                    "description": "Resumir archivo con IA",
                    "adapter": "data",
                    "params": {
                        "op": "summarize",
                        "src": _strip_wrapping_quotes(match.group("src")),
                        "dst": _strip_wrapping_quotes(match.group("dst")),
                    },
                }
            ]

        match = re.fullmatch(
            r"(?:copia|copiar|guarda una copia de)\s+(?P<src>.+?)\s+(?:a|en)\s+(?P<dst>.+)",
            task,
            flags=re.IGNORECASE,
        )
        if match:
            return [
                {
                    "index": 0,
                    "description": "Copiar archivo",
                    "adapter": "files",
                    "params": {
                        "op": "copy",
                        "src": _strip_wrapping_quotes(match.group("src")),
                        "dst": _strip_wrapping_quotes(match.group("dst")),
                    },
                }
            ]

        match = re.fullmatch(
            r"(?:mueve|mover)\s+(?P<src>.+?)\s+(?:a|en)\s+(?P<dst>.+)",
            task,
            flags=re.IGNORECASE,
        )
        if match:
            return [
                {
                    "index": 0,
                    "description": "Mover archivo",
                    "adapter": "files",
                    "params": {
                        "op": "move",
                        "src": _strip_wrapping_quotes(match.group("src")),
                        "dst": _strip_wrapping_quotes(match.group("dst")),
                    },
                }
            ]

        match = re.fullmatch(
            r"(?:renombra|renombrar)\s+(?P<src>.+?)\s+como\s+(?P<dst>.+)",
            task,
            flags=re.IGNORECASE,
        )
        if match:
            return [
                {
                    "index": 0,
                    "description": "Mover archivo",
                    "adapter": "files",
                    "params": {
                        "op": "move",
                        "src": _strip_wrapping_quotes(match.group("src")),
                        "dst": _strip_wrapping_quotes(match.group("dst")),
                    },
                }
            ]

        match = re.fullmatch(
            r"(?:escribe|escribir)\s+['\"](?P<content>.+?)['\"]\s+(?:en|a)\s+(?P<path>.+)",
            task,
            flags=re.IGNORECASE,
        )
        if match:
            return [
                {
                    "index": 0,
                    "description": "Escribir archivo",
                    "adapter": "files",
                    "params": {
                        "op": "write",
                        "path": _strip_wrapping_quotes(match.group("path")),
                        "content": match.group("content"),
                    },
                }
            ]

        match = re.fullmatch(
            r"(?:crea|crear)\s+(?P<path>.+?)\s+con\s+['\"](?P<content>.+?)['\"]",
            task,
            flags=re.IGNORECASE,
        )
        if match:
            return [
                {
                    "index": 0,
                    "description": "Escribir archivo",
                    "adapter": "files",
                    "params": {
                        "op": "write",
                        "path": _strip_wrapping_quotes(match.group("path")),
                        "content": match.group("content"),
                    },
                }
            ]

        match = re.fullmatch(
            r"(?:lee|leer|abre|abrir|muestra|mostrar|muestrame)\s+(?P<path>.+)",
            task,
            flags=re.IGNORECASE,
        )
        if match:
            path = _strip_wrapping_quotes(match.group("path"))
            if not re.match(r"https?://", path, flags=re.IGNORECASE):
                return [
                    {
                        "index": 0,
                        "description": "Leer archivo",
                        "adapter": "files",
                        "params": {"op": "read", "path": path},
                    }
                ]

        return None

    def _normalize_subtasks(self, raw_subtasks: Any) -> list[Subtask]:
        if isinstance(raw_subtasks, dict):
            raw_subtasks = [raw_subtasks]
        if not isinstance(raw_subtasks, list) or not raw_subtasks:
            raise ValueError("El modelo debe devolver una lista JSON no vacia de subtareas.")

        subtasks: list[Subtask] = []
        for fallback_index, item in enumerate(raw_subtasks):
            if not isinstance(item, dict):
                raise ValueError(f"Subtarea invalida en posicion {fallback_index}: {item!r}")

            adapter = self._canonicalize_adapter(item.get("adapter", ""))
            if adapter not in self._config.action_allowlist:
                raise ValueError(
                    f"El adaptador '{adapter}' no esta en ACTION_ALLOWLIST "
                    f"({self._config.action_allowlist})."
                )

            params = item.get("params") or {}
            if not isinstance(params, dict):
                raise ValueError(f"params debe ser un objeto JSON para '{adapter}'.")

            description = str(item.get("description") or f"Subtarea {fallback_index}").strip()
            canonical_params = self._normalize_params(adapter, description, params)

            subtasks.append(
                Subtask(
                    index=int(item.get("index", fallback_index)),
                    description=description,
                    adapter=adapter,
                    params=canonical_params,
                )
            )

        return sorted(subtasks, key=lambda subtask: subtask.index)

    def _normalize_params(
        self, adapter: str, description: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        if adapter in {"browser", "windows"}:
            return params

        op = self._canonicalize_op(
            adapter,
            params.get("op") or self._infer_op_from_description(adapter, description),
        )
        if not op:
            raise ValueError(
                f"No pude determinar la operacion para adapter='{adapter}' "
                f"en la subtarea '{description}'."
            )

        if adapter == "files":
            return self._normalize_files_params(op, params)
        if adapter == "data":
            return self._normalize_data_params(op, params)

        raise ValueError(f"Adaptador desconocido: '{adapter}'")

    def _normalize_files_params(self, op: str, params: dict[str, Any]) -> dict[str, Any]:
        if op == "read":
            path = self._pick_param(params, "path", "src", "file", "filepath")
            if not path:
                raise ValueError("files.read requiere 'path'.")
            return {"op": "read", "path": self._clean_path(path)}

        if op == "write":
            path = self._pick_param(params, "path", "dst", "target", "output")
            if not path:
                raise ValueError("files.write requiere 'path'.")
            content = self._pick_param(params, "content", "text", "value")
            return {
                "op": "write",
                "path": self._clean_path(path),
                "content": "" if content is None else str(content),
            }

        if op in {"copy", "move"}:
            src = self._pick_param(params, "src", "from", "source")
            dst = self._pick_param(params, "dst", "to", "target", "output")
            if not src or not dst:
                raise ValueError(f"files.{op} requiere 'src' y 'dst'.")
            return {
                "op": op,
                "src": self._clean_path(src),
                "dst": self._clean_path(dst),
            }

        raise ValueError(f"Operacion no soportada para files: '{op}'")

    def _normalize_data_params(self, op: str, params: dict[str, Any]) -> dict[str, Any]:
        if op == "summarize":
            src = self._pick_param(params, "src", "path", "file", "input")
            dst = self._pick_param(params, "dst", "target", "output")
            if not src or not dst:
                raise ValueError("data.summarize requiere 'src' y 'dst'.")
            normalized = {
                "op": "summarize",
                "src": self._clean_path(src),
                "dst": self._clean_path(dst),
            }
            prompt = self._pick_param(params, "prompt", "instruction")
            if prompt:
                normalized["prompt"] = str(prompt).strip()
            return normalized

        if op == "write_summary":
            path = self._pick_param(params, "path", "dst", "target", "output")
            if not path:
                raise ValueError("data.write_summary requiere 'path'.")
            lines = params.get("lines")
            if isinstance(lines, str):
                lines = [lines]
            elif lines is None:
                content = self._pick_param(params, "content", "text")
                lines = [str(content)] if content is not None else []
            elif not isinstance(lines, list):
                raise ValueError("data.write_summary requiere 'lines' como lista.")
            return {
                "op": "write_summary",
                "path": self._clean_path(path),
                "lines": [str(line) for line in lines],
            }

        if op == "write_json":
            path = self._pick_param(params, "path", "dst", "target", "output")
            if not path:
                raise ValueError("data.write_json requiere 'path'.")

            payload = self._pick_param(params, "data", "json", "value", "content")
            if payload is None:
                payload = {}
            elif isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError as exc:
                    raise ValueError("data.write_json requiere 'data' con JSON valido.") from exc
            elif not isinstance(payload, (dict, list)):
                raise ValueError("data.write_json requiere 'data' como dict o list.")

            return {
                "op": "write_json",
                "path": self._clean_path(path),
                "data": payload,
            }

        raise ValueError(f"Operacion no soportada para data: '{op}'")

    def _canonicalize_adapter(self, adapter: Any) -> str:
        key = str(adapter).strip().lower()
        return _ADAPTER_ALIASES.get(key, key)

    def _canonicalize_op(self, adapter: str, op: Any) -> str:
        key = str(op).strip().lower()
        for canonical, aliases in _OPERATION_ALIASES.get(adapter, {}).items():
            if key == canonical or key in aliases:
                return canonical
        return key

    def _infer_op_from_description(self, adapter: str, description: str) -> str | None:
        text = description.lower()

        if adapter == "files":
            if any(token in text for token in ("copi", "copy")):
                return "copy"
            if any(token in text for token in ("muev", "move", "renombr")):
                return "move"
            if any(token in text for token in ("lee", "leer", "read", "abre", "muestra")):
                return "read"
            if any(token in text for token in ("escrib", "write", "crea")):
                return "write"

        if adapter == "data":
            if any(token in text for token in ("resum", "summary", "summar")):
                return "summarize"
            if "json" in text:
                return "write_json"
            if any(token in text for token in ("linea", "lineas", "resumen")):
                return "write_summary"

        return None

    def _pick_param(self, params: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in params and params[key] not in (None, ""):
                return params[key]
        return None

    def _clean_path(self, value: Any) -> str:
        return _strip_wrapping_quotes(str(value))

    def _run_subtask(self, task_id: str, queue: TaskQueue, subtask: Subtask) -> None:
        """Ejecuta una subtarea con un reintento en caso de fallo."""
        queue.mark_running(subtask)

        for attempt in range(self._config.max_retries + 1):
            subtask.attempts = attempt + 1
            if attempt > 0:
                queue.mark_retrying(subtask)
                self._logger.info(
                    f"Reintentando subtarea {subtask.index} (intento {attempt + 1})",
                    extra={"task_id": task_id, "subtask_index": subtask.index},
                )

            self._logger.info(
                f"Subtarea {subtask.index} [{subtask.adapter}]: {subtask.description[:60]}",
                extra={
                    "task_id": task_id,
                    "subtask_index": subtask.index,
                    "adapter": subtask.adapter,
                    "attempt": attempt + 1,
                },
            )

            try:
                skill = self._skills.get(subtask.adapter)
                if skill is None:
                    raise ValueError(f"Adaptador desconocido: '{subtask.adapter}'")

                result = skill.run(subtask.description, subtask.params)
                queue.mark_success(subtask, result)
                self._logger.info(
                    f"Subtarea {subtask.index} completada",
                    extra={"task_id": task_id, "subtask_index": subtask.index},
                )
                return

            except Exception as exc:
                self._logger.warning(
                    f"Subtarea {subtask.index} fallo (intento {attempt + 1}): {exc}",
                    extra={
                        "task_id": task_id,
                        "subtask_index": subtask.index,
                        "attempt": attempt + 1,
                        "error": str(exc),
                    },
                )
                if attempt >= self._config.max_retries:
                    queue.mark_failed(subtask, str(exc))
                    self._logger.error(
                        f"Subtarea {subtask.index} agoto reintentos",
                        extra={"task_id": task_id, "subtask_index": subtask.index},
                    )

    def _save_playbook(
        self, task_id: str, task_description: str, queue: TaskQueue
    ) -> None:
        """Guarda el playbook JSON en playbooks/<task_id>.json."""
        playbook = {
            "task_id": task_id,
            "task_description": task_description,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "subtasks": queue.to_dict(),
        }
        path = self._config.playbooks_dir / f"{task_id}.json"
        path.write_text(
            json.dumps(playbook, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        self._logger.info(
            f"Playbook guardado: {path.name}",
            extra={"path": str(path)},
        )
