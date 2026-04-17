"""
Shared self-model engine used by Claude, Gemini, Codex, and wrapper CLIs.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

try:
    from core.automation_detection import detect_automation_route
except ImportError:
    from .automation_detection import detect_automation_route


ROOT_DIR = Path(__file__).resolve().parents[2]
SELF_MODEL_DIR = ROOT_DIR / "self_model"

DEFAULT_SELF_MODEL: dict[str, dict[str, Any]] = {
    "capabilities": {"version": 1, "models": {}, "agents": {}},
    "weaknesses": {
        "version": 1,
        "models": {},
        "agents": {},
        "update_rules": {
            "failure_threshold_for_avoid": 2,
            "success_threshold_for_preference": 3,
            "max_recent_decisions": 25,
            "max_failure_patterns": 50,
            "slow_ms_threshold": 90000,
        },
    },
    "routing_knowledge": {
        "version": 1,
        "task_preferences": {},
        "meta_strategies": {},
        "observed_stats": {},
        "recent_decisions": [],
    },
    "tool_map": {"version": 1, "tools": {}, "agent_tooling": {}},
    "failure_patterns": {"version": 1, "known_signatures": {}, "observed_patterns": {}},
}


class SelfModelEngine:
    """Maintain and apply a structured model of the system itself."""

    FILE_NAMES = {
        "capabilities": "capabilities.json",
        "weaknesses": "weaknesses.json",
        "routing_knowledge": "routing_knowledge.json",
        "tool_map": "tool_map.json",
        "failure_patterns": "failure_patterns.json",
    }

    TRAIT_KEYWORDS = {
        "planning": ["plan", "strategy", "approach", "how should"],
        "architecture": ["architecture", "design", "system design"],
        "fast_coding": ["implement", "create", "write", "modify", "fix", "code"],
        "heavy_refactor": ["refactor", "multi-file", "rewrite", "migrate", "redesign"],
        "validation": ["validate", "validation", "verify", "check"],
        "parsing": ["parse", "extract", "tokenize"],
        "formatting": ["format", "pretty print", "normalize"],
        "classification": ["classify", "categorize", "label"],
        "json": ["json", "schema"],
        "vision": ["screenshot", "screen", "image", "visual", "ui"],
        "browser_automation": ["browser", "chrome", "edge", "website", "url", "navigate", "web"],
        "windows_automation": ["notepad", "paint", "calculator", "desktop", "windows", "explorer"],
        "worker_automation": ["save", "summary", "output", "tasks/output", "report"],
        "file_edit": ["replace", "exact text", "surgical edit", "swap text"],
        "debugging": ["bug", "error", "traceback", "stack trace", "debug"],
        "test": ["test", "spec", "assert"],
    }

    def __init__(self, agent_name: str = "claude_code", base_dir: Optional[Path] = None):
        self.agent_name = agent_name
        self.base_dir = Path(base_dir) if base_dir else SELF_MODEL_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_files()

    def snapshot(self) -> dict[str, Any]:
        return self._load_bundle()

    def get_summary(self, top_patterns: int = 5) -> dict[str, Any]:
        bundle = self._load_bundle()
        failures = bundle["failure_patterns"]["observed_patterns"]
        sorted_patterns = sorted(
            failures.values(),
            key=lambda entry: entry.get("count", 0),
            reverse=True,
        )
        return {
            "agent": self.agent_name,
            "self_model_dir": str(self.base_dir),
            "known_models": sorted(bundle["capabilities"]["models"].keys()),
            "known_agents": sorted(bundle["capabilities"]["agents"].keys()),
            "recent_decisions": bundle["routing_knowledge"].get("recent_decisions", [])[-5:],
            "top_failure_patterns": sorted_patterns[:top_patterns],
        }

    def build_execution_brief(
        self,
        task: str,
        task_type: str,
        selected_model: str,
        decision: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        bundle = self._load_bundle()
        capabilities = bundle["capabilities"]["models"].get(selected_model, {})
        weaknesses = bundle["weaknesses"]["models"].get(selected_model, {})
        return {
            "task": task,
            "task_type": task_type,
            "agent": self.agent_name,
            "selected_model": selected_model,
            "task_traits": sorted(self._task_traits(task, task_type)),
            "strengths": capabilities.get("strengths", [])[:4],
            "watchouts": weaknesses.get("avoid_for", [])[:4],
            "critic_notes": (decision or {}).get("critic_notes", [])[:3],
        }

    def plan_for_task(
        self,
        task: str,
        task_type: Optional[str] = None,
        default_model: Optional[str] = None,
        candidate_models: Optional[Iterable[str]] = None,
    ) -> dict[str, Any]:
        automation_route = detect_automation_route(task)
        if automation_route:
            return {
                "mode": "automation",
                "route": automation_route,
                "tool_plan": self.suggest_tool(task),
            }
        if task_type and default_model:
            return {
                "mode": "model",
                "routing_plan": self.simulate_routing(
                    task=task,
                    task_type=task_type,
                    default_model=default_model,
                    candidate_models=candidate_models,
                ),
            }
        return {
            "mode": "generic",
            "task_traits": sorted(self._task_traits(task, task_type)),
        }

    def simulate_routing(
        self,
        task: str,
        task_type: str,
        default_model: str,
        candidate_models: Optional[Iterable[str]] = None,
    ) -> dict[str, Any]:
        bundle = self._load_bundle()
        candidates = self._unique_values(candidate_models or [default_model])
        if default_model not in candidates:
            candidates.insert(0, default_model)

        task_traits = self._task_traits(task, task_type)
        scored_options = [
            self._score_model_candidate(bundle, task_type, task_traits, default_model, model_name)
            for model_name in candidates
        ]
        scored_options.sort(key=lambda entry: (entry["score"], entry["model"]), reverse=True)
        selected = scored_options[0] if scored_options else {
            "model": default_model,
            "score": 0,
            "reasons": ["No candidates were available."],
        }

        critic_notes = []
        if selected["model"] != default_model:
            critic_notes.append(
                f"Self-model override: '{selected['model']}' scored higher than registry default '{default_model}'."
            )
        for reason in selected.get("reasons", []):
            if "avoid" in reason.lower() or "failure" in reason.lower():
                critic_notes.append(f"Internal critic: {reason}")

        agent_profile = bundle["capabilities"]["agents"].get(self.agent_name, {})
        return {
            "agent": self.agent_name,
            "task_type": task_type,
            "task_traits": sorted(task_traits),
            "default_model": default_model,
            "selected_model": selected["model"],
            "critic_notes": critic_notes[:3],
            "strategy": self._pick_strategy(bundle, task, task_type),
            "agent_profile": {
                "strengths": agent_profile.get("strengths", [])[:3],
                "best_for": agent_profile.get("best_for", [])[:3],
            },
            "ranked_options": [
                {
                    "model": option["model"],
                    "score": option["score"],
                    "reasons": option["reasons"][:4],
                }
                for option in scored_options[:5]
            ],
        }

    def suggest_tool(
        self,
        task: str,
        available_tools: Optional[Iterable[str]] = None,
    ) -> dict[str, Any]:
        bundle = self._load_bundle()
        default_tool = self._default_tool_for_task(task)
        candidates = list(available_tools or ["browser", "windows", "worker", "surgical_edit"])
        if default_tool and default_tool not in candidates:
            candidates.insert(0, default_tool)

        task_type = self._tool_task_type(task)
        task_traits = self._task_traits(task, task_type)
        scored_options = [
            self._score_tool_candidate(bundle, task_traits, default_tool, tool_name)
            for tool_name in self._unique_values(candidates)
        ]
        scored_options.sort(key=lambda entry: (entry["score"], entry["tool"]), reverse=True)
        selected = scored_options[0] if scored_options else {
            "tool": default_tool or "worker",
            "score": 0,
            "reasons": ["No tool candidates were available."],
        }

        critic_notes = []
        if default_tool and selected["tool"] != default_tool:
            critic_notes.append(
                f"Self-model override: '{selected['tool']}' scored higher than detected default '{default_tool}'."
            )

        return {
            "agent": self.agent_name,
            "task_type": task_type,
            "task_traits": sorted(task_traits),
            "default_tool": default_tool,
            "selected_tool": selected["tool"],
            "critic_notes": critic_notes[:3],
            "ranked_tools": [
                {
                    "tool": option["tool"],
                    "score": option["score"],
                    "reasons": option["reasons"][:4],
                }
                for option in scored_options[:4]
            ],
        }

    def record_execution(
        self,
        task: str,
        task_type: str,
        model_name: str,
        success: bool,
        execution_time_ms: int,
        error: Optional[str] = None,
        tools_used: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        decision_simulation: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        bundle = self._load_bundle()
        routing = bundle["routing_knowledge"]
        weaknesses = bundle["weaknesses"]
        capabilities = bundle["capabilities"]
        tool_map = bundle["tool_map"]
        failure_patterns = bundle["failure_patterns"]
        task_type = task_type or "generic"
        tools_used = tools_used or []

        model_stats = (
            routing.setdefault("observed_stats", {})
            .setdefault(model_name, {})
            .setdefault(task_type, {
                "runs": 0,
                "successes": 0,
                "failures": 0,
                "avg_time_ms": 0,
                "last_agent": self.agent_name,
                "last_used": None,
                "last_error": None,
            })
        )

        model_stats["runs"] += 1
        if success:
            model_stats["successes"] += 1
        else:
            model_stats["failures"] += 1

        previous_runs = max(model_stats["runs"] - 1, 0)
        previous_average = model_stats.get("avg_time_ms", 0)
        model_stats["avg_time_ms"] = int(
            ((previous_average * previous_runs) + execution_time_ms) / max(model_stats["runs"], 1)
        )
        model_stats["last_agent"] = self.agent_name
        model_stats["last_used"] = self._timestamp()
        model_stats["last_error"] = self._trim(error, 200) if error else None

        for tool_name in tools_used:
            self._update_tool_stats(tool_map, tool_name, success, error)

        pattern_key = None
        if not success or error:
            pattern_key = self._record_failure_pattern(
                failure_patterns=failure_patterns,
                model_name=model_name,
                task_type=task_type,
                error=error,
            )

        self._apply_learning_rules(
            capabilities=capabilities,
            weaknesses=weaknesses,
            routing=routing,
            model_name=model_name,
            task_type=task_type,
            stats=model_stats,
        )

        recent_decisions = routing.setdefault("recent_decisions", [])
        recent_decisions.append({
            "timestamp": self._timestamp(),
            "agent": self.agent_name,
            "task": self._trim(task, 160),
            "task_type": task_type,
            "model": model_name,
            "success": success,
            "execution_time_ms": execution_time_ms,
            "tools_used": tools_used,
            "pattern_key": pattern_key,
            "metadata": {
                "error": self._trim(error, 160) if error else None,
                "decision": self._compact_decision(decision_simulation),
                "extra": metadata or {},
            },
        })

        max_recent = weaknesses.get("update_rules", {}).get("max_recent_decisions", 25)
        routing["recent_decisions"] = recent_decisions[-max_recent:]
        self._write_bundle(bundle)

        return {
            "model": model_name,
            "task_type": task_type,
            "pattern_key": pattern_key,
            "stats": copy.deepcopy(model_stats),
        }

    def _ensure_files(self) -> None:
        for key, filename in self.FILE_NAMES.items():
            path = self.base_dir / filename
            if path.exists():
                current = self._read_json(path)
                merged = self._merge_with_defaults(DEFAULT_SELF_MODEL[key], current)
                if merged != current:
                    self._write_json(path, merged)
                continue
            self._write_json(path, copy.deepcopy(DEFAULT_SELF_MODEL[key]))

    def _load_bundle(self) -> dict[str, Any]:
        return {
            key: self._read_json(self.base_dir / filename)
            for key, filename in self.FILE_NAMES.items()
        }

    def _write_bundle(self, bundle: dict[str, Any]) -> None:
        for key, filename in self.FILE_NAMES.items():
            self._write_json(self.base_dir / filename, bundle[key])

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

    def _task_traits(self, task: str, task_type: Optional[str]) -> set[str]:
        normalized = " ".join(task.lower().split())
        traits: set[str] = set()
        if task_type:
            traits.add(task_type)
            if task_type.endswith("_automation"):
                traits.add("automation")

        automation_route = detect_automation_route(task)
        if automation_route:
            traits.add("automation")
            traits.add(f"{automation_route}_automation")

        for trait, keywords in self.TRAIT_KEYWORDS.items():
            if any(keyword in normalized for keyword in keywords):
                traits.add(trait)

        if " and " in normalized or " then " in normalized or " y luego " in normalized:
            traits.add("multi_step")
        return traits

    def _score_model_candidate(
        self,
        bundle: dict[str, Any],
        task_type: str,
        task_traits: set[str],
        default_model: str,
        model_name: str,
    ) -> dict[str, Any]:
        capabilities = bundle["capabilities"]["models"].get(model_name, {})
        weaknesses = bundle["weaknesses"]["models"].get(model_name, {})
        task_preferences = bundle["routing_knowledge"].get("task_preferences", {}).get(task_type, {})
        stats = bundle["routing_knowledge"].get("observed_stats", {}).get(model_name, {}).get(task_type, {})

        score = 40
        reasons = []
        if model_name == default_model:
            score += 8
            reasons.append("Registry default for this task type.")
        if model_name in task_preferences.get("preferred_models", []):
            score += 16
            reasons.append(f"Marked preferred for '{task_type}'.")
        if model_name in task_preferences.get("avoid_models", []):
            score -= 18
            reasons.append(f"Marked avoid for '{task_type}'.")

        preferred_tasks = set(capabilities.get("preferred_tasks", []))
        strengths = set(capabilities.get("strengths", []))
        avoid_for = set(weaknesses.get("avoid_for", []))
        weakness_terms = set(weaknesses.get("weaknesses", []))

        matched_preferred = sorted(task_traits & preferred_tasks)
        if matched_preferred:
            score += 6 * len(matched_preferred)
            reasons.append(f"Matches preferred tasks: {', '.join(matched_preferred[:3])}.")
        matched_strengths = sorted(task_traits & strengths)
        if matched_strengths:
            score += 3 * len(matched_strengths)
            reasons.append(f"Strength match: {', '.join(matched_strengths[:3])}.")
        matched_avoid = sorted(task_traits & avoid_for)
        if matched_avoid:
            score -= 8 * len(matched_avoid)
            reasons.append(f"avoid_for conflict: {', '.join(matched_avoid[:3])}.")
        matched_weaknesses = sorted(task_traits & weakness_terms)
        if matched_weaknesses:
            score -= 4 * len(matched_weaknesses)
            reasons.append(f"Weakness overlap: {', '.join(matched_weaknesses[:3])}.")

        runs = stats.get("runs", 0)
        if runs:
            success_rate = stats.get("successes", 0) / max(runs, 1)
            score += int(round((success_rate - 0.5) * 12))
            reasons.append(f"Observed success rate {int(success_rate * 100)}% over {runs} run(s).")

        avg_time = stats.get("avg_time_ms", 0)
        slow_threshold = bundle["weaknesses"].get("update_rules", {}).get("slow_ms_threshold", 90000)
        if avg_time and avg_time > slow_threshold:
            score -= 3
            reasons.append(f"Observed slow average execution ({avg_time}ms).")

        failure_penalty = self._failure_penalty(bundle["failure_patterns"], model_name, task_type)
        if failure_penalty:
            score -= failure_penalty
            reasons.append(f"Recent failure pattern penalty: -{failure_penalty}.")

        return {
            "model": model_name,
            "score": score,
            "reasons": reasons or ["No special signals."],
        }

    def _score_tool_candidate(
        self,
        bundle: dict[str, Any],
        task_traits: set[str],
        default_tool: Optional[str],
        tool_name: str,
    ) -> dict[str, Any]:
        tool_data = bundle["tool_map"].get("tools", {}).get(tool_name, {})
        stats = tool_data.get("observed_stats", {}).get(self.agent_name, {})
        best_for = set(tool_data.get("best_for", []))
        avoid_for = set(tool_data.get("avoid_for", []))

        score = 35
        reasons = []
        if tool_name == default_tool:
            score += 10
            reasons.append("Detected default tool for this task.")

        matched_best = sorted(task_traits & best_for)
        if matched_best:
            score += 5 * len(matched_best)
            reasons.append(f"best_for match: {', '.join(matched_best[:3])}.")
        matched_avoid = sorted(task_traits & avoid_for)
        if matched_avoid:
            score -= 8 * len(matched_avoid)
            reasons.append(f"avoid_for conflict: {', '.join(matched_avoid[:3])}.")

        runs = stats.get("runs", 0)
        if runs:
            success_rate = stats.get("successes", 0) / max(runs, 1)
            score += int(round((success_rate - 0.5) * 10))
            reasons.append(f"Observed success rate {int(success_rate * 100)}% over {runs} run(s).")

        return {
            "tool": tool_name,
            "score": score,
            "reasons": reasons or ["No special signals."],
        }

    def _pick_strategy(self, bundle: dict[str, Any], task: str, task_type: str) -> dict[str, Any]:
        normalized = task.lower()
        meta_strategies = bundle["routing_knowledge"].get("meta_strategies", {})
        if detect_automation_route(task) == "worker":
            return meta_strategies.get("multi_step_automation", {})
        if detect_automation_route(task) == "browser":
            return meta_strategies.get("browser_task", {})
        if detect_automation_route(task) == "windows":
            return meta_strategies.get("desktop_task", {})
        if any(keyword in normalized for keyword in ["broken project", "fix project", "repair project"]):
            return meta_strategies.get("repair_project", {})
        return bundle["routing_knowledge"].get("task_preferences", {}).get(task_type, {})

    def _failure_penalty(self, failure_patterns: dict[str, Any], model_name: str, task_type: str) -> int:
        observed = failure_patterns.get("observed_patterns", {})
        penalty = 0
        prefix = f"{model_name}::{task_type}::"
        for key, payload in observed.items():
            if key.startswith(prefix):
                penalty += min(payload.get("count", 0) * 2, 8)
        return min(penalty, 12)

    def _record_failure_pattern(
        self,
        failure_patterns: dict[str, Any],
        model_name: str,
        task_type: str,
        error: Optional[str],
    ) -> str:
        signature = self._error_signature(error)
        observed = failure_patterns.setdefault("observed_patterns", {})
        key = f"{model_name}::{task_type}::{signature}"
        entry = observed.setdefault(key, {
            "model": model_name,
            "task_type": task_type,
            "signature": signature,
            "count": 0,
            "last_seen": None,
            "last_error": None,
        })
        entry["count"] += 1
        entry["last_seen"] = self._timestamp()
        entry["last_error"] = self._trim(error, 240) if error else None

        max_patterns = DEFAULT_SELF_MODEL["weaknesses"]["update_rules"]["max_failure_patterns"]
        if len(observed) > max_patterns:
            overflow = sorted(observed.items(), key=lambda item: item[1].get("count", 0))[:-max_patterns]
            for old_key, _ in overflow:
                observed.pop(old_key, None)
        return key

    def _apply_learning_rules(
        self,
        capabilities: dict[str, Any],
        weaknesses: dict[str, Any],
        routing: dict[str, Any],
        model_name: str,
        task_type: str,
        stats: dict[str, Any],
    ) -> None:
        rules = weaknesses.get("update_rules", {})
        success_threshold = rules.get("success_threshold_for_preference", 3)
        failure_threshold = rules.get("failure_threshold_for_avoid", 2)

        runs = stats.get("runs", 0)
        successes = stats.get("successes", 0)
        failures = stats.get("failures", 0)
        success_rate = successes / max(runs, 1)

        task_preferences = routing.setdefault("task_preferences", {}).setdefault(task_type, {
            "preferred_models": [],
            "avoid_models": [],
            "strategy": "",
        })
        model_capabilities = capabilities.setdefault("models", {}).setdefault(model_name, {
            "strengths": [],
            "preferred_tasks": [],
            "execution_style": "learned",
        })
        model_weaknesses = weaknesses.setdefault("models", {}).setdefault(model_name, {
            "weaknesses": [],
            "avoid_for": [],
        })

        if runs >= success_threshold and success_rate >= 0.8:
            if model_name not in task_preferences["preferred_models"]:
                task_preferences["preferred_models"].append(model_name)
            if task_type not in model_capabilities["preferred_tasks"]:
                model_capabilities["preferred_tasks"].append(task_type)

        if runs >= failure_threshold and failures > successes and success_rate < 0.5:
            if model_name not in task_preferences["avoid_models"]:
                task_preferences["avoid_models"].append(model_name)
            if task_type not in model_weaknesses["avoid_for"]:
                model_weaknesses["avoid_for"].append(task_type)

    def _update_tool_stats(
        self,
        tool_map: dict[str, Any],
        tool_name: str,
        success: bool,
        error: Optional[str],
    ) -> None:
        tools = tool_map.setdefault("tools", {})
        tool_entry = tools.setdefault(tool_name, {
            "best_for": [],
            "avoid_for": [],
            "drivers": [],
            "observed_stats": {},
        })
        stats = tool_entry.setdefault("observed_stats", {}).setdefault(self.agent_name, {
            "runs": 0,
            "successes": 0,
            "failures": 0,
            "last_error": None,
        })
        stats["runs"] += 1
        if success:
            stats["successes"] += 1
        else:
            stats["failures"] += 1
            stats["last_error"] = self._trim(error, 200) if error else None

        agent_tooling = tool_map.setdefault("agent_tooling", {}).setdefault(self.agent_name, {
            "available_tools": [],
            "observed_stats": {},
        })
        agent_stats = agent_tooling.setdefault("observed_stats", {}).setdefault(tool_name, {
            "runs": 0,
            "successes": 0,
            "failures": 0,
        })
        agent_stats["runs"] += 1
        if success:
            agent_stats["successes"] += 1
        else:
            agent_stats["failures"] += 1

    def _default_tool_for_task(self, task: str) -> Optional[str]:
        route = detect_automation_route(task)
        if route == "browser":
            return "browser"
        if route == "windows":
            return "windows"
        if route == "worker":
            return "worker"

        normalized = task.lower()
        if any(keyword in normalized for keyword in ["replace ", "exact text", "swap text", "surgical"]):
            return "surgical_edit"
        return None

    def _tool_task_type(self, task: str) -> str:
        route = detect_automation_route(task)
        if route:
            return f"{route}_automation"

        normalized = task.lower()
        if any(keyword in normalized for keyword in ["replace ", "exact text", "swap text", "surgical"]):
            return "file_edit"
        return "tool_task"

    def _error_signature(self, error: Optional[str]) -> str:
        if not error:
            return "unknown_failure"
        normalized = error.lower()
        if "timeout" in normalized:
            return "timeout"
        if "api key" in normalized or "not set" in normalized or "credential" in normalized:
            return "api_key_missing"
        if "json" in normalized:
            return "invalid_json"
        if "not found" in normalized or "missing" in normalized:
            return "tool_unavailable"
        if "permission" in normalized or "access denied" in normalized:
            return "permission_denied"
        if "navigate" in normalized or "browser" in normalized or "page" in normalized:
            return "navigation_failed"
        return "unknown_failure"

    def _compact_decision(self, decision_simulation: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
        if not decision_simulation:
            return None
        return {
            "selected_model": decision_simulation.get("selected_model"),
            "default_model": decision_simulation.get("default_model"),
            "selected_tool": decision_simulation.get("selected_tool"),
            "critic_notes": decision_simulation.get("critic_notes", [])[:2],
            "ranked_options": decision_simulation.get("ranked_options", [])[:2],
            "ranked_tools": decision_simulation.get("ranked_tools", [])[:2],
        }

    def _unique_values(self, values: Iterable[str]) -> list[str]:
        unique: list[str] = []
        for value in values:
            if value and value not in unique:
                unique.append(value)
        return unique

    def _trim(self, value: Optional[str], limit: int) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        if len(text) <= limit:
            return text
        return text[: limit - 3] + "..."

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
