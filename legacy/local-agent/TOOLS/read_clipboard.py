#!/usr/bin/env python3
"""
Read text from system clipboard.
"""

import sys


def read_clipboard():
    """Read text from clipboard."""
    try:
        import pyperclip
        text = pyperclip.paste()
        print(text)
        return text
    except ImportError:
        pass

    # Try tkinter
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        text = root.clipboard_get()
        root.destroy()
        print(text)
        return text
    except Exception:
        pass

    print("ERROR: No clipboard backend available")
    print("Install pyperclip or ensure tkinter is available")
    sys.exit(1)


if __name__ == "__main__":
    read_clipboard()