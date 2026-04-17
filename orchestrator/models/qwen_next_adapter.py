"""
Adapter for qwen3-coder-next:cloud - Fast coding / Agentic.
"""

import ollama
from typing import Dict, Any, Optional
from .base_adapter import BaseAdapter


class QwenNextAdapter(BaseAdapter):
    """Adapter for fast coding, scaffolding, and agentic tasks."""

    def __init__(self):
        self.model_name = "qwen3-coder-next:cloud"
        self.system_prompt = """You are a fast, efficient coding agent.
Focus on:
- Quick, correct implementations
- Clean, simple solutions
- Fast iterations
- Getting things done

Act decisively. Make reasonable assumptions when needed.
"""

    def generate_response(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a fast coding response."""
        try:
            messages = [{"role": "system", "content": self.system_prompt}]

            if context and "target_file" in context:
                messages.append({
                    "role": "system",
                    "content": f"Target file: {context['target_file']}"
                })

            if context and "history" in context:
                messages.extend(context["history"])

            messages.append({"role": "user", "content": task})

            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                options={"num_predict": 1500}
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
        """Check if qwen3-coder-next model is available."""
        try:
            ollama.show(self.model_name)
            return True
        except Exception:
            return False