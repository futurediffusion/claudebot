"""
Adapter for gemma4:latest - Lightweight local model.
"""

import ollama
from typing import Dict, Any, Optional
from .base_adapter import BaseAdapter


class Gemma4Adapter(BaseAdapter):
    """Adapter for lightweight, cheap tasks."""

    def __init__(self):
        self.model_name = "gemma4:latest"
        self.system_prompt = """You are a fast, lightweight assistant.
Handle simple tasks efficiently:
- Quick classifications
- Brief summaries
- Simple decisions
- Listing and counting

Be concise. Don't overthink.
"""

    def generate_response(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a lightweight response."""
        try:
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(self._context_state_messages(context))

            messages.extend(self._history_messages(context))

            messages.append({"role": "user", "content": task})

            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                options={"num_predict": 500}
            )

            return {
                "success": True,
                "response": response["message"]["content"],
                "model": self.model_name,
                "tokens": response.get("eval_count", 0)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": self.model_name
            }

    def health_check(self) -> bool:
        """Check if gemma4 model is available."""
        try:
            ollama.show(self.model_name)
            return True
        except Exception:
            return False
