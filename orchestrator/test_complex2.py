#!/usr/bin/env python3
"""Manual run rotation tests for single-agent policy."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.task_decomposer import SingleAgentOrchestrator
from models.model_registry import get_model_by_agent


def _fake_subtasks() -> list[dict]:
    return [
        {"id": "s1", "description": "Analyze", "phase": "Analysis", "task_type": "planning", "model": None, "depends_on": None, "outputs": [], "result": None, "completed": False},
        {"id": "s2", "description": "Apply", "phase": "Implementation", "task_type": "fast_coding", "model": None, "depends_on": "s1", "outputs": [], "result": None, "completed": False},
    ]


def _run_for_agent(agent_name: str) -> dict:
    locked_model = get_model_by_agent(agent_name)
    assert locked_model is not None

    orchestrator = SingleAgentOrchestrator.__new__(SingleAgentOrchestrator)
    orchestrator.agent_name = agent_name
    orchestrator.routing_mode = "locked_agent"
    orchestrator.decomposer = SimpleNamespace(decompose=lambda _task: _fake_subtasks())
    orchestrator.base_orchestrator = SimpleNamespace(
        router=SimpleNamespace(resolve_locked_model=lambda _agent: locked_model),
        execute=lambda _task: {"model": locked_model.value, "success": True, "execution_time_ms": 2},
    )
    return orchestrator.execute_complex_task("Apply change safely", verbose=False)


def test_manual_rotation_between_runs_without_internal_mix():
    run_a = _run_for_agent("gemini_cli")
    run_b = _run_for_agent("codex_cli")

    models_a = {result["model"] for result in run_a["results"]}
    models_b = {result["model"] for result in run_b["results"]}

    assert run_a["execution_mode"] == "single_agent"
    assert run_b["execution_mode"] == "single_agent"
    assert len(models_a) == 1
    assert len(models_b) == 1
    assert models_a == {run_a["model_locked"]}
    assert models_b == {run_b["model_locked"]}
    assert run_a["model_locked"] != run_b["model_locked"]
