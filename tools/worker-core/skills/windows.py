from __future__ import annotations

from typing import Any

from adapters.windows_adapter import WindowsAdapter


class WindowsSkill:
    """Skill de escritorio Windows: delega al WindowsAdapter."""

    def __init__(self, adapter: WindowsAdapter) -> None:
        self._adapter = adapter

    def run(self, description: str, params: dict[str, Any] | None = None) -> dict:
        return self._adapter.run(description)
