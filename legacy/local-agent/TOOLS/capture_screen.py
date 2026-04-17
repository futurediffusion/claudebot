#!/usr/bin/env python3
"""
Capture screen using multiple backends.
Tries: PIL > mss > pyautogui
"""

import sys
import os
from datetime import datetime

def capture_screen():
    """Try multiple backends to capture screen."""
    output_path = None

    # Try PIL
    try:
        from PIL import ImageGrab
        screenshot = ImageGrab.grab()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        workspace = os.path.join(os.path.dirname(__file__), "..", "WORKSPACE")
        os.makedirs(workspace, exist_ok=True)
        output_path = os.path.join(workspace, f"screen_{timestamp}.png")
        screenshot.save(output_path)
        print(f"OK: {output_path}")
        return
    except Exception as e:
        pass

    # Try mss
    try:
        import mss
        with mss.mss() as sct:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            workspace = os.path.join(os.path.dirname(__file__), "..", "WORKSPACE")
            os.makedirs(workspace, exist_ok=True)
            output_path = os.path.join(workspace, f"screen_{timestamp}.png")
            sct.shot(output=output_path)
            print(f"OK: {output_path}")
            return
    except Exception as e:
        pass

    print("ERROR: No screen capture backend available")
    print("Install one of: Pillow, mss")
    sys.exit(1)


if __name__ == "__main__":
    capture_screen()