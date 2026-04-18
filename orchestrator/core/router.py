"""
Router - classifies tasks and selects the optimal model.
"""

import os
from typing import Any, Dict, Tuple

from core.self_model_engine import SelfModelEngine
from models.model_registry import (
    MODELS,
    ModelType,
    TaskType,
    can_use_groq,
    classify_task,
    get_fallback_model,
    get_model_by_agent,
    get_model_by_task,
    should_not_use_groq,
)


def _env_flag_enabled(name: str) -> bool:
    """Return True when an env flag is set to a truthy value."""
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


class Router:
    """
    Routes tasks to the appropriate model based on classification.

    Principles:
    - Never use heavy models for simple tasks
    - Always route before executing
    - One model per decision phase
    - Groq is only for fast processing, not for thinking
    - The self-model can override defaults when repeated evidence says so
    """

    def __init__(
        self,
        agent_name: str = "claude_code",
        routing_mode: str = "locked_agent",
        allow_legacy_routing: bool = False,
        gemini_model: ModelType = ModelType.FAST_CODING,
        claude_model: ModelType = ModelType.HEAVY_CODING,
        codex_model: ModelType = ModelType.HEAVY_CODING,
        minimax_model: ModelType = ModelType.PLANNING,
    ):
        local_multimodel_enabled = _env_flag_enabled("ENABLE_LOCAL_MULTIMODEL_EXPERIMENTAL")
        if routing_mode != "locked_agent" and not (allow_legacy_routing and local_multimodel_enabled):
            raise ValueError(
                "Legacy routing is disabled. Set ENABLE_LOCAL_MULTIMODEL_EXPERIMENTAL=1 "
                "and pass allow_legacy_routing=True to enable it explicitly."
            )

        self.agent_name = agent_name
        self.routing_mode = routing_mode
        self.classify = classify_task
        self.get_model_by_task = get_model_by_task
        self.get_model_by_agent = get_model_by_agent
        self.get_fallback = get_fallback_model
        self.self_model = SelfModelEngine(agent_name=agent_name)
        self._gemini_model = gemini_model
        self._claude_model = claude_model
        self._codex_model = codex_model
        self._minimax_model = minimax_model
        self._last_decision_meta: Dict[str, Any] = {}

    def resolve_locked_model(self, agent_name: str) -> ModelType:
        """Resolve a fixed model for a given agent identity."""
        profiled_model = self.get_model_by_agent(agent_name)
        if profiled_model is not None:
            return profiled_model

        normalized_agent = (agent_name or "").strip().lower()
        legacy_mapping = {
            "gemini_cli": self._gemini_model,
            "claude_code": self._claude_model,
            "codex_cli": self._codex_model,
            "minimax_cli": self._minimax_model,
        }
        return legacy_mapping.get(normalized_agent, self._claude_model)

    def route(self, task: str) -> Tuple[ModelType, TaskType, str]:
        """
        Route a task to the appropriate model.

        Returns:
            Tuple of (model_type, task_type, reasoning)
        """
        task_type = self.classify(task)
        agent_default_model = self.get_model_by_agent(self.agent_name)
        default_model = agent_default_model or self.get_model_by_task(task_type)
        locked_agent = self.routing_mode == "locked_agent"
        locked_model = self.resolve_locked_model(self.agent_name) if locked_agent else None
        model_type = locked_model or default_model

        if locked_agent:
            decision_simulation = {
                "selected_model": model_type.value,
                "default_model": default_model.value,
                "critic_notes": ["Locked-agent routing enforced fixed model selection."],
                "ranked_options": [
                    {
                        "model": model_type.value,
                        "score": 1.0,
                        "reasons": ["routing_mode=locked_agent"],
                    }
                ],
            }
        else:
            decision_simulation = self.self_model.simulate_routing(
                task=task,
                task_type=task_type.value,
                default_model=default_model.value,
                candidate_models=[candidate.value for candidate in self._candidate_models(task_type, default_model)],
            )

            selected_name = decision_simulation.get("selected_model")
            if selected_name:
                selected_model = self._find_model_type(selected_name)
                if selected_model is not None:
                    model_type = selected_model

        is_valid, validation_reason = self.validate_task_model_match(task, model_type)
        if not is_valid and not locked_agent:
            if task_type in {TaskType.PLANNING, TaskType.ARCHITECTURE}:
                model_type = ModelType.PLANNING
            elif task_type in {TaskType.HEAVY_REFACTOR, TaskType.MULTI_FILE_FIX}:
                model_type = ModelType.HEAVY_CODING
            else:
                model_type = ModelType.FAST_CODING

        model_config = MODELS[model_type]
        provider_note = "Groq fast-processing layer" if model_config.provider == "groq" else model_config.provider
        reasoning = (
            f"Task classified as '{task_type.value}'. "
            f"Selected '{model_config.name}' via {provider_note} "
            f"for {model_config.role}. "
            f"Strengths: {', '.join(model_config.strengths[:2])}."
        )

        if decision_simulation.get("selected_model") != default_model.value:
            reasoning += (
                f" Self-model preferred '{decision_simulation.get('selected_model')}' "
                f"over registry default '{default_model.value}'."
            )
        if locked_agent and locked_model is not None:
            profile_note = "profiled" if agent_default_model is not None else "legacy-compat"
            reasoning += (
                f" Locked to agent '{self.agent_name}' model '{locked_model.value}' "
                f"(routing_mode=locked_agent, {profile_note} by get_model_by_agent)."
            )

        critic_notes = decision_simulation.get("critic_notes", [])
        if critic_notes:
            reasoning += f" Critic: {critic_notes[0]}"

        if not is_valid:
            if locked_agent:
                reasoning += f" Validation warning: {validation_reason}."
            else:
                reasoning += f" Rerouted because: {validation_reason}."

        self._last_decision_meta = {
            "task": task,
            "task_type": task_type.value,
            "default_model": default_model.value,
            "selected_model": model_type.value,
            "decision_simulation": decision_simulation,
            "validation_reason": validation_reason,
            "locked_agent": locked_agent,
            "locked_model": locked_model.value if locked_model else None,
        }

        return model_type, task_type, reasoning

    def route_with_fallback(
        self,
        task: str,
        max_fallbacks: int = 2
    ) -> Tuple[ModelType, TaskType, str, bool]:
        """
        Route with automatic fallback support.

        Returns:
            Tuple of (model_type, task_type, reasoning, used_fallback)
        """
        model_type, task_type, reasoning = self.route(task)
        used_fallback = False
        if self.routing_mode == "locked_agent":
            return model_type, task_type, reasoning, used_fallback

        if max_fallbacks <= 0:
            return model_type, task_type, reasoning, used_fallback

        current_cost = MODELS[model_type].cost_level

        if current_cost == "high" and task_type in {TaskType.FAST_CODING, TaskType.SCAFFOLDING}:
            fallback = get_fallback_model(model_type)
            if fallback:
                model_type = fallback
                used_fallback = True
                model_config = MODELS[model_type]
                reasoning += f" [FALLBACK: using lighter model {model_config.name}]"
                if self._last_decision_meta:
                    self._last_decision_meta["selected_model"] = model_type.value
                    decision = self._last_decision_meta.get("decision_simulation", {})
                    if decision:
                        decision["selected_model"] = model_type.value
                        decision.setdefault("critic_notes", []).append("Cost fallback applied after simulation.")

        return model_type, task_type, reasoning, used_fallback

    def estimate_cost(
        self,
        model_type: ModelType,
        task_complexity: str = "medium"
    ) -> Dict[str, Any]:
        """
        Estimate the cost and time for a model.

        Args:
            model_type: The selected model
            task_complexity: "low", "medium", or "high"

        Returns:
            Cost and time estimates
        """
        config = MODELS[model_type]
        multipliers = {"low": 0.5, "medium": 1.0, "high": 2.0}
        mult = multipliers.get(task_complexity, 1.0)

        return {
            "model": config.name,
            "provider": config.provider,
            "cloud": config.cloud,
            "cost_level": config.cost_level,
            "estimated_seconds": int(config.timeout_seconds * mult),
            "local_only": not config.cloud,
        }

    def get_last_decision_meta(self) -> Dict[str, Any]:
        """Return the last self-model routing simulation."""
        return dict(self._last_decision_meta)

    def validate_task_model_match(self, task: str, model_type: ModelType) -> Tuple[bool, str]:
        """
        Validate that a model is appropriate for a task.

        Returns:
            (is_valid, reason)
        """
        task_type = classify_task(task)

        if model_type == ModelType.VISION:
            task_lower = task.lower()
            vision_indicators = ["screenshot", "image", "visual", "ui ", "interface"]
            if not any(indicator in task_lower for indicator in vision_indicators):
                return False, "qwen3-vl:latest should only be used for vision tasks"

        if model_type == ModelType.LIGHTWEIGHT and task_type in {
            TaskType.PLANNING,
            TaskType.ARCHITECTURE,
            TaskType.HEAVY_REFACTOR,
            TaskType.MULTI_FILE_FIX,
        }:
            return False, "gemma4:latest is too weak for planning or complex coding"

        if model_type in {ModelType.GROQ_FAST, ModelType.GROQ_ULTRA_CHEAP}:
            if should_not_use_groq(task_type):
                return False, f"{model_type.value} should not be used for {task_type.value}"
            if not can_use_groq(task_type):
                return False, f"{model_type.value} is reserved for parsing, validation, formatting, classification, or json tasks"

        return True, "Match validated"

    def _candidate_models(self, task_type: TaskType, default_model: ModelType) -> list[ModelType]:
        """Build a compact set of candidate models for self-model simulation."""
        candidates = [default_model]
        fallback = self.get_fallback(default_model)
        if fallback is not None and fallback not in candidates:
            candidates.append(fallback)

        if task_type in {TaskType.PLANNING, TaskType.ARCHITECTURE}:
            candidates.extend([ModelType.PLANNING, ModelType.FAST_CODING])
        elif task_type in {TaskType.HEAVY_REFACTOR, TaskType.MULTI_FILE_FIX, TaskType.FAST_CODING, TaskType.SCAFFOLDING}:
            candidates.extend([ModelType.HEAVY_CODING, ModelType.FAST_CODING, ModelType.LIGHTWEIGHT])
        elif task_type in {TaskType.LOG_ANALYSIS, TaskType.PARSING, TaskType.VALIDATION}:
            candidates.extend([ModelType.GROQ_FAST, ModelType.GROQ_ULTRA_CHEAP, ModelType.LIGHTWEIGHT])
        elif task_type in {TaskType.FORMATTING, TaskType.CLASSIFICATION, TaskType.JSON_GEN}:
            candidates.extend([ModelType.GROQ_ULTRA_CHEAP, ModelType.GROQ_FAST, ModelType.LIGHTWEIGHT])
        elif task_type in {TaskType.VISION, TaskType.SCREENSHOT, TaskType.UI_ANALYSIS}:
            candidates.extend([ModelType.GROQ_VISION_SCOUT, ModelType.VISION])
        else:
            candidates.extend([ModelType.LIGHTWEIGHT, ModelType.FAST_CODING])

        unique_candidates: list[ModelType] = []
        for candidate in candidates:
            if candidate not in unique_candidates:
                unique_candidates.append(candidate)
        return unique_candidates

    def _find_model_type(self, model_name: str) -> ModelType | None:
        """Resolve a model string back to ModelType when possible."""
        for candidate in ModelType:
            if candidate.value == model_name:
                return candidate
        return None
