from __future__ import annotations

from typing import Any

from adapters.browser_adapter import BrowserAdapter


class BrowserSkill:
    """Skill de navegador: delega al BrowserAdapter."""

    def __init__(self, adapter: BrowserAdapter) -> None:
        self._adapter = adapter

    def run(self, description: str, params: dict[str, Any] | None = None) -> dict:
        return self._adapter.run(description)
