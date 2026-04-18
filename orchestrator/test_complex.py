#!/usr/bin/env python3
"""Fallback policy tests for single-agent routing behavior."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.router import Router
from models.model_registry import ModelType, TaskType


def test_fallback_not_used_without_explicit_permission(monkeypatch):
    router = Router(agent_name="claude_code", routing_mode="adaptive")
    monkeypatch.setattr(router, "route", lambda _task: (ModelType.HEAVY_CODING, TaskType.FAST_CODING, "base"))

    model_type, _task_type, _reasoning, used_fallback = router.route_with_fallback("Task", max_fallbacks=0)

    assert used_fallback is False
    assert model_type == ModelType.HEAVY_CODING


def test_fallback_only_when_explicitly_enabled(monkeypatch):
    router = Router(agent_name="claude_code", routing_mode="adaptive")
    monkeypatch.setattr(router, "route", lambda _task: (ModelType.HEAVY_CODING, TaskType.FAST_CODING, "base"))

    model_type, _task_type, _reasoning, used_fallback = router.route_with_fallback("Task", max_fallbacks=1)

    assert used_fallback is True
    assert model_type == ModelType.FAST_CODING
