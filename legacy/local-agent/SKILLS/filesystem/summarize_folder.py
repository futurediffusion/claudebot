#!/usr/bin/env python3
"""
Summarize a folder structure.
Usage: python summarize_folder.py <path> [depth]
"""

import sys
import os
from pathlib import Path
from datetime import datetime


def format_size(size_bytes):
    """Format bytes to human readable."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def summarize_folder(path, max_depth=2, current_depth=0, prefix=""):
    """Recursively summarize a folder."""
    path = Path(path)

    if not path.exists():
        print(f"ERROR: Path does not exist: {path}")
        sys.exit(1)

    items = []
    total_size = 0
    file_count = 0
    folder_count = 0
    largest_file = (None, 0)

    try:
        for item in sorted(path.iterdir()):
            if item.name.startswith('.'):
                continue

            if item.is_dir():
                folder_count += 1
                items.append((item.name + "/", item, "dir"))
            else:
                size = item.stat().st_size
                total_size += size
                file_count += 1

                if size > largest_file[1]:
                    largest_file = (item.name, size)

                items.append((item.name, item, "file"))
    except PermissionError:
        print(f"ERROR: Permission denied: {path}")
        sys.exit(1)

    # Print current level
    for i, (name, item, item_type) in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "

        if current_depth < max_depth and item_type == "dir":
            print(f"{prefix}{connector}{name}")
            extension = "    " if is_last else "│   "
            summarize_folder(item, max_depth, current_depth + 1, prefix + extension)
        else:
            if item_type == "dir":
                print(f"{prefix}{connector}{name}")
            else:
                size_str = format_size(item.stat().st_size)
                print(f"{prefix}{connector}{name} ({size_str})")

    return file_count, folder_count, total_size, largest_file


def main():
    # Fix UTF-8 encoding on Windows
    sys.stdout.reconfigure(encoding='utf-8')

    if len(sys.argv) < 2:
        path = Path.cwd()
    else:
        path = Path(sys.argv[1])

    depth = int(sys.argv[2]) if len(sys.argv) > 2 else 2

    print(f"SUMMARY: {path}")
    print("-" * 40)

    file_count, folder_count, total_size, largest = summarize_folder(path, depth)

    print("-" * 40)
    print(f"Stats:")
    print(f"  Total files: {file_count}")
    print(f"  Total folders: {folder_count}")
    if largest[0]:
        print(f"  Largest file: {largest[0]} ({format_size(largest[1])})")

    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    print(f"  Last modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()