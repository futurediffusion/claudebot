"""
Natural-language detection for browser/windows/worker automation tasks.
"""

from __future__ import annotations

import re
from typing import Optional


_URL_RE = re.compile(r"https?://|www\.", flags=re.IGNORECASE)

_CODE_KEYWORDS = {
    "python",
    "javascript",
    "typescript",
    "java",
    "c#",
    "class",
    "function",
    "method",
    "module",
    "api",
    "sdk",
    "refactor",
    "bug",
    "stack trace",
    "traceback",
    "json schema",
    "unit test",
    "integration test",
    "write code",
    "implement",
    "codebase",
}

_BROWSER_KEYWORDS = {
    "browser",
    "chrome",
    "edge",
    "firefox",
    "tab",
    "page",
    "website",
    "web",
    "url",
    "navigate",
    "navega",
    "abre la pagina",
    "abre el sitio",
    "open website",
    "search google",
    "buscar en google",
    "freepik",
    "pikaso",
    "click en la pagina",
    "fill the form",
    "rellena el formulario",
}

_WINDOWS_KEYWORDS = {
    "notepad",
    "paint",
    "calculator",
    "explorer",
    "file explorer",
    "task manager",
    "settings",
    "windows",
    "desktop",
    "start menu",
    "taskbar",
    "ventana",
    "escritorio",
    "abre notepad",
    "abre calculadora",
    "abre configuracion",
    "abre explorer",
}

_AUTOMATION_ACTIONS = {
    "open",
    "abre",
    "abrir",
    "navigate",
    "navega",
    "go to",
    "ve a",
    "click",
    "haz click",
    "type",
    "escribe",
    "press",
    "pulsa",
    "select",
    "selecciona",
    "search",
    "busca",
    "login",
    "inicia sesion",
    "download",
    "descarga",
    "upload",
    "sube",
}

_WORKER_COMPOSITE_KEYWORDS = {
    "save",
    "guarda",
    "guardar",
    "write",
    "copy",
    "copia",
    "move",
    "mueve",
    "summary",
    "summarize",
    "resumen",
    "resume",
    "tasks/",
    "output/",
}


def _normalize(task: str) -> str:
    return " ".join(task.lower().split())


def has_code_intent(task: str) -> bool:
    """Return True for software-building tasks, not end-user automation."""
    normalized = _normalize(task)
    return any(keyword in normalized for keyword in _CODE_KEYWORDS)


def detect_automation_route(task: str) -> Optional[str]:
    """
    Detect whether a natural-language task should go to browser, windows,
    or the full worker-core orchestrator.
    """
    normalized = _normalize(task)

    if normalized.startswith("browser:"):
        return "browser"

    if normalized.startswith("windows:"):
        return "windows"

    if normalized.startswith("worker:"):
        return "worker"

    if has_code_intent(normalized):
        return None

    browser_signal = _URL_RE.search(normalized) is not None or any(
        keyword in normalized for keyword in _BROWSER_KEYWORDS
    )
    windows_signal = any(keyword in normalized for keyword in _WINDOWS_KEYWORDS)
    automation_signal = any(keyword in normalized for keyword in _AUTOMATION_ACTIONS)
    worker_signal = any(keyword in normalized for keyword in _WORKER_COMPOSITE_KEYWORDS)
    multi_step_signal = any(separator in normalized for separator in (" and ", " luego ", " then ", " y luego "))

    if browser_signal and (worker_signal or multi_step_signal):
        return "worker"

    if windows_signal and (worker_signal or multi_step_signal):
        return "worker"

    if browser_signal and windows_signal:
        return "worker"

    if browser_signal and automation_signal:
        return "browser"

    if windows_signal and automation_signal:
        return "windows"

    if browser_signal:
        return "browser"

    if windows_signal:
        return "windows"

    return None
