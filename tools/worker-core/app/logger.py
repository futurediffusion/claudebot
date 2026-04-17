from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path


class _JsonFormatter(logging.Formatter):
    """Formatea cada registro como una línea JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Añadir campos extra pasados con extra={...}
        for key in ("task_id", "subtask_index", "adapter", "attempt", "path", "error"):
            val = record.__dict__.get(key)
            if val is not None:
                payload[key] = val
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str, logs_dir: Path) -> logging.Logger:
    """Devuelve un logger que escribe en logs/<YYYY-MM-DD>.jsonl y en consola."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # ya configurado

    logger.setLevel(logging.DEBUG)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = logs_dir / f"{date_str}.jsonl"
    logs_dir.mkdir(parents=True, exist_ok=True)

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(_JsonFormatter())
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)

    return logger
