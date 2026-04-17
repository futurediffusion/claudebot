#!/usr/bin/env python3
"""
Describe the last screenshot taken.
Reads the most recent image from WORKSPACE/ and describes it.
"""

import os
import glob
from datetime import datetime


def get_last_screenshot():
    """Find the most recent screenshot in WORKSPACE."""
    workspace = os.path.join(os.path.dirname(__file__), "..", "..", "WORKSPACE")
    screenshots = glob.glob(os.path.join(workspace, "screenshot_*.png"))

    if not screenshots:
        print("ERROR: No screenshots found in WORKSPACE/")
        exit(1)

    # Sort by modification time, newest first
    screenshots.sort(key=os.path.getmtime, reverse=True)
    return screenshots[0]


def describe_image(image_path):
    """Describe an image using vision."""
    # This would call the vision skill or anthropic API
    # For now, returns the path for manual inspection
    return image_path


if __name__ == "__main__":
    last = get_last_screenshot()
    print(f"LAST: {last}")

    # TODO: Integrate with vision/inspect_image.py
    # For now, just report which file is the last screenshot
    describe_image(last)