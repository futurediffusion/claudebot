#!/usr/bin/env python3
"""Execute shell commands. Returns stdout + stderr."""

import subprocess
import sys
import json


def run_shell(command: str, timeout: int = 30) -> dict:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Timeout", "returncode": -1, "success": False}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": -1, "success": False}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_shell.py \"command\"")
        sys.exit(1)
    command = " ".join(sys.argv[1:])
    result = run_shell(command)
    print(json.dumps(result, ensure_ascii=False))