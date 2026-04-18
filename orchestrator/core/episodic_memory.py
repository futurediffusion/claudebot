"""
Shared episodic memory engine used across Claude, Gemini, Codex, and wrappers.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse
from uuid import uuid4

try:
    from core.automation_detection import detect_automation_route
except ImportError:
    from .automation_detection import detect_automation_route


ROOT_DIR = Path(__file__).resolve().parents[2]
EPISODIC_MEMORY_DIR = ROOT_DIR / "episodic_memory"
EPISODES_FILE = EPISODIC_MEMORY_DIR / "episodes.jsonl"


class EpisodicMemoryEngine:
    """Store and retrieve task episodes with operational context."""

    APP_KEYWORDS = {
        "chrome": ["chrome", "google chrome"],
        "edge": ["edge", "microsoft edge"],
        "firefox": ["firefox"],
        "notepad": ["notepad", "bloc de notas"],
        "file_explorer": ["file explorer", "explorer", "explorador"],
        "calculator": ["calculator", "calculadora"],
        "paint": ["paint", "mspaint"],
        "settings": ["settings", "configuracion", "configuration"],
        "powershell": ["powershell"],
        "terminal": ["terminal", "cmd.exe", "command prompt", "shell"],
        "vscode": ["vscode", "vs code", "visual studio code"],
        "browser": ["browser", "website", "web page", "page", "site"],
    }

    UI_KEYWORDS = [
        "screen",
        "window",
        "page",
        "tab",
        "dialog",
        "modal",
        "button",
        "menu",
        "form",
        "title",
        "sidebar",
        "panel",
        "login",
        "error",
        "warning",
    ]

    STOPWORDS = {
        "the",
        "and",
        "for",
        "with",
        "this",
        "that",
        "from",
        "into",
        "your",
        "then",
        "open",
        "abre",
        "para",
        "con",
        "una",
        "que",
        "por",
        "then",
        "task",
        "please",
    }

    def __init__(self, agent_name: str = "claude_code", base_dir: Optional[Path] = None):
        self.agent_name = agent_name
        self.base_dir = Path(base_dir) if base_dir else EPISODIC_MEMORY_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.episodes_file = self.base_dir / EPISODES_FILE.name

    def record_episode(
        self,
        task: str,
        task_type: str,
        success: bool,
        execution_time_ms: int,
        episode_type: str,
        model_name: Optional[str] = None,
        tools_used: Optional[list[str]] = None,
        steps: Optional[list[dict[str, Any]]] = None,
        response: Any = None,
        error: Optional[str] = None,
        tool_results: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
        log_id: Optional[str] = None,
        app_context: Optional[dict[str, Any]] = None,
        web_context: Optional[dict[str, Any]] = None,
        screen_context: Optional[dict[str, Any]] = None,
        failure: Optional[dict[str, Any]] = None,
        resolution: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Append a new operational episode to shared memory."""
        metadata = metadata or {}
        active_agent_cli = str(metadata.get("active_agent_cli") or self.agent_name)
        tools_used = tools_used or []
        route = metadata.get("automation_route") or detect_automation_route(task)
        combined_text = self._combine_text(task, response, error, tool_results, metadata)
        inferred_app = app_context or self._extract_app_context(task, combined_text, route, tools_used)
        inferred_web = web_context or self._extract_web_context(task, combined_text)
        inferred_screen = screen_context or self._extract_screen_context(task, combined_text, route)
        inferred_failure = failure or self._build_failure(error, steps, tool_results)
        inferred_resolution = resolution or self._build_resolution(
            success=success,
            route=route,
            model_name=model_name,
            metadata=metadata,
            tools_used=tools_used,
        )

        episode = {
            "id": str(uuid4())[:8],
            "timestamp": self._timestamp(),
            "agent": self.agent_name,
            "active_agent_cli": active_agent_cli,
            "episode_type": episode_type,
            "task": self._trim(task, 500),
            "task_type": task_type or "generic",
            "model": model_name,
            "success": success,
            "execution_time_ms": execution_time_ms,
            "tools_used": tools_used,
            "steps": self._sanitize(steps or []),
            "app_context": inferred_app,
            "web_context": inferred_web,
            "screen_context": inferred_screen,
            "failure": inferred_failure,
            "resolution": inferred_resolution,
            "artifacts": {
                "log_id": log_id,
                "response_excerpt": self._trim(self._coerce_text(response), 1200),
                "tool_result_excerpt": self._trim(self._coerce_text(tool_results), 1200),
                "metadata": self._sanitize(metadata),
            },
        }
        self._append_jsonl(self.episodes_file, episode)

        return {
            "id": episode["id"],
            "success": success,
            "task_type": episode["task_type"],
            "apps": episode["app_context"].get("apps", []),
            "domains": episode["web_context"].get("domains", []),
            "resolution": episode["resolution"].get("summary"),
        }

    def find_relevant_episodes(
        self,
        task: str,
        task_type: Optional[str] = None,
        limit: int = 3,
        search_window: int = 200,
    ) -> list[dict[str, Any]]:
        """Return recent episodes ranked by task and context similarity."""
        target_route = detect_automation_route(task)
        target_tokens = self._tokenize(task)
        target_apps = set(self._extract_app_context(task, task, target_route, []).get("apps", []))
        target_domains = set(self._extract_web_context(task, task).get("domains", []))

        ranked = []
        for episode in self._read_recent(search_window):
            score, reasons = self._score_episode(
                episode=episode,
                task_type=task_type,
                target_route=target_route,
                target_tokens=target_tokens,
                target_apps=target_apps,
                target_domains=target_domains,
            )
            if score <= 0:
                continue
            item = dict(episode)
            item["relevance_score"] = score
            item["match_reasons"] = reasons
            ranked.append(item)

        ranked.sort(
            key=lambda entry: (
                entry.get("relevance_score", 0),
                entry.get("timestamp", ""),
            ),
            reverse=True,
        )
        return ranked[:limit]

    def build_context_brief(
        self,
        task: str,
        task_type: Optional[str] = None,
        limit: int = 3,
    ) -> dict[str, Any]:
        """Return a compact memory brief suitable for model context injection."""
        matches = self.find_relevant_episodes(task=task, task_type=task_type, limit=limit)
        return {
            "task": self._trim(task, 240),
            "task_type": task_type,
            "matches": [self._compact_episode(match) for match in matches],
            "match_count": len(matches),
        }

    def get_summary(self, limit: int = 5) -> dict[str, Any]:
        """Return a high-level summary of stored episodes."""
        episodes = self._read_recent(500)
        recent = [self._compact_episode(item) for item in episodes[-limit:]]
        failures = [item for item in episodes if not item.get("success")]
        successes = [item for item in episodes if item.get("success")]
        return {
            "agent": self.agent_name,
            "episodic_memory_dir": str(self.base_dir),
            "total_episodes": len(episodes),
            "successful_episodes": len(successes),
            "failed_episodes": len(failures),
            "recent": recent,
        }

    def _score_episode(
        self,
        episode: dict[str, Any],
        task_type: Optional[str],
        target_route: Optional[str],
        target_tokens: set[str],
        target_apps: set[str],
        target_domains: set[str],
    ) -> tuple[int, list[str]]:
        score = 0
        reasons: list[str] = []

        if task_type and episode.get("task_type") == task_type:
            score += 8
            reasons.append("same_task_type")

        episode_route = episode.get("app_context", {}).get("route")
        if target_route and episode_route == target_route:
            score += 6
            reasons.append("same_route")

        episode_apps = set(episode.get("app_context", {}).get("apps", []))
        shared_apps = sorted(target_apps & episode_apps)
        if shared_apps:
            score += 4 * len(shared_apps)
            reasons.append(f"apps:{','.join(shared_apps[:3])}")

        episode_domains = set(episode.get("web_context", {}).get("domains", []))
        shared_domains = sorted(target_domains & episode_domains)
        if shared_domains:
            score += 5 * len(shared_domains)
            reasons.append(f"domains:{','.join(shared_domains[:2])}")

        episode_tokens = self._tokenize(
            " ".join(
                [
                    str(episode.get("task", "")),
                    str((episode.get("failure") or {}).get("message", "")),
                    str((episode.get("resolution") or {}).get("summary", "")),
                ]
            )
        )
        shared_tokens = sorted(target_tokens & episode_tokens)
        if shared_tokens:
            token_score = min(len(shared_tokens), 6)
            score += token_score
            reasons.append(f"tokens:{','.join(shared_tokens[:4])}")

        if episode.get("success") and episode.get("resolution", {}).get("summary"):
            score += 2
            reasons.append("has_working_resolution")
        if not episode.get("success") and episode.get("failure", {}).get("message"):
            score += 1
            reasons.append("has_failure_signature")

        return score, reasons

    def _compact_episode(self, episode: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": episode.get("id"),
            "timestamp": episode.get("timestamp"),
            "agent": episode.get("agent"),
            "task": self._trim(episode.get("task"), 180),
            "task_type": episode.get("task_type"),
            "model": episode.get("model"),
            "success": episode.get("success"),
            "apps": episode.get("app_context", {}).get("apps", []),
            "domains": episode.get("web_context", {}).get("domains", []),
            "failure": self._trim((episode.get("failure") or {}).get("message"), 160),
            "resolution": self._trim((episode.get("resolution") or {}).get("summary"), 160),
            "steps": episode.get("steps", [])[:3],
            "relevance_score": episode.get("relevance_score"),
            "match_reasons": episode.get("match_reasons", []),
        }

    def _extract_app_context(
        self,
        task: str,
        combined_text: str,
        route: Optional[str],
        tools_used: list[str],
    ) -> dict[str, Any]:
        normalized = combined_text.lower()
        apps = []
        for app_name, keywords in self.APP_KEYWORDS.items():
            if any(keyword in normalized for keyword in keywords) and app_name not in apps:
                apps.append(app_name)

        if route == "browser" and "browser" not in apps:
            apps.append("browser")
        if route == "windows" and not apps:
            apps.append("desktop")
        if route == "worker" and "worker_core" not in apps:
            apps.append("worker_core")
        for tool_name in tools_used:
            bridge_name = f"{tool_name}_tool"
            if bridge_name not in apps and tool_name in {"browser", "windows", "worker"}:
                apps.append(bridge_name)

        return {
            "route": route,
            "apps": apps,
            "task_excerpt": self._trim(task, 200),
        }

    def _extract_web_context(self, task: str, combined_text: str) -> dict[str, Any]:
        urls = self._extract_urls(" ".join([task, combined_text]))
        domains = []
        for url in urls:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain and domain not in domains:
                domains.append(domain)
        return {"urls": urls[:5], "domains": domains[:5]}

    def _extract_screen_context(
        self,
        task: str,
        combined_text: str,
        route: Optional[str],
    ) -> dict[str, Any]:
        surface = "code"
        if route == "browser":
            surface = "browser"
        elif route == "windows":
            surface = "desktop"
        elif route == "worker":
            surface = "automation"

        normalized = combined_text.lower()
        ui_terms = [term for term in self.UI_KEYWORDS if term in normalized]
        observed_lines = []
        for line in self._coerce_text(combined_text).splitlines():
            stripped = line.strip()
            if stripped and any(term in stripped.lower() for term in self.UI_KEYWORDS):
                observed_lines.append(self._trim(stripped, 120))
            if len(observed_lines) >= 4:
                break

        if not observed_lines and task:
            observed_lines.append(self._trim(task, 120))

        return {
            "surface": surface,
            "ui_terms": ui_terms[:6],
            "observed_text": observed_lines[:4],
        }

    def _build_failure(
        self,
        error: Optional[str],
        steps: Optional[list[dict[str, Any]]],
        tool_results: Optional[dict[str, Any]],
    ) -> Optional[dict[str, Any]]:
        failed_step = None
        for step in reversed(steps or []):
            if step.get("status") == "failed":
                failed_step = step.get("stage")
                break

        if not error and not failed_step:
            return None

        tool_error = None
        stderr = None
        if isinstance(tool_results, dict):
            for result in tool_results.values():
                if isinstance(result, dict) and result.get("error"):
                    tool_error = result.get("error")
                    stderr = result.get("stderr")
                    break

        message = error or tool_error
        return {
            "message": self._trim(message, 500),
            "failed_step": failed_step,
            "stderr": self._trim(stderr, 500) if stderr else None,
            "signature": self._failure_signature(message or failed_step or "unknown_failure"),
        }

    def _build_resolution(
        self,
        success: bool,
        route: Optional[str],
        model_name: Optional[str],
        metadata: dict[str, Any],
        tools_used: list[str],
    ) -> dict[str, Any]:
        if not success:
            return {
                "status": "unresolved",
                "summary": "No working fix recorded in this episode.",
                "actions": [],
            }

        actions = []
        if metadata.get("used_fallback"):
            actions.append("runtime_fallback")
        follow_up = metadata.get("follow_up") or {}
        if follow_up.get("model"):
            actions.append(f"follow_up:{follow_up['model']}")
        if route:
            actions.append(f"route:{route}")
        if tools_used:
            actions.extend(f"tool:{tool}" for tool in tools_used)
        if not actions and model_name:
            actions.append(f"model:{model_name}")

        if metadata.get("used_fallback") and model_name:
            summary = f"Fallback route succeeded with {model_name}."
        elif follow_up.get("model"):
            summary = f"Primary output completed and follow-up validation used {follow_up['model']}."
        elif route:
            summary = f"Delegation through {route} automation completed successfully."
        elif model_name:
            summary = f"Primary execution path completed with {model_name}."
        else:
            summary = "Execution path completed successfully."

        return {
            "status": "resolved",
            "summary": summary,
            "actions": actions[:6],
        }

    def _read_recent(self, limit: int) -> list[dict[str, Any]]:
        if not self.episodes_file.exists():
            return []

        episodes = []
        with open(self.episodes_file, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    episodes.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return episodes[-limit:]

    def _append_jsonl(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _combine_text(
        self,
        task: str,
        response: Any,
        error: Optional[str],
        tool_results: Optional[dict[str, Any]],
        metadata: Optional[dict[str, Any]],
    ) -> str:
        return " ".join(
            value
            for value in [
                task,
                self._coerce_text(response),
                error or "",
                self._coerce_text(tool_results),
                self._coerce_text(metadata),
            ]
            if value
        )

    def _coerce_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        try:
            return json.dumps(value, ensure_ascii=False)
        except TypeError:
            return str(value)

    def _extract_urls(self, text: str) -> list[str]:
        urls = []
        for match in re.findall(r"https?://[^\s\"'<>]+", text):
            if match not in urls:
                urls.append(match)
        return urls

    def _tokenize(self, text: str) -> set[str]:
        tokens = set()
        for token in re.findall(r"[a-z0-9_:-]{3,}", text.lower()):
            if token in self.STOPWORDS:
                continue
            tokens.add(token)
        return tokens

    def _failure_signature(self, text: str) -> str:
        normalized = " ".join(text.lower().split())
        normalized = re.sub(r"[^a-z0-9 ]+", " ", normalized)
        return "_".join(normalized.split()[:8]) or "unknown_failure"

    def _sanitize(self, value: Any, depth: int = 0) -> Any:
        if depth > 3:
            return self._trim(self._coerce_text(value), 240)
        if value is None or isinstance(value, (bool, int, float)):
            return value
        if isinstance(value, str):
            return self._trim(value, 1000)
        if isinstance(value, list):
            return [self._sanitize(item, depth + 1) for item in value[:10]]
        if isinstance(value, dict):
            return {
                str(key): self._sanitize(item, depth + 1)
                for key, item in list(value.items())[:20]
            }
        return self._trim(str(value), 240)

    def _trim(self, value: Any, limit: int) -> Optional[str]:
        if value is None:
            return None
        text = str(value)
        if len(text) <= limit:
            return text
        return text[: max(limit - 3, 0)] + "..."

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()
