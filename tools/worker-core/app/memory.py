from __future__ import annotations

import json
import threading
from pathlib import Path


class Memory:
    """KV store persistente en JSON. Thread-safe con escritura atómica."""

    def __init__(self, file_path: Path) -> None:
        self._path = file_path
        self._lock = threading.Lock()

    def get(self, key: str) -> dict | None:
        return self._load().get(key)

    def set(self, key: str, value: dict) -> None:
        with self._lock:
            data = self._load()
            data[key] = value
            self._save(data)

    def delete(self, key: str) -> None:
        with self._lock:
            data = self._load()
            data.pop(key, None)
            self._save(data)

    def all(self) -> dict[str, dict]:
        return self._load()

    def _load(self) -> dict:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self, data: dict) -> None:
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self._path)
