#!/usr/bin/env python3
"""Execute command via Gemma using Ollama API."""

import subprocess
import json
import sys
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
SYSTEM_PROMPT_PATH = "agent/system_prompt.txt"


def load_system_prompt():
    with open(SYSTEM_PROMPT_PATH, "r") as f:
        return f.read()


def ask_gemma(command: str) -> str:
    """Send command to Gemma and return response."""
    system_prompt = load_system_prompt()

    payload = {
        "model": "gemma",
        "prompt": command,
        "system": system_prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.5
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        return f"Error: {e}"


def execute_gemma_output(output: str):
    """Parse Gemma output and execute commands."""
    lines = output.strip().split("\n")

    for line in lines:
        line = line.strip()
        if line.startswith("$ python run_shell.py"):
            # Extract command
            cmd = line.replace("$ python run_shell.py", "").strip()
            cmd = cmd.strip('"')

            # Execute it
            result = subprocess.run(
                ["python", "run_shell.py", cmd],
                capture_output=True,
                text=True
            )
            print(result.stdout)
            return result.stdout

    return ""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_gemma.py \"create folder test\"")
        sys.exit(1)

    command = " ".join(sys.argv[1:])
    print(f"User: {command}")

    response = ask_gemma(command)
    print(f"Gemma: {response}")

    execute_gemma_output(response)