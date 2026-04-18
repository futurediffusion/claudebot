"""
Shared desktop world model for Claude, Gemini, Codex, and wrapper CLIs.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

try:
    from core.automation_detection import detect_automation_route
except ImportError:
    from .automation_detection import detect_automation_route


ROOT_DIR = Path(__file__).resolve().parents[2]
WORKER_CORE_ROOT = ROOT_DIR / "tools" / "worker-core"
WORLD_MODEL_DIR = ROOT_DIR / "world_model"
WORLD_MODEL_STATE = WORLD_MODEL_DIR / "state.json"

DEFAULT_WORLD_MODEL: dict[str, Any] = {
    "version": 1,
    "last_updated": None,
    "desktop": {
        "active_window": {},
        "open_apps": [],
    },
    "browser": {
        "tabs": [],
        "active_tab": {},
    },
    "filesystem": {
        "recent_files": [],
        "created_files": [],
        "downloads_in_progress": [],
    },
    "tasks": {
        "active_task": None,
        "recent_tasks": [],
        "objectives": [],
    },
}


class WorldModelEngine:
    """Maintain a shared operational model of the desktop and task state."""

    APP_ALIASES = {
        "chrome": ["chrome", "google chrome"],
        "edge": ["edge", "microsoft edge", "msedge"],
        "firefox": ["firefox"],
        "notepad": ["notepad", "bloc de notas"],
        "explorer": ["file explorer", "explorer", "explorador"],
        "powershell": ["powershell"],
        "terminal": ["terminal", "cmd", "command prompt"],
        "vscode": ["vscode", "visual studio code", "vs code"],
        "paint": ["paint", "mspaint"],
        "calculator": ["calculator", "calculadora"],
    }

    BROWSER_PROCESSES = {"chrome", "msedge", "edge", "firefox", "browser"}
    OBJECTIVE_SPLIT_PATTERN = re.compile(
        r"\b(?:and then|then|and|y luego|luego|despues|después)\b",
        flags=re.IGNORECASE,
    )
    FILE_PATTERN = re.compile(
        r"(?:[A-Za-z]:[\\/][^\s\"']+|(?:tasks|playbooks|logs|memory|output|downloads)[\\/][^\s\"']+|(?:[\w.-]+[\\/])+[\w .-]+\.[A-Za-z0-9]{1,10})"
    )

    def __init__(self, agent_name: str = "claude_code", base_dir: Optional[Path] = None):
        self.agent_name = agent_name
        self.base_dir = Path(base_dir) if base_dir else WORLD_MODEL_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.base_dir / WORLD_MODEL_STATE.name
        self._ensure_state_file()

    def get_state(self, refresh: bool = False) -> dict[str, Any]:
        if refresh:
            return self.observe_desktop()
        return self._load_state()

    def get_summary(self, refresh: bool = False) -> dict[str, Any]:
        state = self.get_state(refresh=refresh)
        return {
            "agent": self.agent_name,
            "world_model_dir": str(self.base_dir),
            "active_window": state["desktop"].get("active_window", {}),
            "open_app_count": len(state["desktop"].get("open_apps", [])),
            "tracked_tabs": len(state["browser"].get("tabs", [])),
            "tracked_files": len(state["filesystem"].get("recent_files", [])),
            "downloads_in_progress": state["filesystem"].get("downloads_in_progress", [])[:5],
            "active_task": state["tasks"].get("active_task"),
            "pending_objectives": [
                item for item in state["tasks"].get("objectives", [])
                if item.get("status") not in {"completed"}
            ][:5],
            "recent_tasks": state["tasks"].get("recent_tasks", [])[:5],
        }

    def observe_desktop(self) -> dict[str, Any]:
        """Refresh open apps, active window, and download status from the local desktop."""
        state = self._load_state()
        snapshot = self._collect_desktop_snapshot()
        desktop = state.setdefault("desktop", {})
        filesystem = state.setdefault("filesystem", {})

        desktop["active_window"] = snapshot.get("active_window", {})
        desktop["open_apps"] = snapshot.get("open_apps", [])
        filesystem["downloads_in_progress"] = snapshot.get("downloads_in_progress", [])
        state["last_updated"] = self._timestamp()
        self._write_state(state)
        return state

    def build_context_brief(
        self,
        task: str,
        task_type: Optional[str] = None,
        refresh: bool = True,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Return a compact task-relevant slice of the world model."""
        state = self.get_state(refresh=refresh)
        task_tokens = self._tokenize(task)
        relevant_apps = self._rank_relevant_apps(state["desktop"].get("open_apps", []), task_tokens)
        relevant_tabs = self._rank_relevant_tabs(state["browser"].get("tabs", []), task_tokens, task, task_type)
        relevant_files = self._rank_relevant_files(state["filesystem"].get("recent_files", []), task_tokens, task)
        pending_objectives = self._rank_relevant_objectives(
            state["tasks"].get("objectives", []),
            task_tokens,
            task,
            task_type,
        )

        return {
            "task": self._trim(task, 240),
            "task_type": task_type,
            "active_window": state["desktop"].get("active_window", {}),
            "open_apps": relevant_apps[:limit] or state["desktop"].get("open_apps", [])[:limit],
            "tabs": relevant_tabs[:limit],
            "files": relevant_files[:limit],
            "downloads_in_progress": state["filesystem"].get("downloads_in_progress", [])[:limit],
            "active_task": state["tasks"].get("active_task"),
            "pending_objectives": pending_objectives[:limit],
        }

    def record_task_start(
        self,
        task: str,
        task_type: str,
        route: Optional[str] = None,
        model_name: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        refresh_desktop: bool = True,
    ) -> dict[str, Any]:
        """Mark a task as active in the shared world model."""
        metadata = metadata or {}
        active_agent_cli = str(metadata.get("active_agent_cli") or self.agent_name)
        state = self.get_state(refresh=refresh_desktop)
        route = route or detect_automation_route(task)
        task_key = self._task_key(task, task_type)
        related_urls = self._extract_urls(task)
        related_files = [item["path"] for item in self._extract_file_records(task, None, None, None)]

        state["tasks"]["active_task"] = {
            "task_key": task_key,
            "task": self._trim(task, 300),
            "task_type": task_type,
            "route": route,
            "model": model_name,
            "agent": self.agent_name,
            "active_agent_cli": active_agent_cli,
            "status": "running",
            "started_at": self._timestamp(),
        }

        for description in self._extract_objective_descriptions(task):
            objective_id = self._objective_id(task_key, description)
            self._upsert_objective(
                state,
                {
                    "id": objective_id,
                    "task_key": task_key,
                    "task": self._trim(task, 240),
                    "description": self._trim(description, 180),
                    "task_type": task_type,
                    "route": route,
                    "model": model_name,
                    "status": "running",
                    "error": None,
                    "related_urls": related_urls[:4],
                    "related_files": related_files[:6],
                    "agent": self.agent_name,
                    "active_agent_cli": active_agent_cli,
                    "last_seen": self._timestamp(),
                },
            )

        if related_urls:
            self._update_tabs(
                state=state,
                task=task,
                task_type=task_type,
                route=route,
                urls=related_urls,
                success=None,
            )

        state["last_updated"] = self._timestamp()
        self._write_state(state)
        return {"task_key": task_key, "route": route}

    def record_execution(
        self,
        task: str,
        task_type: str,
        success: bool,
        model_name: Optional[str] = None,
        route: Optional[str] = None,
        tools_used: Optional[list[str]] = None,
        response: Any = None,
        error: Optional[str] = None,
        tool_results: Optional[dict[str, Any]] = None,
        playbook_path: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        refresh_desktop: bool = True,
    ) -> dict[str, Any]:
        """Update the world model after an execution finishes."""
        state = self.get_state(refresh=refresh_desktop)
        route = route or detect_automation_route(task)
        task_key = self._task_key(task, task_type)
        tools_used = tools_used or []
        metadata = metadata or {}
        active_agent_cli = str(metadata.get("active_agent_cli") or self.agent_name)

        playbook = self._load_playbook(playbook_path)
        file_records = self._extract_file_records(task, response, tool_results, playbook)
        related_urls = self._extract_urls(
            " ".join(
                part
                for part in [
                    task,
                    self._coerce_text(response),
                    self._coerce_text(tool_results),
                    self._coerce_text(metadata),
                ]
                if part
            )
        )

        self._update_filesystem(state, task, task_type, file_records)
        if related_urls or route in {"browser", "worker"} or "browser" in tools_used:
            self._update_tabs(
                state=state,
                task=task,
                task_type=task_type,
                route=route,
                urls=related_urls,
                success=success,
            )

        self._update_objectives(
            state=state,
            task=task,
            task_type=task_type,
            task_key=task_key,
            success=success,
            error=error,
            route=route,
            model_name=model_name,
            playbook=playbook,
            file_records=file_records,
            related_urls=related_urls,
            active_agent_cli=active_agent_cli,
        )

        if state["tasks"].get("active_task", {}).get("task_key") == task_key:
            state["tasks"]["active_task"] = None

        recent_tasks = state["tasks"].setdefault("recent_tasks", [])
        recent_tasks.append(
            {
                "task_key": task_key,
                "task": self._trim(task, 220),
                "task_type": task_type,
                "route": route,
                "model": model_name,
                "success": success,
                "tools_used": tools_used,
                "agent": self.agent_name,
                "active_agent_cli": active_agent_cli,
                "last_seen": self._timestamp(),
                "error": self._trim(error, 180) if error else None,
            }
        )
        state["tasks"]["recent_tasks"] = recent_tasks[-20:]
        state["last_updated"] = self._timestamp()
        self._write_state(state)

        return {
            "task_key": task_key,
            "route": route,
            "touched_files": [item["path"] for item in file_records][:6],
            "urls": related_urls[:4],
            "pending_objectives": [
                item["description"]
                for item in state["tasks"].get("objectives", [])
                if item.get("status") not in {"completed"}
            ][:6],
        }

    def _ensure_state_file(self) -> None:
        if self.state_path.exists():
            current = self._read_json(self.state_path)
            merged = self._merge_with_defaults(DEFAULT_WORLD_MODEL, current)
            if merged != current:
                self._write_json(self.state_path, merged)
            return
        self._write_json(self.state_path, copy.deepcopy(DEFAULT_WORLD_MODEL))

    def _load_state(self) -> dict[str, Any]:
        return self._read_json(self.state_path)

    def _write_state(self, state: dict[str, Any]) -> None:
        self._write_json(self.state_path, state)

    def _read_json(self, path: Path) -> dict[str, Any]:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_suffix(path.suffix + ".tmp")
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        temp_path.replace(path)

    def _merge_with_defaults(self, defaults: dict[str, Any], current: Any) -> Any:
        if not isinstance(defaults, dict) or not isinstance(current, dict):
            return current if current is not None else copy.deepcopy(defaults)
        merged = copy.deepcopy(defaults)
        for key, value in current.items():
            if key in merged:
                merged[key] = self._merge_with_defaults(merged[key], value)
            else:
                merged[key] = value
        return merged

    def _collect_desktop_snapshot(self) -> dict[str, Any]:
        return {
            "active_window": self._collect_active_window(),
            "open_apps": self._collect_open_apps(),
            "downloads_in_progress": self._collect_downloads_in_progress(),
        }

    def _collect_active_window(self) -> dict[str, Any]:
        script = r"""
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class Win32Native {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
}
"@;
$hwnd = [Win32Native]::GetForegroundWindow()
if ($hwnd -eq [IntPtr]::Zero) { "{}"; exit 0 }
$pid = 0
[Win32Native]::GetWindowThreadProcessId($hwnd, [ref]$pid) | Out-Null
$titleBuilder = New-Object System.Text.StringBuilder 1024
[Win32Native]::GetWindowText($hwnd, $titleBuilder, $titleBuilder.Capacity) | Out-Null
$proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
[pscustomobject]@{
    title = $titleBuilder.ToString()
    process_name = if ($proc) { $proc.ProcessName } else { $null }
    pid = $pid
} | ConvertTo-Json -Compress
"""
        return self._run_powershell_json(script, expect_list=False)

    def _collect_open_apps(self) -> list[dict[str, Any]]:
        script = r"""
Get-Process |
    Where-Object { $_.MainWindowTitle -and $_.MainWindowTitle.Trim() -ne "" } |
    Sort-Object ProcessName |
    Select-Object -First 20 @{
        Name = "process_name"; Expression = { $_.ProcessName }
    }, @{
        Name = "title"; Expression = { $_.MainWindowTitle }
    }, @{
        Name = "pid"; Expression = { $_.Id }
    } |
    ConvertTo-Json -Compress
"""
        data = self._run_powershell_json(script, expect_list=True)
        return data if isinstance(data, list) else []

    def _collect_downloads_in_progress(self) -> list[dict[str, Any]]:
        script = r"""
$downloads = Join-Path $env:USERPROFILE "Downloads"
Get-ChildItem -Path $downloads -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '\.(crdownload|part|partial|download|tmp)$' } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 20 @{
        Name = "name"; Expression = { $_.Name }
    }, @{
        Name = "path"; Expression = { $_.FullName }
    }, @{
        Name = "size_bytes"; Expression = { $_.Length }
    }, @{
        Name = "last_write_time"; Expression = { $_.LastWriteTime.ToString("o") }
    } |
    ConvertTo-Json -Compress
"""
        data = self._run_powershell_json(script, expect_list=True)
        return data if isinstance(data, list) else []

    def _run_powershell_json(self, script: str, expect_list: bool) -> Any:
        if os.name != "nt":
            return [] if expect_list else {}

        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                capture_output=True,
                text=True,
                timeout=4,
                check=False,
            )
        except Exception:
            return [] if expect_list else {}

        stdout = result.stdout.strip()
        if result.returncode != 0 or not stdout:
            return [] if expect_list else {}

        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            return [] if expect_list else {}

        if expect_list:
            if isinstance(payload, list):
                return payload
            if isinstance(payload, dict):
                return [payload]
            return []
        if isinstance(payload, list):
            return payload[0] if payload else {}
        return payload if isinstance(payload, dict) else {}

    def _rank_relevant_apps(self, open_apps: list[dict[str, Any]], task_tokens: set[str]) -> list[dict[str, Any]]:
        ranked = []
        for app in open_apps:
            haystack = " ".join(
                [
                    str(app.get("process_name", "")),
                    str(app.get("title", "")),
                ]
            ).lower()
            score = len(task_tokens & self._tokenize(haystack))
            if score or self._matches_known_app(haystack, task_tokens):
                ranked.append((score + 1, app))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in ranked]

    def _rank_relevant_tabs(
        self,
        tabs: list[dict[str, Any]],
        task_tokens: set[str],
        task: str,
        task_type: Optional[str],
    ) -> list[dict[str, Any]]:
        del task
        ranked = []
        for tab in tabs:
            haystack = " ".join(
                [
                    str(tab.get("url", "")),
                    str(tab.get("domain", "")),
                    str(tab.get("task", "")),
                    str(tab.get("task_type", "")),
                ]
            )
            score = len(task_tokens & self._tokenize(haystack))
            if task_type and tab.get("task_type") == task_type:
                score += 2
            if score:
                ranked.append((score, tab))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in ranked]

    def _rank_relevant_files(
        self,
        files: list[dict[str, Any]],
        task_tokens: set[str],
        task: str,
    ) -> list[dict[str, Any]]:
        del task
        ranked = []
        for record in files:
            haystack = " ".join(
                [
                    str(record.get("path", "")),
                    str(record.get("task", "")),
                    str(record.get("status", "")),
                ]
            )
            score = len(task_tokens & self._tokenize(haystack))
            if score:
                ranked.append((score, record))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in ranked]

    def _rank_relevant_objectives(
        self,
        objectives: list[dict[str, Any]],
        task_tokens: set[str],
        task: str,
        task_type: Optional[str],
    ) -> list[dict[str, Any]]:
        del task
        ranked = []
        for objective in objectives:
            if objective.get("status") == "completed":
                continue
            haystack = " ".join(
                [
                    str(objective.get("task", "")),
                    str(objective.get("description", "")),
                    str(objective.get("task_type", "")),
                ]
            )
            score = len(task_tokens & self._tokenize(haystack))
            if task_type and objective.get("task_type") == task_type:
                score += 2
            if score:
                ranked.append((score, objective))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in ranked] or [
            item for item in objectives if item.get("status") != "completed"
        ][:5]

    def _matches_known_app(self, haystack: str, task_tokens: set[str]) -> bool:
        for aliases in self.APP_ALIASES.values():
            if any(alias in haystack for alias in aliases):
                alias_tokens = set()
                for alias in aliases:
                    alias_tokens |= self._tokenize(alias)
                if task_tokens & alias_tokens:
                    return True
        return False

    def _update_tabs(
        self,
        state: dict[str, Any],
        task: str,
        task_type: str,
        route: Optional[str],
        urls: list[str],
        success: Optional[bool],
    ) -> None:
        tabs = state["browser"].setdefault("tabs", [])
        status = "planned" if success is None else ("ready" if success else "error")
        for url in urls:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            tab_id = hashlib.sha1(f"{url}|{task_type}".encode("utf-8")).hexdigest()[:10]
            entry = {
                "id": tab_id,
                "url": url,
                "domain": domain,
                "task": self._trim(task, 220),
                "task_type": task_type,
                "route": route,
                "status": status,
                "agent": self.agent_name,
                "last_seen": self._timestamp(),
            }
            self._upsert_record(tabs, entry, "id")
            if status in {"planned", "ready"}:
                state["browser"]["active_tab"] = entry
        state["browser"]["tabs"] = tabs[-30:]

    def _update_filesystem(
        self,
        state: dict[str, Any],
        task: str,
        task_type: str,
        file_records: list[dict[str, Any]],
    ) -> None:
        filesystem = state.setdefault("filesystem", {})
        recent_files = filesystem.setdefault("recent_files", [])
        created_files = filesystem.setdefault("created_files", [])

        for record in file_records:
            entry = {
                "path": record["path"],
                "status": record.get("status", "touched"),
                "task": self._trim(task, 220),
                "task_type": task_type,
                "exists": record.get("exists"),
                "agent": self.agent_name,
                "last_seen": self._timestamp(),
            }
            self._upsert_record(recent_files, entry, "path")
            if entry["status"] in {"created", "copied", "moved", "summarized", "json_written"}:
                self._upsert_record(created_files, entry, "path")

        filesystem["recent_files"] = recent_files[-40:]
        filesystem["created_files"] = created_files[-20:]

    def _update_objectives(
        self,
        state: dict[str, Any],
        task: str,
        task_type: str,
        task_key: str,
        success: bool,
        error: Optional[str],
        route: Optional[str],
        model_name: Optional[str],
        playbook: Optional[dict[str, Any]],
        file_records: list[dict[str, Any]],
        related_urls: list[str],
        active_agent_cli: str,
    ) -> None:
        objectives = state["tasks"].setdefault("objectives", [])
        related_files = [item["path"] for item in file_records][:6]

        if playbook:
            for subtask in playbook.get("subtasks", []):
                description = str(subtask.get("description") or f"Subtask {subtask.get('index')}")
                objective = {
                    "id": self._objective_id(task_key, description, subtask.get("index")),
                    "task_key": task_key,
                    "task": self._trim(task, 220),
                    "description": self._trim(description, 180),
                    "task_type": task_type,
                    "route": route or subtask.get("adapter"),
                    "model": model_name,
                    "status": self._playbook_status_to_world_status(subtask.get("status")),
                    "error": self._trim(subtask.get("error"), 180) if subtask.get("error") else None,
                    "related_urls": related_urls[:4],
                    "related_files": self._files_from_subtask(subtask) or related_files,
                    "agent": self.agent_name,
                    "active_agent_cli": active_agent_cli,
                    "last_seen": self._timestamp(),
                }
                self._upsert_objective(state, objective)

        top_status = "completed" if success else "blocked"
        for description in self._extract_objective_descriptions(task):
            objective = {
                "id": self._objective_id(task_key, description),
                "task_key": task_key,
                "task": self._trim(task, 220),
                "description": self._trim(description, 180),
                "task_type": task_type,
                "route": route,
                "model": model_name,
                "status": top_status,
                "error": self._trim(error, 180) if error else None,
                "related_urls": related_urls[:4],
                "related_files": related_files,
                "agent": self.agent_name,
                "active_agent_cli": active_agent_cli,
                "last_seen": self._timestamp(),
            }
            self._upsert_objective(state, objective)

        state["tasks"]["objectives"] = objectives[-50:]

    def _upsert_objective(self, state: dict[str, Any], objective: dict[str, Any]) -> None:
        objectives = state["tasks"].setdefault("objectives", [])
        self._upsert_record(objectives, objective, "id")

    def _upsert_record(self, records: list[dict[str, Any]], entry: dict[str, Any], key: str) -> None:
        for index, record in enumerate(records):
            if record.get(key) == entry.get(key):
                records[index] = {**record, **entry}
                return
        records.append(entry)

    def _extract_file_records(
        self,
        task: str,
        response: Any,
        tool_results: Optional[dict[str, Any]],
        playbook: Optional[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        seen: set[str] = set()

        def add_record(path_value: str, status: str) -> None:
            normalized = self._normalize_path(path_value)
            if "://" in normalized:
                return
            if not normalized or normalized in seen:
                return
            resolved = self._resolve_candidate_path(normalized)
            seen.add(normalized)
            records.append(
                {
                    "path": normalized,
                    "absolute_path": str(resolved) if resolved else None,
                    "status": status,
                    "exists": resolved.exists() if resolved else None,
                }
            )

        for match in self.FILE_PATTERN.findall(task):
            add_record(match, "mentioned")

        if response:
            for match in self.FILE_PATTERN.findall(self._coerce_text(response)):
                add_record(match, "touched")

        self._walk_for_paths(tool_results, add_record)

        if playbook:
            for subtask in playbook.get("subtasks", []):
                params = subtask.get("params") or {}
                adapter = subtask.get("adapter")
                op = (params.get("op") or "").lower()
                status = subtask.get("status")
                if status != "success":
                    write_status = "expected"
                elif op == "write":
                    write_status = "created"
                elif op == "copy":
                    write_status = "copied"
                elif op == "move":
                    write_status = "moved"
                elif op == "summarize":
                    write_status = "summarized"
                elif op == "write_json":
                    write_status = "json_written"
                else:
                    write_status = "touched"

                if adapter in {"files", "data"}:
                    for key in ("path", "dst", "src"):
                        value = params.get(key)
                        if isinstance(value, str):
                            add_record(value, write_status if key != "src" else "read")

        return records

    def _walk_for_paths(self, value: Any, add_record) -> None:
        if value is None:
            return
        if isinstance(value, str):
            for match in self.FILE_PATTERN.findall(value):
                add_record(match, "touched")
            return
        if isinstance(value, list):
            for item in value[:20]:
                self._walk_for_paths(item, add_record)
            return
        if isinstance(value, dict):
            for key, item in list(value.items())[:25]:
                if key in {"path", "src", "dst", "playbook", "file", "filepath"} and isinstance(item, str):
                    inferred = "touched" if key != "playbook" else "playbook"
                    add_record(item, inferred)
                else:
                    self._walk_for_paths(item, add_record)

    def _extract_urls(self, text: str) -> list[str]:
        urls = []
        for match in re.findall(r"https?://[^\s\"'<>]+", text):
            if match not in urls:
                urls.append(match)
        return urls

    def _extract_objective_descriptions(self, task: str) -> list[str]:
        parts = [
            part.strip(" ,.;:")
            for part in self.OBJECTIVE_SPLIT_PATTERN.split(task)
            if part and part.strip(" ,.;:")
        ]
        return parts or [task]

    def _load_playbook(self, playbook_path: Optional[str]) -> Optional[dict[str, Any]]:
        if not playbook_path:
            return None
        path = Path(playbook_path)
        if not path.is_absolute():
            path = WORKER_CORE_ROOT / path
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError):
            return None

    def _files_from_subtask(self, subtask: dict[str, Any]) -> list[str]:
        params = subtask.get("params") or {}
        files = []
        for key in ("path", "src", "dst"):
            value = params.get(key)
            if isinstance(value, str) and value not in files:
                files.append(value)
        return files[:6]

    def _playbook_status_to_world_status(self, status: Optional[str]) -> str:
        mapping = {
            "success": "completed",
            "failed": "blocked",
            "pending": "pending",
            "running": "running",
            "retrying": "running",
        }
        return mapping.get((status or "").lower(), "pending")

    def _resolve_candidate_path(self, path_value: str) -> Optional[Path]:
        candidate = Path(path_value)
        if candidate.is_absolute():
            return candidate
        if path_value.startswith(("tasks/", "tasks\\", "playbooks/", "playbooks\\", "logs/", "logs\\")):
            return WORKER_CORE_ROOT / candidate
        return ROOT_DIR / candidate

    def _normalize_path(self, path_value: str) -> str:
        cleaned = path_value.strip().strip("\"'")
        return cleaned.replace("\\", "/")

    def _task_key(self, task: str, task_type: str) -> str:
        digest = hashlib.sha1(f"{task_type}|{task}".encode("utf-8")).hexdigest()
        return digest[:12]

    def _objective_id(self, task_key: str, description: str, index: Optional[Any] = None) -> str:
        seed = f"{task_key}|{index}|{description}"
        return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]

    def _tokenize(self, text: str) -> set[str]:
        tokens = set()
        for token in re.findall(r"[a-z0-9_:/.-]{3,}", text.lower()):
            tokens.add(token)
        return tokens

    def _coerce_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        try:
            return json.dumps(value, ensure_ascii=False)
        except TypeError:
            return str(value)

    def _trim(self, value: Any, limit: int) -> Optional[str]:
        if value is None:
            return None
        text = str(value)
        if len(text) <= limit:
            return text
        return text[: max(limit - 3, 0)] + "..."

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()
