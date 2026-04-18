#!/usr/bin/env python3
"""Tests for decomposition + single-agent execution policy."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.task_decomposer import SingleAgentOrchestrator
from models.model_registry import MODELS, ModelType, get_model_by_agent


def _provider_for_model(model_name: str) -> str:
    for model_type in ModelType:
        if model_type.value == model_name:
            return MODELS[model_type].provider
    raise AssertionError(f"Unknown model in test: {model_name}")


def _fake_subtasks() -> list[dict]:
    return [
        {"id": "a1", "description": "Plan", "phase": "Planning", "task_type": "planning", "model": None, "depends_on": None, "outputs": [], "result": None, "completed": False},
        {"id": "b2", "description": "Implement", "phase": "Implementation", "task_type": "fast_coding", "model": None, "depends_on": "a1", "outputs": [], "result": None, "completed": False},
        {"id": "c3", "description": "Validate", "phase": "Validation", "task_type": "validation", "model": None, "depends_on": "b2", "outputs": [], "result": None, "completed": False},
    ]


def _build_orchestrator(agent_name: str) -> SingleAgentOrchestrator:
    locked_model = get_model_by_agent(agent_name)
    assert locked_model is not None

    orchestrator = SingleAgentOrchestrator.__new__(SingleAgentOrchestrator)
    orchestrator.agent_name = agent_name
    orchestrator.routing_mode = "locked_agent"
    orchestrator.decomposer = SimpleNamespace(decompose=lambda _task: _fake_subtasks())
    orchestrator.base_orchestrator = SimpleNamespace(
        router=SimpleNamespace(resolve_locked_model=lambda _agent: locked_model),
        execute=lambda _task: {"model": locked_model.value, "success": True, "execution_time_ms": 5},
    )
    return orchestrator


def test_single_locked_model_per_execution():
    orchestrator = _build_orchestrator("gemini_cli")
    report = orchestrator.execute_complex_task("Implement auth feature", verbose=False)

    models_used = {result["model"] for result in report["results"]}
    assert report["execution_mode"] == "single_agent"
    assert report["model_locked"] == get_model_by_agent("gemini_cli").value
    assert len(models_used) == 1


def test_no_provider_change_between_subtasks():
    orchestrator = _build_orchestrator("codex_cli")
    report = orchestrator.execute_complex_task("Refactor module", verbose=False)

    providers = {_provider_for_model(result["model"]) for result in report["results"]}
    assert len(providers) == 1
