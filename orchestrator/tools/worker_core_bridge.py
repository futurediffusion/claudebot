"""
Bridge tools that expose worker-core browser/windows automation to the orchestrator
and to external CLI agents.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional


_REPO_ROOT = Path(__file__).resolve().parents[2]
_WORKER_CORE_ROOT = _REPO_ROOT / "tools" / "worker-core"
_WORKER_VENV_PYTHON = _WORKER_CORE_ROOT / ".venv" / "Scripts" / "python.exe"


def _resolve_worker_python() -> str:
    """Prefer worker-core's managed interpreter when available."""
    if _WORKER_VENV_PYTHON.exists():
        return str(_WORKER_VENV_PYTHON)
    return sys.executable


def _merge_allowlist(*required: str) -> str:
    """
    Build ACTION_ALLOWLIST for worker-core without mutating its .env file.
    """
    current = os.environ.get("ACTION_ALLOWLIST", "")
    merged: list[str] = []
    for value in [current, "files,data", ",".join(required)]:
        for item in value.split(","):
            normalized = item.strip()
            if normalized and normalized not in merged:
                merged.append(normalized)
    return ",".join(merged)


def _extract_json_payload(stdout: str) -> dict[str, Any] | None:
    """
    Worker-core can log to stdout before printing the final JSON result.
    Parse the last JSON object found in the output.
    """
    candidate_positions = [index for index, char in enumerate(stdout) if char == "{"]  # noqa: C416
    for index in reversed(candidate_positions):
        candidate = stdout[index:].strip()
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return None


class WorkerCoreBridge:
    """Run worker-core scripts and normalize JSON output."""

    def __init__(self, timeout: int = 300):
        self.timeout = timeout
        self.worker_root = _WORKER_CORE_ROOT
        self.worker_python = _resolve_worker_python()

    def is_available(self) -> bool:
        """Return True when worker-core exists locally."""
        return self.worker_root.exists()

    def run_script(
        self,
        script_relative_path: str,
        task: str,
        allowlist: str,
        config_path: Optional[str] = None
    ) -> dict[str, Any]:
        """Execute a worker-core script and parse its JSON result."""
        script_path = self.worker_root / script_relative_path
        if not script_path.exists():
            return {
                "success": False,
                "error": f"Worker script not found: {script_path}",
                "content": None,
            }

        env = os.environ.copy()
        env["ACTION_ALLOWLIST"] = allowlist

        command = [self.worker_python, str(script_path), "--task", task]
        if config_path:
            command.extend(["--config", config_path])

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=str(self.worker_root),
                env=env,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Worker task timed out after {self.timeout}s",
                "content": None,
            }
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "content": None,
            }

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if stdout:
            payload = _extract_json_payload(stdout)
            if payload is not None:
                payload.setdefault("stdout", stdout)
                payload.setdefault("stderr", stderr)
                payload.setdefault("returncode", result.returncode)
                return payload

        return {
            "success": result.returncode == 0,
            "content": stdout or None,
            "error": None if result.returncode == 0 else (stderr or stdout or "Worker task failed"),
            "stdout": stdout,
            "stderr": stderr,
            "returncode": result.returncode,
        }


class BrowserAutomationTool:
    """Direct browser automation through worker-core/browser-use."""

    def __init__(self, timeout: int = 300):
        self.bridge = WorkerCoreBridge(timeout=timeout)

    def execute(self, task: str, config_path: Optional[str] = None) -> dict[str, Any]:
        return self.bridge.run_script(
            script_relative_path="scripts/run_browser_task.py",
            task=task,
            allowlist=_merge_allowlist("browser"),
            config_path=config_path,
        )


class WindowsAutomationTool:
    """Direct Windows desktop automation through worker-core/windows-use."""

    def __init__(self, timeout: int = 300):
        self.bridge = WorkerCoreBridge(timeout=timeout)

    def execute(self, task: str, config_path: Optional[str] = None) -> dict[str, Any]:
        return self.bridge.run_script(
            script_relative_path="scripts/run_windows_task.py",
            task=task,
            allowlist=_merge_allowlist("windows"),
            config_path=config_path,
        )


class WorkerOrchestratorTool:
    """
    Full worker-core orchestration with files/data/browser/windows available.
    Useful when a CLI agent wants the worker-core planner, not only direct adapters.
    """

    def __init__(self, timeout: int = 300):
        self.bridge = WorkerCoreBridge(timeout=timeout)

    def execute(self, task: str, config_path: Optional[str] = None) -> dict[str, Any]:
        return self.bridge.run_script(
            script_relative_path="scripts/run_worker_task.py",
            task=task,
            allowlist=_merge_allowlist("browser", "windows"),
            config_path=config_path,
        )
