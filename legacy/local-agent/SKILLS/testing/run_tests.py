#!/usr/bin/env python3
"""
Run tests and report results.
Usage: python run_tests.py [path] [--framework pytest|unittest|all]
"""

import sys
import os
import subprocess
from datetime import datetime


def run_pytest(path="."):
    """Run pytest on the given path."""
    try:
        result = subprocess.run(
            ["pytest", "-v", "--tb=short", path],
            capture_output=True,
            text=True
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return None, None, "pytest not found"


def run_unittest(path="."):
    """Run unittest on the given path."""
    try:
        result = subprocess.run(
            ["python", "-m", "unittest", "discover", "-s", path],
            capture_output=True,
            text=True
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return None, None, str(e)


def detect_framework(path="."):
    """Auto-detect which test framework to use."""
    path_obj = os.path.abspath(path)

    # Check for pytest files
    if os.path.exists(os.path.join(path_obj, "pytest.ini")):
        return "pytest"
    if os.path.exists(os.path.join(path_obj, "pyproject.toml")):
        with open(os.path.join(path_obj, "pyproject.toml")) as f:
            content = f.read()
            if "[tool.pytest" in content:
                return "pytest"

    # Check for test files
    for root, dirs, files in os.walk(path_obj):
        for f in files:
            if f.startswith("test_") and f.endswith(".py"):
                return "unittest"

    return "pytest"  # Default


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "."

    framework = "all"
    for arg in sys.argv[2:]:
        if arg.startswith("--framework="):
            framework = arg.split("=")[1]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(
        os.path.dirname(__file__), "..", "..", "LOGS",
        f"test_{timestamp}.log"
    )

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    print(f"TEST RUN: {path}")

    if framework == "all":
        framework = detect_framework(path)

    print(f"FRAMEWORK: {framework}")

    if framework == "pytest":
        returncode, stdout, stderr = run_pytest(path)
    elif framework == "unittest":
        returncode, stdout, stderr = run_unittest(path)
    else:
        print(f"ERROR: Unknown framework: {framework}")
        sys.exit(1)

    if returncode is None:
        print(f"ERROR: {stderr}")
        sys.exit(1)

    # Log results
    with open(log_file, "w") as f:
        f.write(f"TEST RUN: {path}\n")
        f.write(f"FRAMEWORK: {framework}\n")
        f.write(f"TIMESTAMP: {timestamp}\n")
        f.write("-" * 40 + "\n")
        f.write("STDOUT:\n")
        f.write(stdout or "(no output)")
        f.write("\nSTDERR:\n")
        f.write(stderr or "(no errors)")

    print(f"LOG: {log_file}")

    if returncode == 0:
        print("RESULT: ALL TESTS PASSED")
    else:
        print("RESULT: TESTS FAILED")
        print("-" * 40)
        print(stderr or stdout)

    sys.exit(returncode)


if __name__ == "__main__":
    main()