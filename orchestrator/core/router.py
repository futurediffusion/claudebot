"""
Router - classifies tasks and selects the optimal model.
"""

from typing import Any, Dict, Tuple

from models.model_registry import (
    MODELS,
    ModelType,
    TaskType,
    can_use_groq,
    classify_task,
    get_fallback_model,
    get_model_by_task,
    should_not_use_groq,
)


class Router:
    """
    Routes tasks to the appropriate model based on classification.

    Principles:
    - Never use heavy models for simple tasks
    - Always route before executing
    - One model per decision phase
    - Groq is only for fast processing, not for thinking
    """

    def __init__(self):
        self.classify = classify_task
        self.get_model = get_model_by_task
        self.get_fallback = get_fallback_model

    def route(self, task: str) -> Tuple[ModelType, TaskType, str]:
        """
        Route a task to the appropriate model.

        Returns:
            Tuple of (model_type, task_type, reasoning)
        """
        task_type = self.classify(task)
        model_type = self.get_model(task_type)

        is_valid, validation_reason = self.validate_task_model_match(task, model_type)
        if not is_valid:
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

        if not is_valid:
            reasoning += f" Rerouted because: {validation_reason}."

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
