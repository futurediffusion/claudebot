"""Core package with lazy exports."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_LAZY_EXPORTS = {
    "Router": ("core.router", "Router"),
    "SelfModelEngine": ("core.self_model_engine", "SelfModelEngine"),
    "EpisodicMemoryEngine": ("core.episodic_memory", "EpisodicMemoryEngine"),
    "WorldModelEngine": ("core.world_model", "WorldModelEngine"),
    "TaskLogger": ("core.task_logger", "TaskLogger"),
    "ContextManager": ("core.context_manager", "ContextManager"),
    "Orchestrator": ("core.orchestrator", "Orchestrator"),
    "TaskDecomposer": ("core.task_decomposer", "TaskDecomposer"),
    "MultiModelOrchestrator": ("core.task_decomposer", "MultiModelOrchestrator"),
}

__all__ = list(_LAZY_EXPORTS.keys())


def __getattr__(name: str) -> Any:
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module 'core' has no attribute {name!r}")

    module_name, attr_name = _LAZY_EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
