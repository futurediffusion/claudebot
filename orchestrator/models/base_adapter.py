"""
Base adapter interface for all model adapters.
"""

import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseAdapter(ABC):
    """Base class for all model adapters."""

    CONTEXT_LABELS = {
        "self_model": "Self-model brief",
        "episodic_memory": "Relevant episodic memory",
        "world_model": "Current world model",
        "skills": "Available skill bridge matches",
    }

    def _context_state_messages(
        self,
        context: Optional[Dict[str, Any]] = None,
    ) -> list[Dict[str, str]]:
        state = (context or {}).get("state") or {}
        messages: list[Dict[str, str]] = []

        for key, label in self.CONTEXT_LABELS.items():
            value = state.get(key)
            if not value:
                continue

            try:
                serialized = json.dumps(value, ensure_ascii=False)
            except TypeError:
                serialized = str(value)

            messages.append({"role": "system", "content": f"{label}: {serialized}"})
        return messages

    def _history_messages(
        self,
        context: Optional[Dict[str, Any]] = None,
    ) -> list[Dict[str, Any]]:
        if not context:
            return []
        history = context.get("history")
        return list(history) if history else []

    @abstractmethod
    def generate_response(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a response for the given task."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the model is available."""
        pass
