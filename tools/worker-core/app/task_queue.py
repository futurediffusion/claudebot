from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SubtaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    RETRYING = "retrying"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class Subtask:
    index: int
    description: str
    adapter: str          # "browser" | "windows" | "files" | "data"
    params: dict = field(default_factory=dict)
    status: SubtaskStatus = SubtaskStatus.PENDING
    attempts: int = 0
    result: Any = None
    error: str | None = None
    started_at: float | None = None
    finished_at: float | None = None

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "description": self.description,
            "adapter": self.adapter,
            "params": self.params,
            "status": self.status.value,
            "attempts": self.attempts,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


class TaskQueue:
    """Cola ordenada de subtareas para una ejecución."""

    def __init__(self, subtasks: list[Subtask]) -> None:
        self._subtasks = sorted(subtasks, key=lambda s: s.index)

    def next_pending(self) -> Subtask | None:
        for s in self._subtasks:
            if s.status == SubtaskStatus.PENDING:
                return s
        return None

    def mark_running(self, subtask: Subtask) -> None:
        subtask.status = SubtaskStatus.RUNNING
        subtask.started_at = time.time()

    def mark_retrying(self, subtask: Subtask) -> None:
        subtask.status = SubtaskStatus.RETRYING

    def mark_success(self, subtask: Subtask, result: Any) -> None:
        subtask.status = SubtaskStatus.SUCCESS
        subtask.result = result
        subtask.finished_at = time.time()

    def mark_failed(self, subtask: Subtask, error: str) -> None:
        subtask.status = SubtaskStatus.FAILED
        subtask.error = error
        subtask.finished_at = time.time()

    def all_done(self) -> bool:
        return all(
            s.status in (SubtaskStatus.SUCCESS, SubtaskStatus.FAILED)
            for s in self._subtasks
        )

    def any_failed(self) -> bool:
        return any(s.status == SubtaskStatus.FAILED for s in self._subtasks)

    def to_dict(self) -> list[dict]:
        return [s.to_dict() for s in self._subtasks]
