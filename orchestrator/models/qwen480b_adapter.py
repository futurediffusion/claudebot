"""
Adapter for qwen3-coder:480b-cloud - Heavy code specialist.
"""

import ollama
from typing import Dict, Any, Optional
from .base_adapter import BaseAdapter


class Qwen480bAdapter(BaseAdapter):
    """Adapter for heavy coding tasks and multi-file operations."""

    def __init__(self):
        self.model_name = "qwen3-coder:480b-cloud"
        self.system_prompt = """You are an expert code engineer specializing in:
- Multi-file refactoring
- Complex bug fixes
- Large-scale code changes
- Deep analysis of existing codebases
- Full feature implementation

Be thorough. Analyze all relevant files before making changes.
Consider edge cases and potential regressions.
"""

    def generate_response(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a heavy coding response."""
        try:
            messages = [{"role": "system", "content": self.system_prompt}]

            if context and "file_context" in context:
                # Include file context for analysis
                for fc in context["file_context"]:
                    messages.append({
                        "role": "system",
                        "content": f"File: {fc['path']}\n\n{fc['content']}"
                    })

            if context and "history" in context:
                messages.extend(context["history"])

            messages.append({"role": "user", "content": task})

            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                options={"num_predict": 4000}
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
        """Check if qwen3-480b model is available."""
        try:
            ollama.show(self.model_name)
            return True
        except Exception:
            return False