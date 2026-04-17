#!/usr/bin/env python3
"""
Context Hotloader - Session Start Summary
Reads MEMORY/ and outputs a 3-line summary:
  Line 1: What was done
  Line 2: What failed
  Line 3: What's next
"""

import sys
from pathlib import Path

MEMORY_DIR = Path(__file__).parent / "MEMORY"


def read_md(filepath):
    """Read a markdown file and return content."""
    if not filepath.exists():
        return ""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def get_last_entry(content, section_header):
    """Get the most recent entry under a section header."""
    if not content:
        return None

    lines = content.split("\n")
    in_section = False
    entries = []

    for line in lines:
        if section_header in line:
            in_section = True
        elif in_section and line.startswith("## ") and not line.startswith("## ["):
            # Section ended
            break
        elif in_section and ("### [" in line or "## [20" in line):
            if "Ejemplo" not in line and "Template" not in line:
                entries.append(line)

    return entries[-1] if entries else None


def get_in_progress(content):
    """Get in-progress tasks."""
    if not content:
        return []
    lines = content.split("\n")
    tasks = []
    capture = False

    for line in lines:
        if "Tareas en Curso" in line or "## Tareas" in line:
            capture = True
        elif capture and line.startswith("## [20"):
            break
        elif capture and "IN_PROGRESS" in line:
            tasks.append(line.strip())
        elif capture and line.startswith("**"):
            # Could be task title
            pass

    return tasks


def main():
    # Fix UTF-8 on Windows
    sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 50)
    print("CONTEXT HOTLOADER")
    print("=" * 50)

    # Read memory files
    failures_content = read_md(MEMORY_DIR / "failures.md")
    learnings_content = read_md(MEMORY_DIR / "learnings.md")
    todos_content = read_md(MEMORY_DIR / "todos.md")

    # DONE: from last learning
    last_learning = get_last_entry(learnings_content, "Learnings Importantes")
    if last_learning:
        done = last_learning.strip()
        print(f"DONE: {done}")
    else:
        print("DONE: (sin actividad reciente)")

    # FAIL: from last failure (check for UNRESOLVED first)
    last_failure = get_last_entry(failures_content, "Fracasos Registrados")
    if last_failure:
        fail = last_failure.strip()
        print(f"FAIL: {fail}")
    else:
        print("FAIL: (sin fracasos registrados)")

    # NEXT: from todos in-progress
    in_progress = get_in_progress(todos_content)
    if in_progress:
        for task in in_progress[:3]:
            print(f"NEXT: {task}")
    else:
        print("NEXT: (sin tareas en progreso)")

    print("=" * 50)


if __name__ == "__main__":
    main()