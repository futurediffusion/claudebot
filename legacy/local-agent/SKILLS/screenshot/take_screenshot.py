#!/usr/bin/env python3
"""
Take screenshot and save to workspace or specified path.
Usage: python take_screenshot.py [output_path]
"""

import sys
import os
from datetime import datetime

try:
    from PIL import Image, ImageGrab
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install pillow")
    sys.exit(1)


def take_screenshot(output_path=None):
    """Capture screen and save to file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if output_path is None:
        workspace = os.path.join(os.path.dirname(__file__), "..", "..", "WORKSPACE")
        os.makedirs(workspace, exist_ok=True)
        output_path = os.path.join(workspace, f"screenshot_{timestamp}.png")

    try:
        # Try PIL first (works on Windows)
        screenshot = ImageGrab.grab()
        screenshot.save(output_path)
        print(f"OK: {output_path}")
        return output_path
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    output_path = sys.argv[1] if len(sys.argv) > 1 else None
    take_screenshot(output_path)