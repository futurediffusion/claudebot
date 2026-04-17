#!/usr/bin/env python3
"""
Self-check: verify all tools and dependencies are available.
"""

import sys
import os
from pathlib import Path


def check_python():
    """Check Python version."""
    v = sys.version_info
    print(f"Python: {v.major}.{v.minor}.{v.micro}")
    return True


def check_module(name, import_name=None):
    """Check if a module is available."""
    import_name = import_name or name
    try:
        __import__(import_name)
        print(f"{name}: OK")
        return True
    except ImportError:
        print(f"{name}: MISSING")
        return False


def check_file(path):
    """Check if a file exists."""
    if os.path.exists(path):
        print(f"{path}: OK")
        return True
    else:
        print(f"{path}: MISSING")
        return False


def main():
    print("=" * 40)
    print("SELF-CHECK")
    print("=" * 40)

    print("\n[Python]")
    check_python()

    print("\n[Core Modules]")
    check_module("Pillow", "PIL")
    check_module("requests")
    check_module("pytest")

    print("\n[Agent Structure]")
    base = Path(__file__).parent.parent
    check_file(base / "SKILLS")
    check_file(base / "MEMORY")
    check_file(base / "WORKSPACE")
    check_file(base / "LOGS")
    check_file(base / "SYSTEM.md")
    check_file(base / "RULES.md")

    print("\n[Skills]")
    skills = ["screenshot", "filesystem", "vision", "testing", "webgrab"]
    for skill in skills:
        skill_path = base / "SKILLS" / skill
        if skill_path.exists():
            print(f"{skill}: OK")
        else:
            print(f"{skill}: MISSING")

    print("\n" + "=" * 40)
    print("DONE")


if __name__ == "__main__":
    main()