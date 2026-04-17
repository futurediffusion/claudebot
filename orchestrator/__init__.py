"""
Multi-Model Orchestrator for Claude Code with Ollama.

This package uses lazy exports so lightweight helpers can be imported without
pulling model dependencies such as `ollama` immediately.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

__version__ = "1.2.0"

_LAZY_EXPORTS = {
    "Orchestrator": ("orchestrator.core.orchestrator", "Orchestrator"),
    "Router": ("orchestrator.core.router", "Router"),
    "TaskLogger": ("orchestrator.core.task_logger", "TaskLogger"),
    "ContextManager": ("orchestrator.core.context_manager", "ContextManager"),
    "SelfModelEngine": ("orchestrator.core.self_model_engine", "SelfModelEngine"),
    "EpisodicMemoryEngine": ("orchestrator.core.episodic_memory", "EpisodicMemoryEngine"),
    "WorldModelEngine": ("orchestrator.core.world_model", "WorldModelEngine"),
    "TaskDecomposer": ("orchestrator.core.task_decomposer", "TaskDecomposer"),
    "MultiModelOrchestrator": ("orchestrator.core.task_decomposer", "MultiModelOrchestrator"),
    "ModelType": ("orchestrator.models.model_registry", "ModelType"),
    "TaskType": ("orchestrator.models.model_registry", "TaskType"),
    "MODELS": ("orchestrator.models.model_registry", "MODELS"),
}

__all__ = ["__version__", *_LAZY_EXPORTS.keys()]


def __getattr__(name: str) -> Any:
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module 'orchestrator' has no attribute {name!r}")

    module_name, attr_name = _LAZY_EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
