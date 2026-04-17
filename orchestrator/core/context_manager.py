"""
Context manager - maintains task context and conversation history.
"""

from typing import Dict, Any, List, Optional
from collections import deque


class ContextManager:
    """
    Manages context for task execution.

    Maintains:
    - Conversation history
    - File context
    - Tool results
    - Execution state
    """

    def __init__(self, max_history: int = 10, max_file_contexts: int = 5):
        self.max_history = max_history
        self.max_file_contexts = max_file_contexts
        self._history: deque = deque(maxlen=max_history)
        self._file_contexts: List[Dict[str, str]] = []
        self._tool_results: Dict[str, Any] = {}
        self._state: Dict[str, Any] = {}

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self._history.append({"role": role, "content": content})

    def add_file_context(self, path: str, content: str):
        """Add file content to context."""
        self._file_contexts.append({"path": path, "content": content})
        if len(self._file_contexts) > self.max_file_contexts:
            self._file_contexts.pop(0)

    def add_tool_result(self, tool: str, result: Dict[str, Any]):
        """Store a tool execution result."""
        self._tool_results[tool] = result

    def set_state(self, key: str, value: Any):
        """Set execution state."""
        self._state[key] = value

    def get_state(self, key: str) -> Any:
        """Get execution state."""
        return self._state.get(key)

    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        return list(self._history)

    def get_file_context(self) -> List[Dict[str, str]]:
        """Get all file contexts."""
        return self._file_contexts.copy()

    def get_tool_results(self) -> Dict[str, Any]:
        """Get all tool results."""
        return self._tool_results.copy()

    def get_context(self) -> Dict[str, Any]:
        """Get complete context for model adapter."""
        return {
            "history": list(self._history),
            "file_context": self._file_contexts.copy(),
            "tool_results": self._tool_results.copy(),
            "state": self._state.copy()
        }

    def clear(self):
        """Clear all context."""
        self._history.clear()
        self._file_contexts.clear()
        self._tool_results.clear()
        self._state.clear()