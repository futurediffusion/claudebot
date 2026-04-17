"""
Task logger - records all task executions for audit and analysis.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from uuid import uuid4


class TaskLogger:
    """Log task executions to memory/logs/."""

    def __init__(self, log_dir: str = "memory/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        task: str,
        model_type: str,
        task_type: str,
        tools_used: list[str],
        result: str,
        error: Optional[str] = None,
        execution_time_ms: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a task execution.

        Returns:
            Log entry ID
        """
        entry_id = str(uuid4())[:8]
        timestamp = datetime.now().isoformat()

        entry = {
            "id": entry_id,
            "timestamp": timestamp,
            "task": task,
            "model": model_type,
            "task_type": task_type,
            "tools": tools_used,
            "execution_time_ms": execution_time_ms,
            "result": result,
            "error": error,
            "metadata": metadata or {}
        }

        # Write to daily log file
        date = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"tasks_{date}.jsonl"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        return entry_id

    def get_recent(self, limit: int = 10) -> list[Dict[str, Any]]:
        """Get recent task logs."""
        logs = []
        for log_file in sorted(self.log_dir.glob("tasks_*.jsonl"), reverse=True)[:5]:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line))
                    if len(logs) >= limit:
                        break
            if len(logs) >= limit:
                break

        return logs[-limit:] if len(logs) > limit else logs

    def get_logs_by_model(self, model: str, limit: int = 20) -> list[Dict[str, Any]]:
        """Get logs for a specific model."""
        logs = []
        for log_file in sorted(self.log_dir.glob("tasks_*.jsonl"), reverse=True):
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        if entry.get("model") == model:
                            logs.append(entry)
                    if len(logs) >= limit:
                        break
            if len(logs) >= limit:
                break
        return logs

    def get_errors(self, limit: int = 20) -> list[Dict[str, Any]]:
        """Get recent error logs."""
        errors = []
        for log_file in sorted(self.log_dir.glob("tasks_*.jsonl"), reverse=True):
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        if entry.get("error"):
                            errors.append(entry)
                    if len(errors) >= limit:
                        break
            if len(errors) >= limit:
                break
        return errors
