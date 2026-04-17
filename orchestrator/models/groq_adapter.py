"""
Groq API adapters used as a fast processing layer for simple tasks.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from urllib import error, request

from .base_adapter import BaseAdapter

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
_ENV_LOADED = False


def _load_local_env() -> None:
    """
    Load GROQ_API_KEY from a local .env file if present.

    This keeps the key out of source code while still allowing simple local setup.
    """
    global _ENV_LOADED

    if _ENV_LOADED:
        return

    _ENV_LOADED = True
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if key != "GROQ_API_KEY" or key in os.environ:
            continue

        cleaned_value = value.strip().strip('"').strip("'")
        if cleaned_value:
            os.environ[key] = cleaned_value


class GroqAdapter(BaseAdapter):
    """Base adapter for Groq-backed models."""

    def __init__(self, model_name: str, system_prompt: str):
        _load_local_env()
        self.model_name = model_name
        self.system_prompt = system_prompt.strip()
        self.api_key = os.environ.get("GROQ_API_KEY", "").strip()

    def _build_messages(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> list[Dict[str, str]]:
        """Build Groq chat messages without leaking sensitive config."""
        messages: list[Dict[str, str]] = []

        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        if context and "history" in context:
            messages.extend(context["history"])

        if context and "target_file" in context:
            messages.append({
                "role": "system",
                "content": f"Target file: {context['target_file']}"
            })

        messages.append({"role": "user", "content": task})
        return messages

    def _call_api(
        self,
        messages: list[Dict[str, str]],
        max_tokens: int = 800,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """Call Groq's OpenAI-compatible chat endpoint."""
        if not self.api_key:
            return {
                "success": False,
                "error": "GROQ_API_KEY not set",
                "model": self.model_name
            }

        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        req = request.Request(
            GROQ_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))

            return {
                "success": True,
                "response": data["choices"][0]["message"]["content"],
                "model": self.model_name,
                "tokens": data.get("usage", {}).get("total_tokens", 0),
            }
        except error.HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="ignore")
            message = f"Groq API error: {exc.code}"

            try:
                error_payload = json.loads(response_body)
                api_message = error_payload.get("error", {}).get("message")
                if api_message:
                    message = f"Groq API error: {api_message}"
            except json.JSONDecodeError:
                pass

            return {
                "success": False,
                "error": message,
                "model": self.model_name,
            }
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "model": self.model_name,
            }

    def generate_response(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a response using Groq."""
        messages = self._build_messages(task, context)
        return self._call_api(messages)

    def health_check(self) -> bool:
        """Groq is considered healthy when the API key is configured."""
        return bool(self.api_key)


class GroqQwenAdapter(GroqAdapter):
    """Fast parser and validator backed by Groq's Qwen 3 32B."""

    def __init__(self):
        super().__init__(
            model_name="qwen/qwen3-32b",
            system_prompt="""
You are a fast processing model used for parsing and validation.
Focus on:
- extracting structure
- validating outputs
- checking consistency
- making small intermediate decisions

Do not do architecture, planning, or deep debugging.
Be concise and literal.
""",
        )


class GroqGPTAdapter(GroqAdapter):
    """Ultra-cheap formatter/classifier backed by GPT-OSS 20B on Groq."""

    def __init__(self):
        super().__init__(
            model_name="openai/gpt-oss-20b",
            system_prompt="""
You are a fast formatting and transformation worker.
Focus on:
- classification
- formatting
- JSON generation
- simple structured transforms

Do not plan, brainstorm, or over-explain.
Return compact outputs.
""",
        )
