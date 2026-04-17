"""
Adapter for minimax-m2.7:cloud - Planning / Strategic model.
"""

import ollama
from typing import Dict, Any, Optional
from .base_adapter import BaseAdapter


class MinimaxAdapter(BaseAdapter):
    """Adapter for strategic planning and architecture tasks."""

    def __init__(self):
        self.model_name = "minimax-m2.7:cloud"
        self.system_prompt = """You are a strategic planner and architect.
Focus on:
- Understanding the core problem
- Designing clean solutions
- Considering trade-offs
- Breaking down complex tasks

Think before you act. Be thorough but efficient.
"""

    def generate_response(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a planning-oriented response."""
        try:
            messages = [{"role": "system", "content": self.system_prompt}]

            if context and "history" in context:
                messages.extend(context["history"])

            messages.append({"role": "user", "content": task})

            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                options={"num_predict": 2000}
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
        """Check if minimax model is available."""
        try:
            ollama.show(self.model_name)
            return True
        except Exception:
            return False