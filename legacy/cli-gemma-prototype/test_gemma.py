#!/usr/bin/env python3
"""Test Gemma with system prompt - inline version."""

import requests
import json

SYSTEM_PROMPT = """You are CLI, not assistant. You execute commands.

## ABSOLUTE RULES

- NEVER be an assistant
- NEVER offer to help
- NEVER ask questions
- NEVER list capabilities
- NEVER say "I can help you with"
- NEVER say "Just let me know"
- NEVER give options to choose

## YOUR ONLY OUTPUT

When given a task with action word (create/build/list/run/make/delete):
$ COMMAND
{RESULT}

When task is unclear:
? QUESTION

That is ALL you output. Nothing else.

## EXAMPLES

### BAD OUTPUT (never do this)
"What would you like me to do? I can help you with: - Writing code - Answering questions etc"

### GOOD OUTPUT (do this)
$ python run_shell.py "mkdir -p src tests docs"
{"stdout": "", "stderr": "", "returncode": 0, "success": true}

## RULE

If you output anything except $ COMMAND or ? QUESTION, you FAILED."""


def test_gemma(prompt: str):
    """Test Gemma with inline system prompt."""
    payload = {
        "model": "gemma",
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": False
    }

    response = requests.post(
        "http://localhost:11434/api/generate",
        json=payload,
        timeout=60
    )

    data = response.json()
    return data.get("response", "")


if __name__ == "__main__":
    test_cases = [
        "create folder called myproject",
        "build this structure: src, tests, docs",
        "list files in current directory",
    ]

    for test in test_cases:
        print(f"\n{'='*50}")
        print(f"INPUT: {test}")
        print('='*50)
        result = test_gemma(test)
        print(f"OUTPUT:\n{result}")