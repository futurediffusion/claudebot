#!/usr/bin/env python3
"""
Index a folder and output a summary of all files.
Similar to filesystem skill but simpler output.
"""

import sys
import os
from pathlib import Path


def index_folder(path="."):
    """Index all files in a folder recursively."""
    path = Path(path)

    if not path.exists():
        print(f"ERROR: {path} not found")
        sys.exit(1)

    files = []
    for root, dirs, filenames in os.walk(path):
        # Skip hidden and common ignore dirs
        dirs[:] = [d for d in dirs if not d.startswith('.')
                   and d not in ['node_modules', '__pycache__', '.git']]

        for f in filenames:
            if not f.startswith('.'):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, path)
                size = os.path.getsize(full_path)
                files.append((rel_path, size))

    print(f"PATH: {path}")
    print(f"TOTAL_FILES: {len(files)}")

    # Top 10 largest files
    files.sort(key=lambda x: x[1], reverse=True)
    print("\nLARGEST_FILES:")
    for f, size in files[:10]:
        print(f"  {size:>10}  {f}")

    return files


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    index_folder(path)